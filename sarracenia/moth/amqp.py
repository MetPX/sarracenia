# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, 2008-2020
#
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
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

# the real AMQP library... not this one...
import amqp
import copy
import json
import uuid

import logging

import re

import sarracenia
from sarracenia.postformat import PostFormat
from sarracenia.moth import Moth
from sarracenia.interruptible_sleep import interruptible_sleep
import os

import time
from urllib.parse import unquote

logger = logging.getLogger(__name__)
"""
amqp_ss_maxlen 

the maximum length of a "short string", as per AMQP protocol, in bytes.

"""
amqp_ss_maxlen = 255

default_options = {
    'auto_delete': False,
    'batch': 25,
    'durable': True,
    'exchange': None,
    'exchangeDeclare': True,
    'expire': None,
    'logLevel': 'info',
    'persistent': True,
    'prefetch': 25,
    'queueName': None,
    'queueBind': True,
    'queueDeclare': True,
    'reset': False,
    'subtopic': [],
    'messageDebugDump': False,
    'topicPrefix': ['v03'],
    'vhost': '/',
}


class AMQP(Moth):
    """
       implementation of the Moth API for the amqp library, which is built to talk to rabbitmq brokers in 0.8 and 0.9
       AMQP dialects.

       to allow acknowledgements we map: AMQP' 'delivery_tag' to the 'ack_id'

       additional AMQP specific options:

       exchangeDeclare  - declare exchanges before use.
       queueBind        - bind queue to exchange before use.
       queueDeclare     - declare queue before use.

    """

    def _msgRawToDict(self, raw_msg) -> sarracenia.Message:
        if raw_msg is not None:
            body = raw_msg.body

            if self.o['messageDebugDump']:
                logger.info('raw message start')
                if not ('content_type' in raw_msg.properties):
                    logger.warning('message is missing content-type header')
                if body:
                    logger.info('body: type: %s (%d bytes) %s' %
                             (type(body), len(body), body))
                else:
                    logger.info('had no body')
                if raw_msg.headers:
                    logger.info('headers: type: %s (%d elements) %s' %
                             (type(raw_msg.headers), len(raw_msg.headers), raw_msg.headers))
                else:
                    logger.info('had no headers')
                if raw_msg.properties:
                    logger.info('properties:' % raw_msg.properties)
                else:
                    logger.info('had no properties')
                if raw_msg.delivery_info: 
                    logger.info( f"delivery info: {raw_msg.delivery_info}" )
                else:
                    logger.info('had no delivery info')
                logger.info('raw message end')



            if type(body) is bytes:
                try:
                    body = raw_msg.body.decode("utf8")
                except Exception as ex:
                    logger.error(
                        'ignoring message. UTF8 encoding expected. raw message received: %s' % ex)
                    logger.debug('Exception details: ', exc_info=True)
                    self.channel.basic_ack( raw_msg.delivery_info['delivery_tag'])
                    return None

            if 'content_type' in raw_msg.properties:
                content_type = raw_msg.properties['content_type']
            else:
                content_type = None

            msg = PostFormat.importAny( body, raw_msg.headers, content_type, self.o )
            if not msg:
                logger.error('Decode failed, discarding message')
                self.channel.basic_ack( raw_msg.delivery_info['delivery_tag'])
                return None

            topic = raw_msg.delivery_info['routing_key'].replace(
                '%23', '#').replace('%22', '*')
            msg['exchange'] = raw_msg.delivery_info['exchange']

            msg.deriveSource( self.o )
            msg.deriveTopics( self.o, topic )

            # keep track of which connection and channel the msg came from
            msg['ack_id'] = { 'delivery_tag':  raw_msg.delivery_info['delivery_tag'], 
                              'channel_id':    raw_msg.channel.channel_id, 
                              'connection_id': self.connection_id,
                              'broker':        self.broker,
                            }
            msg['local_offset'] = 0
            msg['_deleteOnPost'] |= set( ['ack_id', 'exchange', 'local_offset', 'subtopic'])
            if not msg.validate():
                if hasattr(self,'channel'):
                    self.channel.basic_ack(msg['ack_id']['delivery_tag'])
                logger.error('message acknowledged and discarded: %s' % msg)
                msg = None
        else:
            msg = None

        return msg

    # length of an AMQP short string (used for headers and many properties)
    amqp_ss_maxlen = 255

    def __init__(self, props, is_subscriber) -> None:
        """
           connect to broker, depending on message_strategy stubborness, remain connected.
           
        """

        super().__init__(props, is_subscriber)

        self.last_qDeclare = time.time()

        logging.basicConfig(
            format=
            '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s')

        self.o = copy.deepcopy(default_options)
        self.o.update(props)

        self.first_setup = True
        self._stop_requested = False

        me = "%s.%s" % (__class__.__module__, __class__.__name__)

        if ('settings' in self.o) and (me in self.o['settings']):
            for s in self.o['settings'][me]:
                self.o[s] = self.o['settings'][me][s]

            if 'logLevel' in self.o['settings'][me]:
                logger.setLevel(self.o['logLevel'].upper())

        self.connection = None
        self.connection_id = None
        self.broker = None

    def __connect(self, broker) -> bool:
        """
          connect to broker. 
          returns True if connected, false otherwise.
          * side effect: self.channel set to a new channel.

          Expect caller to handle errors.
        """
        if broker.url.hostname:
            host = broker.url.hostname
            if broker.url.port is None:
                if (broker.url.scheme[-1] == 's'):
                    host += ':5671'
                else:
                    host += ':5672'
            else:
                host += ':{}'.format(broker.url.port)
        else:
            logger.critical( f"invalid broker specification: {broker} " )
            return False

        # if needed, set the vhost using the broker URL's path
        vhost = self.o['vhost']
        # if the URL path is '/' or '', no vhost is specified and the default vhost from self.o
        # will be used. Otherwise, strip off leading or trailing slashes.
        if broker.url.path != '/' and broker.url.path != '':
            vhost = broker.url.path.strip('/')

        self.connection = amqp.Connection(host=host,
                                          userid=broker.url.username,
                                          password=unquote(
                                              broker.url.password),
                                          login_method=broker.login_method,
                                          virtual_host=vhost,
                                          ssl=(broker.url.scheme[-1] == 's'))
        self.connection_id = str(uuid.uuid4()) + ("_sub" if self.is_subscriber else "_pub")
        self.broker = host + '/' + vhost
        if hasattr(self.connection, 'connect'):
            # check for amqp 1.3.3 and 1.4.9 because connect doesn't exist in those older versions
            self.connection.connect()

        self.management_channel = self.connection.channel(1)
        self.channel = self.connection.channel(2)
        return True

    def metricsReport(self):

        if 'no' in self.o and self.o['no'] < 2 and self.is_subscriber and self.connection and self.connection.connected:
            # control frequency of checks for queue size. hardcoded for now.
            next_time = self.last_qDeclare + 30
            now=time.time()
            if next_time <= now:
                self._queueDeclare(passive=True)
                self.last_qDeclare=now

        super().metricsReport()

        return self.metrics

    def _queueDeclare(self,passive=False) ->  int:

        try:
            # from sr_consumer.build_connection...
            if not self.connection or not self.connection.connected:
                if not self.__connect(self.o['broker']):
                    logger.critical('could not connect')
                    if hasattr(self,'metrics'):
                        self.metrics['brokerQueuedMessageCount'] = -2
                    return -2

            #FIXME: test self.first_setup and props['reset']... delete queue...
            broker_str = self.o['broker'].url.geturl().replace(
                ':' + self.o['broker'].url.password + '@', '@')

            if self.o['queueDeclare'] and self.o['queueName']:

                args = {}
                if self.o['expire']:
                    x = int(self.o['expire'] * 1000)
                    if x > 0: args['x-expires'] = x
                if self.o['messageAgeMax']:
                    x = int(self.o['messageAgeMax'] * 1000)
                    if x > 0: args['x-message-ttl'] = x

                #FIXME: conver expire, message_ttl to proper units.
                if self.o['dry_run']:
                    logger.info('queue declare (dry run) %s (as: %s) ' %
                            (self.o['queueName'], broker_str))
                    msg_count=0
                else:
                    qname, msg_count, consumer_count = self.management_channel.queue_declare(
                        self.o['queueName'],
                        passive=passive,
                        durable=self.o['durable'],
                        exclusive=False,
                        auto_delete=self.o['auto_delete'],
                        nowait=False,
                        arguments=args)
                    if not passive:
                        logger.info( f"queue declared {self.o['queueName']} (as: {broker_str}), (messages waiting: {msg_count})" )

                if hasattr(self,'metrics'):
                   self.metrics['brokerQueuedMessageCount'] = msg_count
                return msg_count

        except Exception as err:
            logger.error(
                    f'connecting to: {self.o["queueName"]}, durable: {self.o["durable"]}, expire: {self.o["expire"]}, auto_delete={self.o["auto_delete"]}'
                )
            logger.error("AMQP getSetup failed to {} with {}".format(
                    self.o['broker'].url.hostname, err))
            logger.debug('Exception details: ', exc_info=True)

        if hasattr(self,'metrics'):
            self.metrics['brokerQueuedMessageCount'] = -1
        return -1


    def getSetup(self) -> None:
        """
        Setup so we can get messages.

        if message_strategy is stubborn, will loop here forever.
             connect, declare queue, apply bindings.
        """
        ebo = 1

        while True:
            
            if self._stop_requested:
                break

            if 'broker' not in self.o or self.o['broker'] is None:
                logger.critical( f"no broker given" )
                break

            # It does not really matter how it fails, the recovery approach is always the same:
            # tear the whole thing down, and start over.
            try:
                # from sr_consumer.build_connection...
                if not self.__connect(self.o['broker']):
                    logger.critical('could not connect')
                    break

                # only first/lead instance needs to declare a queue and bindings.
                if 'no' in self.o and self.o['no'] >= 2:
                    self.metricsConnect()
                    return

                #logger.info('getSetup connected to {}'.format(self.o['broker'].url.hostname) )

                if self.o['prefetch'] != 0:
                    self.channel.basic_qos(0, self.o['prefetch'], True)

                #FIXME: test self.first_setup and props['reset']... delete queue...
                broker_str = self.o['broker'].url.geturl().replace(
                    ':' + self.o['broker'].url.password + '@', '@')

                # from Queue declare
                msg_count = self._queueDeclare()
                
                if msg_count == -2: break

                if self.o['queueBind'] and self.o['queueName']:
                    for tup in self.o['bindings']:
                        exchange, prefix, subtopic = tup
                        topic = '.'.join(prefix + subtopic)
                        if self.o['dry_run']:
                            logger.info('binding (dry run) %s with %s to %s (as: %s)' % \
                                ( self.o['queueName'], topic, exchange, broker_str ) )
                        else:
                            logger.info('binding %s with %s to %s (as: %s)' % \
                                ( self.o['queueName'], topic, exchange, broker_str ) )
                            if exchange:
                                self.management_channel.queue_bind(self.o['queueName'], exchange,
                                                topic)

                # Setup Successfully Complete!
                self.metricsConnect()
                logger.debug('getSetup ... Done!')
                break

            except Exception as err:
                logger.error(
                    f'connecting to: {self.o["queueName"]}, durable: {self.o["durable"]}, expire: {self.o["expire"]}, auto_delete={self.o["auto_delete"]}'
                )
                logger.error("AMQP getSetup failed to {} with {}".format(
                    self.o['broker'].url.hostname, err))
                logger.debug('Exception details: ', exc_info=True)

            if not self.o['message_strategy']['stubborn']: return

            if ebo < 60: ebo *= 2

            logger.info("Sleeping {} seconds ...".format(ebo))
            interruptible_sleep(ebo, obj=self)

    def putSetup(self) -> None:

        ebo = 1

        while True:

            # It does not really matter how it fails, the recovery approach is always the same:
            # tear the whole thing down, and start over.
            try:
                if self._stop_requested:
                    break

                if self.o['broker'] is None:
                    logger.critical( f"no broker given" )
                    break

                if not self.__connect(self.o['broker']):
                    logger.critical('could not connect')
                    break

                # transaction mode... confirms would be better...
                self.channel.tx_select()
                broker_str = self.o['broker'].url.geturl().replace(
                    ':' + self.o['broker'].url.password + '@', '@')

                #logger.debug('putSetup ... 1. connected to {}'.format(broker_str ) )

                if self.o['exchangeDeclare']:
                    logger.debug('putSetup ... 1. declaring {}'.format(
                        self.o['exchange']))
                    if type(self.o['exchange']) is not list:
                        self.o['exchange'] = [self.o['exchange']]
                    for x in self.o['exchange']:
                        if self.o['dry_run']:
                            logger.info('exchange declare (dry run): %s (as: %s)' %
                                    (x, broker_str))
                        else:
                            self.channel.exchange_declare(
                                x,
                                'topic',
                                auto_delete=self.o['auto_delete'],
                                durable=self.o['durable'])
                            logger.info('exchange declared: %s (as: %s)' %
                                    (x, broker_str))

                # Setup Successfully Complete!
                self.metricsConnect()
                logger.debug('putSetup ... Done!')
                break

            except Exception as err:
                logger.error(
                    "AMQP putSetup failed to connect or declare exchanges {}@{} on {}: {}"
                    .format(self.o['exchange'], self.o['broker'].url.username,
                            self.o['broker'].url.hostname, err))
                logger.debug('Exception details: ', exc_info=True)

            if not self.o['message_strategy']['stubborn']: return

            if ebo < 60: ebo *= 2

            self.close()
            logger.info("Sleeping {} seconds ...".format(ebo))
            interruptible_sleep(ebo, obj=self)

    def putCleanUp(self) -> None:

        try:
            for x in self.o['exchange']:
                try:
                    if self.o['dry_run']:
                        logger.info("deleted exchange (dry run): %s (if unused)" % x)
                    else:
                        if hasattr(self,'channel'):
                            self.channel.exchange_delete(x, if_unused=True)
                        logger.info("deleted exchange: %s" % x)
                except amqp.exceptions.PreconditionFailed as err:
                    err_msg = str(err).replace("Exchange.delete: (406) PRECONDITION_FAILED - exchange ", "")
                    logger.warning("failed to delete exchange: %s" % err_msg)
        except Exception as err:
            logger.error("failed on {} with {}".format(
                self.o['broker'].url.hostname, err))
            logger.debug('Exception details: ', exc_info=True)

    def getCleanUp(self) -> None:

        try:
            if self.o['dry_run']:
                logger.info("deleting queue (dry run) %s" % self.o['queueName'] )
            else:
                logger.info("deleting queue %s" % self.o['queueName'] )
                if hasattr(self,'channel'):
                    self.channel.queue_delete(self.o['queueName'])
        except Exception as err:
            logger.error("failed to {} with {}".format(
                self.o['broker'].url.hostname, err))
            logger.debug('Exception details: ', exc_info=True)

    def newMessages(self) -> list:

        if not self.is_subscriber:  #build_consumer
            logger.error("getting from a publisher")
            return []

        ml = []
        m = self.getNewMessage()
        if m is not None:
            fetched = 1
            ml.append(m)
            while fetched < self.o['batch']:
                m = self.getNewMessage()
                if m is None:
                    break
                ml.append(m)
                fetched += 1

        return ml

    def getNewMessage(self) -> sarracenia.Message:

        if not self.is_subscriber:  #build_consumer
            logger.error("getting from a publisher")
            return None

        try:
            if not self.connection:
                self.getSetup()

            raw_msg = self.channel.basic_get(self.o['queueName'])
            if (raw_msg is None) and (self.connection.connected):
                return None
            else:
                self.metrics['rxByteCount'] += len(raw_msg.body)
                try: 
                    msg = self._msgRawToDict(raw_msg)
                except Exception as err:
                    logger.error("message decode failed. raw message: %s" % raw_msg.body )
                    logger.debug('Exception details: ', exc_info=True)
                    msg = None
                if msg is None:
                    self.metrics['rxBadCount'] += 1
                    return None
                else:
                    self.metrics['rxGoodCount'] += 1
                self.metrics['rxLast'] = sarracenia.nowstr()
                if hasattr(self.o, 'fixed_headers'):
                    for k in self.o.fixed_headers:
                        msg[k] = self.o.fixed_headers[k]

                logger.debug("new msg: %s" % msg)
                return msg
        except Exception as err:
            logger.warning("failed %s: %s" %
                           (self.o['queueName'], err))
            logger.debug('Exception details: ', exc_info=True)

        if not self.o['message_strategy']['stubborn']:
            return None

        logger.warning('lost connection to broker')
        self.close()
        time.sleep(1)
        return None

    def ack(self, m: sarracenia.Message) -> None:
        """
           do what you need to acknowledge that processing of a message is done.
           NOTE: AMQP delivery tags (we call them ack_id) are scoped per channel. "Deliveries must be 
           acknowledged on the same channel they were received on. Acknowledging on a different channel 
           will result in an "unknown delivery tag" protocol exception and close the channel."
        """
        if not self.is_subscriber:  #build_consumer
            logger.error("getting from a publisher")
            return False

        # silent success. retry messages will not have an ack_id, and so will not require acknowledgement.
        if not 'ack_id' in m:
            #logger.warning( f"no ackid present" )
            return True

        # when the connection/channel/broker doesn't match the current, don't attempt to ack, it will fail
        if (m['ack_id']['connection_id'] != self.connection_id
            or m['ack_id']['channel_id'] != self.channel.channel_id
            or m['ack_id']['broker'] != self.broker):
            logger.warning(f"failed for {m['ack_id']}. Does not match the current connection {self.connection_id}," +
                           f" channel {self.channel.channel_id} or broker {self.broker}")
            del m['ack_id']
            m['_deleteOnPost'].remove('ack_id')
            return False
        
        #logger.info( f"acknowledging {m['ack_id']}" )
        ebo = 1
        while True:
            try:
                if hasattr(self, 'channel'): 
                    self.channel.basic_ack(m['ack_id']['delivery_tag'])
                    del m['ack_id']
                    m['_deleteOnPost'].remove('ack_id')
                    return True
                else:
                    logger.warning(f"Can't ack {m['ack_id']}, don't have a channel")
                    del m['ack_id']
                    m['_deleteOnPost'].remove('ack_id')
                    return False
            
            except Exception as err:
                logger.warning("failed for tag: %s: %s" % (m['ack_id'], err))
                logger.debug('Exception details: ', exc_info=True)
                if type(err) == BrokenPipeError or type(err) == ConnectionResetError:
                    # Cleanly close partially broken connection
                    self.close()
                    # No point in trying to ack again if the connection is broken
                    del m['ack_id']
                    m['_deleteOnPost'].remove('ack_id')
                    return False
            
            if ebo < 60:
                ebo *= 2
            logger.info("Sleeping {} seconds before re-trying ack...".format(ebo))
            interruptible_sleep(ebo, obj=self)
            # TODO maybe implement message strategy stubborn here and give up after retrying?

    def putNewMessage(self,
                      message: sarracenia.Message,
                      content_type: str = 'application/json',
                      exchange: str = None ) -> bool:
        """
        put a new message out, to the configured exchange by default.
        """

        if self.is_subscriber:  #build_consumer
            logger.error("publishing from a consumer")
            return False

        # Check connection and channel status, try to reconnect if not connected
        if (not self.connection) or (not self.connection.connected) or (not self.channel.is_open):
            try:
                self.close()
                self.putSetup()
            except Exception as err:
                logger.warning(f"failed, connection was closed/broken and could not be re-opened {exchange}: {err}")
                logger.debug('Exception details: ', exc_info=True)
                return False

        # The caller probably doesn't expect the message to get modified by this method, so use a copy of the message
        body = copy.deepcopy(message)

        version = body['_format']


        if '_deleteOnPost' in body:
            # FIXME: need to delete because building entire JSON object at once.
            # makes this routine alter the message. Ideally, would use incremental
            # method to build json and _deleteOnPost would be a guide of what to skip.
            # library for that is jsonfile, but not present in repos so far.
            for k in body['_deleteOnPost']:
                if k in body:
                    del body[k]
            del body['_deleteOnPost']

        if not exchange:
            if (type(self.o['exchange']) is list):
                if (len(self.o['exchange']) > 1):
                    if ( 'exchangeSplit' in self.o) and self.o['exchangeSplit'] > 1:
                        # FIXME: assert ( len(self.o['exchange']) == self.o['post_exchangeSplit'] )
                        #        if that isn't true... then there is something wrong... should we check ?
                        if 'exchangeSplitOverride' in message:
                            idx = int(message['exchangeSplitOverride'])%len(self.o['exchange'])
                        else:
                            idx = sum( bytearray(body['identity']['value'],
                                      'ascii')) % len(self.o['exchange'])
                        
                        exchange = self.o['exchange'][idx]
                    else:
                        logger.error(
                            'do not know which exchange to publish to: %s' %
                            self.o['exchange'])
                        return False
                else:
                    exchange = self.o['exchange'][0]
            else:
                exchange = self.o['exchange']

        if self.o['messageAgeMax']:
            ttl = "%d" * int(
                sarracenia.durationToSeconds(self.o['messageAgeMax']) * 1000)
        else:
            ttl = "0"
        
        if 'persistent' in self.o:
            deliv_mode = 2 if self.o['persistent'] else 1
        else:
            deliv_mode = 2

        raw_body, headers, content_type = PostFormat.exportAny( body, version, self.o['topicPrefix'], self.o )

        topic = '.'.join(headers['topic'])
        topic = topic.replace('#', '%23')
        topic = topic.replace('*', '%22')

        if len(topic) >= 255:  # ensure topic is <= 255 characters
            logger.error("message topic too long, truncating")
            mxlen = amqp_ss_maxlen
            while (topic.encode("utf8")[mxlen - 1] & 0xc0 == 0xc0):
                mxlen -= 1
            topic = topic.encode("utf8")[0:mxlen].decode("utf8")

        if self.o['messageDebugDump']:
            logger.info('raw message body: version: %s type: %s %s' %
                             (version, type(raw_body),  raw_body))
            logger.info('raw message headers: type: %s value: %s' % (type(headers),  headers))

        message['post_topic'] = topic
        message['post_exchange'] = exchange
        message['_deleteOnPost'] |= set( ['post_exchange', 'post_topic'] )
        del headers['topic']

        if headers :  
            for k in headers:
                if (type(headers[k]) is str) and (len(headers[k]) >=
                                                      amqp_ss_maxlen):
                    logger.error("message header %s too long, dropping" % k)
                    return False

        AMQP_Message = amqp.Message(raw_body,
                                        content_type=content_type,
                                        application_headers=headers,
                                        expire=ttl,
                                        delivery_mode=deliv_mode)
        self.metrics['txByteCount'] += len(raw_body) 
        if headers:
            self.metrics['txByteCount'] += len(''.join(str(headers)))
        self.metrics['txLast'] = sarracenia.nowstr()

        # timeout option is a float and default is 0.0. basic_publish wants int or None for no timeout
        try:
            if self.o['timeout']:
                pub_timeout = int(self.o['timeout'])
            else:
                pub_timeout = None
        except Exception as err:
            logger.debug('Set pub_timeout to None. Exception details: ', exc_info=True)
            pub_timeout = None

        body=raw_body
        ebo = 1
        try:
            logger.debug( f"trying to publish body: {body} headers: {headers} to {exchange} under: {topic} " )
            self.channel.basic_publish(AMQP_Message, exchange, topic, timeout=pub_timeout)
            # Issue #732: tx_commit can get stuck forever
            self.channel.tx_commit()
            logger.debug("published body: {} headers: {} to {} under: {} ".format(
                          body, headers, exchange, topic))
            self.metrics['txGoodCount'] += 1
            return True  # no failure == success :-)

        except Exception as err:
            logger.warning("failed %s: %s" % (exchange, err))
            logger.debug('Exception details: ', exc_info=True)

            self.metrics['txBadCount'] += 1
            # Issue #466: commenting this out until message_strategy stubborn is working correctly (Issue #537)
            # Always return False when an error occurs and use the DiskQueues to retry, instead of looping. This should
            # eventually be configurable with message_strategy stubborn
            # if True or not self.o['message_strategy']['stubborn']:
            #     return False

            self.close()
            return False # instead of looping

    def close(self) -> None:
        try:
            if self.connection:
                self.connection.collect()
                self.connection.close()

        except Exception as err:
            logger.error("sr_amqp/close 2: {}".format(err))
            logger.debug("sr_amqp/close 2 Exception details:", exc_info=True)
        # FIXME toclose not useful as we don't close channels anymore
        self.metricsDisconnect()
        self.connection = None
        self.connection_id = None
        self.broker = None
