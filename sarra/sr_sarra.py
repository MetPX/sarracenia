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
# sr_sarra.py : python3 program allowing users to listen and download product from
#               another sarracenia server or from user posting (sr_post/sr_watch)
#               and reannounce the product on the current server
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Mon Sep 25 20:45 UTC 2017
#                   code rewritten : sr_sarra is an instantiation of sr_subscribe
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
# sr_sarra [options] [config] [foreground|start|stop|restart|reload|status|cleanup|setup]
#
# sr_sarra consumes message, for each message it downloads the product
# and reannounce it. On usage of sarra is to acquire data from source
# that announce their products.  The other usage is to dessiminate products
# from other brokers/pumps.
#
# condition 1: from a source
# broker                  = where sarra is running (manager)
# exchange                = xs_source_user
# product                 = downloaded under directory (option document_root)
#                         = subdirectory from mirror option  OR
#                           message.headers['rename'] ...
#                           can be trimmed by option  strip
#
# post_broker             = where sarra is running (manager)
# post_exchange           = xpublic
# post_message            = same as incoming message
#                           message.headers['source']  is set from source_user
#                           message.headers['cluster'] is set from option cluster from default.conf
#                           message is built from url option give
#
# report_exchange         = xreport
#
#
# condition 2: from another broker/pump
# broker                  = the remote broker...
# exchange                = xpublic
# product                 = usually the product placement is mirrored 
#                           option document_root needs to be set
# post_broker             = where sarra is running (manager)
# post_exchange           = xpublic
# post_message            = same as incoming message
#                           message.headers['source']  left as is
#                           message.headers['cluster'] left as is 
#                           option url : gives new url announcement for this product
# report_exchange         = xs_"remoteBrokerUser"
#
#
#============================================================

import os,sys,time

try :    
         from sr_subscribe      import *
         print( "Using local module definitions, not system ones")
except : 
         from sarra.sr_subscribe import *

class sr_sarra(sr_subscribe):

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

        # verify post_base_dir

        if self.post_base_dir == None :
           if self.post_document_root != None :
              self.post_base_dir = self.post_document_root
              self.logger.warning("use post_base_dir instead of post_document_root")
           elif self.document_root != None :
              self.post_base_dir = self.document_root
              self.logger.warning("use post_base_dir instead of document_root")

        # bindings should be defined 

        if self.bindings == []  :
           key = self.topic_prefix + '.#'
           self.bindings.append( (self.exchange,key) )
           self.logger.debug("*** BINDINGS %s"% self.bindings)

        # default queue name if not given

        if self.queue_name == None :
           self.queue_name  = 'q_' + self.broker.username + '.'
           self.queue_name += self.program_name + '.' + self.config_name 

        # ===========================================================
        # some sr_subscribe options reset to match sr_sarra behavior
        # ===========================================================

        # currentDir is post_document_root if unset

        if self.currentDir == None :
           self.currentDir = self.post_document_root

        # always download ...

        self.notify_only = False

        # we dont save nor restore

        self.save    = False
        self.restore = False

        # never discard

        self.discard = False

        # default reportback if unset

        if self.reportback == None : self.reportback = False

        # do_task should have doit_download for now... make it a plugin later
        # and the download is the first thing that should be done

        if not self.doit_download in self.do_task_list :
           self.do_task_list.insert(0,self.doit_download)

        # MG FIXME : I dont think I forgot anything but if some options need
        #            to be specifically set for sr_sarra put them HERE

    def overwrite_defaults(self):

        # overwrite defaults
        # the default settings in most cases :
        # sarra receives directly from sources  onto itself
        # or it consumes message from another pump
        # we cannot define a default broker exchange

        # default broker and exchange None

        self.broker   = None
        self.exchange = None
        # FIX ME  report_exchange set to NONE
        # instead of xreport and make it mandatory perhaps ?
        # since it can be xreport or xs_remotepumpUsername ?

        # in most cases, sarra downloads and repost for itself.
        # default post_broker and post_exchange are

        self.post_broker    = None
        self.post_exchange  = 'xpublic'
        if hasattr(self,'manager'):
           self.post_broker = self.manager

        # Should there be accept/reject option used unmatch are accepted

        self.accept_unmatch = True

        # most of the time we want to mirror product directory and share queue

        self.mirror         = True

        # no directory if not provided

        self.currentDir     = None

        # ===========================================================
        # some sr_subscribe options reset to understand user sr_sarra setup
        # ===========================================================

        self.reportback = None


# ===================================
# MAIN
# ===================================

def main():

    args,action,config,old = startup_args(sys.argv)

    sarra = sr_sarra(config,args,action)
    sarra.exec_action(action,old)

    os._exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()

