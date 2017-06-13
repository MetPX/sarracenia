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
#  Last Changed   : Jan  5 08:31:59 EST 2016
#  Last Changed   : Apr  29 14:30:00 CDT 2016
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
# sr_sender [options] [config] [start|stop|restart|reload|status]
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
         from sr_amqp           import *
         from sr_consumer       import *
         from sr_ftp            import *
         from sr_instances      import *
         from sr_message        import *
         from sr_poster         import *
except : 
         from sarra.sr_amqp      import *
         from sarra.sr_consumer  import *
         from sarra.sr_ftp       import *
         from sarra.sr_instances import *
         from sarra.sr_message   import *
         from sarra.sr_poster    import *

class sr_sender(sr_instances):

    def __init__(self,config=None,args=None):
        sr_instances.__init__(self,config,args)
        self.sleep_connect_try_interval_min=0.01
        self.sleep_connect_try_interval_max=30
        self.sleep_connect_try_interval=self.sleep_connect_try_interval_min

    def check(self):
        self.connected     = False 

        # fallback bindings to "all"

        if self.bindings == []  :
           key = self.topic_prefix + '.#'
           self.bindings.append( (self.exchange,key) )
           self.logger.debug("*** BINDINGS %s"% self.bindings)

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

        # check destination
        if self.post_broker != None :
           if self.post_exchange == None : self.post_exchange = self.exchange

        # accept/reject
        self.use_pattern          = self.masks != []
        self.accept_unmatch       = self.masks == []

        # to clusters required

        if self.to_clusters == None:
            self.to_clusters = self.post_broker.hostname


    def close(self):
        self.consumer.close()
        if self.post_broker :
           self.poster.close()
        self.connected = False 
        if hasattr(self,'sftp_link'): self.sftp_link.close()
        if hasattr(self,'ftp_link') : self.ftp_link.close()

    def connect(self):

        # =============
        # create message
        # =============

        self.msg = sr_message(self)

        # =============
        # consumer
        # =============

        self.consumer          = sr_consumer(self)

        if self.save_file :
            self.consumer.save_path = self.save_file + self.save_path[-10:]
            self.save_path = self.consumer.save_path
        else:
            self.consumer.save_path = self.save_path

        if self.save: self.consumer.save = True


        self.msg.report_publisher = self.consumer.publish_back()
        # modified by Murray Dec 5 2016
        self.msg.report_exchange  = self.report_exchange
        self.logger.debug("before if self.msg.report_exchange set to %s\n" % (self.msg.report_exchange))
        if self.broker.username in self.users.keys():
                  self.logger.debug("self.msg.report_exchange usernameifthereisone: %s\n" % (self.broker.username))
                  if self.users[self.broker.username] == 'feeder' or self.users[self.broker.username] == 'admin':
                       self.msg.report_exchange = 'xreport'
                  else:
                       self.msg.report_exchange = 'xs_' + self.broker.username
        else:
           self.msg.report_exchange = 'xs_' + self.broker.username
        self.logger.debug("self.msg.report_exchange set to %s\n" % (self.msg.report_exchange))
        self.msg.user          = self.details.url.username
        self.msg.host          = self.details.url.scheme + '://' + self.details.url.hostname
        self.msg.post_exchange_split = self.post_exchange_split

        # =============
        # poster
        # =============

        if self.post_broker :
           self.poster           = sr_poster(self)

           self.msg.publisher    = self.poster.publisher
           self.msg.pub_exchange = self.post_exchange
           self.msg.user         = self.post_broker.username

        self.connected        = True 

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

    def help(self):
        print("Usage: %s [OPTIONS] configfile [start|stop|restart|reload|status]\n" % self.program_name )
        print("version: %s \n" % sarra.__version__ )
        print("OPTIONS:")
        print("instances <nb_of_instances>      default 1")
        print("\nAMQP consumer broker settings:")
        print("\tbroker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>")
        print("\t\t(MANDATORY)")
        print("\nAMQP Queue bindings:")
        print("\texchange             <name>          (default: xpublic)")
        print("\ttopic_prefix         <amqp pattern>  (default: v02.post)")
        print("\tsubtopic             <amqp pattern>  (default: #)")
        print("\t\t  <amqp pattern> = <directory>.<directory>.<directory>...")
        print("\t\t\t* single directory wildcard (matches one directory)")
        print("\t\t\t# wildcard (matches rest)")
        print("\nAMQP Queue settings:")
        print("\tdurable              <boolean>       (default: False)")
        print("\texpire               <minutes>       (default: None)")
        print("\tmessage-ttl          <minutes>       (default: None)")
        print("\nFile settings:")
        print("\tdocument_root        <document_root> (MANDATORY)")
        print("\taccept    <regexp pattern>           (default: None)")
        print("\tmirror               <boolean>       (default True)")
        print("\treject    <regexp pattern>           (default: None)")
        print("\tstrip      <strip count (directory)> (default 0)")
        print("\nDestination/message settings:")
        print("\tdo_send              <script>        (default None)")
        print("\tdestination          <url>           (MANDATORY)")
        print("\tpost_document_root   <document_root> (default None)")
        print("\turl                  <url>           (MANDATORY)")
        print("\ton_message           <script>        (default None)")
        print("\tto                   <cluster>       (MANDATORY)")
        print("\nAMQP posting broker settings (optional):")
        print("\tpost_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>")
        print("\t\t(default: manager amqp broker in default.conf)")
        print("\tpost_exchange        <name>          (default xs_postusername)")
        print("\ton_post              <script>        (default None)")
        print("DEBUG:")
        print("-debug")

    # =============
    # __on_message__
    # =============

    def __on_message__(self):

        # only if sending to another pump
        if self.post_broker != None :
           # the message has not specified a destination.
           if not 'to_clusters' in self.msg.headers :
              if self.reportback:
                  self.msg.report_publish(403,"Forbidden : message without destination amqp header['to_clusters']")
              self.logger.error("message without destination amqp header['to_clusters']")
              return False

           # this instances of sr_sender runs,
           # to send product to cluster: self.to_clusters.
           # since self.to_clusters might be a list, we check for 
           # and try matching any of this list to the message's to_clusters list

           ok = False
           for cluster in self.msg.to_clusters :
              if not cluster in self.to_clusters :  continue
              ok = True
              break

           if not ok :
              self.logger.warning("self.to_clusters=%s, self.msg.to_clusters=%s" % ( self.to_clusters, self.msg.to_clusters ) )
              self.logger.warning("skipped : not for remote cluster...")
              return False

        if self.destination[:3] == 'ftp' :
            # 'i' cannot be supported by ftp/ftps
            # we cannot offset in the remote file to inject data
            #
            # FIXME instead of dropping the message
            # the inplace part could be delivered as 
            # a separate partfile and message set to 'p'
            if  self.msg.partflg == 'i':
                logger.error("ftp, inplace part file not supported")
                if self.reportback:
                   msg.report_publish(499,'ftp cannot deliver partitioned files')
                return False

        self.remote_file = self.new_file #FIXME: remove in 2018

        # invoke user defined on_message when provided

        for plugin in self.on_message_list:
            if not plugin(self): return False

            if self.remote_file != self.new_file : #FIXME: remove in 2018
                logger.warning("on_message plugin should be updated: replace self.msg.remote_file, by self.msg.new_file")
                self.new_file = self.remote_file 

        return True

    # =============
    # __on_post__ posting of message
    # =============

    def __on_post__(self):

        # invoke on_post when provided

        for plugin in self.on_post_list:
            if not plugin(self): return False

        ok = self.msg.publish( )

        return ok

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

    # =============
    # process message  
    # =============

    def process_message(self):

        self.logger.debug("Accepting to send %s '%s' %s" % (self.msg.topic,self.msg.notice,self.msg.hdrstr))

        #=================================
        # setting up message with sr_sender config options
        # self.set_local  : setting local info for the file/part
        # self.set_new : setting remote server info for the file/part
        #=================================

        self.set_local()
        self.set_new()
        self.set_new_url()

        #=================================
        # now message is complete : invoke __on_message__
        #=================================

        ok = self.__on_message__()
        if not ok : return ok

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
           self.msg.set_topic_url('v02.post',self.new_url)
           self.msg.set_notice(self.new_url,self.msg.time)
           self.__on_post__()
           if self.reportback:
               self.msg.report_publish(201,'Published')

        return True

    def run(self):

        # present basic config

        self.logger.info("sr_sender run")

        # loop/process messages

        self.connect()

        if self.restore and os.path.exists(self.save_path):
           rtot=0
           with open(self.save_path,"r") as rf:
               for ml in rf:
                   rtot += 1

           self.logger.info("sr_sender restoring %d messages from save %s " % ( rtot, self.save_path ) )
           rnow=0

           with open(self.save_path,"r") as rf:
               for ml in rf:
                  rnow += 1
                  self.msg.exchange = 'save'
                  self.msg.topic, self.msg.headers, self.msg.notice = json.loads(ml)
                  self.msg.from_amqplib()
                  self.logger.info("sr_sender restoring message %d of %d: topic: %s" % (rnow, rtot, self.msg.topic) )
                  ok = self.process_message()

           if rnow >= rtot:
               self.logger.info("sr_sender restore complete deleting save file: %s " % ( self.save_path ) )
               os.unlink(self.save_path) 
           else:
               self.logger.error("sr_sender only restored %d of %d messages from save file: %s " % ( rnow, rtot, self.save_path ) )

        if self.save :
            self.logger.info("sr_sender saving to %s for future restore" % self.save_path )
            sf = open(self.save_path,"a")
            stot=0

        active = self.has_vip()
        if not active :
            self.logger.debug("sr_sender does not have vip=%s, is sleeping" % self.vip)
        else:
            self.logger.debug("sr_sender is active on vip=%s" % self.vip)


        while True :
            try:

                  if not self.has_vip() : #  is it sleeping ?
                      if active:
                          self.logger.debug("sr_sender does not have vip=%s, is sleeping" % self.vip)
                          active=False
     
                      time.sleep(5)
                      continue
                  else:
                     if not active:
                         self.logger.debug("sr_sender is active on vip=%s" % self.vip)
                         active=True

                  #  consume message
                  ok, self.msg = self.consumer.consume()
                  if not ok : continue

                  if self.save :
                      stot += 1
                      self.logger.info("sr_sender saving %d message topic: %s" % ( stot, self.msg.topic ) )
                      sf.write(json.dumps( [ self.msg.topic, self.msg.headers, self.msg.notice ], sort_keys=True ) + '\n' )   
                      sf.flush()
                  else:
                      #  process message (ok or not... go to the next)
                      ok = self.process_message()

            except:
                  (stype, svalue, tb) = sys.exc_info()
                  self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))

        if self.save:
            sf.close()

    def set_local(self):

        self.local_root  = ''
        self.local_rpath = ''

        path  = '%s' % self.msg.path
        token = path.split('/')

        if self.document_root != None : self.local_root  = self.document_root
        if len(token) > 1             : self.local_rpath = '/'.join(token[:-1])
        self.filename = token[-1]


        # Local directory (directory created if needed)

        self.local_dir    = self.local_root + '/' + self.local_rpath
        self.local_dir    = self.local_dir.replace('//','/')
        self.local_file   = self.filename

        self.local_path   = self.local_dir   + '/' + self.filename

        self.local_offset = self.msg.offset
        self.local_length = self.msg.length


    def set_new(self):

        self.new_root  = ''
        if self.post_document_root != None : self.new_root = self.post_document_root

        # mirror case by default

        self.new_rpath = self.local_rpath
        self.new_file  = self.local_file
       

        if self.strip > 0 :
           token = self.new_rpath.split('/')
           self.new_rpath = '/'.join(token[self.strip:])

        # no mirror and no directory ...
        if not self.mirror and self.currentDir == None :
           self.logger.warning("no mirroring and directory unset : assumed None ")
           self.new_rpath = ''

        # a target directory was provided
        if self.use_pattern and self.currentDir != None:
           self.new_rpath = self.currentDir

        # PDS like destination pattern/keywords

        if self.currentFileOption != None :
           self.new_file = self.sundew_getDestInfos(self.local_file)

        if self.destfn_script :
            last_new_file = self.new_file
            ok = self.destfn_script(self)
            if last_new_file != self.new_file :
               self.logger.debug("destfn_script : %s becomes %s "  % (last_new_file,self.new_file) )

        destDir = self.new_rpath
        destDir = self.sundew_dirPattern(self.msg.urlstr,self.local_file,destDir,self.new_file)

        self.new_rpath = destDir

        # build dir/path and url from options

        self.new_dir  = self.new_root + '/' + self.new_rpath
        #self.new_path = self.new_dir  + '/' + self.new_file

    def set_new_url(self):

        self.new_urlstr    = self.destination
        if self.url != None :
           self.new_urlstr = self.url.geturl()

        if self.new_urlstr[-1] != '/' : self.new_urlstr += '/'

        if self.new_rpath != '' and self.new_rpath[0] == '/':
           self.pnew_rpath = self.new_rpath[1:]

        if not self.post_document_root and 'ftp' in self.new_urlstr[:4] : self.new_urlstr += '/'

        self.new_urlstr += self.new_rpath + '/' + self.new_file
        self.new_url     = urllib.parse.urlparse(self.new_urlstr)

    def reload(self):
        self.logger.info("%s reload" % self.program_name)
        self.close()
        self.configure()
        self.run()

    def start(self):
        self.logger.info("%s %s start" % (self.program_name, sarra.__version__) )
        self.run()

    def stop(self):
        self.logger.info("%s stop" % self.program_name)
        self.close()
        os._exit(0)

# ===================================
# MAIN
# ===================================

def main():

    action = None
    args   = None
    config = None

    if len(sys.argv) >= 2 : 
       action = sys.argv[-1]

    if len(sys.argv) >= 3 : 
       config = sys.argv[-2]
       args   = sys.argv[1:-2]

    sender = sr_sender(config,args)

    if   action == 'foreground' : sender.foreground_parent()
    elif action == 'reload'     : sender.reload_parent()
    elif action == 'restart'    : sender.restart_parent()
    elif action == 'start'      : sender.start_parent()
    elif action == 'stop'       : sender.stop_parent()
    elif action == 'status'     : sender.status_parent()
    else :
           sender.logger.error("action unknown %s" % action)
           sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
