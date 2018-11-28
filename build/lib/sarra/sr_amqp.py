#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SarraDocumentation
#
# sr_amqp.py : python3 utility tools from python's amqplib
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Sep 22 10:41:32 EDT 2015
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
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

try   : import amqplib.client_0_8 as amqp
except: pass

try   : import pika
except: pass

import logging, os, random, sys, time

try :    
         from sr_util            import *
except : 
         from sarra.sr_util      import *

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

       self.rebuilds   = []
       self.toclose    = []

       self.sleeping   = None

       self.pika_available    = 'pika'    in sys.modules
       self.amqplib_available = 'amqplib' in sys.modules

       self.use_pika          = self.pika_available

   def add_build(self,func):
       self.rebuilds.append(func)

   def add_sleeping(self,func):
       self.sleeping = func
       
   def close(self):
       for channel in self.toclose:
           if self.use_pika : cid = channel.channel_number
           else:              cid = channel.channel_id
           self.logger.debug("closing channel_id: %s" % cid)
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
               self.logger.debug("%s://%s:<pw>@%s%s ssl=%s" % (self.protocol,self.user,host,self.vhost,self.ssl))
               if self.use_pika:
                      self.logger.debug("PIKA is used")
                      logger = logging.getLogger('pika')
                      logger.setLevel(logging.CRITICAL)
                      credentials = pika.PlainCredentials(self.user, self.password)
                      parameters  = pika.connection.ConnectionParameters(self.host,self.port,self.vhost,credentials,ssl=self.ssl)
                      self.connection = pika.BlockingConnection(parameters)
               else:
                      self.logger.debug("AMQPLIB is used")
                      # dont know why... need to raise an exception when problem
                      try   :
                              self.connection = amqp.Connection(host, userid=self.user, password=self.password, \
                                                                virtual_host=self.vhost,ssl=self.ssl)
                      except: raise Exception("amqp.Connection failed")

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

   def exchange_declare(self,exchange,edelete=False,edurable=True):
       try    :
                    self.channel.exchange_declare(exchange, 'topic', auto_delete=edelete,durable=edurable)
                    self.logger.info("declaring exchange %s (%s@%s)" % (exchange,self.user,self.host))
       except :
                    (stype, svalue, tb) = sys.exc_info()
                    self.logger.error("could not declare exchange %s (%s@%s)" % (exchange,self.user,self.host))
                    self.logger.error("Type=%s, Value=%s" % (stype, svalue))

   def exchange_delete(self,exchange):

       # never delete basic and permanent exchanges...

       if exchange in ['xpublic','xreport'] :
          self.logger.info("exchange %s remains" % exchange)
          return

       if exchange.startswith('xwinnow') :
          self.logger.info("exchange %s remains" % exchange)
          return

       # proceed for all others
       try    :
                    self.channel.exchange_delete(exchange)
                    self.logger.info("deleting exchange %s (%s@%s)" % (exchange,self.user,self.host))
       except :
                    (stype, svalue, tb) = sys.exc_info()
                    self.logger.error("could not delete exchange %s (%s@%s)" % (exchange,self.user,self.host))
                    self.logger.error("Type=%s, Value=%s" % (stype, svalue))


   def new_channel(self):
       channel = self.connection.channel()
       self.toclose.append(channel)
       return channel

   def queue_delete(self,queue_name):
       self.logger.info("deleting queue %s (%s@%s)" % (queue_name,self.user,self.host))
       try    :
                    self.channel.queue_delete(queue_name)
       except :
                    (stype, svalue, tb) = sys.exc_info()
                    error_str = '%s' % svalue
                    if 'NOT_FOUND' in error_str : return
                    self.logger.error("could not delete queue %s (%s@%s)" % (queue_name,self.user,self.host))
                    self.logger.error("Type=%s, Value=%s" % (stype, svalue))

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
       if self.vhost    == None    : self.vhost = '/'
       if self.vhost    == ''      : self.vhost = '/'

   def set_url(self,url):
       self.protocol = url.scheme
       self.user     = url.username
       self.password = url.password
       self.host     = url.hostname
       self.port     = url.port
       self.vhost    = url.path

       if self.protocol == 'amqps' : 
          self.ssl = True
          if self.port == None :
               self.port=5671

       if self.vhost    == None    : self.vhost = '/'
       if self.vhost    == ''      : self.vhost = '/'

   def set_pika(self,pika=True):

       self.use_pika = pika

       # good choices

       if self.pika_available    and     pika: return
       if self.amqplib_available and not pika: return

       # failback choices

       if self.pika_available    and not pika:
          self.logger.warning("amqplib unavailable : using pika")
          self.use_pika = True
          return

       if self.amqplib_available and     pika:
          self.logger.warning("pika unavailable : using amqplib")
          self.use_pika = False
          return

       # nothing available

       if not self.pika_available and not self.amqplib_available :
          self.logger.error("pika unavailable, amqplib unavailable")
          os._exit(1)


