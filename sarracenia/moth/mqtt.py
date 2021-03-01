import copy
import json
import logging
import paho.mqtt.client as mqtt
from sarracenia.moth import Moth
from sarracenia.flowcb.gather import msg_validate
import time


logger = logging.getLogger(__name__)

default_options = {
   'batch' : 25,
   'clean_session': False,
   'mqtt_v5': False,
   'prefetch': 25,
   'qos' : 1,
   'topic_prefix' : [ 'v03' ]
}

"""
   MQTT v5, they added "reason codes, and there are a whole bunch.. they aren't there in mqttv3...
   so faking it?
"""

class MQTT(Moth):
    """
       Message Queue Telemetry Transport support.
       problems with MQTT:
           lack of explicit acknowledgements (in paho library) means ack's happen without the
           application being able to process the messages... potential for message loss of
           whatever is queued... this is not good for reliability.  Don't know if this is a protocol
           problem, or just a defect in the paho library.

      This is just a stub for now, proof of concept. things not checked:

      * 
    """
    def __init__(self, broker, options, is_subscriber):
        """

          MQTT connection instances...
          in AMQP: topic separator is dot (.) in MQTT, the topic separator is slash (/)
          have exchange arguments use protocol specific separator or mapped one?

        """

        super().__init__(broker, options, is_subscriber)

        self.o.update(default_options)
        self.o.update(options)

        logger.setLevel(getattr(logging, self.o['logLevel'].upper()))
        logger.info('options: %s' % sorted(self.o) )

        if self.o['mqtt_v5']:
            self.proto_version=mqtt.MQTTv5
        else:
            self.proto_version=mqtt.MQTTv311

        ebo=1
        if is_subscriber:
            self.__getSetup(self.o) 
        else:
            self.__putSetup(self.o)
        

    def __sub_on_connect(client, userdata, flags, rc):
        logger.info( mqtt.connack_string(rc) )

        if rc != mqtt.MQTT_ERR_SUCCESS:
            client.connection_in_progress=False

        # FIXME: enhancement could subscribe accepts multiple (subj, qos) tuples so, could do this in one RTT.
        for binding_tuple in client.o['bindings']:
            prefix, exchange, subtopic = binding_tuple
            subj = '/'.join( [exchange] + prefix + subtopic )
            res = client.subscribe( subj , qos=client.o['qos'] )
            logger.info( "subscribed to: %s, result: %s" % (subj, mqtt.error_string(res)) )

    def __pub_on_connect(client, userdata, flags, rc):

        logger.info( mqtt.connack_string(rc) )
        if rc != mqtt.MQTT_ERR_SUCCESS:
            client.connection_in_progress=False


    def __getSetup(self, options):
        """
           establish a connection to consume messages with.  
        """
        ebo = 1
        while True:
            try: 
                self.client = mqtt.Client( clean_session=options['clean_session'], client_id=options['queue_name'], protocol=self.proto_version )
                self.client.o = options
                self.client.new_messages = []
                self.client.connected=False
                self.client.on_connect = MQTT.__sub_on_connect
                self.client.on_message = MQTT.__on_message
                # defaults to 20... kind of a mix of "batch" and prefetch... 
                self.client.max_inflight_messages_set(options['batch']+options['prefetch'])
                if hasattr( self.client, 'auto_ack' ):
                    self.client.auto_ack( False )
                    logger.info("Switching off auto_ack for higher reliability. Using explicit acknowledgements." )
                else:
                    logger.info("paho library without auto_ack support" )

                self.client.username_pw_set( self.broker.username, self.broker.password )
                self.client.connection_in_progress=True        
                self.client.connect( self.broker.hostname )

                count=1
                while not self.client.is_connected() and (count < 5):
                     logger.debug("connecting loop" )
                     self.client.loop(1)
                     if not self.client.connection_in_progress:
                         break
                     count += 1
                     time.sleep(1)
 
                if self.client.is_connected(): 
                    self.client.loop_start()
                    return

            except Exception as err:
                logger.error("failed to {} with {}".format( self.broker.hostname, err))
                logger.error('Exception details: ', exc_info=True)

            if ebo < 60 : ebo *= 2
            time.sleep(ebo)


    def __putSetup(self, options):
        """
           establish a connection to allow publishing. 
        """
        ebo=1
        while True:
            try:
                self.post_client = mqtt.Client( protocol=self.proto_version) 
                self.post_client.on_connect = MQTT.__pub_on_connect
                #dunno if this is a good idea.
                #self.post_client.max_queued_messages_set(options['prefetch'])
                self.post_client.username_pw_set( self.broker.username, self.broker.password )
                res = self.post_client.connect( options['broker'].hostname )
                logger.info( 'connecting to %s, res=%s' % (options['broker'].hostname, res ) )
                self.post_client.connection_in_progress=True        
                count=1
                while not self.post_client.is_connected() and (count < 5):
                    logger.info("connecting loop" )
                    self.post_client.loop(1)
                    if not self.post_client.connection_in_progress:
                        break
                    count += 1
                    time.sleep(1)
         
                if self.post_client.is_connected(): 
                    self.post_client.loop_start()
                    return

            except Exception as err:
                logger.error("failed to {} with {}".format( self.broker.hostname, err))
                logger.error('Exception details: ', exc_info=True)

            if ebo < 60 : ebo *= 2
            time.sleep(ebo)
               
        
    def __on_message(client, userdata, msg):
        """
          callback to append messages received to new queue.
          MQTT only supports v03 messages, so always assumed to be JSON encoded.
        """
       
        try:
            message = json.loads(msg.payload.decode('utf-8'))
        except Exception as ex:
            logger.error( "ignored malformed message: %s" % msg.payload.decode('utf-8') )
            logger.error("decode error" % err)
            logger.error('Exception details: ', exc_info=True)
            return

        subtopic=msg.topic.split('/')
         
        if subtopic[0] != client.o['topic_prefix'][0]:
            message['exchange'] = subtopic[0]
            message['subtopic'] = subtopic[1+len(client.o['topic_prefix']):]
        else:
            message['subtopic'] = subtopic[len(client.o['topic_prefix']):]

        message['message-id'] = msg.mid
        message['_deleteOnPost'] = set( [ 'exchange', 'subtopic', 'message-id' ] )

        logger.info( "Message received: %s" % message )
        if msg_validate( message ):
            client.new_messages.append( message )
        else:
            logger.info( "Message dropped as invalid" )

    def putCleanUp(self):
        pass

    def getCleanUp(self):         
        pass

    def newMessages(self):

        ml=self.client.new_messages
        self.client.new_messages=[]
        return ml

    def getNewMessage(self):

        if len(self.client.new_messages) > 0: 
            m=self.client.new_messages[0]
            self.client.new_messages=self.client.new_messages[1:]
            return m
        else:
            return None
    
    def ack(self, m):
        if hasattr(self.client,'ack'):
            self.client.ack(m['message-id'])

    def putNewMessage(self, body, content_type='application/json', exchange=None):
        """
          publish a message.
        """
        if self.is_subscriber:  #build_consumer
           logger.error("publishing from a consumer")
           return None

        #body = copy.deepcopy(bd)
  
        if '_deleteOnPost' in body:
            # FIXME: need to delete because building entire JSON object at once.
            # makes this routine alter the message. Ideally, would use incremental
            # method to build json and _deleteOnPost would be a guide of what to skip.
            # library for that is jsonfile, but not present in repos so far.
            for k in body['_deleteOnPost']:
                if k == 'subtopic' : continue
                if k in body:
                    del body[k]
            del body['_deleteOnPost']
  
         
        if not exchange:
             if (type(self.o['exchange']) is list):
                  if (len(self.o['exchange']) > 1):
                      if 'post_exchange_split' in self.o:
                          # FIXME: assert ( len(self.o['exchange']) == self.o['post_exchange_split'] )
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
        topic= '/'.join( [ exchange ] + self.o['topic_prefix'] + body['subtopic']  )
        topic = topic.replace('#', '%23')
        logger.info('topic: %s' % topic )

        del body['subtopic']

        while True:
            try:
                info = self.post_client.publish( topic=topic, payload=json.dumps(body), qos=1 )
                if info.rc == mqtt.MQTT_ERR_SUCCESS: 
                    return #success...

            except Exception as ex:
                logger.error('Exception details: ', exc_info=True)

            self.close()
            self.__putSetup()
            
  
  
    def getCleanUp():
         pass

    def close(self):
         pass
