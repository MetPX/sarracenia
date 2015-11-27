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
# sr_log2source.py : python3 program takes all log messages and repost them to the
#                    log exchange of the source user
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Jun Hu         - Shared Services Canada
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

import signal

#============================================================
# usage example
#
# sr_log2source -b broker -i 1

#============================================================

try :    
         from sr_amqp           import *
         from sr_instances      import *
         from sr_message        import *
except : 
         from sarra.sr_amqp      import *
         from sarra.sr_instances import *
         from sarra.sr_message   import *


class sr_log2source(sr_instances):

    def __init__(self,config=None,args=None):
        sr_instances.__init__(self,config,args)
        self.defaults()
        self.exchange = 'xlog'
        self.topic    = 'v02.log.#'
        self.broker   = urllib.parse.urlparse('amqp://guest:guest@localhost/')
        self.configure()


    def check(self):
        # dont want to recreate these if they exists
        if not hasattr(self,'msg') :
           self.msg = sr_message(self.logger)

    def close(self):
        self.hc.close()

    def configure(self):

        # installation general configurations and settings

        self.general()

        # arguments from command line

        self.args(self.user_args)

        # config from file

        self.config(self.user_config)

        # verify all settings

        self.check()
        self.logger.info("nbr_instances %d"% self.nbr_instances)


    def connect(self):

        # =============
        # consumer
        # =============

        # consumer host

        self.hc = HostConnect( logger = self.logger )
        self.hc.set_url( self.broker )
        self.hc.connect()

        # consumer  add_prefetch(1) allows queue sharing between instances

        self.consumer  = Consumer(self.hc)
        self.consumer.build()

        # consumer queue

        name  = 'q_' + self.broker.username + '.' + self.program_name
        if self.queue_name != None :
           name = 'q_' + self.broker.username + '.' + self.queue_name

        self.queue = Queue(self.hc,name)
        self.queue.add_binding(self.exchange,self.topic)
        self.queue.build()

        # publisher

        self.pub = Publisher(self.hc)
        self.pub.build()


    def help(self):
        self.logger.info("Usage: %s -b <broker> -i <instances> [start|stop|restart|reload|status]  \n" % self.program_name )
        self.logger.info("OPTIONS:")
        self.logger.info("-b   <broker>    default:amqp://guest:guest@localhost/")
        self.logger.info("-i   <instances> default:1")

    def run(self):

        self.logger.info("sr_log2source run")
        self.logger.info("AMQP  broker(%s) user(%s) vhost(%s)" % (self.broker.hostname,self.broker.username,self.broker.path) )
        self.logger.info("AMQP  input :    exchange(%s) topic(%s)" % (self.exchange,self.topic) )



        self.connect()

        self.msg.logger       = self.logger
        self.msg.amqp_log     = None
        self.msg.amqp_pub     = None

        #
        # loop on all message
        #

        raw_msg = None

        while True :

          try  :
                 if raw_msg != None : self.consumer.ack(raw_msg)

                 raw_msg = self.consumer.consume(self.queue.qname)
                 if raw_msg == None : continue

                 # make use it as a sr_message

                 self.msg.from_amqplib(raw_msg)

                 self.logger.info("Received topic   %s" % self.msg.topic)
                 self.logger.info("Received notice  %s" % self.msg.notice)
                 self.logger.info("Received headers %s\n" % self.msg.hdrstr)

                 # check for  from_cluster and source in headers

                 if not 'from_cluster' in self.msg.headers :
                    self.logger.info("skipped : no cluster in message headers")
                    continue

                 if not 'source' in self.msg.headers :
                    self.logger.info("skipped : no source in message headers")
                    continue

                 # skip if cluster is not self.broker.hostname

                 if self.msg.headers['from_cluster'] != self.cluster :
                    self.logger.info("not for this cluster %s = %s\n" % (self.broker.hostname,self.cluster ))
                    continue

                 # ok ship it back to the user exchange 

                 user_exchange = 'xl_' + self.msg.headers['source']

                 # FIXME ... what to do if xl_'source' does not work ????  ex.: deleting a user... extra log message back ...

                 ok = self.pub.publish( user_exchange, self.msg.topic, self.msg.notice, self.msg.headers )
                 if ok : self.logger.info("published to %s" % user_exchange)


          except :
                 (type, value, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s,  ..." % (type, value))

    def reload(self):
        self.logger.info("sr_log2source reload")
        self.close()
        self.configure()
        self.run()

    def start(self):
        self.configure()
        self.logger.info("sr_log2source start")
        self.run()

    def stop(self):
        self.logger.info("sr_log2source stop")
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
       if len(sys.argv) > 3: args = sys.argv[1:-1]

    log2source = sr_log2source(config,args)

    if   action == 'reload' : log2source.reload_parent()
    elif action == 'restart': log2source.restart_parent()
    elif action == 'start'  : log2source.start_parent()
    elif action == 'stop'   : log2source.stop_parent()
    elif action == 'status' : log2source.status_parent()
    else :
           log2source.logger.error("action unknown %s" % action)
           sys.exit(1)

    sys.exit(0)



# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