# ==========
# Consumer
# ==========

class Consumer:

   def __init__(self,hostconnect):

      self.hc       = hostconnect
      self.logger   = self.hc.logger
      self.prefetch = 20
      self.channel  = None

      self.exchange_type = 'topic'

      self.hc.add_build(self.build)

      self.retry_msg = raw_message(self.logger)

      self.for_pika_msg  = None
      if self.hc.use_pika :
         self.for_pika_msg = raw_message(self.logger)

   def add_prefetch(self,prefetch):
       self.prefetch = prefetch

   def build(self):
       self.logger.debug("building consumer")
       self.channel = self.hc.new_channel()
       # MG : seems important to have, but behave correctly without it
       self.channel.basic_recover(requeue=True)
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
                      if self.hc.use_pika :
                           #self.logger.debug("consume PIKA is used")
                           method_frame, properties, body = self.channel.basic_get(queuename)
                           if method_frame and properties and body :
                              self.for_pika_msg.pika_to_amqplib(method_frame, properties, body )
                              msg = self.for_pika_msg
                      else:
                              #self.logger.debug("consume AMQPLIB is used")
                              msg = self.channel.basic_get(queuename)
              except :
                     (stype, value, tb) = sys.exc_info()
                     self.logger.error("sr_amqp/consume Type: %s, Value: %s" % (stype, value))
                     self.logger.error("Could not consume in queue %s" % queuename )
                     if self.hc.loop :
                        self.hc.reconnect()
                        self.logger.debug("consume resume ok")
                        if not self.hc.asleep : msg = self.consume(queuename)
       else:
              time.sleep(5)

       if msg != None : msg.isRetry = False

       return msg

# ==========
# Publisher
# ==========

class Publisher:

   def __init__(self,hostconnect):
       self.hc     = hostconnect
       self.logger = self.hc.logger
       self.hc.add_build(self.build)
       self.iotime = 30
       self.restore_exchange = None
       self.restore_queue    = None

   def build(self):
       self.channel = self.hc.new_channel()
       if self.hc.use_pika :  self.channel.confirm_delivery()
       else:                  self.channel.tx_select()

   def isAlive(self):
       if not hasattr(self,'channel') : return False
       alarm_set(self.iotime)
       try:
               if self.hc.use_pika: self.channel.confirm_delivery()
               else:                self.channel.tx_select()
       except:
               alarm_cancel()
               return False
       alarm_cancel()
       return True

   def publish(self,exchange_name,exchange_key,message,mheaders,mexp=0):
       try :
              if self.hc.use_pika :
                     #self.logger.debug("publish PIKA is used")
                     if mexp :
                        expms = '%s' % mexp
                        properties = pika.BasicProperties(content_type='text/plain', delivery_mode=1, headers=mheaders,expiration=expms)
                     else:
                        properties = pika.BasicProperties(content_type='text/plain', delivery_mode=1, headers=mheaders)
                     self.channel.basic_publish(exchange_name, exchange_key, message, properties, True )
              else:
                     #self.logger.debug("publish AMQPLIB is used")
                     if mexp :
                        expms = '%s' % mexp
                        msg = amqp.Message(message, content_type= 'text/plain',application_headers=mheaders,expiration=expms)
                     else:
                        msg = amqp.Message(message, content_type= 'text/plain',application_headers=mheaders)
                     self.channel.basic_publish(msg, exchange_name, exchange_key )
                     self.channel.tx_commit()
              return True
       except :
              if self.hc.loop :
                 (stype, value, tb) = sys.exc_info()
                 self.logger.error("sr_amqp/publish: %s, Value: %s" % (stype, value))
                 self.logger.error("Sleeping 5 seconds ... and reconnecting")
                 time.sleep(5)
                 self.hc.reconnect()
                 if self.hc.asleep : return False
                 return self.publish(exchange_name,exchange_key,message,mheaders,mexp)
              else:
                 (etype, evalue, tb) = sys.exc_info()
                 self.logger.error("sr_amqp/publish 2 Type: %s, Value: %s" %  (etype, evalue))
                 self.logger.error("could not publish %s %s %s %s" % (exchange_name,exchange_key,message,mheaders))
                 return False

   def restore_clear(self):
       if self.restore_queue and self.restore_exchange :
          try   : self.channel.queue_unbind( self.restore_queue, self.restore_exchange, '#' )
          except: pass
          self.restore_queue    = None

       if self.restore_exchange:
          try   : self.channel.exchange_delete( self.restore_exchange )
          except: pass
          self.restore_exchange = None

   def restore_set(self,parent):
       try   :
              self.restore_queue      = parent.restore_queue
              self.restore_exchange   = parent.post_exchange 
              self.restore_exchange  += '.%s.%s.restore.' % (parent.program_name,parent.config_name)
              self.restore_exchange  += str(random.randint(0,100000000)).zfill(8)
              self.channel.exchange_declare( self.restore_exchange, 'topic', auto_delete=True, durable=False)
              self.channel.queue_bind( self.restore_queue, self.restore_exchange, '#' )
       except:
              (etype, evalue, tb) = sys.exc_info()
              self.logger.error("sr_amqp/restore_set Type: %s, Value: %s" %  (etype, evalue))
              self.logger.error("restore_set exchange %s queuename %s" % (self.restore_exchange,self.restore_queue))
              os._exit(1)

