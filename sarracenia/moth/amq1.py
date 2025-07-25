from sarracenia.moth import Moth

import copy
import logging
import time
import threading
import queue

import sarracenia
from sarracenia.postformat import PostFormat

from proton.handlers import MessagingHandler
from proton.reactor import Container
from proton import SSLDomain
from proton import Message

logger = logging.getLogger(__name__)

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
    'queueBind': True,
    'queueDeclare': True,
    'reset': False,
    'subtopic': [],
    'messageDebugDump': False,
    'topicPrefix': ['v03'],
    'vhost': '/',
}

class Amqp1Client(MessagingHandler):
    """
        Based on https://qpid.apache.org/releases/qpid-proton-0.40.0/proton/python/examples/
        Docs: https://qpid.apache.org/releases/qpid-proton-0.40.0/proton/python/docs/index.html
    """
    def __init__(self, url: str, topics: list, msg_q: queue.Queue, is_subscriber: bool):
        super(Amqp1Client, self).__init__()
        self.url = url
        self.topics = topics
        self.msg_q = msg_q
        self.is_subscriber = is_subscriber

        self.is_connected = False # FIXME check connection.state can be UNINIT, ACTIVE, CLOSED https://qpid.apache.org/releases/qpid-proton-0.40.0/proton/python/docs/proton.html#proton.Connection.state
        self.receiver = None
        self.connection = None
        self.seq = 0

        scheme = self.url.split("://")[0].lower()
        self.__secure = scheme[-1] == 's'

    def on_start(self, event):
        """ Event loop in container has started, new receiver can be created.
        """
        if self.__secure:
            ssl_domain = SSLDomain(SSLDomain.MODE_CLIENT)
            # FIXME: currently not verifying SSL at all
            ssl_domain.set_peer_authentication(SSLDomain.ANONYMOUS_PEER)
        else:
            ssl_domain = None

        self.connection = event.container.connect(self.url, ssl_domain=ssl_domain)

        # FIXME how to subscribe to multiple topics?
        if self.is_subscriber:
            self.receiver = event.container.create_receiver(self.connection, source=self.topics[0])

    def on_message(self, event):
        """ Handle message received from broker.
        """
        msg = event.message
        self.msg_q.put(msg)
        logger.debug(f"new message pushed from broker: {msg}")

    def on_connection_opened(self, event):
        logger.info(f"connection opened {event}")
        self.is_connected = True

    def on_connection_closed(self, event):
        logger.info(f"connection closed {event}")
        self.is_connected = False

    def close(self):
        if self.receiver:
            self.receiver.close()
            self.receiver.free()
            self.receiver = None
            logger.debug("closed receiver")
        if self.connection:
            self.connection.close()
            self.connection.free()
            self.connection = None
            logger.debug("closed connection")

