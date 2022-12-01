# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, 2008-2022
#
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://metpx.github.io/sarracenia
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 2 of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#
#

import collections
import copy
import json
import logging

from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes
import paho.mqtt.client

import sarracenia
from sarracenia.encoding import Encoding
from sarracenia.moth import Moth
import ssl
import threading
import time
from urllib.parse import unquote

logger = logging.getLogger(__name__)

default_options = {
    'auto_ack': True,
    'batch': 25,
    'clean_session': False,
    'no': 0,
    'prefetch': 25,
    'qos': 1,
    'topicPrefix': ['v03']
}


class MQTT(Moth):
    """
       Message Queue Telemetry Transport support.
           talks to an MQTT broker.  Tested with mosquitto. requires MQTTv5

       Concept mapping from AMQP:

           Only supports v03 messages since mqtt3.1 has no headers.


           AMQP -> MQTT topic hierarcy mapping: 
           exchange: xpublic,  topic prefix:   v03 subtopic:   /my/favourite/directory
           results in :   xpublic/v03/my/favourite/directory

           AMQP queue -> MQTT group-id (client-id should map to  queue+instance, I think.)

       deviation from standard: group-id lengths are not checked, neither are client-id's.
           Sarracenia routinely generates such ids with 40 to 50 characters in them.
           the MQTTv3.1 standard specifies a maximum length of 23 characters, as the minimum
           a compliant broker must support.  
           https://www.eclipse.org/lists/mosquitto-dev/msg00433.html#:~:text=It%20is%2065535%20bytes.,the%20limit%20in%20mqtt%20v3.
           Both mosquitto and EMQ supports 65535 chars for that field even in v3.1, so enforcing limit seems counter-productive.

       problems with MQTT:
           lack of explicit acknowledgements (in paho library) means ack's happen without the
           application being able to process the messages... potential for message loss of
           whatever is queued... this is not good for reliability.  
           It looks like just a choice in the paho library python version... other language bindings apparently have it.
           added to bug report: https://github.com/eclipse/paho.mqtt.python/pull/554
           made a pull request: https://github.com/eclipse/paho.mqtt.python/pull/554 
           Implemented support for the modification here. Seems to work fine (not thoroughly tested yet.)

      Why v5 only:

           No shared subscriptions prior to v5. Used extensively. had originally written library with v3
           support just restricting instance=1, but then I read about the re-transmission strategy:

           In MQTT < 5, in QoS==1, one is supposed to resend messages until you get an ack. some implementations
           do it every 20 seconds.  So in a case where you have, say 5 minutes of queueing, each message will be 
           sent 300/20 -> 15 times...  an unhelpful packet storm.


      There is additionally a vulnerability/inefficiency resulting from async message reception:
           when a new message arrive the loop thread started by the paho library will append
           it to the received_messages data structure (protected by a mutex.)
           if the application crashes, the received_messages have not been ack'd to the sender... so it is
           likely that you will just get them later... could use for a shelf for received_messages,
           and sync it once in while... probably not worth it.
 
    """
    def __init__(self, broker, options, is_subscriber):
        """

          MQTT connection instances...
          in AMQP: topic separator is dot (.) in MQTT, the topic separator is slash (/)
          have exchange arguments use protocol specific separator or mapped one?

        """

        super().__init__(broker, options, is_subscriber)

        # setting this is wrong and breaks things, was already set in super-class init, doing this here overwites
        #  interpretation of options done in superclass.
        #self.o = options
        self.o.update(default_options)
        self.o.update(options)

        me = "%s.%s" % (__class__.__module__, __class__.__name__)
        logger.setLevel('WARNING')

        if ('settings' in self.o) and (me in self.o['settings']):
            for s in self.o['settings'][me]:
                self.o[s] = self.o['settings'][me][s]

            if 'logLevel' in self.o['settings'][me]:
                logger.setLevel(self.o['logLevel'].upper())

        self.proto_version = paho.mqtt.client.MQTTv5

        if is_subscriber:
            # https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Receive_Maximum
            if not 'receiveMaximum' in self.o:
                self.o['receiveMaximum'] = int(
                    min(self.o['batch'] + self.o['prefetch'], 65535))
            self.__getSetup(self.o)
        else:
            self.__putSetup(self.o)

        logger.info("note: mqtt support is newish, not very well tested")

    def __sub_on_disconnect(client, userdata, rc, properties=None):
        logger.info(paho.mqtt.client.connack_string(rc))
        if hasattr(userdata, 'pending_messages'):
            lost = len(userdata.pending_messages)
            if lost > 0:
                logger.error(
                    'message loss! cannot confirm %d messages were published: mids=%s'
                    % (lost, userdata.pending_messages))
            else:
                logger.info('clean. no published messages lost.')

    def __mgt_on_connect(client, userdata, flags, rc, properties=None):
        logger.info("management connection succeeded: rc=%s, flags=%s" %
                    (paho.mqtt.client.connack_string(rc), flags))

    def __sub_on_connect(client, userdata, flags, rc, properties=None):
        logger.info("rc=%s, flags=%s" %
                    (paho.mqtt.client.connack_string(rc), flags))

        if flags['session present'] != 1:
            logger.debug(
                'no existing session, no recovery of inflight messages from previous connection'
            )

        if rc != paho.mqtt.client.MQTT_ERR_SUCCESS:
            return

        # FIXME: enhancement could subscribe accepts multiple (subj, qos) tuples so, could do this in one RTT.
        for binding_tuple in userdata.o['bindings']:
            exchange, prefix, subtopic = binding_tuple
            logger.info("tuple: %s %s %s" % (exchange, prefix, subtopic))
            subj = '/'.join(['$share', userdata.o['queueName'], exchange] +
                            prefix + subtopic)

            (res, mid) = client.subscribe(subj, qos=userdata.o['qos'])
            logger.info( "subscribed to: %s, mid=%d qos=%s result: %s" % (subj, mid, \
                userdata.o['qos'], paho.mqtt.client.error_string(res)) )

        client.subscribe_in_progress = True

    def __sub_on_subscribe(client,
                           userdata,
                           mid,
                           granted_qos,
                           properties=None):
        logger.info("subscribe completed mid={} granted_qos={}".format(
            mid, list(map(lambda x: x.getName(), granted_qos))))

    def __pub_on_disconnect(client, userdata, rc, properties=None):
        logger.info(paho.mqtt.client.connack_string(rc))

    def __pub_on_connect(client, userdata, flags, rc, properties=None):
        logger.info(paho.mqtt.client.connack_string(rc))

    def __pub_on_publish(client, userdata, mid):
        userdata.pending_messages_mutex.acquire()

        if mid in userdata.pending_messages:
            logger.info('publish complete. mid={}'.format(mid))
            userdata.pending_messages.remove(mid)
        else:
            logger.error(
                'BUG: ack for message we do not know we published. mid={}'.
                format(mid))

        userdata.pending_messages_mutex.release()

    def __sslClientSetup(self) -> int:
        """
          Initializse self.client SSL context, must be called after self.client is instantiated.
          return port number for connection.
      
        """
        if self.broker.url.scheme[-1] == 's':
            port = 8883
            logger.info('tlsRigour: %s' % self.o['tlsRigour'])
            self.o['tlsRigour'] = self.o['tlsRigour'].lower()
            if self.o['tlsRigour'] == 'lax':
                self.tlsctx = ssl.create_default_context()
                self.tlsctx.check_hostname = False
                self.tlsctx.verify_mode = ssl.CERT_NONE

            elif self.o['tlsRigour'] == 'strict':
                self.tlsctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
                self.tlsctx.options |= ssl.OP_NO_TLSv1
                self.tlsctx.options |= ssl.OP_NO_TLSv1_1
                self.tlsctx.check_hostname = True
                self.tlsctx.verify_mode = ssl.CERT_REQUIRED
                self.tlsctx.load_default_certs()
                # TODO Find a way to reintroduce certificate revocation (CRL) in the future
                #  self.tlsctx.verify_flags = ssl.VERIFY_CRL_CHECK_CHAIN
                #  https://github.com/MetPX/sarracenia/issues/330
            elif self.o['tlsRigour'] == 'normal':
                self.tlsctx = ssl.create_default_context()
            else:
                self.logger.warning(
                    "option tlsRigour must be one of:  lax, normal, strict")
            self.client.tls_set_context(self.tlsctx)
        else:
            port = 1883

        if self.broker.url.port:
            port = self.broker.url.port
        return port

    def __clientSetup(self, options, cid) -> paho.mqtt.client.Client:

        client = paho.mqtt.client.Client( userdata=self, \
            client_id=cid, protocol=paho.mqtt.client.MQTTv5 )

        #self.client.o = options
        client.connected = False
        client.on_connect = MQTT.__sub_on_connect
        client.on_disconnect = MQTT.__sub_on_disconnect
        client.on_message = MQTT.__sub_on_message
        client.on_subscribe = MQTT.__sub_on_subscribe
        client.subscribe_in_progress = True
        # defaults to 20... kind of a mix of "batch" and prefetch...
        client.max_inflight_messages_set(options['batch'] +
                                         options['prefetch'])
        client.username_pw_set(self.broker.url.username,
                               unquote(self.broker.url.password))
        return client

    def __getSetup(self, options):
        """
           Establish a connection to consume messages with.  
        """
        ebo = 1
        while True:
            try:
                self.new_message_mutex = threading.Lock()

                cs = options['clean_session']
                if ('queueName' in options) and ('no' in options):
                    cid = options['queueName'] + '%02d' % options['no']
                else:
                    #cid = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
                    cid = None
                    cs = True

                props = Properties(PacketTypes.CONNECT)
                props.SessionExpiryInterval = int(self.o['expire'])
                props.ReceiveMaximum = int(self.o['receiveMaximum'])

                if (not ('no' in options)
                        or options['no'] == 0) and 'instances' in options:
                    logger.info('declare sessions for instances')
                    for i in range(1, options['instances'] + 1):
                        icid = options['queueName'] + '%02d' % i
                        decl_client = self.__clientSetup(options, icid)
                        decl_client.on_connect = MQTT.__mgt_on_connect
                        decl_client.connect( self.broker.url.hostname, port=self.__sslClientSetup(), \
                           clean_start=False, properties=props )
                        while not decl_client.is_connected():
                            decl_client.loop(1)
                        decl_client.disconnect()
                        decl_client.loop_stop()
                        logger.info('instance declaration for %s done' % icid)

                self.client = self.__clientSetup(options, cid)

                self.new_message_mutex.acquire()
                self.client.received_messages = []
                self.new_message_mutex.release()

                if hasattr(self.client, 'auto_ack'):  # FIXME breaking this...
                    self.client.auto_ack(False)
                    logger.debug(
                        "Switching off auto_ack for higher reliability via explicit acknowledgements."
                    )
                    self.auto_ack = False
                else:
                    logger.warning(
                        "paho library using auto_ack. may lose data every crash or restart."
                    )
                    self.auto_ack = True

                self.client.connect_async( self.broker.url.hostname, port=self.__sslClientSetup(), \
                       clean_start=False, properties=props )
                self.client.loop_start()
                return

            except Exception as err:
                logger.error("failed to {} with {}".format(
                    self.broker.url.hostname, err))
                logger.error('Exception details: ', exc_info=True)

            if ebo < 60: ebo *= 2
            time.sleep(ebo)

    def __putSetup(self, options):
        """
           establish a connection to allow publishing. 
        """
        ebo = 1
        while True:
            try:

                props = Properties(PacketTypes.CONNECT)
                if self.o['message_ttl'] > 0:
                    props.MessageExpiryInterval = int(self.o['message_ttl'])

                self.pending_messages_mutex = threading.Lock()
                self.pending_messages = collections.deque()

                self.client = paho.mqtt.client.Client(
                    protocol=self.proto_version, userdata=self)
                self.client.on_connect = MQTT.__pub_on_connect
                self.client.on_disconnect = MQTT.__pub_on_disconnect
                self.client.on_publish = MQTT.__pub_on_publish
                #dunno if this is a good idea.
                self.client.max_queued_messages_set(options['prefetch'])
                self.client.username_pw_set(self.broker.url.username,
                                            unquote(self.broker.url.password))
                res = self.client.connect(options['broker'].url.hostname,
                                          port=self.__sslClientSetup(),
                                          properties=props)
                logger.info('connecting to %s, res=%s' %
                            (options['broker'].url.hostname, res))

                self.client.loop_start()
                return

            except Exception as err:
                logger.error("failed to {} with {}".format(
                    self.broker.url.hostname, err))
                logger.error('Exception details: ', exc_info=True)

            if ebo < 60: ebo *= 2
            time.sleep(ebo)

    def __sub_on_message(client, userdata, msg):
        """
          callback to append messages received to new queue.
          MQTT only supports v03 messages, so always assumed to be JSON encoded.

          FIXME: locking here is expensive... would like to group them ... 1st draft.
             could do a rotating set of batch size lists, and that way just change counters.
             and not lock individual messages  list[1], list[2], ... consumer consumes old lists...
             no locking needed, except to increment list index.... later.
        """

        if userdata.o['messageDebugDump']:
            logger.info("Message received: %d, %s %s" %
                        (msg.mid, msg.topic, msg.payload))

        userdata.new_message_mutex.acquire()
        client.received_messages.append(msg)
        userdata.new_message_mutex.release()

    def putCleanUp(self):
        self.client.disconnect()
        self.client.loop_stop()
        pass

    def getCleanUp(self):

        if (not ('no' in self.o)
                or self.o['no'] == 0) and 'instances' in self.o:
            props = Properties(PacketTypes.CONNECT)
            props.SessionExpiryInterval = 1
            logger.info('cleanup sessions for instances')
            for i in range(1,self.o['instances']+1):
                icid= self.o['queueName'] + '%02d' % i 
                myclient = self.__clientSetup( self.o, icid )
                myclient.connect( self.broker.url.hostname, port=self.__sslClientSetup(), \
                   myclean_start=True, properties=props )
                while not self.client.is_connected():
                    myclient.loop(0.1)
                myclient.disconnect()
                logger.info('instance deletion for %02d done' % i)

        self.client.disconnect()
        self.client.loop_stop()
        pass

    def _msgDecode(self, mqttMessage) -> sarracenia.Message:
        """
           decode MQTT message (protocol specific thingamabob) into sr3 one (python dictionary)
        """
        subtopic = mqttMessage.topic.replace('%23',
                                             '#').replace('%2b',
                                                          '+').split('/')
        self.metrics['rxByteCount'] += len(mqttMessage.payload)
        try:
            message = Encoding.importAny( 
                mqttMessage.payload, 
                None, # headers
                mqttMessage.properties.ContentType,  
                subtopic,
                self.o['topicPrefix'] )

        except Exception as ex:
            logger.error("ignored malformed message: %s" % mqttMessage.payload)
            logger.error("decode error: %s" % ex)
            logger.error('Exception details: ', exc_info=True)
            self.metrics['rxBadCount'] += 1
            return None

        if subtopic[0] != self.o['topicPrefix'][0]:
            message['exchange'] = subtopic[0]
            message['subtopic'] = subtopic[1 + len(self.o['topicPrefix']):]
        else:
            message['subtopic'] = subtopic[len(self.o['topicPrefix']):]
        message['ack_id'] = mqttMessage.mid
        message['local_offset'] = 0
        message['_deleteOnPost'] = set(
            ['exchange', 'local_offset', 'ack_id', 'subtopic'])

        if message.validate():
            self.metrics['rxGoodCount'] += 1
            return message
        else:
           self.metrics['rxBadCount'] += 1
           self.client.ack(message['ack_id'])
           logger.error('message acknowledged and discarded: %s' % message)
           return None

    def newMessages(self, blocking=False) -> list:
        """
           return new messages.

           FIXME: hate the locking... too fine grained, especially in on_message... just a 1st shot.

        """
        if blocking:
            ebo = 0.1
            while len(self.client.received_messages) == 0:
                logger.debug('blocked: no messages available')
                time.sleep(ebo)
                if ebo < 10:
                    ebo *= 2

        self.new_message_mutex.acquire()

        if len(self.client.received_messages) > self.o['batch']:
            mqttml = self.client.received_messages[0:self.o['batch']]
            self.client.received_messages = self.client.received_messages[
                self.o['batch']:]
        else:
            mqttml = self.client.received_messages
            self.client.received_messages = []

        self.new_message_mutex.release()

        ml = list(filter(None, map(self._msgDecode, mqttml)))
        return ml

    def getNewMessage(self, blocking=False) -> sarracenia.Message:

        if blocking:
            ebo = 0.1
            while len(self.client.received_messages) == 0:
                logger.debug('blocked: no messages available')
                time.sleep(ebo)
                if ebo < 10:
                    ebo *= 2

        self.new_message_mutex.acquire()

        if len(self.client.received_messages) > 0:
            m = self.client.received_messages[0]
            self.client.received_messages = self.client.received_messages[1:]
        else:
            m = None
        self.new_message_mutex.release()

        if m:
            return self._msgDecode(m)
        else:
            return None

    def ack(self, m) -> None:
        if (not self.auto_ack) and ('ack_id' in m):
            logger.info('mid=%d' % m['ack_id'])
            self.client.ack(m['ack_id'])
            del m['ack_id']
            m['_deleteOnPost'].remove('ack_id')

    def putNewMessage(self,
                      body,
                      content_type='application/json',
                      exchange=None) -> bool:
        """
          publish a message.
        """
        if self.is_subscriber:  #build_consumer
            logger.error("publishing from a consumer")
            return False

        if '_deleteOnPost' in body:
            # FIXME: need to delete because building entire JSON object at once.
            # makes this routine alter the message. Ideally, would use incremental
            # method to build json and _deleteOnPost would be a guide of what to skip.
            # library for that is jsonfile, but not present in repos so far.
            for k in body['_deleteOnPost']:
                if k == 'subtopic': continue
                if k in body:
                    del body[k]
            del body['_deleteOnPost']

        if not exchange:
            if (type(self.o['exchange']) is list):
                if (len(self.o['exchange']) > 1):
                    if 'post_exchangeSplit' in self.o:
                        # FIXME: assert ( len(self.o['exchange']) == self.o['post_exchangeSplit'] )
                        #        if that isn't true... then there is something wrong... should we check ?
                        idx = sum(
                            bytearray(body['integrity']['value'],
                                      'ascii')) % len(self.o['exchange'])
                        exchange = self.o['exchange'][idx]
                    else:
                        logger.error(
                            'do not know which exchange to publish to: %s' %
                            self.o['exchange'])
                        return
                else:
                    exchange = self.o['exchange'][0]
            else:
                exchange = self.o['exchange']

        # FIXME: might
        topic = '/'.join([exchange] + self.o['topicPrefix'] + body['subtopic'])

        # url-quote wildcard characters in topics.
        topic = topic.replace('#', '%23')
        topic = topic.replace('+', '%2B')

        del body['subtopic']
        props = Properties(PacketTypes.PUBLISH)
        # https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901111
        props.PayloadFormatIndicator = 1  # designates UTF-8

        props.ContentType = Encoding.content_type( body['version'] )

        while True:
            try:
                raw_body = Encoding.exportAny( body, body['version'] )
                if self.o['messageDebugDump']:
                     logger.info("Message to publish: %s %s" % (topic, raw_body))
                        
                self.metrics['txByteCount'] += len(raw_body)
                info = self.client.publish(topic=topic,
                                           payload=raw_body,
                                           qos=1,
                                           properties=props)
                if info.rc == paho.mqtt.client.MQTT_ERR_SUCCESS:
                    self.pending_messages_mutex.acquire()
                    self.pending_messages.append(info.mid)
                    self.metrics['txGoodCount'] += 1
                    self.pending_messages_mutex.release()
                    logger.info("published mid={} {} to under: {} ".format(
                        info.mid, body, topic))
                    return True  #success...

            except Exception as ex:
                logger.error('Exception details: ', exc_info=True)

            self.metrics['txBadCount'] += 1
            self.close()
            self.__putSetup(self.o)

    def close(self):
        logger.info('closing')
        if self.client.is_connected():
            if self.is_subscriber and self.client.subscribe_in_progress:
                time.sleep(0.1)

            if hasattr(self, 'pending_messages'):
                while len(self.pending_messages) > 0:
                    logger.info('waiting for last messages to publish')
                    time.sleep(0.1)
                logger.info('no more pending messages')
            self.client.disconnect()
