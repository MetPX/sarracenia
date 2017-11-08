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
#  Last Changed   : Mon Sep 25 18:05 UTC 2017
#                   code rewritten : sr_shovel is an instantiation of sr_subscribe
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

    def __init__(self,config=None,args=None,action=None):
        sr_subscribe.__init__(self,config,args,action)


    def check(self):

        if self.config_name == None : return

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

        #self.accept_msg_for_clusters      = [ self.cluster ]
        #self.accept_msg_for_clusters.extend ( self.cluster_aliases )
        #self.accept_msg_for_clusters.extend ( self.gateway_for  )
        #self.logger.debug("accept_msg_for_clusters %s "% self.accept_msg_for_clusters)

        # default queue name if not given

        if self.queue_name == None :
           self.queue_name  = 'q_' + self.broker.username + '.'
           self.queue_name += self.program_name + '.' + self.config_name 

        # ===========================================================
        # some sr_subscribe options reset to match sr_shovel behavior
        # ===========================================================

        # the message is consumed and posted

        self.notify_only = True

        # default reportback if unset

        if self.reportback == None : self.reportback = True

        # MG FIXME : I dont think I forgot anything but if some options need
        #            to be specifically set for sr_shovel put them HERE

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
        
        # ===========================================================
        # some sr_subscribe options reset to understand user sr_shovel setup
        # ===========================================================

        self.reportback = None

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
