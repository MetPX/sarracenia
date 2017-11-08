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
# sr_sender.py : python3 program consumes product messages and send them to another pump
#                and announce the newly arrived product on that pump. If the post_broker
#                is not given... it is accepted, the products are sent without notices.
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Wed Oct  4 20:24 UTC 2017
#                   code rewritten : sr_sender is an instantiation of sr_subscribe
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
# sr_sender [options] [config] [foreground|start|stop|restart|reload|status|cleanup|setup]
#
# sr_sender connects to a broker. For each product it has selected, it sends it onto the other
# broker and reannounce it there.
#
# conditions:
#
# broker                  = where sarra is running (manager)
# exchange                = xpublic
# message.headers[to_clusters] verified if destination includes remote pump ?
#
# do_send                 = a script supporting the protocol defined in the destination
# destination             = an url of the credentials of the remote server and its options (see credentials)
# directory               = the placement is mirrored usually
# accept/reject           = pattern matching what we want to poll in that directory
#
# (optional... only if message are posted after products are sent)
# post_broker             = remote broker (remote manager)
# post_exchange           = xpublic
# document_root           = if provided, extracted from the url if present
# url                     = build from the destination/directory/product
# product                 = the product placement is mirrored by default
#                           unless if accept/reject are under a directory option
# post_message            = incoming message with url changes
#                           message.headers['source']  left as is
#                           message.headers['cluster'] left as is 
#                           option url : gives new url announcement for this product
#============================================================

#

import os,sys,time
import json

try :    
         from sr_subscribe       import *
except : 
         from sarra.sr_subscribe import *

