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
# sr_subscribe.py : python3 program allowing users to download product from dd.weather.gc.ca
#                   as soon as they are made available (through amqp notifications)
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Jun Hu         - Shared Services Canada
#  Last Changed   : Dec 17 09:23:05 EST 2015
#  Last Changed   : Tue Sep 26 17:30 UTC 2017
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

#============================================================
# usage example
#
# sr_subscribe [options] [config] [foreground|start|stop|restart|reload|status|cleanup|setup]
#
#============================================================

import json,os,sys,time

try :    
         from sr_cache           import *
         from sr_consumer        import *
         from sr_file            import *
         from sr_ftp             import *
         from sr_http            import *
         from sr_instances       import *
         from sr_message         import *
         from sr_util            import *
except : 
         from sarra.sr_cache     import *
         from sarra.sr_consumer  import *
         from sarra.sr_file      import *
         from sarra.sr_ftp       import *
         from sarra.sr_http      import *
         from sarra.sr_instances import *
         from sarra.sr_message   import *
         from sarra.sr_util      import *

class sr_subscribe(sr_instances):

    def __init__(self,config=None,args=None,action=None):
        sr_instances.__init__(self,config,args,action)

    def check(self):
        self.logger.debug("%s check" % self.program_name)

        # if no subtopic given... make it #  for all
        if self.bindings == []  :
           key = self.topic_prefix + '.#'
           self.bindings.append( (self.exchange,key) )
           self.logger.debug("*** BINDINGS %s"% self.bindings)

        # pattern must be used
        # if unset we will accept unmatched... so everything

        self.use_pattern          = True
        self.accept_unmatch       = self.masks == []

        # verify post_base_dir

        if self.post_base_dir == None :
           if self.post_document_root != None :
              self.post_base_dir = self.post_document_root
              self.logger.warning("use post_base_dir instead of post_document_root")
           elif self.document_root != None :
              self.post_base_dir = self.document_root
              self.logger.warning("use post_base_dir instead of document_root")

        # impacting other settings

        if self.discard:
           self.inplace    = False
           self.overwrite  = True

        # caching

        if self.caching :
           self.cache      = sr_cache(self)
           self.cache_stat = True
           self.cache.open()
           self.execfile("on_heartbeat",'heartbeat_cache')
           self.on_heartbeat_list.append(self.on_heartbeat)

        # reporting

        if self.reportback :
           self.report_exchange = 'xs_' + self.broker.username

        # do_task should have doit_download for now... make it a plugin later
        # and the download is the first thing that should be done

        if not self.doit_download in self.do_task_list :
           self.do_task_list.insert(0,self.doit_download)

    def close(self):
        self.consumer.close()

        if self.post_broker :
           if self.post_broker != self.broker : self.post_hc.close()

        if self.save_fp: self.save_fp.close()

        if hasattr(self,'ftp_link') : self.ftp_link.close()
        if hasattr(self,'http_link'): self.http_link.close()
        if hasattr(self,'sftp_link'): self.sftp_link.close()

        if self.cache :
           self.cache.save()
           self.cache.close()

    def connect(self):

        # =============
        # create message if needed
        # =============

        self.msg = sr_message(self)

        # =============
        # consumer  queue_name : let consumer takes care of it
        # =============

        self.consumer = sr_consumer(self)

        self.logger.info("reading from to %s@%s, exchange: %s" % \
                        ( self.broker.username, self.broker.hostname, self.exchange ) )

        # =============
        # report_publisher
        # =============

        if self.reportback :

           self.report_publisher     = self.consumer.publish_back()
           self.msg.report_publisher = self.report_publisher
           self.msg.report_exchange  = self.report_exchange

           self.logger.info("report_back to %s@%s, exchange: %s" % 
               ( self.broker.username, self.broker.hostname, self.msg.report_exchange ) )

        else:
           self.logger.info("report_back suppressed")


        # =============
        # in save mode...
        # =============

        if self.save :
           self.logger.warning("running in save mode")
           self.post_broker        = None
           self.consumer.save      = True
           self.consumer.save_path = self.save_path

           if self.save_file  :
              self.save_path = self.save_file + self.save_path[-10:]
              self.consumer.save_path = self.save_path

           self.save_fp       = open(self.save_path,"a")
           self.save_count    = 1
           return

        # =============
        # publisher : if self.post_broker exists
        # =============

        if self.post_broker :

           # publisher host

           self.post_hc = self.consumer.hc
           if self.post_broker != self.broker :
              self.post_hc = HostConnect( logger = self.logger )
              self.post_hc.set_pika( self.use_pika )
              self.post_hc.set_url( self.post_broker )
              self.post_hc.connect()

              self.msg.user = self.post_broker.username

           self.logger.info("Output AMQP broker(%s) user(%s) vhost(%s)" % \
                           (self.post_broker.hostname,self.post_broker.username,self.post_broker.path) )


           # publisher

           self.publisher = Publisher(self.post_hc)
           self.publisher.build()
           self.msg.publisher = self.publisher
           if self.post_exchange :
              self.msg.pub_exchange = self.post_exchange
           self.msg.post_exchange_split = self.post_exchange_split
           self.logger.info("Output AMQP exchange(%s)" % self.post_exchange )

           # amqp resources

           self.declare_exchanges()


    def __do_download__(self):

        self.logger.debug("downloading/copying %s (scheme: %s) into %s " % \
                         (self.msg.urlstr, self.msg.url.scheme, self.new_file))

        try :
                if   self.msg.url.scheme == 'http' :
                     if not hasattr(self,'http_link') :
                        self.http_link = http_transport()
                     return self.http_link.download(self)

                elif self.msg.url.scheme == 'ftp' :
                     if not hasattr(self,'ftp_link') :
                        self.ftp_link = ftp_transport()
                     return self.ftp_link.download(self)

                elif self.msg.url.scheme == 'sftp' :
                     try    : from sr_sftp       import sftp_transport
                     except : from sarra.sr_sftp import sftp_transport
                     if not hasattr(self,'sftp_link') :
                        self.sftp_link = sftp_transport()
                     return self.sftp_link.download(self)

                elif self.msg.url.scheme == 'file' :
                     return file_process(self)

                # user defined download scripts

                elif self.do_download :
                     return self.do_download(self)

        except :
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Download  Type: %s, Value: %s,  ..." % (stype, svalue))
                if self.reportback: 
                   self.msg.report_publish(503,"Unable to process")
                self.logger.error("%s: Could not download" % self.program_name)

        if self.reportback: 
            self.msg.report_publish(503,"Service unavailable %s" % self.msg.url.scheme)

    # =============
    # __do_tasks__ (download, or send, or convert)
    # =============

    def __do_tasks__(self):
        self.logger.debug("%s __do_tasks__" % self.program_name)

        # invoke on_post when provided

        for plugin in self.do_task_list:
           if not plugin(self): return False

        return True

    # =============
    # get_source_from_exchange
    # =============

    def get_source_from_exchange(self,exchange):
        self.logger.debug("%s get_source_from_exchange %s" % (self.program_name,exchange))

        source = None
        if len(exchange) < 4 or not exchange.startswith('xs_') : return source

        # check if source is a valid declared source user

        len_u   = 0
        try:
                # look for user with role source
                for u in self.users :
                    if self.users[u] != 'source' : continue
                    if exchange[3:].startswith(u) and len(u) > len_u :
                       source = u
                       len_u  = len(u)
        except: pass

        return source

    def help(self):

        # ---------------------------
        # general startup and version
        # ---------------------------

        print("\nUsage: %s [OPTIONS] [foreground|start|stop|restart|reload|status|cleanup|setup] configfile\n" % self.program_name )
        print("version: %s \n" % sarra.__version__ )

        # ---------------------------
        # program's purpose
        # ---------------------------

        if self.program_name == 'sr_sarra' :
           print("\n%s: Subscribe to download, and Recursively Re-Announce(implements a sarracenia pump)\n"\
                    % self.program_name)
           print("\nminimal configuration includes :")
           print("broker, exchange, post_broker, [post_exchange (defaults to exchange)]\n")

        if self.program_name == 'sr_winnow' :
           print("\n%s: read messages from exchange and post them(post_exchange), suppressing duplicates\n"\
                    % self.program_name)
           print("\nminimal configuration includes :")
           print("broker, exchange, [post_broker (defaults to broker)], post_exchange\n")

        if self.program_name == 'sr_shovel' :
           print("\n%s: read messages from exchange and post them on another broker using post_exchange\n"\
                    % self.program_name)
           print("\nminimal configuration includes :")
           print("broker, exchange, post_broker, [post_exchange (defaults to exchange)]\n")

        if self.program_name == 'sr_subscribe' :
           print("\n%s: Connect to an AMQP broker, subscribe to file announcements, do timely downloads\n"\
                    % self.program_name)
           print("\nminimal configuration :")
           print("sr_subscribe start ./aaa")
           print("\t\twhere aaa is an empty file: downloads announced files on dd.weather in cwd\n")

           print("\nExamples:\n")    

           print("%s subscribe.conf start # download files and display log in stdout" % self.program_name)
           print("%s -d subscribe.conf start # discard files after downloaded and display log in stout" % self.program_name)
           print("%s -l /tmp subscribe.conf start # download files,write log file in directory /tmp" % self.program_name)
           print("%s -n subscribe.conf start # get notice only, no file downloaded and display log in stout" % self.program_name)
           print("subscribe.conf file settings, MANDATORY ones must be set for a valid configuration:")
           print("\t\t(default: amqp://anonymous:anonymous@dd.weather.gc.ca/ )")

        # ---------------------------
        # option presentations
        # ---------------------------

        print("OPTIONS:")

        # ---------------------------
        # instances
        # ---------------------------

        if self.program_name != 'sr_winnow' :
           print("\ninstances <nb_of_instances>      default 1")

        # ---------------------------
        # consumer broker
        # ---------------------------

        print("\nAMQP consumer broker settings:")
        print("\tbroker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>   (MANDATORY)")

        if self.program_name == 'sr_subscribe':
           print("\t\t(default: amqp://anonymous:anonymous@dd.weather.gc.ca/ )")

        # ---------------------------
        # queue bindings
        # ---------------------------

        print("\nAMQP Queue bindings:")

        if self.program_name == 'sr_subscribe':
          print("\texchange             <name>          (default: xpublic)")
        else :
          print("\texchange             <name>          (MANDATORY)")

        print("\ttopic_prefix         <amqp pattern>  (default: v02.post)")
        print("\tsubtopic             <amqp pattern>  (default: #)")
        print("\t\t  <amqp pattern> = <directory>.<directory>.<directory>...")
        print("\t\t\t* single directory wildcard (matches one directory)")
        print("\t\t\t# wildcard (matches rest)")

        # ---------------------------
        # queue settings
        # ---------------------------

        print("\nAMQP Queue settings:")
        print("\tqueue_name    <name>         (default: program set it for you)\n")
        print("\tdurable              <boolean>       (default: False)")
        print("\texpire               <minutes>       (default: None)")
        print("\tmessage-ttl          <minutes>       (default: None)")

        # ---------------------------
        # message filtering
        # ---------------------------

        print("\nMessage targeted (filtering):")

        if self.program_name in ['sr_sarra','sr_subscribe']:
           print("\tdirectory <path>     target directory (post_base_dir/directory/\"file settings\"")
           print("\t * accept/reject following a directory option determine what is placed under it")
           print("\t\t(default currentdir/\"file settings\"")

        print("\taccept    <regexp pattern>           (default: None)")
        print("\treject    <regexp pattern>           (default: None)")
        print("\taccept_unmatch   <boolean> if no match for all accept/reject opt, accept message? (default: no).\n")
        print("\tevents    <event list>  msg events processed (default:create|delete|follow|link|modify)")
        print("\ton_message           <script>        (default None)")

        # ---------------------------
        # file download settings
        # ---------------------------

        if self.program_name in ['sr_sarra','sr_subscribe'] :
           print("\nFile download settings:")
           print("\tinplace              <boolean>       (default False)")
           print("\toverwrite            <boolean>       (default False)")
           print("\tflatten   <string>   filename= message relpath replacing '/' by *flatten*(default:'/')")
           print("\tinflight  <.string>  suffix (or prefix) on filename during downloads (default: .tmp)\n")
           print("\tmirror    <boolean>  same directory tree as message relpath or flat. (default: True)")
           print("\tstrip     <count>    nb. of directories to remove from message relpath. (default: 0)")
           print("\tbase_dir             <base_dir>      (if file is local and msg_2localfile.py is used)")
           print("\tdo_download          <script>        (default None)")
           print("\ton_file              <script>        (default None)")
           print("\n\tif the download of the url received in the amqp message needs credentials")
           print("\tyou defines the credentials in the $HOME/.config/sarra/credentials.conf")
           print("\tone url per line. as an example, the file could contain:")
           print("\thttp://myhttpuser:myhttppassword@apachehost.com/")
           print("\tftp://myftpuser:myftppassword@ftpserver.org/")
           print("\tetc...")

        # ---------------------------
        # message posting
        # ---------------------------

        print("\nAMQP posting settings:")
        print("\tpost_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>")

        if self.program_name == 'sr_sarra' :
           print("\t\t(default: manager amqp broker in default.conf)")
           print("\tpost_exchange        <name>          (default xpublic)")
        else :
           print("\tpost_exchange        <name>          (MANDATORY)")

        print("\tpost_base_dir        <name>          (default None)")
        print("\tpost_base_url        <url>      post message: base_url         (MANDATORY)")
        print("\trecompute_chksum     <boolean>  post message: reset checksum   (default False)")
        if self.program_name == 'sr_sarra' :
           print("\tsource_from_exchange <boolean>  post message: reset headers[source] (default False)")
        print("\ton_post              <script>        (default None)")

        # ---------------------------
        # report posting
        # ---------------------------

        print("\nAMQP reporting to broker:")
        if self.program_name == 'sr_sarra':
           print("\treportback              <boolean>       (default: true)")
        else :
           print("\treportback              <boolean>       (default: false)")

        print("\treport_exchange         <name>          (default: xreport)")

        # ---------------------------
        # debugging
        # ---------------------------

        print("\nDEBUG:")
        print("\t-debug")

    # =============
    # __on_file__
    # =============

    def __on_file__(self):
        self.logger.debug("%s __on_file__" % self.program_name)

        # keep current value of these variables

        val_new_dir     = self.new_dir
        val_new_file    = self.new_file
        val_new_baseurl = self.new_baseurl
        val_new_relpath = self.new_relpath

        for plugin in self.on_file_list :

           # invoke user defined on_file when provided

           self.local_file = self.new_dir + '/' + self.new_file  # FIXME: remove in 2018, once all plugins are converted.
           self.msg.local_file = self.local_file
           saved_file = self.local_file

           self.local_dir = self.new_dir     # FIXME: remove in 2018, once all plugins are converted.
           self.msg.local_dir = self.new_dir
           saved_dir = self.new_dir

           # sender
           self.remote_file = self.new_file #FIXME: remove in 2018

           if not plugin(self): return False

           if self.msg.local_file != saved_file :
              self.logger.warning("on_file plugins 2 should replace parent.msg.local_file, by parent.new_dir and parent.new_file" )
              self.new_file = os.path.basename(self.msg.local_file)
              self.new_dir  = os.path.dirname( self.msg.local_file)

           if self.msg.local_dir != saved_dir :
              self.logger.warning("on_file plugins 2 should replace parent.msg.local_dir, by parent.new_dir" )
              self.logger.warning("parent.msg.local_dir=%s, by parent.new_dir=%s" % (self.msg.local_dir, self.new_dir) )
              self.new_dir = self.msg.local_dir

           # sender
           if self.remote_file != self.new_file : #FIXME: remove in 2018
              logger.warning("on_file plugin should be updated: replace parent.remote_file, by parent.new_file")
              self.new_file = self.remote_file

           # this code should not be removed ... necessary when the plugin changed something
           # if differences with new_dir and/or new_file...
           # reset new_relpath if it stayed the same

           if self.new_dir != val_new_dir or self.new_file != val_new_file :
              if self.new_relpath == val_new_relpath :
                 relpath = self.new_dir + '/' + self.new_file
                 if self.post_base_dir : relpath = relpath.replace(self.post_base_dir,'',1)
                 self.new_relpath = relpath
              # to do it once (per plugin changes)
              val_new_dir     = self.new_dir
              val_new_file    = self.new_file
              val_new_relpath = self.new_relpath

        return True

    # =============
    # __on_message__
    # =============

    def __on_message__(self):

        # keep current value of these variables

        val_new_dir     = self.new_dir
        val_new_file    = self.new_file
        val_new_baseurl = self.new_baseurl
        val_new_relpath = self.new_relpath

        # invoke user defined on_message when provided

        self.local_file = self.new_dir + '/' + self.new_file  # FIXME: remove in 2018, once all plugins are converted.
        self.msg.local_file = self.local_file
        saved_file = self.local_file

        self.local_dir = self.new_dir     # FIXME: remove in 2018, once all plugins are converted.
        self.msg.local_dir = self.new_dir
        saved_dir = self.new_dir

        if not hasattr(self,'new_url') :
           self.new_url = self.new_baseurl + '/' + self.new_relpath  # FIXME: remove  in 2018, new_url replaced by new_baseurl and new_relpath
           self.new_url = urllib.parse.urlparse(self.new_url)
        saved_url    = self.new_url.geturl()

        # sender
        self.remote_file = self.new_file #FIXME: remove in 2018


        for plugin in self.on_message_list :

           if not plugin(self): return False

           if self.msg.local_file != saved_file :
              self.logger.warning("on_message plugins 2 should replace parent.msg.local_file, by parent.new_dir and parent.new_file" )
              self.new_file = os.path.basename(self.local_file)
              self.new_dir  = os.path.dirname( self.local_file)

           if self.msg.local_dir != saved_dir :
              self.logger.warning("on_message plugins 2 should replace parent.msg.local_dir, by parent.new_dir" )
              self.logger.warning("parent.msg.local_dir=%s, by parent.new_dir=%s" % (self.msg.local_dir, self.new_dir) )
              self.new_dir = self.msg.local_dir

           urlstr = self.new_url.geturl()
           if urlstr != saved_url :
              self.logger.warning("on_message plugins 2 should replace self.new_url, by parent.new_baseurl and parent.new_relpath" )
              self.new_relpath = self.new_url.path
              if not self.new_baseurl in urlstr:
                 self.new_baseurl = urlstr.replace(self.new_relpath,'')
               
           # sender
           if self.remote_file != self.new_file : #FIXME: remove in 2018
              logger.warning("on_message plugin should be updated: replace parent.remote_file, by parent.new_file")
              self.new_file = self.remote_file

           # if differences with new_dir/new_file... reset new_relpath

           if self.new_dir != val_new_dir or self.new_file != val_new_file :
              if self.new_relpath == val_new_relpath :
                 relpath = self.new_dir + '/' + self.new_file
                 if self.post_base_dir : relpath = relpath.replace(self.post_base_dir,'',1)
                 self.new_relpath = relpath

        return True


    # =============
    # __on_post__ posting of message
    # =============

    def __on_post__(self):
        self.logger.debug("%s __on_post_" % self.program_name)

        self.msg.local_file = self.new_file # FIXME, remove in 2018

        # invoke on_post when provided

        for plugin in self.on_post_list:
           if not plugin(self): return False
           if ( self.msg.local_file != self.new_file ): # FIXME, remove in 2018
                self.logger.warning("on_post plugins should replace self.msg.local_file, by self.new_file" )
                self.new_file = self.msg.local_file

        ok = self.msg.publish( )

        return ok


    def overwrite_defaults(self):
        self.logger.debug("%s overwrite_defaults" % self.program_name)

        # special settings for sr_subscribe

        self.accept_unmatch = False
        self.broker         = urllib.parse.urlparse("amqp://anonymous:anonymous@dd.weather.gc.ca:5672/")
        self.exchange       = 'xpublic'
        self.inplace        = True
        self.inflight       = '.tmp'
        self.mirror         = False

        self.post_broker    = None
        self.post_exchange  = None

    # =============
    # process message  
    # =============

    def process_message(self):

        self.logger.debug("Received notice  %s %s%s" % tuple(self.msg.notice.split()[0:3]) )

        #=================================
        # complete the message (source,from_cluster,to_clusters)
        #=================================

        # if a message is received directly from a source...
        # we dont trust its settings of  source and from_cluster

        if self.source_from_exchange :
           source = self.get_source_from_exchange(self.msg.exchange)
           if source : self.msg.headers['source'] = source
           else      : del self.msg.headers['source']
           if 'from_cluster' in self.msg.headers : del self.msg.headers['from_cluster']
 
        # apply default to a message without a source
        if not 'source' in self.msg.headers :
           if self.source: self.msg.headers['source'] = self.source
           else          : self.msg.headers['source'] = self.broker.username
           self.logger.debug("message missing header, set default headers['source'] = %s" % self.msg.headers['source'])

        # apply default to a message without an origin cluster
        if not 'from_cluster' in self.msg.headers :
           if self.cluster : self.msg.headers['from_cluster'] = self.cluster
           else            : self.msg.headers['from_cluster'] = self.broker.netloc.split('@')[-1] 
           self.logger.debug("message missing header, set default headers['from_cluster'] = %s" % self.msg.headers['from_cluster'])

        # apply default to a message without routing clusters
        if not 'to_clusters' in self.msg.headers :
           if self.to_clusters  : self.msg.headers['to_clusters'] = self.to_clusters
           elif self.post_broker: self.msg.headers['to_clusters'] = self.post_broker.netloc.split('@')[-1] 
           if 'to_clusters' in self.msg.headers :
              self.logger.debug("message missing header, set default headers['to_clusters'] = %s" % self.msg.headers['to_clusters'])
           else:
              self.logger.warning("message without headers['to_clusters']")

        #=================================
        # setting up message with sr_subscribe config options
        # self.set_new    : how/where sr_subscribe is configured for that product
        # self.msg.set_new: how message settings (like parts) applies in this case
        #=================================

        self.set_new()
        self.msg.set_new()

        #=================================
        # now invoke __on_message__
        #=================================

        ok = self.__on_message__()
        if not ok : return ok

        #=================================
        # if caching is set
        #=================================

        if self.caching :
           new_msg = self.cache.check_msg(self.msg)

           if not new_msg :
              if self.reportback : self.msg.report_publish(304,'Not modified')
              self.logger.info("Ignored %s not modified" % (self.msg.notice))
              return True

        #=================================
        # if notify_only... publish if set
        #=================================

        if self.notify_only :
           if self.post_broker :
              self.logger.debug("notify_only post")
              ok = self.__on_post__()
              if ok and self.reportback : self.msg.report_publish(201,'Published')
           return True

        #=================================
        # do all tasks
        #=================================
        ok = self.__do_tasks__()

        return ok


    #=================================
    # determine a file from a relpath
    #
    # returns None,None,None     if resulting file is rejected (reject/on_message)
    # returns None,None,newrelp  if resulting file is already up to date (newname only)
    # returns dir,file,relpath   of the file determined by the message and argument relpath
    #
    #=================================

    def determine_move_file(self,name,relpath):

        # build a working message from self.msg
        w_msg = sr_message(self)
        w_msg.exchange = self.msg.exchange + ''
        w_msg.notice   = self.msg.notice   + ''
        w_msg.topic    = self.msg.topic    + ''

        w_msg.headers     = self.msg.headers.copy()
        w_msg.add_headers = self.msg.add_headers.copy()
        w_msg.del_headers = self.msg.del_headers.copy()

        # set working message  with relpath info

        w_msg.set_topic ('v02.post', relpath )
        w_msg.set_notice(self.msg.baseurl,relpath,self.msg.time)

        w_msg.parse_v02_post()

        # make use of accept/reject on working message
        if self.use_pattern :

           # Adjust url to account for sundew extension if present, and files do not already include the names.
           if urllib.parse.urlparse(w_msg.urlstr).path.count(":") < 1 and 'sundew_extension' in w_msg.headers.keys() :
              urlstr = w_msg.urlstr + ':' + w_msg.headers[ 'sundew_extension' ]
           else:
              urlstr = w_msg.urlstr

           self.logger.debug("determine_move_file, path being matched: %s " % ( urlstr )  )


           if not self.isMatchingPattern(urlstr,self.accept_unmatch) :
              self.logger.debug("Rejected by accept/reject options")
              return None,None,None

        # get a copy of received message

        saved_msg = self.msg

        # user working message to validate with on_message

        self.msg = w_msg
        self.set_new()
        self.msg.set_new()

        ok = self.__on_message__()
        if not ok : return None,None,None

        # ok what we have found

        #self.logger.debug("W new_dir     = %s" % self.new_dir)
        #self.logger.debug("W new_file    = %s" % self.new_file)
        #self.logger.debug("W new_baseurl = %s" % self.new_baseurl)
        #self.logger.debug("W new_relpath = %s" % self.new_relpath)

        # set the directory of the file we try to determine

        found = True
        try   : os.chdir(self.new_dir)
        except: found = False

        # if it is for 'newname' verify if the files are the same

        if found and name == 'newname' :
    
           if not self.overwrite and self.msg.partstr and self.msg.content_should_not_be_downloaded() :
              if self.reportback : self.msg.report_publish(304,'Not modified')
              self.new_dir  = None
              self.new_file = None

        # if it is for 'oldname' verify if the file exists

        if found and name == 'oldname' :
    
           if not os.path.exists(self.new_file):
              self.logger.debug("move: oldname not found %s" % self.new_file)
              self.new_dir  = None
              self.new_file = None

        # prepare results
        tdir  = self.new_dir
        tfile = self.new_file
        trelp = self.new_relpath

        # restore original message and settings

        self.msg = saved_msg
        self.set_new()
        self.msg.set_new()

        ok = self.__on_message__()

        try   : os.chdir(self.new_dir)
        except: pass

        # return results

        return tdir,tfile,trelp

    # =============
    # doit_download
    # =============

    def doit_download(self,parent=None):
        self.logger.debug("%s doit_download" % self.program_name)

        """
        FIXME: 201612-PAS There is perhaps several bug here:
            -- no_download is not consulted. In no_download, mkdir, deletes and links should not happen.
            -- on_file/on_part processing is not invoked for links or deletions, should it?
               do we need on_link? on_delete? ugh...
            
        """

        need_download = True

        #=================================
        # move event: case 1
        # sum has 'R,' and  self.msg.headers['newname'] provided
        # Try to move oldfile from notice to newfile from headers['newname']
        # If the move is performed or not, we continue in the module because
        # the 'R,' meaning delete old file will be performed next
        # and the move message will be (corrected and) propagated that way
        #=================================

        newname = None
        if 'newname' in self.msg.headers :
           newname = self.msg.headers

           # it means that the message notice contains info about oldpath
           oldpath = self.new_dir + '/' + self.new_file

           # we can do something if the oldpath exists
           if os.path.exists(oldpath) : 

              # determine the 'move to' file (accept/reject ok and on_message ok)
              newdir,newfile,newrelp = self.determine_move_file('newname',self.msg.headers['newname'])
              if newrelp != None : newname = newrelp

              if newfile != None :
                 newpath = newdir + '/' + newfile

                 # only if the newpath doesnt exist
                 if not os.path.exists(newpath):

                    # make sure directory exists, create it if not
                    if not os.path.isdir(newdir):
                       try   : os.makedirs(newdir,0o775,True)
                       except: pass
                       #MG FIXME : except: return False  maybe ?

                    # move
                    try   : 
                            # file link
                            if os.path.isfile(oldpath) or os.path.islink(oldpath) :
                               os.link(oldpath,newpath)
                               self.logger.info("move %s to %s (hardlink)" % (oldpath,newpath))
                            # dir rename
                            if os.path.isdir( oldpath) : 
                               os.rename(oldpath,newpath)
                               self.logger.info("move %s to %s (rename)" % (oldpath,newpath))
                            if self.reportback: self.msg.report_publish(201, 'moved')
                            need_download = False
                    except: pass
                    #MG FIXME : except: return False  maybe ?

                 # if the newpath exists log a message in debug only
                 else : 
                    self.logger.debug("could not move %s to %s (file exists)" % (oldpath,newpath))

        #=================================
        # move event: case 2
        # self.msg.headers['oldname'] provided
        # Try to move oldfile from headers['oldname'] to newfile from notice
        # If the move is performed we are done (post and) return True
        # If it doesnt work, continue and the file will be downloaded normally
        #=================================

        oldname = None
        if 'oldname' in self.msg.headers :
           oldname = self.msg.headers

           # set 'move to' file
           newpath = self.new_dir + '/' + self.new_file

           # determine oldfile infos 

           olddir,oldfile,oldrelp = self.determine_move_file('oldname',self.msg.headers['oldname'])
           if oldrelp != None : oldname = oldrelp

           if oldfile != None :
              oldpath = olddir + '/' + oldfile

              # oldfile exists: try to link it to newfile
              # if it doesnt work... pass... the newfile will be downloaded

              if os.path.exists(oldpath) : 

                 if not os.path.isdir(self.new_dir):
                    try   : os.makedirs(self.new_dir,0o775,True)
                    except: pass
                    #MG FIXME : except: return False  maybe ?

                 # move
                 ok = True
                 try   : 
                         if os.path.isfile(oldpath) or os.path.islink(oldpath) :
                            os.link(oldpath,newpath)
                            self.logger.info("move %s to %s (hardlink)" % (oldpath,newpath))
                         if os.path.isdir( oldpath) : 
                            os.rename(oldpath,newpath)
                            self.logger.info("move %s to %s (rename)" % (oldpath,newpath))
                         need_download = False
                 except: ok = False

                 if ok  :
                          need_download = False
                          if self.reportback: self.msg.report_publish(201, 'moved')

                          if self.post_broker :
                             self.msg.set_topic('v02.post',self.new_relpath)
                             self.msg.set_notice(self.new_baseurl,self.new_relpath,self.msg.time)
                             self.msg.headers['oldname'] = oldname
                             ok = self.__on_post__()
                             if ok and self.reportback : self.msg.report_publish(201,'Published')
                          return True

                 self.logger.debug("could not move %s to %s (hardlink)" % (oldpath,newpath))
                 self.logger.debug("newfile will be downloaded" % newpath)

        #=================================
        # delete event, try to delete the local product given by message
        #=================================

        if self.msg.sumflg.startswith('R') : 

           self.logger.debug("message is to remove %s" % self.new_file)

           if not 'delete' in self.events and not 'newname' in self.msg.headers : 
              self.logger.info("message to remove %s ignored (events setting)" % self.new_file)
              return True

           try : 
               path = self.new_dir + os.sep + self.new_file

               if os.path.isfile(path) : os.unlink(path)
               if os.path.islink(path) : os.unlink(path)
               if os.path.isdir (path) : os.rmdir (path)
               self.logger.debug("%s removed" % self.new_file)
               if self.reportback: self.msg.report_publish(201, 'removed')
           except:
               self.logger.error("remove %s failed." % self.new_file )
               if self.reportback: self.msg.report_publish(500, 'remove failed')

           if self.post_broker :
              self.msg.set_topic('v02.post',self.new_relpath)
              self.msg.set_notice(self.new_baseurl,self.new_relpath,self.msg.time)
              if 'newname' in self.msg.headers : self.msg.headers['newname'] = newname
              ok = self.__on_post__()
              if ok and self.reportback : self.msg.report_publish(201,'Published')

           return True

        #=================================
        # link event, try to link the local product given by message
        #=================================

        if self.msg.sumflg.startswith('L') :
           self.logger.debug("message is to link %s to %s" % ( self.new_file, self.msg.headers[ 'link' ] ) )
           if not 'link' in self.events: 
              self.logger.info("message to link %s to %s ignored (events setting)" %  \
                                            ( self.new_file, self.msg.headers[ 'link' ] ) )
              return True

           if not os.path.isdir(self.new_dir):
              try   : os.makedirs(self.new_dir,0o775,True)
              except: pass

           ok = True
           try : 
               path = self.new_dir + os.sep + self.new_file

               if os.path.isfile(path) : os.unlink(path)
               if os.path.islink(path) : os.unlink(path)
               if os.path.isdir (path) : os.rmdir (path)
               os.symlink( self.msg.headers[ 'link' ], path )
               self.logger.debug("%s linked to %s " % (self.new_file, self.msg.headers[ 'link' ]) )
               if self.reportback: self.msg.report_publish(201,'linked')
           except:
               ok = False
               self.logger.error("symlink of %s %s failed." % (self.new_file, self.msg.headers[ 'link' ]) )
               if self.reportback: self.msg.report_publish(500, 'symlink failed')

           if ok and self.post_broker :
              self.msg.set_topic('v02.post',self.new_relpath)
              self.msg.set_notice(self.new_baseurl,self.new_relpath,self.msg.time)
              ok = self.__on_post__()
              if ok and self.reportback : self.msg.report_publish(201,'Published')

           return True

        #=================================
        # prepare download 
        # the post_base_dir should exists : it the starting point of the downloads
        # make sure local directory where the file will be downloaded exists
        #=================================
        # Caveat, where the local directory has sundew substitutions, it is normal for 
        # that directory not to exist ( e.g. /home/peter/test/dd/{RYYYY} )
        # FIXME: should we remove the substitutions and check the root of the root?
        #=================================

        if self.post_base_dir and not '{' in self.post_base_dir :
           if not os.path.isdir(self.post_base_dir) :
              self.logger.error("directory %s does not exist" % self.post_base_dir)
              return False

        # pass no warning it may already exists
        try    : os.makedirs(self.new_dir,0o775,True)
        except : pass

        #=================================
        # overwrite False, user asked that if the announced file already exists,
        # verify checksum to avoid an unnecessary download
        #=================================

        if not self.overwrite and self.msg.content_should_not_be_downloaded() :
           if self.reportback: self.msg.report_publish(304, 'not modified')
           self.logger.debug("file not modified %s " % self.new_file)

           # if we are processing an entire file... we are done
           if self.msg.partflg == '1' :  return False

           need_download = False

        #=================================
        # attempt downloads
        #=================================

        if need_download :

           # make x attempts to download
           i  = 0
           while i < self.attempts : 
                 ok = self.__do_download__()
                 if ok : break
                 i = i + 1
           # could not download
           if not ok : return False

           # after download we dont propagate renaming... once used get rid of it
           if 'rename'  in self.msg.headers : del self.msg.headers['rename']

           # after download : setting of sum for 'z' flag ...

           if len(self.msg.sumflg) > 2 and self.msg.sumflg[:2] == 'z,':
              self.msg.set_sum(self.msg.checksum,self.msg.onfly_checksum)
              if self.reportback: self.msg.report_publish(205,'Reset Content : checksum')

           # onfly checksum is different from the message ???
           if not self.msg.onfly_checksum == self.msg.checksum :
              self.logger.warning("onfly_checksum %s differ from message %s" %
                                 (self.msg.onfly_checksum, self.msg.checksum))

              # force onfly checksum  in message

              if self.recompute_chksum :
                 #self.msg.compute_local_checksum()
                 self.msg.set_sum(self.msg.sumflg,self.msg.onfly_checksum)
                 if self.reportback: self.msg.report_publish(205,'Reset Content : checksum')


           # if the part should have been inplace... but could not

           if self.inplace and self.msg.in_partfile :
              if self.reportback: self.msg.report_publish(307,'Temporary Redirect')

           # got it : call on_part (for all parts, a file being consider
           # a 1 part product... we run on_part in all cases)

           self.msg.local_file = self.new_file # FIXME: remove in 2018
           saved_file = self.new_file

           self.msg.local_dir = self.new_dir # FIXME: remove in 2018
           saved_dir = self.new_dir

           for plugin in self.on_part_list :

              if not plugin(self): return False

              if ( self.msg.local_file != saved_file ): # FIXME: remove in 2018
                 self.logger.warning("on_part plugins 1 should replace parent.msg.local_file, by parent.new_file" )
                 self.new_file = self.msg.local_file

              if ( self.msg.local_dir != saved_dir ): # FIXME: remove in 2018
                 self.logger.warning("on_part plugins 1 should replace parent.msg.local_dir, by parent.new_dir" )
                 self.new_dir = self.msg.local_dir

           # running on_file : if it is a file, or 
           # it is a part and we are not running "inplace" (discard True)
           # or we are running in place and it is the last part.

           if self.on_file_list :
              """
                 *** FIXME ***: When reassembled, lastchunk is inserted last and therefore
                 calling on_file on lastchunk is accurate... Here, the lastchunk was inserted
                 directly into the target file... The decision of directly inserting the part
                 into the file is based on the file'size being bigger or equal to part's offset.
                 It may be the case that we were at the point of inserting the last chunk...
                 BUT IT IS POSSIBLE THAT,WHEN OVERWRITING A FILE WITH PARTS BEING SENT IN PARALLEL,
                 THE PROGRAM INSERTS THE LASTCHUNK BEFORE THE END OF COLLECTING THE FILE'PARTS...
                 HENCE AN INAPPROPRIATE CALL TO on_file ... 

                 2016/12 FIXME:  I do not understand the (not self.inplace) clause... if it is a part file
                  if it handled by on_part above, if it is the last part, it is called by reassembly below
                  do not understand why calling on this condition.

                  If think this will be called for every partition file, which I think is wrong.

              """

              if (self.msg.partflg == '1') or  \
                       (self.msg.partflg != '1' and ( \
                             (not self.inplace) or \
                             (self.inplace and (self.msg.lastchunk and not self.msg.in_partfile)))):

                 if not self.__on_file__(): return False

                 #for plugin in self.on_file_list:
                 #    if not plugin(self): return False

                 #    if ( self.msg.local_file != self.new_file ): # FIXME remove in 2018
                 #       self.logger.warning("on_file plugins should replace parent.msg.local_file, by parent.new_file" )
                 #       self.new_file = self.msg.local_file

           # discard option

           if self.discard :
              try    :
                        os.unlink(self.new_file)
                        self.logger.debug("Discarded  %s" % self.new_file)
              except :
                        (stype, svalue, tb) = sys.exc_info()
                        self.logger.error("Could not discard  Type: %s, Value: %s,  ..." % (stype, svalue))
              return False


        #=================================
        # publish our download
        #=================================

        if self.msg.partflg != '1' :
           if self.inplace : self.msg.change_partflg('i')
           else            : self.msg.change_partflg('p')

        if self.post_broker :
           self.msg.set_topic('v02.post',self.new_relpath)
           self.msg.set_notice(self.new_baseurl,self.new_relpath,self.msg.time)
           if 'oldname' in self.msg.headers : self.msg.headers['oldname'] = oldname
           ok = self.__on_post__()
           if ok and self.reportback: self.msg.report_publish(201,'Published')

        #=================================
        # if we processed a file we are done
        #=================================

        if self.msg.partflg == '1' : return True

        #=================================
        # if we processed a part (downloaded or not)
        # it can make a difference for parts that wait reassembly
        #=================================
   
        if self.inplace : file_reassemble(self)

        """
        FIXME: 2016/10 - PAS: suspect a bug: pretty sure on_file plugin should run after reassembly complete.
                         2016/12 - ok I get it: on_file is called in the inplace case above.
                                   for the parts case, it is called from reassemble correctly.
                                  
        FIXME: 2016/10 - PAS: suspect a bug: pretty sure discard should run after reassembly complete.
                    2016/12 - well maybe not, if it is discarding parts, it is probably better... hmm..
        """
        return True

    def restore_messages(self):
        self.logger.info("%s restore_messages" % self.program_name)

        # no file to restore
        if not os.path.exists(self.save_path): return

        # not active

        if self.vip  and  not self.has_vip() : return
         
        # restore_queue setup

        if self.restore_queue != None:
           user    = self.broker.username
           config  = self.config_name
           channel = self.post_hc.channel

           # create temporary exchange to publish only to restore_queue.

           self.restore_exchange = 'xs_%s.%s.%s.restore' % (user,self.program_name,config)
           self.msg.pub_exchange =  self.restore_exchange
           self.msg.post_exchange_split = 0
           channel.exchange_declare( self.restore_exchange, 'topic', auto_delete=True, durable=False)
           channel.queue_bind( self.restore_queue, self.restore_exchange, '#' )

        # display restore message count

        total = 0
        with open(self.save_path,"r") as fp :
             for json_line in fp:
                 total += 1

        self.logger.info("%s restoring %d messages from save %s " % (self.program_name,total,self.save_path) )

        # restore each message

        count = 0
        with open(self.save_path,"r") as fp :
             for json_line in fp:

                 count += 1
                 self.msg.exchange = 'save'
                 self.msg.topic, self.msg.headers, self.msg.notice = json.loads(json_line)
                 self.msg.from_amqplib()
                 self.logger.info("%s restoring message %d of %d: topic: %s" %
                                 (self.program_name,  count,total, self.msg.topic) )
                 ok = self.process_message()

        if count >= total:
           self.logger.info("%s restore complete deleting save file: %s " % ( self.program_name, self.save_path ) )
           os.unlink(self.save_path)
        else:
           self.logger.error("%s only restored %d of %d messages from save file: %s " %
                            (self.program_name, count, total, self.save_path ) )

        # only if restoring from a restore_queue : cleanup and exit

        if self.restore_queue != None:
           self.post_hc.channel.queue_unbind( self.restore_queue, self.restore_exchange, '#' )
           self.cleanup()
           os._exit(0)


    def run(self):

        self.logger.info("%s run" % self.program_name)

        # if report_daemons is false than skip 'rr_' config ... cleaning up ressources if any

        if self.config_name and self.config_name[0:3] == 'rr_'  and not self.report_daemons :
           self.logger.info("report_daemons is False, skipping %s config" % self.config_name)
           self.cleanup()
           os._exit(0)

        # reset was asked... so cleanup before connection

        if self.reset : self.cleanup()

        # loop/process messages

        self.connect()

        # restoring messages

        if self.restore or self.restore_queue :
           self.restore_messages()

        # processing messages

        while True :
              try  :
                      # if vip provided, check if has vip

                      if self.vip :
                         #  is it sleeping ?
                         if not self.has_vip() :
                            self.logger.debug("%s does not have vip=%s, is sleeping", \
                                             (self.program_name,self.vip))
                            time.sleep(5)
                            continue
                         else:
                            self.logger.debug("%s is active on vip=%s", (self.program_name,self.vip))


                      #  heartbeat
                      ok = self.heartbeat_check()

                      #  consume message
                      ok, self.msg = self.consumer.consume()
                      if not ok : continue

                      #  in save mode

                      if self.save :
                         self.save_message()
                         continue

                      #  process message (ok or not... go to the next)
                      ok = self.process_message()

              except:
                      (stype, svalue, tb) = sys.exc_info()
                      self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))


    def save_message(self):
        self.logger.info("%s saving %d message topic: %s" % ( self.program_name,self.save_count,self.msg.topic))
        self.save_count += 1
        self.save_fp.write(json.dumps( [ self.msg.topic, self.msg.headers, self.msg.notice ], sort_keys=True ) + '\n' ) 
        self.save_fp.flush()

    def set_dir_pattern(self,cdir):

        new_dir = cdir

        if '${BD}' in cdir and self.base_dir != None :
           new_dir = new_dir.replace('${BD}',self.base_dir)

        if '${PBD}' in cdir and self.post_base_dir != None :
           new_dir = new_dir.replace('${PBD}',self.post_base_dir)

        if '${DR}' in cdir and self.document_root != None :
           self.logger.warning("DR = document_root should be replaced by BD for base_dir")
           new_dir = new_dir.replace('${DR}',self.document_root)

        if '${PDR}' in cdir and self.post_base_dir != None :
           self.logger.warning("PDR = post_document_root should be replaced by PBD for post_base_dir")
           new_dir = new_dir.replace('${PDR}',self.post_base_dir)

        if '${YYYYMMDD}' in cdir :
           YYYYMMDD = time.strftime("%Y%m%d", time.gmtime()) 
           new_dir  = new_dir.replace('${YYYYMMDD}',YYYYMMDD)

        if '${SOURCE}' in cdir :
           new_dir = new_dir.replace('${SOURCE}',self.msg.headers['source'])

        if '${HH}' in cdir :
           HH = time.strftime("%H", time.gmtime()) 
           new_dir = new_dir.replace('${HH}',HH)


        return new_dir


    # ==============================================
    # how will the download file land on this server
    # with all options, this is really tricky
    # ==============================================

    def set_new(self):

        self.logger.debug("set_new strip=%s, mirror=%s flatten=%s pbd=%s msg.relpath=%s" %  \
             ( self.strip, self.mirror, self.flatten, self.post_base_dir, self.msg.relpath ) ) 

        # relative path by default mirror 

        relpath = '%s' % self.msg.relpath

        # case S=0  sr_post -> sr_suscribe... rename in headers
        # FIXME: 255 char limit on headers, rename will break!
        if 'rename' in self.msg.headers : relpath = '%s' % self.msg.headers['rename']

        token    = relpath.split('/')
        filename = token[-1]

        # if provided, strip (integer) ... strip N heading directories
        #         or  pstrip (pattern str) strip regexp pattern from relpath
        # cannot have both (see setting of option strip in sr_config)

        if self.strip > 0 :
           strip = self.strip
           #MG folling code was a fix...
           #   if strip is a number of directories
           #   add 1 to strip not to count '/'
           #   impact to current configs avoided by commenting out

           #if relpath[0] == '/' : strip = strip + 1
           try :
                   token   = token[strip:]

           # strip too much... keep the filename
           except:
                   token   = [filename]

        # strip using a pattern

        elif self.pstrip != None :
           #MG FIXME Peter's wish to have replacement in pstrip (ex.:${SOURCE}...)
           try:    relstrip = re.sub(self.pstrip,'',relpath,1)
           except: relstrip = relpath

           # if filename dissappear... same as numeric strip, keep the filename
           if not filename in relstrip : relstrip = filename
           token = relstrip.split('/')

        # if flatten... we flatten relative path
        # strip taken into account

        if self.flatten != '/' :
           filename  = self.flatten.join(token)
           token[-1] = [filename]

        if self.currentFileOption != None :
           try   :  filename  = self.sundew_getDestInfos(filename)
           except:  self.logger.error("problem with accept file option %s" % self.currentFileOption )
           token[-1] = [filename]

        # not mirroring

        if not self.mirror :
           token = [filename]

        # uses current dir

        new_dir = ''
        if self.currentDir : new_dir = self.currentDir

        # add relpath

        if len(token) > 1 :
           new_dir = new_dir + '/' + '/'.join(token[:-1])

        if '$' in new_dir :
           new_dir = self.set_dir_pattern(new_dir)

        # resolution of sundew's dirPattern

        if 'sundew_extension' in self.msg.headers.keys() :
            tfname  = filename.split(':')[0] + ':' + self.msg.headers[ 'sundew_extension' ]
            new_dir = self.sundew_dirPattern(self.msg.urlstr,tfname,new_dir,filename)


        # reset relpath from new_dir

        relpath = new_dir + '/' + filename
        if self.post_base_dir :
           relpath = relpath.replace(self.post_base_dir, '')

        # set the results for the new file (downloading or sending)

        self.new_baseurl = 'file:'

        # final value
        # NOTE : normpath keeps '/a/b/c' and '//a/b/c' the same
        #        Everywhere else // or /../ are corrected.
        #        but if the number of / starting the path > 2  ... it will result into 1 /

        self.new_dir     = os.path.normpath(new_dir)
        self.new_file    = filename
        self.new_relpath = os.path.normpath(relpath)

        if self.post_broker and self.post_base_url :
           self.new_baseurl = self.post_base_url

        #self.logger.debug("new_dir     = %s" % self.new_dir)
        #self.logger.debug("new_file    = %s" % self.new_file)
        #self.logger.debug("new_baseurl = %s" % self.new_baseurl)
        #self.logger.debug("new_relpath = %s" % self.new_relpath)

    def reload(self):
        self.logger.info("%s reload" % self.program_name )
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

    def cleanup(self):
        self.logger.info("%s %s cleanup" % (self.program_name,self.config_name))

        # if report_daemons is false than skip 'rr_' config

        if self.config_name and self.config_name[0:3] == 'rr_'  and not self.report_daemons :
           self.logger.info("skipping cleanup for %s" % self.config_name)
           return

        # consumer declare

        self.consumer = sr_consumer(self,admin=True)
        self.consumer.cleanup()

        # if posting

        if self.post_broker :
           self.post_hc = self.consumer.hc
           if self.post_broker != self.broker :
              self.post_hc = HostConnect( logger = self.logger )
              self.post_hc.set_pika( self.use_pika )
              self.post_hc.set_url( self.post_broker )
              self.post_hc.connect()
           self.declare_exchanges(cleanup=True)

        # caching

        if self.caching :
           self.cache.close(unlink=True)
           self.cache = None

        self.close()

    def declare(self):
        self.logger.info("%s %s declare" % (self.program_name,self.config_name))

        # if report_daemons is false than skip 'rr_' config

        if self.config_name and self.config_name[0:3] == 'rr_'  and not self.report_daemons :
           self.logger.info("skipping declare for %s" % self.config_name)
           self.close
           return

        # consumer declare

        self.consumer = sr_consumer(self,admin=True)
        self.consumer.declare()

        # on posting host
        if self.post_broker :
           self.post_hc = self.consumer.hc
           if self.post_broker != self.broker :
              self.post_hc = HostConnect( logger = self.logger )
              self.post_hc.set_pika( self.use_pika )
              self.post_hc.set_url( self.post_broker )
              self.post_hc.connect()
           self.declare_exchanges()

        self.close()

    def declare_exchanges(self, cleanup=False):

        # restore_queue mode has no post_exchange 

        if not self.post_exchange : return

        # define post exchange (splitted ?)

        exchanges = []

        if self.post_exchange_split != 0 :
           for n in list(range(self.post_exchange_split)) :
               exchanges.append(self.post_exchange + "%02d" % n )
        else :
               exchanges.append(self.post_exchange)

        # do exchanges
              
        for x in exchanges :
            if cleanup: self.post_hc.exchange_delete(x)
            else      : self.post_hc.exchange_declare(x)


    def setup(self):
        self.logger.info("%s %s setup" % (self.program_name,self.config_name))

        # if report_daemons is false than skip 'rr_' config

        if self.config_name and self.config_name[0:3] == 'rr_'  and not self.report_daemons :
           self.logger.info("skipping setup for %s" % self.config_name)
           self.close
           return

        # consumer setup

        self.consumer = sr_consumer(self,admin=True)
        self.consumer.setup()

        # on posting host
        if self.post_broker :
           self.post_hc = self.consumer.hc
           if self.post_broker != self.broker :
              self.post_hc = HostConnect( logger = self.logger )
              self.post_hc.set_pika( self.use_pika )
              self.post_hc.set_url( self.post_broker )
              self.post_hc.connect()
           self.declare_exchanges()

        if self.caching :
           self.cache = sr_cache(self)
           self.cache.open()

        self.close()
                 
