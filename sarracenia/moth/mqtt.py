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
from sarracenia.postformat import PostFormat
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
    'max_inflight_messages': 20000, # https://pypi.org/project/paho-mqtt/ ... says default is 20, raised because of data loss
    #'max_queued_messages' : 20000,
    'no': 0,
    'prefetch': 25,
    #'receiveMaximum': 65535, # https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Receive_Maximum
    'topicPrefix': ['v03']
}

class MQTT(Moth):
    """
       Message Queue Telemetry Transport support.
           talks to an MQTT broker.  Tested with mosquitto. requires MQTTv5

       Sarracenia Concept mapping from AMQP:

           Only supports v03 messages since mqtt3.1 has no headers.


           AMQP -> MQTT topic hierarcy mapping: 
           exchange: xpublic,  topic prefix:   v03 subtopic:   /my/favourite/directory
           results in :   xpublic/v03/my/favourite/directory

           AMQP queue -> MQTT group-id (queue maps to queue, client-id should map to  queue+instance, I think.)

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
           it to the rx_msg data structure (protected by a mutex.)
           if the application crashes, the rx_msg have not been ack'd to the sender... so it is
           likely that you will just get them later... could use for a shelf for rx_msg,
           and sync it once in while... probably not worth it.
 

      References:
         good discussion of shared subscriptions:
          https://www.hivemq.com/blog/mqtt5-essentials-part7-shared-subscriptions/#:~:text=Shared%20subscriptions%20are%20an%20MQTT,is%20sent%20to%20that%20topic.


    """
    def __init__(self, broker, options, is_subscriber):
        """

          MQTT connection instances...
          in AMQP: topic separator is dot (.) in MQTT, the topic separator is slash (/)
          have exchange arguments use protocol specific separator or mapped one?

        """

        super().__init__(broker, options, is_subscriber)

        self.connected=False
        # setting this is wrong and breaks things, was already set in super-class init, doing this here overwites
        #  interpretation of options done in superclass.
        #self.o = options
        self.o.update(default_options)
        self.o.update(options)

        if 'qos' in self.o:
            if type(self.o['qos']) is not int:
                self.o['qos'] = int(self.o['qos'])
        else:
            self.o['qos'] = 1


        me = "%s.%s" % (__class__.__module__, __class__.__name__)
        logger.setLevel('WARNING')

        if ('settings' in self.o) and (me in self.o['settings']):
            for s in self.o['settings'][me]:
                self.o[s] = self.o['settings'][me][s]

            if 'logLevel' in self.o['settings'][me]:
                logger.setLevel(self.o['logLevel'].upper())

        self.proto_version = paho.mqtt.client.MQTTv5

        if 'receiveMaximum' in self.o and type(self.o['receiveMaximum']) is not int:
            self.o['receiveMaximum'] = min( int( self.o['receiveMaximum'] ), 65535 )

        if 'max_inflight_messages' in self.o and type(self.o['max_inflight_messages']) is not int:
            self.o['max_inflight_messages'] = int( self.o['max_inflight_messages'] )

        if 'max_queued_messages' in self.o and type(self.o['max_queued_messages']) is not int:
            self.o['max_queued_messages'] = int( self.o['max_queued_messages'] )

        if is_subscriber:
            self.subscribe_mutex = threading.Lock()
            self.subscribe_mutex.acquire()
            self.subscribe_in_progress = 0
            self.subscribe_mutex.release()

            self.rx_msg_mutex = threading.Lock()
            self.rx_msg_mutex.acquire()
            self.rx_msg_iToApp=0
            self.rx_msg_iFromBroker=1
            self.rx_msg_iMax=4
            self.rx_msg={}
            self.rx_msg[0]=[]
            self.rx_msg[1]=[]
            self.rx_msg[2]=[]
            self.rx_msg[3]=[]
            self.rx_msg[4]=[]
            self.rx_msg_mutex.release()
            self.__getSetup()
        else:
            self.__putSetup()

        logger.warning("note: mqtt support is newish, not very well tested")

    def __sub_on_disconnect(client, userdata, rc, properties=None):
        userdata.metricsDisconnect()
        logger.debug(paho.mqtt.client.connack_string(rc))
        if hasattr(userdata, 'pending_publishes'):
            lost = len(userdata.pending_publishes)
            if lost > 0:
                logger.error(
                    'message loss! cannot confirm %d messages were published: mids=%s'
                    % (lost, userdata.pending_publishes))
            else:
                logger.info('clean. no published messages lost.')

    def __sub_on_connect(client, userdata, flags, rc, properties=None):
        logger.debug("client=%s rc=%s, flags=%s" %
                    (client, paho.mqtt.client.connack_string(rc), flags))

        if flags['session present'] != 1:
            logger.debug(
                'no existing session, no recovery of inflight messages from previous connection'
            )

        userdata.connect_in_progress = False
        if rc != paho.mqtt.client.MQTT_ERR_SUCCESS:
            logger.error("failed to establish connection")
            return

        # FIXME: enhancement could subscribe accepts multiple (subj, qos) tuples so, could do this in one RTT.
        userdata.subscribe_mutex.acquire()
        for binding_tuple in userdata.o['bindings']:
            exchange, prefix, subtopic = binding_tuple
            logger.info("tuple: %s %s %s" % (exchange, prefix, subtopic))
            subj = '/'.join(['$share', userdata.o['queueName'], exchange] +
                            prefix + subtopic)
            (res, mid) = client.subscribe(subj, qos=userdata.o['qos'])
            userdata.subscribe_in_progress += 1
            logger.info( "asked to subscribe to: %s, mid=%d qos=%s result: %s" % (subj, mid, \
                userdata.o['qos'], paho.mqtt.client.error_string(res)) )
        userdata.subscribe_mutex.release()
        userdata.metricsConnect()


    def __sub_on_subscribe(client,
                           userdata,
                           mid,
                           granted_qos,
                           properties=None):
        userdata.subscribe_mutex.acquire()
        logger.info("client: {} subscribe completed mid={} granted_qos={}".format(
            client._client_id, mid, list(map(lambda x: x.getName(), granted_qos))))
        userdata.subscribe_in_progress -= 1
        userdata.subscribe_mutex.release()

    def __pub_on_disconnect(client, userdata, rc, properties=None):
        userdata.metricsDisconnect()
        logger.info(paho.mqtt.client.connack_string(rc))

    def __pub_on_connect(client, userdata, flags, rc, properties=None):
        userdata.connect_in_progress = False
        userdata.metricsConnect()
        logger.info(paho.mqtt.client.connack_string(rc))

    def __pub_on_publish(client, userdata, mid):

        if mid in userdata.pending_publishes:
            logger.info('publish complete. mid={}'.format(mid))
            # FIXME: worried... not clear if dequeue remove is thread safe.
            userdata.pending_publishes.remove(mid)
        else:
            userdata.unexpected_publishes.append(mid)
            logger.info( 'BUG: ack for message we do not know we published. mid={}'.  format(mid))

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

    def __clientSetup(self, cid) -> paho.mqtt.client.Client:

        self.connect_in_progress = True

        client = paho.mqtt.client.Client( userdata=self, \
            client_id=cid, protocol=paho.mqtt.client.MQTTv5 )

        client.connected = False
        client.on_connect = MQTT.__sub_on_connect
        client.on_disconnect = MQTT.__sub_on_disconnect
        client.on_message = MQTT.__sub_on_message
        client.on_subscribe = MQTT.__sub_on_subscribe
        # defaults to 20... kind of a mix of "batch" and prefetch...
        if 'max_inflight_messages' in self.o:
            client.max_inflight_messages_set(self.o['max_inflight_messages'])

        client.username_pw_set(self.broker.url.username,
                               unquote(self.broker.url.password))
        return client

    def __getSetup(self):
        """
           Establish a connection to consume messages with.  
        """
        ebo = 1
        self.connected=False
        while True:
            try:

                cs = self.o['clean_session']
                if ('queueName' in self.o) and ('no' in self.o):
                    cid = self.o['queueName'] + "_i%02d" % self.o['no']
                else:
                    #cid = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
                    cid = None
                    cs = True
                    logger.info( f" cid=+{cid}+"  )

                props = Properties(PacketTypes.CONNECT)
                if 'expire' in self.o and self.o['expire']:
                    props.SessionExpiryInterval = int(self.o['expire'])
                if 'receiveMaximum' in self.o:
                    props.ReceiveMaximum = self.o['receiveMaximum']

                logger.info( f"is no around? {self.o['no']} " )
                if ('no' in self.o) and self.o['no'] > 0:
                    self.client = self.__clientSetup(cid)
                else:
                    if 'instances' in self.o:    
                        session_mxi=self.o['instances']+1
                    else:
                        session_mxi=2

                    for i in range(1,session_mxi ):
                        icid = self.o['queueName'] + "_i%02d" %  i
                        logger.info('declare session for instances %s' %icid)
                        decl_client = self.__clientSetup(icid)
                        decl_client.on_connect = MQTT.__sub_on_connect
                        decl_client.connect( self.broker.url.hostname, port=self.__sslClientSetup(), \
                           clean_start=False, properties=props )
                        while (self.connect_in_progress) or (self.subscribe_in_progress > 0):
                            decl_client.loop(1)
                        decl_client.disconnect()
                        decl_client.loop_stop()
                        logger.info('instance declaration for %s done' % icid)
                        return

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
                self.client.enable_logger(logger)
                self.client.loop_start()
                self.connected=True
                return

            except Exception as err:
                logger.error("failed to {} with {}".format(
                    self.broker.url.hostname, err))
                logger.error('Exception details: ', exc_info=True)

            if ebo < 60: ebo *= 2
            time.sleep(ebo)

    def __putSetup(self):
        """
           establish a connection to allow publishing. 
        """
        ebo = 1
        self.connected=False
        while True:
            try:
                self.pending_publishes = collections.deque()
                self.unexpected_publishes = collections.deque()

                props = Properties(PacketTypes.CONNECT)
                if self.o['message_ttl'] > 0:
                    props.MessageExpiryInterval = int(self.o['message_ttl'])


                self.client = paho.mqtt.client.Client(
                    protocol=self.proto_version, userdata=self)

                self.client.enable_logger(logger)
                self.client.on_connect = MQTT.__pub_on_connect
                self.client.on_disconnect = MQTT.__pub_on_disconnect
                self.client.on_publish = MQTT.__pub_on_publish
                if 'max_queued_messages' in self.o:
                    self.client.max_queued_messages_set(self.o['max_queued_messages'])

                self.client.username_pw_set(self.broker.url.username,
                                            unquote(self.broker.url.password))
                self.connect_in_progress = True
                res = self.client.connect_async(self.o['broker'].url.hostname,
                                          port=self.__sslClientSetup(),
                                          properties=props)
                logger.info('connecting to %s, res=%s' %
                            (self.o['broker'].url.hostname, res))

                self.client.loop_start()
                self.connected=True
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

          FIXME: locking here is expensive... would like to group them ... 1st draft.
             could do a rotating set of batch size lists, and that way just change counters.
             and not lock individual messages  list[1], list[2], ... consumer consumes old lists...
             no locking needed, except to increment list index.... later.
        """

        if userdata.o['messageDebugDump']:
            logger.info("Message received: id:%d, topic:%s payload:%s" %
                        (msg.mid, msg.topic, msg.payload))

        m = userdata._msgDecode(msg)
        userdata.rx_msg[userdata.rx_msg_iFromBroker].append(m)

    def putCleanUp(self):
        self.client.disconnect()
        self.client.loop_stop()
        pass

    def getCleanUp(self):

        if not ('no' in self.o):
            props = Properties(PacketTypes.CONNECT)
            props.SessionExpiryInterval = 1
            for i in range(1,self.o['instances']+1):
                icid= self.o['queueName'] + "_i%02d" % i
                logger.info('cleanup session %s' % icid )
                myclient = self.__clientSetup( icid )
                myclient.connect( self.broker.url.hostname, port=self.__sslClientSetup(), \
                   clean_start=False, properties=props )
                while self.connect_in_progress:
                    myclient.loop(0.1)
                myclient.disconnect()
                logger.info('instance deletion for %02d done' % i)

        if hasattr(self, 'client'):
            self.client.disconnect()
            self.client.loop_stop()

    def _msgDecode(self, mqttMessage) -> sarracenia.Message:
        """
           decode MQTT message (protocol specific thingamabob) into sr3 one (python dictionary)
        """
        if self.o['messageDebugDump']:
            logger.info('raw message start')
            if hasattr(mqttMessage.properties, 'ContentType'): 
                logger.info( f'Content-type: {mqttMessage.properties.ContentType}')
            else:
                logger.warning('message is missing content-type header')

            if hasattr(mqttMessage, 'payload'): 
                logger.info('payload: type: %s (%d bytes) %s' %
                             (type(mqttMessage.payload), len(mqttMessage.payload), mqttMessage.payload))

            if hasattr(mqttMessage.properties, 'UserProperty'): 
                logger.info( f'UserProperty: {mqttMessage.properties.UserProperty} ')

        self.metrics['rxByteCount'] += len(mqttMessage.payload)
        try:
            if hasattr( mqttMessage.properties, 'UserProperty'):
                headers = {}
                [ headers.update({k:v}) for k,v in mqttMessage.properties.UserProperty ]
            else:
                headers=None
            message = PostFormat.importAny( mqttMessage.payload.decode('utf-8'), headers, mqttMessage.properties.ContentType)

        except Exception as ex:
            logger.error("ignored malformed message: %s" % mqttMessage.payload)
            logger.error("decode error: %s" % ex)
            logger.error('Exception details: ', exc_info=True)
            self.metrics['rxBadCount'] += 1
            return None

        message['ack_id'] = mqttMessage.mid
        message['local_offset'] = 0
        message['_deleteOnPost'] |= set( ['exchange', 'local_offset', 'ack_id' ])

        if message.validate():
            self.metrics['rxGoodCount'] += 1
            return message
        else:
           self.metrics['rxBadCount'] += 1
           self.client.ack(message['ack_id'])
           logger.error('message acknowledged and discarded: %s' % message)
           return None

    def _rotateInputBuffers(self) -> None:
        """
           to reduce locking granularity allocate one queue to accepting messages, and a second
           one to read from. and just swap between them from time to time (kind of double buffering.)

        """
        if len(self.rx_msg[self.rx_msg_iToApp]) == 0:
            self.rx_msg_mutex.acquire()
            self.rx_msg_iToApp = self.rx_msg_iFromBroker

            if self.rx_msg_iFromBroker >= self.rx_msg_iMax:
                self.rx_msg_iFromBroker=0
            else:
                self.rx_msg_iFromBroker+=1
            time.sleep(0.1)
            self.rx_msg_mutex.release()

    def newMessages(self) -> list:
        """
           return new messages.

           FIXME: hate the locking... too fine grained, especially in on_message... just a 1st shot.

        """

        #logger.debug( f"rx_msg queue before: indices: {self.rx_msg_iToApp} {self.rx_msg_iFromBroker} " )
        #logger.debug( f"rx_msg queue before: {len(self.rx_msg[self.rx_msg_iToApp])} indices: {self.rx_msg_iToApp} {self.rx_msg_iFromBroker} " )

        if len(self.rx_msg[self.rx_msg_iToApp]) > self.o['batch']:
            mqttml = self.rx_msg[self.rx_msg_iToApp][0:self.o['batch']]
            self.rx_msg[self.rx_msg_iToApp] = self.rx_msg[self.rx_msg_iToApp][self.o['batch']:]
        elif len(self.rx_msg[self.rx_msg_iToApp]) > 0:
            mqttml = self.rx_msg[self.rx_msg_iToApp]
            self.rx_msg[self.rx_msg_iToApp] = []
        else:
            mqttml = []

        #logger.debug( f"picked up {len(mqttml)} rx_msg queue after: {len(self.rx_msg[self.rx_msg_iToApp])} ")

        self._rotateInputBuffers()

        return mqttml

    def getNewMessage(self) -> sarracenia.Message:

        if len(self.rx_msg) > 0:
            m = self.rx_msg[self.rx_msg_iToApp][0]
            self.rx_msg[self.rx_msg_iToApp] = self.rx_msg[self.rx_msg_iToApp][1:]
        else:
            m = None
        self._rotateInputBuffers()

        if m:
            return m
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

        if not self.connected:
            self.__putSetup(self.o)

        postFormat = body['_format']
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

        props.ContentType = PostFormat.content_type( postFormat )

        try:
            raw_body, headers, content_type = PostFormat.exportAny( body, postFormat )

            if headers:
                props.UserProperty=list(map( lambda x :  (x,headers[x]) , headers ))

            if self.o['messageDebugDump']:
                logger.info( f"Message to publish: topic: {topic} body type:{type(raw_body)} body:{raw_body}" )
                if hasattr(props, 'UserProperty'): 
                    logger.info( f"user_property:{props.UserProperty}" )
                    

            info = self.client.publish(topic=topic, payload=raw_body, qos=self.o['qos'], properties=props)
               
            if info.rc == paho.mqtt.client.MQTT_ERR_SUCCESS:
                if info.mid in self.unexpected_publishes:
                    self.unexpected_publishes.remove(info.mid)
                    ack_pending=False
                else:
                    self.pending_publishes.append(info.mid)
                    ack_pending=True

                self.metrics['txByteCount'] += len(raw_body)
                self.metrics['txGoodCount'] += 1
                logger.info("published mid={} ack_pending={} {} to under: {} ".format(
                    info.mid, ack_pending, body, topic))
                return True  #success...

        except Exception as ex:
            logger.error('Exception details: ', exc_info=True)
            self.metrics['txBadCount'] += 1
            self.close()
        return False

    def close(self):
        logger.info('closing')
        if hasattr(self,'client') and self.client.is_connected():
            if self.is_subscriber and self.subscribe_in_progress:
                time.sleep(0.1)

            if hasattr(self, 'pending_publishes'):
                ebo=0.1
                while  (len(self.pending_publishes)+len(self.unexpected_publishes)) >0:
                    logger.info( f'waiting {ebo} seconds for last {len(self.pending_publishes)} messages to publish')
                    if len(self.unexpected_publishes) < 10:
                        logger.info( f'messages acknowledged before publish?: {self.unexpected_publishes}')
                    if len(self.pending_publishes) < 10:
                        logger.info( f'messages awaiting publish: {self.pending_publishes}')
                    time.sleep(ebo)
                    if ebo < 64:
                        ebo *= 2
                logger.info('no more pending messages')
            self.client.disconnect()
        self.connected=False
