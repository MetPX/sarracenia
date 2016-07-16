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
# sr_report2source.py : python3 program takes all log messages and repost them to the
#                    log exchange of the source user
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Dec 17 09:20:42 EST 2015
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
# sr_report2source [options] [config] [start|stop|restart|reload|status]
#
# logs message have travel back to this cluster
#
# conditions :
# exchange                = xreport
# topic                   = v02.report
# header['from_cluster']  = cluster        (here)
# header['source]         in source_users  (one of our source : users.conf)
#
# it is a log message that our source sould be able to see so:
#
# publish this log message in xr_"source"
#
#============================================================

try :    
         from sr_consumer       import *
         from sr_instances      import *
         from sr_message        import *
except : 
         from sarra.sr_consumer  import *
         from sarra.sr_instances import *
         from sarra.sr_message   import *

class sr_report2source(sr_instances):

    def __init__(self,config=None,args=None):
        sr_instances.__init__(self,config,args)

    def check(self):

        # create bindings from default ?

        if self.bindings == [] :
           key = self.topic_prefix + '.' + self.subtopic
           self.bindings.append( (self.exchange,key) )

        # scan users for role source

        self.source_users = []

        for user in self.users :
            roles = self.users[user]
            if 'source' in roles :
               self.source_users.append(user)

        self.logger.debug("source_users = %s " % self.source_users)

        if len(self.source_users) == 0 :
           self.nbr_instances = 0

    def close(self):
        self.consumer.close()

    def connect(self):

        # =============
        # create message if needed
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
        self.msg.post_exchange_split = self.post_exchange_split

    def help(self):
        self.logger.info("Usage: %s [options] [config] [start|stop|restart|reload|status]  \n" % self.program_name )


    # =============
    # __on_message__  internal message validation
    # =============

    def __on_message__(self):
        self.logger.debug("sr_report2source __on_message__")

        # is the log message for this cluster

        if not 'from_cluster' in self.msg.headers or self.msg.headers['from_cluster'] != self.cluster :
           self.logger.debug("skipped : not for cluster %s" % self.cluster)
           self.logger.debug("hdr from_cluster %s" % self.msg.headers['from_cluster'])
           return False

        # is the log message from a source on this cluster

        if not 'source' in self.msg.headers or not self.msg.headers['source'] in self.source_users:
           self.logger.debug("skipped : source not in %s" % self.source_users)
           return False

        # yup this is one message we want to ship to our source

        # user provided an on_message script

        ok = True

        if self.on_message : ok = self.on_message(self)

        return ok

    # =============
    # __on_post__ internal posting
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

        # overwrite defaults

        self.broker               = self.manager
        self.exchange             = 'xreport'
        self.topic_prefix         = 'v02.report'
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

                 # ok ship it back to the user exchange 

                 self.msg.exchange = 'xr_' + self.msg.headers['source']

                 # invoke __on_post__

                 ok = self.__on_post__()

                 return ok

        except :
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
                 return False

        return ok


    def run(self):

        # present basic config

        self.logger.info("sr_report2source run")
        self.logger.info("AMQP  broker(%s) user(%s) vhost(%s)" % \
                        (self.broker.hostname,self.broker.username,self.broker.path) )

        for tup in self.bindings:
            e,k =  tup
            self.logger.info("AMQP  input :    exchange(%s) topic(%s)" % (e,k) )

        self.logger.info("\nsource users = %s" % self.source_users)


        # connect and loop/process messages

        self.connect()

        while True :
              ok = self.process_message()


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
          self.debug   = print
          self.error   = print
          self.info    = print
          self.warning = print

def test_sr_report2source():

    logger = test_logger()

    yyyy   = time.strftime("%Y",time.gmtime())
    opt1   = 'accept .*' + yyyy + '.*'
    opt2   = 'reject .*'
    opt3   = 'on_message ./on_msg_test.py'
    opt4   = 'on_post ./on_pst_test.py'

    # here an example that calls the default_on_message...
    # then process it if needed
    f      = open("./on_msg_test.py","w")
    f.write("class Transformer(object): \n")
    f.write("      def perform(self, parent ):\n")
    f.write("          parent.msg.mtypej = 'transformed'\n")
    f.write("          return True\n")
    f.write("transformer = Transformer()\n")
    f.write("self.on_message = transformer.perform\n")
    f.close()

    f      = open("./on_pst_test.py","w")
    f.write("class Transformer(object): \n")
    f.write("      def perform(self, parent ):\n")
    f.write("          parent.msg.mtypek = 'transformed'\n")
    f.write("          return True\n")
    f.write("transformer = Transformer()\n")
    f.write("self.on_post = transformer.perform\n")
    f.close()

    # setup sr_report2source to catch repost N log messages

    N = 10

    report2source         = sr_report2source()
    report2source.logger  = logger
    report2source.debug   = True

    report2source.user_cache_dir = os.getcwd()

    # because following options have accept/reject
    report2source.masks   = []
    report2source.option( opt1.split()  )
    report2source.option( opt2.split()  )

    report2source.option( opt3.split()  )
    report2source.option( opt4.split()  )

    # ==================
    # define YOUR BROKER HERE

    ok, details = report2source.credentials.get("amqp://tfeed@localhost/")
    if not ok :
       print("UNABLE TO PERFORM TEST")
       print("Need feeder privileges to a broker")
       sys.exit(1)
    report2source.broker = details.url

    # ==================
    # define a source_users list here

    report2source.source_users = ['tsource']

    # ==================
    # define the matching cluster here
    report2source.cluster = 'DDI.CMC'

    report2source.connect()

    # process N messages

    i = 0
    j = 0
    k = 0
    while True :
          if report2source.process_message():
             if report2source.msg.mtypej == 'transformed': j += 1
             if report2source.msg.mtypek == 'transformed': k += 1
             i = i + 1
          if i == N: break

    os.unlink(report2source.consumer.queuepath)

    report2source.close()

    if j != N or k != N :
       print("sr_report2source TEST Failed 1")
       sys.exit(1)

    print("sr_report2source TEST PASSED")

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

    if len(sys.argv) > 2 : 
       config    = sys.argv[-2]
       cfg       = sr_config()
       cfg.defaults()
       cfg.general()
       ok,config = cfg.config_path('report2source',config,mandatory=False)
       if ok     : args = sys.argv[1:-2]
       if not ok : config = None

    report2source = sr_report2source(config,args)

    if action != 'TEST' and  not report2source.log_daemons :
       report2source.logger.info("sr_report2source will not run (log_daemons), action '%s' ignored " % action)
       sys.exit(0)

    if   action == 'reload' : report2source.reload_parent()
    elif action == 'restart': report2source.restart_parent()
    elif action == 'start'  : report2source.start_parent()
    elif action == 'stop'   : report2source.stop_parent()
    elif action == 'status' : report2source.status_parent()
    elif action == 'TEST'   : test_sr_report2source()
    else :
           report2source.logger.error("action unknown %s" % action)
           sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
