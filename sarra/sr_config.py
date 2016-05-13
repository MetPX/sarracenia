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
import inspect
import netifaces
import os,re,socket,sys,random
import urllib,urllib.parse
from   appdirs import *
import sarra

try :
         from sr_credentials       import *
         from sr_util              import *
except : 
         from sarra.sr_credentials import *
         from sarra.sr_util        import *

class sr_config:

    def __init__(self,config=None,args=None):
        if '-V' in sys.argv :
           print("Version %s" % sarra.__version__ )
           os._exit(0)
        # IN BIG DEBUG
        #self.debug = True
        #self.logpath = None
        #self.setlog()

        # package_dir     = where sarra is installed on system
        # appdirs setup... on linux it gives :
        # site_data_dir   = /usr/share/default/sarra   ** unused
        # user_data_dir   = ~/.local/share/sarra       ** unused
        #
        # site_config_dir = /etc/xdg/xdg-default/sarra
        # user_cache_dir  = ~/.cache/sarra
        # user_log_dir    = ~/.cache/sarra/var/log
        # user_config_dir = ~/.config/sarra
         
        self.appname          = 'sarra'
        self.appauthor        = 'science.gc.ca'

        self.package_dir      = os.path.dirname(inspect.getfile(sr_credentials))
        self.site_config_dir  = site_config_dir(self.appname,self.appauthor)
        self.user_config_dir  = user_config_dir(self.appname,self.appauthor)
        self.user_log_dir     = user_log_dir   (self.appname,self.appauthor)
        self.user_log_dir     = self.user_log_dir.replace(os.sep+'log',os.sep+'var'+os.sep+'log')
        self.user_plugins_dir = self.user_config_dir + '/plugins'
        self.http_dir         = self.user_config_dir + '/Downloads'

        # umask change for directory creation and chmod

        try    : os.umask(0)
        except : pass

        # make sure the users directories exist

        try    : os.makedirs(self.user_config_dir, 0o775,True)
        except : pass
        try    : os.makedirs(self.user_log_dir,    0o775,True)
        except : pass
        try    : os.makedirs(self.user_plugins_dir,0o775,True)
        except : pass
        try    : os.makedirs(self.http_dir,        0o775,True)
        except : pass

        # logging is interactive at start

        self.debug         = False
        self.remote_config = False
        # IN BIG DEBUG
        #self.debug = True
        #self.loglevel = logging.DEBUG
        self.loglevel = logging.INFO
        self.setlog()
        self.logger.debug("sr_config __init__")

        # hostname

        self.hostname     = socket.getfqdn()

        # program_name

        self.program_name = re.sub(r'(-script\.pyw|\.exe|\.py)?$', '', os.path.basename(sys.argv[0]) )
        self.program_dir  = self.program_name[3:]
        self.logger.debug("sr_config program_name %s " % self.program_name)

        # config

        self.config_dir   = ''
        self.config_name  = None
        self.user_config  = config

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
        if not self.program_name in [ 'sr', 'sr_config' ]:
           self.logger.debug("sr_config user_cache_dir  %s " % self.user_cache_dir ) 
           try    : os.makedirs(self.user_cache_dir,  0o775,True)
           except : pass

        # check arguments

        if args == [] : args = None
        self.user_args       = args

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

    def check(self):
        self.logger.debug("sr_config check")

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
        self.logger.debug("sr_config config")
        self.logger.debug("sr_config %s" % path)

        if path == None : return

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
          if subdir == 'plugins' : self.logger.error("script not found %s" % config)
          else                   : self.logger.error("file not found %s" % config)
          os._exit(1)

        return False,config

    def configure(self):
        
        self.defaults()
        self.general()

        self.overwrite_defaults()

        # load/reload all config settings

        self.args   (self.user_args)
        self.config (self.user_config)

        # verify / complete settings

        self.check()

    def defaults(self):
        self.logger.debug("sr_config defaults")

        # IN BIG DEBUG
        #self.debug = True
        self.debug                = False

        self.remote_config        = False
        self.remote_config_url    = []

        self.loglevel             = logging.INFO
        self.logrotate            = 5
        self.log_daemons          = False

        self.bufsize              = 8192
        self.kbytes_ps            = 0

        self.sumalgo              = None
        self.lastflg              = None
        self.set_sumalgo('d')

        self.admin                = None
        self.manager              = None

        # consumer
        self.broker               = urllib.parse.urlparse('amqp://guest:guest@localhost/')
        self.bindings             = []
        self.exchange             = None
        self.topic_prefix         = 'v02.post'
        self.subtopic             = None

        self.queue_name           = None
        self.queue_suffix         = None
        self.durable              = False
        self.expire               = 1000 *60 *60 *24 *7    # 1 week= 1000millisec * 60s * 60m *24hr * 7d
        self.reset                = False
        self.message_ttl          = None
        self.prefetch             = 1
        self.max_queue_size       = 25000

        self.use_pattern          = False    # accept if No pattern matching
        self.accept_unmatch       = False    # accept if No pattern matching
        self.masks                = []       # All the masks (accept and reject)
        self.currentPattern       = None     # defaults to all
        self.currentDir           = '.'      # mask directory (if needed)
        self.currentFileOption    = None     # should implement metpx like stuff
        self.delete               = False

        self.log_exchange         = 'xlog'
        # 

        # publish
        self.caching              = False
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
        self.flow                 = None
        self.events               = 'created|deleted|modified'
        self.event                = 'created|deleted|modified'

        self.randomize            = False
        self.reconnect            = False

        self.partflg              = '1'
        #

        self.batch                = 100
        self.destination          = None
        self.timeout              = None

        # subscribe

        self.discard              = False
        self.flatten              = '/'
        self.no_logback           = False

        self.recursive            = False

        self.pump_flag            = False
        self.users_flag           = False

        self.post_broker          = urllib.parse.urlparse('amqp://guest:guest@localhost/')
        self.post_exchange        = None

        self.source               = None
        self.source_from_exchange = False

        # general cluster stuff
        self.cluster              = None
        self.cluster_aliases      = []
        self.gateway_for          = []
        self.users                = {}

        self.sleep                = 0
        self.strip                = 0

        self.blocksize            = 0

        self.destfn_script        = None
        self.do_download          = None
        self.do_poll              = None
        self.do_send              = None
        self.on_file              = None
        self.on_line              = None
   

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


        self.mirror               = False

        self.overwrite            = False
        self.recompute_chksum     = False

        self.interface            = None
        self.vip                  = None

        #self.on_message = None
        self.execfile("on_message",'msg_log')
        #if self.on_message == None :
        #    self.logger.error("built-in plugin script load failed, still None: msg_log" )

        #self.on_file = None
        self.execfile("on_file",'file_log')
        #if self.on_file == None :
        #    self.logger.error("built-in plugin script load failed, still None: file_log" )

        #self.on_post = None
        self.execfile("on_post",'post_log')
        #if self.on_post == None :
        #    self.logger.error("built-in plugin script load failed, still None: post_log" )



    def execfile(self, opname, path):

        setattr(self,opname,None)

        if path == 'None' or path == 'none' or path == 'off':
             self.logger.info("Reset script %s to None" % opname ) 
             return

        ok,script = self.config_path('plugins',path,mandatory=True,ctype='py')
        if ok:
             self.logger.info("installing %s script %s" % (opname, script ) ) 
        else:
             self.logger.error("installing %s script %s failed: not found " % (opname, path) ) 

        try    : 
            exec(compile(open(script).read(), script, 'exec'))
        except : 
            (stype, svalue, tb) = sys.exc_info()
            self.logger.error("Type: %s, Value: %s" % (stype, svalue))
            self.logger.error("for option %s script %s did not work" % (opname,path))

        if not hasattr(self,opname):
            self.logger.error("%s script incorrect (%s)" % (opname, words1))




    def general(self):
        self.logger.debug("sr_config general")

        # read in provided credentials
        credent = self.user_config_dir + os.sep + 'credentials.conf'
        self.cache_url   = {}
        self.credentials = sr_credentials(self.logger)
        self.credentials.read(credent)


        # read in provided log cluster infos
        log_cluster = self.user_config_dir + os.sep + 'log2clusters.conf'
        self.log_clusters = {}
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
                        self.logger.error("invalid URL %s" % parts[1])
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
        # at this level (for includes) user_config = self.user_config_dir

        defconf     = self.user_config_dir + os.sep + 'default.conf'
        self.logger.debug("defconf = %s\n" % defconf)
        if os.path.isfile(defconf) : 
           #user_config      = self.user_config
           #self.user_config = defconf
           config_dir       = self.config_dir
           self.config_dir  = ''
           self.config(defconf)
           self.config_dir  = config_dir
           #self.user_config = user_config

    def has_vip(self): 

        # no vip given... so should not matter ?
        if self.vip == None or self.interface == None :
           self.logger.warning("option vip or interface missing...")
           return False

        try   :
                a = netifaces.ifaddresses(self.interface)
                if netifaces.AF_INET in a :
                   for inet in a[netifaces.AF_INET]:
                       if 'addr' in inet :
                           if inet['addr'] == self.vip :
                              return True
        except: pass

        return False


    def isMatchingPattern(self, chaine, accept_unmatch = False): 

        for mask in self.masks:
            self.logger.debug(mask)
            pattern, maskDir, maskFileOption, mask_regexp, accepting = mask
            if mask_regexp.match(chaine) :
               if not accepting : return accepting
               self.currentPattern    = pattern
               self.currentDir        = maskDir
               self.currentFileOption = maskFileOption
               self.currentRegexp     = mask_regexp
               return accepting

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
    def metpx_basename_parts(self,basename):

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
    def metpx_dirPattern(self,urlstr,basename,destDir,destName) :

        BN = basename.split(":")
        EN = BN[0].split("_")
        BP = self.metpx_basename_parts(urlstr)

        ndestDir = ""
        DD = destDir.split("/")
        for  ddword in DD :
             if ddword == "" : continue

             nddword = ""
             DW = ddword.split("$")
             for dwword in DW :
                 nddword += self.metpx_matchPattern(BN,EN,BP,dwword,dwword)

             ndestDir += "/" + nddword 

        return ndestDir

    # modified from metpx client
    def metpx_getDestInfos(self, filename):
        """
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
                 old_remote_file    = self.remote_file
                 self.remote_file   = destFileName
                 self.destfn_script = None
                 script = spec[13:]
                 self.execfile('destfn_script',script)
                 if self.destfn_script != None :
                    ok = self.destfn_script(self)
                 destFileName       = self.remote_file
                 self.destfn_script = old_destfn_script
                 self.remote_file   = old_remote_file
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
    def metpx_matchPattern(self,BN,EN,BP,keywd,defval) :
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

           words1 = words1.replace('${HOSTNAME}',   self.hostname)
           words1 = words1.replace('${PROGRAM}',    self.program_name)
           words1 = words1.replace('${CONFIG}',     config)
           words1 = words1.replace('${BROKER_USER}',buser)
          
        # parsing

        needexit = False
        n        = 0
        try:
                if   words0 in ['accept','get','reject']: # See: sr_config.7
                     accepting   = words0 == 'accept' or words0 == 'get'
                     pattern     = words1
                     mask_regexp = re.compile(pattern)
                     n = 2

                     if len(words) > 2:
                        self.currentFileOption = words[2]
                        n = 3

                     self.masks.append((pattern, self.currentDir, self.currentFileOption, mask_regexp, accepting))
                     self.logger.debug("Masks")
                     self.logger.debug("Masks %s"% self.masks)

                elif words0 in ['accept_unmatch','au']: # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.accept_unmatch = True
                        n = 1
                     else :
                        self.accept_unmatch = self.isTrue(words[1])
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

                elif words0 == 'batch' : # See: sr_config.7
                     self.batch = int(words[1])
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
                     n = 2

                elif words0 == 'bufsize' :   # See: sr_config.7
                     self.bufsize = int(words[1])
                     n = 2

                elif words0 == 'caching': # See: sr_post.1 sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.caching = True
                        n = 1
                     else :
                        self.caching = self.isTrue(words[1])
                        n = 2

                elif words0 == 'chmod':    # See: function not actually implemented, stub of ftp support.
                     self.chmod = int(words[1])
                     n = 2

                elif words0 in ['cluster','cl']: # See: sr_config.7
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
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.debug = True
                        n = 1
                     else :
                        self.debug = self.isTrue(words[1])
                        n = 2

                     if self.debug :
                        self.loglevel = logging.DEBUG
                        self.logger.setLevel(self.loglevel)

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
                     ok, url          = self.validate_urlstr(urlstr)
                     self.destination = words1
                     if not ok :
                        self.logger.error("could not understand destination (%s)" % urlstr)
                        needexit = True
                     n = 2

                elif words0 == 'directory': # See: sr_config.7 ++ everywhere? FIXME too much?
                     self.currentDir = words1
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
                     path = os.path.realpath(path)
                     if sys.platform == 'win32':
                         self.document_root = path.replace('\\','/')
                     else:
                         self.document_root = path
                     n = 2

                elif words0 == 'do_download': # See sr_config.7, sr_warra, shovel, subscribe
                     self.do_download = None
                     self.execfile("do_download",words1)
                     if ( self.do_download == None ) and not self.isNone(words1):
                        ok = False
                     n = 2

                elif words0 == 'do_poll': # See sr_config.7 and sr_poll.1
                     self.do_poll = None
                     self.execfile("do_poll",words1)
                     if ( self.do_poll == None ) and not self.isNone(words1):
                        ok = False
                     n = 2

                elif words0 == 'do_send': # See sr_config.7, and sr_sender.1
                     self.do_send = None
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
                     if 'modified' in words[1] : i = i + 1
                     if 'deleted'  in words[1] : i = i + 1
                     if 'created'  in words[1] : i = i + 1
                     if 'moved'  in words[1] : i = i + 1
                     if i == 0 :
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
                           # should be expressed in mins (and in rabbitmq millisec hence 60000 factor)
                           self.expire = int(words[1]) * 60 * 1000
                           if self.expire <= 0 : self.expire = None
                     n = 2

                elif words0 == 'filename': # See: sr_poll.1, sr_sender.1
                     self.currentFileOption = words[1]
                     n = 2

                elif words0 in ['flow','f']: # See: sr_post.1, sr_log.7, shovel, subscribe, watch ? FIXME: should be in sr_config?
                     self.flow = words1 
                     n = 2

                elif words0 in ['gateway_for','gf']: # See: sr_config.7, sr_sarra.8 (FIXME: needed for sender?)
                     self.gateway_for = words1.split(',')
                     n = 2

                elif words0 in ['help','h']: # See: sr_config.7
                     self.help()
                     needexit = True

                elif words0 in ['hostname']: # See: dd_subscribe (obsolete option...ok)
                     self.hostname = words[1] 
                     n = 2

                elif words0 in ['inplace','in']: # See: sr_sarra.8, sr_post.1, sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.inplace = True
                        n = 1
                     else :
                        self.inplace = self.isTrue(words[1])
                        n = 2

                elif words0 in ['instances','i']: # See: sr_config++ FIXME: too many others?
                     self.nbr_instances = int(words[1])
                     n = 2

                elif words0 == 'interface': # See: sr_poll, sr_winnow
                     self.interface = words[1]
                     n = 2

                elif words0 == 'kbytes_ps': # See: sr_sender FIXME (only here? what about consumers? sr_config?)
                     self.kbytes_ps = int(words[1])
                     n = 2

                elif words0 in ['lock','inflight']: # See: sr_config.7, sr_subscribe.1
                     self.lock = words[1] 
                     if self.lock[0] != '.' : self.lock = None
                     n = 2

                elif words0 in ['log','l']: # See: sr_config.7 ++ too many others?  FIXME?
                     self.logpath         = words1
                     if os.path.isdir(words1) :
                        self.user_log_dir = words1
                     else :
                        self.user_log_dir = os.path.dirname(words1)
                     n = 2

                elif words0 == 'log_daemons': # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.log_daemons = True
                        n = 1
                     else :
                        self.log_daemons = self.isTrue(words[1])
                        n = 2

                elif words0 in ['log_exchange', 'lx', 'le'] : # See: sr_config.7 ++ everywhere fixme?
                     self.log_exchange = words1
                     n = 2

                elif words0 in ['logdays', 'ld', 'logrotate','lr']:  # See: sr_config.7 FIXME++ too many others?
                     self.logrotate = int(words[1])
                     n = 2

                elif words0 in ['loglevel','ll']:  # See: sr_config.7
                     level = words1.lower()
                     if level in 'critical' : self.loglevel = logging.CRITICAL
                     if level in 'error'    : self.loglevel = logging.ERROR
                     if level in 'info'     : self.loglevel = logging.INFO
                     if level in 'warning'  : self.loglevel = logging.WARNING
                     if level in 'debug'    : self.loglevel = logging.DEBUG
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
                     self.message_ttl = int(words[1]) * 60 * 1000
                     n = 2

                elif words0 == 'mirror': # See: sr_config.7 FIXME++ too many others?
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

                elif words0 in ['no_logback','nlb']:  # See: sr_subscribe.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.no_logback = True
                        n = 1
                     else :
                        self.no_logback = self.isTrue(words[1])
                        n = 2

                elif words0 in ['notify_only','n','no-download']: # See: sr_subscribe.1  FIXME... doesn't work for sarra? sender?
                     self.logger.debug("option %s" % words[0])
                     self.notify_only = True
                     n = 1

                elif words0 == 'on_file': # See: sr_config.7, sr_sarra,shovel,subscribe
                     self.on_file = None
                     self.execfile("on_file",words1)
                     if ( self.on_file == None ) and not self.isNone(words1):
                        ok = False
                        needexit = True
                     n = 2

                elif words0 == 'on_line': # See: sr_poll.1
                     self.on_line = None
                     self.execfile("on_line",words1)
                     if ( self.on_line == None ) and not self.isNone(words1):
                        ok = False
                        needexit = True
                     n = 2

                elif ( words0 == 'on_message' ) or ( words0 == 'on_msg' ) : # See: sr_config.1, others...
                     self.on_message = None
                     self.execfile("on_message",words1)
                     if ( self.on_message == None ) and not self.isNone(words1):
                        ok = False
                        needexit = True
                     n = 2

                elif words0 == 'on_part': # See: sr_config, sr_subscribe
                     self.on_part = None
                     self.execfile("on_part",words1)
                     if ( self.on_part == None ) and not self.isNone(words1):
                        ok = False
                        needexit = True
                     n = 2

                elif words0 == 'on_post': # See: sr_config, ++ FIXME many others?
                     self.on_post = None
                     self.execfile("on_post",words1)
                     if ( self.on_post == None ) and not self.isNone(words1):
                        ok = False
                        needexit = True
                     n = 2

                elif words0 in ['overwrite','o'] : # See: sr_config.7, FIXME: others.
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
                                 path = os.path.realpath(path)
                                 self.postpath.append(path)
                                 n = n + 1
                         except: break

                     if n == 1 :
                        self.logger.error("problem with path option")
                        needexit = True

                elif words0 in ['post_broker','pb'] : # See: sr_sarra,sender,shovel,winnow FIXME: add to sr_config
                     urlstr      = words1
                     ok, url     = self.validate_urlstr(urlstr)
                     self.post_broker = url
                     if not ok or not url.scheme in ['amqp','amqps']:
                        self.logger.error("invalid post_broker url (%s)" % urlstr)
                        needexit = True
                     n = 2

                elif words0 in ['post_document_root','pdr']: # See: sr_sarra,sender,shovel,winnow FIXME: add to sr_config
                     if sys.platform == 'win32':
                         self.post_document_root = words1.replace('\\','/')
                     else:
                         self.post_document_root = words1
                     n = 2

                elif words0 in ['post_exchange','pe']: # See: sr_sarra,sender,shovel,winnow FIXME: add to sr_config
                     self.post_exchange = words1
                     n = 2

                elif words0 == 'prefetch': # See: sr_consumer.1  (Nbr of prefetch message when queue is shared)
                     self.prefetch = int(words1)
                     n = 2

                elif words0 == 'pump':  # See: sr_audit.1  (give pump hints or setting errors)
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.pump_flag = True
                        n = 1
                     else :
                        self.pump_flag = self.isTrue(words[1])
                        n = 2

                elif words0 in ['queue_name','qn'] : # See:  sr_config.7, sender, shovel, sub, winnow too much?
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

                elif words0 in ['recursive','rec']: # See: sr_post.1, sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.recursive = True
                        n = 1
                     else :
                        self.recursive = self.isTrue(words[1])
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

                elif words0 in ['rename','rn']: # See: FIXME... sr_poll, sarra, sender, sub, watch? why not sr_config?
                     self.rename = words1
                     n = 2

                elif words0 in ['reset']:  # See: sr_consumer.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.reset = True
                        n = 1
                     else :
                        self.reset = self.isTrue(words[1])
                        n = 2

                elif words0 in ['role']:  # See: sr_audit.1
                     roles  = words[1].lower()
                     user   = words[2]
                     self.users[user] = roles
                     n = 3

                elif words0 == 'sleep': # See: sr_audit.8 sr_poll.1
                     self.sleep = int(words[1])
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

                elif words0 == 'strip': # See: sr_config.7 ++FIXME too many!?
                     self.strip = int(words[1])
                     n = 2

                elif words0 in ['subtopic','sub'] : # See: sr_config.7 ++FIXME too many!?
                     self.subtopic = words1
                     key = self.topic_prefix + '.' + self.subtopic
                     self.bindings.append( (self.exchange,key) )
                     self.logger.debug("BINDINGS")
                     self.logger.debug("BINDINGS %s"% self.bindings)
                     n = 2

                elif words0 == 'sum': # See: sr_config.7 ++FIXME too many!?
                     self.sumflg = words[1]
                     ok = self.validate_sum()
                     if not ok : needexit = True
                     n = 2

                elif words0 == 'timeout': # See: sr_sarra.8
                     self.timeout = float(words[1])
                     n = 2

                elif words0 == 'to': # See: sr_config.7
                     self.to_clusters = words1
                     n = 2

                elif words0 in ['topic_prefix','tp'] : # See: sr_config.7 ++FIXME too many!?
                     self.topic_prefix = words1

                elif words0 in ['url','u']: # See: sr_config.7 ++FIXME too many!?
                     self.url = urllib.parse.urlparse(words1)
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
                     # if unknown option is supplied, then set to string value.
                     # string value all the words on the option line.
                     # if unknown option is supplied more than once, then make a list
                     value = ' '.join(words[1:])
                     self.logger.warning("unrecognized option %s %s" % (words[0],value))
                     if not hasattr(self,words[0]):
                         setattr(self, words[0],[ value ])
                     else:
                         value2=getattr(self,words[0])
                         value2.append(value)
                         setattr(self,words[0],value2)
                     self.logger.info("extend self.%s = '%s'" % (words[0],getattr(self,words[0])))

        except:
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
                self.logger.error("unknown option %s" % words[0])

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

        if flgs == '0' or flgs == 'R' :
           self.sumalgo = checksum_0()
           return

        sum_error    = False
        self.sumalgo = None
        self.execfile('sumflg',flgs)

        if self.sumalgo == None : sum_error = True

        if not sum_error and not hasattr(self.sumalgo,'set_path' ) : sum_error = True
        if not sum_error and not hasattr(self.sumalgo,'update'   ) : sum_error = True
        if not sum_error and not hasattr(self.sumalgo,'get_value') : sum_error = True

        if sum_error :
           self.logger.error("sumflg %s not working... set to 'd'" % sumflg)
           self.lastflg = 'd'
           self.sumalgo = checksum_d()

    def setlog(self):

        import logging.handlers

        LOG_FORMAT  = ('%(asctime)s [%(levelname)s] %(message)s')

        if not hasattr(self,'logger') :
           logging.basicConfig(level=self.loglevel, format=LOG_FORMAT)
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
        self.logger.setLevel(self.loglevel)
        self.logger.addHandler(self.handler)

        if self.debug :
           self.logger.setLevel(logging.DEBUG)

    # check url and add credentials if needed from credential file

    def validate_urlstr(self,urlstr):

        ok, details = self.credentials.get(urlstr)
        if details == None :
           self.logger.error("bad credential %s" % urlstr)
           return False, urllib.parse.urlparse(urlstr)

        return True, details.url


    def validate_parts(self):
        self.logger.debug("sr_config validate_parts %s" % self.parts)
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
           try    : self.blocksize = self.chunksize_from_str(token[1])
           except :
                    self.logger.error("parts invalid (%s)" % self.parts)
                    return False
        return True

    def validate_sum(self):
        self.logger.debug("sr_config validate_sum %s" % self.sumflg)

        sumflg = self.sumflg.split(',')[0]

        if sumflg == 'z' : sumflg = self.sumflg[2:]

        if sumflg in ['0','n','d','R']: return True

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
          self.debug   = self.silence
          self.error   = print
          self.info    = self.silence
          self.warning = print

def self_test():
    f = open("./bbb.inc","w")
    f.write("randomize False\n")
    f.close()
    f = open("./aaa.conf","w")
    f.write("include bbb.inc\n")
    f.close()
    # instantiation
    logger = test_logger()
    cfg    = sr_config(config="aaa")

    # overwrite logs
    cfg.logger = logger

    # defaults + check isTrue
    cfg.defaults()
    if not cfg.isTrue('true') or cfg.isTrue('false') :
       cfg.logger.error("problem with isTrue")
       cfg.logger.error("TEST FAILED")
       sys.exit(1)

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

    ok, path = cfg.config_path("plugins","scrpt.py",mandatory=True,ctype='py')
    if not ok :
       cfg.logger.error("problem with config_path")
       cfg.logger.error("TEST FAILED")
       os.unlink("./scrpt.py")
       sys.exit(1)

    cfg.this_value  = 0
    cfg.this_script = None
    cfg.execfile("this_script",path)
    if cfg.this_script == None :
       cfg.logger.error("problem with execfile")
       cfg.logger.error("TEST FAILED")
       os.unlink("./scrpt.py")
       sys.exit(1)

    cfg.this_script(cfg)
    if cfg.this_value != 1 :
       cfg.logger.error("problem with script ")
       cfg.logger.error("TEST FAILED")
       os.unlink("./scrpt.py")
       sys.exit(1)
    os.unlink("./scrpt.py")

    # general ... 

    cfg.general()
    cfg.logger.info(cfg.user_cache_dir)
    cfg.logger.info(cfg.user_log_dir)    
    cfg.logger.info(cfg.user_config_dir)

    # args ... 

    cfg.randomize = False
    cfg.inplace   = False
    cfg.logrotate = 5
    cfg.args(['--randomize', '--inplace', 'True',  '--logrotate', '10', '-vip', '127.0.0.1', '-interface', 'lo' ])
    if not cfg.randomize   or \
       not cfg.inplace     or \
       cfg.logrotate != 10 :
       cfg.logger.error("problem with args")
       sys.exit(1)


    # has_vip... 

    if not cfg.has_vip():
       cfg.logger.error("has_vip failed")
       sys.exit(1)

    # config... 
    #def isMatchingPattern(self, str, accept_unmatch = False): 
    #def metpx_dirPattern(self,basename,destDir,destName) :
    #def metpx_getDestInfos(self, filename):
    #def validate_urlstr(self,urlstr):
    #def validate_parts(self):
    #def validate_sum(self):


    opt1 = "hostname toto"
    opt2 = "broker amqp://a:b@${HOSTNAME}"
    cfg.option(opt1.split())
    cfg.option(opt2.split())
    if cfg.broker.geturl() != "amqp://a:b@toto" :
       cfg.logger.error("problem with args")
       sys.exit(1)

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

    #opt1 = "sum checksum_AHAH.py"
    #cfg.option(opt1.split())


    opt1 = "remote_config True"
    #opt2 = "remote_config_url http://ddsr1.cmc.ec.gc.ca/keep_this_test_dir"
    opt2 = "remote_config_url http://localhost:8000/keep_this_test_dir"
    cfg.option(opt1.split())
    cfg.option(opt2.split())

    cfg.inplace       = False
    opt1 = "include inplace_true.inc"
    cfg.option(opt1.split())
    if cfg.inplace != True :
       cfg.logger.error(" include http:  did not work")

    cfg.reconnect     = True
    opt1 = "config reconnect_false.conf"
    cfg.option(opt1.split())
    if cfg.reconnect != False :
       cfg.logger.error(" include http:  did not work")

    cfg.set_sumalgo('z,checksum_mg.py')

    #cfg.remote_config = False
    #cfg.inplace       = False
    #opt1 = "include http://ddsr1.cmc.ec.gc.ca/keep_this_test_dir/inplace_true.inc"
    #cfg.option(opt1.split())
    #if cfg.inplace == True :
    #   cfg.logger.error(" include http: worked but should not")

    opt1 = "surplus_opt surplus_value"
    cfg.option(opt1.split())

    if cfg.surplus_opt != "surplus_value" :
       cfg.logger.error(" extended option:  did not work")

    opt1 = "prefetch 10"
    cfg.option(opt1.split())

    if cfg.prefetch != 10 :
       cfg.logger.error(" prefetch option:  did not work")

    cfg.config(cfg.user_config)

    print("TEST PASSED")
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
