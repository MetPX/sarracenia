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
# sr_report2clusters.py : python3 this program assumes log routing
#                      between clusters
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
# sr_report2clusters [options] [config] [start|stop|restart|reload|status]
#
# On the current cluster... subscribers return their log about
# product downloads. It is possible that this cluster "pumped" that product
# from another cluster. It is this originating cluster that needs this log
# This program publishes the message back to their originating cluster
#
# conditions :
#
# Each line in report2clusters.conf (self.report_clusters) contains :
# cluster_name  cluster_broker  cluster_exchange
# One instance of sr_report2clusters is fork for each of them
#
# The instance consumes log messages on self.broker 
# exchange = xreport     
# topic    = v02.report  
# subtopic = #        
#
# It validates the message : it must have the header['source']
# and header['from_cluster'] for proper log routing.
#
# If valid and header['from_cluster'] match cluster_name
# the log message is published in cluster_exchange on the cluster_broker
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

class sr_report2clusters(sr_instances):

    def __init__(self,config=None,args=None):
        sr_instances.__init__(self,config,args)

    def check(self):

        # create bindings from default ?

        if self.bindings == [] :
           key = self.topic_prefix + '.' + self.subtopic
           self.bindings.append( (self.exchange,key) )

        # no queue name allowed

        if self.queue_name != None:
           self.logger.error("queue name forced in this program")
           self.queue_name =  None

        # as many instances than cluster to route log to

        self.logger.debug("report_clusters = %s" % self.report_clusters)

        self.nbr_instances = len(self.report_clusters)

    def close(self):
        self.consumer.close()
        self.hc.close()

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
        # publisher... on remote cluster
        # =============

        self.hc = HostConnect( logger = self.logger )
        self.hc.set_url( self.cluster_broker )
        self.hc.connect()

        self.publisher = Publisher(self.hc)
        self.publisher.build()

        # =============
        # setup message publisher
        # =============

        self.msg.publisher = self.publisher
        self.msg.post_exchange_split = self.post_exchange_split

    def help(self):
        self.logger.info("Usage: %s [options] [config] [start|stop|restart|reload|status]  \n" % self.program_name )


    # =============
    # __on_message__  how message are processed internaly
    # =============

    def __on_message__(self):
        self.logger.debug("sr_report2clusters __on_message__")

        # check for from_cluster and it the cluster match  cluster_name

        if not 'from_cluster' in self.msg.headers or self.msg.headers['from_cluster'] != self.cluster_name :
           self.logger.debug("skipped : not for cluster %s" % self.cluster_name)
           return False

        # avoid bad message (no source) and looping no repost on this cluster

        if not 'source' in self.msg.headers or self.msg.headers['from_cluster'] == self.cluster :
           self.logger.debug("skipped : invalid message or looping avoided")
           return False

        # yup this is one valid message from that post broker

        # invoke user provided on_message 

        ok = True

        if self.on_message : ok = self.on_message(self)

        return ok

    # =============
    # __on_post__ how messages are posted internally
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

                 # ok accepted... ship subscriber log to xreport

                 self.msg.exchange = self.cluster_exchange

                 # invoke __on_post__

                 ok = self.__on_post__()

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

        self.logger.info("sr_report2clusters run")
        self.logger.info("AMQP  broker(%s) user(%s) vhost(%s)" % \
                        (self.broker.hostname,self.broker.username,self.broker.path) )
        tup = self.bindings[0]
        e,k =  tup
        self.logger.info("AMQP  input :    exchange(%s) topic(%s)" % (e,k) )

        self.logger.info("\nCLUSTER")
        self.logger.info("AMQP  broker(%s) user(%s) vhost(%s)" % \
                        (self.cluster_broker.hostname,self.cluster_broker.username,self.cluster_broker.path) )
        self.logger.info("AMQP  output:    exchange(%s) topic(%s)" % (self.cluster_exchange,k) )

        # loop/process messages

        self.connect()

        while True :
              ok = self.process_message()


    def set_instance(self):

        i = self.instance - 1

        self.cluster_name, self.cluster_broker, self.cluster_exchange = self.report_clusters[i]

        self.queue_name  = 'q_' + self.broker.username + '.'
        self.queue_name += self.program_name + '.' + self.cluster_name + '.' + self.cluster_exchange

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