class sr_sender(sr_subscribe):

    def __init__(self,config=None,args=None,action=None):
        sr_subscribe.__init__(self,config,args,action)
        self.sleep_connect_try_interval_min=0.01
        self.sleep_connect_try_interval_max=30
        self.sleep_connect_try_interval=self.sleep_connect_try_interval_min


    def check(self):
        self.connected     = False 

        if self.config_name == None : return

        # fallback bindings to "all"

        if self.bindings == []  :
           key = self.topic_prefix + '.#'
           self.bindings.append( (self.exchange,key) )
           self.logger.debug("*** BINDINGS %s"% self.bindings)

        # accept/reject
        self.use_pattern          = self.masks != []
        self.accept_unmatch       = self.masks == []

        # posting... discard not permitted

        if self.post_broker != None :

           # enforcing post_exchange

           if self.post_exchange == None :
              if self.exchange   != None :
                 self.post_exchange = self.exchange
                 self.logger.warning("use post_exchange to set exchange")

           # verify post_base_dir

           if self.post_base_dir == None :
              if self.post_document_root != None :
                 self.post_base_dir = self.post_document_root
                 self.logger.warning("use post_base_dir instead of post_document_root")
              elif self.document_root != None :
                 self.post_base_dir = self.document_root
                 self.logger.warning("use post_base_dir instead of defaulting to document_root")

           # verify post_base_url (not mandatory...)
           #if self.post_base_url == None :
           #   self.logger.error("post_base_url required")

        # caching

        if self.caching :
           self.cache      = sr_cache(self)
           self.cache_stat = True
           self.cache.open()
           self.execfile("on_heartbeat",'heartbeat_cache')
           self.on_heartbeat_list.append(self.on_heartbeat)

        # reporting (by default suppose we are on pump so xreport)

        if self.reportback :
           if self.report_exchange == None :
              self.report_exchange = 'xreport'

        # no queue name allowed... force this one

        if self.queue_name == None :
           self.queue_name  = 'q_' + self.broker.username + '.'
           self.queue_name += self.program_name + '.' + self.config_name 

        # check destination

        self.details = None
        if self.destination != None :
           ok, self.details = self.credentials.get(self.destination)

        if self.destination == None or self.details == None :
           self.logger.error("destination option incorrect or missing\n")
           sys.exit(1)

        # to clusters required

        if self.to_clusters == None and self.post_broker != None :
           self.to_clusters = self.post_broker.hostname

        # do_task should have doit_send for now... make it a plugin later
        # and the sending is the last thing that should be done

        if not self.doit_send in self.do_task_list :
           self.do_task_list.append(self.doit_send)

        # ===========================================================
        # some sr_subscribe options reset to match sr_sarra behavior
        # ===========================================================

        # always sends ...

        self.notify_only = False

        # never discard

        self.discard = False

        # default reportback if unset

        if self.reportback == None : self.reportback = True


    # =============
    # __do_send__
    # =============

    def __do_send__(self):

        self.logger.debug("sending/copying %s to %s " % ( self.local_path, self.new_dir ) )

        try : 
                if   self.do_send :
                     return self.do_send(self)

                elif self.details.url.scheme in ['ftp','ftps']  :
                     if not hasattr(self,'ftp_link') :
                        self.ftp_link = ftp_transport()
                     return self.ftp_link.send(self)

                elif self.details.url.scheme == 'sftp' :
                     try    : from sr_sftp       import sftp_transport
                     except : from sarra.sr_sftp import sftp_transport
                     if not hasattr(self,'sftp_link') :
                        self.sftp_link = sftp_transport()
                     return self.sftp_link.send(self)

        except :
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Sender  Type: %s, Value: %s,  ..." % (stype, svalue))
                if self.reportback:
                    self.msg.report_publish(503,"Unable to process")
                self.logger.error("Could not send")

        if self.reportback:
           self.msg.report_publish(503,"Service unavailable %s" % self.msg.url.scheme)

    def overwrite_defaults(self):

        # a destination must be provided

        self.destination    = None
        self.post_broker    = None
        self.currentDir     = None
        self.currentPattern = None

        # consumer defaults

        if hasattr(self,'manager'):
           self.broker = self.manager
        self.exchange  = 'xpublic'

        # most of the time we want to mirror product directory

        self.mirror      = True

        # Should there be accept/reject option used unmatch are accepted

        self.accept_unmatch = True

        # add msg_2localfile to the on_message_list at the beginning

        self.execfile("on_message",'msg_2localfile')
        self.on_message_list.insert(0,self.on_message )


    # =============
    # doit_send  
    # =============

    def doit_send(self,parent=None):
        self.logger.debug("doit_send with %s '%s' %s" % (self.msg.topic,self.msg.notice,self.msg.hdrstr))

        self.local_path = self.msg.relpath

        # the code of msg_2localfile could be put here...

        #=================================
        # impossible to send
        #=================================

        if self.destination[:3] == 'ftp' :
            # 'i' cannot be supported by ftp/ftps
            # we cannot offset in the remote file to inject data
            #
            # FIXME instead of dropping the message
            # the inplace part could be delivered as 
            # a separate partfile and message set to 'p'
            if  self.msg.partflg == 'i':
                self.logger.error("ftp, inplace part file not supported")
                if self.reportback:
                   msg.report_publish(499,'ftp cannot deliver partitioned files')
                return False

        #=================================
        # check message for local file
        #=================================

        if self.msg.baseurl != 'file:' or \
           (self.msg.sumflg != 'R' and not os.path.isfile(self.msg.relpath)) :
           self.logger.error("The file to send is not local: %s" % self.msg.relpath)
           return False

        self.local_path = self.msg.relpath
        self.local_file = os.path.basename(self.msg.relpath)

        #=================================
        # proceed to send :  has to work
        #=================================

        while True : 
              ok =self.__do_send__()
              if ok :
                   self.sleep_connect_try_interval=self.sleep_connect_try_interval_min
                   break
              else:
                   #========================
                   # Connection failed.  increment interval, sleep and try again
                   #========================
                   time.sleep(self.sleep_connect_try_interval)       
                   if self.sleep_connect_try_interval < self.sleep_connect_try_interval_max:
                        self.sleep_connect_try_interval=self.sleep_connect_try_interval * 2

        #=================================
        # publish our sending
        #=================================

        if self.post_broker :
           self.msg.set_topic('v02.post',self.new_relpath)
           self.msg.set_notice(self.new_baseurl,self.new_relpath,self.msg.time)
           self.__on_post__()
           if self.reportback:
               self.msg.report_publish(201,'Published')

        return True

# ===================================
# MAIN
# ===================================

def main():

    args,action,config,old = startup_args(sys.argv)

    sender = sr_sender(config,args,action)
    sender.exec_action(action,old)

    os._exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
