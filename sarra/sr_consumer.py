#!/usr/bin/python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SarraDocumentation
#
# sr_consumer.py : python3 wraps consumer queue binding accept/reject
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  first shot     : Dec 11 10:26:22 EST 2015
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

import os,sys,random

try :    
         from sr_amqp           import *
         from sr_config         import *
         from sr_message        import *
except : 
         from sarra.sr_amqp     import *
         from sarra.sr_config   import *
         from sarra.sr_message  import *

# class sr_consumer

class sr_consumer:

    def __init__(self, parent):
        self.logger         = parent.logger
        self.logger.debug("sr_consumer __init__")
        self.parent         = parent

        self.build_connection()
        self.build_consumer()
        self.build_queue()
        self.build_message()
        self.build_logback()

    def build_connection(self):
        self.logger.debug("sr_consumer build_broker")

        self.broker     = self.parent.broker

        self.logger.info("AMQP  broker(%s) user(%s) vhost(%s)" % \
                        (self.broker.hostname,self.broker.username,self.broker.path) )

        self.hc = HostConnect( logger = self.logger )
        self.hc.set_url(self.broker)
        self.hc.connect()

    def build_consumer(self):
        self.logger.debug("sr_consumer build_consumer")

        self.queue_share = self.parent.queue_share
        self.consumer    = Consumer(self.hc)

        if self.queue_share :
            self.consumer.add_prefetch(1)

        self.consumer.build()

    def build_logback(self):
        self.logger.debug("sr_consumer build_logback")

        self.log_back     = self.parent.log_back
        self.msg.amqp_log = None

        if self.log_back :
           self.msg.amqp_log = Publisher(self.hc)
           self.msg.amqp_log.build()
           self.msg.exchange_log = 'xs_' + self.broker.username
           self.logger.info("AMQP  output:    exchange(%s) topic(%s)\n" % (self.msg.exchange_log,'v02.log.#') )

    def build_message(self):
        self.logger.debug("sr_consumer build_message")

        self.raw_msg  = None
        self.msg      = sr_message(self.logger)
        self.msg.user = self.broker.username

    def build_queue(self):
        self.logger.debug("sr_consumer build_queue")

        self.broker      = self.parent.broker
        self.bindings    = self.parent.bindings
        self.durable     = self.parent.durable
        self.expire      = self.parent.expire
        self.message_ttl = self.parent.message_ttl

        self.broker_str  = self.broker.geturl().replace(self.broker.password,'')

        # queue name 
        self.set_queue_name()

        # queue settings
        self.msg_queue   = Queue(self.hc,self.queue_name,durable=self.durable)

        if self.expire != None :
           self.msg_queue.add_expire(self.expire)

        if self.message_ttl != None :
           self.msg_queue.add_message_ttl(self.message_ttl)

        # queue bindings 

        for tup in self.bindings :
            exchange, key = tup
            self.logger.info('Binding queue %s with key %s from exchange %s on broker %s' % \
		            ( self.queue_name, key, exchange, self.broker_str ) )
            self.msg_queue.add_binding( exchange, key )

        # queue creation 
        self.msg_queue.build()

    def close(self):
        self.hc.close()

    def consume(self,use_pattern=True,accept_unmatch=False):

        # acknowledge last message... we are done with it
        if self.raw_msg != None : self.consumer.ack(self.raw_msg)

        # consume a new one
        self.raw_msg = self.consumer.consume(self.msg_queue.qname)
        if self.raw_msg == None : return False, self.msg


        # make use it as a sr_message

        try :
                 self.msg.from_amqplib(self.raw_msg)
                 self.logger.debug("notice %s " % self.msg.notice)
                 self.logger.debug("urlstr %s " % self.msg.urlstr)
        except :
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
                 self.logger.error("problem with message %s"% vars(self.raw_msg))
                 return None

        # make use of accept/reject

        if use_pattern :
           if not self.parent.isMatchingPattern(self.msg.urlstr,accept_unmatch) :
              self.logger.debug("Rejected by accept/reject options")
              return False,self.msg

        return True,self.msg

    def random_queue_name(self) :

        queuedir  = self.parent.user_queue_dir
        queuefile = '.' + self.parent.config_name + '.queue'
        queuepath = queuedir + os.sep + queuefile

        if os.path.isfile(queuepath) :
           f = open(queuepath)
           self.queue_name = f.read()
           f.close()
           return
        
        self.queue_name  = self.queue_prefix
        self.queue_name += '.'  + str(random.randint(0,100000000)).zfill(8)
        self.queue_name += '.'  + str(random.randint(0,100000000)).zfill(8)

        f = open(queuepath,'w')
        f.write(self.queue_name)
        f.close()

    def set_queue_name(self):

        self.broker       = self.parent.broker
        self.queue_prefix = 'q_'+ self.broker.username
        self.queue_name   = self.parent.queue_name

        if self.queue_name :
           if self.queue_prefix in self.queue_name : return
           self.logger.warning("non standard queue name %s" % self.queue_name )
           #self.queue_name = self.queue_prefix + '.'+ self.queue_name
           return

        self.random_queue_name()

# ===================================
# self_test
# ===================================

class test_logger:
      def silence(self,str):
          pass
      def __init__(self):
          self.debug   = self.silence
          self.error   = print
          self.info    = self.silence
          self.warning = print

def self_test():

    logger = test_logger()

    yyyy   = time.strftime("%Y",time.gmtime())
    opt1   = 'accept .*' + yyyy + '.*'
    opt2   = 'reject .*'

    #setup consumer to catch first post
    cfg = sr_config()
    cfg.defaults()
    cfg.logger         = logger
    cfg.debug          = False
    cfg.broker         = urllib.parse.urlparse("amqp://anonymous:anonymous@ddi.cmc.ec.gc.ca/")
    cfg.queue_share    = True
    cfg.log_back       = True
    cfg.bindings       = [ ( 'xpublic', 'v02.post.#') ]
    cfg.durable        = True
    cfg.expire         = 30
    cfg.message_ttl    = 30
    cfg.user_queue_dir = os.getcwd()
    cfg.config_name    = "test"
    cfg.queue_name     = None
    cfg.option( opt1.split()  )
    cfg.option( opt2.split()  )

    consumer = sr_consumer(cfg)

    #FIXME setup another consumer
    # from message... log ...  catch log messsage

    i = 0
    while True :
          ok, msg = consumer.consume(use_pattern=True,accept_unmatch=False)
          if ok: break

          i = i + 1
          if i == 100 : 
             msg = None
             break

    consumer.close()

    if msg != None :
       if yyyy in msg.notice :
           print("sr_consumer TEST PASSED")
           sys.exit(0)
       print("sr_consumer TEST Failed 1 wrong message")
       sys.exit(1)

    print("sr_consumer TEST Failed 2 no message")
    sys.exit(2)

# ===================================
# MAIN
# ===================================

def main():

    self_test()
    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()
