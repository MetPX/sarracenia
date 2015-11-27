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
# sr_log.py : python3 program allowing users to receive all log messages
#             generated from his products
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
# sr_log -b broker

#============================================================

try :    
         from sr_amqp           import *
         from sr_config       import *
         from sr_message        import *
except : 
         from sarra.sr_amqp      import *
         from sarra.sr_config  import *
         from sarra.sr_message   import *


class sr_log(sr_config):

    def __init__(self,config=None,args=None):
        sr_config.__init__(self,config,args)

    def check(self):
        self.msg = sr_message(self.logger)

        if self.exchange == None :
           self.exchange = 'xl_' + self.broker.username

        self.topic = self.topic_prefix + '.' + self.subtopic

    def close(self):
        self.hc_src.close()

    def configure(self):

        # installation general configurations and settings

        self.general()

        # defaults general and proper to sr_post

        self.defaults()

        self.topic_prefix = 'v02.log'
        self.subtopic     = '#'

        self.broker       = urllib.parse.urlparse('amqp://guest:guest@localhost/')

        # arguments from command line

        self.args(self.user_args)

        # config from file

        self.config(self.user_config)

        # verify all settings

        self.check()


    def connect(self):

        # =============
        # consumer
        # =============

        # consumer host

        self.hc_src = HostConnect( logger = self.logger )
        self.hc_src.set_url( self.broker )
        self.hc_src.connect()

        # consumer  add_prefetch(1) allows queue sharing between instances

        self.consumer  = Consumer(self.hc_src)
        self.consumer.build()

        # consumer queue

        # OPTION ON QUEUE NAME ?
        name  = 'q_' + self.broker.username + '.' 
        if self.queue_name != None :
           name += self.queue_name
        else :
           name += self.program_name + '.' + self.exchange

        self.queue = Queue(self.hc_src,name)
        self.queue.add_binding(self.exchange,self.topic)
        self.queue.build()


    def help(self):
        self.logger.info("Usage: %s -b <broker> \n" % self.program_name )
        self.logger.info("OPTIONS:")
        self.logger.info("-b   <broker>   default:amqp://guest:guest@localhost/")

    def run(self):

        self.logger.info("sr_log run")
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
                 raw_msg = self.consumer.consume(self.queue.qname)
                 if raw_msg == None : continue

                 # make use it as a sr_message

                 self.msg.from_amqplib(raw_msg)

                 self.logger.info("Received topic   %s" % self.msg.topic)
                 self.logger.info("Received notice  %s" % self.msg.notice)
                 self.logger.info("Received headers %s\n" % self.msg.hdrstr)

                 self.consumer.ack(raw_msg)
          except :
                 (type, value, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s,  ..." % (type, value))
                 

def main():

    dlog = sr_log(config=None,args=sys.argv)
    dlog.configure()

    # =========================================
    # signal stop
    # =========================================

    def signal_stop(signal, frame):
        dlog.logger.info('Stop!')
        dlog.close()
        os._exit(0)

    # =========================================
    # signal handling
    # =========================================

    signal.signal(signal.SIGINT, signal_stop)

    dlog.run()

    sys.exit(0)

if __name__ == '__main__':
    main()