class Amqp1Pub(MessagingHandler):
    """
        Based on https://qpid.apache.org/releases/qpid-proton-0.40.0/proton/python/examples/
        Docs: https://qpid.apache.org/releases/qpid-proton-0.40.0/proton/python/docs/index.html
    """

    def __init__(self, url: str, topics: list, msg_q: queue.Queue, options):
        #super().__init__(default_options)
        super(Amqp1Pub, self).__init__()
        self.url = url
        self.topics = topics
        self.msg_q = msg_q

        self.is_connected = False # FIXME check connection.state can be UNINIT, ACTIVE, CLOSED https://qpid.apache.org/releases/qpid-proton-0.40.0/proton/python/docs/proton.html#proton.Connection.state
        self.sender = None
        self.connection = None
        self.sent = 0
        self.total = 1
        self.o = options

        scheme = self.url.split("://")[0].lower()
        self.host = self.url.split("://")[1]
        self.__secure = scheme[-1] == 's'

    def on_start(self, event):
        """ Event loop in container has started, new sender can be created.
        """
        if self.__secure:
            ssl_domain = SSLDomain(SSLDomain.MODE_CLIENT)
            # FIXME: currently not verifying SSL at all
            ssl_domain.set_peer_authentication(SSLDomain.ANONYMOUS_PEER)
        else:
            ssl_domain = None

        if self.o['broker'].url.username and self.o['broker'].url.password:
            self.connection = event.container.connect(self.url, user=self.o['broker'].url.username, \
                                                      password=self.o['broker'].url.password)
            logger.critical(f"Topic {self.topics}")
        else:
            self.connection = event.container.connect(self.url, ssl_domain=ssl_domain)

        # FIXME Probably need to have a guard here. Correct guard?
        self.sender = event.container.create_sender(self.connection, self.topics[0])
        logger.critical(f"Sender container initialized!")
        # event.container.declare_transaction(self.connection, handler=self)
        # self.transaction = None

    # From : https://qpid.apache.org/releases/qpid-proton-0.40.0/proton/python/examples/tx_send.py.html
    # def on_transaction_declared(self, event):
    #     self.transaction = event.transaction
    #     self.send()

    def on_sendable(self, event):
        while event.sender.credit and self.sent < self.total:
            event.sender.send(self.msg_q.get_nowait())
            logger.critical("MESSAGE SENT!")
            self.sent += 1

    def on_accepted(self, event):
        logger.critical("Message was accepted!!!")
        event.connection.close()

    # From : https://qpid.apache.org/releases/qpid-proton-0.40.0/proton/python/examples/tx_send.py.html
    # def send(self):
    #     self.transaction.commit()
    #     # Send nothing for now
    #     self.seq = self.seq + 1
    #     msg = Message(id=self.seq, body={'sequence': self.seq})
    #     self.transaction.send(self.sender, msg)
    #     self.transaction.commit()

    def update_queue(self, new_q):
        self.msg_q = new_q
        logger.critical(f"Is the queue empty? {self.msg_q.empty()}")


    def close(self):
        if self.sender:
            self.sender.close()
            self.sender.free()
            self.sender = None
            logger.debug("closed sender")
        if self.connection:
            self.connection.close()
            self.connection.free()
            self.connection = None
            logger.debug("closed connection")

