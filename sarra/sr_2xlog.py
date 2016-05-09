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
#                       validates them and put the valid one in xlog
#                       to permit pump  log routing
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Dec 17 09:23:05 EST 2015
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
#                         = one sr_2xlog instance per exchange
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

    def check(self):
        self.logger.debug("sr_2xlog check")

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

    def connect(self):

        # =============
        # create message
        # =============

        self.msg = sr_message(self)

        # =============
        # consumer  queue_name : let consumer takes care of it
        # =============

        self.consumer = sr_consumer(self)

        # =============
        # publisher... (publish back to consumer)  
        # =============

        self.publisher = self.consumer.publish_back()

        # =============
        # setup message publisher
        # =============

        self.msg.publisher = self.consumer.publisher


    def help(self):
        self.logger.info("Usage: %s [options] [config] [start|stop|restart|reload|status]  \n" % self.program_name )


    # =============
    # __on_message__ internal process of message
    # =============

    def __on_message__(self):
        self.logger.debug("sr_2xlog __on_message__")

        # is the log message for this cluster

        if not 'from_cluster' in self.msg.headers or not 'source' in self.msg.headers :
           self.logger.debug("skipped : no cluster or source in message")
           return False

        # is the log message from a source on this cluster

        if not hasattr(self.msg,'log_user')  or self.msg.log_user != self.subscriber:
           self.logger.debug("skipped : log_user is not subscriber %s " % self.subscriber)
           return False

        # yup this is one valid message from that suscriber
     
        # invoke on_message when provided

        ok = True

        if self.on_message : ok = self.on_message(self)

        return ok

    # =============
    # __on_post__ internal posting of message
    # =============

    def __on_post__(self):

        # invoke on_post when provided

        if self.on_post :
           ok = self.on_post(self)
           if not ok: return ok

        # should always be ok

        ok = self.msg.publish( )

        return ok

    def overwrite_defaults(self):
        self.logger.debug("sr_2xlog overwrite_defaults")

        # overwrite defaults

        if hasattr(self,'manager'):
           self.broker            = self.manager
        self.topic_prefix         = 'v02.log'
        self.subtopic             = '#'

    # =============
    # process message  
    # =============

    def process_message(self):

        try  :
                 ok, self.msg = self.consumer.consume()
                 if not ok : return ok

                 self.logger.debug("Received topic   %s" % self.msg.topic)
                 self.logger.debug("Received notice  %s" % self.msg.notice)
                 self.logger.debug("Received headers %s" % self.msg.hdrstr)

                 # invoke __on_message__

                 ok = self.__on_message__()
                 if not ok : return ok

                 # ok accepted... ship subscriber log to xlog

                 self.msg.exchange = 'xlog'

                 # invoke __on_post__

                 ok = self.__on_post__()
                 if not ok : return ok

                 return ok

        except :
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
                 return False

        return ok


    def run(self):

        # set instance

        self.set_instance()

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


    def set_instance(self):
        i = self.instance - 1

        self.subscriber = self.subscribe_users[i]

        self.bindings.append(self.exchanges[i])

        self.queue_name = 'q_' + self.broker.username + '.' + self.program_name + '.' + self.subscriber


    def reload(self):
        self.logger.info("%s reload" % self.program_name)
        self.close()
        self.configure()
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
          self.debug   = self.silence
          self.error   = print
          self.info    = self.silence
          self.warning = print

