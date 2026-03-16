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
from proton.utils import BlockingConnection
from proton import Delivery, Endpoint, Message, SSLDomain

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

class Amqp1ClientBase:
    """ Base class for AMQP1 connections.
        Just handles some instance variables that are shared between both receivers and publishers.
    """
    def __init__(self, broker_url: str, options: dict, is_subscriber=False):
        self.broker_url = broker_url
        self.o = options

        scheme = self.broker_url.split("://")[0].lower()
        self.__secure = scheme.endswith('s')

        self.username = self.o['broker'].url.username
        self.password = self.o['broker'].url.password
        self.anonymous = (self.username == 'anonymous' and self.password == 'anonymous')

        self.connection_name = f"metpx-sr3_v{sarracenia.__version__}-{self.o['component']}_{self.o['config']}"
        self.connection_name += "-SUB" if is_subscriber else "-PUB"
        logger.debug(f"connection name: {self.connection_name}")

        if self.__secure:
            self.ssl_domain = SSLDomain(SSLDomain.MODE_CLIENT)
            # FIXME: currently not verifying SSL at all
            self.ssl_domain.set_peer_authentication(SSLDomain.ANONYMOUS_PEER)
        else:
            self.ssl_domain = None

    @staticmethod
    def delivery_state_to_str(delivery_state):
        if delivery_state == Delivery.ACCEPTED:
            return "accepted"
        elif delivery_state == Delivery.REJECTED:
            return "rejected"
        elif delivery_state == Delivery.RELEASED:
            return "released"
        elif delivery_state == Delivery.MODIFIED:
            return "modified"
        elif delivery_state == 0:
            return "no state"
        else:
            return "unknown"

class Amqp1Publisher(Amqp1ClientBase):
    def __init__(self, broker_url: str, options: dict):
        """ Handles publishing messages to an AMQP1.0 broker.
        """
        super().__init__(broker_url, options, is_subscriber=False)

        self.container = None
        self.connection = None
        self.sender = None

        if options['timeout'] > 0:
            self.timeout = options['timeout']
        else:
            self.timeout = None # default is 60 seconds

        self._connect()

    def _connect(self):
        container = Container()
        container.container_id = self.connection_name

        if self.anonymous:
            self.connection = BlockingConnection(url=self.broker_url, timeout=self.timeout,
                                                 ssl_domain=self.ssl_domain, container=container)
        else:
            self.connection = BlockingConnection(url=self.broker_url, timeout=self.timeout,
                                                 ssl_domain=self.ssl_domain, container=container,
                                                 user=self.username, password=self.password)
        # addresses will be specified in the message
        self.sender = self.connection.create_sender(address=None, name=self.connection_name)

    def is_connected(self):
        """ BlockingConnection doesn't expose a state like the async does.
            If the connection is broken, we have no way of knowing until we attempt to publish.
        """
        return (self.connection is not None)

    def publish(self, message):
        """ Publish an AMQP1.0 message.
            Return True when successful, False when failed.
        """
        try:
            delivery = self.sender.send(message, timeout=self.o['timeout'])
            return True
        except Exception as e:
            err_name = ''
            err_desc = ''
            try:
                if self.sender.remote_condition:
                    err_name = self.sender.remote_condition.name
                    err_desc = self.sender.remote_condition.description
            except:
                pass
            logger.error(f"failed because {e} {err_name} {err_desc}")
            logger.debug("Exception details:", exc_info=True)
        return False

    def close(self):
        try:
            self.sender.close()
            self.sender.free()
        except:
            pass
        self.sender = None
        try:
            self.connection.close()
            self.connection.free()
        except:
            pass
        self.connection = None