# ===================================
# self test
# ===================================

class test_logger:
      def silence(self,str):
          pass
      def __init__(self):
          self.debug   = print
          self.error   = print
          self.info    = print
          self.warning = print
          self.debug   = self.silence
          self.info    = self.silence

def test_sr_subscribe():

    logger = test_logger()

    opt1   = 'on_message ./on_msg_test.py'
    opt2   = 'on_part ./on_prt_test.py'
    opt3   = 'on_file ./on_fil_test.py'

    # here an example that calls the default_on_message...
    # then process it if needed
    f      = open("./on_msg_test.py","w")
    f.write("class Transformer(object): \n")
    f.write("      def __init__(self):\n")
    f.write("          self.count_ok = 0\n")
    f.write("      def perform(self, parent ):\n")
    f.write("          if parent.msg.sumflg == 'R' : return True\n")
    f.write("          self.count_ok += 1\n")
    f.write("          parent.msg.mtype_m = self.count_ok\n")
    f.write("          return True\n")
    f.write("transformer = Transformer()\n")
    f.write("self.on_message = transformer.perform\n")
    f.close()

    f      = open("./on_prt_test.py","w")
    f.write("class Transformer(object): \n")
    f.write("      def __init__(self): \n")
    f.write("          self.count_ok = 0\n")
    f.write("      def perform(self, parent ):\n")
    f.write("          if parent.msg.sumflg == 'R' : return True\n")
    f.write("          self.count_ok += 1\n")
    f.write("          parent.msg.mtype_p = self.count_ok\n")
    f.write("          return True\n")
    f.write("transformer = Transformer()\n")
    f.write("self.on_part = transformer.perform\n")
    f.close()

    f      = open("./on_fil_test.py","w")
    f.write("class Transformer(object): \n")
    f.write("      def __init__(self): \n")
    f.write("          self.count_ok = 0\n")
    f.write("      def perform(self, parent ):\n")
    f.write("          self.count_ok += 1\n")
    f.write("          parent.msg.mtype_f  = self.count_ok\n")
    f.write("          return True\n")
    f.write("transformer = Transformer()\n")
    f.write("self.on_file = transformer.perform\n")
    f.close()

    # setup sr_subscribe (just this instance)

    subscribe         = sr_subscribe()
    subscribe.logger  = logger

    # set options
    subscribe.option( opt1.split()  )
    subscribe.option( opt2.split()  )
    subscribe.option( opt3.split()  )
    subscribe.debug   = True

    # ==================
    # set instance

    subscribe.instance      = 1
    subscribe.nbr_instances = 1
    subscribe.connect()
    
    # do an empty consume... assure AMQP's readyness


    # process with our on_message and on_post
    # expected only 1 hit for a good message
    # to go to xreport

    i = 0
    j = 0
    k = 0
    c = 0
    while True :
          ok, msg = subscribe.consumer.consume()
          if not ok : continue
          ok = subscribe.process_message()
          if not ok : continue
          if subscribe.msg.mtype_m == 1: j += 1
          if subscribe.msg.mtype_f == 1: k += 1
          logger.debug(" new_file = %s" % msg.new_file)
          subscribe.msg.sumflg = 'R'
          subscribe.msg.checksum = '0'
          ok = subscribe.process_message()
          
          i = i + 1
          if i == 1 : break

    subscribe.close()

    if j != 1 or k != 1 :
       print("sr_subscribe TEST Failed 1")
       sys.exit(1)

    # FIX ME part stuff
    # with current message from a local file
    # create some parts in parent.msg
    # and process them with subscribe.process_message
    # make sure temporary redirection, insert, download inplace
    # truncate... etc works

    print("sr_subscribe TEST PASSED")

    os.unlink('./on_fil_test.py')
    os.unlink('./on_msg_test.py')
    os.unlink('./on_prt_test.py')

    sys.exit(0)

# ===================================
# MAIN
# ===================================

def main():

    args,action,config,old = startup_args(sys.argv)

    subscribe = sr_subscribe(config,args,action)
    subscribe.exec_action(action,old)

    os._exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
