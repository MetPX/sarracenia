#!/usr/bin/python3

import amqplib.client_0_8 as amqp
import logging,logging.handlers
import sys, time

# ==========
# HostConnect
# ==========

class HostConnect:

   def __init__(self, logger = None):

       self.asleep     = False
       self.loop       = True

       self.connection = None
       self.channel    = None
       self.ssl        = False

       self.logger     = logger

       self.protocol   = 'amqp'
       self.host       = 'localhost'
       self.port       = None
       self.user       = 'guest'
       self.passwd     = 'guest'

       self.vhost      = '/'

       self.rebuilds   = []
       self.toclose    = []

       self.sleeping   = None

   def add_build(self,func):
       self.rebuilds.append(func)

   def add_sleeping(self,func):
       self.sleeping = func
       
   def close(self):
       for channel in self.toclose:
           self.logger.debug("closing channel_id: %s" % channel.channel_id)
           try:    channel.close()
           except: pass
       try:    self.connection.close()
       except: pass
       self.toclose    = []
       self.connection = None

   def connect(self):

       if self.sleeping != None :
          self.asleep = self.sleeping()

       if self.asleep : return

       while True:
          try:
               # connect
               self.logger.debug("Connecting %s %s (ssl %s)" % (self.host,self.user,self.ssl) )
               host = self.host
               if self.port   != None : host = host + ':%s' % self.port
               self.logger.debug("%s://%s:%s@%s%s ssl=%s" % (self.protocol,self.user,self.password,host,self.vhost,self.ssl))
               self.connection = amqp.Connection(host, userid=self.user, password=self.password, \
                                                 virtual_host=self.vhost,ssl=self.ssl)
               self.channel    = self.new_channel()
               self.logger.debug("Connected ")
               for func in self.rebuilds:
                   func()
               break
          except:
               (stype, svalue, tb) = sys.exc_info()
               self.logger.error("AMQP Sender cannot connect to: %s" % self.host)
               self.logger.error("Type=%s, Value=%s" % (stype, svalue))
               if not self.loop : sys.exit(1)
               self.logger.error("Sleeping 5 seconds ...")
               time.sleep(5)

   def new_channel(self):
       channel = self.connection.channel()
       self.toclose.append(channel)
       return channel

   def reconnect(self):
       self.close()
       self.connect()

   def set_credentials(self,protocol,user,password,host,port,vhost):
       self.protocol = protocol
       self.user     = user
       self.password = password
       self.host     = host
       self.port     = port
       self.vhost    = vhost

       if self.protocol == 'amqps' : self.ssl = True

   def set_url(self,url):
       self.protocol = url.protocol
       self.user     = url.user
       self.password = url.password
       self.host     = url.host
       self.port     = url.port
       self.vhost    = url.vhost

       if self.protocol == 'amqps' : self.ssl = True

# ==========
# Consumer
# ==========

class Consumer:

   def __init__(self,hostconnect):

      self.hc       = hostconnect
      self.logger   = self.hc.logger
      self.prefetch = 0

      self.exchange_type = 'topic'

      self.hc.add_build(self.build)

   def add_prefetch(self,prefetch):
       self.prefetch = prefetch

   def build(self):
       self.logger.debug("building consumer")
       self.channel = self.hc.new_channel()
       if self.prefetch != 0 :
          prefetch_size = 0      # dont care
          a_global      = False  # only apply here
          self.channel.basic_qos(prefetch_size,self.prefetch,a_global)
       
   def ack(self,msg):
       self.logger.debug("--------------> ACK")
       self.logger.debug("--------------> %s" % msg.delivery_tag )
       self.channel.basic_ack(msg.delivery_tag)

   def consume(self,queuename):

       msg = None

       if not self.hc.asleep :
              try :
                     msg = self.channel.basic_get(queuename)
              except :
                     if self.hc.loop :
                        self.hc.reconnect()
                        self.logger.info("consume resume ok")
                        if not self.hc.asleep : msg = self.consume(queuename)
       else:
              time.sleep(5)

       if msg == None : time.sleep(0.01)
       if msg != None : self.logger.debug("--------------> GOT")

       return msg

# ==========
# Exchange 
# ==========

class Exchange:

   def __init__(self,hostconnect,name):
       self.hc     = hostconnect
       self.logger = self.hc.logger
       self.name   = name
       self.exchange_type = 'topic'
       self.hc.add_build(self.build)

   def build(self):
       self.logger.debug("building exchange %s" % self.name)
       self.hc.channel.exchange_declare(self.name, self.exchange_type, auto_delete=False)

# ==========
# Publisher
# ==========

class Publisher:

   def __init__(self,hostconnect):
       self.hc     = hostconnect
       self.logger = self.hc.logger
       self.hc.add_build(self.build)

   def build(self):
       self.logger.debug("building publisher")
       self.channel = self.hc.new_channel()
       self.channel.tx_select()
       
   def publish(self,exchange_name,exchange_key,message,filename):
       try :
              hdr = {'filename': filename }
              msg = amqp.Message(message, content_type= 'text/plain',application_headers=hdr)
              self.channel.basic_publish(msg, exchange_name, exchange_key )
              self.channel.tx_commit()
              return True
       except :
              if self.hc.loop :
                 time.sleep(5)
                 self.hc.reconnect()
                 if self.hc.asleep : return False
                 return self.publish(exchange_name,exchange_key,message,filename)
              else:
                 (etype, evalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s" %  (etype, evalue))
                 self.logger.error("could not publish %s %s %s %s" % (exchange_name,exchange_key,message,filename))
                 return False


# ==========
# Queue
# ==========

class Queue:

   def __init__(self,hc,qname,auto_delete=False):

       self.hc          = hc
       self.logger      = self.hc.logger
       self.name        = qname
       self.qname       = qname
       self.auto_delete = False

       self.expire      = 0
       self.message_ttl = 0

       self.bindings    = []

       self.hc.add_build(self.build)

   def add_binding(self,exchange_name,exchange_key):
       self.bindings.append( (exchange_name,exchange_key) )

   def add_expire(self, expire):
       self.expire = expire

   def add_message_ttl(self, message_ttl):
       self.message_ttl = message_ttl

   def bind(self, exchange_name,exchange_key):
       self.channel.queue_bind(self.qname, exchange_name, exchange_key )

   def build(self):
       self.logger.debug("building queue %s" % self.name)
       self.channel = self.hc.new_channel()

       # queue arguments
       args = {}
       if self.expire > 0 :
          args   = {'x-expires' : self.expire }
       if self.message_ttl > 0 :
          args   = {'x-message-ttl' : self.message_ttl }

       # create queue
       self.qname, msg_count, consumer_count = \
       self.channel.queue_declare( self.name,
                                   passive=False, durable=False, exclusive=False,
                                   auto_delete=self.auto_delete,
                                   nowait=False,
                                   arguments= args )

       # queue bindings
       for exchange_name,exchange_key in self.bindings:
           self.bind(exchange_name, exchange_key )
