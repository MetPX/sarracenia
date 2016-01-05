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
         from sr_consumer       import *
except : 
         from sarra.sr_consumer import *


class sr_log(sr_config):

    def __init__(self,config=None,args=None):
        sr_config.__init__(self,config,args)
        self.configure()

    def check(self):
        self.exchange = 'xl_' + self.broker.username

        if self.bindings == [] :
           key = self.topic_prefix + '.' + self.subtopic
           self.bindings     = [ (self.exchange,key) ]

        # pattern must be used
        # if unset we will accept unmatched... so everything

        self.use_pattern          = self.masks != []
        self.accept_unmatch       = self.masks == []

    def close(self):
        self.consumer.close()

    def configure(self):

        # installation general configurations and settings

        self.general()

        # defaults

        self.defaults()


        # proper to this program

        self.exchange             = 'xl_' + self.broker.username
        self.topic_prefix         = 'v02.log'
        self.subtopic             = '#'
        self.broker               = urllib.parse.urlparse('amqp://guest:guest@localhost/')

        # arguments from command line

        self.args(self.user_args)

        # config from file

        self.config(self.user_config)

        # verify all settings

        self.check()


    def help(self):
        self.logger.info("Usage: %s -b <broker> \n" % self.program_name )
        self.logger.info("OPTIONS:")
        self.logger.info("-b   <broker>   default:amqp://guest:guest@localhost/")

    def run(self):

        self.logger.info("sr_log run")

        parent        = self
        self.consumer = sr_consumer(parent)

        #
        # loop on all message
        #

        while True :

          try  :
                 ok, self.msg = self.consumer.consume()
                 if not ok : continue

                 self.logger.info("Received topic   %s" % self.msg.topic)
                 self.logger.info("Received notice  %s" % self.msg.notice)
                 self.logger.info("Received headers %s\n" % self.msg.hdrstr)

          except :
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
                 

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