def test_sr_2xlog():

    logger = test_logger()

    opt1   = 'on_message ./on_msg_test.py'
    opt2   = 'on_post ./on_pst_test.py'

    # here an example that calls the default_on_message...
    # then process it if needed
    f      = open("./on_msg_test.py","w")
    f.write("class Transformer(object): \n")
    f.write("      def __init__(self):\n")
    f.write("          self.count_ok = 0\n")
    f.write("      def perform(self, parent ):\n")
    f.write("          self.count_ok += 1\n")
    f.write("          parent.msg.mtypej = self.count_ok\n")
    f.write("          return True\n")
    f.write("transformer = Transformer()\n")
    f.write("self.on_message = transformer.perform\n")
    f.close()

    f      = open("./on_pst_test.py","w")
    f.write("class Transformer(object): \n")
    f.write("      def __init__(self): \n")
    f.write("          self.count_ok = 0\n")
    f.write("      def perform(self, parent ):\n")
    f.write("          self.count_ok += 1\n")
    f.write("          parent.msg.mtypek = self.count_ok\n")
    f.write("          return True\n")
    f.write("transformer = Transformer()\n")
    f.write("self.on_post = transformer.perform\n")
    f.close()

    # setup sr_2xlog for 1 user (just this instance)

    toxlog         = sr_2xlog()
    toxlog.logger  = logger
    toxlog.debug   = True

    subscriber = 'tsource'
    exchange   = 'xs_' + subscriber
    toxlog.subscribe_users = [subscriber]
    toxlog.exchanges       = {}
    toxlog.exchanges[0]    = ( exchange, 'v02.log.#' )
    toxlog.user_queue_dir  = os.getcwd()
    toxlog.nbr_instances   = 1

    toxlog.option( opt1.split()  )
    toxlog.option( opt2.split()  )

    # ==================
    # define YOUR BROKER HERE

    ok, details = toxlog.credentials.get("amqp://localhost/")
    if not ok :
       print("UNABLE TO PERFORM TEST")
       print("Need a good broker")
       sys.exit(1)
    toxlog.broker = details.url

    # ==================
    # define the matching cluster here
    toxlog.cluster = 'DDI.CMC'

    # ==================
    # set instance

    toxlog.instance = 1
    toxlog.set_instance()
    toxlog.connect()
    
    # do an empty consume... assure AMQP's readyness
    ok, msg = toxlog.consumer.consume()

    # use toxlog.publisher to post a log to xs_anonymous

    toxlog.msg.exchange = exchange
    toxlog.msg.topic    = 'v02.log.this.is.test1'
    toxlog.msg.url      = urllib.parse.urlparse("http://me@mytest.con/this/is/test1")
    toxlog.msg.headers  = {}

    toxlog.msg.headers['parts']        = '1,1591,1,0,0'
    toxlog.msg.headers['sum']          = 'd,a66d85b0b87580fb4d225640e65a37b8'
    toxlog.msg.headers['from_cluster'] = 'DDI.CMC'
    toxlog.msg.headers['source']       = 'a_provider'
    toxlog.msg.headers['to_clusters']  = 'dont_care_forward_direction'
    toxlog.msg.headers['message']      = 'Downloaded'
    toxlog.msg.headers['filename']     = 'toto'

    # start with a bad one
    BAD                 = 'A_STRANGER'
    toxlog.msg.notice   = '20151217093654.123 http://me@mytest.con/ this/is/test1 '
    toxlog.msg.notice  += '201 foreign.host.com '+ BAD + ' 823.353824'
    toxlog.msg.parse_v02_post()

    toxlog.msg.publish()

    # than post the good one

    toxlog.msg.notice   = '20151217093654.123 http://me@mytest.con/ this/is/test1 '
    toxlog.msg.notice  += '201 foreign.host.com '+ subscriber + ' 823.353824'
    toxlog.msg.parse_v02_post()

    toxlog.msg.publish()

    # process with our on_message and on_post
    # expected only 1 hit for a good message
    # to go to xlog

    i = 0
    j = 0
    k = 0
    c = 0
    while True :
          ok = toxlog.process_message()
          c = c + 1
          if c == 10 : break
          if not ok : continue
          if toxlog.msg.headers['source'] != 'a_provider': continue
          if toxlog.msg.mtypej == 1: j += 1
          if toxlog.msg.mtypek == 1: k += 1
          i = i + 1

    toxlog.close()

    if j != 1 or k != 1 :
       print("sr_2xlog TEST Failed 1")
       sys.exit(1)

    print("sr_2xlog TEST PASSED")

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
       args   = sys.argv[1:-1]

    if len(sys.argv) >= 3 : 
       config    = sys.argv[-2]
       cfg       = sr_config()
       cfg.defaults()
       cfg.general()
       ok,config = cfg.config_path('2xlog',config,mandatory=False)
       if ok     : args = sys.argv[1:-2]
       if not ok : config = None

    toxlog = sr_2xlog(config,args)

    if action != 'TEST' and  not toxlog.log_daemons :
       toxlog.logger.info("sr_2xlog will not run (log_daemons), action '%s' ignored " % action)
       sys.exit(0)

    if   action == 'reload' : toxlog.reload_parent()
    elif action == 'restart': toxlog.restart_parent()
    elif action == 'start'  : toxlog.start_parent()
    elif action == 'stop'   : toxlog.stop_parent()
    elif action == 'status' : toxlog.status_parent()
    elif action == 'TEST'   : test_sr_2xlog()
    else :
           toxlog.logger.error("action unknown %s" % action)
           sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
