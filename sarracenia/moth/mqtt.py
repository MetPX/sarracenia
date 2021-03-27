import copy
import json
import logging
import paho.mqtt.client 
from sarracenia.moth import Moth
from sarracenia.flowcb.gather import msg_validate,msg_dumps
import ssl
import threading
import time


logger = logging.getLogger(__name__)

default_options = {
   'batch' : 25,
   'clean_session': False,
   'no': 0,
   'prefetch': 25,
   'qos' : 1,
   'topicPrefix' : [ 'v03' ]
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
           it to the new_messages data structure (protected by a mutex.)
           if the application crashes, the new_messages have not been ack'd to the sender... so it is
           likely that you will just get them later... could use for a shelf for new_messages,
           and sync it once in while... probably not worth it.
 
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

        self.proto_version=paho.mqtt.client.MQTTv5

        ebo=1
        if is_subscriber:
            self.__getSetup(self.o) 
        else:
            self.__putSetup(self.o)

        logger.info("note: mqtt support is newish, not very well tested")
        

    def __sub_on_disconnect(client, userdata, rc):
        logger.info( paho.mqtt.client.connack_string(rc) )

    def __sub_on_connect(client, userdata, flags, rc, properties=None):
        logger.info( paho.mqtt.client.connack_string(rc) )

        if rc != paho.mqtt.client.MQTT_ERR_SUCCESS:
            client.connection_in_progress=False
            return

        # FIXME: enhancement could subscribe accepts multiple (subj, qos) tuples so, could do this in one RTT.
        for binding_tuple in userdata.o['bindings']:
            exchange, prefix, subtopic = binding_tuple
            logger.info( "tuple: %s %s %s" % ( exchange, prefix, subtopic ) )
            subj = '/'.join( ['$share', userdata.o['queue_name'], exchange] + prefix + subtopic )

            (res, mid) = client.subscribe( subj , qos=userdata.o['qos'] )
            logger.info( "subscribed to: %s, result: %s" % (subj, paho.mqtt.client.error_string(res)) )

    def __pub_on_disconnect(client, userdata, rc ):
        logger.info( paho.mqtt.client.connack_string(rc) )

    def __pub_on_connect(client, userdata, flags, rc, properties=None):
        logger.info( paho.mqtt.client.connack_string(rc) )

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
                self.new_message_mutex = threading.Lock()

                cs=options['clean_session']
                if ('queue_name' in options ) and ( 'no' in options ):
                     cid = options['queue_name'] + '%02d' % options['no']
                else:
                     #cid = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
                     cid = None
                     cs=True

                self.client = paho.mqtt.client.Client( userdata=self, \
                        client_id=cid, protocol=paho.mqtt.client.MQTTv5 )

                #self.client.o = options
                self.new_message_mutex.acquire()
                self.client.new_messages = []
                self.new_message_mutex.release()
                self.client.connected=False
                self.client.on_connect = MQTT.__sub_on_connect
                self.client.on_disconnect = MQTT.__sub_on_disconnect
                self.client.on_message = MQTT.__on_message
                # defaults to 20... kind of a mix of "batch" and prefetch... 
                self.client.max_inflight_messages_set(options['batch']+options['prefetch'])
                if hasattr( self.client, 'auto_ack' ):
                    self.client.auto_ack( False )
                    logger.info("Switching off auto_ack for higher reliability. Using explicit acknowledgements." )
                else:
                    logger.info("paho library without auto_ack support. Loses data every crash or restart." )

                self.client.username_pw_set( self.broker.username, self.broker.password )
                self.client.connect( self.broker.hostname, port=self.__sslClientSetup() )
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
                self.client = paho.mqtt.client.Client( protocol=self.proto_version, userdata=self) 
                self.client.on_connect = MQTT.__pub_on_connect
                self.client.on_disconnect = MQTT.__pub_on_disconnect
                #dunno if this is a good idea.
                #self.client.max_queued_messages_set(options['prefetch'])
                self.client.username_pw_set( self.broker.username, self.broker.password )
                res = self.client.connect( options['broker'].hostname, port=self.__sslClientSetup()  )
                logger.info( 'connecting to %s, res=%s' % (options['broker'].hostname, res ) )

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

          FIXME: locking here is expensive... would like to group them ... 1st draft.
             could do a rotating set of batch size lists, and that way just change counters.
             and not lock individual messages  list[1], list[2], ... consumer consumes old lists...
             no locking needed, except to increment list index.... later.
        """
       
        try:
            message = json.loads(msg.payload.decode('utf-8'))
        except Exception as ex:
            logger.error( "ignored malformed message: %s" % msg.payload.decode('utf-8') )
            logger.error("decode error" % err)
            logger.error('Exception details: ', exc_info=True)
            return

        subtopic=msg.topic.split('/')
         
        if subtopic[0] != userdata.o['topicPrefix'][0]:
            message['exchange'] = subtopic[0]
            message['subtopic'] = subtopic[1+len(userdata.o['topicPrefix']):]
        else:
            message['subtopic'] = subtopic[len(userdata.o['topicPrefix']):]

        message['ack_id'] = msg.mid
        message['local_offset'] = 0
        message['_deleteOnPost'] = set( [ 'exchange', 'local_offset', 'ack_id', 'subtopic' ] )

        logger.info( "Message received: %s" % message )
        if msg_validate( message ):
            userdata.new_message_mutex.acquire()
            client.new_messages.append( message )
            userdata.new_message_mutex.release()
        else:
            logger.info( "Message dropped as invalid" )

    def putCleanUp(self):
        self.client.loop_stop()
        pass

    def getCleanUp(self):         
        self.client.loop_stop()
        pass

    def newMessages(self):
        """
           return new messages.

           FIXME: hate the locking... too fine grained, especially in on_message... just a 1st shot.

        """
        self.new_message_mutex.acquire()
        if len(self.client.new_messages) > self.o['batch'] :
            ml=self.client.new_messages[0:self.o['batch']]
            self.client.new_messages=self.client.new_messages[self.o['batch']:]
        else:
            ml=self.client.new_messages
            self.client.new_messages=[]
        self.new_message_mutex.release()
        return ml

    def getNewMessage(self):

        if len(self.client.new_messages) > 0: 
            self.new_message_mutex.acquire()
            m=self.client.new_messages[0]
            self.client.new_messages=self.client.new_messages[1:]
            self.new_message_mutex.release()
            return m
        else:
            return None
    
    def ack(self, m):
        if hasattr(self.client,'ack') and ('ack_id' in m):
            self.client.ack(m['ack_id'])
            del m['ack_id']
            m['_deleteOnPost'].remove('ack_id')

    def putNewMessage(self, body, content_type='application/json', exchange=None):
        """
          publish a message.
        """
        if self.is_subscriber:  #build_consumer
           logger.error("publishing from a consumer")
           return False
 
        if not self.client.is_connected():
           logger.error("no connection to publish to broker with")
           return False

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
                    logger.info("published {} to {} under: {} ".format(
                         body, exchange, topic))
 
                    return True #success...

            except Exception as ex:
                logger.error('Exception details: ', exc_info=True)

  
  
    def close(self):
        if self.client.is_connected():
            self.client.disconnect()
