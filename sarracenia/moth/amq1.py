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
from proton import Endpoint

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
    def __init__(self, url: str, addresses: list, msg_q: queue.Queue, is_subscriber: bool, options: dict):
        """ Handles communication with an AMQP1.0 broker.
            Args:
                url (str): The AMQP broker connection URL.
                addresses (list): A list of source addresses to receive from. Not used for publishing. The publish
                                    address is specified in the message's address field.
                msg_q (queue.Queue): When subscribing, messages received from the broker are placed in this queue.
                    When publishing, messages to be published are placed in this queue.
                is_subscriber (bool): True when subscribing (receive messages from the broker), False when
                    publishing messages to the broker.
                options (dict): sr3 options dictionary
        """
        # TODO: can pass prefetch as param
        super(Amqp1Client, self).__init__()
        self.url = url
        self.addresses = addresses
        self.msg_q = msg_q
        self.is_subscriber = is_subscriber

        self.__connected = False
        self.receivers = []
        self.sender = None
        self.connection = None
        self.seq = 0

        self.pending_deliveries = queue.Queue()
        self.pending_msgs = {}

        scheme = self.url.split("://")[0].lower()
        self.__secure = scheme[-1] == 's'

        self.o = options

        self.username = self.o['broker'].url.username
        self.password = self.o['broker'].url.password

        self.anonymous = (self.username == 'anonymous' and self.password == 'anonymous')

        # NAVCANADA requires [CLIENTNAME]-[ENDPOINT]-[PUB/SUB]
        # TODO: revisit this
        self.connection_name = "metpx-sr3_v" + sarracenia.__version__ + '-' + self.o['component'] + '_' + self.o['config']
        if self.is_subscriber:
            self.connection_name += '-SUB'
        else:
            self.connection_name += '-PUB'
        logger.debug(f"connection name: {self.connection_name}")

    def on_start(self, event):
        """ Event loop in container has started, can now create senders/receivers.
        """
        if self.__secure:
            ssl_domain = SSLDomain(SSLDomain.MODE_CLIENT)
            # FIXME: currently not verifying SSL at all
            ssl_domain.set_peer_authentication(SSLDomain.ANONYMOUS_PEER)
        else:
            ssl_domain = None

        event.container.container_id = self.connection_name

        # TODO test anon
        logger.debug(f"attempting to connect to broker={self.url} user={self.username}")
        if self.anonymous:
            self.connection = event.container.connect(self.url, ssl_domain=ssl_domain)
        else:
            self.connection = event.container.connect(self.url, ssl_domain=ssl_domain,
                                                      user=self.username,
                                                      password=self.password)

        # subscriber: create receivers for each source address
        if self.is_subscriber:
            for addr in self.addresses:
                try:
                    rx = event.container.create_receiver(self.connection, source=addr)
                    self.receivers.append(rx)
                    logger.info(f"created receiver for source address: {addr}")
                except Exception as e:
                    logger.error("failed to create receiver for address: {addr}")
                    logger.debug("Exception details:", exc_info=True)

        # publisher: create senders for each destination address
        else:
            # anonymous sender, no address defined
            self.sender = event.container.create_sender(self.connection)
            # event.container.declare_transaction(self.connection, handler=self)
            # self.transaction = None


    def on_message(self, event):
        """ Subscriber: handle message received from broker.
        """
        # TODO: does this get called when we are a publisher, if yes, need an if statement here
        msg = event.message
        self.msg_q.put(msg)
        logger.debug(f"new message pushed from broker (address: {event.receiver.source.address}): {msg}")
        logger.debug(f"testing: {event.receiver.source.properties}")

    # From : https://qpid.apache.org/releases/qpid-proton-0.40.0/proton/python/examples/tx_send.py.html
    # def on_transaction_declared(self, event):
    #     self.transaction = event.transaction
    #     self.send()

    def on_sendable(self, event):
        """ Publisher: called when there is "credit" on the sender link, publishes all messages in the msg_q.
            TODO: how to detect when a message was published successfully and report back? transaction?
        """
        logger.warning("hello from on sendable")
        # TODO: maybe only remove the message from the queue once it has been sent successfully, it that possible?
        while event.sender.credit and not self.msg_q.empty():
            msg = self.msg_q.get()
            # NOTE: this is async
            delivery = event.sender.send(msg)
            self.pending_msgs[delivery] = msg
            self.pending_deliveries.put(msg)
            logger.critical(f"message passed to broker, hopefully it will send {delivery} {msg}")
            # self.sent += 1

    def on_accepted(self, event):
        """ Publisher: the broker has accepted a message we sent.
        """
        msg = self.pending_msgs.pop(event.delivery)
        logger.debug(f"Message was accepted!!! {event.delivery}")
        self.pending_deliveries.get()
        # event.connection.close()

    def on_rejected(self, event):
        """ Publisher: the broker has rejected a message we sent.
        """
        msg = self.pending_msgs.pop(event.delivery)
        logger.error(f"message rejected by broker {event.delivery} {msg}")
        self.pending_deliveries.get()
        # event.connection.close()

    def on_released(self, event):
        """ Publisher: the message was returned to be retried.
        """
        logger.error("message released by broker")
        self.pending_deliveries.get()
        # TODO ??

    # From : https://qpid.apache.org/releases/qpid-proton-0.40.0/proton/python/examples/tx_send.py.html
    # def send(self):
    #     self.transaction.commit()
    #     # Send nothing for now
    #     self.seq = self.seq + 1
    #     msg = Message(id=self.seq, body={'sequence': self.seq})
    #     self.transaction.send(self.sender, msg)
    #     self.transaction.commit()

    def update_queue(self, new_q):
        """ TODO
        this is for publishing
        """
        self.msg_q = new_q
        #logger.critical(f"Is the queue empty? {self.msg_q.empty()}")

    def on_connection_opened(self, event):
        logger.info(f"connection opened to {self.url} {event}")
        self.__connected = True

    def on_connection_closed(self, event):
        logger.info(f"connection closed {event}")
        self.__connected = False

    def close(self):
        for rx in self.receivers:
            rx.close()
            rx.free()
            logger.debug(f"closed receiver from address {rx.source.address}")
        self.receivers = []
        if self.sender:
            self.sender.close()
            self.sender.free()
            logger.debug(f"closed sender")
        self.sender = None
        if self.connection:
            self.connection.close()
            self.connection.free()
            self.connection = None
            logger.debug("closed connection")

    def is_connected(self):
        """ Return True when the connection is connected.
            connection.state can be UNINIT, ACTIVE, CLOSED 
            https://qpid.apache.org/releases/qpid-proton-0.40.0/proton/python/docs/proton.html#proton.Connection.state
        """
        if self.connection is None:
            logger.debug("no connection")
            return False
        else:
            state = self.connection.state
            # connection can be used when both REMOTE and LOCAL are active
            if (state & Endpoint.LOCAL_ACTIVE) and (state & Endpoint.REMOTE_ACTIVE):
                return True
            else:
                connection_state = ''
                if state & Endpoint.LOCAL_UNINIT:
                    connection_state += 'LOCAL_UNINIT '
                if state & Endpoint.LOCAL_ACTIVE:
                    connection_state += 'LOCAL_ACTIVE '
                if state & Endpoint.LOCAL_CLOSED:
                    connection_state += 'LOCAL_CLOSED '
                if state & Endpoint.REMOTE_UNINIT:
                    connection_state += 'REMOTE_UNINIT '
                if state & Endpoint.REMOTE_ACTIVE:
                    connection_state += 'REMOTE_ACTIVE '
                if state & Endpoint.REMOTE_CLOSED:
                    connection_state += 'REMOTE_CLOSED '
                logger.debug(f"connection not active, state: {connection_state}")
                return False

