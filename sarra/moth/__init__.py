
"""
  Moth ... Messages Organized by Topic Headers

  A multi-protocol library for use by hierarchical message passing implementations,
  (messages which have a 'topic' header that is used for routing by brokers.)
 
       - regardless of protocol, the message format returned should be the same.
       - the message is turned into a python dictionary, corresponding to key-value pairs
         in the message body, and properties.
       - topic is special key that may end up in the message body, or some sort of property
         or metadata.
       - There is a special dict item:  "_DeleteOnPost"
         to identify keys which are added only for local use.
         they will be removed from the message when publishing.
         examples:  topic (sent outside body), message-id (used for acknowledgements.)
                    new_basedir, new_... (settings...)

  intent is to be specialized for topic based data distribution (MQTT style.)
  API to allow pass-through of protocol specific properties, but apply templates for genericity.

  Target protocols (and corresponding libraries.)

  Things to specify:
  	broker
	topicPrefix
        subTopic  
        id   (queue for amqp, id for mqtt)

  this library knows nothing about Sarracenia, the only code used from sarra is to interpret
  duration properties, from sr_util.
  
  usage:
     c= Moth( broker, True, '5m', { 'batch':1 } )

     c.newMessages()()
       - if there are new messages from a publisher, return them, otherwise return
         an empty list []].
       
     p=Moth( broker, True, '5m', { 'batch':1 } )
     p.post_new_message()

     p.close()
       - tear down connection.     


"""
import copy
import logging

logger = logging.getLogger( __name__ )

default_options = { 
           'accept_unmatch':True,
           'batch': 100, 
           'bindings':[], 
           'broker': None, 
           'inline': False,
           'inline_encoding': 'guess',
           'inline_max': 4096,
           'logFormat' : '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s',
           'logLevel': 'info',
           'message_strategy': { 
                 'reset': True, 'stubborn' : True, 'failure_duration':'5m' 
           }
}


class Moth():
    

    def __init__( self, broker, props=None, is_subscriber=True ):
       """
       initialize a broker connection. Connections are unidirectional.
       either for subscribing or publishing.

       props is a dictionary or properties/parameters.
       supplied as overrides to the default properties listed above.

       Some may vary among protocols.

       Protocol     library implementing    URL to select
       --------     --------------------    -------------

       AMQPv0.9 --> amqplib from Celery --> amqp, amqps
       AMQPv0.9 --> pika                --> pika, pikas
       MQTTv3   --> paho                --> mqtt, mqtts
       AMQPv1.0 --> qpid-proton         --> amq1, amq1s


       If is_subscriber=True, then this is a consuming instance.
       expect calls to get* routines.

       if is_subscriber=False, then expect/permit only calls to put*

       messaging_strategy:
        how to manage the connection. Covers whether to treat the connection
        as new or assume it is set up. Also, If something goes wrong.  
        What should be done. 
         
       reset:
         on startup... erase any state, and re-initialize.

       stubborn:  
         if set to True, loop forever if something bad happens.  Never give up.
         This sort of setting is desired in operations, especially unattended.
 
         if set to False, may give up more easily.

       failure_duration is to advise library how to structure connection service level.
          
       5m - make a connection that will recover from transient errors of a few minutes,
            but not tax the broker too much for prolonged outages.

       5d    - duration outage to striving to survive connection for five days.

       Changing recovery_strategy setting, might result in having to destroy and re-create 
       consumer queues (AMQP.)

       props


       both:
           'topic_prefix' : 'v03.post'

       for get:
           'batch'  : 100  # how many messages to get at once
           'broker' : an sr_broker ?
           'Queue'  : Mandatory, name of a queue. (only in AMQP... hmm...)
           'bindings' : [ list of bindings ]

           'loop'
        optional:
           'message_ttl'    

       for put:
           'exchange' (only in AMQP... hmm...)
       

       """

       protos=[]
       self.is_subscriber = is_subscriber

       self.props=copy.deepcopy(default_options)
       if props is not None:
           self.props.update(props)

       self.broker = broker

       me='sarra.moth.Moth'

       # apply settings from props.
       if 'settings' in self.props:
           if me in self.props['settings']:
               for s in self.props['settings'][me]:
                   self.props[s] = self.props['settings'][me][s]

       logging.basicConfig( format=self.props['logFormat'], level=getattr(logging, self.props['logLevel'].upper()) )

       """ relevant:
         https://stackoverflow.com/questions/18020074/convert-a-baseclass-object-into-a-subclass-object-idiomatically
         assmimilate in the vein of the Borg: "You will be assimilated." Turns the caller into child class.
       """
       for sc in Moth.__subclasses__() :
            purl = sc.url_proto(self)
            if self.broker.scheme[0:4] == purl :
                sc.__init__(self,broker,self.props)
                return
            protos.append(purl) 

       logger.critical( "unsupported broker URL. Pick one of: %s" % protos )

    @property
    def default_options():
        """
        get default properties to override, used by client for validation. 

        """
        return Moth.__default_options

    def url_proto(self):
        return "undefined"

    def getNewMessage( self ):
        """
        If there is one new message available, return it. Otherwise return None. Do not block.

        """
        logger.error("cleanup unimplemented")

    def getNewMessages( self ):
        """
        If there are new messages available from the broker, return them, otherwise return None.

        On Success, this routine returns immediately (non-blocking) with either None, or a list of messages.

        On failure, this routine blocks, and loops reconnecting to broker, until interaction with broker is successful.
        
        """
        logger.error("getNewMessages unimplemented")

    def ackMessage( self, m ):
        """
          tell broker that a given message has been received.
        """ 
        logger.error("ackMessage unimplemented")

    def putNewMessage( self, topic, body, headers, content_type ):
        """
           publish a message as set up to the given topic.
        """
        logger.error("putNewMessage unimplemented")


    def close(self):
        """
           tear down an existing connection.
        """
        logger.error("close unimplemented")

    def cleanup(self):
        """
          get rid of server-side resources associated with a client. (queues/id's, etc...)
        """
        logger.error("cleanup unimplemented")

import importlib.util

if importlib.util.find_spec("amqp"):
    import sarra.moth.amqp

if importlib.util.find_spec("paho"):
    import sarra.moth.mqtt

if importlib.util.find_spec("proton"):
    import sarra.moth.amq1

if importlib.util.find_spec("paho"):
    import sarra.moth.pika



