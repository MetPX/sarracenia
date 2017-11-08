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
import inspect
import netifaces
import os,re,socket,sys,random
import urllib,urllib.parse
from   appdirs import *
import shutil
import sarra

try   : import amqplib.client_0_8 as amqp
except: pass

try   : import pika
except: pass

import paramiko
from   paramiko import *

try :
         from sr_credentials       import *
         from sr_util              import *
except : 
         from sarra.sr_credentials import *
         from sarra.sr_util        import *

class sr_config:

    def __init__(self,config=None,args=None,action=None):
        if '-V' in sys.argv :
           print("Version %s" % sarra.__version__ )
           os._exit(0)


        # package_dir     = where sarra is installed on system
        # appdirs setup... on linux it gives :
        # site_data_dir   = /usr/share/default/sarra   ** unused
        # user_data_dir   = ~/.local/share/sarra       ** unused
        #
        # site_config_dir = /etc/xdg/xdg-default/sarra
        # user_cache_dir  = ~/.cache/sarra
        # user_log_dir    = ~/.cache/sarra/var/log
        # user_config_dir = ~/.config/sarra

        self.action           = action
         
        self.appname          = 'sarra'
        self.appauthor        = 'science.gc.ca'

        self.package_dir      = os.path.dirname(inspect.getfile(sr_credentials))
        self.site_config_dir  = site_config_dir(self.appname,self.appauthor)
        self.user_config_dir  = user_config_dir(self.appname,self.appauthor)
        self.user_log_dir     = user_log_dir   (self.appname,self.appauthor)
        self.user_old_log_dir     = self.user_log_dir.replace(os.sep+'log',os.sep+'var'+os.sep+'log')
        self.user_plugins_dir = self.user_config_dir + '/plugins'
        self.http_dir         = self.user_config_dir + '/Downloads'

        # umask change for directory creation and chmod
        # 2017/06/20- FIXME commenting this out, because it seems wrong!... why override umask?
        #try    : os.umask(0)
        #except : pass

        # FIXME:
        # before 2.16.08x sr_log was a comment (that became sr_report). so the log directory was needed
        # to store configuration states.  The actual log file directory was moved under 'var/' to put
        # it out of the way.  in newer versions, the state directory for sr_report became 'reports',
        # so it is possible to have log used for the normal purpose.
        #
        # For existing configurations, if ~/.cache/sarra/var/log exists, move it to ~/.cache/sarra/log
        # so everything still works, move the old var out of the way (to var.old.)
        # and create var as a symbolic link to '.' so that var/log still works.
        # this code should be removed once all users are past the transition.
        #
        var = user_cache_dir(self.appname,self.appauthor) + "/var"
        if os.path.isdir( var ) and not os.path.islink( var ):
              print("sr_config __init__ migrating logs to new location (without 'var')")
              if os.path.isdir( self.user_log_dir ): 
                 print("sr_config __init__ moving old sr_log state directory out of the way to .old")
                 os.rename( self.user_log_dir, self.user_log_dir.replace("/log", "/log.old" ))            
              print("sr_config __init__ moving old log file directory the new location %s " % self.user_log_dir )
              shutil.move( self.user_old_log_dir, self.user_log_dir)
              print("sr_config __init__ moving old var directory out of the way to %s.old" % ( var ) )
              os.rename( var, var + ".old" )
              if sys.platform != 'win32' :
                 print("sr_config __init__ create var symlink so no scripts need to be change for now. ")
                 os.symlink( "." , var )


        try    : os.makedirs(self.user_config_dir, 0o775,True)
        except : pass
        try    : os.makedirs(self.user_plugins_dir,0o775,True)
        except : pass
        try    : os.makedirs(self.http_dir,        0o775,True)
        except : pass

        # hostname

        self.hostname  = socket.getfqdn()

        # logging is interactive at start

        self.debug     = False
        self.statehost = False
        self.hostform  = 'short'
        self.loglevel  = logging.INFO

        #self.debug    = True
        #self.loglevel = logging.DEBUG

        self.LOG_FORMAT= ('%(asctime)s [%(levelname)s] %(message)s')
        logging.basicConfig(level=self.loglevel, format = self.LOG_FORMAT )
        self.logger = logging.getLogger()
        self.logger.debug("sr_config __init__")

        # program_name

        self.program_name = re.sub(r'(-script\.pyw|\.exe|\.py)?$', '', os.path.basename(sys.argv[0]) )
        self.program_dir  = self.program_name[3:]
        self.logger.debug("sr_config program_name %s " % self.program_name)

        # config

        self.config_dir    = ''
        self.config_name   = None
        self.user_config   = config
        self.remote_config = False

        # config might be None ... in some program or if we simply instantiate a class
        # but if it is not... it better be an existing file

        if config != None :
           cdir = os.path.dirname(config)
           if cdir and cdir != '' : self.config_dir = cdir.split(os.sep)[-1]
           self.config_name = re.sub(r'(\.conf)','',os.path.basename(config))
           ok, self.user_config = self.config_path(self.program_dir,config)
           if ok :
              cdir = os.path.dirname(self.user_config)
              if cdir and cdir != '' : self.config_dir = cdir.split(os.sep)[-1]
           self.logger.debug("sr_config config_dir   %s " % self.config_dir  ) 
           self.logger.debug("sr_config config_name  %s " % self.config_name ) 
           self.logger.debug("sr_config user_config  %s " % self.user_config ) 

        # build user_cache_dir/program_name/[config_name|None] and make sure it exists

        self.user_cache_dir  = user_cache_dir (self.appname,self.appauthor)
        self.user_cache_dir += os.sep + self.program_name.replace('sr_','')
        self.user_cache_dir += os.sep + "%s" % self.config_name
        # user_cache_dir will be created later in configure()

        # keep a list of extended options

        self.extended_options = []
        self.known_options    = []


        # check arguments

        if args == [] : args = None
        self.user_args       = args

    def args(self,args):
        """

        given the command line arguments look for options, and parse them.  When they are over, 

        for use by sr_post:
        set first_arg  to be the index of the first command line argument that isn't an option.
        for sr_post the files to post are sys.argv[self.first_arg:] 

        """

        self.logger.debug("sr_config args")

        if args == None : return

        # on command line opition starts with - or --
        i = 0
        self.first_arg=0
        while i < len(args):
              n = 1
              if args[i][0] == '-' :
                 n = self.option(args[i:])
                 if n == 0 : n = 1
              elif self.first_arg == 0:
                 self.first_arg=i+1
              i = i + n

    def check(self):
        self.logger.debug("sr_config check")

    def check_extended(self):
        self.logger.debug("sr_config check_extended")

        ok = True
        for option in self.extended_options :
            if option in self.known_options : continue
            value=getattr(self,option)
            self.logger.warning("extended option %s = %s (unknown or not declared)" % (option,value) ) 
            ok = False

        return ok

    def chunksize_from_str(self,str_value):
        self.logger.debug("sr_config chunksize_from_str %s" % str_value)
        factor = 1
        if str_value[-1] in 'bB'   : str_value = str_value[:-1]
        if str_value[-1] in 'kK'   : factor = 1024
        if str_value[-1] in 'mM'   : factor = 1024 * 1024
        if str_value[-1] in 'gG'   : factor = 1024 * 1024 * 1024
        if str_value[-1] in 'tT'   : factor = 1024 * 1024 * 1024 * 1024
        if str_value[-1].isalpha() : str_value = str_value[:-1]
        chunksize = int(str_value) * factor

        return chunksize

    def config(self,path):
        self.logger.debug("sr_config config component is: %s" % self.program_name )
        self.logger.debug("sr_config %s" % path)
        self.logger.debug("action    %s" % self.action)

        if path        == None  : return
        if self.action == 'edit': return

        try:
            f = open(path, 'r')
            for line in f.readlines():
                words = line.split()
                if (len(words) >= 1 and not re.compile('^[ \t]*#').search(line)):
                    self.option(words)
            f.close()

        except:
            (stype, svalue, tb) = sys.exc_info()
            self.logger.error("Type: %s, Value: %s" % (stype, svalue))

    def config_path(self,subdir,config, mandatory=True, ctype='conf'):
        self.logger.debug("config_path = %s %s" % (subdir,config))

        if config == None : return False,None

        # priority 1 : config given is a valid path

        self.logger.debug("config_path %s " % config )
        if os.path.isfile(config) :
           return True,config

        config_file = os.path.basename(config)
        config_name = re.sub(r'(\.inc|\.conf|\.py)','',config_file)
        ext         = config_file.replace(config_name,'')
        if ext == '': ext = '.' + ctype

        # priority 1.5: config file given without extenion...
        config_path = config_name + ext
        if os.path.isfile(config_path) :
           return True,config_path

        # priority 2 : config given is a user one

        config_path = self.user_config_dir + os.sep + subdir + os.sep + config_name + ext
        self.logger.debug("config_path %s " % config_path )

        if os.path.isfile(config_path) :
           return True,config_path

        # priority 3 : config given to site config

        config_path = self.site_config_dir + os.sep + subdir + os.sep + config_name + ext
        self.logger.debug("config_path %s " % config_path )

        if os.path.isfile(config_path) :
           return True,config_path

        # priority 4 : plugins

        if subdir == 'plugins' :
           config_path = self.package_dir + os.sep + 'plugins' + os.sep + config_name + ext
           self.logger.debug("config_path %s " % config_path )
           if os.path.isfile(config_path) :
              return True,config_path

        # priority 5 : if remote_config enabled, check at given remote_config_url[]

        if self.remote_config :
           wconfig = self.wget(config)
           if wconfig != None :
              self.logger.debug("config = %s" % wconfig)
              return True, wconfig

        # return bad file ... 
        if mandatory :
          if subdir == 'plugins' :     self.logger.error("script not found %s" % config)
          elif self.action != 'edit' : self.logger.error("file not found %s" % config)
          if config == None : return False,None
          #os._exit(1)

        return False,config

    def configure(self):
        self.logger.debug("configure")
        
        # on reload : get rid of extended options... because they are lists

        self.logger.debug("clearing out extended options")
        for opt in self.extended_options :
            if hasattr(self,opt): delattr (self,opt)

        self.extended_options = []
        self.known_options    = []

        # go through normal configuration

        self.defaults()
        self.general()

        self.overwrite_defaults()

        # load/reload all config settings

        self.args   (self.user_args)
        self.config (self.user_config)

        # configure some directories if statehost was set

        self.configure_statehost()

        # verify / complete settings

        if not self.action in ['add','disable','edit','enable','list','log','remove' ]  :
           self.check()

        # check extended options

        self.check_extended()


    def configure_statehost(self):
        self.logger.debug("configure_statehost")

        hostdir = None

        # user asked for statehost

        if self.statehost :
           hostdir = self.hostname
           if self.hostform == 'short' : hostdir = self.hostname.split('.')[0] 

        # finalize user_log_dir

        if hostdir and not hostdir in self.user_log_dir :
           self.user_log_dir = self.user_log_dir[:-4] + os.sep + hostdir + '/log'

        # create user_log_dir 

        self.logger.debug("sr_config user_log_dir  %s " % self.user_log_dir ) 
        try    : os.makedirs(self.user_log_dir, 0o775,True)
        except : pass

        # finalize user_cache_dir

        if hostdir and not hostdir in self.user_cache_dir :
           self.user_cache_dir  = user_cache_dir (self.appname,self.appauthor)
           self.user_cache_dir += os.sep + hostdir
           self.user_cache_dir += os.sep + self.program_name.replace('sr_','')
           self.user_cache_dir += os.sep + "%s" % self.config_name

        # create user_cache_dir

        if not self.program_name in [ 'sr', 'sr_config' ]:
           self.logger.debug("sr_config user_cache_dir  %s " % self.user_cache_dir ) 
           try    : os.makedirs(self.user_cache_dir,  0o775,True)
           except : pass

    def declare_option(self,option):
        self.logger.debug("sr_config declare_option")
        self.known_options.append(option)

    def defaults(self):
        self.logger.debug("sr_config defaults")

        # IN BIG DEBUG
        #self.debug = True
        self.debug                = False

        self.remote_config        = False
        self.remote_config_url    = []

        self.heartbeat            = 300
        self.last_heartbeat       = time.time()

        self.loglevel             = logging.INFO
        self.logrotate            = 5
        self.report_daemons          = False

        self.bufsize              = 8192
        self.kbytes_ps            = 0

        self.sumalgo              = None
        self.lastflg              = None
        self.set_sumalgo('d')

        self.admin                = None
        self.manager              = None

        # consumer
        self.attempts             = 3   # number of times to attempt downloads.
        self.broker               = urllib.parse.urlparse('amqp://guest:guest@localhost/')
        self.bindings             = []
        self.exchange             = None
        self.exchanges            = [ 'xlog', 'xpublic', 'xreport', 'xwinnow' ]
        self.topic_prefix         = 'v02.post'
        self.subtopic             = None

        self.queue_name           = None
        self.queue_suffix         = None
        self.durable              = False
        self.expire               = 1000 *60 * 5  # 5 mins = 1000millisec * 60s * 5m 
        self.reset                = False
        self.message_ttl          = None
        self.prefetch             = 1
        self.max_queue_size       = 25000
        self.set_passwords        = True

        self.use_pattern          = False    # accept if No pattern matching
        self.accept_unmatch       = False    # accept if No pattern matching
        self.masks                = []       # All the masks (accept and reject)
        self.currentPattern       = None     # defaults to all
        self.currentDir           = os.getcwd()   # mask directory (if needed)
        self.currentFileOption    = None     # should implement metpx like stuff
        self.delete               = False

        self.report_exchange      = 'xreport'
          
        # amqp

        self.use_pika             = 'pika' in sys.modules

        # cache
        self.cache                = None
        self.caching              = False
        self.cache_stat           = False

        # save/restore
        self.save_fp              = None
        self.save_count           = 1

        # new set
        self.base_dir             = None
        self.post_base_dir        = None
        self.post_base_url        = None

        # deprecated set
        self.document_root        = None
        self.post_document_root   = None
        self.url                  = None

        self.postpath             = []
        self.movepath             = []

        #self.broker              = urllib.parse.urlparse('amqp://guest:guest@localhost/')
        #self.exchange            = None
        #self.topic_prefix        = 'v02.post'
        #self.subtopic            = None

        self.to_clusters          = None
        self.parts                = None
        self.sumflg               = 'd'

        self.rename               = None

        self.headers_to_add       = {}
        self.headers_to_del       = []

        #

        self.batch                = 100

        self.chmod                = 0o0   # Peter changed this to 0, so umask can be used. July 2017.
        self.chmod_dir            = 0o775 # added by Murray Rennie May 17, 2016
        self.chmod_log            = 0o600 
        self.cluster              = None
        self.cluster_aliases      = []

        self.destination          = None
        self.discard              = False

        self.events               = 'create|delete|link|modify'
        self.event                = 'create|delete|modify'

        self.flatten              = '/'
        self.follow_symlinks      = False
        self.force_polling        = False

        self.gateway_for          = []
        self.mirror               = False

        self.partflg              = '0'
        self.pipe                 = False
        self.post_broker          = urllib.parse.urlparse('amqp://guest:guest@localhost/')
        self.post_exchange        = None
        self.post_exchange_split  = 0
        self.preserve_mode        = True
        self.preserve_time        = True
        self.pump_flag            = False

        self.randomize            = False
        self.realpath             = False
        self.reconnect            = False
        self.reportback           = True
        self.restore              = False
        self.restore_queue        = None

        self.save                 = False
        self.save_file            = None
        self.sleep                = 0
        self.strip                = 0
        self.pstrip               = None
        self.source               = None
        self.source_from_exchange = False

        self.timeout              = None
        self.users                = {}
        self.users_flag           = False

        self.blocksize            = 0

        self.destfn_script        = None
        self.do_download          = None
        self.do_poll              = None
        self.do_send              = None

        self.inplace              = False

        self.inflight             = None

        self.notify_only          = False

        # 2 object not to reset in child
        if not hasattr(self,'logpath') :
           self.logpath           = None
        if not hasattr(self,'instance') :
           self.instance          = 0
        self.no                   = -1
        self.nbr_instances        = 1



        self.overwrite            = False
        self.recompute_chksum     = False

        self.interface            = None
        self.vip                  = None

        # Plugin defaults

        self.execfile("on_message",'msg_log')
        self.on_message_list = [ self.on_message ]
        self.execfile("on_file",'file_log')
        self.on_file_list = [ self.on_file ]
        self.execfile("on_post",'post_log')
        self.on_post_list = [ self.on_post ]

        self.execfile("on_heartbeat",'heartbeat_log')
        self.on_heartbeat_list    = [self.on_heartbeat]

        self.execfile("on_html_page",'html_page')
        self.on_html_page_list    = [self.on_html_page]

        self.on_part              = None
        self.on_part_list         = []

        self.do_task              = None
        self.do_task_list         = []

        self.on_post_list = [ self.on_post ]
        self.execfile("on_line",'line_mode')
        self.on_line_list = [ self.on_line ]

        self.on_watch             = None
        self.on_watch_list        = []

    def duration_from_str(self,str_value,setting_units='s'):
        self.logger.debug("sr_config duration_from_str %s unit %s" % (str_value,setting_units))

        # str_value should be expressed in secs 
        # unit is used to initialise the factor (ex: 's': factor = 1  'ms' : factor = 1000 )

        factor    = 1

        # most settings are in sec (or millisec)
        if setting_units[-1] == 's' :
           if setting_units == 'ms'   : factor = 1000
           if str_value[-1] in 'sS'   : factor *= 1
           if str_value[-1] in 'mM'   : factor *= 60
           if str_value[-1] in 'hH'   : factor *= 60 * 60
           if str_value[-1] in 'dD'   : factor *= 60 * 60 * 24
           if str_value[-1] in 'wW'   : factor *= 60 * 60 * 24 * 7
           if str_value[-1].isalpha() : str_value = str_value[:-1]

        elif setting_units == 'd'     :
           if str_value[-1] in 'dD'   : factor *= 1
           if str_value[-1] in 'wW'   : factor *= 7
           if str_value[-1].isalpha() : str_value = str_value[:-1]

        duration = float(str_value) * factor

        return duration


    def execfile(self, opname, path):

        setattr(self,opname,None)

        if path == 'None' or path == 'none' or path == 'off':
             self.logger.debug("Reset plugin %s to None" % opname ) 
             return

        ok,script = self.config_path('plugins',path,mandatory=True,ctype='py')
        if ok:
             self.logger.debug("installing %s plugin %s" % (opname, script ) ) 
        else:
             self.logger.error("installing %s plugin %s failed: not found " % (opname, path) ) 

        try    : 
            exec(compile(open(script).read(), script, 'exec'))
        except : 
            (stype, svalue, tb) = sys.exc_info()
            self.logger.error("Type: %s, Value: %s" % (stype, svalue))
            self.logger.error("for option %s plugin %s did not work" % (opname,path))

        if getattr(self,opname) is None:
            self.logger.error("%s plugin %s incorrect: does not set self.%s" % (opname, path, opname ))


    def heartbeat_check(self):
        now    = time.time()
        elapse = now - self.last_heartbeat
        if elapse > self.heartbeat :
           self.__on_heartbeat__()
           self.last_heartbeat = now

    def __on_heartbeat__(self):
        self.logger.debug("__on_heartbeat__")

        # invoke on_hearbeat when provided
        for plugin in self.on_heartbeat_list:
           if not plugin(self): return False

        return True



    def general(self):
        self.logger.debug("sr_config general")

        # read in provided credentials
        credent = self.user_config_dir + os.sep + 'credentials.conf'
        self.cache_url   = {}
        self.credentials = sr_credentials(self.logger)
        self.credentials.read(credent)

        defconf     = self.user_config_dir + os.sep + 'default.conf'
        self.logger.debug("defconf = %s\n" % defconf)

        if os.path.isfile(defconf) : 
           config_dir       = self.config_dir
           self.config_dir  = ''
           self.config(defconf)
           self.config_dir  = config_dir

        adminconf   = self.user_config_dir + os.sep + 'admin.conf'
        self.logger.debug("adminconf = %s\n" % adminconf)

        if os.path.isfile(adminconf) : 
           config_dir       = self.config_dir
           self.config_dir  = ''
           self.config(adminconf)
           self.config_dir  = config_dir

    def has_vip(self): 

        # no vip given... standalone always has vip.
        if self.vip == None: 
           return True

        for i in netifaces.interfaces():
            for a in netifaces.ifaddresses(i):
                if self.vip in netifaces.ifaddresses(i)[a][0].get('addr'):
                   return True
        return False
 
    def isMatchingPattern(self, chaine, accept_unmatch = False): 

        for mask in self.masks:
            self.logger.debug(mask)
            pattern, maskDir, maskFileOption, mask_regexp, accepting = mask
            if mask_regexp.match(chaine) :
               if not accepting : return False
               self.currentPattern    = pattern
               self.currentDir        = maskDir
               self.currentFileOption = maskFileOption
               self.currentRegexp     = mask_regexp
               return True

        return accept_unmatch

    def isTrue(self,S):
        s = S.lower()
        if  s == 'true' or s == 'yes' or s == 'on' or s == '1': return True
        return False

    def isNone(self,S):
        s = S.lower()
        if  s == 'false' or s == 'none' or s == 'off' or s == '0': return True
        return False

    # modified from metpx SenderFTP
    def sundew_basename_parts(self,basename):

        if self.currentPattern == None : return []
        parts = re.findall( self.currentPattern, basename )
        if len(parts) == 2 and parts[1] == '' : parts.pop(1)
        if len(parts) != 1 : return None

        lst = []
        if isinstance(parts[0],tuple) :
           lst = list(parts[0])
        else:
          lst.append(parts[0])

        return lst

    # from metpx SenderFTP
    def sundew_dirPattern(self,urlstr,basename,destDir,destName) :
        """
        does substitutions for patterns in directories.

        FIXME: destName not used?
        """
        BN = basename.split(":")
        EN = BN[0].split("_")

        BP = self.sundew_basename_parts(urlstr)

        ndestDir = ""
        DD = destDir.split("/")
        for  ddword in DD :
             if ddword == "" : continue

             nddword = ""
             DW = ddword.split("$")
             for dwword in DW :
                 nddword += self.sundew_matchPattern(BN,EN,BP,dwword,dwword)

             ndestDir += "/" + nddword 

        return ndestDir

    def sundew_getDestInfos(self, filename):
        """
        modified from sundew client

        WHATFN         -- First part (':') of filename 
        HEADFN         -- Use first 2 fields of filename
        NONE           -- Use the entire filename
        TIME or TIME:  -- TIME stamp appended
        DESTFN=fname   -- Change the filename to fname

        ex: mask[2] = 'NONE:TIME'
        """
        if self.currentFileOption == None : return filename
        timeSuffix   = ''
        satnet       = ''
        parts        = filename.split(':')
        firstPart    = parts[0]

        if 'sundew_extension' in self.msg.headers.keys() :
           parts = [ parts[0] ] + self.msg.headers[ 'sundew_extension' ].split(':')
           filename = ':'.join(parts)

        destFileName = filename

        for spec in self.currentFileOption.split(':'):
            if spec == 'WHATFN':
                destFileName =  firstPart
            elif spec == 'HEADFN':
                headParts = firstPart.split('_')
                if len(headParts) >= 2:
                    destFileName = headParts[0] + '_' + headParts[1] 
                else:
                    destFileName = headParts[0] 
            elif spec == 'SENDER' and 'SENDER=' in filename:
                 i = filename.find('SENDER=')
                 if i >= 0 : destFileName = filename[i+6:].split(':')[0]
                 if destFileName[-1] == ':' : destFileName = destFileName[:-1]
            elif spec == 'NONE':
                 if 'SENDER=' in filename:
                     i = filename.find('SENDER=')
                     destFileName = filename[:i]
                 else :
                     if len(parts) >= 6 :
                        # PX default behavior : keep 6 first fields
                        destFileName = ':'.join(parts[:6])
                        #  PDS default behavior  keep 5 first fields
                        if len(parts[4]) != 1 : destFileName = ':'.join(parts[:5])
                 # extra trailing : removed if present
                 if destFileName[-1] == ':' : destFileName = destFileName[:-1]
            elif spec == 'NONESENDER':
                 if 'SENDER=' in filename:
                     i = filename.find('SENDER=')
                     j = filename.find(':',i)
                     destFileName = filename[:i+j]
                 else :
                     if len(parts) >= 6 :
                        # PX default behavior : keep 6 first fields
                        destFileName = ':'.join(parts[:6])
                        #  PDS default behavior  keep 5 first fields
                        if len(parts[4]) != 1 : destFileName = ':'.join(parts[:5])
                 # extra trailing : removed if present
                 if destFileName[-1] == ':' : destFileName = destFileName[:-1]
            elif re.compile('SATNET=.*').match(spec):
                 satnet = ':' + spec
            elif re.compile('DESTFN=.*').match(spec):
                 destFileName = spec[7:]
            elif re.compile('DESTFNSCRIPT=.*').match(spec):
                 old_destfn_script  = self.destfn_script
                 saved_new_file    = self.new_file
                 self.new_file   = destFileName
                 self.destfn_script = None
                 script = spec[13:]
                 self.execfile('destfn_script',script)
                 if self.destfn_script != None :
                    ok = self.destfn_script(self)
                 destFileName       = self.new_file
                 self.destfn_script = old_destfn_script
                 self.new_file   = saved_new_file
                 if destFileName == None : destFileName = old_destFileName
            elif spec == 'TIME':
                if destFileName != filename :
                   timeSuffix = ':' + time.strftime("%Y%m%d%H%M%S", time.gmtime())
                   # check for PX or PDS behavior ... if file already had a time extension keep his...
                   if parts[-1][0] == '2' : timeSuffix = ':' + parts[-1]
            else:
                self.logger.error("Don't understand this DESTFN parameter: %s" % spec)
                return (None, None) 
        return destFileName + satnet + timeSuffix

    # modified from metpx SenderFTP
    def sundew_matchPattern(self,BN,EN,BP,keywd,defval) :
        if   keywd[:4] == "{T1}"    : return (EN[0])[0:1]   + keywd[4:]
        elif keywd[:4] == "{T2}"    : return (EN[0])[1:2]   + keywd[4:]
        elif keywd[:4] == "{A1}"    : return (EN[0])[2:3]   + keywd[4:]
        elif keywd[:4] == "{A2}"    : return (EN[0])[3:4]   + keywd[4:]
        elif keywd[:4] == "{ii}"    : return (EN[0])[4:6]   + keywd[4:]
        elif keywd[:6] == "{CCCC}"  : return  EN[1]         + keywd[6:]
        elif keywd[:4] == "{YY}"    : return (EN[2])[0:2]   + keywd[4:]
        elif keywd[:4] == "{GG}"    : return (EN[2])[2:4]   + keywd[4:]
        elif keywd[:4] == "{Gg}"    : return (EN[2])[4:6]   + keywd[4:]
        elif keywd[:5] == "{BBB}"   : return (EN[3])[0:3]   + keywd[5:]
        # from pds'datetime suffix... not sure
        elif keywd[:7] == "{RYYYY}" : return (BN[6])[0:4]   + keywd[7:]
        elif keywd[:5] == "{RMM}"   : return (BN[6])[4:6]   + keywd[5:]
        elif keywd[:5] == "{RDD}"   : return (BN[6])[6:8]   + keywd[5:]
        elif keywd[:5] == "{RHH}"   : return (BN[6])[8:10]  + keywd[5:]
        elif keywd[:5] == "{RMN}"   : return (BN[6])[10:12] + keywd[5:]
        elif keywd[:5] == "{RSS}"   : return (BN[6])[12:14] + keywd[5:]

        # Matching with basename parts if given

        if BP != None :
           for i,v in enumerate(BP):
               kw  = '{' + str(i) +'}'
               lkw = len(kw)
               if keywd[:lkw] == kw : return v + keywd[lkw:]

        return defval

    def option(self,words):
        self.logger.debug("sr_config option %s" % words[0])

        # option strip out '-' 

        words0 = words[0].strip('-')

        # value : variable substitutions

        words1 = None
        if len(words) > 1 :
           buser  = ''
           config = ''
           words1 = words[1]

           if self.config_name : config = self.config_name

           # options need to check if there
           if hasattr(self,'broker') and self.broker  : buser  = self.broker.username

           if '$' in words1 :
              words1 = words1.replace('${HOSTNAME}',   self.hostname)
              words1 = words1.replace('${PROGRAM}',    self.program_name)
              words1 = words1.replace('${CONFIG}',     config)
              words1 = words1.replace('${BROKER_USER}',buser)

           if '$' in words1 :
              elst = []
              plst = words1.split('}')
              for parts in plst :
                  try:
                          if '{' in parts : elst.append((parts.split('{'))[1])
                  except: pass
              for e in elst :
                  try:    words1 = words1.replace('${'+e+'}',os.environ.get(e))
                  except: pass

          
        # parsing

        needexit = False
        n        = 0
        try:
                if words0 in ['accept','get','reject']: # See: sr_config.7
                     accepting   = words0 in [ 'accept', 'get' ]
                     pattern     = words1
                     mask_regexp = re.compile(pattern)
                     n = 2

                     if len(words) > 2:
                        save_currentFileOption = self.currentFileOption
                        self.currentFileOption = words[2]
                        n = 3
                     

                     self.masks.append((pattern, self.currentDir, self.currentFileOption, mask_regexp, accepting))

                     if len(words) > 2:
                         self.currentFileOption = save_currentFileOption 

                     self.logger.debug("Masks")
                     self.logger.debug("Masks %s"% self.masks)

                elif words0 in ['accept_unmatched','accept_unmatch','au']: # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.accept_unmatch = True
                        n = 1
                     else :
                        self.accept_unmatch = self.isTrue(words[1])
                        n = 2

                elif words0 in [ 'a', 'action' ]:
                     self.action = words1
                     n = 2

                elif words0 == 'admin': # See: sr_audit.8 
                     urlstr     = words1
                     ok, url    = self.validate_urlstr(urlstr)
                     self.admin = url
                     self.users[url.username] = 'admin'
                     if not ok or not url.scheme in ['amqp','amqps']:
                        self.logger.error("invalid admin URL (%s)" % urlstr)
                        needexit = True
                     n = 2

                elif words0 in [ 'at', 'attempts' ]: # FIXME
                     self.attempts = int(words1)
                     n = 2

                elif words0 == 'batch' : # See: sr_config.7
                     self.batch = int(words[1])
                     n = 2

                elif words0 in ['base_dir','bd']: # See: sr_config.7  for sr_post.1,sarra,sender,watch
                     path = os.path.abspath(words1)
                     if self.realpath:
                         path = os.path.realpath(path)
                     if sys.platform == 'win32':
                         self.base_dir = path.replace('\\','/')
                     else:
                         self.base_dir = path
                     # FIXME MG should we test if directory exists ? and warn if not 
                     n = 2

                elif words0 in ['broker','b'] : # See: sr_consumer.7 ++   fixme: everywhere, perhaps reduce
                     urlstr      = words1
                     ok, url     = self.validate_urlstr(urlstr)
                     self.broker = url
                     if not ok or not url.scheme in ['amqp','amqps']:
                        self.logger.error("invalid broker URL (%s)" % urlstr)
                        needexit = True
                     n = 2

                elif words0 == 'blocksize' :   # See: sr_config.7
                     self.blocksize = self.chunksize_from_str(words[1])
                     if self.blocksize == 1:
                        self.parts   =  '1'
                        ok = self.validate_parts()
                             
                     n = 2

                elif words0 == 'bufsize' :   # See: sr_config.7
                     self.bufsize = int(words[1])
                     n = 2

                elif words0 in [ 'caching', 'cache', 'no_duplicates', 'noduplicates', 'nd', 'suppress_duplicates', 'sd' ] : # See: sr_post.1 sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        #self.caching = True
                        self.caching = 300
                        n = 1
                     else :
                        if words[1].isalpha():
                               self.caching = self.isTrue(words[1])
                               if self.caching : self.caching = 300
                        else :
                               # caching setting is in sec 
                               self.caching = int(self.duration_from_str(words1,'s'))
                               if self.caching <= 0 : self.caching = False
                        n = 2

                elif words0 == 'cache_stat'   : # FIXME! what is this?
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.cache_stat = True
                        n = 1
                     else :
                        self.cache_stat = self.isTrue(words[1])
                        n = 2


                elif words0 in [ 'chmod', 'default_mode', 'dm']:    # See: sr_config.7.rst
                     self.chmod = int(words[1],8)
                     n = 2

                elif words0 in [ 'chmod_dir', 'default_dir_mode', 'ddm' ]:    # See: sr_config.7.rst
                     self.chmod_dir = int(words[1],8)
                     n = 2

                elif words0 in [ 'chmod_log', 'default_log_mode', 'dlm' ]:    
                     self.chmod_log = int(words[1],8)
                     n = 2

                elif words0 in ['cluster','cl','from_cluster','fc']: # See: sr_config.7
                     self.cluster = words1 
                     n = 2

                elif words0 in ['cluster_aliases','ca']: # See: sr_config.7
                     self.cluster_aliases = words1.split(',')
                     n = 2

                elif words0 in ['config','c','include']: # See: sr_config.7
                     ok, include = self.config_path(self.config_dir,words1,mandatory=True,ctype='inc')
                     self.config(include)
                     n = 2

                elif words0 == 'debug': # See: sr_config.7
                     debug = self.debug
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.debug = True
                        n = 1
                     else :
                        self.debug = self.isTrue(words[1])
                        n = 2

                     if self.debug : self.loglevel = logging.DEBUG
                     else:           self.loglevel = logging.INFO

                     if debug != self.debug : self.set_loglevel()

                elif words0 == 'delete': # See: sr_sarra.8
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.delete = True
                        n = 1
                     else :
                        self.delete = self.isTrue(words[1])
                        n = 2

                elif words0 == 'destfn_script': # See: sr_sender(1)
                     self.destfn_script = None
                     self.execfile("destfn_script",words1)
                     if ( self.destfn_script == None ) and not self.isNone(words1):
                        ok = False
                     n = 2

                elif words0 == 'destination' : # See: sr_sender.1
                     urlstr           = words1
                     if words1[-1] != '/': urlstr += '/'   
                     ok, url          = self.validate_urlstr(urlstr)
                     self.destination = words1
                     if not ok :
                        self.logger.error("could not understand destination (%s)" % urlstr)
                        needexit = True
                     n = 2

                elif words0 == 'directory': # See: sr_config.7 
                     self.currentDir = words1.replace('//','/')
                     n = 2

                elif words0 in ['discard','d','download-and-discard']:  # sr_subscribe.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.discard = True
                        n = 1
                     else :
                        self.discard = self.isTrue(words[1])
                        n = 2

                elif words0 in ['document_root','dr']: # See sr_post.1,sarra,sender,watch
                     path = os.path.abspath(words1)
                     if self.realpath:
                         path = os.path.realpath(path)
                     if sys.platform == 'win32':
                         self.document_root = path.replace('\\','/')
                     else:
                         self.document_root = path
                     n = 2

                elif words0 == 'do_download': # See sr_config.7, sr_warra, shovel, subscribe
                     self.execfile("do_download",words1)
                     if ( self.do_download == None ) and not self.isNone(words1):
                        ok = False
                     n = 2

                elif words0 == 'do_task': # See: sr_config.1, others...
                     self.execfile("do_task",words1)
                     if ( self.do_task == None ):
                        if self.isNone(words1):
                           self.do_task_list = []
                        else:
                           ok = False
                           needexit = True
                     else:
                        self.do_task_list.append(self.do_task)
                     n = 2

                elif words0 == 'do_poll': # See sr_config.7 and sr_poll.1
                     self.execfile("do_poll",words1)
                     if ( self.do_poll == None ) and not self.isNone(words1):
                        ok = False
                     n = 2

                elif words0 == 'do_send': # See sr_config.7, and sr_sender.1
                     self.execfile("do_send",words1)
                     if ( self.do_send == None ) and not self.isNone(words1):
                        ok = False
                     n = 2

                elif words0 == 'durable'   : # See sr_config.7 ++
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.durable = True
                        n = 1
                     else :
                        self.durable = self.isTrue(words[1])
                        n = 2

                elif words0 in ['events','e']:  # See sr_watch.1
                     i = 0
                     if 'deleted' in words[1]:
                         self.logger.warning("deprecated Event spec: please change 'deleted' --> 'delete'")
                         words[1] = words[1].replace("deleted","delete")

                     if 'created' in words[1]:
                         self.logger.warning("deprecated Event spec: please change 'created' --> 'create'")
                         words[1] = words[1].replace("created","create")

                     if 'linked' in words[1]:
                         self.logger.warning("deprecated Event spec: please change 'linked' --> 'link'")
                         words[1] = words[1].replace("linked","link")

                     if 'modified' in words[1]:
                         self.logger.warning("deprecated event spec: please change 'modified' --> 'modify'")
                         words[1] = words[1].replace("modified","modify")

                     if 'create'  in words[1] : i = i + 1
                     if 'delete'  in words[1] : i = i + 1
                     if 'link' in words[1] : i = i + 1
                     if 'modify' in words[1] : i = i + 1
                     if 'move'  in words[1] : i = i + 1
                     
                     if i < len(words[1].split(',')) :
                        self.logger.error("events invalid (%s)" % words[1])
                        needexit = True

                     self.events = words[1]
                     n = 2

                elif words0 in ['exchange','ex'] : # See: sr_config.7 ++ everywhere fixme?
                     self.exchange = words1
                     n = 2

                elif words0 == 'expire' : # See: sr_config.7 ++ everywhere fixme?
                     if    words1.lower() == 'none' :
                           self.expire = None
                     else:
                           # rabbitmq setting is in millisec / user in secs
                           self.expire = int(self.duration_from_str(words1,'ms'))
                           if self.expire < 300000 : 
                              self.logger.warning("expire setting (%s) may cause problem...too low" % words[1])
                     n = 2

                elif words0 == 'filename': # See: sr_poll.1, sr_sender.1
                     self.currentFileOption = words[1]
                     n = 2

                elif words0 in [ 'flatten' ]: # See: sr_poll.1, sr_sender.1
                     self.flatten = words[1]
                     n = 2

                elif words0 in ['follow_symlinks','fs']: # See: sr_post.1, sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.follow_symlinks = True
                        n = 1
                     else :
                        self.follow_symlinks = self.isTrue(words[1])
                        n = 2

                elif words0 in ['force_polling','fp']: # See: sr_post.1, sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.force_polling = True
                        n = 1
                     else :
                        self.force_polling = self.isTrue(words[1])
                        n = 2

                elif words0 in ['headers']: # See: sr_config.7
                     kvlist = words1.split('=')
                     key    = kvlist[0]
                     value  = kvlist[1]

                     if value.lower() in ['none','null'] :
                        self.headers_to_del.append(key)
                     else :
                        self.headers_to_add [key] = value
                     n = 2

                elif words0 in ['gateway_for','gf']: # See: sr_config.7, sr_sarra.8, sr_sender.1 
                     self.gateway_for = words1.split(',')
                     n = 2

                elif words0 == 'heartbeat' :   # See: sr_config.7
                     # heartbeat setting is in sec 
                     self.heartbeat = self.duration_from_str(words1,'s')
                     if self.heartbeat <= 0 : self.heartbeat = 0
                     n = 2

                elif words0 in ['help','h']: # See: sr_config.7
                     self.help()
                     needexit = True
                     os._exit(0)

                elif words0 in ['hostname']: # See: dd_subscribe (obsolete option...ok)
                     self.hostname = words[1] 
                     n = 2

                elif words0 in ['inplace','in','assemble']: # See: sr_sarra.8, sr_post.1, sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.inplace = True
                        n = 1
                     else :
                        self.inplace = self.isTrue(words[1])
                        n = 2

                elif words0 in ['instances','i']: # See: sr_config.7
                     self.nbr_instances = int(words[1])
                     n = 2

                elif words0 == 'interface': # See: sr_poll, sr_winnow
                     self.logger.warning("deprecated *interface* option no longer has any effect, vip is enough." )
                     self.interface = words[1]
                     n = 2

                elif words0 == 'kbytes_ps': # See: sr_sender 
                     self.kbytes_ps = int(words[1])
                     n = 2

                elif words0 in ['lock','inflight']: # See: sr_config.7, sr_subscribe.1
                     if words[1].lower() in [ 'none' ]: 
                         self.inflight=None
                     elif words[1][0].isnumeric() :
                         self.inflight = self.duration_from_str(words1,'s')
                         if self.inflight <= 1 : self.inflight = None
                     else:
                         self.inflight = words[1] 
                     n = 2

                elif words0 in ['log','l']: # See: sr_config.7 
                     self.logpath         = words1
                     if os.path.isdir(words1) :
                        self.user_log_dir = words1
                     else :
                        self.user_log_dir = os.path.dirname(words1)
                     n = 2

                elif words0 == 'pipe' : # See: FIXME
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.pipe = True
                        n = 1
                     else :
                        self.pipe = self.isTrue(words[1])
                        n = 2

                elif words0 == 'restore' : # See: sr_config.7 
                     #-- report_daemons left for transition, should be removed in 2017
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.restore = True
                        n = 1
                     else :
                        self.restore = self.isTrue(words[1])
                        n = 2

                elif words0 in ['restore_to_queue', 'restore2queue', 'r2q', 'rq']: 
                     # FIXME: should be in: sr_shovel.1
                     self.restore_queue = words1
                     n = 2

                elif words0 == 'report_daemons' or words0 == 'report_daemons': # See: sr_config.7 
                     #-- report_daemons left for transition, should be removed in 2017
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.report_daemons = True
                        n = 1
                     else :
                        self.report_daemons = self.isTrue(words[1])
                        n = 2

                elif words0 in ['report_exchange', 'lx', 'le'] : # See: sr_config.7 ++ everywhere fixme?
                     self.report_exchange = words1
                     n = 2

                elif words0 in ['logdays', 'ld', 'logrotate','lr']:  # See: sr_config.7 
                     # log setting is in days 
                     self.logrotate = int(self.duration_from_str(words1,'d'))
                     if self.logrotate < 1 : self.logrotate = 1
                     n = 2

                elif words0 in ['loglevel','ll']:  # See: sr_config.7
                     level = words1.lower()
                     if level in 'critical' : self.loglevel = logging.CRITICAL
                     if level in 'error'    : self.loglevel = logging.ERROR
                     if level in 'info'     : self.loglevel = logging.INFO
                     if level in 'warning'  : self.loglevel = logging.WARNING
                     if level in 'debug'    : self.loglevel = logging.DEBUG
                     if level in 'none'     : self.loglevel = None
                     self.set_loglevel()
                     n = 2


                elif words0 in ['manager','feeder'] : # See: sr_config.7, sr_sarra.8
                     urlstr       = words1
                     ok, url      = self.validate_urlstr(urlstr)
                     self.manager = url
                     self.users[url.username] = 'feeder'
                     if not ok or not url.scheme in ['amqp','amqps']:
                        self.logger.error("invalid manager url (%s)" % urlstr)
                        needexit = True
                     n = 2

                elif words0 == 'max_queue_size':  # See: sr_audit.8 (sr_config also)
                     self.max_queue_size = int(words[1])
                     n = 2

                elif words0 == 'message_ttl':  # See: sr_consumer.7
                     if    words1.lower() == 'none' :
                           self.message_ttl = None
                     else:
                           # rabbitmq setting is in millisec 
                           self.message_ttl = int(self.duration_from_str(words1,'ms'))
                           if self.message_ttl < 300000 :
                              self.logger.warning("message_ttl setting (%s) may cause problem...too low" % words[1])
                     n = 2

                elif words0 == 'mirror': # See: sr_config.7 
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.mirror = True
                        n = 1
                     else :
                        self.mirror = self.isTrue(words[1])
                        n = 2

                elif words0 == 'move': # See: sr_post.1
                     self.movepath = []
                     self.movepath.append(words[1])
                     self.movepath.append(words[2])
                     n = 3

                # Internal use only: when instances>1 is used, and the instances are started
                # there are N instances asked to start each one having its own number (no)
                # -no 1,  -no 2, ...  -no N
                elif words0 == 'no':
                     self.no = int(words[1])
                     n = 2

                elif words0 in ['notify_only','n','no_download']: # See: sr_subscribe.1  
                     self.logger.debug("option %s" % words[0])
                     self.notify_only = True
                     n = 1

                elif words0 == 'on_file': # See: sr_config.7, sr_sarra,shovel,subscribe
                     self.execfile("on_file",words1)
                     if ( self.on_file == None ):
                        if self.isNone(words1):
                           self.on_file_list = []
                        else:
                           ok = False
                           needexit = True
                     else:
                        self.on_file_list.append(self.on_file)

                     n = 2

                elif words0 == 'on_heartbeat': # See: sr_config.7, sr_sarra,shovel,subscribe
                     self.execfile("on_heartbeat",words1)
                     if ( self.on_heartbeat == None ):
                        if self.isNone(words1):
                           self.on_heartbeat_list = []
                        else:
                           ok = False
                           needexit = True
                     else:
                        self.on_heartbeat_list.append(self.on_heartbeat)

                     n = 2

                elif words0 == 'on_html_page': # See: sr_config
                     self.execfile("on_html_page",words1)
                     if ( self.on_html_page == None ):
                        if self.isNone(words1):
                            self.on_html_page_list = []
                        else:
                            ok = False
                            needexit = True
                     else:
                        self.on_html_page_list.append(self.on_html_page)
                     n = 2

                elif words0 == 'on_line': # See: sr_poll.1
                     self.execfile("on_line",words1)
                     if ( self.on_line == None ):
                        if self.isNone(words1):
                           self.on_line_list = []
                        else:
                           ok = False
                           needexit = True
                     else:
                        self.on_line_list.append(self.on_line)

                     n = 2

                elif ( words0 == 'on_message' ) or ( words0 == 'on_msg' ) : # See: sr_config.1, others...
                     self.execfile("on_message",words1)
                     if ( self.on_message == None ):
                        if self.isNone(words1):
                           self.on_message_list = []
                        else:
                           ok = False
                           needexit = True
                     else:
                        self.on_message_list.append(self.on_message)
                     n = 2

                elif words0 == 'on_part': # See: sr_config, sr_subscribe
                     self.execfile("on_part",words1)
                     if ( self.on_part == None ):
                        if self.isNone(words1):
                           self.on_part_list = []
                        else:
                           ok = False
                           needexit = True
                     else:
                        self.on_part_list.append(self.on_part)

                     n = 2

                elif words0 == 'on_post': # See: sr_config
                     self.execfile("on_post",words1)
                     if ( self.on_post == None ):
                        if self.isNone(words1):
                            self.on_post_list = []
                        else:
                            ok = False
                            needexit = True
                     else:
                        self.on_post_list.append(self.on_post)
                     n = 2

                elif words0 == 'on_watch': # See: sr_config
                     self.execfile("on_watch",words1)
                     if ( self.on_watch == None ):
                        if self.isNone(words1):
                            self.on_watch_list = []
                        else:
                            ok = False
                            needexit = True
                     else:
                        self.on_watch_list.append(self.on_watch)
                     n = 2

                elif words0 in ['overwrite','o'] : # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.overwrite = True
                        n = 1
                     else :
                        self.overwrite = self.isTrue(words[1])
                        n = 2

                elif words0 == 'parts': # See: sr_poll.1, sr_watch.1
                     self.parts   = words[1]
                     ok = self.validate_parts()
                     if not ok : needexit = True
                     n = 2

                # adding paths in command line might be a mess...
                elif words0 in ['path','p']: # See: sr_post.1, sr_watch.1
                     n  = 1
                     dr = self.document_root
                     for w in words[1:]:

                         # stop if next option
                         if words[0][0:1] == '-' : 
                            if w[0:1] == '-'     : break

                         # adding path (cannot check if it exists we may post a delete)
                         try:
                                 path = w
                                 if dr and not dr in w: path = dr + os.sep + w

                                 path = os.path.abspath(path)
                                 if self.realpath:
                                     path = os.path.realpath(path)
                                 self.postpath.append(path)
                                 n = n + 1
                         except: break

                     if n == 1 :
                        self.logger.error("problem with path option")
                        needexit = True

                elif words0 in ['post_base_dir','pbd']: # See: sr_sarra,sender,shovel,winnow
                     if sys.platform == 'win32':
                         self.post_base_dir = words1.replace('\\','/')
                     else:
                         self.post_base_dir = words1
                     n = 2


                elif words0 in ['post_broker','pb'] : # See: sr_sarra,sender,shovel,winnow
                     urlstr      = words1
                     ok, url     = self.validate_urlstr(urlstr)
                     self.post_broker = url
                     if not ok or not url.scheme in ['amqp','amqps']:
                        self.logger.error("invalid post_broker url (%s)" % urlstr)
                        needexit = True
                     n = 2

                elif words0 in ['post_document_root','pdr']: # See: sr_sarra,sender,shovel,winnow
                     if sys.platform == 'win32':
                         self.post_document_root = words1.replace('\\','/')
                     else:
                         self.post_document_root = words1
                     n = 2

                elif words0 in ['post_exchange','pe','px']: # See: sr_sarra,sender,shovel,winnow 
                     self.post_exchange = words1
                     n = 2

                elif words0 in ['post_exchange_split','pes', 'pxs']: # sr_config.7, sr_shovel.1
                     self.post_exchange_split = int(words1)
                     n = 2

                elif words0 == 'prefetch': # See: sr_consumer.1  (Nbr of prefetch message when queue is shared)
                     self.prefetch = int(words1)
                     n = 2

                elif words0 in ['preserve_mode','pm'] : # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.preserve_mode = True
                        n = 1
                     else :
                        self.preserve_mode = self.isTrue(words[1])
                        n = 2

                elif words0 in ['preserve_time','pt'] : # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.preserve_time = True
                        n = 1
                     else :
                        self.preserve_time = self.isTrue(words[1])
                        n = 2

                elif words0 == 'pump':  # See: sr_audit.1  (give pump hints or setting errors)
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.pump_flag = True
                        n = 1
                     else :
                        self.pump_flag = self.isTrue(words[1])
                        n = 2

                elif words0 in ['queue', 'queue_name','qn'] : # See:  sr_config.7, sender, shovel, sub, winnow too much?
                     self.queue_name = words1
                     n = 2

                elif words0 in ['queue_suffix'] : # See: sr_consumer.1 : but not very usefull... could be removed
                     self.queue_suffix = words1
                     n = 2

                elif words0 in ['randomize','r']: # See: sr_watch.1, sr_post.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.randomize = True
                        n = 1
                     else :
                        self.randomize = self.isTrue(words[1])
                        n = 2

                elif words0 in ['realpath','real']: # See: sr_post.1, sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.realpath = True
                        n = 1
                     else :
                        self.realpath = self.isTrue(words[1])
                        n = 2

                elif words0 in ['recompute_chksum','rc']: # See: sr_sarra.8
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.recompute_chksum = True
                        n = 1
                     else :
                        self.recompute_chksum = self.isTrue(words[1])
                        n = 2

                elif words0 in ['reconnect','rr']: # See: sr_post.1, sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.reconnect = True
                        n = 1
                     else :
                        self.reconnect = self.isTrue(words[1])
                        n = 2

                elif words0 in ['remote_config']: # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.remote_config = True
                        n = 1
                     else :
                        self.remote_config = self.isTrue(words[1])
                        n = 2

                elif words0 in ['remote_config_url']: # See: sr_config.7
                     self.remote_config_url.append(words[1])
                     n = 2

                elif words0 in ['rename','rn']: # See: sr_poll, sarra, sender, sub, watch? 
                     self.rename = words1
                     n = 2

                elif words0 in ['report_back','rb']:  # See: sr_subscribe.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.reportback = True
                        n = 1
                     else :
                        self.reportback = self.isTrue(words[1])
                        n = 2

                elif words0 in ['reset']:  # See: sr_consumer.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.reset = True
                        n = 1
                     else :
                        self.reset = self.isTrue(words[1])
                        n = 2

                elif words0 in [ 'role', 'declare' ]:  # See: sr_audit.1
                     item = words[1].lower()
                     if words0 in [ 'role' ]:
                        self.logger.warning("role option deprecated, please replace with 'declare'" )

                     if item in [ 'source' , 'subscriber' ]:
                        roles  = item
                        user   = words[2]
                        self.users[user] = roles
                     elif item in [ 'exchange' ]:
                        self.exchanges.append( words[2] )                                                
                     n = 3

                elif words0 == 'save' : # See: sr_config.7 
                     #-- report_daemons left for transition, should be removed in 2017
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.save = True
                        n = 1
                     else :
                        self.save = self.isTrue(words[1])
                        n = 2

                elif words0 in [ 'save_file', 'sf' ]: # FIXMEFIXME
                     self.save_file = words[1]
                     n = 2

                elif words0 in ['set_passwords']:  # See: sr_consumer.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.set_passwords = True
                        n = 1
                     else :
                        self.set_passwords = self.isTrue(words[1])
                        n = 2

                elif words0 == 'sleep': # See: sr_audit.8 sr_poll.1
                     # sleep setting is in sec 
                     self.sleep = self.duration_from_str(words1,'s')
                     if self.sleep <= 0 : self.sleep = 0
                     n = 2

                elif words0 == 'source': # See: sr_post.1 sr_watch.1
                     self.source = words[1]
                     n = 2

                elif words0 in ['source_from_exchange','sfe']: # See: sr_sarra.8
                     if (words1 is None ) or words[0][0:1] == '-' : 
                        self.source_from_exchange = True
                        n = 1
                     else :
                        self.source_from_exchange = self.isTrue(words[1])
                        n = 2

                elif words0 == 'statehost': # MG FIXME to be documented somewhere ???
                     self.statehost = True
                     self.hostform  = 'short'
                     if (words1 is None) or words[0][0:1] == '-' : 
                        n = 1
                     elif words1.lower() in ['short','fqdn']:
                        self.hostform  = words1.lower()
                        n = 2
                     else:
                        if not self.isTrue(words[1]): self.statehost = False
                        n = 2

                elif words0 == 'strip': # See: sr_config.7 
                     if words1.isnumeric() :
                        self.strip  = int(words1)
                        self.pstrip = None
                     else:                   
                        self.strip  = 0
                        self.pstrip = words1
                     n = 2

                elif words0 in ['subtopic','sub'] : # See: sr_config.7 
                     self.subtopic = words1
                     key = self.topic_prefix + '.' + self.subtopic
                     self.bindings.append( (self.exchange,key) )
                     self.logger.debug("BINDINGS")
                     self.logger.debug("BINDINGS %s"% self.bindings)
                     n = 2

                elif words0 == 'sum': # See: sr_config.7 
                     self.sumflg = words[1]
                     ok = self.validate_sum()
                     if not ok : needexit = True
                     n = 2

                elif words0 == 'timeout': # See: sr_sarra.8
                     # timeout setting is in sec 
                     self.timeout = int(self.duration_from_str(words1,'s'))
                     if self.timeout <= 0 : self.timeout = None
                     n = 2

                elif words0 == 'to': # See: sr_config.7
                     self.to_clusters = words1
                     n = 2

                elif words0 in ['topic_prefix','tp'] : # See: sr_config.7 
                     self.topic_prefix = words1

                elif words0 in ['post_base_url','pbu','url','u','post_url']: # See: sr_config.7 
                     if words0 in ['url','u'] : self.logger.warning("option url deprecated please use post_base_url")
                     self.url = urllib.parse.urlparse(words1)
                     self.post_base_url = words1
                     n = 2

                elif words0 == 'use_pika': # See: FIX ME
                     if (words1 is None) or words[0][0:1] == '-' :
                        self.use_pika = True
                        n = 1
                     else :
                        self.use_pika = self.isTrue(words[1])
                        n = 2

                elif words0 == 'users':  # See: sr_audit.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.users_flag = True
                        n = 1
                     else :
                        self.users_flag = self.isTrue(words[1])
                        n = 2

                elif words0 == 'vip': # See: sr_poll.1, sr_winnow.1
                     self.vip = words[1]
                     n = 2

                else :
                     # if unknown option is supplied, create a list for the values 
                     # FIXME: if specifying values on command line, this breaks (including all options)
                     #        dunno solution.  having it take all values allows options with > 1 word, which is very useful
                     #        see post_override plugin.
                     #
                     value = ' '.join(words[1:])
                     if not hasattr(self,words[0]):
                         self.logger.debug("unrecognized option %s %s" % (words[0],value))
                         setattr(self, words[0],[ value ])
                         self.extended_options.append(words[0])
                         self.logger.debug("extend set %s = '%s'" % (words[0],getattr(self,words[0])))
                     else:
                         value2=getattr(self,words[0])
                         value2.append(value)
                         setattr(self,words[0],value2)
                         self.logger.debug("extend add %s = '%s'" % (words[0],getattr(self,words[0])))

        except:
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
                self.logger.error("problem evaluating option %s" % words[0])

        if needexit :
           os._exit(1)

        return n

    def overwrite_defaults(self):
        self.logger.debug("sr_config overwrite_defaults")

    def set_sumalgo(self,sumflg):
        self.logger.debug("sr_config set_sumalgo %s" % sumflg)

        if sumflg == self.lastflg : return

        flgs = sumflg

        if len(sumflg) > 2 and sumflg[:2] in ['z,','M,']:
           flgs = sumflg[2:]

        if flgs == self.lastflg : return
        self.lastflg = flgs

        if flgs == 'd' : 
           self.sumalgo = checksum_d()
           return

        if flgs == 'n' :
           self.sumalgo = checksum_n()
           return

        if flgs in [ 's' ]:
           self.sumalgo = checksum_s()
           return

        if flgs in [ '0', 'L', 'R' ]:
           self.sumalgo = checksum_0()
           return

        sum_error    = False
        self.execfile('sumalgo',flgs)

        if self.sumalgo == None : sum_error = True

        if not sum_error and not hasattr(self.sumalgo,'set_path' ) : sum_error = True
        if not sum_error and not hasattr(self.sumalgo,'update'   ) : sum_error = True
        if not sum_error and not hasattr(self.sumalgo,'get_value') : sum_error = True

        if sum_error :
           self.logger.error("sumflg %s not working... set to 'd'" % sumflg)
           self.lastflg = 'd'
           self.sumalgo = checksum_d()


    def set_loglevel(self):

        if self.loglevel == None :
           if hasattr(self,'logger') : del self.logger
           self.logpath = None
           self.logger  = logging.RootLogger(logging.CRITICAL)
           noop         = logging.NullHandler()
           self.logger.addHandler(noop)
           return

        self.logger.setLevel(self.loglevel)

    def setlog(self):

        import logging.handlers

        self.set_loglevel()

        # no log

        if self.loglevel == None : return

        # interactive

        if self.logpath  == None :
           self.logger.debug("on screen logging")
           return

        # to file

        self.logger.debug("switching to log file %s" % self.logpath )

        del self.logger

        LOG_FORMAT   = ('%(asctime)s [%(levelname)s] %(message)s')
          
        self.handler = logging.handlers.TimedRotatingFileHandler(self.logpath, when='midnight', \
                       interval=1, backupCount=self.logrotate)
        fmt          = logging.Formatter( LOG_FORMAT )
        self.handler.setFormatter(fmt)

        self.logger = logging.RootLogger(logging.WARNING)
        self.logger.setLevel(self.loglevel)
        self.logger.addHandler(self.handler)
        os.chmod( self.logpath, self.chmod_log )


    # check url and add credentials if needed from credential file

    def validate_urlstr(self,urlstr):

        ok, details = self.credentials.get(urlstr)
        if details == None :
           self.logger.error("bad credential %s" % urlstr)
           return False, urllib.parse.urlparse(urlstr)

        return True, details.url


    def validate_parts(self):
        self.logger.debug("sr_config validate_parts %s" % self.parts)
        if not self.parts[0] in ['0','1','p','i']:
           self.logger.error("parts invalid strategy (only 0,1,p, or i)(%s)" % self.parts)
           return False

        self.partflg = self.parts[0]
        token = self.parts.split(',')

        if len(token) > 1:
           if self.partflg == '1' :
               self.logger.error("parts invalid strategy 1 (whole files) accepts no other options: (%s)" % self.parts)
               return False
           if self.partflg == 'p' : 
               self.logger.error("parts invalid strategy p arguments partial file posting not supported (%s)" % self.parts)
               return False

           if ( self.partflg == 'i' or self.partflg== '0'):
              if len(token) > 2 :
                 self.logger.error("parts invalid too much  (%s)" % self.parts)
                 return False

              try    : self.blocksize = self.chunksize_from_str(token[1])
              except :
                    self.logger.error("parts invalid blocksize given (%s)" % self.parts)
                    return False

        return True

    def validate_sum(self):
        self.logger.debug("sr_config validate_sum %s" % self.sumflg)

        sumflg = self.sumflg.split(',')[0]

        if sumflg == 'z' : sumflg = self.sumflg[2:]

        if sumflg in ['0','n','d','s','R']: return True

        try :
                 self.set_sumalgo(sumflg)
                 return True
        except : 
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s" % (stype, svalue))
                 self.logger.error("sum invalid (%s)" % self.sumflg)
                 return False
        return False


    def wget(self,config):
        self.logger.debug("sr_config wget %s" % config)
        import urllib.request, urllib.error

        if len(self.remote_config_url) == 0 : return None

        for u in self.remote_config_url :

            url        = u + os.sep + config
            local_file = self.http_dir + os.sep + config

            try :
                req  = urllib.request.Request(url)
                resp = urllib.request.urlopen(req)
                fp   = open(local_file,'wb')
                while True:
                      chunk = resp.read(self.bufsize)
                      if not chunk : break
                      fp.write(chunk)
                fp.close()
                return local_file

            except urllib.error.HTTPError as e:
                self.logger.error('Download failed: %s', url)                    
                self.logger.error('Server couldn\'t fulfill the request. Error code: %s, %s', e.code, e.reason)
            except urllib.error.URLError as e:
                self.logger.error('Download failed: %s', url)                                    
                self.logger.error('Failed to reach server. Reason: %s', e.reason)            
            except:
                self.logger.error('Download failed: %s', url )
                self.logger.error('Uexpected error')              
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))

        return None

