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
# sr_winnow.py : python3 program allowing to winnow duplicated messages
#                and post the uniqie and first message in.
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Murray Rennie  - Shared Services Canada
#  Last Changed   : Dec  8 15:22:58 GMT 2015
#  Last Revision  : Dec  8 15:22:58 GMT 2015
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

import os,sys,time, netifaces

try :    
         from sr_amqp           import *
         from sr_instances      import *
         from sr_message        import *
except : 
         from sarra.sr_amqp      import *
         from sarra.sr_instances import *
         from sarra.sr_message   import *

class sr_winnow(sr_instances):

    def __init__(self,config=None,args=None):
        sr_instances.__init__(self,config,args)
        self.defaults()
        self.accept_if_unmatch = True
        self.configure()

    def check(self):

        # When doing winnowing :
        # we cannot share the queue with another process
        # we cannot have more than one instance since we 
        # need to work with a single cache.

        if self.nbr_instances != 1 :
           self.logger.warning("Only one instance allowed... set to 1")
           self.nbr_instances = 1

        # dont want to recreate these if they exists

        if not hasattr(self,'msg') :
           self.msg      = sr_message(self.logger)

        self.msg.user = self.broker.username

        # make a single list for clusters that we accept message for

        self.accept_msg_for_clusters      = [ self.cluster ]
        self.accept_msg_for_clusters.extend ( self.cluster_aliases )
        self.accept_msg_for_clusters.extend ( self.gateway_for  )

        # =========================================
        # =========================================
        # === FIXME : Murray, initialize cache here
        # =========================================
        # =========================================


    def close(self):
        self.hc.close()

    def connect(self):

        # =============
        # consumer
        # =============

        # consumer host

        self.hc = HostConnect( logger = self.logger )
        self.hc.set_url( self.broker )
        self.hc.connect()

        # consumer  no queue sharing no instances

        self.consumer  = Consumer(self.hc)
        self.consumer.build()

        # consumer queue
        name  = 'q_' + self.broker.username + '.' + self.program_name + '.' + self.config_name
        if self.queue_name != None :
           name = 'q_' + self.broker.username + '.' + self.queue_name

        self.queue = Queue(self.hc,name)
        self.queue.add_binding(self.source_exchange,self.source_topic)
        self.queue.build()

        # log publisher

        self.amqp_log    = Publisher(self.hc)
        self.amqp_log.build()

        # =============
        # publisher on same broker
        # =============

        self.amqp_pub    = Publisher(self.hc)
        self.amqp_pub.build()

    def configure(self):

        # cumulative variable reinitialized

        self.exchange_key         = None     
        self.masks                = []       
        self.currentDir           = '.'      
        self.currentFileOption    = 'WHATFN' 

        # installation general configurations and settings

        self.general()

        # arguments from command line

        self.args(self.user_args)

        # config from file

        self.config(self.user_config)

        # verify all settings

        self.check()

        self.setlog()
        self.logger.info("user_config = %s" % self.user_config)

    def help(self):
        self.logger.info("Usage: %s [OPTIONS] configfile [start|stop|restart|reload|status]\n" % self.program_name )
        self.logger.info("OPTIONS:")
        self.logger.info("-b   <broker>                default amqp://guest:guest@localhost/")
        self.logger.info("-se  <source_exchange>       default None")
        self.logger.info("-st  <source_topic>          default v02.post.#")
        self.logger.info("-ex  <exchange>              default xpublic")
        self.logger.info("DEBUG:")
        self.logger.info("-debug")

    # this instance of sr_winnow runs,
    # for cluster               : self.cluster
    # alias for the cluster are : self.cluster_aliases
    # it is a gateway for       : self.gateway_for 
    # all these cluster names were put in list self.accept_msg_for_clusters
    # The message's target clusters  self.msg.to_clusters should be in
    # the self.accept_msg_for_clusters list

    def route_this_message(self):

        # the message has not specified a destination.
        if not 'to_clusters' in self.msg.headers :
           self.msg.code    = 403
           self.msg.message = "Forbidden : message without destination amqp header['to_clusters']"
           self.msg.log_error()
           return False

        # loop on all message destinations (target)
        for target in self.msg.to_clusters :
           if target in self.accept_msg_for_clusters : return True

        # nope this one is not for this cluster
        self.logger.warning("skipped : not for this cluster...")

        return False

    def run(self):

        self.logger.info("sr_winnow run")

        self.connect()

        self.msg.logger       = self.logger
        self.msg.amqp_log     = self.amqp_log
        self.msg.amqp_pub     = self.amqp_pub
        self.msg.exchange_pub = self.exchange

        #
        # loop on all message
        #

        raw_msg = None

        while True :

          try  :
                 # ========================================
                 # ========================================
                 # === FIXME : Murray, put ip presence test
                 # === HERE
                 # use    self.vip     self.interface
                 # ========================================
                 # ========================================


                 # instead of acking in every test ... ack at beginning of iteration
  
                 if raw_msg != None : self.consumer.ack(raw_msg)

                 raw_msg = self.consumer.consume(self.queue.qname)
                 if raw_msg == None : continue

                 # make use it as a sr_message

                 self.msg.from_amqplib(raw_msg)
                 self.logger.info("Received %s '%s' %s" % (self.msg.topic,self.msg.notice,self.msg.hdrstr))
                 # ========================================
                 # ========================================
                 # === FIXME : Murray, test if already in cache
                 # === HERE
                 # === if already in cache:
                 # ===    log ignore message in cache
                 # ===    continue
                 # ========================================
                 # === checksum is   self.msg.checksum
                 # ========================================

                 # make use of accept/reject

                 if not self.isMatchingPattern(self.msg.urlstr) :
                    self.logger.info("Rejected by accept/reject options")
                    continue

                 # if message for this cluster or for this cluster's route

                 ok = self.route_this_message()
                 if not ok : continue

                 # setting source from exchange 

                 if self.source_from_exchange :
                    ok = self.set_source()
                    if not ok : continue

                 # setting originating cluster if not defined

                 if not 'from_cluster' in self.msg.headers :
                    ok = self.set_cluster()
                    if not ok : continue

                 # announcing the first and unique message

                 self.msg.exchange = self.exchange
                 self.msg.code     = 201
                 self.msg.message  = 'Published'
                 self.msg.publish()
              
          except :
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))

    def set_cluster(self):
        if self.cluster == None :
           self.msg.code    = 403
           self.msg.message = "Forbidden : message without cluster"
           self.msg.log_error()
           return False

        self.msg.set_from_cluster(self.cluster)
        return True

    def set_source(self):
        if self.msg.exchange[:3] != 'xs_' :
           self.msg.code    = 403
           self.msg.message = "Forbidden : message without source"
           self.msg.log_error()
           return False

        source = self.msg.exchange[3:]
        self.msg.set_source(source)
        return True

    def reload(self):
        self.logger.info("sr_winnow reload")
        self.close()
        self.configure()
        self.run()

    def start(self):
        self.configure()
        self.logger.info("sr_winnow start")
        self.run()

    def stop(self):
        self.logger.info("sr_winnow stop")
        self.close()
        os._exit(0)


# ===================================
# MAIN
# ===================================

def main():

    action = None
    args   = None
    config = None

    if len(sys.argv) >= 3 :
       action = sys.argv[-1]
       config = sys.argv[-2]
       if len(sys.argv) > 3: args = sys.argv[1:-2]

    winnow = sr_winnow(config,args)

    if   action == 'reload' : winnow.reload_parent()
    elif action == 'restart': winnow.restart_parent()
    elif action == 'start'  : winnow.start_parent()
    elif action == 'stop'   : winnow.stop_parent()
    elif action == 'status' : winnow.status_parent()
    else :
           winnow.logger.error("action unknown %s" % action)
           sys.exit(1)

    sys.exit(0)



# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
