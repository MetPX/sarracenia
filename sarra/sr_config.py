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
        # IN BIG DEBUG
        #self.debug = True
        #self.logpath = None
        #self.setlog()

        # appdirs setup... on linux it gives :
        # site_data_dir   = /usr/share/default/sarra   ** unused
        # user_data_dir   = ~/.local/share/sarra       ** unused
        #
        # site_config_dir = /etc/xdg/xdg-default/sarra
        # user_cache_dir  = ~/.cache/sarra
        # user_log_dir    = ~/.cache/sarra/log
        # user_config_dir = ~/.config/sarra
         
        self.appname          = 'sarra'
        self.appauthor        = 'science.gc.ca'

        self.site_config_dir  = site_config_dir(self.appname,self.appauthor)
        self.user_config_dir  = user_config_dir(self.appname,self.appauthor)
        self.user_log_dir     = user_log_dir   (self.appname,self.appauthor)
        self.user_log_dir     = self.user_log_dir.replace(os.sep+'log',os.sep+'var'+os.sep+'log')
        self.user_scripts_dir = self.user_config_dir + '/scripts'

        # umask change for directory creation and chmod

        try    : os.umask(0)
        except : pass

        # make sure the users directories exist

        try    : os.makedirs(self.user_config_dir, 0o775,True)
        except : pass
        try    : os.makedirs(self.user_log_dir,    0o775,True)
        except : pass
        try    : os.makedirs(self.user_scripts_dir,0o775,True)
        except : pass

        # logging is interactive at start

        # IN BIG DEBUG
        #self.debug = True
        self.debug = False
        self.setlog()
        self.logger.debug("sr_config __init__")

        # hostname

        self.hostname     = socket.getfqdn()

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

        # build user_cache_dir/program_name/[config_name|None] and make sure it exists

        self.user_cache_dir   = user_cache_dir (self.appname,self.appauthor)
        self.user_cache_dir  += os.sep + self.program_name.replace('sr_','')
        self.user_cache_dir  += os.sep + "%s" % self.config_name
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

    def config_path(self,subdir,config, mandatory=True):

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
        if mandatory :
          if subdir == 'scripts' : self.logger.error("Script incorrect %s" % config)
          else                   : self.logger.error("File incorrect %s" % config)

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

        self.logrotate            = 5

        self.bufsize              = 8192
        self.kbytes_ps            = 0

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
        self.expire               = None
        self.reset                = False
        self.message_ttl          = None
        self.queue_share          = False

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

        self.batch                = 100
        self.destination          = None
        self.timeout              = None

        # subscribe

        self.discard              = False
        self.flatten              = '/'
        self.no_logback           = False

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

        self.destfn_script        = None
        self.do_download          = None
        self.do_poll              = None
        self.do_send              = None
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


        self.mirror               = False

        self.overwrite            = False
        self.recompute_chksum     = False

        self.interface            = None
        self.vip                  = None


    def execfile(self, opname, path):

        ok,script = self.config_path('scripts',path)
        self.logger.debug("installing script %s " % script ) 

        try    : 
                 exec(compile(open(script).read(), script, 'exec'))
        except : 
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s" % (stype, svalue))
                 self.logger.error("for option %s script %s did not work" % (opname,path))

    def general(self):
        self.logger.debug("sr_config general")

        # read in provided credentials
        credent = self.user_config_dir + os.sep + 'credentials.conf'
        self.cache_url   = {}
        self.credentials = sr_credentials(self.logger)
        self.credentials.read(credent)

        # read in provided rabbit users
        users = self.user_config_dir + os.sep + 'users.conf'
        self.users = {}
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
        # at this level (for includes) user_config = self.user_config_dir

        defconf     = self.user_config_dir + os.sep + 'default.conf'
        self.logger.debug("defconf = %s\n" % defconf)
        if os.path.isfile(defconf) : 
           user_config      = self.user_config
           self.user_config = defconf
           self.config(defconf)
           self.user_config = user_config

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
                if   words0 in ['accept','get','reject']:
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

                elif words0 in ['accept_unmatch','au']:
                     if words[0][0:1] == '-' : 
                        self.accept_unmatch = True
                        n = 1
                     else :
                        self.accept_unmatch = self.isTrue(words[1])
                        n = 2

                # admin: suppose to appear directly under the broker declaration
                # of the default manager account of the cluster in defaults.conf
                elif words0 == 'admin':
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

                elif words0 == 'batch' :
                     self.batch = int(words[1])
                     n = 2

                elif words0 in ['broker','b'] :
                     urlstr      = words1
                     ok, url     = self.validate_urlstr(urlstr)
                     self.broker = url
                     if not ok or not url.scheme in ['amqp','amqps']:
                        self.logger.error("problem with broker (%s)" % urlstr)
                        needexit = True
                     n = 2

                elif words0 == 'bufsize' :
                     self.bufsize = int(words[1])
                     n = 2

                elif words0 == 'chmod':
                     self.chmod = int(words[1])
                     n = 2

                elif words0 in ['cluster','cl']:
                     self.cluster = words1 
                     n = 2

                elif words0 in ['cluster_aliases','ca']:
                     self.cluster_aliases = words1.split(',')
                     n = 2

                elif words0 in ['config','-c','include']:
                     include = os.path.dirname(self.user_config) + os.sep + words1
                     self.logger.debug("include %s" % include)
                     self.config(include)
                     n = 2

                elif words0 == 'debug':
                     if words[0][0:1] == '-' : 
                        self.debug = True
                        n = 1
                     else :
                        self.debug = self.isTrue(words[1])
                        n = 2
                     if self.debug :
                        self.logger.setLevel(logging.DEBUG)

                elif words0 == 'delete':
                     if words[0][0:1] == '-' : 
                        self.delete = True
                        n = 1
                     else :
                        self.delete = self.isTrue(words[1])
                        n = 2

                elif words0 == 'destfn_script':
                     self.destfn_script = None
                     self.execfile("destfn_script",words1)
                     if self.destfn_script == None :
                        self.logger.error("destfn_script script incorrect (%s)" % words[1])
                        ok = False
                     n = 2

                elif words0 == 'destination' :
                     urlstr           = words1
                     ok, url          = self.validate_urlstr(urlstr)
                     self.destination = words1
                     if not ok :
                        self.logger.error("problem with destination (%s)" % urlstr)
                        needexit = True
                     n = 2

                elif words0 == 'directory':
                     self.currentDir = words1
                     n = 2

                elif words0 in ['discard','d','download-and-discard']:
                     if words[0][0:1] == '-' : 
                        self.discard = True
                        n = 1
                     else :
                        self.discard = self.isTrue(words[1])
                        n = 2

                elif words0 in ['document_root','dr']:
                     if sys.platform == 'win32':
                         self.document_root = words1.replace('\\','/')
                     else:
                         self.document_root = words1
                     n = 2

                elif words0 == 'do_download':
                     self.do_download = None
                     self.execfile("do_download",words1)
                     if self.do_download == None :
                        self.logger.error("do_download script incorrect (%s)" % words1)
                        ok = False
                     n = 2

                elif words0 == 'do_poll':
                     self.do_poll = None
                     self.execfile("do_poll",words1)
                     if self.do_poll == None :
                        self.logger.error("do_poll script incorrect (%s)" % words1)
                        ok = False
                     n = 2

                elif words0 == 'do_send':
                     self.do_send = None
                     self.execfile("do_send",words1)
                     if self.do_send == None :
                        self.logger.error("do_send script incorrect (%s)" % words1)
                        ok = False
                     n = 2

                elif words0 == 'durable'   : 
                     if words[0][0:1] == '-' : 
                        self.durable = True
                        n = 1
                     else :
                        self.durable = self.isTrue(words[1])
                        n = 2

                elif words0 in ['events','e']:
                     i = 0
                     if 'IN_CLOSE_WRITE' in words[1] : i = i + 1
                     if 'IN_DELETE'      in words[1] : i = i + 1
                     if i == 0 :
                        self.logger.error("events invalid (%s)" % words[1])
                        needexit = True
                     self.events = words[1]
                     n = 2

                elif words0 in ['exchange','ex'] :
                     self.exchange = words1
                     n = 2

                elif words0 == 'expire' :
                     self.expire = int(words[1]) * 60 * 1000
                     n = 2

                elif words0 == 'filename':
                     self.currentFileOption = words[1]
                     n = 2

                elif words0 in ['flow','f']:
                     self.flow = words1 
                     n = 2

                elif words0 in ['gateway_for','gf']:
                     self.gateway_for = words1.split(',')
                     n = 2

                elif words0 in ['help','h']:
                     self.help()
                     needexit = True

                elif words0 in ['hostname']:
                     self.hostname = words[1] 
                     n = 2

                elif words0 in ['inplace','in']:
                     if words[0][0:1] == '-' : 
                        self.inplace = True
                        n = 1
                     else :
                        self.inplace = self.isTrue(words[1])
                        n = 2

                elif words0 in ['instances','i']:
                     self.nbr_instances = int(words[1])
                     n = 2

                elif words0 == 'interface':
                     self.interface = words[1]
                     n = 2

                elif words0 == 'kbytes_ps':
                     self.kbytes_ps = int(words[1])
                     n = 2

                elif words0 == 'lock':
                     self.lock = words[1] 
                     n = 2

                elif words0 in ['log','l']:
                     self.logpath = words1
                     n = 2

                elif words0 in ['logrotate','lr']:
                     self.logrotate = int(words[1])
                     n = 2

                elif words0 == 'manager' :
                     urlstr       = words1
                     ok, url      = self.validate_urlstr(urlstr)
                     self.manager = url
                     if not ok or not url.scheme in ['amqp','amqps']:
                        self.logger.error("problem with manager (%s)" % urlstr)
                        needexit = True
                     n = 2

                elif words0 == 'message_ttl':
                     self.message_ttl = int(words[1]) * 60 * 1000
                     n = 2

                elif words0 == 'mirror':
                     if words[0][0:1] == '-' : 
                        self.mirror = True
                        n = 1
                     else :
                        self.mirror = self.isTrue(words[1])
                        n = 2

                elif words0 == 'no':
                     self.no = int(words[1])
                     n = 2

                elif words0 in ['no_logback','-nlb']:
                     if words[0][0:1] == '-' : 
                        self.no_logback = True
                        n = 1
                     else :
                        self.no_logback = self.isTrue(words[1])
                        n = 2

                elif words0 in ['notify_only','n','--no-download']:
                     self.logger.debug("option %s" % words[0])
                     self.notify_only = True
                     n = 1

                elif words0 == 'on_file':
                     self.on_file = None
                     self.execfile("on_file",words1)
                     if self.on_file == None :
                        self.logger.error("on_file script incorrect (%s)" % words1)
                        ok = False
                     n = 2

                elif words0 == 'on_line':
                     self.on_line = None
                     self.execfile("on_line",words1)
                     if self.on_line == None :
                        self.logger.error("on_line script incorrect (%s)" % words1)
                        ok = False
                     n = 2

                elif words0 == 'on_message':
                     self.on_message = None
                     self.execfile("on_message",words1)
                     if self.on_message == None :
                        self.logger.error("on_message script incorrect (%s)" % words1)
                        ok = False
                     n = 2

                elif words0 == 'on_part':
                     self.on_part = None
                     self.execfile("on_part",words1)
                     if self.on_part == None :
                        self.logger.error("on_part script incorrect (%s)" % words1)
                        ok = False
                     n = 2

                elif words0 == 'on_post':
                     self.on_post = None
                     self.execfile("on_post",words1)
                     if self.on_post == None :
                        self.logger.error("on_post script incorrect (%s)" % words1)
                        ok = False
                     n = 2

                elif words0 in ['overwrite','o'] :
                     if words[0][0:1] == '-' : 
                        self.overwrite = True
                        n = 1
                     else :
                        self.overwrite = self.isTrue(words[1])
                        n = 2

                elif words0 in ['parts','p']:
                     self.parts   = words[1]
                     ok = self.validate_parts()
                     if not ok : needexit = True
                     n = 2

                elif words0 in ['post_broker','pb'] :
                     urlstr      = words1
                     ok, url     = self.validate_urlstr(urlstr)
                     self.post_broker = url
                     if not ok or not url.scheme in ['amqp','amqps']:
                        self.logger.error("problem with post_broker (%s)" % urlstr)
                        needexit = True
                     n = 2

                elif words0 in ['post_document_root','pdr']:
                     if sys.platform == 'win32':
                         self.post_document_root = words1.replace('\\','/')
                     else:
                         self.post_document_root = words1
                     n = 2

                elif words0 in ['post_exchange','pe']:
                     self.post_exchange = words1
                     n = 2

                elif words0 in ['queue_name','qn'] :
                     self.queue_name = words1
                     n = 2

                elif words0 in ['queue_share','qs'] :
                     if words[0][0:1] == '-' : 
                        self.queue_share = True
                        n = 1
                     else :
                        self.queue_share = self.isTrue(words[1])
                        n = 2

                elif words0 in ['queue_suffix'] :
                     self.queue_suffix = words1
                     n = 2

                elif words0 in ['randomize','r']:
                     if words[0][0:1] == '-' : 
                        self.randomize = True
                        n = 1
                     else :
                        self.randomize = self.isTrue(words[1])
                        n = 2

                elif words0 in ['recompute_chksum','rc']:
                     if words[0][0:1] == '-' : 
                        self.recompute_chksum = True
                        n = 1
                     else :
                        self.recompute_chksum = self.isTrue(words[1])
                        n = 2

                elif words0 in ['reconnect','rr']:
                     if words[0][0:1] == '-' : 
                        self.reconnect = True
                        n = 1
                     else :
                        self.reconnect = self.isTrue(words[1])
                        n = 2

                elif words0 in ['recursive','rec']:
                     if words[0][0:1] == '-' : 
                        self.recursive = True
                        n = 1
                     else :
                        self.recursive = self.isTrue(words[1])
                        n = 2

                elif words0 in ['rename','rn']:
                     self.rename = words1
                     n = 2

                elif words0 in ['reset']:
                     if words[0][0:1] == '-' : 
                        self.reset = True
                        n = 1
                     else :
                        self.reset = self.isTrue(words[1])
                        n = 2

                elif words0 == 'sleep':
                     self.sleep = int(words[1])
                     n = 2

                elif words0 in ['source_from_exchange','sfe']:
                     if words[0][0:1] == '-' : 
                        self.source_from_exchange = True
                        n = 1
                     else :
                        self.source_from_exchange = self.isTrue(words[1])
                        n = 2

                elif words0 == 'strip':
                     self.strip = int(words[1])
                     n = 2

                elif words0 in ['subtopic','sub'] :
                     self.subtopic = words1
                     key = self.topic_prefix + '.' + self.subtopic
                     self.bindings.append( (self.exchange,key) )
                     self.logger.debug("BINDINGS")
                     self.logger.debug("BINDINGS %s"% self.bindings)
                     n = 2

                elif words0 == 'sum':
                     self.sumflg = words[1]
                     ok = self.validate_sum()
                     if not ok : needexit = True
                     n = 2

                elif words0 == 'timeout':
                     self.timeout = float(words[1])
                     n = 2

                elif words0 == 'to':
                     self.to_clusters = words1
                     n = 2

                elif words0 in ['topic_prefix','tp'] :
                     self.topic_prefix = words1

                elif words0 in ['url','u']:
                     self.url = urllib.parse.urlparse(words1)
                     n = 2

                elif words0 == 'vip':
                     self.vip = words[1]
                     n = 2

                else :
                     self.logger.error("problem with option %s" % words[0])

        except:
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
                self.logger.error("problem with option %s" % words[0])

        if needexit :
           sys.exit(1)

        return n

    def overwrite_defaults(self):
        self.logger.debug("sr_config overwrite_defaults")

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
    # instantiation
    cfg = sr_config()

    # overwrite logs
    logger     = test_logger()
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

    ok, path = cfg.config_path("scripts","scrpt.py")
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
    if not os.path.isdir(cfg.user_cache_dir)   or \
       not os.path.isdir(cfg.user_log_dir)     or \
       not os.path.isdir(cfg.user_config_dir)  :
       cfg.logger.error("problem with general user directories ")
       sys.exit(1)

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
    opt3 = "queue_name amqp://a:b@${HOSTNAME}"
    cfg.option(opt1.split())
    cfg.option(opt2.split())
    if cfg.broker.geturl() != "amqp://a:b@toto" :
       cfg.logger.error("problem with args")
       sys.exit(1)

    #cfg.config(self.user_config)

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