# ===================================
# self_test
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

def self_test():

    failed = False

    # test include
    f = open("./bbb.inc","w")
    f.write("randomize True\n")
    f.close()
    f = open("./aaa.conf","w")
    f.write("include bbb.inc\n")
    f.close()

    # instantiation, test include and overwrite logs
    logger = test_logger()
    cfg    = sr_config(config="aaa")
    cfg.logger = logger
    cfg.configure()

    if not cfg.randomize :
       cfg.logger.error("problem with include")
       failed = True

    # back to defaults + check isTrue
    cfg.defaults()
    if not cfg.isTrue('true') or cfg.isTrue('false') :
       cfg.logger.error("problem with module isTrue")
       failed = True

    # pluggin script checking
    f = open("./scrpt.py","w")
    f.write("class Transformer(object): \n")
    f.write("      def __init__(self):\n")
    f.write("          pass\n")
    f.write("\n")
    f.write("      def perform(self,parent):\n")
    f.write("          if parent.this_value != 0 : return False\n")
    f.write("          parent.this_value = 1\n")
    f.write("          return True\n")
    f.write("\n")
    f.write("transformer = Transformer()\n")
    f.write("self.this_script = transformer.perform\n")
    f.close()

    # able to find the script
    ok, path = cfg.config_path("plugins","scrpt.py",mandatory=True,ctype='py')
    if not ok :
       cfg.logger.error("problem with config_path script not found")
       failed = True
 
    # able to load the script
    cfg.execfile("this_script",path)
    if cfg.this_script == None :
       cfg.logger.error("problem with module execfile script not loaded")
       failed = True

    # able to run the script
    cfg.this_value = 0
    cfg.this_script(cfg)
    if cfg.this_value != 1 :
       cfg.logger.error("problem to run the script ")
       failed = True
    os.unlink("./scrpt.py")

    # general ... 

    cfg.general()
    cfg.logger.info(cfg.user_cache_dir)
    cfg.logger.info(cfg.user_log_dir)    
    cfg.logger.info(cfg.user_config_dir)

    # args ... 

    cfg.randomize = False
    cfg.assemble  = False
    cfg.logrotate = 5
    cfg.expire      = 0
    expire_value    = 1000*60*60*3
    message_value   = 1000*60*60*24*7*3
    cfg.message_ttl = 0
    cfg.args(['-expire','3h','-message_ttl','3W','--randomize', '--assemble', 'True',  '-logrotate', '10'])
    if not cfg.randomize :
       cfg.logger.error("problem randomize")
       failed = True
    if not cfg.inplace  :
       cfg.logger.error("problem assemble")
       failed = True
    if cfg.logrotate !=10 :
       cfg.logger.error("problem logrotate %s" % cfg.logrotate)
       failed = True
    if cfg.expire != expire_value :
       cfg.logger.error("problem expire %s" % cfg.expire)
       failed = True
    if cfg.message_ttl != message_value :
       cfg.logger.error("problem message_ttl %s" % cfg.message_ttl)
       failed = True


    # has_vip... 
    cfg.args(['-vip', '127.0.0.1' ])
    if not cfg.has_vip():
       cfg.logger.error("has_vip failed")
       failed = True

    # config... 
    #def isMatchingPattern(self, str, accept_unmatch = False): 
    #def sundew_dirPattern(self,basename,destDir,destName) :
    #def sundew_getDestInfos(self, filename):
    #def validate_urlstr(self,urlstr):
    #def validate_parts(self):
    #def validate_sum(self):


    opt1 = "hostname toto"
    opt2 = "broker amqp://a:b@${HOSTNAME}"
    cfg.option(opt1.split())
    cfg.option(opt2.split())
    if cfg.broker.geturl() != "amqp://a:b@toto" :
       cfg.logger.error("problem with args 2")
       failed = True

    opt1 = "parts i,128"
    cfg.option(opt1.split())

    opt1 = "sum z,d"
    cfg.option(opt1.split())

    opt1 = "sum R,0"
    cfg.option(opt1.split())

    opt1 = "move toto titi"
    cfg.option(opt1.split())
    cfg.logger.debug(cfg.movepath)

    opt1 = "path .. ."
    cfg.option(opt1.split())
    cfg.logger.debug(cfg.postpath)

    opt1 = "inflight ."
    cfg.option(opt1.split())
    if cfg.inflight != '.' :
       cfg.logger.error("inflight .")
       failed = True

    opt1 = "inflight .tmp"
    cfg.option(opt1.split())
    if cfg.inflight != '.tmp' :
       cfg.logger.error("inflight .tmp")
       failed = True

    opt1 = "inflight 1.5"
    cfg.option(opt1.split())
    if cfg.inflight != 1.5 :
       cfg.logger.error("inflight 1.5")
       failed = True

    #opt1 = "sum checksum_AHAH.py"
    #cfg.option(opt1.split())


    opt1 = "remote_config True"
    #opt2 = "remote_config_url http://ddsr1.cmc.ec.gc.ca/keep_this_test_dir"
    opt2 = "remote_config_url http://localhost:8000/keep_this_test_dir"
    cfg.option(opt1.split())
    cfg.option(opt2.split())

    #cfg.reconnect     = True
    #opt1 = "config reconnect_false.conf"
    #cfg.option(opt1.split())
    #if cfg.reconnect != False :
    #   cfg.logger.error(" include http:  did not work")

    #cfg.set_sumalgo('z,checksum_mg.py')

    #cfg.remote_config = False
    #cfg.assemble       = False
    #opt1 = "include http://ddsr1.cmc.ec.gc.ca/keep_this_test_dir/assemble_true.inc"
    #cfg.option(opt1.split())
    #if cfg.assemble == True :
    #   cfg.logger.error(" include http: worked but should not")

    opt1 = "prefetch 10"
    cfg.option(opt1.split())

    if cfg.prefetch != 10 :
       cfg.logger.error(" prefetch option:  did not work")
       failed = True

    # reexecuting the config aaa.conf
    cfg.config(cfg.user_config)
    os.unlink('aaa.conf')
    os.unlink('bbb.inc')

    opt1 = "headers toto1=titi1"
    cfg.option(opt1.split())
    opt2 = "headers toto2=titi2"
    cfg.option(opt2.split())
    opt3 = "headers tutu1=None"
    cfg.option(opt3.split())
    opt4 = "headers tutu2=None"
    cfg.option(opt4.split())

    opt4 = "expire 10m"
    cfg.option(opt4.split())

    opt4 = "message_ttl 10m"
    cfg.option(opt4.split())

    if not 'toto1' in cfg.headers_to_add      or \
       not 'toto2' in cfg.headers_to_add      or \
       cfg.headers_to_add['toto1'] != 'titi1' or \
       cfg.headers_to_add['toto2'] != 'titi2' or \
       len(cfg.headers_to_add)     != 2 :
       cfg.logger.error(" option headers adding entries did not work")
       failed = True

    if not 'tutu1' in cfg.headers_to_del      or \
       not 'tutu2' in cfg.headers_to_del      or \
       len(cfg.headers_to_del)     != 2 :
       cfg.logger.error(" option headers deleting entries did not work")
       failed = True

    opt4="directory ${MAIL}/${USER}/${SHELL}/blabla"
    cfg.option(opt4.split())
    if '$' in cfg.currentDir:
       cfg.logger.error(" env variable substitution failed %s" % cfg.currentDir)
       failed = True

    opt4='strip 4'
    cfg.option(opt4.split())
    if cfg.strip != 4 :
       cfg.logger.error(" strip 4 failed")
       failed = True

    opt4='strip .*aaa'
    cfg.option(opt4.split())
    if cfg.pstrip != '.*aaa' :
       cfg.logger.error(" strip .*aaa failed")
       failed = True

    pika = cfg.use_pika

    opt4='use_pika True'
    cfg.option(opt4.split())
    if not cfg.use_pika :
       cfg.logger.error(" use_pika 1 failed")
       failed = True

    opt4='use_pika False'
    cfg.option(opt4.split())
    if cfg.use_pika :
       cfg.logger.error(" use_pika 2 failed")
       failed = True

    opt4='use_pika'
    cfg.option(opt4.split())
    if not cfg.use_pika :
       cfg.logger.error(" use_pika 3 failed")
       failed = True

    opt4='statehost False'
    cfg.option(opt4.split())
    if cfg.statehost :
       cfg.logger.error(" statehost 1 failed")
       failed = True

    opt4='statehost True'
    cfg.option(opt4.split())
    if not cfg.statehost or cfg.hostform != 'short' :
       cfg.logger.error(" statehost 2 failed")
       failed = True

    opt4='statehost SHORT'
    cfg.option(opt4.split())
    if not cfg.statehost or cfg.hostform != 'short' :
       cfg.logger.error(" statehost 3 failed")
       failed = True

    opt4='statehost fqdn'
    cfg.option(opt4.split())
    if not cfg.statehost or cfg.hostform != 'fqdn' :
       cfg.logger.error(" statehost 3 failed")
       failed = True

    opt4='statehost TOTO'
    cfg.option(opt4.split())
    if cfg.statehost and cfg.hostform != None:
       cfg.logger.error(" statehost 4 failed")
       failed = True

    opt4='extended TOTO'
    cfg.option(opt4.split())

    cfg.declare_option('extended')
    if not cfg.check_extended():
       cfg.logger.error(" declared extended 1 failed")
       failed = True

    opt4='extended_bad TITI'
    cfg.option(opt4.split())
    #if cfg.check_extended():
    #   cfg.logger.error(" undeclared extended failed")
    #   failed = True

    opt1 = "surplus_opt surplus_value"
    cfg.option(opt1.split())

    if cfg.surplus_opt != [ "surplus_value" ] :
       cfg.logger.error(" extended option:  did not work")
       failed = True

    opt1 = "surplus_opt surplus_value2"
    cfg.option(opt1.split())
    if cfg.surplus_opt[0] != "surplus_value" or cfg.surplus_opt[1] != "surplus_value2":
       cfg.logger.error(" extended option:  did not work")
       failed = True

    opt1 = "base_dir /home/aspymjg/dev/metpx-sarracenia/sarra"
    cfg.option(opt1.split())

    opt1 = "post_base_dir /totot/toto"
    cfg.option(opt1.split())

    opt1 = "post_base_url file://toto"
    cfg.option(opt1.split())


    if not failed : print("TEST PASSED")
    else :          print("TEST FAILED")

    sys.exit(0)

# ===================================
# MAIN
# ===================================

def main():

    self_test()
    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()
