#!/usr/bin/python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SaraDocumentation
#
# dd_subscribe.py : python3 program allowing users to download product from dd.weather.gc.ca
#                   as soon as they are made available (through amqp notifications)
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
# dd_log -b broker

#============================================================

try :    
         from dd_amqp           import *
         from dd_config       import *
         from dd_message        import *
except : 
         from sara.dd_amqp      import *
         from sara.dd_config  import *
         from sara.dd_message   import *


class dd_log(dd_config):

    def __init__(self,config=None,args=None):
        dd_config.__init__(self,config,args)
        self.configure()

    def check(self):
        self.msg = dd_message(self.logger)

    def close(self):
        self.hc_src.close()

    def configure(self):

        # defaults general and proper to dd_post

        self.defaults()

        self.exchange = 'xlog'
        self.topic    = 'v02.log.#'
        self.broker   = urllib.parse.urlparse('amqp://guest:guest@localhost/')

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
        name  = 'cmc.' + self.program_name + '.' + self.exchange
        if self.queue_name != None :
           name = self.queue_name

        self.queue = Queue(self.hc_src,name)
        self.queue.add_binding(self.exchange,self.topic)
        self.queue.build()


    def help(self):
        self.logger.info("Usage: %s -b <broker> \n" % self.program_name )
        self.logger.info("OPTIONS:")
        self.logger.info("-b   <broker>   default:amqp://guest:guest@localhost/")

    def run(self):

        self.logger.info("dd_log run")

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

                 # make use it as a dd_message

                 self.msg.from_amqplib(raw_msg)

                 self.logger.info("Received topic   %s" % self.msg.topic)
                 self.logger.info("Received notice  %s" % self.msg.notice)
                 self.logger.info("Received headers %s\n" % self.msg.headers)

                 self.consumer.ack(raw_msg)
          except :
                 (type, value, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s,  ..." % (type, value))
                 

def main():

    dlog = dd_log(config=None,args=sys.argv)
    dlog.configure()
    dlog.connect()

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

