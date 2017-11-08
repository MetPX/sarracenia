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
# sr_winnow.py : python3 program allowing to winnow duplicated messages
#                and post the unique and first message in.
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Mon Sep 25 20:00 UTC 2017
#                   code rewritten : sr_winnow is an instantiation of sr_subscribe
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

try :    
         from sr_subscribe       import *
except : 
         from sarra.sr_subscribe import *

class sr_winnow(sr_subscribe):

    def __init__(self,config=None,args=None,action=None):
        sr_subscribe.__init__(self,config,args,action)

    def check(self):

        if self.config_name == None : return

        # no queue name allowed

        if self.queue_name == None:
           self.queue_name  = 'q_' + self.broker.username + '.'
           self.queue_name += self.program_name + '.' + self.config_name 

        # we cannot have more than one instance since we 
        # need to work with a single cache.

        if self.nbr_instances != 1 :
           self.logger.warning("Only one instance allowed... set to 1")
           self.nbr_instances = 1

        # exchange must be provided 
        if self.exchange == None:
           self.logger.error("exchange (input) unset... exitting")
           sys.exit(1)

        # post_exchange must be provided
        if self.post_exchange == None :
           self.logger.error("post_exchange (output) not properly set...exitting")
           sys.exit(1)

        # post_exchange must be different from exchange if on same broker
        if not self.post_broker and self.post_exchange == self.exchange :
           self.logger.error("post_exchange (output) not properly set...exitting")
           sys.exit(1)

        if not self.post_broker : self.post_broker = self.broker

        # no vip given... so should not matter ?
        if self.vip == None and self.interface == None :
           self.logger.debug("both vip and interface missing... standalone mode")

        # bindings should be defined 

        if self.bindings == []  :
           key = self.topic_prefix + '.#'
           self.bindings.append( (self.exchange,key) )
           self.logger.debug("*** BINDINGS %s"% self.bindings)

        # accept/reject
        self.use_pattern          = self.masks != []
        self.accept_unmatch       = True

        # caching must be "on" ( entry cleanup default to 20 mins old )

        if not self.caching : self.caching = 1200

        self.cache      = sr_cache(self)
        self.cache_stat = True
        self.cache.open()
        self.execfile("on_heartbeat",'heartbeat_cache')
        self.on_heartbeat_list.append(self.on_heartbeat)

        # ===========================================================
        # some sr_subscribe options reset to match sr_winnow behavior
        # ===========================================================

        # set notify_only : no download

        self.notify_only = True

        # we dont save nor restore

        self.save    = False
        self.restore = False

        # default reportback if unset

        if self.reportback == None : self.reportback = True

        # MG FIXME : I dont think I forgot anything but if some options need
        #            to be specifically set for sr_winnow put them HERE

    def overwrite_defaults(self):

        # default broker : manager

        self.broker      = None
        self.post_broker = None
        if hasattr(self,'manager'):
           self.broker   = self.manager

        # ===========================================================
        # some sr_subscribe options reset to understand user sr_winnow setup
        # ===========================================================

        self.reportback = None

# ===================================
# MAIN
# ===================================

def main():

    args,action,config,old = startup_args(sys.argv)

    winnow = sr_winnow(config,args,action)
    winnow.exec_action(action,old)

    os._exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