class Amqp1Receiver(MessagingHandler, Amqp1ClientBase):
    """
        Based on https://qpid.apache.org/releases/qpid-proton-0.40.0/proton/python/examples/
        Docs: https://qpid.apache.org/releases/qpid-proton-0.40.0/proton/python/docs/index.html
    """
    def __init__(self, broker_url: str, options: dict, addresses: list, msg_q: queue.Queue, ack_q: queue.Queue):
        """ Handles receiving messages from an AMQP1.0 broker. Reception is asynchronous.

            Args:
                url (str): The AMQP broker connection URL.
                options (dict): sr3 options dictionary
                addresses (list): A list of source addresses to receive from. Not used for publishing. The publish
                    address is specified in the message's address field.
                msg_q (queue.Queue): messages received from the broker are placed in this queue.
                ack_q (queue.Queue): tags for messages ready to be acked should be placed in this queue.
        """
        Amqp1ClientBase.__init__(self, broker_url, options, is_subscriber=True)
        # auto_accept and auto_settle False means we want to manually ack messages
        MessagingHandler.__init__(self, prefetch=self.o['prefetch'], auto_accept=False, auto_settle=False)

        self.addresses = addresses
        self.msg_q = msg_q
        self.ack_q = ack_q

        self.__connected = False
        self.connection = None
        self.receivers = []
        self.ack_id_counter = 0
        self.pending_deliveries = {}

    def on_start(self, event):
        """ Event loop in container has started, can now create receivers.
        """
        event.container.container_id = self.connection_name

        # TODO test anon
        if self.anonymous:
            self.connection = event.container.connect(self.broker_url, ssl_domain=self.ssl_domain)
        else:
            self.connection = event.container.connect(self.broker_url, ssl_domain=self.ssl_domain,
                                                      user=self.username,
                                                      password=self.password)

        # subscriber: create receivers for each source address
        for addr in self.addresses:
            try:
                rx = event.container.create_receiver(self.connection, source=addr, name=self.connection_name)
                self.receivers.append(rx)
                logger.info(f"created receiver for source address: {addr}")
            except Exception as e:
                logger.error(f"failed to create receiver for address: {addr}")
                logger.debug("Exception details:", exc_info=True)
                # abort
                self.close()
                event.container.stop()

    def on_message(self, event):
        """ Subscriber: handle message received from broker.
        """
        msg = event.message
        delivery = event.delivery

        # There is a delivery.tag value, but Proton tries to decode it as a UTF-8 string, which crashes
        # because sometimes we receive messages with non-UTF-8-decodable tags. (from Solace brokers).
        # Therefore we just assign our own ID and store it for future acking. (Delivery objects are not
        # thread-safe according to C++ docs so we can't just use the delivery object itself).
        # (https://qpid.apache.org/releases/qpid-proton-0.37.0/proton/cpp/api/mt_page.html)
        self.pending_deliveries[self.ack_id_counter] = (delivery, event.receiver)

        self.msg_q.put( (msg, self.ack_id_counter) )
        self.ack_id_counter += 1
        logger.debug(f"new message pushed from broker (address: {event.receiver.source.address}, delivery_count: {msg.delivery_count}): {msg}")

    def on_timer_task(self, event):
        """ Execute to handle message acking
        """
        # Ack:
        if not self.ack_q.empty():
            self.__ack(event)

    def __ack(self, event):
        """ Ack all IDs waiting in the ack_q
        """
        while not self.ack_q.empty():
            tag = self.ack_q.get()
            # FIXME: should maybe implement rollover for counter
            if tag > self.ack_id_counter:
                logger.warning(f"asked to ack ID {tag} less than current {self.ack_id_counter}")
            try:
                delivery, receiver = self.pending_deliveries.pop(tag, (None,None))
                if delivery:
                    cb = receiver.credit
                    delivery.update(Delivery.ACCEPTED)
                    delivery.settle()
                    # TODO: this doesn't seem right, but if the credit is 0 then the
                    # ack doesn't seem to transmit (related to prefetch)
                    if cb == 0:
                        receiver.flow(1)
                    logger.debug(f"local_state: {Amqp1ClientBase.delivery_state_to_str(delivery.local_state)}, " +
                                 f"remote_state: {Amqp1ClientBase.delivery_state_to_str(delivery.remote_state)}, " +
                                 f"settled: {delivery.settled}, credit before ack: {cb}, " +
                                 f"credit after ack: {receiver.credit}")
            except Exception as e:
                logger.warning(f"ack failed for id: {tag} {e}")

    def on_connection_opened(self, event):
        logger.info(f"connection opened to {self.broker_url} {event}")
        self.__connected = True

    def on_connection_closed(self, event):
        logger.info(f"connection closed {event}")
        self.__connected = False

    def on_link_error(self, event):
        logger.error("link error")
        self.close()

    def close(self):
        for rx in self.receivers:
            rx.close()
            rx.free()
            logger.debug(f"closed receiver from address {rx.source.address}")
        self.receivers = []
        if self.connection:
            self.connection.close()
            self.connection.free()
            logger.debug("closed connection")
        self.connection = None

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

            To subscribe, the documentation notes that the queue must already exist. The queue and bindings must be
            created *somehow*, but AMQP1.0/proton has no way to do that. Any code implemented or other libraries
            used to create queues and configure bindings would be RabbitMQ-specific.

            Since we can use AMQP 0.9.1 for RabbitMQ, there isn't really any point in making our AMQP1.0
            implementation work with RabbitMQ's model.

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

            AMQP1.0 Delivery States: a message can be ACCEPTED, REJECTED, RELEASED or MODIFIED.
                - ACCEPTED: a message that has been received and processed successfully
                - REJECTED: permanently failed
                - RELEASED: put back to the source to be redelivered
                - MODIFIED: redliver with changes (likely not useful to us)

                By default, qpid proton sets auto_accept and auto_settle True, which is like auto-acking.
                We probably want to set those to False, then we would "ack" by setting:
                    delivery.update(proton.ACCEPTED)
                    delivery.settle()

            Delivery guarantees (similar to MQTT QoS)

            AMQP 1.0 expresses guarantees via link settlement modes:
                At-most-once - pre-settled messages (no redelivery)
                At-least-once - receiver accepts after processing
                Exactly-once - requires transactions

            TODO:
            -----
            - Figure out how we want to define address(es) in the config. (topic)
            - How do we ack messages?
            - How to have multiple instances share a 'queue'?

            Other Notes:
            ------------
              - It seems like most of the time we will be connecting to pre-existing addresses (that behave like
                queues). This is broker dependent. At least for NAVCAN, they will pre-create our queues, with routing
                and other options (e.g. durability, round-robin, etc.) already configured.
              - Given a "queue-like" address, can we request additional broker-side filtering?
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

        self.broker = None

        # instance of Amqp1Receiver
        self.client = None
        self.reactor = None

        self.client_thread = None

        self._raw_msg_q = None
        self._ack_q = None

    def _msgRawToDict(self, raw_msg) -> sarracenia.Message:
        """ Convert AMQP1.0 raw message to sr3 message (dictionary)
        """
        if self.o['messageDebugDump']:
            logger.info(f"raw message: {raw_msg}")
            # for thing in sorted(dir(raw_msg)):
            #     if thing[0] != '_':
            #         try:
            #             val = getattr(raw_msg, thing)
            #             if not callable(val):
            #                 logger.debug(f"{thing:>20}: {val}")
            #         except:
            #             pass

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

        # for SWIM messages, content-type and content-encoding fields in the message are for the data,
        # not the message itself like in other protocols, and there are multiple possible types
        # we might receive that that could theoretically collide with the types we're using for
        # other messages (text/plain for v2, application/json for sr3, application/geo+json for WIS).

        # i.e. content-type in the message is useless for determining the type of message received when we have a
        # SWIM/NAVCAN message, but we still handle it here to allow v03 and v02 messages to be received via AMQP1
        if hasattr(raw_msg, 'content_type'):
            content_type = getattr(raw_msg, 'content_type')
        elif hasattr(raw_msg, 'content-type'):
            content_type = getattr(raw_msg, 'content-type')
        else:
            content_type = 'amqp1' # unknown

        # for decoding AMQP1 messages, we map the Application Properties to "headers"
        # the data (Message Payload/body), if present, is mapped to "payload"
        message = PostFormat.importAny(raw_msg.body, app_properties, content_type, self.o)

        if self.o['messageDebugDump']:
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
            broker_url = broker.url.hostname
            if broker.url.port is None:
                if (broker.url.scheme[-1] == 's'):
                    broker_url += ':5671'
                else:
                    broker_url += ':5672'
            else:
                broker_url += ':{}'.format(broker.url.port)
            if (broker.url.scheme[-1] == 's'):
                broker_url = 'amqps://' + broker_url
            else:
                broker_url = 'amqp://' + broker_url
        else:
            logger.critical( f"invalid broker specification: {broker} " )
            return False

        # It does not really matter how it fails, the recovery approach is always the same:
        # tear the whole thing down, and start over.
        try:
            if self.is_subscriber:
                self._raw_msg_q = queue.Queue() # FIXME need to deal with messages still in q? when subscribing
                self._ack_q = queue.Queue()

                self.client = Amqp1Receiver(
                    broker_url,
                    self.o,
                    addresses,
                    self._raw_msg_q,
                    self._ack_q
                )
                self.reactor = Container(self.client)
                self.client_thread = threading.Thread(target=self.reactor.run)
                self.client_thread.daemon = True
                self.client_thread.start()

            else:
                self.client = Amqp1Publisher(
                    broker_url,
                    self.o
                )

        except Exception as err:
            logger.error( f"failed connection to {str(broker)}: {err}" )
            logger.debug('Exception details: ', exc_info=True)

        time.sleep(0.5)
        if not self.__is_connected():
            logger.error( f"failed connection to {str(broker)}" )
            self.close()
            self.setEbo(start)

        self.broker = broker


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
        # and topic, which is used for MQTT but only allows one address
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
                # don't block waiting for messages to be available, better to just try again later
                raw_msg, ack_id = self._raw_msg_q.get_nowait()
            except queue.Empty:
                raw_msg = None
                ack_id = None

            if raw_msg is None:
                return None
            elif ack_id is None:
                logger.error("received raw msg but no ack_id")
            else:
                # self.metrics['rxByteCount'] += len(raw_msg.body)
                try:
                    msg = self._msgRawToDict(raw_msg)
                    logger.info(f"ACK ID is: {ack_id}")
                    # ack_id can be 0, need to specifically check that it's not None
                    if ack_id is not None and msg is not None:
                        msg['ack_id'] = { 'tag': ack_id,
                                          'broker': self.broker, # must match broker in gather.message
                                        }
                        msg['_deleteOnPost'].add('ack_id')
                except Exception as err:
                    logger.error("message decode failed. raw message: %s" % raw_msg.body )
                    logger.debug('Exception details: ', exc_info=True)
                    msg = None
                    # tell the broker we've acked the message, even though we can't process
                    if ack_id:
                        self._ack_q.put(ack_id)

                if msg is None:
                    self.metrics['rxBadCount'] += 1
                    return None
                else:
                    self.metrics['rxGoodCount'] += 1

                if hasattr(self.o, 'fixed_headers'):
                    for k in self.o.fixed_headers:
                        msg[k] = self.o.fixed_headers[k]

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

    def ack(self, m: sarracenia.Message) -> bool:
        """ Acknowledge a received message
        """
        if not self.is_subscriber:
            logger.error("getting from a publisher")
            return False

        # silent success. retry messages will not have an ack_id, and so will not require acknowledgement.
        if not 'ack_id' in m:
            #logger.warning( f"no ackid present" )
            return True

        # pass the ack_id to the AMQP thread and hope it works
        # FIXME: check if it was acked successfully?
        try:
            self._ack_q.put(m['ack_id']['tag'])
            # trigger the ack in the thread (on_timer_task will run)
            self.reactor.schedule(0, self.client)
            logger.debug(f"requested for {m['ack_id']}")
            del m['ack_id']
            m['_deleteOnPost'].remove('ack_id')
            return True
        except Exception as e:
            logger.warning(f"failed for {m['ack_id']}")

        return False

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
                time.sleep(1) # TODO

            # check again, fail if it didn't connect
            if not self.__is_connected():
                logger.error("connection to broker was closed/broken and could not be re-opened")
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
            # (NOTE: set post_format swim or post_format navcanada in config file)
            raw_body, properties, content_type = PostFormat.exportAny(sr3_msg, version, self.o['topicPrefix'], self.o)

            if raw_body is not None and len(raw_body) <= 0:
                logger.warning(f"message body is empty (properties: {properties})")

            # address to publish to is post_topicPrefix + a dynamic topic
            # FIXME: topic separator should be configurable
            address = properties['topic']
            del properties['topic']

            # Address length limit is broker-specific
            # Solace limits addresses to 250 bytes and 128 levels: https://docs.solace.com/Messaging/SMF-Topics.htm
            if len(address) > 250:
                logger.error(f"message address is too long (>250), truncating. address: {address}")
                address = address[:250]

            # create AMQP1 message object to be published
            # postformat stuff determines *what* the body is. For SWIM/NAVCANADA, the body is the inline content.
            # for sr3 format, I think the body would be the JSON message itself.
            amqp1_msg = Message(address=address, body=raw_body, durable=self.o.get('persistent', True))
            amqp1_msg.properties = properties
            amqp1_msg.content_type = content_type

            if self.o['messageDebugDump']:
                logger.info(f"trying to publish raw message: {amqp1_msg} (format: {version})")
            else:
                logger.debug(f"trying to publish raw message: {amqp1_msg} (format: {version})")

            result = self.client.publish(amqp1_msg)

            if result:
                    self.metrics['txGoodCount'] += 1
                    self.metrics['txByteCount'] += len(raw_body)
                    if properties:
                        self.metrics['txByteCount'] += len(''.join(str(properties)))
                    self.metrics['txLast'] = sarracenia.nowstr()
            else:
                self.metrics['txBadCount'] += 1
                self.close()

            # for logging
            if not 'posts' in message:
                message['posts'] = []
            message['posts'].append( { 'broker':str(self.o['broker']), 'topic': address} )
            message['_deleteOnPost'].add('posts')

            return result

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
        self.broker = None