class AMQ1(Moth):
    def __init__(self, props, is_subscriber):
        """
            AMQP 1.0 library to be built with libqpid-proton (the only free amqp 1.0 library around.)

            work in progress, incomplete, currently just experimental/alpha quality code

            To install the Proton library:
                pip3 install python-qpid-proton

            for debug logging add this to config:
            set sarracenia.moth.amq1.AMQ1.logLevel debug

            RabbitMQ-specific AMQP 1.0 Notes:
            ---------------------------------
            AMQP 1.0 does not define server side concepts like queues or exchanges.
            RabbitMQ's AMQP 1.0 implementation uses exchanges and queues (i.e. they use the
            AMQP 0.9.1 server model) with specific AMQP 1.0 *address* formats used to publish to
            exchanges, create and bind queues.
            https://www.rabbitmq.com/docs/amqp#address-v2

            E.g. to publish to an exchange, we post to address:
                /exchanges/xs_SOME_EXCHANGE/v03.some.routing.key
                or maybe it's /exchanges/xs_SOME_EXCHANGE/v03/some/routing/key ?
            To subscribe to a queue:
                /queues/queue_name

            FIXME: For subscribing to a queue, the documentation notes that the queue must already
            exist, and it doesn't say anything about the queue's bindings. So I assume we can't currently
            create exchanges/queues/bindings with AMQP 1.0, but this needs to be confirmed.

            Since we can use AMQP 0.9.1 for RabbitMQ, I'm not sure that we need to bother supporting
            the RabbitMQ-specific AMQP 1.0 implementation.

            Non-RabbitMQ AMQP 1.0:
            ----------------------
            We want to support non-RabbitMQ AMQP 1.0 brokers, so we need to support
            other address formats, without the concept of exchanges or queues.

            FIXME: I think I'm going to add an *address* option to the subscription config,
            and ignore queueName, exchange, subtopic, topicPrefix, etc.

            TODO:
            -----
            - Concept of durable queues - can we have messages queue up on the broker while we're
                disconnected?
            - Equivalent to queue names - can we specify the name of our queue/connection?
            - How do we ack messages?
            - How to have multiple instances share a 'queue'?
        """
        super().__init__(props, is_subscriber)

        logging.basicConfig(
            format=
            '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s')

        self.o = copy.deepcopy(default_options)
        self.o.update(props)

        me = "%s.%s" % (__class__.__module__, __class__.__name__)
        if ('settings' in self.o) and (me in self.o['settings']):
            for s in self.o['settings'][me]:
                self.o[s] = self.o['settings'][me][s]

            if 'logLevel' in self.o['settings'][me]:
                logger.setLevel(self.o['logLevel'].upper())

        now = time.time()
        self.next_connect_time = now
        self.next_connect_failures = 0
        self.next_message = 0

        # instance of Amqp1Client
        self.client = None
        self.reactor = None

        self.client_thread = None

        self._raw_msg_q = None
        self.amq1msg = None

    def _msgRawToDict(self, raw_msg) -> sarracenia.Message:
        """ Convert AMQP1.0 raw message to sr3 message (dictionary)
        """
        if self.o['messageDebugDump']:
            logger.info(f"Raw AMQP1.0 Message: {raw_msg}\n")
            for thing in sorted(dir(raw_msg)):
                if thing[0] != '_':
                    try:
                        val = getattr(raw_msg, thing)
                        if not callable(val):
                            logger.info(f"{thing:>20}: {val}")
                    except:
                        pass

        # at least for SWIM messages, msg.properties (AMQP 1.0 "Application Properties") is a dictionary
        # that contains the kind of info we'd put in the body of an sr3 format message.
        if raw_msg.properties:
            app_properties = raw_msg.properties
        else:
            app_properties = {}

        # all the other stuff in the message (Address, Header and Message Properties), we put
        # into the app_properties dict
        for thing in dir(raw_msg):
            if thing[0] != '_' and thing != 'properties' and thing != 'body':
                try:
                    val = getattr(raw_msg, thing)
                    if not callable(val):
                        app_properties[f'amqp1_{thing}'] = val
                except:
                    pass

        # for decoding these messages, we map the Application Properties to "headers"
        # the data (Message Payload/body), if present, is mapped to "payload"

        # for SWIM messages, content_type and content_encoding fields in the message are for the data,
        # not the message itself like in other protocols, and there are multiple possible types
        # we might receive that that could theoretically collide with the types we're using for
        # other messages (text/plain for v2, application/json for sr3, application/geo+json for WIS).
        # FIXME:
        # I'm not quite sure how to deal with content_type. For now we just give a fake content
        # type to ensure we don't accidentally interpret the message as sr3, v2 or WIS, but that
        # won't work if we want to receive one of those message formats over AMQP 1.0.
        #
        # We could potentially call the PostFormat.Swim.mine method here to check if the message
        # is in SWIM format before checking any other types, and if it's NOT SWIM, then pass the
        # actual content type?
        message = PostFormat.importAny(raw_msg.body, app_properties, "amqp1", self.o)
        logger.debug(f"sr3 message: {message}")

        return message

    def getSetup(self) -> None:
        """ Setup as a consumer to receive messages.
        """
        if not self.is_subscriber:
            logger.critical("trying to call getSetup but not instantiated as a subscriber")
            return

        if self._stop_requested:
            return

        if 'broker' not in self.o or self.o['broker'] is None:
            logger.critical( f"no broker given" )
            return

        if self.__is_connected():
            logger.warning("Already connected, nothing to do")
            return

        subscription = self.o['subscriptions'][self.o['subscription_index']]
        queuename = subscription['queue'] # FIXME: not used?
        broker = subscription['broker']

        start = time.time()
        if start < self.next_connect_time:
            if start > self.next_message:
                logger.critical( f"too soon to connect again to {str(broker)} index={self.o['subscription_index']} will try in: {self.next_connect_time-start:.2f} seconds" )
                self.next_message=start+5
            return

        if broker.url.hostname:
            host = broker.url.hostname
            if broker.url.port is None:
                if (broker.url.scheme[-1] == 's'):
                    host += ':5671'
                else:
                    host += ':5672'
            else:
                host += ':{}'.format(broker.url.port)
            if (broker.url.scheme[-1] == 's'):
                host = 'amqps://' + host
            else:
                host = 'amqp://' + host
        else:
            logger.critical( f"invalid broker specification: {broker} " )
            return False

        # It does not really matter how it fails, the recovery approach is always the same:
        # tear the whole thing down, and start over.
        self._raw_msg_q = queue.Queue() # FIXME need to deal with messages still in q?
        try:
            self.client = Amqp1Client(
                host,
                ["origin.a.wis2.com-ibl.data.core.weather.aviation.*"],
                self._raw_msg_q,
                self.is_subscriber
            )
            self.reactor = Container(self.client)
            self.client_thread = threading.Thread(target=self.reactor.run)
            self.client_thread.daemon = True
            self.client_thread.start()
            self.connection = True
            return

        except Exception as err:
            logger.error( f"failed connection to {str(broker)}: {err}" )
            logger.debug('Exception details: ', exc_info=True)
            self.setEbo(start)
            self.connection = None

    def putSetup(self) -> None:
        """ Setup as a publisher to post messages.
        """
        if self._stop_requested:
            return

        start = time.time()

        if start < self.next_connect_time:
            if start > self.next_message :
                logger.critical( f"too soon to connect to {str(self.o['broker'])}. Will try again in: {self.next_connect_time-start:.2f} seconds" )
                self.next_message=start+5
            return

        # subscription = self.o['subscriptions'][self.o['subscription_index']]
        # subtopic = '.'.join(subscription['bindings'][self.o['subscription_index']]['sub'][:])
        # prefix = '.'.join(subscription['bindings'][self.o['subscription_index']]['prefix'][:])
        # topic = '.'.join(prefix + subtopic)

        # It does not really matter how it fails, the recovery approach is always the same:
        # tear the whole thing down, and start over.
        try:
            # if self.o['broker'] is None:
            #     logger.critical( f"no broker given" )
            #     return

            # # FIXME?
            # # if not self.__connect(self.o['broker']):
            # #     self.setEbo(start)
            # #     self.connection = None
            # #     return

            # if self.o['broker'].url.hostname:
            #     host = self.o['broker'].url.hostname
            #     if self.o['broker'].url.port is None:
            #         if (self.o['broker'].url.scheme[-1] == 's'):
            #             host += ':5671'
            #         else:
            #             host += ':5672'
            #     else:
            #         host += ':{}'.format(self.o['broker'].url.port)
            #     if (self.o['broker'].url.scheme[-1] == 's'):
            #         host = 'amqps://' + host
            #     else:
            #         host = 'amqp://' + host
            # else:
            #     logger.critical( f"invalid broker specification: {self.o['broker']} " )
            #     return False

            # self._raw_msg_q = queue.Queue() # FIXME need to deal with messages still in q?

            # self.client = Amqp1Pub(
            #     host,
            #     topic,
            #     self._raw_msg_q,
            #     self.o
            # )
            # logger.critical(f"Host : {host}")

            # self.connection = True

            # logger.critical(f"AMQ1 client connection initialized")
            return

        except Exception as err:
            logger.error( f"failed connection to {str(self.o['broker'])}: {err}" )
            logger.debug('Exception details: ', exc_info=True)
            self.setEbo(start)
            self.connection=None
            self.close()


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
        """ Mostly a copy of moth.amqp.AMQP's getNewMessage.
        """

        if not self.is_subscriber:  #build_consumer
            logger.error("getting from a publisher")
            return None

        try:
            if not self.__is_connected():
                self.getSetup()

            # check again, fail if it didn't connect
            if not self.__is_connected():
                return None

            try:
                # don't block waiting for the queue to be available, better to just try again later
                raw_msg = self._raw_msg_q.get_nowait()
            except queue.Empty:
                raw_msg = None

            if raw_msg is None:
                return None
            else:
                # self.metrics['rxByteCount'] += len(raw_msg.body)
                try:
                    msg = self._msgRawToDict(raw_msg)
                except Exception as err:
                    logger.error("message decode failed. raw message: %s" % raw_msg.body )
                    logger.debug('Exception details: ', exc_info=True)
                    msg = None
                # if msg is None:
                #     self.metrics['rxBadCount'] += 1
                #     return None
                # else:
                #     self.metrics['rxGoodCount'] += 1
                # if hasattr(self.o, 'fixed_headers'):
                #     for k in self.o.fixed_headers:
                #         msg[k] = self.o.fixed_headers[k]
                # logger.debug("new msg: %s" % msg)
                return msg
        except Exception as err:
            subscription = self.o['subscriptions'][self.o['subscription_index']]
            sub_queue = subscription['queue']
            logger.warning("failed %s: %s" % (sub_queue['name'], err))
            logger.debug('Exception details: ', exc_info=True)

        if not self.o['message_strategy']['stubborn']:
            return None

        logger.warning('lost connection to broker')
        self.close()
        time.sleep(1)
        return None

    def putNewMessage(self,
                      message: sarracenia.Message,
                      content_type: str = 'application/json',
                      exchange: str = None ) -> bool:
        """ Mostly a copy of moth.amqp.AMQP's putNewMessage.
        """

        if self.is_subscriber:  #build_consumer
            logger.error("publishing from a consumer")
            return False

        # Check connection status, try to reconnect if not connected
        # if (not self.connection) or (not self.__is_connected):
        #     try:
        #         self.close()
        #         self.putSetup()
        #         if (not self.connection) or (not self.__is_connected):
        #             return False
        #     except Exception as err:
        #         logger.warning(f"failed, connection was closed/broken and could not be re-opened {exchange}: {err}")
        #         logger.debug('Exception details: ', exc_info=True)
        #         return False

        # The caller probably doesn't expect the message to get modified by this method, so use a copy of the message
        body = copy.deepcopy(message)

        logger.critical(f"Message body {body}")

        if 'format' in self.o:
            version=self.o['format']
        else:
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

        #if not exchange:
        #    if (type(self.o['exchange']) is list):
        #        if (len(self.o['exchange']) > 1):
        #            if ( 'exchangeSplit' in self.o) and self.o['exchangeSplit'] > 1:
        #                exchange = self.o['exchange'][self.splitPick(message)]
        #            else:
        #                logger.error(
        #                    'do not know which exchange to publish to: %s' %
        #                    self.o['exchange'])
        #                return False
        #        else:
        #            exchange = self.o['exchange'][0]
        #    else:
        #        exchange = self.o['exchange']

        #if 'messageAgeMax' in self.o and self.o['messageAgeMax']:
        #    ttl = "%d" * int(
        #        sarracenia.durationToSeconds(self.o['messageAgeMax']) * 1000)
        #else:
        #    ttl = "0"
        #
        #if 'persistent' in self.o:
        #    deliv_mode = 2 if self.o['persistent'] else 1
        #else:
        #    deliv_mode = 2

        # Limit to only SWIM protocol now.
        raw_body = PostFormat.exportAny( body, version, 'swim', self.o )
        logger.critical(f"SWIM RAW MESSAGE BODY {raw_body}")

        subscription = self.o['subscriptions'][self.o['subscription_index']]
        subtopic = ''.join(subscription['bindings'][self.o['subscription_index']]['sub'][:])
        prefix = ''.join(subscription['bindings'][self.o['subscription_index']]['prefix'][:])
        topic = prefix + '.' + subtopic

        logger.critical(f"Topic {topic} , prefix {prefix} , subtopic {subtopic}")

        # topic = topic.replace('#', '%23')
        # topic = topic.replace('*', '%22')
        exchange = 'exchange-not-used' # FIXME: What to do about this?

        #if len(topic) >= 255:  # ensure topic is <= 255 characters
        #    logger.error("message topic too long, truncating")
        #    mxlen = amqp_ss_maxlen
        #    while (topic.encode("utf8")[mxlen - 1] & 0xc0 == 0xc0):
        #        mxlen -= 1
        #    topic = topic.encode("utf8")[0:mxlen].decode("utf8")

        if self.o['messageDebugDump']:
            logger.info('raw message body: version: %s type: %s %s' %
                             (version, type(raw_body),  raw_body))
            #logger.info('raw message headers: type: %s value: %s' % (type(headers),  headers))

        if not 'posts' in message:
            message['posts'] = []
        message['posts'].append( { 'broker':str(self.o['broker']), 'topic': topic, 'exchange':exchange } ) 
        message['_deleteOnPost'] |= set( ['posts'] )
        #del headers['topic']

        # if headers :  
        #     for k in headers:
        #         if (type(headers[k]) is str) and (len(headers[k]) >=
        #                                               amqp_ss_maxlen):
        #             logger.error("message header %s too long, dropping" % k)
        #             return False

        if self.o['broker'] is None:
            logger.critical( f"no broker given" )
            return

        # FIXME?
        # if not self.__connect(self.o['broker']):
        #     self.setEbo(start)
        #     self.connection = None
        #     return
    

        if self.o['broker'].url.hostname:
            host = self.o['broker'].url.hostname
            if self.o['broker'].url.port is None:
                if (self.o['broker'].url.scheme[-1] == 's'):
                    host += ':5671'
                else:
                    host += ':5672'
            else:
                host += ':{}'.format(self.o['broker'].url.port)
            if (self.o['broker'].url.scheme[-1] == 's'):
                host = 'amqps://' + host
            else:
                host = 'amqp://' + host
        else:
            logger.critical( f"invalid broker specification: {self.o['broker']} " )
            return False

        self._raw_msg_q = queue.Queue() # FIXME need to deal with messages still in q?

        self.client = Amqp1Pub(
            host,
            topic,
            self._raw_msg_q,
            self.o
        )

        self.amq1msg = Message(id=1, body=raw_body)
        self._raw_msg_q.put_nowait(self.amq1msg)
        #logger.critical(f"Client : {self.client}")
        self.client.update_queue(self._raw_msg_q)

        # FIXME: Add metrics
        # self.metrics['txByteCount'] += len(raw_body) 
        # if headers:
        #     self.metrics['txByteCount'] += len(''.join(str(headers)))
        # self.metrics['txLast'] = sarracenia.nowstr()

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
            #logger.debug( f"trying to publish body: {body} headers: {headers} to {exchange} under: {topic} " )
            #self.channel.basic_publish(AMQP_Message, exchange, topic, timeout=pub_timeout)
            self.reactor = Container(self.client)
            self.reactor.run()

            # Issue #732: tx_commit can get stuck forever
            #logger.debug("published body: {} headers: {} to {} under: {} ".format(
            #              body, headers, exchange, topic))
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


    def __is_connected(self):
        return self.client and self.client.is_connected

    def close(self) -> None:
        if self.client:
            self.client.close()
            self.client = None
        if self.reactor:
            self.reactor.stop()
            logger.debug("stopped reactor")
            self.reactor = None
        if self.client_thread:
            # wait for thread to shut itself down
            logger.debug("waiting for thread to terminate")
            self.client_thread.join()
            logger.debug("thread terminated")
            self.client_thread = None
        # FIXME metrics stuff
