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
# sr_shovel.py : python3 program allows to shovel message from one source broker
#                to another destination broker (called post_broker)
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Feb  8 16:14:12 EST 2016
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
#============================================================
# usage example
#
# sr_shovel [options] [config] [start|stop|restart|reload|status]
#
# sr_shovel consumes message, for each selected message it reannounces it.
# One usage of shovel is to acquire log from source brokers.
# Another could be to avoid servers to announce to x broker, but instead
# to have its own broker and all remote brokers interested to its announcement
# coud shovel them down to themselves.
#
# broker                  = the remote broker...
# exchange                = Mandatory
# topic_prefix            = Mandatory
# subtopic                = Mandatory
# accept/reject           = default accept everything from previous settings
#
# post_broker             = where sarra is running (manager)
# post_exchange           = default to the value of exchange
#
# report_exchange            = xreport (sent back to broker)
#
#============================================================
#

import os,sys,time,json

try :    
         from sr_amqp           import *
         from sr_consumer       import *
         from sr_instances      import *
         from sr_message        import *
except : 
         from sarra.sr_amqp      import *
         from sarra.sr_consumer  import *
         from sarra.sr_instances import *
         from sarra.sr_message   import *

class sr_shovel(sr_instances):

    def __init__(self,config=None,args=None):
        sr_instances.__init__(self,config,args)

    def check(self):

        if self.broker == None :
           self.logger.error("no broker given")
           self.help()
           sys.exit(1)

        if self.exchange == None :
           self.logger.error("no exchange given")
           self.help()
           sys.exit(1)

        if self.topic_prefix == None :
           self.logger.error("no topic_prefix given")
           self.help()
           sys.exit(1)

        # bindings should be defined 

        if self.bindings == []  :
           key = self.topic_prefix + '.#'
           self.bindings.append( (self.exchange,key) )
           self.logger.debug("*** BINDINGS %s"% self.bindings)

        # accept/reject
        self.use_pattern          = self.masks != []
        self.accept_unmatch       = self.masks == []

        # make a single list for clusters that we accept message for

        self.accept_msg_for_clusters      = [ self.cluster ]
        self.accept_msg_for_clusters.extend ( self.cluster_aliases )
        self.accept_msg_for_clusters.extend ( self.gateway_for  )
        self.logger.debug("accept_msg_for_clusters %s "% self.accept_msg_for_clusters)

        # default queue name if not given

        if self.queue_name == None :
           self.queue_name  = 'q_' + self.broker.username + '.'
           self.queue_name += self.program_name + '.' + self.config_name 

    def close(self):
        self.consumer.close()
        self.hc_pst.close()

    def connect(self):

        # =============
        # create message if needed
        # =============

        self.msg = sr_message(self)

        # =============
        # consumer
        # =============

        self.consumer          = sr_consumer(self)

        if self.save_file :
            self.consumer.save_path = self.save_file + self.save_path[-10:] 
            self.save_path = self.consumer.save_path
        else:
            self.consumer.save_path = self.save_path
            
        if self.save: self.consumer.save = True

        if self.reportback :
            self.msg.report_publisher = self.consumer.publish_back()
            self.msg.report_exchange  = self.report_exchange

            self.logger.info("report_back to %s@%s, exchange: %s" %
                  ( self.broker.username, self.broker.hostname, self.msg.report_exchange ) )
        else:
            self.logger.info( "report_back suppressed" )

        # =============
        # publisher
        # =============

        # publisher host

        self.hc_pst = HostConnect( logger = self.logger )
        self.hc_pst.set_url( self.post_broker )
        self.hc_pst.connect()

        if self.restore_queue is not None:
            # create temporary exchange to publish only to restore_queue.
            self.post_exchange = 'xs_' + self.broker.username + '.' + \
                self.program_name + '.' + self.config_name + '.restore'
            self.msg.pub_exchange = self.post_exchange
            self.hc_pst.channel.exchange_declare( self.post_exchange, \
                'topic', auto_delete=True, durable=False)
            self.hc_pst.channel.queue_bind( self.restore_queue, \
                self.post_exchange, '#' )

        # publisher

        self.publisher = Publisher(self.hc_pst)
        self.publisher.build()
        self.msg.publisher    = self.publisher

        self.msg.post_exchange_split = self.post_exchange_split


    def help(self):
        print("Usage: %s [OPTIONS] configfile [start|stop|restart|reload|status]\n" % self.program_name )
        print("version: %s \n" % sarra.__version__ )
        print("read messages from exchange, apply on_message if provided, reannounce/post them to post_broker & post_exchange\n")
        print("OPTIONS:")
        print("instances <nb_of_instances>      default 1")
        print("\nAMQP consumer broker settings:")
        print("\tbroker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>")
        print("\t\t(MANDATORY)")
        print("\nAMQP Queue bindings:")
        print("\texchange             <name>          (MANDATORY)")
        print("\ttopic_prefix         <amqp pattern>  (default: v02.post)")
        print("\tsubtopic             <amqp pattern>  (default: #)")
        print("\t\t  <amqp pattern> = <directory>.<directory>.<directory>...")
        print("\t\t\t* single directory wildcard (matches one directory)")
        print("\t\t\t# wildcard (matches rest)")
        print("\treport_exchange         <name>          (default: xreport)")
        print("\nAMQP Queue settings:")
        print("\tdurable              <boolean>       (default: False)")
        print("\texpire               <minutes>       (default: None)")
        print("\tmessage-ttl          <minutes>       (default: None)")
        print("\nMessage settings:")
        print("\taccept    <regexp pattern>           (default: None)")
        print("\treject    <regexp pattern>           (default: None)")
        print("\ton_message           <script>        (default None)")
        print("\nAMQP posting broker settings:")
        print("\tpost_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>")
        print("\t\t(default: manager amqp broker in default.conf)")
        print("\tpost_exchange        <name>          (default xpublic)")
        print("\ton_post              <script>        (default None)")
        print("DEBUG:")
        print("-debug")

    # =============
    # __on_message__
    # =============

    def __on_message__(self):

        # the message has not specified a source.
        if not 'source' in self.msg.headers :
           if self.reportback:
               self.msg.report_publish(403,"Forbidden : message without a source amqp header['source']")
           self.logger.error("message without a source amqp header['source']")
           return False

        # the message has not specified a from_cluster.
        if not 'from_cluster' in self.msg.headers :
           if self.reportback:
               self.msg.report_publish(403,"Forbidden : message without a cluster amqp header['from_cluster']")
           self.logger.error("message without a cluster amqp header['from_cluster']")
           return False

        # the message has not specified a destination.
        if not 'to_clusters' in self.msg.headers :
           if self.reportback:
               self.msg.report_publish(403,"Forbidden : message without destination amqp header['to_clusters']")
           self.logger.error("message without destination amqp header['to_clusters']")
           return False

        # this instances of sr_shovel runs,
        # for cluster               : self.cluster
        # alias for the cluster are : self.cluster_aliases
        # it is a gateway for       : self.gateway_for 
        # all these cluster names were put in list self.accept_msg_for_clusters
        # The message's target clusters  self.msg.to_clusters should be in
        # the self.accept_msg_for_clusters list

        # if this cluster is a valid destination than one of the "to_clusters" pump
        # will be present in self.accept_msg_for_clusters

        # PSilva: I don't think the gatway logic is ever useful for shovel.
        # so commented out.
        #ok = False
        #for target in self.msg.to_clusters :
        #   if  not target in self.accept_msg_for_clusters :  continue
        #   ok = True
        #   break

        #if not ok :
        #   self.logger.warning("skipped : not for this cluster...")
        #   return False

        # invoke user defined on_message when provided

        for plugin in self.on_message_list:
           if not plugin(self): return False

        return True

    # =============
    # __on_post__ posting of message
    # =============

    def __on_post__(self):

        # same exchange or overwrite with config one ?

        if self.post_exchange : self.msg.exchange = self.post_exchange

        # invoke on_post when provided

        for plugin in self.on_post_list:
           if not plugin(self): return False

        ok = self.msg.publish( )

        return ok

    def overwrite_defaults(self):

        # overwrite defaults
        # the default settings in most cases :
        # sarra receives directly from sources  onto itself
        # or it consumes message from another pump
        # we cannot define a default broker exchange

        # default broker and exchange None

        self.broker       = None
        self.exchange     = None
        self.topic_prefix = None

        # FIX ME  report_exchange set to NONE
        # instead of xreport and make it mandatory perhaps ?
        # since it can be xreport or xs_remotepumpUsername ?
        self.report_exchange = 'xreport'

        # in most cases, sarra downloads and repost for itself.
        # default post_broker and post_exchange are

        self.post_broker    = None
        self.post_exchange  = None
        if hasattr(self,'manager'):
           self.post_broker = self.manager

        # Should there be accept/reject option used unmatch are accepted

        self.accept_unmatch = True


    # =============
    # process message  
    # =============

    def process_message(self):

        self.logger.debug( "Received %s '%s' %s" % (self.msg.topic,self.msg.notice,self.msg.hdrstr) )

        #=================================
        # now message is complete : invoke __on_message__
        #=================================

        ok = self.__on_message__()
        if not ok : return ok

        #=================================
        # publish the message
        #=================================

        self.__on_post__()

        if self.reportback:
            self.msg.report_publish(201,'Published')


        return True


    def run(self):

        # present basic config

        self.logger.info("sr_shovel run")

        if not self.report_daemons and self.config_name[0:3] == 'rr_' :
            self.logger.info("report_daemons is False, skipping %s config." % self.config_name )
            self.stop_instance()

        # loop/process messages

        self.connect()

        if ( self.restore_queue is not None ) and os.path.exists(self.save_path):
           self.restore_exchange_name  = 'xs_' + self.broker.username + '.' + \
                self.program_name + '.' + self.config_name + '.restore'

           rtot=0
           with open(self.save_path,"r") as rf:
               for ml in rf:
                   rtot += 1

           self.logger.info("sr_shovel restoring %d messages from save %s " % ( rtot, self.save_path ) )
           rnow=0

           with open(self.save_path,"r") as rf:
               for ml in rf:
                  rnow += 1
                  self.msg.exchange = 'save'
                  self.msg.topic, self.msg.headers, self.msg.notice = json.loads(ml)
                  self.msg.from_amqplib()
                  self.logger.info("sr_shovel restoring message %d of %d: topic: %s" % (rnow, rtot, self.msg.topic) )
                  ok = self.process_message()

           if self.save_file :
               self.logger.info("sr_shovel restore: %s complete." % ( self.save_path ) )
           elif rnow >= rtot:
               self.logger.info("sr_shovel restore complete deleting save file: %s " % ( self.save_path ) )
               os.unlink(self.save_path)
           else:
               self.logger.error("sr_shovel only restored %d of %d messages from save file: %s " % ( rnow, rtot, self.save_path ) )
 
           # should have effect of deleting restore exchange as auto_delete is True.
           self.hc_pst.channel.queue_unbind( self.restore_queue, self.post_exchange, '#' )

           # clean exit
           sys.exit(0)


        if self.save :
            self.logger.info("sr_shovel saving to %s for future restore" % self.save_path )
            sf = open(self.save_path,"a")
            stot=0


        active = self.has_vip()
        if not active :
            self.logger.debug("sr_shovel does not have vip=%s, is sleeping", self.vip)
        else:
            self.logger.debug("sr_shovel is active on vip=%s", self.vip)

        while True :
              try :
                  #  is it sleeping ?
                  if not self.has_vip() :
                          if active:
                              self.logger.debug("sr_shovel does not have vip=%s, is sleeping", self.vip)
                              active=False

                          time.sleep(5)
                          continue
                  else:
                          if not active:
                              self.logger.debug("sr_shovel is active on vip=%s", self.vip)
                              active=True

                  #  consume message
                  ok, self.msg = self.consumer.consume()
                  if not ok : continue
                  if self.save :
                      stot += 1
                      self.logger.info("sr_shovel saving %d message topic: %s" % ( stot, self.msg.topic ) )
                      sf.write(json.dumps( [ self.msg.topic, self.msg.headers, self.msg.notice ], sort_keys=True) + '\n')
                      sf.flush()
                  else:
                      #  process message (ok or not... go to the next)
                      ok = self.process_message()

              except:
                      (stype, svalue, tb) = sys.exc_info()
                      self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
    
        if self.save:
            sf.close()


    def reload(self):
        self.logger.info("%s reload" % self.program_name)
        self.close()
        self.configure()
        self.run()

    def start(self):
        self.logger.info("%s %s start" % (self.program_name, sarra.__version__) )
        self.run()

    def stop(self):
        self.logger.info("%s stop" % self.program_name)
        self.close()
        os._exit(0)

# ===================================
# MAIN
# ===================================

def main():

    action = None
    args   = None
    config = None

    if len(sys.argv) >= 2 : 
       action = sys.argv[-1]

    if len(sys.argv) >= 3 : 
       config = sys.argv[-2]
       args   = sys.argv[1:-2]

    shovel = sr_shovel(config,args)

    if   action == 'foreground' : shovel.foreground_parent()
    elif action == 'reload'     : shovel.reload_parent()
    elif action == 'restart'    : shovel.restart_parent()
    elif action == 'start'      : shovel.start_parent()
    elif action == 'stop'       : shovel.stop_parent()
    elif action == 'status'     : shovel.status_parent()
    else :
           shovel.logger.error("action unknown %s" % action)
           shovel.help()
           sys.exit(1)

    sys.exit(0)



# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