# ==========
# Queue
# ==========

class Queue:

   def __init__(self,hc,qname,auto_delete=False,durable=False,reset=False):

       self.hc          = hc
       self.logger      = self.hc.logger
       self.name        = qname
       self.qname       = qname
       self.auto_delete = False
       self.durable     = durable
       self.reset       = reset

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

       # reset 
       if self.reset :
          try    : self.channel.queue_delete( self.name )
          except : self.logger.debug("could not delete queue %s (%s@%s)" % (self.name,self.hc.user,self.hc.host))
                  
       # declare queue

       msg_count = self.declare()

       # something went wrong
       if msg_count == -1 : return

       # no bindings... in declare mode

       if len(self.bindings) == 0 :
          self.logger.debug("queue build done in declare mode")
          return

       # queue bindings
       exchange_ok = None
       for exchange_name,exchange_key in self.bindings:
           self.logger.debug("binding queue to exchange=%s with key=%s" % (exchange_name,exchange_key))
           try:
              self.bind(exchange_name, exchange_key )
              exchange_ok = exchange_name
           except : 
              self.logger.error( "bind queue: %s to exchange: %s with key: %s failed.." % \
                                 (self.name,exchange_name, exchange_key ) )
              self.logger.error( "Permission issue with %s@%s or exchange %s not found." % \
                                 (self.hc.user,self.hc.host,exchange_name ) )

       # always allow pulse binding... use last exchange_name
       if exchange_ok :
           exchange_key = 'v02.pulse.#'
           self.logger.debug("binding queue to exchange=%s with key=%s (pulse)" % (exchange_name,exchange_key))
           try:
              self.bind(exchange_name, exchange_key )
           except : 
              self.logger.error( "bind queue: %s to exchange: %s with key: %s failed.." % \
                                 (self.name,exchange_name, exchange_key ) )
              self.logger.error( "Permission issue with %s@%s or exchange %s not found." % \
                                 (self.hc.user,self.hc.host,exchange_name ) )
       else:
           self.logger.warning( "this process will not receive pulse message")

       self.logger.debug("queue build done")

   def declare(self):
       self.logger.debug("declaring queue %s" % self.name)

       # queue arguments
       args = {}
       if self.expire      > 0 : args['x-expires']     = self.expire
       if self.message_ttl > 0 : args['x-message-ttl'] = self.message_ttl

       # create queue
       try:
           if self.hc.use_pika:
                  #self.logger.debug("queue_declare PIKA is used")
                  q_dclr_ok = self.channel.queue_declare( self.name,
                                       passive=False, durable=self.durable, exclusive=False,
                                       auto_delete=self.auto_delete,
                                       arguments= args )

                  method = q_dclr_ok.method

                  self.qname, msg_count, consumer_count = method.queue, method.message_count, method.consumer_count

           else:
                  #self.logger.debug("queue_declare AMQPLIB is used")
                  self.qname, msg_count, consumer_count = \
                      self.channel.queue_declare( self.name,
                                          passive=False, durable=self.durable, exclusive=False,
                                          auto_delete=self.auto_delete,
                                          nowait=False,
                                          arguments= args )

           self.logger.debug("queue declare done")
           return msg_count

       except : 
              self.logger.error( "queue declare: %s failed...(%s@%s) permission issue ?" % (self.name,self.hc.user,self.hc.host))
              (stype, svalue, tb) = sys.exc_info()
              self.logger.error("sr_amqp/build Type: %s, Value: %s" %  (stype, svalue))
              return -1
