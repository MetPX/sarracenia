#!/usr/bin/python3
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
# sr_subscribe [options] [config] [start|stop|restart|reload|status]
#
#============================================================

import os,sys,time

try :    
         from sr_consumer       import *
         from sr_file           import *
         from sr_ftp            import *
         from sr_http           import *
         from sr_instances      import *
except : 
         from sarra.sr_consumer  import *
         from sarra.sr_file      import *
         from sarra.sr_ftp       import *
         from sarra.sr_http      import *
         from sarra.sr_instances import *

class sr_subscribe(sr_instances):

    def __init__(self,config=None,args=None):
        sr_instances.__init__(self,config,args)

    def check(self):
        self.logger.debug("sr_subscribe check")

        # setting impacting other settings

        if self.discard:
           self.inplace    = False
           self.overwrite  = True

        # if no subtopic given... make it #  for all
        if self.bindings == []  :
           key = self.topic_prefix + '.#'
           self.bindings.append( (self.exchange,key) )
           self.logger.debug("*** BINDINGS %s"% self.bindings)

        # pattern must be used
        # if unset we will accept unmatched... so everything

        self.use_pattern          = True
        self.accept_unmatch       = self.masks == []

    def close(self):
        self.consumer.close()
        if hasattr(self,'ftp_link') : self.ftp_link.close()
        if hasattr(self,'http_link'): self.http_link.close()
        if hasattr(self,'sftp_link'): self.sftp_link.close()

    def overwrite_defaults(self):
        self.logger.debug("sr_subscribe overwrite_defaults")

        # special settings for sr_subscribe

        self.accept_unmatch = False
        self.broker         = urllib.parse.urlparse("amqp://anonymous:anonymous@dd.weather.gc.ca:5672/")
        self.exchange       = 'xpublic'
        self.inplace        = True
        self.lock           = '.tmp'
        self.mirror         = False
        self.no_logback     = False

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
        # publisher... (publish back to consumer)  
        # =============

        if not self.no_logback :
           self.logger.warning("logback is active exchange is: %s" % self.log_exchange )

           self.publisher         = self.consumer.publish_back()
           self.msg.log_publisher = self.publisher
           self.msg.log_exchange  = 'xs_' + self.broker.username
        else:
           self.logger.warning("logback suppressed")

    def __do_download__(self):


        self.logger.debug("downloading/copying into %s " % self.msg.local_file)

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
                self.msg.log_publish(503,"Unable to process")
                self.logger.error("sr_subscribe: Could not download")

        self.msg.log_publish(503,"Service unavailable %s" % self.msg.url.scheme)


    def help(self):
        print("Usage: %s [OPTIONS] configfile [start|stop|restart|reload|status]\n" % self.program_name )

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
          "\nAMQP Queue settings:\n" +
          "\tdurable       <boolean>      (default: False)\n" +
          "\texpire        <minutes>      (default: None)\n" +
          "\tmessage-ttl   <minutes>      (default: None)\n" +
          "\tqueue_name    <name>         (default: program set it for you)\n" +
          "\nHTTP Settings:\n" +
          "\nLocal File Delivery settings:\n" +
          "\taccept    <regexp pattern> (MANDATORY)\n" +
          "\tdirectory <path>           (default: .)\n" +
          "\tflatten   <boolean>        (default: false)\n" +
          "\tlock      <.string>        (default: .tmp)\n" +
          "\tmirror    <boolean>        (default: false)\n" +
          "\treject    <regexp pattern> (optional)\n" +
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

        # invoke user defined on_message when provided

        if self.on_message : 
           ok = self.on_message(self)
           if not ok : return ok

        # notify only : we are done with this message

        if self.notify_only : return False

        return True

    # =============
    # process message  
    # =============

    def process_message(self):

        self.logger.debug("Received notice  %s" % self.msg.notice)

        # selected directory from accept/reject resolved in consumer

        self.document_root = self.currentDir

        #=================================
        # setting up message with sr_subscribe config options
        # self.set_local     : how/where sr_subscribe is configured for that product
        # self.msg.set_local : how message settings (like parts) applies in this case
        #=================================

        self.set_local()
        self.msg.set_local(self.inplace,self.local_path,self.local_url)
        self.msg.headers['rename'] = self.local_path

        #=================================
        # now invoke __on_message__
        #=================================

        ok = self.__on_message__()
        if not ok : return ok

        #=================================
        # delete event, try to delete the local product given by message
        #=================================

        if self.msg.sumflg == 'R' :
           self.logger.debug("message is to remove %s" % self.msg.local_file)
           try : 
                  if os.path.isfile(self.msg.local_file) : os.unlink(self.msg.local_file)
                  if os.path.isdir( self.msg.local_file) : os.rmdir( self.msg.local_file)
                  self.logger.debug("%s deleted" % self.msg.local_file)
           except:pass
           return True

        #=================================
        # prepare download 
        # the document_root should exists : it the starting point of the downloads
        # make sure local directory where the file will be downloaded exists
        #=================================

        if not os.path.isdir(self.document_root) :
           self.logger.error("directory %s does not exist" % self.document_root)
           return False

        # pass no warning it may already exists
        try    : os.makedirs(self.local_dir,0o775,True)
        except : pass

        #=================================
        # overwrite False, user asked that if the announced file already exists,
        # verify checksum to avoid an unnecessary download
        #=================================

        need_download = True
        if not self.overwrite and self.msg.checksum_match() :
           self.msg.log_publish(304, 'not modified')
           self.logger.debug("file not modified %s " % self.msg.local_file)

           # if we are processing an entire file... we are done
           if self.msg.partflg == '1' :  return False

           need_download = False

        #=================================
        # proceed to download  3 attempts
        #=================================

        if need_download :
           i  = 0
           while i < 3 : 
                 ok = self.__do_download__()
                 if ok : break
                 i = i + 1
           # could not download
           if not ok : return False

           # if the part should have been inplace... but could not

           if self.inplace and self.msg.in_partfile :
              self.msg.log_publish(307,'Temporary Redirect')

           # got it : call on_part (for all parts, a file being consider
           # a 1 part product... we run on_part in all cases)

           if self.on_part :
              ok = self.on_part(self)
              if not ok : return False

           # running on_file : if it is a file, or 
           # it is a part and we are not running "inplace" (discard True)
           # or we are running in place and it is the last part.

           if self.on_file :
              # entire file pumped in
              if self.msg.partflg == '1' :
                 ok = self.on_file(self)

              # parts : not inplace... all considered files
              else:
                 if not self.inplace :
                    ok = self.on_file(self)

                 # ***FIX ME***: When reassembled, lastchunk is inserted last and therefore
                 # calling on_file on lastchunk is accurate... Here, the lastchunk was inserted
                 # directly into the target file... The decision of directly inserting the part
                 # into the file is based on the file'size being bigger or equal to part's offset.
                 # It may be the case that we were at the point of inserting the last chunk...
                 # BUT IT IS POSSIBLE THAT,WHEN OVERWRITING A FILE WITH PARTS BEING SENT IN PARALLEL,
                 # THE PROGRAM INSERTS THE LASTCHUNK BEFORE THE END OF COLLECTING THE FILE'PARTS...
                 # HENCE AN APPROPRIATE CALL TO on_file ... 

                 # inplace : last part(chunk) is inserted
                 elif (self.msg.lastchunk and not self.msg.in_partfile) :
                    ok = self.on_file(self)

              if not ok : return False

           # discard option

           if self.discard :
              try    :
                        os.unlink(self.msg.local_file)
                        self.logger.debug("Discarded  %s" % self.msg.local_file)
              except :
                        (stype, svalue, tb) = sys.exc_info()
                        self.logger.error("Could not discard  Type: %s, Value: %s,  ..." % (stype, svalue))
              return False

        #=================================
        # if we processed a file we are done
        #=================================

        if self.msg.partflg == '1' : return True

        #=================================
        # if we processed a part (downloaded or not)
        # it can make a difference for parts that wait reassembly
        #=================================
   
        file_reassemble(self)

        return True


    def run(self):

        self.logger.info("sr_subscribe run")

        # loop/process messages

        self.connect()

        while True :
              try  :
                      #  consume message
                      ok, self.msg = self.consumer.consume()
                      if not ok : continue

                      #  process message (ok or not... go to the next)
                      ok = self.process_message()

              except:
                      (stype, svalue, tb) = sys.exc_info()
                      self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))


    # ==============================================
    # how will the download file land on this server
    # with all options, this is really tricky
    # ==============================================

    def set_local(self):

        # default the file is dropped in document_root directly

        local_dir  = self.document_root

        # relative path and filename from message

        rel_path = '%s' % self.msg.path
        token    = rel_path.split('/')
        filename = token[-1]

        # case S=0  sr_post -> sr_suscribe... rename in headers

        if 'rename' in self.msg.headers :
           rel_path = self.msg.headers['rename']
           token    = rel_path.split('/')
           filename = token[-1]

        # if strip is used... strip N heading directories

        if self.strip > 0 :
           if self.strip >= len(token)-1 : token = [token[-1]]
           else :                          token = token[self.strip:]
           rel_path = '/'.join(token)

        # if mirror... we need to add to document_root the relative path
        # strip taken into account

        if self.mirror :
           rel_dir    = '/'.join(token[:-1])
           local_dir  = self.document_root + '/' + rel_dir
           
        # if flatten... we flatten relative path
        # strip taken into account

        if self.flatten != '/' :
           filename = self.flatten.join(token)

        self.local_dir  = local_dir
        self.local_file = filename
        self.local_path = local_dir + '/' + filename
        self.local_url  = 'file:' + self.local_path
        self.local_url  = urllib.parse.urlparse(self.local_url)


    def reload(self):
        self.logger.info("%s reload" % self.program_name)
        self.close()
        self.configure()
        self.run()

    def start(self):
        self.logger.info("%s start" % self.program_name)
        self.run()

    def stop(self):
        self.logger.info("%s stop" % self.program_name)
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
    # to go to xlog

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
          logger.debug(" local_file = %s" % msg.local_file)
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

    action = None
    args   = None
    config = None

    if len(sys.argv) >= 2 : 
       action = sys.argv[-1]

    if len(sys.argv) >= 3 : 
       config = sys.argv[-2]
       args   = sys.argv[1:-2]

    subscribe = sr_subscribe(config,args)

    if   action == 'foreground' : subscribe.foreground_parent()
    elif action == 'reload'     : subscribe.reload_parent()
    elif action == 'restart'    : subscribe.restart_parent()
    elif action == 'start'      : subscribe.start_parent()
    elif action == 'stop'       : subscribe.stop_parent()
    elif action == 'status'     : subscribe.status_parent()
    elif action == 'TEST'       : test_sr_subscribe()
    else :
           subscribe.logger.error("action unknown %s" % action)
           sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
