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
# sr_shovel.py : python3 program allows to shovel message from one source broker
#                to another destination broker (called post_broker)
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Mon Sep 25 18:05 UTC 2017
#                   code rewritten : sr_shovel is an instantiation of sr_subscribe
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
#============================================================
# usage example
#
# sr_shovel [options] [config] [foreground|start|stop|restart|reload|status|cleanup|setup]
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
# report_exchange         = xreport (sent back to broker)
#
#============================================================
#

try :    
         from sr_subscribe      import *
except : 
         from sarra.sr_subscribe import *

class sr_shovel(sr_subscribe):

    def check(self):

        if self.config_name == None : return

        self.check_consumer_options()

        # exchanges suffix process if needed

        if self.post_exchange == None and self.post_exchange_suffix :
           self.post_exchange = 'xs_%s' % self.post_broker.username + self.post_exchange_suffix

        # ===========================================================
        # some sr_subscribe options reset to match sr_shovel behavior
        # ===========================================================

        # the message is consumed and posted (no download)

        if not self.notify_only :
           self.logger.error("sr_shovel works with notify_only True")
           sys.exit(1)

    def overwrite_defaults(self):

        # overwrite defaults
        # the default settings in most cases :
        # sarra receives directly from sources  onto itself
        # or it consumes message from another pump
        # we cannot define a default broker exchange

        # in most cases, sarra downloads and repost for itself.
        # default post_broker and post_exchange are

        if hasattr(self,'manager'):
           self.post_broker = self.manager

        # ===========================================================
        # some sr_subscribe options reset to understand user sr_shovel setup
        # ===========================================================

        self.notify_only    = True
        self.accept_unmatch = True

# ===================================
# MAIN
# ===================================

def main():

    args,action,config,old = startup_args(sys.argv)

    shovel = sr_shovel(config,args,action)
    shovel.exec_action(action,old)

    os._exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
