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

    def check(self):

        self.sleep_connect_try_interval_min=0.01
        self.sleep_connect_try_interval_max=30
        self.sleep_connect_try_interval=self.sleep_connect_try_interval_min

        self.connected     = False 

        if self.config_name == None : return

        self.check_consumer_options()

        # posting... discard not permitted

        if self.post_broker != None :

           if self.post_exchange == None and self.post_exchange_suffix :
              self.post_exchange = 'xs_%s' % self.post_broker.username + '_' + self.post_exchange_suffix

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
           if self.post_base_url == None :
              self.post_base_url = self.destination

           # overwrite inflight to be None when posting to a broker.
           if self.inflight == 'unspecified':
              self.inflight=None
        else:
           if self.inflight == 'unspecified':
              self.inflight='.tmp'
           
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

        if self.notify_only :
           self.logger.error("sender notify_only True\n")
           sys.exit(1)

        # never discard

        if self.discard :
           self.logger.error("sender discard True\n")
           sys.exit(1)


    # =============
    # __do_send__
    # =============

    def __do_send__(self):

        self.logger.debug("sending/copying %s to %s " % ( self.msg.relpath, self.msg.new_dir ) )

        # try registered do_send first... might overload defaults

        scheme = self.details.url.scheme 
        try:
                if   scheme in self.do_sends :
                     self.logger.debug("using registered do_send for %s" % scheme)
                     do_send = self.do_sends[scheme]
                     ok = do_send(self)
                     # if ok == None  it means that the scheme was one
                     # of the supported python one (sftp,ftp[s])
                     # and the plugin decided to go with the python defaults
                     if ok != None : return ok
        except:
                self.logger.debug('Exception details:', exc_info=True)


        # try supported hardcoded send

        try : 
                if   scheme in ['ftp','ftps']  :
                     if not hasattr(self,'ftp_link') :
                        self.ftp_link = ftp_transport()
                     ok = self.ftp_link.send(self)
                     return ok

                elif scheme == 'sftp' :
                     try    : from sr_sftp       import sftp_transport
                     except : from sarra.sr_sftp import sftp_transport
                     if not hasattr(self,'sftp_link') :
                        self.sftp_link = sftp_transport()
                     ok = self.sftp_link.send(self)
                     return ok


                # user defined send scripts
                # if many are configured, this one is the last one in config

                elif self.do_send :
                     ok = self.do_send(self)
                     return ok

        except :
                if self.reportback:
                    self.msg.report_publish(503, "Unable to process")
                self.logger.error("sender/__do_send__: could not send")
                self.logger.debug('Exception details: ', exc_info=True)

        # something went wrong

        if self.reportback:
           self.msg.report_publish(503,"Service unavailable %s" % self.msg.url.scheme)

        return False

    def overwrite_defaults(self):

        # a destination must be provided

        self.destination    = None
        self.currentDir     = None
        self.currentPattern = None

        # consumer defaults

        if hasattr(self,'manager'):
           self.broker = self.manager
        self.exchange  = 'xpublic'

        # most of the time we want to mirror product directory

        self.mirror      = True

        # add msg_2localfile to the on_message_list at the beginning

        self.execfile("on_message",'msg_2localfile')
        self.on_message_list.insert(0,self.on_message )

        # always sends ...

        self.notify_only = False

        # never discard

        self.discard = False

        # dont accept unmatch by default

        self.accept_unmatch = False



    # =============
    # doit_send  
    # =============

    def doit_send(self,parent=None):
        self.logger.debug("doit_send with %s '%s %s %s' %s" % \
            (self.msg.topic, self.msg.pubtime, self.msg.baseurl, \
             self.msg.relpath, self.msg.hdrstr))

        self.logger.debug("doit_send to: %s / %s " % ( self.msg.new_dir, self.msg.new_file)  )
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

        if self.msg.baseurl != 'file:' :
           self.logger.error("protocol should be 'file:' message ignored")
           return False

        #=================================
        # proceed to send :  has to work
        #=================================

        # N attempts to send

        i  = 1
        while i <= self.attempts :
              # it is confusing to see in log for the same product
              # Delivery failed on one line than... 
              # Sent on next line
              # so insert a warning about subsequent  attempts
              if i != 1  : self.logger.warning("attempt %d" % i )

              ok = self.__do_send__()
              if ok : break
              # dont force on retry 
              if self.msg.isRetry : break
              i = i + 1
               
        # if retry mode... do retry stuff
        if self.retry_mode :
           if ok : self.consumer.msg_worked()
           else  : self.consumer.msg_to_retry()

        # could not download ...

        if not ok: return False

        #=================================
        # publish our sending
        #=================================

        if self.post_broker :
           self.msg.set_topic(self.post_topic_prefix,self.msg.new_relpath)
           self.msg.set_notice(self.msg.new_baseurl,self.msg.new_relpath,self.msg.pubtime)
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
