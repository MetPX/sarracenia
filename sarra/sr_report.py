#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#
# sr_report.py : python3 program allowing users to receive all report messages
#             generated from his products
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Tue Oct  3 18:25 UTC 2017
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 2 of the License.
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
# sr_report -b broker

#============================================================

try :    
         from sr_subscribe       import *
except : 
         from sarra.sr_subscribe import *

class sr_report(sr_subscribe):

    def check(self):
        self.logger.debug("%s check" % self.program_name)
        if self.config_name == None : return

        self.nbr_instances = 1
        self.reportback    = False
        self.notify_only   = True
        self.post_broker   = None

        self.check_consumer_options()

        username = self.broker.username

        for i,tup in enumerate(self.bindings):
            e,k   = tup
            if e != self.exchange :
               self.logger.info("exchange forced to %s" % self.exchange)
               e = self.exchange
            self.bindings[i] = (e,k)

    def overwrite_defaults(self):
        self.logger.debug("%s overwrite_defaults" % self.program_name)
        self.topic_prefix         = 'v02.report'
        self.subtopic             = '#'
        self.accept_unmatch       = True

    def help(self):
        print("Usage: %s [OPTIONS] configfile [add|cleanup|edit|foreground|start|stop|restart|reload|remove|setup|status]\n" % self.program_name )
        print("version: %s \n" % sarra.__version__ )
        print("Or   : %s [OPTIONS] -b <broker> [add|cleanup|edit|foreground|start|stop|restart|reload|remove|setup|status]\n" % self.program_name )
        self.logger.info("OPTIONS:")
        self.logger.info("-b   <broker>   default:amqp://guest:guest@localhost/")

# ===================================
# MAIN
# ===================================

def main():

    args,action,config,old = startup_args(sys.argv)

    # config is optional so check the argument


    args,action,config,old = startup_args(sys.argv)

    srreport = sr_report(config,args,action)

    srreport.exec_action(action,old)

    os._exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
