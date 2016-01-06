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
import netifaces
import os,re,socket,sys,random
import urllib,urllib.parse
from   appdirs import *

try :
         from sr_credentials       import *
         from sr_util              import *
except : 
         from sarra.sr_credentials import *
         from sarra.sr_util        import *

class sr_config:

    def __init__(self,config=None,args=None):

        # appdirs setup... on linux it gives :
        # site_data_dir   = /usr/share/default/sarra
        # site_config_dir = /etc/xdg/xdg-default/sarra
        # user_data_dir   = ~/.local/share/sarra
        # user_cache_dir  = ~/.cache/sarra
        # user_log_dir    = ~/.cache/sarra/log
        # user_config_dir = ~/.config/sarra
         
        self.appname          = 'sarra'
        self.appauthor        = 'science.gc.ca'
        self.site_data_dir    = site_data_dir  (self.appname,self.appauthor)
        self.site_config_dir  = site_config_dir(self.appname,self.appauthor)
        self.user_data_dir    = user_data_dir  (self.appname,self.appauthor)
        self.user_cache_dir   = user_cache_dir (self.appname,self.appauthor)
        self.user_config_dir  = user_config_dir(self.appname,self.appauthor)
        self.user_log_dir     = user_log_dir   (self.appname,self.appauthor)

        self.user_queue_dir   = self.user_cache_dir + '/queue'
        self.user_scripts_dir = self.user_config_dir + '/scripts'

        # umask change for directory creation and chmod

        try    : os.umask(0)
        except : pass

        # make sure the users directories exist

        try    : os.makedirs(self.user_cache_dir,  0o775,True)
        except : pass
        try    : os.makedirs(self.user_config_dir, 0o775,True)
        except : pass
        try    : os.makedirs(self.user_data_dir,   0o775,True)
        except : pass
        try    : os.makedirs(self.user_log_dir,    0o775,True)
        except : pass
        try    : os.makedirs(self.user_queue_dir,  0o775,True)
        except : pass
        try    : os.makedirs(self.user_scripts_dir,0o775,True)
        except : pass

        # logging is interactive at start

        self.setlog()
        self.logger.debug("sr_config __init__")

        # program_name

        self.program_name = re.sub(r'(-script\.pyw|\.exe|\.py)?$', '', os.path.basename(sys.argv[0]) )
        self.program_dir  = self.program_name[3:]
        self.logger.debug("sr_config program_name %s " % self.program_name)

        # config

        self.config_name  = None
        self.user_config  = config

        # config might be None ... in some program or if we simply instantiate a class
        # but if it is not... it better be an existing file

        if config != None :
           self.config_name = re.sub(r'(\.conf)','',os.path.basename(config))
           ok, self.user_config = self.config_path(self.program_dir,config)
           self.logger.debug("sr_config config_name  %s " % self.config_name ) 
           self.logger.debug("sr_config user_config  %s " % self.user_config ) 

        # check arguments

        if args == [] : args = None
        self.user_args       = args

        # general settings

        self.users           = {}
        self.cache_url       = {}
        self.credentials     = sr_credentials(self.logger)
        self.log_clusters    = {}

    def args(self,args):

        self.logger.debug("sr_config args")

        if args == None : return

        # on command line opition starts with - or --
        i = 0
        while i < len(args):
              n = 1
              if args[i][0] == '-' :
                 n = self.option(args[i:])
                 if n == 0 : n = 1
              i = i + n


    def config(self,path):
        self.logger.debug("sr_config config")

        if path == None : return

        try:
            f = open(path, 'r')
            for line in f.readlines():
                words = line.split()
                if (len(words) >= 2 and not re.compile('^[ \t]*#').search(line)):
                    self.option(words)
            f.close()

        except:
            (stype, svalue, tb) = sys.exc_info()
            self.logger.error("Type: %s, Value: %s" % (stype, svalue))

    def config_path(self,subdir,config):

        if config == None : return False,None

        # priority 1 : config given is absolute path

        if os.path.isfile(config) :
           return True,config

        config_name = re.sub(r'(\.conf|\.py)','',os.path.basename(config))

        if subdir == 'scripts' : ext = '.py'
        else                   : ext = '.conf'

        # priority 2 : config given is a user one

        config_path = self.user_config_dir + os.sep + subdir + os.sep + config_name + ext

        if os.path.isfile(config_path) :
           return True,config_path

        # priority 3 : config given to site config

        config_path = self.site_config_dir + os.sep + subdir + os.sep + config_name + ext

        if os.path.isfile(config_path) :
           return True,config_path

        # return bad file ... 

        if subdir == 'scripts' : self.logger.error("Script incorrect %s" % config)
        else                   : self.logger.error("File incorrect %s" % config)

        return False,config


    def defaults(self):
        self.logger.debug("sr_config defaults")

        self.debug                = False

        self.logrotate            = 5

        self.admin                = None
        self.manager              = None

        # consumer
        self.broker               = urllib.parse.urlparse('amqp://guest:guest@localhost/')
        self.bindings             = []
        self.exchange             = None
        self.topic_prefix         = 'v02.post'
        self.subtopic             = None

        self.queue_name           = None
        self.durable              = False
        self.expire               = None
        self.message_ttl          = None
        self.queue_share          = False

        self.use_pattern          = False    # accept if No pattern matching
        self.accept_unmatch       = False    # accept if No pattern matching
        self.masks                = []       # All the masks (accept and reject)
        self.currentDir           = '.'      # mask directory (if needed)
        self.currentFileOption    = None     # should implement metpx like stuff

        self.log_exchange         = 'xlog'
        # 

        # publish
        self.document_root        = None
        self.post_document_root   = None
        self.url                  = None

        #self.broker              = urllib.parse.urlparse('amqp://guest:guest@localhost/')
        #self.exchange            = None
        #self.topic_prefix        = 'v02.post'
        #self.subtopic            = None

        self.to_clusters          = None
        self.parts                = '1'
        self.sumflg               = 'd'

        self.rename               = None
        self.flow                 = None
        self.events               = 'IN_CLOSE_WRITE|IN_DELETE'
        self.event                = 'IN_CLOSE_WRITE|IN_ATTRIB|IN_MOVED_TO|IN_MOVE_SELF'

        self.randomize            = False
        self.reconnect            = False

        self.partflg              = '1'
        #

        self.destination          = None

        # subscribe

        self.discard              = False
        self.flatten              = '/'
        self.log_back             = True

        self.recursive            = False

        self.post_broker          = urllib.parse.urlparse('amqp://guest:guest@localhost/')
        self.post_exchange        = None

        self.source               = None
        self.source_from_exchange = False

        # general cluster stuff
        self.cluster              = None
        self.cluster_aliases      = []
        self.gateway_for          = []

        self.sleep                = 0
        self.strip                = 0

        self.blocksize            = 0

        self.do_download          = None
        self.do_poll              = None
        self.on_file              = None
        self.on_line              = None
        self.on_message           = None
        self.on_part              = None
        self.on_post              = None

        self.inplace              = False

        self.lock                 = None
        self.chmod                = 775

        self.notify_only          = False

        # 2 object not to reset in child
        if not hasattr(self,'logpath') :
           self.logpath           = None
        if not hasattr(self,'instance') :
           self.instance          = 0
        self.no                   = -1
        self.nbr_instances        = 1


        self.mirror               = True

        self.overwrite            = False
        self.recompute_chksum     = False

        self.interface            = None
        self.vip                  = None


    def execfile(self, opname, path):

        ok,script = self.config_path('scripts',path)
        self.logger.info("installing script %s " % script ) 

        try    : 
                 exec(compile(open(script).read(), script, 'exec'))
        except : 
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s" % (stype, svalue))
                 self.logger.error("for option %s script %s did not work" % (opname,path))

    def general(self):
        self.logger.debug("sr_config general")

        # state variables that need to be reinitialized

        self.bindings             = []     
        self.masks                = []       
        self.currentDir           = '.'      
        self.currentFileOption    = 'WHATFN' 

        # read in provided credentials
        credent = self.user_config_dir + os.sep + 'credentials.conf'
        self.credentials.read(credent)

        # read in provided rabbit users
        users = self.user_config_dir + os.sep + 'users.conf'
        try :
              # users file is not mandatory
              if os.path.exists(users):
                 f = open(users,'r')
                 lines = f.readlines()
                 f.close
                 for line in lines :
                     line = line.strip()
                     if len(line) == 0 or line[0] == '#' : continue
                     parts = line.split()
                     user  = parts[0]
                     roles = line.replace(user,'').lower().strip()
                     self.users[user] = roles

        except : 
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s" % (stype, svalue))
        self.logger.debug("users = %s\n" % self.users)

        # read in provided log cluster infos
        log_cluster = self.user_config_dir + os.sep + 'log2clusters.conf'
        i = 0
        try :
              if os.path.exists(log_cluster):
                 f = open(log_cluster,'r')
                 lines = f.readlines()
                 f.close
                 for line in lines :
                     line = line.strip()
                     if len(line) == 0 or line[0] == '#' : continue
                     parts = line.split()
                     name    = parts[0]
                     urlstr  = parts[1]
                     ok, url = self.validate_urlstr(urlstr)
                     if not ok or not url.scheme in ['amqp','amqps']:
                        self.logger.error("problem with %s" % parts[1])
                     # fixme parts[2] exchange should be optional
                     exch  = parts[2]
                     self.log_clusters[i] = (name,url,exch)
                     i = i + 1

        # cluster file is not mandatory
        except : 
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s" % (stype, svalue))
        self.logger.debug("log_clusters = %s\n" % self.log_clusters)

        # defaults.conf ... defaults for the server
        defconf = self.user_config_dir + os.sep + 'default.conf'
        self.logger.debug("defconf = %s\n" % defconf)
        if os.path.isfile(defconf) : self.config(defconf)

    def has_vip(self): 

        # no vip given... so should not matter ?
        if self.vip == None or self.interface == None :
           self.logger.error("option vip or interface missing...")
           sys.exit(1)
           return False

        a = netifaces.ifaddresses(self.interface)
        if netifaces.AF_INET in a :
           for inet in a[netifaces.AF_INET]:
               if 'addr' in inet :
                   if inet['addr'] == self.vip :
                      return True

        return False


    def isMatchingPattern(self, str, accept_unmatch = False): 

        for mask in self.masks:
            self.logger.debug(mask)
            pattern, maskDir, maskFileOption, mask_regexp, accepting = mask
            if mask_regexp.match(str) :
               self.currentDir        = maskDir
               self.currentFileOption = maskFileOption
               return accepting

        return accept_unmatch

    def isTrue(self,S):
        s = S.lower()
        if  s == 'true' or s == 'yes' or s == 'on' or s == '1': return True
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

                     self.masks.append((pattern, self.currentDir, self.currentFileOption, mask_regexp, accepting))
                     self.logger.debug("Masks")
                     self.logger.debug("Masks %s"% self.masks)

                elif words[0] in ['accept_unmatch','-au','--accept_unmatch']:
                     if words[0][0:1] == '-' : 
                        self.accept_unmatch = True
                        n = 1
                     else :
                        self.accept_unmatch = self.isTrue(words[1])
                        n = 2

                # admin: suppose to appear directly under the broker declaration
                # of the default manager account of the cluster in defaults.conf
                elif words[0] in ['admin','-admin','--admin']:
                     admin_user  = words[1]
                     manager_str = self.manager.geturl()
                     user_pass   = self.manager.username+':'+self.manager.password
                     admin_str   = manager_str.replace(user_pass,admin_user)
                     ok, url     = self.validate_urlstr(admin_str)
                     self.admin  = url
                     if not ok or not url.scheme in ['amqp','amqps']:
                        self.logger.error("problem with admin (%s)" % admin_str)
                        needexit = True
                     n = 2

                elif words[0] in ['manager','-manager','--manager'] :
                     urlstr       = words[1]
                     ok, url      = self.validate_urlstr(urlstr)
                     self.manager = url
                     if not ok or not url.scheme in ['amqp','amqps']:
                        self.logger.error("problem with manager (%s)" % urlstr)
                        needexit = True
                     n = 2

                elif words[0] in ['discard','-d','--discard','--download-and-discard']:
                     self.discard = self.isTrue(words[1])
                     n = 2

                elif words[0] == 'directory':
                     self.currentDir = words[1]

                elif words[0] == 'filename':
                     self.currentFileOption = words[1]

                # like accept... make more sense when poll...
                if   words[0] == 'get':
                     accepting   = True
                     pattern     = words[1]
                     mask_regexp = re.compile(pattern)

                     if len(words) > 2: self.currentFileOption = words[2]

                     self.masks.append((pattern, self.currentDir, self.currentFileOption, mask_regexp, accepting))
                     self.logger.debug("Masks")
                     self.logger.debug("Masks %s"% self.masks)

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
                     if sys.platform == 'win32':
                         self.document_root = words[1].replace('\\','/')
                     else:
                         self.document_root = words[1]
                     n = 2

                elif words[0] in ['post_document_root','-pdr','--post_document_root']:
                     if sys.platform == 'win32':
                         self.post_document_root = words[1].replace('\\','/')
                     else:
                         self.post_document_root = words[1]
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

                elif words[0] in ['filename','-filename','--filename']:
                     self.currentFileOption = words[1]
                     n = 2

                elif words[0] in ['help','-h','-help','--help']:
                     self.help()
                     needexit = True

                elif words[0] in ['lock','-lk','--lock']:
                     self.lock = words[1] 
                     n = 2

                elif words[0] in ['chmod','-chmod','--chmod']:
                     self.chmod = int(words[1])
                     n = 2

                elif words[0] in ['log','-l','-log','--log']:
                     self.logpath = words[1]
                     n = 2

                elif words[0] in ['log_back','-lb','--log_back']:
                     self.log_back = self.isTrue(words[1])
                     n = 2

                elif words[0] in ['logrotate','-lr','--logrotate']:
                     self.logrotate = int(words[1])
                     n = 2

                elif words[0] in ['inplace','-in','--inplace']:
                     self.inplace = self.isTrue(words[1])
                     n = 2

                elif words[0] in ['instances','-i','--instances']:
                     self.nbr_instances = int(words[1])
                     n = 2

                elif words[0] in ['--no']:
                     self.no = int(words[1])
                     n = 2

                elif words[0] in ['interface','-interface','--interface']:
                     self.interface = words[1]
                     n = 2

                elif words[0] in ['notify_only','-n','--notify_only','--no-download']:
                     self.notify_only = True
                     n = 1

                elif words[0] in ['do_download','-do_download','--do_download']:
                     self.on_file = None
                     self.execfile("do_download",words[1])
                     if self.do_download == None :
                        self.logger.error("do_download script incorrect (%s)" % words[1])
                        ok = False
                     n = 2

                elif words[0] in ['on_file','-on_file','--on_file']:
                     self.on_file = None
                     self.execfile("on_file",words[1])
                     if self.on_file == None :
                        self.logger.error("on_file script incorrect (%s)" % words[1])
                        ok = False
                     n = 2

                elif words[0] in ['on_line','-on_line','--on_line']:
                     self.on_line = None
                     self.execfile("on_line",words[1])
                     if self.on_line == None :
                        self.logger.error("on_line script incorrect (%s)" % words[1])
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

                elif words[0] in ['do_poll','-do_poll','--do_poll']:
                     self.do_poll = None
                     self.execfile("do_poll",words[1])
                     if self.do_poll == None :
                        self.logger.error("do_poll script incorrect (%s)" % words[1])
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
                     urlstr      = words[1]
                     ok, url     = self.validate_urlstr(urlstr)
                     self.broker = url
                     if not ok or not url.scheme in ['amqp','amqps']:
                        self.logger.error("problem with broker (%s)" % urlstr)
                        needexit = True
                     n = 2

                elif words[0] in ['destination','-destination','--destination'] :
                     urlstr           = words[1]
                     ok, url          = self.validate_urlstr(urlstr)
                     self.destination = words[1]
                     if not ok :
                        self.logger.error("problem with destination (%s)" % urlstr)
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
                     key = self.topic_prefix + '.' + self.subtopic
                     self.bindings.append( (self.exchange,key) )
                     self.logger.debug("BINDINGS")
                     self.logger.debug("BINDINGS %s"% self.bindings)
                     n = 2

                elif words[0] in ['overwrite','-o','--overwrite'] :
                     self.overwrite = self.isTrue(words[1])
                     n = 2

                elif words[0] in ['queue_name','-qn','--queue_name'] :
                     self.queue_name = words[1]
                     n = 2

                elif words[0] in ['queue_share','-qs','--queue_share'] :
                     if words[0][0:1] == '-' : 
                        self.queue_share = True
                        n = 1
                     else :
                        self.queue_share = self.isTrue(words[1])
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

                elif words[0] in ['post_broker','-pb','--post_broker'] :
                     urlstr      = words[1]
                     ok, url     = self.validate_urlstr(urlstr)
                     self.post_broker = url
                     if not ok or not url.scheme in ['amqp','amqps']:
                        self.logger.error("problem with post_broker (%s)" % urlstr)
                        needexit = True
                     n = 2

                elif words[0] in ['post_exchange','-pe','--post_exchange']:
                     self.post_exchange = words[1]
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
                self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
                self.logger.error("problem with option %s" % words[0])

        if needexit :
           sys.exit(1)

        return n

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
        self.handler = logging.handlers.TimedRotatingFileHandler(self.lpath, when='midnight', \
                       interval=1, backupCount=self.logrotate)
        fmt          = logging.Formatter( LOG_FORMAT )
        self.handler.setFormatter(fmt)

        del self.logger

        self.logger = logging.RootLogger(logging.WARNING)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

        if self.debug :
           self.logger.setLevel(logging.DEBUG)

    # check url and add credentials if needed from credential file

    def validate_urlstr(self,urlstr):

        ok, details = self.credentials.get(urlstr)
        if details == None :
           self.logger.error("credential problem with %s"% urlstr)
           return False, urllib.parse.urlparse(urlstr)

        return True, details.url


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
       cfg = sr_config(None,None)
    elif os.path.isfile(sys.argv[1]):
       args = None
       if len(sys.argv) > 2 : args = sys.argv[2:]
       cfg = sr_config(sys.argv[1],args)
    else :
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
    cfg.logger.debug("user_queue_dir = %s"  % cfg.user_queue_dir)
    cfg.general()
    cfg.args(cfg.user_args)
    cfg.config(cfg.user_config)
    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
