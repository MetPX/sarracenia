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
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Sep 22 10:41:32 EDT 2015
#
########################################################################

#============================================================
# usage example
#
# sr_subscribe configfile.conf [stop|start|status|reload|restart]
#
#============================================================

import os,sys,time

try :    
         from sr_amqp           import *
         from sr_file           import *
         from sr_ftp            import *
         from sr_http           import *
         from sr_instances      import *
         from sr_message        import *
except : 
         from sarra.sr_amqp      import *
         from sarra.sr_file      import *
         from sarra.sr_ftp       import *
         from sarra.sr_http      import *
         from sarra.sr_instances import *
         from sarra.sr_message   import *

class sr_subscribe(sr_instances):

    def __init__(self,config=None,args=None):
        sr_instances.__init__(self,config,args)
        self.defaults()

        # special settings for sr_subscribe

        self.accept_if_unmatch = False
        self.broker            = urllib.parse.urlparse("amqp://anonymous:anonymous@dd.weather.gc.ca:5672/")
        self.exchange          = 'xpublic'
        self.inplace           = True
        self.lock              = '.tmp'
        self.mirror            = False
        self.overwrite         = True
        self.amqp_log          = None

        self.configure()

    def check(self):

        # setting impacting other settings

        if self.discard:
           self.inplace   = False
           self.overwrite = True
           self.log_back  = False

        if self.notify_only :
           self.log_back  = False

        # if no accept/reject provided... accept .*
        if self.masks == [] :
           self.accept_if_unmatch = True

        # if no subtopic given... make it #  for all
        if self.exchange_key == None :
           self.exchange_key = [self.topic_prefix + '.#']

        # dont want to recreate these if they exists

        if not hasattr(self,'msg') :
           self.msg = sr_message(self.logger)

        self.msg.user         = self.broker.username
        self.msg.exchange_log = 'xs_' + self.broker.username
        self.msg.amqp_pub     = None
        self.msg.exchange_pub = None

        # umask change for directory creation and chmod

        try    : os.umask(0)
        except : pass

    def close(self):
        self.hc.close()

    def connect(self):

        self.hc       = None
        self.amqp_log = None

        self.hc = HostConnect( logger = self.logger )
        self.hc.set_url(self.broker)
        self.hc.connect()

        self.consumer = Consumer(self.hc)
        self.consumer.add_prefetch(1)
        self.consumer.build()

        self.queue_prefix = 'q_'+ self.broker.username
        self.get_queue_name()
        self.msg_queue = Queue(self.hc,self.queue_name,durable=self.durable)
        if self.expire != None :
           self.msg_queue.add_expire(self.expire)
        if self.message_ttl != None :
           self.msg_queue.add_message_ttl(self.message_ttl)


        for k in self.exchange_key :
           self.logger.info('Binding queue %s with key %s to exchange %s on broker %s://%s@%s%s', 
		self.queue_name, k, self.exchange, self.broker.scheme, self.broker.username, self.broker.hostname,self.broker.path )
           self.msg_queue.add_binding(self.exchange, k )

        self.msg_queue.build()

        if self.log_back :
           self.amqp_log = Publisher(self.hc)
           self.amqp_log.build()


    def configure(self):

        # cumulative variable reinitialized

        self.exchange_key         = None     
        self.masks                = []       
        self.currentDir           = '.'      
        self.currentFileOption    = 'WHATFN' 

        # installation general configurations and settings

        self.general()

        # arguments from command line

        self.args(self.user_args)

        # config from file

        self.config(self.user_config)

        # verify all settings

        self.check()

        self.setlog()
        self.logger.info("user_config = %d %s" % (self.instance,self.user_config))

    def delete_event(self):
        if self.msg.sumflg != 'R' : return False

        self.msg.code = 503
        self.msg.message = "Service unavailable : delete"
        self.msg.log_error()
 
        return True

    def download(self):

        self.logger.info("downloading/copying into %s " % self.msg.local_file)

        try :
                if   self.msg.url.scheme == 'http' :
                     return http_download(self.msg, self.http_user, self.http_password )

                elif self.msg.url.scheme == 'ftp' :
                     return ftp_download(self.msg, self.ftp_user, self.ftp_password, self.ftp_mode, self.ftp_binary )

                elif self.msg.url.scheme == 'sftp' :
                     try :    
                              from sr_sftp           import sftp_download
                     except : 
                              from sarra.sr_sftp import sftp_download
                     return sftp_download(self.msg, self.sftp_user, self.sftp_password, self.sftp_keyfile )

                elif self.msg.url.scheme == 'file' :
                     return file_process(self.msg)

        except :
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Download  Type: %s, Value: %s,  ..." % (stype, svalue))
                self.msg.code    = 503
                self.msg.message = "Unable to process"
                self.msg.log_error()

        self.msg.code    = 503
        self.msg.message = "Service unavailable %s" % self.msg.url.scheme
        self.msg.log_error()

    def help(self):
        self.logger.info("Usage: %s [OPTIONS] configfile [start|stop|restart|reload|status]\n" % self.program_name )

        self.logger.info("\nConnect to an AMQP broker to subscribe to timely file update announcements.\n")
        self.logger.info("Examples:\n")    

        self.logger.info("%s subscribe.conf start # download files and display log in stdout" % self.program_name)
        self.logger.info("%s -d subscribe.conf start # discard files after downloaded and display log in stout" % self.program_name)
        self.logger.info("%s -l /tmp subscribe.conf start # download files,write log file in directory /tmp" % self.program_name)
        self.logger.info("%s -n subscribe.conf start # get notice only, no file downloaded and display log in stout\n" % self.program_name)

        self.logger.info("subscribe.conf file settings, MANDATORY ones must be set for a valid configuration:\n" +
          "\nAMQP broker connection:\n" +
          "\tbroker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>\n" +
	  "\t\t(default: amqp://anonymous:anonymous@dd.weather.gc.ca/ ) \n" +
          "\nAMQP Queue settings:\n" +
          "\tdurable       <boolean>      (default: False)\n" +
          "\texchange      <name>         (default: xpublic)\n" +
          "\texpire        <minutes>      (default: None)\n" +
          "\tmessage-ttl   <minutes>      (default: None)\n" +
          "\tqueue_name    <name>         (default: None)\n" +
          "\tsubtopic      <amqp pattern> (MANDATORY)\n" +
          "\t\t  <amqp pattern> = <directory>.<directory>.<directory>...\n" +
          "\t\t\t* single directory wildcard (matches one directory)\n" +
          "\t\t\t# wildcard (matches rest)\n" +
          "\ttopic_prefix  <amqp pattern> (invariant prefix, currently v02.post)\n" +
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

        self.logger.info("if the download of the url received in the amqp message needs credentials")
        self.logger.info("you defines the credentials in the $HOME/.config/sarra/credentials.conf")
        self.logger.info("one url per line. as an example, the file could contain:")
        self.logger.info("http://myhttpuser:myhttppassword@apachehost.com/")
        self.logger.info("ftp://myftpuser:myftppassword@ftpserver.org/")
        self.logger.info("etc...")

    def run(self):

        self.logger.info("sr_subscribe run")

        self.logger.info("AMQP  broker(%s) user(%s) vhost(%s)" % (self.broker.hostname,self.broker.username,self.broker.path) )
        for k in self.exchange_key :
            self.logger.info("AMQP  input :    exchange(%s) topic(%s)" % (self.exchange,k) )
        if self.log_back :
            self.logger.info("AMQP  output:    exchange(%s) topic(%s)\n" % (self.msg.exchange_log,'v02.log.#') )

        self.connect()

        self.msg.logger       = self.logger
        self.msg.amqp_log     = self.amqp_log

        #
        # loop on all message
        #

        raw_msg = None

        while True :

          try  :
                 if raw_msg != None : self.consumer.ack(raw_msg)

                 raw_msg = self.consumer.consume(self.msg_queue.qname)
                 if raw_msg == None : continue

                 # make use it as a sr_message

                 try :
                           self.msg.from_amqplib(raw_msg)
                 except :
                           self.msg.code    = 417
                           self.msg.message = "Expectation Failed : sumflg or partflg"
                           self.msg.log_error()
                           continue

                 # make use of accept/reject

                 if not self.isMatchingPattern(self.msg.urlstr) :
                    self.logger.debug("Rejected by accept/reject options")
                    continue
                 self.document_root = self.currentDir

                 # notify_only mode : print out received message
                 if self.notify_only :
                    self.logger.info("%s %s" % (self.msg.notice,self.msg.hdrstr))
                    continue
                 # log what is selected
                 else :
                    self.logger.info("Received topic   %s" % self.msg.topic)
                    self.logger.info("Received notice  %s" % self.msg.notice)
                    self.logger.info("Received headers %s" % self.msg.headers)

                 # root directory should exists
                 if not os.path.isdir(self.document_root) :
                    self.logger.error("directory %s does not exist" % self.document_root)
                    continue

                 # set local file according to subscribe : dr + imsg.path (or renamed path)

                 self.set_local()

                 # set local file according to the message and subscribe's setting

                 self.msg.set_local(self.inplace,self.local_path,self.local_url)
                 self.msg.headers['rename'] = self.local_path

                 # asked to delete ?

                 if self.delete_event() : continue

                 # make sure local directory exists
                 # FIXME : logging errors...
                 try    : os.makedirs(self.local_dir,0o775,True)
                 except : pass

                 # if overwrite is not enforced (False)
                 # verify if msg checksum and local_file checksum match
                 # FIXME : should we republish / repost ???

                 if not self.overwrite and self.msg.checksum_match() :

                    self.msg.code    = 304
                    self.msg.message = 'not modified'
                    self.msg.log_info()
             
                    # a part unmodified can make a difference
                    if self.inplace and self.msg.in_partfile :
                       file_reassemble(self.msg)

                    # chksum computed on msg offset/length may need to truncate
                    file_truncate(self.msg)
                    continue

                 # proceed to download  3 attempts

                 i  = 0
                 while i < 3 : 
                       ok = self.download()
                       if ok : break
                       i = i + 1
                 if not ok : continue

                 # Delayed insertion
                 # try reassemble the file, conditions may have changed since writing

                 if self.inplace and self.msg.in_partfile :
                    self.msg.code    = 307
                    self.msg.message = 'Temporary Redirect'
                    self.msg.log_info()
                    file_reassemble(self.msg)
                    continue

                 # announcing the download or insert

                 if self.msg.partflg != '1' :
                    if self.inplace : self.msg.change_partflg('i')
                    else            : self.msg.change_partflg('p')

                 # if we inserted a part in file ... try reassemble

                 if self.inplace and self.msg.partflg != '1' :
                    file_reassemble(self.msg)

          except :
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

        if self.mirror :
           filename = self.flatten.join(token)

        self.local_dir  = local_dir
        self.local_file = filename
        self.local_path = local_dir + '/' + filename
        self.local_url  = 'file:' + self.local_path
        self.local_url  = urllib.parse.urlparse(self.local_url)

    def reload(self):
        self.logger.info("sr_subscribe reload")
        self.close()
        self.configure()
        self.run()

    def start(self):
        self.configure()
        self.logger.info("sr_subscribe start")
        self.run()

    def stop(self):
        self.logger.info("sr_subscribe stop")
        self.close()
        os._exit(0)

# ===================================
# MAIN
# ===================================

def main():

    action = None
    args   = None
    config = None

    if len(sys.argv) >= 3 :
       action = sys.argv[-1]
       config = sys.argv[-2]
       if len(sys.argv) > 3: args = sys.argv[1:-2]

    subscribe = sr_subscribe(config,args)

    if   action == 'reload' : subscribe.reload_parent()
    elif action == 'restart': subscribe.restart_parent()
    elif action == 'start'  : subscribe.start_parent()
    elif action == 'stop'   : subscribe.stop_parent()
    elif action == 'status' : subscribe.status_parent()
    else :
           subscribe.logger.error("action unknown %s" % action)
           sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
