import copy
import json
import logging
import sys
import sarracenia

logger = logging.getLogger(__name__)

default_options = {
    'acceptUnmatched': True,
    'batch': 100,
    'bindings': [],
    'broker': None,
    'exchange': 'xpublic',
    'expire': 300,
    'inline': False,
    'inlineEncoding': 'guess',
    'inlineByteMax': 4096,
    'logFormat':
    '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s',
    'logLevel': 'info',
    'messageDebugDump': False,
    'message_strategy': {
        'reset': True,
        'stubborn': True,
        'failure_duration': '5m'
    },
    'message_ttl': 0,
    'topicPrefix': ['v03'],
    'tlsRigour': 'normal'
}

def ProtocolPresent(p) -> bool:
    if ( p in ['amqp', 'amqps' ] ) and sarracenia.extras['amqp']['present']:
       return True
    if ( p in ['mqtt', 'mqtts' ] ) and sarracenia.extras['mqtt']['present']:
       return True
    if p in sarracenia.extras:
        logger.critical( f"support for {p} missing, please install python packages: {' '.join(sarracenia.extras[p]['modules_needed'])}" )
    else:
        logger.critical( f"Protocol scheme {p} unsupported for communications with message brokers" )

    sys.exit(1)
    return False


class Moth():
    """
        Moth ... Messages Organized by Topic Headers
        (en français: Messages organisés par thème hierarchique. )

        A multi-protocol library for use by hierarchical message passing implementations,
        (messages which have a 'topic' header that is used for routing by brokers.)
 
        - regardless of protocol, the message format returned should be the same.
        - the message is turned into a sarracenia.Message object, which acts like a python 
          dictionary, corresponding to key-value pairs in the message body, and properties.
        - topic is a special key that may end up in the message body, or some sort of property
          or metadata.
        - the protocol should support acknowledgement under user control. Such control indicated
          by the presence of an entry_point called "ack". The entry point accepts "ack_id" as
          a message identifier to be passed to the broker. Whatever protocol symbol is used
          by the protocol, it is passed through this message property. Examples:
          in rabbitmq/amqp ack takes a "delivery_tag" as an argument, in MQTT, it takes a "message-id"
          so when receiving an AMQP message, the m['ack_id'] is assigned the delivery_tag from the message. 
        - There is a special dict item:  "_DeleteOnPost",  
          to identify keys which are added only for local use.
          they will be removed from the message when publishing.
          examples:  topic (sent outside body), message-id (used for acknowledgements.)
          new_basedir, ack_id, new\_... (settings...)

        Intent is to be specialized for topic based data distribution (MQTT style.)
        API to allow pass-through of protocol specific properties, but apply templates for genericity.

        Target protocols (and corresponding libraries.): AMQP, MQTT, ?

        Things to specify:

        * broker

        * topicPrefix

        * subTopic  

        * id   (queue for amqp, id for mqtt)

        this library knows nothing about Sarracenia, the only code used from sarracenia is to interpret
        duration properties, from the root sarracenia/__init__.py, the broker argument from sarracenia.credentials
  
        usage::

           c= Moth( broker, True, '5m', { 'batch':1 } )

           c.newMessages()
           # if there are new messages from a publisher, return them, otherwise return
           # an empty list []].
             
           p=Moth( broker, True, '5m', { 'batch':1 }, True )

           p.putNewMessage()

           p.close()
           # tear down connection.     
  
        Initialize a broker connection. Connections are unidirectional.
        either for subscribing (with subFactory) or publishing (with pubFactory.)
       
        The factories return objects subclassed to match the protocol required
        by the broker argument.

        arguments to the factories are:

        * broker ... the url of the broker to connect to.

        * props is a dictionary or properties/parameters.

        * supplied as overrides to the default properties listed above.

        Some may vary among protocols::
 
          Protocol     library implementing    URL to select
          --------     --------------------    -------------

          AMQPv0.9 --> amqplib from Celery --> amqp, amqps

          AMQPv0.9 --> pika                --> pika, pikas

          MQTTv3   --> paho                --> mqtt, mqtts

          AMQPv1.0 --> qpid-proton         --> amq1, amq1s



       **messaging_strategy**

       how to manage the connection. Covers whether to treat the connection
       as new or assume it is set up. Also, If something goes wrong.  
       What should be done. 
         
       * reset: on startup... erase any state, and re-initialize.

       * stubborn: If set to True, loop forever if something bad happens.  
         Never give up. This sort of setting is desired in operations, especially unattended.
         if set to False, may give up more easily.

       * failure_duration is to advise library how to structure connection service level.
          
         * 5m - make a connection that will recover from transient errors of a few minutes,
           but not tax the broker too much for prolonged outages.

         * 5d - duration outage to striving to survive connection for five days.

       Changing recovery_strategy setting, might result in having to destroy and re-create 
       consumer queues (AMQP.)

       **Options**

       **both**

       * 'topicPrefix' : [ 'v03' ]

       * 'messageDebugDump': False, --> enable printing of raw messages.

       * 'inline': False,  - Are we inlining content within messages?

       * 'inlineEncoding': 'guess', - what encoding should we use for inlined content?

       * 'inlineByteMax': 4096,  - Maximum size of messages to inline.

       **for get**

       *  'batch'  : 100  # how many messages to get at once

       *  'broker' : an sr_broker ?

       *  'Queue'  : Mandatory, name of a queue. (only in AMQP... hmm...)

       *  'bindings' : [ list of bindings ]

       *  'loop'

       **optional:**

       *  'message_ttl'    

       **for put:**

       *   'exchange' (only in AMQP... hmm...)
       

    """
    @staticmethod
    def subFactory(broker, props) -> 'Moth':

        if not broker :
            logger.error('no broker specified')
            return None

        if not hasattr(broker,'url'):
            logger.error('invalid broker url')
            return None

        if not ProtocolPresent(broker.url.scheme):
           logger.error('unknown broker scheme/protocol specified')
           return None

        for sc in Moth.__subclasses__():
            if (broker.url.scheme == sc.__name__.lower()) or (
                (broker.url.scheme[0:-1] == sc.__name__.lower()) and
                (broker.url.scheme[-1] == 's')):
                return sc(broker, props, True)
        logger.error('broker intialization failure')
        return None

    @staticmethod
    def pubFactory(broker, props) -> 'Moth':
        if not broker:
            logger.error('no broker specified')
            return None

        if not hasattr(broker,'url'):
            logger.error('invalid broker url')
            return None

        if not ProtocolPresent(broker.url.scheme):
           logger.error('unknown broker scheme/protocol specified')
           return None

        for sc in Moth.__subclasses__():
            if (broker.url.scheme == sc.__name__.lower()) or (
                (broker.url.scheme[0:-1] == sc.__name__.lower()) and
                (broker.url.scheme[-1] == 's')):
                return sc(broker, props, False)

        # ProtocolPresent test should ensure that we never get here...
        logger.error('broker intialization failure')
        return None

    def __init__(self, broker, props=None, is_subscriber=True) -> None:
        """
           If is_subscriber=True, then this is a consuming instance.
           expect calls to get* routines.

           if is_subscriber=False, then expect/permit only calls to put*
        """

        self.is_subscriber = is_subscriber
        self.metrics = {}
        self.metricsReset()

        if (sys.version_info.major == 3) and (sys.version_info.minor < 7):
            self.o = {}
            for k in default_options:
                if k == 'masks':
                    self.o[k] = default_options[k]
                else:
                    self.o[k] = copy.deepcopy(default_options[k])
        else:
            self.o = copy.deepcopy(default_options)

        if props is not None:
            self.o.update(props)

        self.broker = broker

        me = 'sarracenia.moth.Moth'

        # apply settings from props.
        if 'settings' in self.o:
            if me in self.o['settings']:
                for s in self.o['settings'][me]:
                    self.o[s] = self.o['settings'][me][s]

        logging.basicConfig(format=self.o['logFormat'],
                            level=getattr(logging, self.o['logLevel'].upper()))

    def ack(self, message) -> None:
        """
          tell broker that a given message has been received.

          ack uses the 'ack_id' property to send an acknowledgement back to the broker.
        """
        logger.error("ack unimplemented")

    @property
    def default_options(self) -> dict:
        """
        get default properties to override, used by client for validation. 

        """
        return Moth.__default_options

    def getNewMessage(self) -> sarracenia.Message:
        """
        If there is one new message available, return it. Otherwise return None. Do not block.

        side effects:
            metrics.
            self.metrics['RxByteCount'] should be incremented by size of payload.
            self.metrics['RxGoodCount'] should be incremented by 1 if a good message is received.
            self.metrics['RxBadCount'] should be incremented by 1 if an invalid message is received (&discarded.)
        """
        logger.error("getNewMessage unimplemented")
        return None

    def newMessages(self) -> list:
        """
        If there are new messages available from the broker, return them, otherwise return None.

        On Success, this routine returns immediately (non-blocking) with either None, or a list of messages.

        On failure, this routine blocks, and loops reconnecting to broker, until interaction with broker is successful.
        
        """
        logger.error("NewMessages unimplemented")
        return []

    def putNewMessage(self, message, content_type='application/json') -> bool:
        """
           publish a message as set up to the given topic.

           return True is succeeded, False otherwise.

           side effect
            self.metrics['TxByteCount'] should be incremented by size of payload.
            self.metrics['TxGoodCount'] should be incremented by 1 if a good message is received.
            self.metrics['TxBadCount'] should be incremented by 1 if an invalid message is received (&discarded.)
        """
        logger.error("putNewMessage unimplemented")
        return False

    def metricsReset(self) -> None:
        self.metrics['rxByteCount'] = 0
        self.metrics['rxGoodCount'] = 0
        self.metrics['rxBadCount'] = 0
        self.metrics['txByteCount'] = 0
        self.metrics['txGoodCount'] = 0
        self.metrics['txBadCount'] = 0

    def metricsReport(self) -> tuple:
        return self.metrics

    def close(self) -> None:
        """
           tear down an existing connection.
        """
        logger.error("close unimplemented")

    def cleanup(self) -> None:
        """
          get rid of server-side resources associated with a client. (queues/id's, etc...)
        """
        if self.is_subscriber:
            self.getCleanUp()
        else:
            self.putCleanUp()

if sarracenia.extras['amqp']['present']:
    import sarracenia.moth.amqp

if sarracenia.extras['mqtt']['present']:
    import sarracenia.moth.mqtt
