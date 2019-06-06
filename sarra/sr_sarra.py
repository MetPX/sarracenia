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

    def check(self):

        if self.config_name == None : return

        self.check_consumer_options()

        if self.post_broker == None : self.post_broker = self.broker

        # post exchanges suffix process if needed

        if self.post_exchange == None and self.post_exchange_suffix :
           self.post_exchange = 'xs_%s' % self.post_broker.username + self.post_exchange_suffix

        # verify post_base_dir

        if self.post_base_dir == None :
           if self.post_document_root != None :
              self.post_base_dir = self.post_document_root
              self.logger.warning("use post_base_dir instead of post_document_root")
           elif self.document_root != None :
              self.post_base_dir = self.document_root
              self.logger.warning("use post_base_dir instead of document_root")

        # ===========================================================
        # some sr_subscribe options reset to match sr_sarra behavior
        # ===========================================================

        # currentDir is post_document_root if unset

        if self.currentDir == None :
           self.currentDir = self.post_document_root

        # always download ...

        if self.notify_only :
           self.logger.error("sarra notify_only True")
           os._exit(1)

        # we dont save nor restore

        if self.save or self.restore :
           self.logger.error("sarra no save/restore support")
           sys.exit(1)

        # we dont discard

        if self.discard :
           self.logger.error("sarra discard True")
           sys.exit(1)


        # default reportback if unset

        if self.reportback == None : self.reportback = False

        # do_task should have doit_download for now... make it a plugin later
        # and the download is the first thing that should be done

        if not self.doit_download in self.do_task_list :
           self.do_task_list.insert(0,self.doit_download)

    def overwrite_defaults(self):

        # overwrite defaults
        # the default settings in most cases :
        # sarra receives directly from sources  onto itself
        # or it consumes message from another pump
        # we cannot define a default broker exchange

        # since it can be xreport or xs_remotepumpUsername ?
        # default broker and exchange None

        # in most cases, sarra downloads and repost for itself.
        self.inflight = None

        # default post_broker and post_exchange are

        self.post_exchange  = 'xpublic'
        if hasattr(self,'manager'):
           self.post_broker = self.manager

        # most of the time we want to mirror product directory and share queue

        self.mirror         = True

        # no directory if not provided

        self.currentDir     = None


        # ===========================================================
        # some sr_subscribe options reset to understand user sr_sarra setup
        # ===========================================================

        self.discard     = False
        self.notify_only = False
        self.restore     = False
        self.save        = False

        self.reportback  = None

        self.accept_unmatch = True



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

