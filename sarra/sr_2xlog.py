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
# sr_2xlog.py : python3 program takes log messages from various source
#                    validate them and put the valid one in xlog
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Dec 16 15:36:43 EST 2015
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

import signal

#============================================================
# usage example
#
# sr_2xlog [options] [config] [start|stop|restart|reload|status]
#
# sr_subscriber logs back its downloads on the cluster it is subscribed to
# The sr_subscribe program are using exchange xs_"username"... for that
# This program validates these log message and if ok, integrate them in xlog
#
# conditions :
# exchangeS               = (from users.conf role subscriber)
#                         = [xs_subscriber1,xs_subscriber2...]
#                         = one instance per exchange
# topic                   = v02.log.#
# header['from_cluster']  = should be defined ... for log routing
# header['source]         = should be defined ... for log routing
#
# valid log messages are publish in xlog for log routing
#
#============================================================

try :    
         from sr_consumer        import *
         from sr_instances       import *
         from sr_message         import *
except : 
         from sarra.sr_consumer  import *
         from sarra.sr_instances import *
         from sarra.sr_message   import *

class sr_2xlog(sr_instances):

    def __init__(self,config=None,args=None):
        sr_instances.__init__(self,config,args)
        self.defaults()

        self.configure()

    def check(self):

        # no binding allowed

        if self.bindings != [] :
           self.logger.error("broker exchange, topic_prefix and subtopic are static in this program")
           self.bindings  = []

        # no queue name allowed

        if self.queue_name != None:
           self.logger.error("queue name forced in this program")
           self.queue_name =  None

        # scan users for role subscribe

        self.subscribe_users = {}

        i = 0
        for user in self.users :
            roles = self.users[user]
            if 'subscribe' in roles :
               self.subscribe_users[i] = user
               i = i + 1

        self.logger.debug("subscribers = %s " % self.subscribe_users)

        # recreate bindings with exchange from subscriber list

        self.exchanges = {}

        for i in self.subscribe_users :
            user = self.subscribe_users[i]
            exchange          = 'xs_'+ user
            key               = self.topic_prefix + '.' + self.subtopic
            self.exchanges[i] = (exchange,key)
            i = i + 1
        self.logger.debug("exchanges = %s " % self.exchanges)

        self.nbr_instances = len(self.subscribe_users)


    def close(self):
        self.consumer.close()

    def configure(self):

        # overwrite defaults

        self.broker               = self.manager
        self.topic_prefix         = 'v02.log'
        self.subtopic             = '#'

        # load/reload all config settings

        self.general()
        self.args   (self.user_args)
        self.config (self.user_config)

        # verify / complete settings

        self.check()


    def connect(self):

        # =============
        # create message if needed
        # =============

        if not hasattr(self,'msg'):
           self.msg = sr_message(self.logger)

        self.msg.user = self.broker.username

        # =============
        # consumer
        # =============

        self.consumer = sr_consumer(self)

        # =============
        # publisher... (publish back to consumer)  
        # =============

        self.publisher    = self.consumer.publish_back()


    def help(self):
        self.logger.info("Usage: %s [options] [config] [start|stop|restart|reload|status]  \n" % self.program_name )


    # =============
    # default_on_message  
    # =============

    def default_on_message(self):
        self.logger.debug("sr_2xlog default_on_message")

        # is the log message for this cluster

        if not 'from_cluster' in self.msg.headers or not 'source' in self.msg.headers :
           self.logger.info("skipped : no cluster or source in message")
           return False,self.msg

        # is the log message from a source on this cluster

        if not hasattr(self.msg,'log_user')  or self.msg.log_user != self.subscriber:
           self.logger.info("skipped : log_user is not subscriber %s " % self.subscriber)
           return False,self.msg

        # yup this is one valid message from that suscriber

        return True,self.msg

    # =============
    # default_on_post  
    # =============

    def default_on_post(self):

        # ok ship it back to the user exchange 

        exchange = 'xlog'

        ok = self.publisher.publish( exchange, self.msg.topic, self.msg.notice, self.msg.headers )
        if ok : self.logger.info("published to %s" % exchange)

        return True,self.msg


    # =============
    # process message  
    # =============

    def process_message(self):

        try  :
                 ok, self.msg = self.consumer.consume()
                 if not ok : return ok

                 self.logger.info("Received topic   %s" % self.msg.topic)
                 self.logger.info("Received notice  %s" % self.msg.notice)
                 self.logger.info("Received headers %s" % self.msg.hdrstr)

                 # invoke default_on_message

                 if not self.on_message :
                        self.logger.debug( "default_on_message called")
                        ok, self.msg = self.default_on_message()

                 # invoke on_message when provided
                 else :
                        self.logger.debug("on_message called")
                        ok, self.msg = self.on_message(self)

                 if not ok : return ok


                 # invoke default_on_post

                 if not self.on_post :
                        self.logger.debug( "default_on_post called")
                        ok, self.msg = self.default_on_post()

                 # invoke on_post when provided
                 else :
                        self.logger.debug("on_post called")
                        ok, self.msg = self.on_post(self)

                 return ok

        except :
                 (type, value, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s,  ..." % (type, value))
                 return False

        return ok


    def run(self):

        # configure

        self.configure()

        # instance set up

        i = self.instance - 1

        self.subscriber = self.subscribe_users[i]

        self.bindings.append(self.exchanges[i])

        self.queue_name = 'q_' + self.broker.username + '.' + self.program_name + '.' + self.subscriber

        # present basic config

        self.logger.info("sr_2xlog run")
        self.logger.info("AMQP  broker(%s) user(%s) vhost(%s)" % \
                        (self.broker.hostname,self.broker.username,self.broker.path) )

        for tup in self.bindings:
            e,k =  tup
            self.logger.info("AMQP  input :    exchange(%s) topic(%s)" % (e,k) )

        self.logger.info("\nsubscriber = %s" % self.subscriber)


        # loop/process messages

        self.connect()

        while True :
              ok = self.process_message()


    def reload(self):
        self.logger.info("%s reload" % self.program_name)
        self.close()
        self.run()

    def start(self):
        self.logger.info("%s start" % self.program_name)
        self.run()

    def stop(self):
        self.logger.info("%s stop" % self.program_name)
        self.close()
        os._exit(0)
                 

# ===================================
# self test
# ===================================

class test_logger:
      def silence(self,str):
          pass
      def __init__(self):
          self.debug   = print
          self.error   = print
          self.info    = print
          self.warning = print

def test_sr_2xlog():

    logger = test_logger()

    opt1   = 'on_message ./on_msg_test.py'
    opt2   = 'on_post ./on_pst_test.py'

    # here an example that calls the default_on_message...
    # then process it if needed
    f      = open("./on_msg_test.py","w")
    f.write("class Transformer(object): \n")
    f.write("      def perform(self, parent ):\n")
    f.write("          ok,msg = parent.default_on_message()\n")
    f.write("          if not ok :  return ok,msg\n")
    f.write("          msg.mtypej = 'transformed'\n")
    f.write("          return True, msg\n")
    f.write("transformer = Transformer()\n")
    f.write("self.on_message = transformer.perform\n")
    f.close()

    f      = open("./on_pst_test.py","w")
    f.write("class Transformer(object): \n")
    f.write("      def perform(self, parent ):\n")
    f.write("          ok,msg = parent.default_on_post()\n")
    f.write("          if not ok :  return ok,msg\n")
    f.write("          msg.mtypek = 'transformed'\n")
    f.write("          return True, msg\n")
    f.write("transformer = Transformer()\n")
    f.write("self.on_post = transformer.perform\n")
    f.close()

    # setup sr_2xlog for 2 users

    N = 10

    toxlog         = sr_2xlog()
    toxlog.logger  = logger
    toxlog.debug   = False

    toxlog.user_queue_dir = os.getcwd()
    toxlog.option( opt1.split()  )
    toxlog.option( opt2.split()  )

    # ==================
    # define YOUR BROKER HERE

    ok, details = toxlog.credentials.get("amqp://ddi1.cmc.ec.gc.ca/")
    if not ok :
       print("UNABLE TO PERFORM TEST")
       print("Need a good broker")
       sys.exit(1)
    toxlog.broker = details.url

    # ==================
    # define a source_users list here

    toxlog.source_users = ['anonymous']

    # ==================
    # define the matching cluster here
    toxlog.cluster = 'DDI.CMC'

    toxlog.connect()

    # process N messages

    i = 0
    j = 0
    k = 0
    while True :
          if toxlog.process_message():
             if toxlog.msg.mtypej == 'transformed': j += 1
             if toxlog.msg.mtypek == 'transformed': k += 1
             i = i + 1
          if i == N: break

    toxlog.close()

    if j != N or k != N :
       print("sr_toxlog TEST Failed 1")
       sys.exit(1)

    print("sr_toxlog TEST PASSED")

    os.unlink('./on_msg_test.py')
    os.unlink('./on_pst_test.py')

    sys.exit(0)

# ===================================
# MAIN
# ===================================

def main():

    action = None
    args   = None
    config = None


    if len(sys.argv) > 1 :
       action = sys.argv[-1]
       args   = sys.argv[:-1]

    if len(sys.argv) > 2 : 
       config    = sys.argv[-2]
       cfg       = sr_config()
       cfg.general()
       ok,config = cfg.config_path('toxlog',config)
       if ok     : args = sys.argv[:-2]
       if not ok :
          config = None
          end = -2


    toxlog = sr_2xlog(config,args[1:])

    if   action == 'reload' : toxlog.reload_parent()
    elif action == 'restart': toxlog.restart_parent()
    elif action == 'start'  : toxlog.start_parent()
    elif action == 'stop'   : toxlog.stop_parent()
    elif action == 'status' : toxlog.status_parent()
    elif action == 'TEST'   : test_sr_toxlog()
    else :
           toxlog.logger.error("action unknown %s" % action)
           sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
