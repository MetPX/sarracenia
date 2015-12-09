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
# sr_config.py : python3 utility tool to configure sarracenia programs
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Jun Hu         - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Sep 22 10:41:32 EDT 2015
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

import logging
import os,re,socket,sys,random
import urllib,urllib.parse
from   appdirs import *

try :    from sr_util      import *
except : from sarra.sr_util import *

class sr_config:

    def __init__(self,config=None,args=None):

        # program_name

        self.program_name    = re.sub(r'(-script\.pyw|\.exe|\.py)?$', '', os.path.basename(sys.argv[0]) )

        # config

        self.user_config     = config
        self.config_name     = config
        if config != None :
           self.config_name  = re.sub(r'(\.cfg|\.conf|\.config)','',os.path.basename(config))

        # check arguments

        if args == [] : args = None
        self.user_args       = args

        # appdirs setup... on linux it gives :
        # site_data_dir   = /usr/share/default/sarra
        # site_config_dir = /etc/xdg/xdg-default/sarra
        # user_data_dir   = ~/.local/share/sarra
        # user_cache_dir  = ~/.cache/sarra
        # user_log_dir    = ~/.cache/sarra/log
        # user_config_dir = ~/.config/sarra
         
        self.appname         = 'sarra'
        self.appauthor       = 'science.gc.ca'
        self.site_data_dir   = site_data_dir  (self.appname,self.appauthor)
        self.site_config_dir = site_config_dir(self.appname,self.appauthor)
        self.user_data_dir   = user_data_dir  (self.appname,self.appauthor)
        self.user_cache_dir  = user_cache_dir (self.appname,self.appauthor)
        self.user_config_dir = user_config_dir(self.appname,self.appauthor)
        self.user_log_dir    = user_log_dir   (self.appname,self.appauthor)

        # umask change for directory creation and chmod

        try    : os.umask(0)
        except : pass

        # make sure the users directories exist

        try    : os.makedirs(self.user_cache_dir, 0o775,True)
        except : pass
        try    : os.makedirs(self.user_config_dir,0o775,True)
        except : pass
        try    : os.makedirs(self.user_data_dir,  0o775,True)
        except : pass
        try    : os.makedirs(self.user_log_dir,   0o775,True)
        except : pass

        # logging is interactive at start

        self.setlog()
        self.logger.debug("sr_config __init__")

        # general settings

        self.cache_url       = {}
        self.credentials     = []
        self.log_clusters    = {}


    def args(self,args):

        self.logger.debug("sr_config args")

        if args == None : return

        i = 0
        while i < len(args):
              n = self.option(args[i:])
              if n == 0 : n = 1
              i = i + n

    def config(self,path):
        self.logger.debug("sr_config config")

        if path == None : return

        try:
            f = open(path, 'r')
        except:
            (type, value, tb) = sys.exc_info()
            self.logger.error("Type: %s, Value: %s" % (type, value))
            return 

        for line in f.readlines():
            words = line.split()
            if (len(words) >= 2 and not re.compile('^[ \t]*#').search(line)):
                self.option(words)

        f.close()

    def defaults(self):
        self.logger.debug("sr_config defaults")

        self.debug                = False

        self.document_root        = None

        self.discard              = False

        self.events               = 'IN_CLOSE_WRITE|IN_DELETE'
        self.event                = 'IN_CLOSE_WRITE|IN_ATTRIB|IN_MOVED_TO|IN_MOVE_SELF'

        self.flow                 = None

        self.lock                 = None

        self.logpath              = None

        self.notify_only          = False

        self.instance             = 0
        self.nbr_instances        = 1

        self.broker               = urllib.parse.urlparse('amqp://guest:guest@localhost/')
        self.exchange             = None
        self.topic_prefix         = 'v02.post'
        self.subtopic             = None
        self.exchange_key         = None
        self.url                  = None

        self.accept_if_unmatch    = True     # accept if No pattern matching
        self.masks                = []       # All the masks (accept and reject)
        self.currentDir           = '.'      # mask directory (if needed)
        self.currentFileOption    = 'WHATFN' # kept... should we ever reimplement this

        self.mirror               = True

        self.queue_name           = None
        self.queue_prefix         = None
        self.durable              = False
        self.expire               = None
        self.message_ttl          = None

        self.flatten              = '/'

        self.log_back             = True

        self.randomize            = False

        self.reconnect            = False

        self.recursive            = False

        self.rename               = None

        self.source_broker        = urllib.parse.urlparse('amqp://guest:guest@localhost/')
        self.source_exchange      = None
        self.source_topic         = None

        self.source_from_exchange = False

        # cluster stuff
        self.cluster              = None
        self.cluster_aliases      = []
        self.to_clusters          = None
        self.gateway_for          = []

        self.ftp_user             = None
        self.ftp_password         = None
        self.ftp_mode             = 'passive'
        self.ftp_binary           = True
        self.http_user            = None
        self.http_password        = None
        self.sftp_user            = None
        self.sftp_password        = None
        self.sftp_keyfile         = None

        self.sleep                = 0
        self.strip                = 0

        self.parts                = '1'
        self.partflg              = '1'

        self.sumflg               = 'd'
        self.blocksize            = 0

        self.on_file              = None
        self.on_message           = None
        self.on_part              = None
        self.on_poll              = None
        self.on_post              = None

        self.inplace              = False
        self.overwrite            = False
        self.recompute_chksum     = False

        self.interface            = None
        self.vip                  = None

    def execfile(self, opname, path):
        try    : 
                 exec(compile(open(path).read(), path, 'exec'))
        except : 
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.debug("Type: %s, Value: %s" % (stype, svalue))
                 self.logger.error("for option %s script %s did not work" % (opname,path))

    def general(self):
        self.logger.debug("sr_config general")

        # read in provided credentials
        credent = self.user_config_dir + os.sep + 'credentials.conf'
        try :
                 f = open(credent,'r')
                 lines = f.readlines()
                 f.close
                 for line in lines :
                     line = line.strip()
                     if len(line) == 0 or line[0] == '#' : continue
                     parts = line.split()
                     url   = urllib.parse.urlparse(parts[0])
                     key   = None
                     # for sftp only, a second field may be added, the path to the ssh_keyfile
                     if url.scheme == 'sftp' and len(parts) > 1 :
                        key = parts[1]
                     self.credentials.append((url,key))

        # credential file is not mandatory
        except : 
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.debug("Type: %s, Value: %s" % (stype, svalue))
        self.logger.debug("credentials = %s\n" % self.credentials)

        # read in provided log cluster infos
        log_cluster = self.user_config_dir + os.sep + 'log2clusters.conf'
        i = 0
        try :
                 f = open(log_cluster,'r')
                 lines = f.readlines()
                 f.close
                 for line in lines :
                     line = line.strip()
                     if len(line) == 0 or line[0] == '#' : continue
                     parts = line.split()
                     name  = parts[0]
                     u     = urllib.parse.urlparse(parts[1])
                     ok, tup  = self.validate_amqp_url(u)
                     url, key = tup
                     if not ok :
                        self.logger.error("problem with %s" % parts[1])
                     # fixme parts[2] exchange should be optional
                     exch  = parts[2]
                     self.log_clusters[i] = (name,url,exch)
                     i = i + 1

        # cluster file is not mandatory
        except : 
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.debug("Type: %s, Value: %s" % (stype, svalue))
        self.logger.debug("log_clusters = %s\n" % self.log_clusters)

        # sarra.conf ... defaults for the server
        sarra = self.user_config_dir + os.sep + 'sarra.conf'
        if os.path.isfile(sarra) : self.config(sarra)

    def get_queue_name(self):
        if self.queue_name :
           if self.queue_prefix in self.queue_name : return
           self.queue_name = self.queue_prefix + '.'+ self.queue_name
           return
        self.random_queue_name()

    def isMatchingPattern(self, str): 

        for mask in self.masks:
            pattern, maskDir, maskFileOption, mask_regexp, accepting = mask
            if mask_regexp.match(str) :
               self.currentDir        = maskDir
               self.currentFileOption = maskFileOption
               return accepting

        return self.accept_if_unmatch

    def isTrue(self,s):
        if  s == 'True' or s == 'true' or s == 'yes' or s == 'on' or \
            s == 'Yes'  or s == 'YES' or s == 'TRUE' or s == 'ON' or \
            s == '1'    or s == 'On' :
            return True
        else:
            return False


    def option(self,words):
        self.logger.debug("sr_config option %s" % words[0])

        needexit = False
        n        = 0
        try:
                if   words[0] in ['accept','reject']:
                     accepting   = words[0] == 'accept'
                     pattern     = words[1]
                     mask_regexp = re.compile(pattern)

                     if len(words) > 2: self.currentFileOption = words[2]

                     self.masks.append(pattern, self.currentDir, self.currentFileOption, mask_regexp, accepting)

                elif words[0] in ['accept_if_unmatch','-aiu','--accept_if_unmatch']:
                     if words[0][0:1] == '-' : 
                        self.accept_if_unmatch = True
                        n = 1
                     else :
                        self.accept_if_unmatch = self.isTrue(words[1])
                        n = 2

                elif words[0] in ['discard','-d','--discard','--download-and-discard']:
                     self.discard = self.isTrue(words[1])
                     n = 2

                elif words[0] == 'directory':
                     self.currentDir = words[1]

                elif words[0] == 'filename':
                     self.currentFileOption = words[1]

                elif words[0] in ['config','-c','--config']:
                     self.config(words[1])
                     n = 2

                elif words[0] in ['cluster','-cl','--cluster']:
                     self.cluster = words[1] 
                     n = 2

                elif words[0] in ['debug','-debug','--debug']:
                     if words[0][0:1] == '-' : 
                        self.debug = True
                        n = 1
                     else :
                        self.debug = self.isTrue(words[1])
                        n = 2
                     if self.debug :
                        self.logger.setLevel(logging.DEBUG)

                elif words[0] in ['document_root','-dr','--document_root']:
                     self.document_root = words[1]
                     n = 2

                elif words[0] in ['events','-e','--events']:
                     i = 0
                     if 'IN_CLOSE_WRITE' in words[1] : i = i + 1
                     if 'IN_DELETE'      in words[1] : i = i + 1
                     if i == 0 :
                        self.logger.error("events invalid (%s)" % words[1])
                        needexit = True
                     self.events = words[1]
                     n = 2

                elif words[0] in ['cluster_aliases','-ca','--cluster_aliases']:
                     self.cluster_aliases = words[1].split(',')
                     n = 2

                elif words[0] in ['flow','-f','--flow']:
                     self.flow = words[1] 
                     n = 2

                elif words[0] in ['help','-h','-help','--help']:
                     self.help()
                     needexit = True

                elif words[0] in ['lock','-lk','--lock']:
                     self.lock = words[1] 
                     n = 2

                elif words[0] in ['log','-l','-log','--log']:
                     self.logpath = words[1]
                     n = 2

                elif words[0] in ['log_back','-lb','--log_back']:
                     self.log_back = self.isTrue(words[1])
                     n = 2

                elif words[0] in ['inplace','-in','--inplace']:
                     self.inplace = self.isTrue(words[1])
                     n = 2

                elif words[0] in ['instances','-i','--instances']:
                     self.nbr_instances = int(words[1])
                     n = 2

                elif words[0] in ['interface','-interface','--interface']:
                     self.interface = words[1]
                     n = 2

                elif words[0] in ['notify_only','-n','--notify_only','--no-download']:
                     self.notify_only = self.isTrue(words[1])
                     n = 2

                elif words[0] in ['on_file','-on_file','--on_file']:
                     self.on_file = None
                     self.execfile("on_file",words[1])
                     if self.on_file == None :
                        self.logger.error("on_file script incorrect (%s)" % words[1])
                        ok = False
                     n = 2

                elif words[0] in ['on_message','-on_message','--on_message']:
                     self.on_message = None
                     self.execfile("on_message",words[1])
                     if self.on_message == None :
                        self.logger.error("on_message script incorrect (%s)" % words[1])
                        ok = False
                     n = 2

                elif words[0] in ['on_part','-on_part','--on_part']:
                     self.on_part = None
                     self.execfile("on_part",words[1])
                     if self.on_part == None :
                        self.logger.error("on_part script incorrect (%s)" % words[1])
                        ok = False
                     n = 2

                elif words[0] in ['on_poll','-on_poll','--on_poll']:
                     self.on_poll = None
                     self.execfile("on_poll",words[1])
                     if self.on_poll == None :
                        self.logger.error("on_poll script incorrect (%s)" % words[1])
                        ok = False
                     n = 2

                elif words[0] in ['on_post','-on_post','--on_post']:
                     self.on_post = None
                     self.execfile("on_post",words[1])
                     if self.on_post == None :
                        self.logger.error("on_post script incorrect (%s)" % words[1])
                        ok = False
                     n = 2

                elif words[0] in ['parts','-p','--parts']:
                     self.parts   = words[1]
                     ok = self.validate_parts()
                     if not ok : needexit = True
                     n = 2

                elif words[0] in ['broker','-b','--broker'] :
                     self.broker = urllib.parse.urlparse(words[1])
                     ok, tup  = self.validate_amqp_url(self.broker)
                     self.broker, key = tup
                     if not ok :
                        self.logger.error("broker has wrong protocol (%s)" % self.broker.scheme)
                        needexit = True
                     n = 2

                elif words[0] in ['exchange','-ex','--exchange'] :
                     self.exchange = words[1]
                     n = 2

                elif words[0] in ['to','-to','--to']:
                     self.to_clusters = words[1]
                     n = 2

                elif words[0] in ['topic_prefix','-tp','--topic_prefix'] :
                     self.topic_prefix = words[1]

                elif words[0] in ['subtopic','-sub','--subtopic'] :
                     self.subtopic = words[1]
                     if self.exchange_key == None :
                        self.exchange_key = [self.topic_prefix + '.' + self.subtopic]
                     else :
                        self.exchange_key.append(self.topic_prefix + '.' + self.subtopic)
                     n = 2

                elif words[0] in ['overwrite','-o','--overwrite'] :
                     self.overwrite = self.isTrue(words[1])
                     n = 2

                elif words[0] in ['queue_name','-qn','--queue_name'] :
                     self.queue_name = words[1]
                     n = 2

                elif words[0] == 'durable'    : self.durable = isTrue(words[1])
                elif words[0] == 'expire'     : self.expire = int(words[1]) * 60 * 1000
                elif words[0] == 'message-ttl': self.message_ttl = int(words[1]) * 60 * 1000

                elif words[0] in ['randomize','-r','--randomize']:
                     if words[0][0:1] == '-' : 
                        self.randomize = True
                        n = 1
                     else :
                        self.randomize = self.isTrue(words[1])
                        n = 2

                elif words[0] in ['recompute_chksum','-rc','--recompute_chksum']:
                     if words[0][0:1] == '-' : 
                        self.recompute_chksum = True
                        n = 1
                     else :
                        self.recompute_chksum = self.isTrue(words[1])
                        n = 2

                elif words[0] in ['reconnect','-rr','--reconnect']:
                     if words[0][0:1] == '-' : 
                        self.reconnect = True
                        n = 1
                     else :
                        self.reconnect = self.isTrue(words[1])
                        n = 2

                elif words[0] in ['recursive','-rec','--recursive']:
                     if words[0][0:1] == '-' : 
                        self.recursive = True
                        n = 1
                     else :
                        self.recursive = self.isTrue(words[1])
                        n = 2

                elif words[0] in ['rename','-rn','--rename']:
                     self.rename = words[1]
                     n = 2

                elif words[0] in ['gateway_for','-gf','--gateway_for']:
                     self.gateway_for = words[1].split(',')
                     n = 2

                elif words[0] in ['url','-u','--url']:
                     self.url = urllib.parse.urlparse(words[1])
                     n = 2

                elif words[0] in ['source_broker','-sb','--source_broker'] :
                     self.source_broker = urllib.parse.urlparse(words[1])
                     ok, tup  = self.validate_amqp_url(self.source_broker)
                     self.source_broker, key = tup
                     if not ok :
                        self.logger.error("source_broker has wrong protocol (%s)" % self.source_broker.scheme)
                        needexit = True
                     n = 2

                elif words[0] in ['source_exchange','-se','--source_exchange']:
                     self.source_exchange = words[1]
                     n = 2

                elif words[0] in ['source_from_exchange','-sfe','--source_from_exchange']:
                     if words[0][0:1] == '-' : 
                        self.source_from_exchange = True
                        n = 1
                     else :
                        self.source_from_exchange = self.isTrue(words[1])
                        n = 2

                elif words[0] in ['ftp_user','-fu','--ftp_user']:
                     self.ftp_user = words[1]
                     n = 2

                elif words[0] in ['ftp_password','-fp','--ftp_password']:
                     self.ftp_password = words[1]
                     n = 2

                elif words[0] in ['ftp_mode','-fm','--ftp_mode']:
                     if not words[1] in ['active','passive'] :
                        self.logger.error("ftp_mode is active or passive")
                        needexit = True
                     self.ftp_mode = words[1]
                     n = 2

                elif words[0] in ['ftp_binary','-fb','--ftp_binary']:
                     self.ftp_binary = self.isTrue(words[1])
                     n = 2

                elif words[0] in ['mirror','-mirror','--mirror']:
                     self.mirror = self.isTrue(words[1])
                     n = 2

                elif words[0] in ['http_user','-hu','--http_user']:
                     self.http_user = words[1]
                     n = 2

                elif words[0] in ['http_password','-hp','--http_password']:
                     self.http_password = words[1]
                     n = 2

                elif words[0] in ['url_password','-up','--url_password']:
                     self.password = words[1]
                     n = 2

                elif words[0] in ['sftp_user','-su','--sftp_user']:
                     self.sftp_user = words[1]
                     n = 2

                elif words[0] in ['sftp_password','-sp','--sftp_password']:
                     self.sftp_password = words[1]
                     n = 2

                elif words[0] in ['sftp_keyfile','-sk','--sftp_keyfile']:
                     self.sftp_keyfile = words[1]
                     n = 2

                elif words[0] in ['source_topic','-st','--source_topic']:
                     self.source_topic = words[1]
                     n = 2

                elif words[0] in ['sleep','-sleep','--sleep']:
                     self.sleep = int(words[1])
                     n = 2

                elif words[0] in ['strip','-strip','--strip']:
                     self.strip = int(words[1])
                     n = 2

                elif words[0] in ['sum','-sum','--sum']:
                     self.sumflg = words[1]
                     ok = self.validate_sum()
                     if not ok : needexit = True
                     n = 2

                elif words[0] in ['vip','-vip','--vip']:
                     self.vip = words[1]
                     n = 2

        except:
                (stype, svalue, tb) = sys.exc_info()
                self.logger.debug("Type: %s, Value: %s,  ..." % (stype, svalue))

        if needexit :
           sys.exit(0)

        return n

    def random_queue_name(self) :

        queuefile = ''
        parts = self.user_config.split(os.sep)
        if len(parts) != 1 :  queuefile = os.sep.join(parts[:-1]) + os.sep

        fnp   = parts[-1].split('.')
        if fnp[0][0] != '.' : fnp[0] = '.' + fnp[0]
        queuefile = queuefile + '.'.join(fnp[:-1]) + '.queue'

        if os.path.isfile(queuefile) :
           f = open(queuefile)
           self.queue_name = f.read()
           f.close()
           return
        
        self.queue_name  = self.queue_prefix
        self.queue_name += '.'  + str(random.randint(0,100000000)).zfill(8)
        self.queue_name += '.'  + str(random.randint(0,100000000)).zfill(8)

        f = open(queuefile,'w')
        f.write(self.queue_name)
        f.close()

    def setlog(self):

        import logging.handlers

        LOG_FORMAT  = ('%(asctime)s [%(levelname)s] %(message)s')

        if not hasattr(self,'logger') :
           logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
           self.logger = logging.getLogger()
           self.lpath  = None
           self.logger.debug("sr_config setlog 1")
           return

        if self.logpath == self.lpath :
           self.logger.debug("sr_config setlog 2")
           if hasattr(self,'debug') and self.debug : self.logger.setLevel(logging.DEBUG)
           return

        if self.logpath == None :
           self.logger.debug("switching log to stdout")
           del self.logger
           self.setlog()
           return

        self.logger.debug("switching to log file %s" % self.logpath )
          
        self.lpath   = self.logpath
        self.handler = logging.handlers.TimedRotatingFileHandler(self.lpath, when='midnight', interval=1, backupCount=5)
        fmt          = logging.Formatter( LOG_FORMAT )
        self.handler.setFormatter(fmt)

        del self.logger

        self.logger = logging.RootLogger(logging.WARNING)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

        if self.debug :
           self.logger.setLevel(logging.DEBUG)

    def validate_amqp_url(self,url):
        if not url.scheme in ['amqp','amqps'] :
           return False,(url,None)

        return self.validate_url(url)

    # check url and add credentials if needed from credential file

    def validate_url(self,url):

        if url in self.cache_url :
           return True, self.cache_url[url]

        rebuild = False
        user    = url.username
        pasw    = url.password
        key     = None

        # default vhost is '/'
        if url.scheme in ['amqp','amqps'] :
           path = url.path
           if path == None or path == '' :
              path = '/'
              rebuild = True

        if user == None or pasw == None :
           for u,k in self.credentials :
               if url.scheme    != u.scheme  : continue
               if url.hostname  != u.hostname: continue
               if url.port      != u.port    : continue
               if user and user != u.username: continue
               user = u.username
               pasw = u.password
               key  = k
               rebuild = True
               break

        if url.scheme in ['amqp','amqps'] :
           if user == None :
              user = 'guest'
              rebuild = True
           if pasw == None :
              pasw = 'guest'
              rebuild = True
               
        if path == None : path = ''

        if rebuild :
           netloc = url.hostname
           if url.port != None : netloc += ':%d'%url.port
           urls   = '%s://%s:%s@%s%s' % (url.scheme,user,pasw,netloc,path)
           newurl = urllib.parse.urlparse(urls)
           self.cache_url[url] = (newurl,key)
           return True, self.cache_url[url]

        return True,(url,None)

    def validate_parts(self):
        if not self.parts[0] in ['1','p','i']:
           self.logger.error("parts invalid (%s)" % self.parts)
           return False

        self.partflg = self.parts[0]
        token = self.parts.split(',')
        if self.partflg in ['1','p'] and len(token) != 1 :
           self.logger.error("parts invalid (%s)" % self.parts)
           return False
        if self.partflg == 'i':
           if len(token) != 2 :
              self.logger.error("parts invalid (%s)" % self.parts)
              return False
           try    : self.blocksize = chunksize_from_str(token[1])
           except :
                    self.logger.error("parts invalid (%s)" % self.parts)
                    return False
        return True

    def validate_sum(self):
        if self.sumflg[0] in ['0','n','d']: return True
        try :
                 chkclass = Checksum()
                 chkclass.from_list(self.sumflg)
                 return True
        except : 
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s" % (stype, svalue))
                 self.logger.error("sum invalid (%s)" % self.sumflg)
                 return False
        return False


# ===================================
# MAIN
# ===================================

def main():

    if len(sys.argv) == 1 :
       print(" None None")
       cfg = sr_config(None,None)
    elif os.path.isfile(sys.argv[1]):
       args = None
       if len(sys.argv) > 2 : args = sys.argv[2:]
       print(" Conf %s" % args)
       cfg = sr_config(sys.argv[1],args)
    else :
       print(" None %s" % sys.argv[1:])
       cfg = sr_config(None,sys.argv[1:])
    cfg.defaults()
    #to get more details
    cfg.debug = True
    cfg.setlog()
    cfg.logger.debug("user_data_dir = %s" % cfg.user_data_dir)
    cfg.logger.debug("user_cache_dir = %s"% cfg.user_cache_dir)
    cfg.logger.debug("user_log_dir = %s"  % cfg.user_log_dir)
    cfg.logger.debug("user_config_dir = %s"% cfg.user_config_dir)
    cfg.logger.debug("site_data_dir = %s" % cfg.site_data_dir)
    cfg.logger.debug("site_config_dir = %s"  % cfg.site_config_dir)
    cfg.general()
    cfg.args(cfg.user_args)
    cfg.config(cfg.user_config)
    print("  %s" % cfg.source_from_exchange)
    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()