def test_sr_report2clusters():

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

    # setup sr_report2clusters for 1 user (just this instance)

    report2clusters         = sr_report2clusters()
    report2clusters.debug   = True
    report2clusters.logger  = logger
    report2clusters.bindings = [ ('xreport','v02.report.this.#') ]
    report2clusters.nbr_instances   = 1

    report2clusters.option( opt1.split()  )
    report2clusters.option( opt2.split()  )

    # ==================
    # define YOUR BROKER HERE

    ok, details = report2clusters.credentials.get("amqp://tsource@localhost/")
    if not ok :
       print("UNABLE TO PERFORM TEST")
       print("Need admin or feeder access on local broker to read from.")
       sys.exit(1)
    report2clusters.broker  = details.url
    report2clusters.cluster = 'DDI.EDM'

    # ==================
    # define REMOTE BROKER HERE

    report2clusters.cluster_name = 'DDI.CMC'
    ok, details = report2clusters.credentials.get("amqp://ddi1.cmc.ec.gc.ca/")
    if not ok :
       print("UNABLE TO PERFORM TEST")
       print("Need admin or feeder access to a remote broker to write to")
       sys.exit(1)
    report2clusters.cluster_exchange = 'xreport'

    # ==================
    # set instance

    report2clusters.instance = 1
    report2clusters.set_instance()
    report2clusters.connect()

    publisher = report2clusters.consumer.publish_back()
    
    # prepare a funky message good message

    report2clusters.msg.exchange = 'xreport'
    report2clusters.msg.topic    = 'v02.report.this.is.test1'
    report2clusters.msg.url      = urllib.parse.urlparse("http://me@mytest.con/this/is/test1")
    report2clusters.msg.headers  = {}

    report2clusters.msg.headers['parts']        = '1,1591,1,0,0'
    report2clusters.msg.headers['sum']          = 'd,a66d85b0b87580fb4d225640e65a37b8'
    report2clusters.msg.headers['source']       = 'a_provider'
    report2clusters.msg.headers['to_clusters']  = 'dont_care_forward_direction'
    report2clusters.msg.headers['message']      = 'Downloaded'
    report2clusters.msg.headers['filename']     = 'toto'
    report2clusters.msg.notice   = '20151217093654.123 http://me@mytest.con/ this/is/test1 '
    report2clusters.msg.notice  += '201 foreign.host.com a_remote_source 823.353824'

    # publish a bad one
    msg = report2clusters.msg
    msg.headers['from_cluster'] = 'BAD'
    msg.parse_v02_post()
    publisher.publish(msg.exchange,msg.topic,msg.notice,msg.headers)

    # publish a good one
    msg = report2clusters.msg
    msg.headers['from_cluster'] = 'DDI.CMC'
    msg.parse_v02_post()
    publisher.publish(msg.exchange,msg.topic,msg.notice,msg.headers)

    # process with our single message that should be posted to our remote cluster

    j = 0
    k = 0
    while True :
          ok = report2clusters.process_message()
          if not ok : continue
          if report2clusters.msg.mtypej == 1: j += 1
          if report2clusters.msg.mtypek == 1: k += 1
          break

    report2clusters.close()

    if j != 1 or k != 1 :
       print("sr_report2clusters TEST Failed 1")
       sys.exit(1)

    print("sr_report2clusters TEST PASSED")

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
       ok,config = cfg.config_path('report2clusters',config,mandatory=False)
       if ok     : args = sys.argv[1:-2]
       if not ok : config = None

    report2clusters = sr_report2clusters(config,args)

    if action != 'TEST' and  not report2clusters.report_daemons :
       report2clusters.logger.info("sr_report2clusters will not run (report_daemons), action '%s' ignored " % action)
       sys.exit(0)

    if   action == 'reload' : report2clusters.reload_parent()
    elif action == 'restart': report2clusters.restart_parent()
    elif action == 'start'  : report2clusters.start_parent()
    elif action == 'stop'   : report2clusters.stop_parent()
    elif action == 'status' : report2clusters.status_parent()
    elif action == 'TEST'   : test_sr_report2clusters()
    else :
           report2clusters.logger.error("action unknown %s" % action)
           sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()