class AMQ1(Moth):
    def __init__(self, props, is_subscriber):
        """
            AMQP 1.0 library to be built with libqpid-proton (the only free amqp 1.0 library around.)

            work in progress, incomplete, currently just experimental/alpha quality code

            To install the Proton library:
                pip3 install python-qpid-proton

            for debug logging add this to config:
            set sarracenia.moth.amq1.AMQ1.logLevel debug

            AMQP 1.0 does not define server side concepts like queues or exchanges.

            RabbitMQ-specific AMQP 1.0 Notes:
            ---------------------------------
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
            We need to support non-RabbitMQ AMQP 1.0 brokers, so we can't rely on RabbitMQ's address
            definitions. Each broker's implementation of AMQP1.0 can be very different, so we're trying to
            be as generic as possible. It's likely that additional subclasses may be required for interfacing
            with specific brokers.

            In AMQP1.0, addresses roughly map to the concept of queues in AMQP0.9.1 and MQTT.

            In sr3, topics are normally related to file paths, so we can have the broker filter messages
            that the client wants to receive. But this convention does not apply in all cases, like SWIM,
            where messages are published to and received from fixed addresses (the address is kind of like
            a queue in this case, and the publisher places messages directly in the "queue" (address))

            Addresses in AMQP1.0 are static, and wildcards are not part of the spec. In MQTT, we map
            the exchange and topicPrefix into the topic, but this causes issues
            when trying to subscribe to sources where a static exchange and topicPrefix are not used.
            We need a way to set no topicPrefix and no exchange, and allow the address to be defined only
            by the subtopic. (Maybe the best way to do this is a fixed list of topics that overrides the
            exchange, topicPrefix and subtopic convention. That would require some larger changes.)
            Whatever we choose to do for AMQP1.0 should work for MQTT too.

            For now, we are just ignoring topicPrefix and exchange and just use the subtopics as addresses.

            TODO:
            -----
            - Figure out how we want to define address(es) in the config.
            - Concept of durable queues - can we have messages queue up on the broker while we're
                disconnected? durable source?
            - Equivalent to queue names - can we specify the name of our queue/connection?
            - How do we ack messages?
            - How to have multiple instances share a 'queue'?

            More notes:
              - A source can have filters configured?
              - message distribution mode: copy (every receiver gets a copy, messages remain in the 'queue')
                  or move (only 1/n receivers gets the message, what we need when using multiple nodes/instances)
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

    def connect(self, broker, addresses=[]) -> bool:
        """ General connection code, for subscriber or publisher.
        """
        if 'broker' not in self.o or self.o['broker'] is None:
            logger.critical( f"no broker given" )
            return

        if self.__is_connected():
            logger.warning("Already connected, nothing to do")
            return

        start = time.time()
        if start < self.next_connect_time:
            if start > self.next_message:
                logger.critical( f"too soon to connect again to {str(broker)} will try in: {self.next_connect_time-start:.2f} seconds" )
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

        self._raw_msg_q = queue.Queue() # FIXME need to deal with messages still in q? when subscribing

        try:
            self.client = Amqp1Client(
                host,
                addresses,
                self._raw_msg_q,
                self.is_subscriber,
                self.o
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

    def getSetup(self) -> None:
        """ Setup as a consumer to receive messages.
        """
        if not self.is_subscriber:
            logger.critical("trying to call getSetup but not instantiated as a subscriber")
            return

        if self._stop_requested:
            return

        subscription = self.o['subscriptions'][self.o['subscription_index']]
        broker = subscription['broker']
        bindings = subscription['bindings']

        # translate sr3 bindings to AMQP1.0 addresses (FIXME: currently ignoring exchange/topicPrefix)
        addresses = [ b['sub'][0] for b in bindings ]
        logger.debug(f"source addresses: {addresses}")

        self.connect(broker, addresses=addresses)


    def putSetup(self) -> None:
        """ Setup as a publisher to post messages.
        """
        if self.is_subscriber:
            logger.critical("trying to call putSetup but not instantiated as a publisher")
            return

        if self._stop_requested:
            return
        if self.o['broker'] is None:
            logger.critical( f"no broker given" )
            return

        self.connect(self.o['broker'], addresses=[])

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

        try:
            if not self.__is_connected():
                self.close()
                self.putSetup()
                time.sleep(5) # TODO

            # check again, fail if it didn't connect
            if not self.__is_connected():
                return False
            
            # The caller probably doesn't expect the message to get modified by this method, so use a copy of the message
            sr3_msg = copy.deepcopy(message)

            if 'format' in self.o:
                version=self.o['format']
            else:
                version = sr3_msg['_format']

            if '_deleteOnPost' in sr3_msg:
                # FIXME: need to delete because building entire JSON object at once.
                # makes this routine alter the message. Ideally, would use incremental
                # method to build json and _deleteOnPost would be a guide of what to skip.
                # library for that is jsonfile, but not present in repos so far.
                for k in sr3_msg['_deleteOnPost']:
                    if k in sr3_msg:
                        del sr3_msg[k]
                del sr3_msg['_deleteOnPost']

            # convert sr3 message to desired raw format (e.g. SWIM, NAVCANADA)
            # (NOTE: set post_format swim or post_format navcanada in config file TODO not sure if post_format or format)
            raw_body, headers, content_type = PostFormat.exportAny(sr3_msg, version, self.o['topicPrefix'], self.o)

            # address to publish to is post_topicPrefix + a dynamic topic
            # FIXME: topic separator should be configurable
            address = headers['topic']
            logger.error(f"TODO: address={address}")

            # TODO is there a length limit for address?

            if self.o['messageDebugDump']:
                logger.info('raw message body: version: %s type: %s %s' %
                                (version, type(raw_body),  raw_body))
                logger.info('raw message headers: type: %s value: %s' % (type(headers),  headers))

            # TODO compare with regular AMQP, posts stuff?

            # create AMQP1 message object to be published
            # postformat stuff determines *what* the body is. For SWIM/NAVCANADA, the body is the inline content.
            # for sr3 format, I think the body would be the JSON message itself.
            amqp1_msg = Message(address=address, body=raw_body)
            amqp1_msg.properties = headers

            logger.debug(f"FULL AMQP1 MESSAGE: {amqp1_msg}")

            # place the message in the queue, the client will take care of sending it
            # FIXME: blocking put used, need to timeout?
            self._raw_msg_q.put(amqp1_msg)

            # TODO: metrics
            time.sleep(5)

            # FIXME: need to check if the message was actually sent... then retry/return appropriately
            while not self.client.pending_deliveries.empty():
                logger.info(f"waiting for {self.client.pending_deliveries.qsize()} msgs to publish")
                time.sleep(1)

            
            return True

        except Exception as e:
            logger.error(f"message publish failed: {e}")
            logger.debug("Exception details:", exc_info=True)
            return False



    def __is_connected(self):
        return self.client and self.client.is_connected()

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
