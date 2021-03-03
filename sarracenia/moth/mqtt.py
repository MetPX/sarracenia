import copy
import json
import logging
import paho.mqtt.client 
from sarracenia.moth import Moth
from sarracenia.flowcb.gather import msg_validate,msg_dumps
import ssl
import time


logger = logging.getLogger(__name__)

default_options = {
   'batch' : 25,
   'clean_session': False,
   'mqtt_v5': False,
   'prefetch': 25,
   'qos' : 1,
   'topicPrefix' : [ 'v03' ]
}


class MQTT(Moth):
    """
       Message Queue Telemetry Transport support.
       problems with MQTT:
           lack of explicit acknowledgements (in paho library) means ack's happen without the
           application being able to process the messages... potential for message loss of
           whatever is queued... this is not good for reliability.  Don't know if this is a protocol
           problem, or just a defect in the paho library.

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
        

        if self.o['mqtt_v5']:
            self.proto_version=paho.mqtt.client.MQTTv5
        else:
            self.proto_version=paho.mqtt.client.MQTTv311

        ebo=1
        if is_subscriber:
            self.__getSetup(self.o) 
        else:
            self.__putSetup(self.o)
        

    def __sub_on_connect(client, userdata, flags, rc):
        logger.info( paho.mqtt.client.connack_string(rc) )

        if rc != paho.mqtt.client.MQTT_ERR_SUCCESS:
            client.connection_in_progress=False
            return

        # FIXME: enhancement could subscribe accepts multiple (subj, qos) tuples so, could do this in one RTT.
        for binding_tuple in client.o['bindings']:
            exchange, prefix, subtopic = binding_tuple
            subj = '/'.join( [exchange] + prefix + subtopic )
            res = client.subscribe( subj , qos=client.o['qos'] )
            logger.info( "subscribed to: %s, result: %s" % (subj, paho.mqtt.client.error_string(res)) )

    def __pub_on_connect(client, userdata, flags, rc):

        logger.info( paho.mqtt.client.connack_string(rc) )
        if rc != paho.mqtt.client.MQTT_ERR_SUCCESS:
            client.connection_in_progress=False

    def __sslClientSetup(self):
        """
          Initializse self.client SSL context, must be called after self.client is instantiated.
          return port number for connection.
      
        """
        if self.broker.scheme[-1] == 's' :
            port=8883
            logger.info('tls_rigour: %s' % self.o['tls_rigour'] )
            self.o['tls_rigour'] = self.o['tls_rigour'].lower()
            if self.o['tls_rigour'] == 'lax':
                    self.tlsctx = ssl.create_default_context()
                    self.tlsctx.check_hostname = False
                    self.tlsctx.verify_mode = ssl.CERT_NONE
     
            elif self.o['tls_rigour'] == 'strict':
                    self.tlsctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
                    self.tlsctx.options |= ssl.OP_NO_TLSv1
                    self.tlsctx.options |= ssl.OP_NO_TLSv1_1
                    self.tlsctx.check_hostname = True
                    self.tlsctx.verify_mode = ssl.CERT_REQUIRED
                    self.tlsctx.load_default_certs()
                    # TODO Find a way to reintroduce certificate revocation (CRL) in the future
                    #  self.tlsctx.verify_flags = ssl.VERIFY_CRL_CHECK_CHAIN
                    #  https://github.com/MetPX/sarracenia/issues/330
            elif self.o['tls_rigour'] == 'normal':
                self.tlsctx = ssl.create_default_context()
            else:
                self.logger.warning( "option tls_rigour must be one of:  lax, normal, strict")
            self.client.tls_set_context(self.tlsctx)
        else:
            port=1883

        if self.broker.port:
           port =  self.broker.port 
        return port

    def __getSetup(self, options):
        """
           Establish a connection to consume messages with.  
        """
        ebo = 1
        while True:
            try: 
                self.client = paho.mqtt.client.Client( clean_session=options['clean_session'], client_id=options['queue_name'], protocol=self.proto_version )
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
                    logger.info("paho library without auto_ack support. Loses data every crash or restart." )

                self.client.username_pw_set( self.broker.username, self.broker.password )

                self.client.connection_in_progress=True        
                self.client.connect( self.broker.hostname, port=self.__sslClientSetup() )

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
                self.client = paho.mqtt.client.Client( protocol=self.proto_version) 
                self.client.on_connect = MQTT.__pub_on_connect
                #dunno if this is a good idea.
                #self.client.max_queued_messages_set(options['prefetch'])
                self.client.username_pw_set( self.broker.username, self.broker.password )
                res = self.client.connect( options['broker'].hostname, port=self.__sslClientSetup()  )
                logger.info( 'connecting to %s, res=%s' % (options['broker'].hostname, res ) )
                self.client.connection_in_progress=True        
                count=1
                while not self.client.is_connected() and (count < 5):
                    logger.info("connecting loop" )
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
         
        if subtopic[0] != client.o['topicPrefix'][0]:
            message['exchange'] = subtopic[0]
            message['subtopic'] = subtopic[1+len(client.o['topicPrefix']):]
        else:
            message['subtopic'] = subtopic[len(client.o['topicPrefix']):]

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
        topic= '/'.join( [ exchange ] + self.o['topicPrefix'] + body['subtopic']  )
        topic = topic.replace('#', '%23')
        logger.info('topic: %s' % topic )

        del body['subtopic']

        while True:
            try:
                info = self.client.publish( topic=topic, payload=json.dumps(body), qos=1 )
                if info.rc == paho.mqtt.client.MQTT_ERR_SUCCESS: 
                    return #success...

            except Exception as ex:
                logger.error('Exception details: ', exc_info=True)

            self.close()
            self.__putSetup()
            
  
  
    def getCleanUp():
         pass

    def close(self):
         pass
