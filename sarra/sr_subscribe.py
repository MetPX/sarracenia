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

    def __init__(self,config=None,args=None):
        sr_instances.__init__(self,config,args)

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

        # posting... discard not permitted

        if self.post_broker :
           self.post_document_root = self.document_root

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


    def close(self):
        self.consumer.close()
        if self.save_fp:              self.save_fp.close()
        if self.post_broker:          self.post_hc.close()
        if hasattr(self,'ftp_link') : self.ftp_link.close()
        if hasattr(self,'http_link'): self.http_link.close()
        if hasattr(self,'sftp_link'): self.sftp_link.close()
        if self.caching :
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

        # =============
        # report_publisher
        # =============

        if self.reportback :

           report_exchange = 'xs_' + self.broker.username

           self.report_publisher     = self.consumer.publish_back()
           self.msg.report_publisher = self.report_publisher
           self.msg.report_exchange  = report_exchange
           self.logger.info("report_back to %s@%s, exchange: %s" % 
               ( self.broker.username, self.broker.hostname, self.msg.report_exchange ) )
        else:
           self.logger.warning("report_back suppressed")


        # =============
        # in save mode...
        # =============

        if self.save :
           self.logger.warning("running in save mode")
           self.post_broker   = None

           self.consumer.save = True
           if self.save_file  : self.save_path = self.save_file + self.save_path[-10:]
           self.consumer.save_path = self.save_path

           self.save_fp       = open(self.save_path,"a")
           self.save_count    = 1
           return

        # =============
        # publisher : if self.post_broker exists
        # =============

        if self.post_broker :

           # publisher host

           self.post_hc = HostConnect( logger = self.logger )
           self.post_hc.set_url( self.post_broker )
           self.post_hc.connect()

           # publisher

           self.publisher = Publisher(self.post_hc)
           self.publisher.build()
           self.msg.publisher    = self.publisher
           self.msg.pub_exchange = self.post_exchange
           self.msg.post_exchange_split = self.post_exchange_split

           # amqp resources
           self.declare_exchanges()


    def __do_download__(self):


        self.logger.debug("downloading/copying %s (scheme: %s) into %s " % (self.msg.urlstr, self.msg.url.scheme, self.new_file))

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


    def help(self):
        print("Usage: %s [OPTIONS] [foreground|start|stop|restart|reload|status|cleanup|setup] configfile\n" % self.program_name )
        print("version: %s \n" % sarra.__version__ )
        print("\nConnect to an AMQP broker to subscribe to timely file update announcements.\n")
        print("Examples:\n")    

        print("%s subscribe.conf start # download files and display log in stdout" % self.program_name)
        print("%s -d subscribe.conf start # discard files after downloaded and display log in stout" % self.program_name)
        print("%s -l /tmp subscribe.conf start # download files,write log file in directory /tmp" % self.program_name)
        print("%s -n subscribe.conf start # get notice only, no file downloaded and display log in stout\n" % self.program_name)

        print("subscribe.conf file settings, MANDATORY ones must be set for a valid configuration:\n" +
          "\nAMQP broker settings:\n" +
          "\tbroker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>\n" +
	  "\t\t(default: amqp://anonymous:anonymous@dd.weather.gc.ca/ ) \n" +
          "\nAMQP Queue bindings:\n" +
          "\texchange      <name>         (default: xpublic)\n" +
          "\ttopic_prefix  <amqp pattern> (invariant prefix, currently v02.post)\n" +
          "\tsubtopic      <amqp pattern> (MANDATORY)\n" +
          "\t\t  <amqp pattern> = <directory>.<directory>.<directory>...\n" +
          "\t\t\t* single directory wildcard (matches one directory)\n" +
          "\t\t\t# wildcard (matches rest)\n" +
          "\nAMQP Queue settings: (usually do not need to set any of these.)\n" +
          "\tdurable       <boolean>      persist across broker restarts (default: False)\n" +
          "\texpire        <minutes>      how long unused queues stay defined (default: None)\n" +
          "\tmessage-ttl   <minutes>      how long messages stay in queue without being consumed (default: None)\n" +
          "\tqueue_name    <name>         (default: program set it for you)\n" +
          "\nHTTP Settings:\n" +
          "\nLocal File Delivery settings:\n" +
          "\taccept    <regexp pattern> regular expressions of files to download.\n" +
          "\taccept_unmatch    <boolean> if no accept or reject clauses match, download? (default: no).\n" +
          "\tdirectory <path>           where to place files (place ABOVE accept in configuration) (default: .)\n" +
          "\tflatten   <string>         keep directories in filename replaced by *flatten* character (default: '/' )\n" +
          "\tinflight  <.string>        suffix (or prefix) to name for files while they are downloaded (default: .tmp)\n" +
          "\tmirror    <boolean>        same directory tree as on source, or flat. (default: false)\n" +
          "\treject    <regexp pattern> regular expression of files to ignore (optional)\n" +
          "\tstrip    <count> (number of directories to remove from beginning.)\n" +
	  "" )

        print("if the download of the url received in the amqp message needs credentials")
        print("you defines the credentials in the $HOME/.config/sarra/credentials.conf")
        print("one url per line. as an example, the file could contain:")
        print("http://myhttpuser:myhttppassword@apachehost.com/")
        print("ftp://myftpuser:myftppassword@ftpserver.org/")
        print("etc...")

    # =============
    # __on_message__
    # =============

    def __on_message__(self):

        # apply default to a message without a source
        ex = self.msg.exchange
        if not 'source' in self.msg.headers :
           if len(ex) > 3 and ex[:3] == 'xs_' : self.msg.headers['source'] = ex[3:].split('_')[0]
           elif self.source                   : self.msg.headers['source'] = self.source
           else                               : self.msg.headers['source'] = self.broker.username
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

        # invoke user defined on_message when provided

        self.local_file = self.new_dir + '/' + self.new_file     # FIXME: remove in 2018, once all plugins are converted.
        self.msg.local_file = self.local_file
        saved_file = self.local_file

        self.local_dir = self.new_dir     # FIXME: remove in 2018, once all plugins are converted.
        self.msg.local_dir = self.new_dir
        saved_dir = self.new_dir

        for plugin in self.on_message_list :

           if not plugin(self): return False

           if self.msg.local_file != saved_file :
               self.logger.warning("on_message plugins 2 should replace parent.msg.local_file, by parent.new_dir and parent.new_file" )
               self.new_file = os.path.basename(self.local_file)
               self.new_dir = os.path.dirname(self.local_file)

           if self.msg.local_dir != saved_dir :
               self.logger.warning("on_message plugins 2 should replace parent.msg.local_dir, by parent.new_dir" )
               self.logger.warning("parent.msg.local_dir=%s, by parent.new_dir=%s" % (self.msg.local_dir, self.new_dir) )
               self.new_dir = self.msg.local_dir

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

        self.save_fp        = None
        self.save_count     = 1

    # =============
    # process message  
    # =============

    def process_message(self):

        self.logger.debug("Received notice  %s %s%s" % tuple(self.msg.notice.split()[0:3]) )

        # selected directory from accept/reject resolved in consumer

        self.document_root = self.currentDir

        #=================================
        # setting up message with sr_subscribe config options
        # self.set_local     : how/where sr_subscribe is configured for that product
        # self.msg.set_local : how message settings (like parts) applies in this case
        #=================================

        self.set_new()
        self.msg.set_new(self.inplace, self.new_dir + '/' + self.new_file, self.new_url)

        #=================================
        # now invoke __on_message__
        #=================================

        ok = self.__on_message__()
        if not ok : return ok

        #=================================
        # if caching is set
        #=================================

        if self.caching :
           if not self.cache.check(str(self.msg.checksum),self.msg.url.path,self.msg.partstr):
              if self.reportback : self.msg.report_publish(304,'Not modified')
              self.logger.debug("Ignored %s" % (self.msg.notice))
              return True

        #=================================
        # if notify_only... just post here
        #=================================

        if self.notify_only :
           if self.post_broker:
              self.logger.debug("notify_only post")
              self.__on_post__()
              if self.reportback : self.msg.report_publish(201,'Published')
           return True


        """
        FIXME: 201612-PAS There is perhaps several bug here:
            -- no_download is not consulted. In no_download, mkdir, deletes and links should not happen.
            -- on_file/on_part processing is not invoked for links or deletions, should it?
               do we need on_link? on_delete? ugh...
            
        """
        #=================================
        # delete event, try to delete the local product given by message
        #=================================

        if self.msg.sumflg.startswith('R') :
           self.logger.debug("message is to remove %s" % self.new_file)
           try : 
               if os.path.isfile(self.new_file) : os.unlink(self.new_file)
               if os.path.isdir( self.new_file) : os.rmdir( self.new_file)
               self.logger.debug("%s removed" % self.new_file)
               if self.reportback: self.msg.report_publish(201, 'removed')
           except:
               self.logger.error("remove %s failed." % self.new_file )
               if self.reportback: self.msg.report_publish(500, 'remove failed')
           return True

        #=================================
        # link event, try to link the local product given by message
        #=================================

        if self.msg.sumflg.startswith('L') :
           self.logger.debug("message is to link %s to %s" % ( self.new_file, self.msg.headers[ 'link' ] ) )
           try : 
               os.symlink( self.msg.headers[ 'link' ], self.new_file )
               self.logger.debug("%s linked to %s " % (self.new_file, self.msg.headers[ 'link' ]) )
               if self.reportback: self.msg.report_publish(201, 'linked')
           except:
               self.logger.error("symlink of %s %s failed." % (self.new_file, self.msg.headers[ 'link' ]) )
               if self.reportback: self.msg.report_publish(500, 'symlink failed')
		

           if ok and self.post_broker :
              self.logger.debug("ERROR self.post_broker = %s" % self.post_broker)
              self.msg.set_topic_url('v02.post',self.new_url)
              self.msg.set_notice_url(self.new_url,self.msg.time)
              self.__on_post__()
              self.msg.report_publish(205,'Reset Content : linked')

           return True

        #=================================
        # prepare download 
        # the document_root should exists : it the starting point of the downloads
        # make sure local directory where the file will be downloaded exists
        #=================================
        # Caveat, where the local directory has sundew substitutions, it is normal for 
        # that directory not to exist ( e.g. /home/peter/test/dd/{RYYYY} )
        # FIXME: should we remove the substitutions and check the root of the root?
        #=================================

        if not '{' in self.document_root :
           if not os.path.isdir(self.document_root) :
              self.logger.error("directory %s does not exist" % self.document_root)
              return False

        # pass no warning it may already exists
        try    : os.makedirs(self.new_dir,0o775,True)
        except : pass

        #=================================
        # overwrite False, user asked that if the announced file already exists,
        # verify checksum to avoid an unnecessary download
        #=================================

        need_download = True
        if not self.overwrite and self.msg.content_should_not_be_downloaded() :
           if self.reportback:
              self.msg.report_publish(304, 'not modified')
           self.logger.debug("file not modified %s " % self.new_file)

           # if we are processing an entire file... we are done
           if self.msg.partflg == '1' :  return False

           need_download = False

        #=================================
        # attempt downloads
        #=================================

        if need_download :
           i  = 0
           while i < self.attempts : 
                 ok = self.__do_download__()
                 if ok : break
                 i = i + 1
           # could not download
           if not ok : return False

           # after download : setting of sum for 'z' flag ...

           if len(self.msg.sumflg) > 2 and self.msg.sumflg[:2] == 'z,':
              self.msg.set_sum(self.msg.checksum,self.msg.onfly_checksum)
              self.msg.report_publish(205,'Reset Content : checksum')

           # onfly checksum is different from the message ???
           if not self.msg.onfly_checksum == self.msg.checksum :
              self.logger.warning("onfly_checksum %s differ from message %s" %
                                 (self.msg.onfly_checksum, self.msg.checksum))

              # force onfly checksum  in message

              if self.recompute_chksum :
                 #self.msg.compute_local_checksum()
                 self.msg.set_sum(self.msg.sumflg,self.msg.onfly_checksum)
                 self.msg.report_publish(205,'Reset Content : checksum')


           # if the part should have been inplace... but could not

           if self.inplace and self.msg.in_partfile :
              if self.reportback:
                 self.msg.report_publish(307,'Temporary Redirect')

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

                 for plugin in self.on_file_list:
                     if not plugin(self): return False

                     if ( self.msg.local_file != self.new_file ): # FIXME remove in 2018
                        self.logger.warning("on_file plugins should replace parent.msg.local_file, by parent.new_file" )
                        self.new_file = self.msg.local_file

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
           self.msg.set_topic_url('v02.post',self.new_url)
           self.msg.set_notice_url(self.new_url,self.msg.time)
           self.__on_post__()
           self.msg.report_publish(201,'Published')

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

                 # =====
                 # MG COMMENTED THIS OUT 
                 # there are several problems with this code part.
                 # 1- builds urlstr and match against msg.urlstr
                 # 2- self.consumer.consume already passed through filtering before the save
                 # 3- anyway, if it was not the case and a message would be filtered, the count would 
                 #    never match the total and the save_path would never get unlinked ...
                 #    that would lead into eventual bugs (like old save_file to which we append new messages...)
                 # 4- the one instance of isMatchingPattern in sr_config is available everywhere
                 #    because it is inherited ... so already available in all programs
                 # =====

                 # make use of accept/reject
                 #if self.use_pattern :
                     # Adjust url to account for sundew extension if present, and files do not already include the names.
                     #if urllib.parse.urlparse(self.msg.urlstr).path.count(":") < 1 and 'sundew_extension' in self.msg.headers.keys() :
                     #   urlstr=self.msg.urlstr + ':' + self.msg.headers[ 'sundew_extension' ]
                     #else:
                     #   urlstr=self.msg.urlstr

                     #self.logger.debug("sr_sender restore, path being matched: %s " % ( urlstr )  )

                     #if not self.isMatchingPattern(self.msg.urlstr,self.accept_unmatch) :
                     #   self.logger.debug("Rejected by accept/reject options")
                     #   return False,self.msg

                 self.logger.info("%s restoring message %d of %d: topic: %s" %
                                 (self.program_name,  count,total, self.msg.topic) )
                 ok = self.process_message()

        if count >= total:
           self.logger.info("%s restore complete deleting save file: %s " % ( self.program_name, self.save_path ) )
           os.unlink(self.save_path)
        else:
           self.logger.error("%s only restored %d of %d messages from save file: %s " %
                            (self.program_name, count, total, self.save_path ) )


    def run(self):

        self.logger.info("%s run" % self.program_name)

        # loop/process messages

        self.connect()

        # restoring messages

        if self.restore : self.restore_messages()

        # processing messages

        while True :
              try  :
                      # if vip provided, check if has vip

                      if self.vip :
                         active = self.has_vip()

                         #  it is sleeping !
                         if not active :
                            time.sleep(5)
                            self.logger.debug("%s does not have vip=%s, is sleeping", (self.program_name,self.vip))
                            active=False
                            continue

                         #  it is alive
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

    # ==============================================
    # how will the download file land on this server
    # with all options, this is really tricky
    # ==============================================

    def set_new(self):

        self.logger.debug("set_new strip=%s, mirror=%s flatten=%s dr=%s msg.path=%s" %  \
             ( self.strip, self.mirror, self.flatten, self.document_root, self.msg.path ) ) 
        # default the file is dropped in document_root directly

        new_dir  = self.document_root

        # relative path and filename from message

        rel_path = '%s' % self.msg.path
        token    = rel_path.split('/')
        filename = token[-1]

        # case S=0  sr_post -> sr_suscribe... rename in headers

        # FIXME: 255 char limit on headers, rename will break!
        if 'rename' in self.msg.headers :
           rel_path = self.msg.headers['rename']
           token    = rel_path.split('/')
           filename = token[-1]


        # if strip is used... strip N heading directories

        if self.strip > 0 :
           rel_path = '/'.join(token[self.strip:])

        # if mirror... we need to add to document_root the relative path
        # strip taken into account

        if self.mirror :
           rel_dir    = '/'.join(token[self.strip:-1])
           new_dir  = self.document_root + '/' + rel_dir
           
        # if flatten... we flatten relative path
        # strip taken into account

        if self.flatten != '/' :
           filename = self.flatten.join(token)

        if self.currentFileOption != None :
           filename = self.sundew_getDestInfos(filename)

        self.new_dir  = new_dir

        if 'sundew_extension' in self.msg.headers.keys() :
            tfname=filename.split(':')[0] + ':' + self.msg.headers[ 'sundew_extension' ]
            self.new_dir  = self.sundew_dirPattern(self.msg.urlstr,tfname,new_dir,filename)

        self.new_file = filename
        self.new_url  = 'file:' + self.new_dir + '/' + filename
        self.new_url  = urllib.parse.urlparse(self.new_url)

        if self.post_broker :
           if  self.post_document_root : rel_dir = new_dir.replace(self.post_document_root,'')
           else                        : rel_dir = new_dir
           rel_path     = rel_dir  + '/' + filename

           if self.url : self.new_url = urllib.parse.urlparse(self.url.geturl() + '/' + rel_path)


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

    def cleanup(self):
        self.logger.info("%s cleanup" % self.program_name)

        self.consumer = sr_consumer(self,admin=True)
        self.consumer.cleanup()

        # if caching

        if self.caching :
           self.cache.close(unlink=True)

        # if posting

        if self.post_broker :
           self.post_hc = HostConnect( logger = self.logger )
           self.post_hc.set_url( self.post_broker )
           self.post_hc.connect()
           self.declare_exchanges(cleanup=True)

        self.close()
        os._exit(0)

    def declare(self):
        self.logger.info("%s declare" % self.program_name)

        self.consumer = sr_consumer(self,admin=True)
        self.consumer.declare()

        # on posting host
        if self.post_broker :
           self.post_hc = HostConnect( logger = self.logger )
           self.post_hc.set_url( self.post_broker )
           self.post_hc.connect()
           self.declare_exchanges()

        self.close()
        os._exit(0)

    def declare_exchanges(self, cleanup=False):

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
        self.logger.info("%s setup" % self.program_name)

        self.consumer = sr_consumer(self,admin=True)
        self.consumer.setup()

        # on posting host
        if self.post_broker :
           self.post_hc = HostConnect( logger = self.logger )
           self.post_hc.set_url( self.post_broker )
           self.post_hc.connect()
           self.declare_exchanges()

        if self.caching :
           self.cache = sr_cache(self)
           self.cache.open()

        self.close()
        os._exit(0)
                 
# ===================================
# self test
# ===================================

class test_logger:
      def silence(self,str):
          pass
      def __init__(self):
          self.debug   = self.silence
          self.error   = print
          self.info    = self.silence
          self.warning = print

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

    subscribe = sr_subscribe(config,args)

    if action == None and config == None:
       subscribe.help()
       sys.exit(1)

    if old :
       subscribe.logger.warning("Should invoke : %s [args] action config" % sys.argv[0])

    if   action == 'foreground' : subscribe.foreground_parent()
    elif action == 'reload'     : subscribe.reload_parent()
    elif action == 'restart'    : subscribe.restart_parent()
    elif action == 'start'      : subscribe.start_parent()
    elif action == 'stop'       : subscribe.stop_parent()
    elif action == 'status'     : subscribe.status_parent()

    elif action == 'cleanup'    : subscribe.cleanup()
    elif action == 'declare'    : subscribe.declare()
    elif action == 'setup'      : subscribe.setup()

    else :
           subscribe.logger.error("action unknown %s" % action)
           subscribe.help()
           sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
