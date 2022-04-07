#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#
# sr_config.py : python3 utility tool to configure sarracenia programs
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Sep 22 10:41:32 EDT 2015
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 2 of the License.
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

import glob, inspect, logging
import netifaces, random
import os, os.path
import re, shutil
import socket, subprocess, sys
import time
import urllib, urllib.parse, urllib.request, urllib.error
import sarra
import io
import ssl

import appdirs

from logging import handlers

try :
   from sr_checksum          import *
   from sr_credentials       import *
   from sr_util              import *
   from sr_xattr             import *
except :
   from sarra.sr_checksum    import *
   from sarra.sr_credentials import *
   from sarra.sr_util        import *
   from sarra.sr_xattr       import *

# ======= amqp alternative libraries =======
try:
   import amqplib.client_0_8 as amqplib_0_8
   amqplib_available = True
except ImportError:
   amqplib_available = False
try:
   import pika
   pika_available = True
except ImportError:
   pika_available = False
# ==========================================

if sys.hexversion > 0x03030000:
   from shutil import get_terminal_size
   py2old=False
else: 
   py2old=True 


class StdFileLogWrapper(io.TextIOWrapper):
   """ Wrapper that delegate stream write operations to an underlying logging handler stream

   It borrows the handler buffer at construction time and will update it as the logging rolls
   """
   def __init__(self, handler, stdno):
       super(StdFileLogWrapper, self).__init__(handler.stream.buffer)
       self.stream = handler.stream
       self.handler = handler
       self.stdno = stdno
       self.dup2()

   def write(self, buf):
       if self.stream != self.handler.stream:
           # Support log rotation so need to check if stream changed
           # don't trust self.stream for write operation only there to check the change
           self.stream = self.handler.stream
           self.dup2()
       self.handler.stream.write(buf)

   def fileno(self):
       """ Fake the file descriptor for the underlying standard fd ( 1 or 2 )

       :return: the fileno from the faked std file
       """
       return self.stdno

   def dup2(self):
       """ Avoiding dup2 for win32 since 3.6 with the introduction of _WindowsConsoleIO

       introduced since issue 240: https://github.com/MetPX/sarracenia/issues/240
       :return: None
       """
       if sys.platform != 'win32':
           os.dup2(self.handler.stream.fileno(), self.fileno())

   def flush(self):
       self.buffer.flush()

   def close(self):
       pass

   @property
   def closed(self):
       """ Override the closed property in parent (io.TextIOWrapper)

       This is useful to really redirect the close info from the underlying stream
       """
       return self.buffer.closed

   @property
   def buffer(self):
       return self.handler.stream.buffer


class sr_config:

    def __init__(self,config=None,args=None,action=None):
        if '-V' in sys.argv or '--version' in sys.argv:
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
         
        self.appauthor        = 'science.gc.ca'

        self.appname = os.getenv( 'SR_DEV_APPNAME' )
        if self.appname == None:
            self.appname = 'sarra'
        else:
            print( 'DEVELOPMENT using alternate application name from SR_DEV_APPNAME: %s' % self.appname )

        self.programs         = ['post', 'watch', 'winnow', 'sarra', 'shovel', 'subscribe', 'sender', 'poll', 'report']
        self.programs.extend  ( ['cpost', 'cpump'] )

        self.package_dir      = os.path.dirname(inspect.getfile(sr_credentials))
        self.site_config_dir  = appdirs.site_config_dir(self.appname,self.appauthor)
        self.user_config_dir  = appdirs.user_config_dir(self.appname,self.appauthor)
        self.user_log_dir     = appdirs.user_log_dir   (self.appname,self.appauthor)
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
        var = appdirs.user_cache_dir(self.appname,self.appauthor) + "/var"
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


        try: 
            os.makedirs(self.user_config_dir, 0o775,True)
        except Exception as ex:
            self.logger.warning( "making %s: %s" % ( self.user_config_dir, ex ) )

        try: 
            os.makedirs(self.user_plugins_dir,0o775,True)
        except Exception as ex:
            self.logger.warning( "making %s: %s" % ( self.user_plugins_dir, ex ) )

        try: 
            os.makedirs(self.http_dir, 0o775,True)
        except Exception as ex:
            self.logger.warning( "making %s: %s" % ( self.http_dir, ex ) )


        # default config files
        defn = self.user_config_dir + os.sep + "default.conf"
        if not os.path.exists( defn ):
            with open( defn, 'w' ) as f: 
                f.writelines( [ "# set environment variables for all components to use." ] )

        defn = self.user_config_dir + os.sep + "credentials.conf"
        if not os.path.exists( defn ):
            with open( defn, 'w' ) as f: 
                f.writelines( [ "amqps://anonymous:anonymous@dd.weather.gc.ca" ] )

        # hostname

        self.hostname  = socket.getfqdn()
        self.tls_rigour = 'normal'
        self.tlsctx    = ssl.create_default_context()
        self.randid    = "%04x" % random.randint(0,65536)

        # logging is interactive at start

        self.statehost = False
        self.hostform  = 'short'
        self.loglevel  = logging.INFO
        self.logger = None
        self.handler = None
        self.setlog(interactive=True)
        self.logger.debug("sr_config __init__")

        # program_name

        self.program_name = re.sub(r'(-script\.(pyw|py)|\.exe|\.py)?$', '', os.path.basename(sys.argv[0]) )
        self.program_dir  = self.program_name[3:]
        self.logger.debug("sr_config program_name %s " % self.program_name)

        # config

        self.config_dir    = ''
        self.config_found  = False
        self.config_name   = None
        self.user_config   = config

        # config might be None ... in some program or if we simply instantiate a class
        # but if it is not... it better be an existing file

        # keep a list of extended options

        self.extended_options = []
        self.known_options    = []

        # check arguments

        if args == [] : args = None
        self.user_args       = args

        # remote config 

        if config and config.startswith('http:') :
           urlstr = config
           name   = os.path.basename(config)
           if not name.endswith('.conf') : name += '.conf'
           path   = self.user_config_dir + os.sep + self.program_dir + os.sep + name
           ok = self.wget_config(urlstr,path,remote_config_url=True)
           config = name

        # starting the program we should have a real config file ... ending with .conf

        if config != None :
           mandatory = True
           if action in ['add','edit','enable','remove','rename']: mandatory = False
           usr_cfg = config
           if not config.endswith('.conf') : usr_cfg += '.conf'
           cdir = os.path.dirname(usr_cfg)
           if cdir and cdir != '' : self.config_dir = cdir.split(os.sep)[-1]
           self.config_name = re.sub(r'(\.conf)','',os.path.basename(usr_cfg))
           ok, self.user_config = self.config_path(self.program_dir,usr_cfg,mandatory)
           if ok :
              cdir = os.path.dirname(self.user_config)
              if cdir and cdir != '' : self.config_dir = cdir.split(os.sep)[-1]
              self.config_found  = True
           else :
              self.user_config = config
              self.config_dir = self.program_dir
           self.logger.debug("sr_config config_dir   %s " % self.config_dir  )
           self.logger.debug("sr_config config_name  %s " % self.config_name )
           self.logger.debug("sr_config user_config  %s " % self.user_config )

        self.prog_config = self.user_config_dir + os.sep + self.program_dir + '.conf'
        self.logger.debug("sr_config prog_config  %s " % self.prog_config )

        # build user_cache_dir/program_name/[config_name|None] and make sure it exists

        self.user_cache_dir  = appdirs.user_cache_dir (self.appname,self.appauthor)
        self.user_cache_dir += os.sep + self.program_name.replace('sr_','')
        self.user_cache_dir += os.sep + "%s" % self.config_name
        # user_cache_dir will be created later in configure()

        # host attributes
        #self.supports_extended_attributes = supports_extended_attributes


    def xcl( self, x ):
        if sys.hexversion > 0x03030000 :
            return x.__qualname__.split('.')[0] + ' '
        else:
            return x.__name__ + ' '

    def log_settings(self):

        self.logger.info( "log settings start for %s (version: %s):" % \
           (self.program_name, sarra.__version__) )
        self.logger.info( "\tinflight=%s events=%s use_pika=%s topic_prefix=%s dry_run=%s" % \
           ( self.inflight, self.events, self.use_pika, self.topic_prefix, self.dry_run) )
        self.logger.info( "\tinline=%s events=%s use_amqplib=%s topic_prefix=%s" % \
           ( self.inline, self.events, self.use_amqplib, self.topic_prefix) )
        self.logger.info( "\tsuppress_duplicates=%s basis=%s retry_mode=%s retry_ttl=%sms tls_rigour=%s" % \
           ( self.caching, self.cache_basis, self.retry_mode, self.retry_ttl, self.tls_rigour ) )
        self.logger.info( "\texpire=%sms reset=%s message_ttl=%s prefetch=%s accept_unmatch=%s delete=%s poll_without_vip=%s" % \
           ( self.expire, self.reset, self.message_ttl, self.prefetch, self.accept_unmatch, self.delete, self.poll_without_vip ) )
        self.logger.info( "\theartbeat=%s sanity_log_dead=%s default_mode=%03o default_mode_dir=%03o default_mode_log=%03o discard=%s durable=%s" % \
           ( self.heartbeat, self.sanity_log_dead, self.chmod, self.chmod_dir, self.chmod_log, self.discard, self.durable ) )
        self.logger.info( "\tdeclare_queue=%s declare_exchange=%s bind_queue=%s" % ( self.declare_queue, self.declare_exchange, self.bind_queue ) )
        self.logger.info( "\tpost_on_start=%s preserve_mode=%s preserve_time=%s realpath_post=%s base_dir=%s follow_symlinks=%s" % \
           ( self.post_on_start, self.preserve_mode, self.preserve_time, self.realpath_post, self.base_dir, self.follow_symlinks ) )
        self.logger.info( "\tmirror=%s flatten=%s realpath_post=%s strip=%s base_dir=%s report_back=%s log_reject=%s" % \
           ( self.mirror, self.flatten, self.realpath_post, self.strip, self.base_dir, self.reportback, self.log_reject ) )

        if self.post_broker :
            self.logger.info( "\tpost_base_dir=%s post_base_url=%s post_topic_prefix=%s post_version=%s sum=%s blocksize=%s " % \
               ( self.post_base_dir, self.post_base_url, self.post_topic_prefix, 
                 self.post_version, self.sumflg, self.blocksize ) )

        self.logger.info('\tPlugins configured:')

        if self.program_name == 'sr_poll' :
            self.logger.info( '\t\ton_line: %s' % ''.join( map( self.xcl , self.on_line_list ) ) )
            self.logger.info( '\t\ton_html_page: %s' % ''.join( map( self.xcl , self.on_html_page_list ) ) )
            self.logger.info( '\t\tdo_poll: %s' % ''.join( map( self.xcl , self.do_poll_list ) ) )

        elif self.program_name == 'sr_sender' :
            self.logger.info( '\t\tdo_send: %s' % ''.join( map( self.xcl , self.do_send_list ) ) )
            self.logger.info( '\t\tdo_put : %s' % ''.join( map( self.xcl , self.do_put_list  ) ) )

        elif self.program_name in [ 'sr_watch', 'sr_post' ]:
            self.logger.info( '\t\ton_watch: %s' % ''.join( map( self.xcl , self.on_watch_list ) ) )

        else :
            self.logger.info( '\t\tdo_download: %s' % ''.join( map( self.xcl , self.do_download_list ) ) )
            self.logger.info( '\t\tdo_get     : %s' % ''.join( map( self.xcl , self.do_get_list  ) ) )


        self.logger.info( '\t\ton_message: %s'   % ''.join( map( self.xcl , self.on_message_list ) ) )
        self.logger.info( '\t\ton_data: %s'      % ''.join( map( self.xcl , self.on_data_list ) ) )
        self.logger.info( '\t\ton_part: %s'      % ''.join( map( self.xcl , self.on_part_list ) ) )
        self.logger.info( '\t\ton_file: %s'      % ''.join( map( self.xcl , self.on_file_list ) ) )
        self.logger.info( '\t\ton_post: %s'      % ''.join( map( self.xcl , self.on_post_list ) ) )
        self.logger.info( '\t\ton_heartbeat: %s' % ''.join( map( self.xcl , self.on_heartbeat_list ) ) )
        self.logger.info( '\t\ton_report: %s'    % ''.join( map( self.xcl , self.on_report_list ) ) )
        self.logger.info( '\t\ton_start: %s'     % ''.join( map( self.xcl , self.on_start_list ) ) )
        self.logger.info( '\t\ton_stop: %s'      % ''.join( map( self.xcl , self.on_stop_list ) ) )

        self.logger.info('log_settings end.')



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

    def backslash_space(self,iwords):
        words = []
        lst   = -1
        for w in iwords:
            if lst >= 0 and words[lst].endswith('\\') :
               rw =  words[lst][:-1]
               words[lst] = rw + ' ' + w
            else:
               words.append(w)
               lst += 1
        return words

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

    def check_for_remote_config(self,path):
        self.logger.debug("check_for_remote_config %s" % path)

        # parse once to seek for  remote_config_url

        urlstr = None
        try:
            f = open(path, 'r')
            for line in f.readlines():
                words = line.split()
                if (len(words) >= 1 and not re.compile('^[ \t]*#').search(line)):
                   if words[0] != 'remote_config_url' : continue
                   urlstr = words[1]
                   ok = self.wget_config(urlstr,path,remote_config_url=True)
            f.close()

        except:
            self.logger.error('sr_config/check_for_remote_config failed')
            self.logger.debug('Exception details: ', exc_info=True)

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

        self.check_for_remote_config(path)

        try:
            f = open(path, 'r')
            for line in f.readlines():
                words = line.split()
                if (len(words) >= 1 and not re.compile('^[ \t]*#').search(line)):
                    words = self.backslash_space(words)
                    self.option(words)
            f.close()

        except:
            self.logger.error('sr_config/config 1 failed')
            self.logger.debug('Exception details: ', exc_info=True)

    def config_path(self,subdir,config, mandatory=True, ctype='conf'):
        self.logger.debug("config_path = %s %s" % (subdir,config))

        if config == None : return False,None

        # remote config

        if config.startswith('http:') :
           urlstr = config
           name   = os.path.basename(config)
           if not name.endswith(ctype) : name += '.' + ctype
           path   = self.user_config_dir + os.sep + subdir + os.sep + name
           config = name

           self.logger.debug("http url %s path %s name %s" % (urlstr,path,name))

           # do not allow plugin (Peter's mandatory decision)
           # because plugins may need system or python packages
           # that may not be installed on the current server.
           if subdir == 'plugins' :
              self.logger.error("it is not allowed to download plugins")
           else :
              ok = self.wget_config(urlstr,path)

        # priority 1 : config given is a valid path

        self.logger.debug("config_path %s " % config )
        if os.path.isfile(config) :
           return True,config

        config_file = os.path.basename(config)
        config_name = re.sub(r'(\.inc|\.conf|\.py)','',config_file)
        ext         = config_file.replace(config_name,'')
        if ext == '': ext = '.' + ctype
        config_path = config_name + ext

        # priority 1.5: config file given without extenion...
        if os.path.isfile(config_path) :
           return True,config_path

        # priority 2 : config given is a user one

        config_path = os.path.join(self.user_config_dir, subdir, config_name + ext)
        self.logger.debug("config_path %s " % config_path )

        if os.path.isfile(config_path) :
           return True,config_path

        # priority 3 : config given to site config

        config_path = os.path.join(self.site_config_dir, subdir, config_name + ext)
        self.logger.debug("config_path %s " % config_path )

        if os.path.isfile(config_path) :
           return True,config_path

        # priority 4 : plugins

        if subdir == 'plugins' :
           config_path = self.package_dir + os.sep + 'plugins' + os.sep + config_name + ext
           self.logger.debug("config_path %s " % config_path )
           if os.path.isfile(config_path) :
              return True,config_path

        # return bad file ... 
        if mandatory :
          if subdir == 'plugins' : self.logger.error("script not found %s" % config)
          elif config_name != 'plugins' : self.logger.error("file not found %s" % config)

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
        self.load_sums()

        self.overwrite_defaults()

        # load/reload all config settings

        self.args   (self.user_args)

        # dont need to configure if it is not a config file or for theses actions

        if self.config_found and \
           not self.action   in  [ 'add','edit','enable', 'list', 'rename', 'remove' ]:
           self.config (self.user_config)

        # configure some directories if statehost was set

        self.configure_statehost()

        # verify / complete settings

        if self.config_found and \
           not self.action   in  [ 'add','edit','enable', 'list', 'rename', 'remove' ]:
           self.check()

        # sr_audit is the only program working without config

        if self.program_name == 'sr_audit' : self.check()

        # check extended options

        self.check_extended()

        # register plugins

        self.register_plugins()


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
        try: 
            os.makedirs(self.user_log_dir, 0o775,True)
        except Exception as ex:
            self.logger.warning( "making %s: %s" % ( self.user_log_dir, ex ) )

        # finalize user_cache_dir

        if hostdir and not hostdir in self.user_cache_dir :
           self.user_cache_dir  = appdirs.user_cache_dir (self.appname,self.appauthor)
           self.user_cache_dir += os.sep + hostdir
           self.user_cache_dir += os.sep + self.program_name.replace('sr_','')
           self.user_cache_dir += os.sep + "%s" % self.config_name

        # create user_cache_dir

        if not self.program_name in [ 'sr', 'sr_config' ]:
           self.logger.debug("sr_config user_cache_dir  %s " % self.user_cache_dir ) 
           try: 
                os.makedirs(self.user_cache_dir,  0o775,True)
           except Exception as ex:
                self.logger.warning( "making %s: %s" % ( self.user_cache_dir, ex ) )

    def declare_option(self,option):
        self.logger.debug("sr_config declare_option")
        self.known_options.append(option)

    def defaults(self):
        self.logger.debug("sr_config defaults")
        self.file_time_limit      = self.duration_from_str("60d")
        self.destination_timezone = 'UTC'
        self.retry_mode           = True
        self.retry_ttl            = None

        self.remote_config_url    = None

        self.heartbeat            = 300
        self.last_heartbeat       = nowflt()

        # Logging attributes
        self.loglevel             = logging.INFO
        self.lr_backupCount = 5
        self.lr_interval = 1
        self.lr_when = 'midnight'
        self.report_daemons          = False

        self.bufsize              = self.chunksize_from_str('1M')
        self.timeout              = self.duration_from_str('5m',setting_units='s')

        self.kbytes_ps            = 0

        self.add_sumalgo_list     = []
        self.sumalgos             = {}
        self.sumalgo              = None
        self.lastflg              = None

        self.admin                = None
        self.manager              = None

        # consumer
        self.attempts             = 3   # number of times to attempt downloads.
        self.bindings             = []
        self.broker               = None

        # deal with more locked down brokers by turning these off.
        self.bind_queue      = True
        self.declare_queue   = True
        self.declare_exchange = True

        self.exchange             = None
        self.exchange_split       = False
        self.exchange_suffix      = None
        self.exchanges            = [ 'xlog', 'xpublic', 'xreport', 'xwinnow' ]
        self.topic_prefix         = 'v02.post'
        self.version              = 'v02'
        self.poll_without_vip     = True
        self.post_topic_prefix    = None
        self.post_version         = 'v02'
        self.subtopic             = None

        self.queue_name           = None
        self.queue_suffix         = None
        self.dry_run              = False
        self.durable              = True
        self.expire               = 1000 *60 * 5  # 5 mins = 1000millisec * 60s * 5m 
        self.reset                = False
        self.message_ttl          = None
        self.prefetch             = 25
        self.max_queue_size       = 25000
        self.set_passwords        = True

        self.accept_unmatch       = None     # default changes depending on program
        self.masks                = []       # All the masks (accept and reject)
        self.currentPattern       = None     # defaults to all
        self.currentDir           = os.getcwd()   # mask directory (if needed)
        self.currentFileOption    = None     # should implement metpx like stuff
        self.delete               = False
        self.log_reject           = False

        self.report_exchange      = None
          
        # amqp alternatives
        self.use_pika              = False
        self.use_amqplib           = False

        # cache
        self.cache                = None
        self.caching              = False
        self.cache_basis         = 'path'
        self.cache_stat           = False

        # save/restore
        self.save_fp              = None
        self.save_count           = 1

        # sanify
        self.sanity_log_dead      = int(1.5*self.heartbeat)

        # counter

        self.message_count        = 0
        self.publish_count        = 0

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

        self.outlet               = 'post'
        self.partflg              = '0'
        self.pipe                 = False
        self.post_broker          = None
        self.post_exchange        = None
        self.post_exchange_suffix = None
        self.post_exchange_split  = 0
        self.post_on_start        = True
        self.preserve_mode        = True
        self.preserve_time        = True
        self.pump_flag            = False

        self.randomize            = False
        self.realpath_post        = False
        self.realpath_filter      = False
        self.reconnect            = False
        self.reportback           = True
        self.restore              = False
        self.restore_queue        = None

        self.save                 = False
        self.save_file            = None
        self.sleep                = 0
        self.strip                = 0
        self.simulate             = False
        self.pstrip               = None
        self.source               = None
        self.source_from_exchange = False


        self.users                = {}
        self.users_flag           = False

        self.blocksize            = 0

        self.destfn_script        = None

        self.do_download          = None
        self.do_downloads         = {}

        self.do_get               = None
        self.do_gets              = {}

        self.do_poll              = None
        self.do_polls             = {}
        self.ls_file_index        = -1

        self.do_put               = None
        self.do_puts              = {}

        self.do_send              = None
        self.do_sends             = {}

        self.inline               = False
        self.inline_encoding      = "guess"
        self.inline_max           = 1024

        self.inplace              = False

        self.inflight             = 'unspecified'

        self.notify_only          = False

        self.windows_run         = 'exe'

        # 2 object not to reset in child
        if not hasattr(self,'logpath') :
           self.logpath           = None
        if not hasattr(self,'instance') :
           self.instance          = 0
        self.no                   = -1
        self.nbr_instances        = 1



        self.overwrite            = False

        self.interface            = None
        self.vip                  = None

        # Plugin defaults

        self.on_data              = None
        self.on_part              = None
        self.do_task              = None
        self.on_watch             = None

        self.plugin_times = [ 'destfn_script', 'on_data', 'on_message', 'on_file', 'on_post', \
            'on_heartbeat', 'on_html_page', 'on_part', 'on_line', 'on_watch', 'do_poll', \
            'do_download', 'do_get', 'do_put', 'do_send', 'do_task', 'on_report', \
            'on_start', 'on_stop' ]

        for t in self.plugin_times + [ 'plugin' ]:
            exec( 'self.'+t+' = None' )
            exec( 'self.'+t+'_list = [ ]' )

        #self.execfile("on_message","log_all")

        self.execfile("on_file",'file_log')
        self.execfile("on_post",'post_log')
        self.execfile("on_heartbeat",'hb_log')


        self.execfile("on_heartbeat",'hb_memory')
        self.execfile("on_html_page",'html_page')

        #self.on_post_list = [ self.on_post ]
        self.execfile("on_line",'line_mode')
        self.execfile("on_line", 'line_date')


    # this function converts duration into a specifid unit: [milliseconds, seconds or days]
    # str_value should be a number followed by a unit [s,m,h,d,w] ex. 1w, 4d, 12h
    # setting_units specifies the factor to convert the value into [d,s] seconds by default
    # ex. duration_from_str('48h', 'd') -> 2, for 2 days
    def duration_from_str(self,str_value,setting_units='s'):
        self.logger.debug("sr_config duration_from_str %s unit %s" % (str_value,setting_units))

        factor    = 1

        # most settings are in sec (or millisec)
        if setting_units[-1] == 's' :
           if setting_units == 'ms'   : factor = 1000
           if str_value[-1] in 'sS'   : factor *= 1
           elif str_value[-1] in 'mM' : factor *= 60
           elif str_value[-1] in 'hH' : factor *= 60 * 60
           elif str_value[-1] in 'dD' : factor *= 60 * 60 * 24
           elif str_value[-1] in 'wW' : factor *= 60 * 60 * 24 * 7
           if str_value[-1].isalpha() : str_value = str_value[:-1]

        elif setting_units == 'm'     :
           if str_value[-1] in 'sS'   : factor /= 60
           elif str_value[-1] in 'hH' : factor *= 60
           elif str_value[-1] in 'dD' : factor *= 60 * 24
           if str_value[-1].isalpha() : str_value = str_value[:-1]

        elif setting_units == 'h'     :
           if str_value[-1] in 'sS'   : factor /= (60 * 60)
           elif str_value[-1] in 'mM' : factor /= 60
           elif str_value[-1] in 'dD' : factor *= 24
           if str_value[-1].isalpha() : str_value = str_value[:-1]

        elif setting_units == 'd'     :
           if str_value[-1] in 'hH'   : factor /= 24
           elif str_value[-1] in 'dD' : factor *= 1
           elif str_value[-1] in 'wW' : factor *= 7
           if str_value[-1].isalpha() : str_value = str_value[:-1]

        duration = float(str_value) * factor

        return duration


    def execfile(self, opname, path):
        """
           Add plugins, returning True on Success.
        """
        setattr(self,opname,None)

        if path == 'None' or path == 'none' or path == 'off':
             self.logger.debug("Reset plugin %s to None" % opname ) 
             exec( 'self.' + opname + '_list = [ ]' )
             return True

        ok,script = self.config_path('plugins',path,mandatory=True,ctype='py')
        if ok:
            self.logger.debug("installing %s plugin %s" % (opname, script ) ) 
        else:
            self.logger.error("installing %s plugin %s failed: not found " % (opname, path) ) 
            return False

        self.logger.debug('installing: %s plugin %s' % ( opname, path ) )
        try:
            with open(script) as f:
                exec(compile(f.read(), script, 'exec'))
        except:
            self.logger.error("sr_config/execfile 2 failed for option '%s' and plugin '%s'" % (opname, path))
            self.logger.debug('Exception details: ', exc_info=True)
            return False

        if getattr(self,opname) is None:
            self.logger.error("%s plugin %s incorrect: does not set self.%s" % (opname, path, opname ))
            return False

        if opname == 'plugin' :
            pci = self.plugin.lower()
            exec( pci + ' = ' + self.plugin + '(self)' )
            pcv = eval( 'vars('+ self.plugin +')' )
            for when in self.plugin_times:
                if when in pcv:
                    exec( 'self.' + when + '=' + pci + '.' + when )
                    eval( 'self.' + when + '_list.append(' + pci + '.' + when + ')' )
        else:
            eval( 'self.' + opname + '_list.append(self.' + opname + ')' )

        return True

    def find_file_in_dir(self,d,name,recursive=False):

        if not os.path.isdir(d) : return None

        for e in sorted( os.listdir(d) ):
            f = d+os.sep+e
            if os.path.isdir(f) :
               if not recursive : continue
               rf = self.find_file_in_dir(f,name,recursive)
               if rf : return rf
               continue
            if f and f.endswith(name) : return f

        return None

    def find_conf_file(self,name):

        # check in user program configs

        for p in self.programs:
            f = self.find_file_in_dir( self.user_config_dir +os.sep+ p, name)
            if f : return f

        # check in user plugin configs

        f = self.find_file_in_dir( self.user_config_dir +os.sep+ 'plugins', name, recursive=True)
        if f : return f

        # check in user general configs

        f = self.find_file_in_dir( self.user_config_dir, name )
        if f : return f

        # check in package plugins

        f = self.find_file_in_dir( self.package_dir +os.sep+ 'plugins', name, recursive=True)
        if f : return f

        # check in package examples

        for p in self.programs:
            f = self.find_file_in_dir( self.package_dir +os.sep+ 'examples' +os.sep+ p , name)
            if f : return f

        # not found

        return None


    def heartbeat_check(self):
        now    = nowflt()
        elapse = now - self.last_heartbeat
        if elapse > self.heartbeat :
           self.__on_heartbeat__()
           self.last_heartbeat = now
           # check how on_heartbeat lasted
           hb_last = nowflt() - now
           ratio   = hb_last/self.heartbeat
           # heartbeat needs to be adjusted (to the nearest higher rounded minute)
           if ratio > 0.1 :
              self.logger.warning("on_heartbeat spent more than 10%% of heartbeat (%d)" % self.heartbeat)
              self.heartbeat = int(ratio * 10 * self.heartbeat/60 + 1) * 60
              self.logger.warning("heartbeat set to %d" % self.heartbeat)
           

    def __on_heartbeat__(self):
        self.logger.debug("__on_heartbeat__")

        # invoke on_hearbeat when provided
        for plugin in self.on_heartbeat_list:
            try: 
                plugin(self)
            except:
                self.logger.error( "ssr_config/__on_heartbeat__  3: plugin %s, execution failed." % plugin )
                self.logger.debug('Exception details: ', exc_info=True)

        return True

    def get_exchange_option(self):

        if not self.broker : return self.exchange

        if self.program_name == 'sr_report' :
           if self.exchange == None :
              self.exchange == 'xs_%s' % self.broker.username
              if self.broker.username in self.users.keys():
                 if self.users[self.broker.username] in [ 'feeder', 'admin' ]:
                    self.exchange = 'xreport'

        if self.exchange_suffix :
           self.exchange = 'xs_%s' % self.broker.username + '_' + self.exchange_suffix

        if self.exchange_split :
           self.exchange += '%02d' % ( (self.no > 0) * (self.no -1) )

        return self.exchange

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

        if os.path.isfile(self.prog_config):
           config_dir       = self.config_dir
           self.config_dir  = ''
           self.config(self.prog_config)
           self.config_dir  = config_dir
            
    def has_vip(self): 

        # no vip given... standalone always has vip.
        if self.vip == None: 
           return True

        for i in netifaces.interfaces():
            for a in netifaces.ifaddresses(i):
                j=0
                while( j < len(netifaces.ifaddresses(i)[a]) ) :
                    if self.vip in netifaces.ifaddresses(i)[a][j].get('addr'):
                       return True
                    j+=1
        return False
 
    def isMatchingPattern(self, chaine, accept_unmatch = False): 

        for mask in self.masks:
            self.logger.debug( "isMatchingPattern: mask: %s" % str(mask) )
            pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask
            self.currentPattern    = pattern
            self.currentDir        = maskDir
            self.currentFileOption = maskFileOption
            self.currentRegexp     = mask_regexp
            self.mirror = mirror
            self.strip = strip
            self.pstrip = pstrip
            self.flatten = flatten
            if mask_regexp.match(chaine) :
               if not accepting : 
                  if self.log_reject:
                      self.logger.info( "reject: mask=%s strip=%s pattern=%s" % (str(mask), strip, chaine) )
                  return False
               self.logger.debug( "isMatchingPattern: mask=%s strip=%s" % (str(mask), strip) )
               return True

        if self.log_reject and not accept_unmatch:
             self.logger.info( "reject: unmatched pattern=%s" % (chaine) )

        return accept_unmatch

    def isTrue(self,S):
        s = S.lower()
        if  s == 'true' or s == 'yes' or s == 'on' or s == '1': return True
        return False

    def isNone(self,S):
        s = S.lower()
        if  s == 'false' or s == 'none' or s == 'off' or s == '0': return True
        return False

    def load_sums(self):
        self.logger.debug("load_sums")

        # load sums from package_dir
        sumdirs = []
        sumdirs.append( self.site_config_dir + os.sep + 'sum' + os.sep )
        sumdirs.append( self.package_dir     + os.sep + 'sum' + os.sep )
        sumdirs.append( self.user_config_dir + os.sep + 'sum' + os.sep )

        # loop on possible sum directories
        for d in sumdirs:
            if not os.path.isdir(d) : continue
            # loop on all files in the current directory
            for s in os.listdir(d):
                p = d + s
                if os.path.isdir(p)   : continue
                if s == '__init__.py' : continue

                # load the checksum algo from the file
                if not self.execfile("add_sumalgo",p):
                   self.logger.error("sum file %s did not execute" % p)
                   continue

                # verify that it is an instance of sr_checksum
                if not isinstance(self.add_sumalgo,sr_checksum):
                   self.logger.error("sum file %s add_sumalgo is not inherited from class sr_checksum" % p)
                   continue

                # get its registering name
                try   : register_name = self.add_sumalgo.registered_as()
                except: register_name = None

                if register_name == None:
                   self.logger.error("sum file %s add_sumalgo does not provide a checksum letter/name" % p)
                   continue

                # check if it overwrites one already set
                if register_name in self.sumalgos :
                   self.logger.error("sum file %s add_sumalgo with a checksum letter/name already set, skipped" % p)
                   continue

                # add the sumalgo 
                self.logger.debug("sum file %s add_sumalgo with a checksum letter/name %s" % (p,register_name))
                self.sumalgos[register_name] = self.add_sumalgo

        # setting default to 'd'
        self.set_sumalgo('d')
         
    def list_file(self,path):
        cmd = os.environ.get('PAGER')
        if cmd == None: 
            if sys.platform != 'win32':
                cmd="more"
            else:
                cmd="more.com"

        self.run_command([ cmd, path ] )

    def run_command(self, cmd_list):
        sr_path = os.environ.get('SARRA_LIB')
        sc_path = os.environ.get('SARRAC_LIB')
        import sys
        import subprocess

        try:
            if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 5):
                subprocess.check_call(cmd_list, close_fds=False)
            else:
                self.logger.debug("using subprocess.run")
                if sc_path and cmd_list[0].startswith("sr_cp"):
                    subprocess.run([sc_path+'/'+cmd_list[0]]+cmd_list[1:], check=True)
                elif sr_path and cmd_list[0].startswith("sr"):
                    subprocess.run([sr_path+'/'+cmd_list[0]+'.py']+cmd_list[1:], check=True)
                else:
                    subprocess.run(cmd_list, check=True)
        except subprocess.CalledProcessError as err:
            self.logger.error("subprocess.run failed err={}".format(err))
            self.logger.debug("Exception details:", exc_info=True)

    def register_plugins(self):
        self.logger.debug("register_plugins")

        # registering downloads

        for do_download in self.do_download_list :
            parent_class = do_download.__self__
            if hasattr(parent_class,'registered_as') :
               register_name = parent_class.registered_as()
               if not isinstance(register_name,list): register_name = [register_name]
               for r in register_name:
                   self.logger.debug("registering do_download with '%s'" % r )
                   self.do_downloads[r] = do_download

        # registering gets

        for do_get in self.do_get_list :
            parent_class = do_get.__self__
            if hasattr(parent_class,'registered_as') :
               register_name = parent_class.registered_as()
               if not isinstance(register_name,list): register_name = [register_name]
               for r in register_name:
                   self.logger.debug("registering do_get with '%s'" % r )
                   self.do_gets[r] = do_get

        # registering pools

        for do_poll in self.do_poll_list :
            parent_class = do_poll.__self__
            if hasattr(parent_class,'registered_as') :
               register_name = parent_class.registered_as()
               if not isinstance(register_name,list): register_name = [register_name]
               for r in register_name:
                   self.logger.debug("registering do_poll with '%s'" % r )
                   self.do_polls[r] = do_poll

        # registering puts

        for do_put in self.do_put_list :
            parent_class = do_put.__self__
            if hasattr(parent_class,'registered_as') :
               register_name = parent_class.registered_as()
               if not isinstance(register_name,list): register_name = [register_name]
               for r in register_name:
                   self.logger.debug("registering do_put with '%s'" % r )
                   self.do_puts[r] = do_put

        # registering sends

        for do_send in self.do_send_list :
            parent_class = do_send.__self__
            if hasattr(parent_class,'registered_as') :
               register_name = parent_class.registered_as()
               if not isinstance(register_name,list): register_name = [register_name]
               for r in register_name:
                   self.logger.debug("registering do_send with '%s'" % r)
                   self.do_sends[r] = do_send

        # FIXME MG sum registering could be done here... 
        #          the simplest code for that is here
        #          you would have to set default to 'd' self.set_sumalgo('d')
        #          after registering the sums
        #          the code for this is in load_sums and pays more attentions
        #          to config, class... etc...

        # registering sums
        # the add_sumalgo is the class... no need to use __self__
         
        #for add_sumalgo in self.add_sumalgo_list :
        #    parent_class = add_sumalgo
        #    if hasattr(parent_class,'registered_as') :
        #       self.sumalgos[parent_class.registered_as()] = self.add_sumalgo


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

        # This code might add an unwanted '/' in front of ndestDir
        # if destDir does not start with a substitution $ and
        # if destDir does not start with a / ... it does not need one

        if destDir[0] != '$' and destDir[0] != '/' :
            if ndestDir[0] == '/' : ndestDir = ndestDir[1:]

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
                 if i >= 0 : destFileName = filename[i+7:].split(':')[0]
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
                 saved_new_file     = self.msg.new_file
                 self.msg.new_file  = destFileName
                 self.destfn_script = None
                 script = spec[13:]
                 self.execfile('destfn_script',script)
                 if self.destfn_script != None :
                    ok = self.destfn_script(self)
                 destFileName       = self.msg.new_file
                 self.destfn_script = old_destfn_script
                 self.msg.new_file  = saved_new_file
                 if destFileName == None : destFileName = old_destFileName
            elif spec == 'TIME':
                 timeSuffix = ':' + time.strftime("%Y%m%d%H%M%S",time.gmtime())
                 if hasattr(self.msg,'time') :
                    timeSuffix = ":" + self.msg.time.split('.')[0]
                 if hasattr(self.msg,'pubtime') :
                    timeSuffix = ":" + self.msg.pubtime.split('.')[0]
                    timeSuffix = timeSuffix.replace('T','')
                 # check for PX or PDS behavior ...
                 # if file already had a time extension keep his...
                 if len(parts[-1]) == 14 and parts[-1][0] == '2' :
                    timeSuffix = ':' + parts[-1]

            else:
                self.logger.error("Don't understand this DESTFN parameter: %s" % spec)
                return (None, None) 
        return destFileName + satnet + timeSuffix

    # modified from metpx SenderFTP
    def sundew_matchPattern(self,BN,EN,BP,keywd,defval) :

        BN6 = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        if len(BN) >= 7 : BN6 = BN[6]

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
        elif keywd[:7] == "{RYYYY}" : return BN6[0:4]       + keywd[7:]
        elif keywd[:5] == "{RMM}"   : return BN6[4:6]       + keywd[5:]
        elif keywd[:5] == "{RDD}"   : return BN6[6:8]       + keywd[5:]
        elif keywd[:5] == "{RHH}"   : return BN6[8:10]      + keywd[5:]
        elif keywd[:5] == "{RMN}"   : return BN6[10:12]     + keywd[5:]
        elif keywd[:5] == "{RSS}"   : return BN6[12:14]     + keywd[5:]

        # Matching with basename parts if given

        if BP != None :
           for i,v in enumerate(BP):
               kw  = '{' + str(i) +'}'
               lkw = len(kw)
               if keywd[:lkw] == kw : return v + keywd[lkw:]

        return defval

    def varsub(self,word):

        buser  = ''
        config = ''
        # options need to check if there
        if hasattr(self,'broker') and self.broker  : buser  = self.broker.username
        if self.config_name : config = self.config_name
        result=word
        if '$' in result :
              result = result.replace('${HOSTNAME}',   self.hostname)
              result = result.replace('${PROGRAM}',    self.program_name)
              result = result.replace('${CONFIG}',     config)
              result = result.replace('${BROKER_USER}',buser)
              result = result.replace('${RANDID}',  self.randid )

        if '$' in result :
              elst = []
              plst = result.split('}')
              for parts in plst :
                  try:
                          if '{' in parts : elst.append((parts.split('{'))[1])
                  except: pass
              for e in elst :
                  try:    
                          repval = eval( '"%s" % self.' + e )
                          # FIXME Peter asked if a list was proposed... we use/set item 0 from that list
                          #       should have a better test than checking for [ ] but it seemed easy that way
                          if '[' in repval and ']' in repval : repval = eval( '"%s" % self.' + e + '[0]' )
                          result = result.replace('${'+e+'}',repval)
                          continue
                  except: pass

                  try:    
                      result = result.replace('${'+e+'}',os.environ.get(e))
                      if sys.platform == 'win32':
                               result = result.replace('\\','/')
                  except: pass

        return(result)


    def option(self,words):
        self.logger.debug("sr_config option %s" % words)

        # option strip out '-' 

        words0 = words[0].strip('-')

        # value : variable substitutions

        words1 = None
        words2 = None
        if len(words) > 1 :
           config = ''
           words1 = self.varsub(words[1])
           
           if len(words) > 2:
              words2 = self.varsub(words[2])

        # parsing

        needexit = False
        n        = 0
        try:
                if words0 in ['accept','get','reject']: # See: sr_config.7
                     accepting   = words0 in [ 'accept', 'get' ]
                     pattern     = words1

                     if sys.platform == 'win32' and (words1.find( '\\' ) >= 0):
                         self.logger.warning( "%s %s" % ( words0, words1 ) )
                         self.logger.warning( "use of backslash \\ is an escape character. For a path separator, use forward slash." )

                     mask_regexp = re.compile(pattern)
                     n = 2

                     if len(words) > 2:
                        save_currentFileOption = self.currentFileOption
                        self.currentFileOption = words2
                        n = 3
                     

                     self.masks.append((pattern, self.currentDir, self.currentFileOption, mask_regexp, accepting, self.mirror, self.strip, self.pstrip, self.flatten ))

                     if len(words) > 2:
                         self.currentFileOption = save_currentFileOption 

                     self.logger.debug("Masks")
                     self.logger.debug("Masks %s"% self.masks)
                elif words0 =='file_time_limit':
                    self.file_time_limit = self.duration_from_str(words1)
                elif words0 == 'destination_timezone':
                    self.destination_timezone = words1
                elif words0 in ['accept_unmatched','accept_unmatch','au']: # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.accept_unmatch = True
                        n = 1
                     else :
                        self.accept_unmatch = self.isTrue(words1)
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
                     self.batch = int(words1)
                     n = 2

                elif words0 in ['base_dir','bd']: # See: sr_config.7  for sr_post.1,sarra,sender,watch
                     if sys.platform == 'win32' and words1.find( '\\' ) :
                         self.logger.warning( "%s %s" % ( words0, words1 ) )
                         self.logger.warning( "use of backslash \\ is an escape character. For a path separator, use forward slash." )

                     if words1.lower() == 'none' : self.base_dir = None
                     else:
                           path = os.path.abspath(words1)
                           if self.realpath_post:
                               path = os.path.realpath(path)
                           if sys.platform == 'win32':
                               self.base_dir = path.replace('\\','/')
                           else:
                               self.base_dir = path
                     # FIXME MG should we test if directory exists ? and warn if not 
                     n = 2

                elif words0 in ['bind_queue','bq']: # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.bind_queue = True
                        n = 1
                     else :
                        self.bind_queue = self.isTrue(words1)
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
                     self.blocksize = self.chunksize_from_str(words1)
                     if self.blocksize == 1:
                        self.parts   =  '1'
                        ok = self.validate_parts()
                             
                     n = 2

                elif words0 == 'bufsize' :   # See: sr_config.7
                     self.bufsize = int(words1)
                     n = 2

                elif words0 in [ 'caching', 'cache', 'no_duplicates', 'noduplicates', 'nd', 'suppress_duplicates', 'sd' ] : # See: sr_post.1 sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.caching = 300
                        n = 1
                     else :
                        if words1.isalpha():
                               self.caching = self.isTrue(words1)
                               if self.caching : self.caching = 300
                        else :
                               # caching setting is in sec 
                               self.caching = int(self.duration_from_str(words1,'s'))
                               if self.caching <= 0 : self.caching = False
                        n = 2
                     if self.caching and not hasattr(self,'heartbeat_cache_installed') :
                        self.execfile("on_heartbeat",'hb_cache')
                        self.heartbeat_cache_installed = True
                     #if self.caching: ####@
                     #   self.cache = sr_cache(self) ####@

                elif words0 in [ 'suppress_duplicates_basis', 'sdb', 'cache_basis', 'cb' ] : # See: sr_post.1 sr_watch.1
                        known_bases = [ 'data', 'name', 'path' ]
                        if words1 in known_bases:
                            self.cache_basis = words1
                        else:
                            self.logger.error("unknown basis for duplicate suppression: %s, should be one of: %s (default: %s)" % \
                                ( words1, known_bases, self.cache_basis ) )

                        n = 2

                elif words0 == 'cache_stat'   : # FIXME! what is this?
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.cache_stat = True
                        n = 1
                     else :
                        self.cache_stat = self.isTrue(words1)
                        n = 2

                elif words0 in [ 'chmod', 'default_mode', 'dm']:    # See: sr_config.7.rst
                     self.chmod = int(words1,8)
                     n = 2

                elif words0 in [ 'chmod_dir', 'default_dir_mode', 'ddm' ]:    # See: sr_config.7.rst
                     self.chmod_dir = int(words1,8)
                     n = 2

                elif words0 in [ 'chmod_log', 'default_log_mode', 'dlm' ]:    
                     self.chmod_log = int(words1,8)
                     n = 2

                elif words0 in ['cluster','cl','from_cluster','fc']: # See: sr_config.7
                     self.cluster = words1 
                     if words1.lower() == 'none' : self.cluster = None
                     n = 2

                elif words0 in ['cluster_aliases','ca']: # See: sr_config.7
                     self.cluster_aliases = words1.split(',')
                     n = 2

                elif words0 in ['config','c','include']: # See: sr_config.7
                     current_dir_confs = glob.glob(words1)
                     for conf in current_dir_confs:
                         ok, include = self.config_path(self.config_dir,conf,mandatory=True,ctype='inc')
                         self.config(include)
                     if not current_dir_confs:
                         config_dir_confs = glob.glob(self.user_config_dir + os.sep + self.program_dir + os.sep + words1)
                         for conf in config_dir_confs:
                             ok, include = self.config_path(self.config_dir,conf,mandatory=True,ctype='inc')
                             self.config(include)
                         if not config_dir_confs:
                             ok, include = self.config_path(self.config_dir,words1,mandatory=True,ctype='inc')
                             self.config(include)
                     n = 2

                elif words0 == 'debug': # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-':
                        self.loglevel = logging.DEBUG
                        n = 1
                     elif self.isTrue(words1):
                        self.loglevel = logging.DEBUG
                        n = 2

                elif words0 in ['declare_exchange','de','dx']: # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.declare_exchange = True
                        n = 1
                     else :
                        self.declare_exchange = self.isTrue(words1)
                        n = 2

                elif words0 in ['declare_queue','dq']: # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.declare_queue = True
                        n = 1
                     else :
                        self.declare_queue = self.isTrue(words1)
                        n = 2

                elif words0 == 'delete': # See: sr_sarra.8
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.delete = True
                        n = 1
                     else :
                        self.delete = self.isTrue(words1)
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
                     if sys.platform == 'win32' and self.currentDir.find( '\\' ) :
                         self.logger.warning( "directory %s" % self.currentDir )
                         self.logger.warning( "use of backslash ( \\ ) is an escape character. For a path separator, use forward slash ( / )." )

                     n = 2

                elif words0 in ['discard','d','download-and-discard']:  # sr_subscribe.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.discard = True
                        n = 1
                     else :
                        self.discard = self.isTrue(words1)
                        n = 2

                elif words0 in ['document_root','dr']: # See sr_post.1,sarra,sender,watch
                     path = os.path.abspath(words1)
                     if self.realpath_post:
                         path = os.path.realpath(path)

                     if sys.platform == 'win32' and words0.find( '\\' ) :
                         self.logger.warning( "%s %s" % (words0, words1) )
                         self.logger.warning( "use of backslash ( \\ ) is an escape character. For a path separator use forward slash ( / )." )

                     if sys.platform == 'win32':
                         self.document_root = path.replace('\\','/')
                     else:
                         self.document_root = path
                     n = 2

                elif words0 == 'do_download': # See sr_config.7, sr_warra, shovel, subscribe
                     ok = self.execfile("do_download",words1)
                     n = 2

                elif words0 == 'do_get': # FIXME MG to document
                     ok = self.execfile("do_get",words1)
                     n = 2

                elif words0 == 'do_put': # FIXME MG to document
                     ok = self.execfile("do_put",words1)
                     n = 2

                elif words0 == 'do_task': # See: sr_config.1, others...
                     ok =self.execfile("do_task",words1)
                     if not ok:
                           needexit = True
                     n = 2

                elif words0 == 'do_poll': # See sr_config.7 and sr_poll.1
                     ok = self.execfile("do_poll",words1)
                     n = 2

                elif words0 == 'do_send': # See sr_config.7, and sr_sender.1
                     ok = self.execfile("do_send",words1)
                     n = 2

                elif words0 == 'dry_run'   : # See sr_config.7 ++
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.dry_run = True
                        n = 1
                     else :
                        self.dry_run = self.isTrue(words1)
                        n = 2

                elif words0 == 'durable'   : # See sr_config.7 ++
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.durable = True
                        n = 1
                     else :
                        self.durable = self.isTrue(words1)
                        n = 2

                elif words0 in ['events','e']:  # See sr_watch.1
                     i = 0
                     if 'deleted' in words1:
                         self.logger.warning("deprecated Event spec: please change 'deleted' --> 'delete'")
                         words1 = words1.replace("deleted","delete")

                     if 'created' in words1:
                         self.logger.warning("deprecated Event spec: please change 'created' --> 'create'")
                         words1 = words1.replace("created","create")

                     if 'linked' in words1:
                         self.logger.warning("deprecated Event spec: please change 'linked' --> 'link'")
                         words1 = words1.replace("linked","link")

                     if 'modified' in words1:
                         self.logger.warning("deprecated event spec: please change 'modified' --> 'modify'")
                         words1 = words1.replace("modified","modify")

                     if 'create'  in words1 : i = i + 1
                     if 'delete'  in words1 : i = i + 1
                     if 'link' in words1 : i = i + 1
                     if 'modify' in words1 : i = i + 1
                     if 'move'  in words1 : i = i + 1
                     
                     if i < len(words1.split(',')) :
                        self.logger.error("events invalid (%s)" % words1)
                        needexit = True

                     self.events = words1
                     n = 2

                elif words0 in ['exchange','ex'] : # See: sr_config.7 ++ everywhere fixme?
                     self.exchange = words1
                     n = 2

                elif words0 in ['exchange_split'] : # FIXME: sr_config.7 ++ everywhere fixme?
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.exchange_split = True
                        n = 1
                     else :
                        self.exchange_split = self.isTrue(words1)
                        n = 2

                elif words0 in ['exchange_suffix'] : # FIXME: sr_config.7 ++ everywhere fixme?
                     self.exchange_suffix = words1
                     n = 2

                elif words0 in [ 'expire', 'expiry' ]: # See: sr_config.7 ++ everywhere fixme?
                     if    words1.lower() == 'none' :
                           self.expire = None
                     else:
                           # rabbitmq setting is in millisec / user in secs
                           self.expire = int(self.duration_from_str(words1,'ms'))
                           if self.expire < 300000 : 
                              self.logger.warning("expire setting (%s) may cause problem...too low" % words1)
                     n = 2

                elif words0 == 'filename': # See: sr_poll.1, sr_sender.1
                     self.currentFileOption = words1
                     n = 2

                elif words0 in ['realpath_filter','fr']: # FIXME: MG new
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.realpath_filter = True
                        n = 1
                     else :
                        self.realpath_filter = self.isTrue(words1)
                        n = 2

                elif words0 in [ 'flatten' ]: # See: sr_poll.1, sr_sender.1
                     self.flatten = words1
                     n = 2

                elif words0 in ['follow_symlinks','fs']: # See: sr_post.1, sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.follow_symlinks = True
                        n = 1
                     else :
                        self.follow_symlinks = self.isTrue(words1)
                        n = 2

                elif words0 in ['force_polling','fp']: # See: sr_post.1, sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.force_polling = True
                        n = 1
                     else :
                        self.force_polling = self.isTrue(words1)
                        n = 2

                elif words0 in ['header']: # See: sr_config.7
                     kvlist = words1.split('=')
                     key    = kvlist[0]
                     value  = kvlist[1]

                     if value.lower() in ['none','null'] :
                        self.headers_to_del.append(key)
                     else :
                        self.headers_to_add [key] = value

                     if key.lower() == "sum":
                           glob_lst = []
                           glob_lst.extend(glob.glob(word) for word in words[2:] if word != [])
                           file_lst = [f for sub_lst in glob_lst for f in sub_lst]  
                           for xfile in file_lst:
                              try: 
                                  x = sr_xattr(xfile)
                                  x.set( 'sum', value )

                                  xmtime = nowstr()
                                  x.set( 'mtime', xmtime )
                                  self.logger.debug("xattr sum set for file: {0} => {1}".format(xfile, value))
                                  x.persist()
                              except:
                                  self.logger.error("could not setxattr (permission denied?)")
                                  self.logger.debug('Exception details: ', exc_info=True)

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
                     self.hostname = words1 
                     n = 2

                elif words0 in ['inline','inl','content' ]: # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.inline = True
                        n = 1
                     else :
                        self.inline = self.isTrue(words1)
                        n = 2

                elif words0 in ['inline_encoding','inlenc','content_encoding' ]: # See: sr_config.7

                     encoding_choices =  [ 'guess', 'text', 'binary' ]
                     if words1.lower() in encoding_choices:
                        self.inline_encoding = words1.lower()
                     else:
                        self.logger.error("inline_encoding must be one of: %s" % encoding_choices )

                     n = 2

                elif words0 in ['inline_max','imx', 'content_max' ]: # See: sr_config.7
                     self.inline_max = int(words1)
                     n = 2

                elif words0 in ['inplace','in','assemble']: # See: sr_sarra.8, sr_post.1, sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.inplace = True
                        n = 1
                     else :
                        self.inplace = self.isTrue(words1)
                        n = 2

                elif words0 in ['instance', 'instances','i']: # See: sr_config.7
                     self.nbr_instances = int(words1)
                     n = 2

                elif words0 == 'interface': # See: sr_poll, sr_winnow
                     self.logger.warning("deprecated *interface* option no longer has any effect, vip is enough." )
                     self.interface = words1
                     n = 2

                elif words0 == 'kbytes_ps': # See: sr_sender 
                     self.kbytes_ps = int(words1)
                     n = 2

                elif words0 in ['lock','inflight']: # See: sr_config.7, sr_subscribe.1
                     if words0 in [ 'lock' ]: # FIXME: remove support in 2019.
                        self.logger.warning( "Deprecated option. Please use *inflight* instead of *lock*" )

                     if words1.lower() in [ 'none' ]: 
                         self.inflight=None
                     elif words1[0].isnumeric() :
                         self.inflight = self.duration_from_str(words1,'s')
                         if self.inflight <= 1 : self.inflight = None
                     else:
                         self.inflight = words1 
                     n = 2

                elif words0 in [ 'log_reject' ]: # See: sr_sarra.8
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.log_reject = True
                        n = 1
                     else :
                        self.log_reject = self.isTrue(words1)
                        n = 2

                elif words0 == 'ls_file_index': # FIX ME to document... position of file in ls
                                                #        use when space in filename is expected
                     self.ls_file_index = int(words1)
                     n = 2


                elif words0 == 'pipe' : # See: FIXME
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.pipe = True
                        n = 1
                     else :
                        self.pipe = self.isTrue(words1)
                        n = 2

                elif words0 == 'restore' : # See: sr_config.7 
                     #-- report_daemons left for transition, should be removed in 2017
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.restore = True
                        n = 1
                     else :
                        self.restore = self.isTrue(words1)
                        n = 2

                elif words0 in ['restore_to_queue', 'restore2queue', 'r2q', 'rq', 'post_queue']: 
                     # FIXME: should be in: sr_shovel.1
                     self.restore_queue = words1
                     n = 2

                elif words0 == 'report_daemons' or words0 == 'report_daemons': # See: sr_config.7 
                     #-- report_daemons left for transition, should be removed in 2017
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.report_daemons = True
                        n = 1
                     else :
                        self.report_daemons = self.isTrue(words1)
                        n = 2

                elif words0 in ['report_exchange', 'lx', 'le'] : # See: sr_config.7 ++ everywhere fixme?
                     self.report_exchange = words1
                     n = 2

                elif words0 in ['logdays', 'ld', 'logrotate', 'lr']:  # See: sr_subscribe.1
                    if words0 in ['logdays', 'ld']:
                        self.logger.warning('Option %s is deprecated please use logrotate or lr instead' % words0)
                    if words1 and len(words1) > 1 and words1[-1] in 'mMhHdD':
                        # this case keeps retro compat with the old interface
                        self.lr_backupCount = int(float(words1[:-1]))
                    else:
                        self.lr_backupCount = int(float(words1))
                    n = 2

                elif words0 in ['logrotate_interval', 'lri']:
                    if words1 and len(words1) > 1 and words1[-1] in 'sSmMhHdD':
                        self.lr_when = words1[-1]
                        self.lr_interval = int(float(words1[:-1]))
                    else:
                        self.lr_interval = int(float(words1))
                    n = 2

                elif words0 in ['loglevel', 'll']:  # See: sr_config.7
                     level = words1.lower()
                     if level in 'critical':
                         self.loglevel = logging.CRITICAL
                     elif level in 'error':
                         self.loglevel = logging.ERROR
                     elif level in 'warning':
                         self.loglevel = logging.WARNING
                     elif level in 'info':
                         self.loglevel = logging.INFO
                     elif level in 'debug':
                         self.loglevel = logging.DEBUG
                     elif level in 'none':
                         self.loglevel = logging.NOTSET
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
                     self.max_queue_size = int(words1)
                     n = 2

                elif words0 in [ 'message-ttl', 'message_ttl' ]:  # See: sr_consumer.7
                     if    words1.lower() == 'none' :
                           self.message_ttl = None
                     else:
                           # rabbitmq setting is in millisec 
                           self.message_ttl = int(self.duration_from_str(words1,'ms'))
                           if self.message_ttl < 300000 :
                              self.logger.warning("message_ttl setting (%s) may cause problem...too low" % words1)
                     n = 2

                elif words0 == 'mirror': # See: sr_config.7 
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.mirror = True
                        n = 1
                     else :
                        self.mirror = self.isTrue(words1)
                        n = 2

                elif words0 == 'move': # See: sr_post.1
                     self.movepath = []
                     self.movepath.append(words1)
                     self.movepath.append(words2)
                     n = 3

                # Internal use only: when instances>1 is used, and the instances are started
                # there are N instances asked to start each one having its own number (no)
                # -no 1,  -no 2, ...  -no N
                elif words0 == 'no':
                     self.no = int(words1)
                     n = 2

                elif words0 in ['notify_only','n','no_download']:  # See: sr_subscribe.1
                    if (words1 is None) or words[0][0:1] == '-':
                        self.notify_only = True
                        n = 1
                    else:
                        self.notify_only = self.isTrue(words1)
                        n = 2

                elif words0 == 'on_data': # See: sr_config.7, sr_sarra,shovel,subscribe
                     if not self.execfile("on_data",words1):
                           ok = False
                           needexit = True
                     n = 2

                elif words0 == 'on_file': # See: sr_config.7, sr_sarra,shovel,subscribe
                     if not self.execfile("on_file",words1):
                           ok = False
                           needexit = True
                     n = 2

                elif words0 in [ 'on_heartbeat', 'on_hb' ]: # See: sr_config.7, sr_sarra,shovel,subscribe
                     if not self.execfile("on_heartbeat",words1):
                           ok = False
                           needexit = True
                     n = 2

                elif words0 == 'on_html_page': # See: sr_config
                     if not self.execfile("on_html_page",words1):
                            ok = False
                            needexit = True
                     n = 2

                elif words0 == 'on_line': # See: sr_poll.1
                     if not self.execfile("on_line",words1):
                           ok = False
                           needexit = True
                     n = 2

                elif words0 in [ 'on_message',  'on_msg' ] : # See: sr_config.1, others...
                     if not self.execfile("on_message",words1):
                           ok = False
                           needexit = True
                     n = 2

                elif words0 == 'on_part': # See: sr_config, sr_subscribe
                     if not self.execfile("on_part",words1):
                           ok = False
                           needexit = True
                     n = 2

                elif words0 == 'on_post': # See: sr_config
                     if not self.execfile("on_post",words1):
                            ok = False
                            needexit = True
                     n = 2

                elif words0 in [ 'on_report',  'on_rpt' ] : # FIXME ... sr_config.1, others...
                     if not self.execfile("on_report",words1):
                           ok = False
                           needexit = True
                     n = 2

                elif words0 == 'on_start': # See: sr_config
                     if not self.execfile("on_start",words1):
                            ok = False
                            needexit = True
                     n = 2

                elif words0 == 'on_stop': # See: sr_config
                     if not self.execfile("on_stop",words1):
                            ok = False
                            needexit = True
                     n = 2

                elif words0 == 'on_watch': # See: sr_config
                     if not self.execfile("on_watch",words1):
                            ok = False
                            needexit = True
                     n = 2

                elif words0 == 'outlet' : # MG FIXME to be documented
                     value = words1.lower()
                     if value in ['post','json','url']:
                           self.outlet = value
                     else:
                           self.logger.error("outlet set to %s ignored" % value )
                     n = 2

                elif words0 in ['overwrite','o'] : # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.overwrite = True
                        n = 1
                     else :
                        self.overwrite = self.isTrue(words1)
                        n = 2

                elif words0 == 'parts': # See: sr_poll.1, sr_watch.1
                     self.parts   = words1
                     ok = self.validate_parts()
                     if not ok : needexit = True
                     n = 2

                # adding paths in command line might be a mess...
                elif words0 in ['path','p']: # See: sr_post.1, sr_watch.1
                     n  = 1
                     pbd = self.post_base_dir

                     for w in words[1:]:

                         # stop if next option
                         if words[0][0:1] == '-' : 
                            if w[0:1] == '-'     : break

                         # adding path (cannot check if it exists we may post a delete)
                         try:
                                 path = self.varsub(w)
                                 if pbd and not pbd in path: path = pbd + os.sep + path

                                 path = os.path.abspath(path)
                                 if self.realpath_post:
                                     path = os.path.realpath(path)
                                
                                 if sys.platform == 'win32':
                                     path = path.replace('\\','/')

                                 self.postpath.append(path)
                                 n = n + 1
                         except: break

                     if n == 1 :
                        self.logger.error("problem with path option")
                        needexit = True

                elif words0 == 'plugin': # See: sr_config
                     if not self.execfile("plugin",words1):
                            ok = False
                            needexit = True
                     n = 2

                elif words0 in ['post_base_dir','pbd']: # See: sr_sarra,sender,shovel,winnow
                     if words1.lower() == 'none' : self.post_base_dir = None
                     else:
                           if sys.platform == 'win32':
                               self.post_base_dir = words1.replace('\\','/')
                           else:
                               self.post_base_dir = words1

                     if sys.platform == 'win32' and words1.find( '\\' ) :
                         self.logger.warning( "%s %s" % (words0, words1) )
                         self.logger.warning( "use of backslash ( \\ ) is an escape character, for a path separator use forward slash ( / )." )

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

                     if sys.platform == 'win32' and words1.find( '\\' ) :
                         self.logger.warning( "%s %s" % (words0, words1) )
                         self.logger.warning( "use of backslash ( \\ ) is an escape character, for a path separator use forward slash ( / )." )

                     if sys.platform == 'win32':
                         self.post_document_root = words1.replace('\\','/')
                     else:
                         self.post_document_root = words1
                     n = 2

                elif words0 in ['post_exchange','pe','px']: # See: sr_sarra,sender,shovel,winnow 
                     self.post_exchange = words1
                     n = 2

                elif words0 in ['post_exchange_suffix']: # FIXME: sr_sarra,sender,shovel,winnow 
                     self.post_exchange_suffix = words1
                     n = 2

                elif words0 in ['post_on_start','pos'] : # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.post_on_start = True
                        n = 1
                     else :
                        self.post_on_start = self.isTrue(words1)
                        n = 2

                elif words0 in ['post_topic_prefix', 'ptp' ]: # FIXME: sr_sarra,sender,shovel,winnow 
                     self.post_topic_prefix = words1
                     if 'v03.' in words1:
                         self.post_version = 'v03'
                     else:
                         self.post_version = 'v02'
                     n = 2

                elif words0 in ['post_exchange_split','pes', 'pxs']: # sr_config.7, sr_shovel.1
                     self.post_exchange_split = int(words1)
                     n = 2

                elif words0 in ['poll_without_vip','pwv'] : # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.poll_without_vip = True
                        n = 1
                     else :
                        self.poll_without_vip = self.isTrue(words1)
                        n = 2

                elif words0 == 'prefetch': # See: sr_consumer.1  (Nbr of prefetch message when queue is shared)
                     self.prefetch = int(words1)
                     n = 2

                elif words0 in ['preserve_mode','pm'] : # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.preserve_mode = True
                        n = 1
                     else :
                        self.preserve_mode = self.isTrue(words1)
                        n = 2

                elif words0 in ['preserve_time','pt'] : # See: sr_config.7
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.preserve_time = True
                        n = 1
                     else :
                        self.preserve_time = self.isTrue(words1)
                        n = 2

                elif words0 == 'pump':  # See: sr_audit.1  (give pump hints or setting errors)
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.pump_flag = True
                        n = 1
                     else :
                        self.pump_flag = self.isTrue(words1)
                        n = 2

                elif words0 in ['queue', 'queue_name','qn'] : # See:  sr_config.7, sender, shovel, sub, winnow too much?
                     self.queue_name = words1
                     if words1.lower() == 'none' : self.queue_name = None
                     n = 2

                elif words0 in ['queue_suffix'] : # See: sr_consumer.1 : but not very usefull... could be removed
                     self.queue_suffix = words1
                     n = 2

                elif words0 in ['randomize','r']: # See: sr_watch.1, sr_post.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.randomize = True
                        n = 1
                     else :
                        self.randomize = self.isTrue(words1)
                        n = 2

                elif words0 in ['realpath_post','realpath','real']: # See: sr_post.1, sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.realpath_post = True
                        n = 1
                     else :
                        self.realpath_post = self.isTrue(words1)
                        n = 2

                elif words0 in ['reconnect','rr']: # See: sr_post.1, sr_watch.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.reconnect = True
                        n = 1
                     else :
                        self.reconnect = self.isTrue(words1)
                        n = 2

                elif words0 in ['remote_config_url']: # See: sr_config.7
                     self.remote_config_url = words1
                     n = 2

                elif words0 in ['rename','rn']: # See: sr_poll, sarra, sender, sub, watch? 
                     self.rename = words1
                     n = 2

                elif words0 in ['report_back','reportback','rb']:  # See: sr_subscribe.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.reportback = True
                        n = 1
                     else :
                        self.reportback = self.isTrue(words1)
                        n = 2

                elif words0 in ['reset']:  # See: sr_consumer.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.reset = True
                        n = 1
                     else :
                        self.reset = self.isTrue(words1)
                        n = 2

                elif words0 in [ 'retry', 'retry_mode']:  # See: sr_consumer.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.retry_mode = True
                        n = 1
                     else :
                        self.retry_mode = self.isTrue(words1)
                        n = 2

                elif words0 in ['retry_ttl']:  # FIXME to be documented
                     if words1.lower() == 'none' :
                           self.retry_ttl = None
                     else:
                           self.retry_ttl = int(self.duration_from_str(words1,'s'))
                     n = 2

                elif words0 in [ 'role', 'declare' ]:  # See: sr_audit.1
                     item = words1.lower()
                     if words0 in [ 'role' ]:
                        self.logger.warning("role option deprecated, please replace with 'declare'" )

                     if item in [ 'source' , 'subscriber', 'subscribe' ]:
                        roles  = item
                        if item == 'subscribe' :
                           roles += 'r'
                        user   = words2
                        self.users[user] = roles
                     elif item in [ 'exchange' ]:
                        self.exchanges.append( words2 )                                                
                     elif item in [ 'env', 'envvar', 'var', 'value' ]:
                        name, value = words2.split('=')
                        os.environ[ name ] = value
                     else:
                        self.logger.error("declare not understood: %s %s" % ( item, words2 ) )
 
                     n = 3

                elif words0 in ['sanity_log_dead','sld'] :   # FIXME ... to document
                     # sanity_log_dead setting is in sec 
                     self.sanity_log_dead = self.duration_from_str(words1,'s')
                     if self.sanity_log_dead <= 0 : self.sanity_log_dead = 0
                     n = 2

                elif words0 == 'save' : # See: sr_config.7 
                     #-- report_daemons left for transition, should be removed in 2017
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.save = True
                        n = 1
                     else :
                        self.save = self.isTrue(words1)
                        n = 2

                elif words0 in [ 'save_file', 'sf' ]: # FIXMEFIXME
                     self.save_file = words1
                     n = 2

                elif words0 in ['set_passwords']:  # See: sr_consumer.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.set_passwords = True
                        n = 1
                     else :
                        self.set_passwords = self.isTrue(words1)
                        n = 2

                elif words0 == 'simulate' : # See: sr_config.7 
                     #-- report_daemons left for transition, should be removed in 2017
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.simulate = True
                        n = 1
                     else :
                        self.simulate = self.isTrue(words1)
                        n = 2
                     if self.simulate and not hasattr(self,'simulate_installed') :
                        self.execfile("plugin",'simulate')
                        self.simulate_installed = True

                elif words0 == 'sleep': # See: sr_audit.8 sr_poll.1
                     # sleep setting is in sec 
                     self.sleep = self.duration_from_str(words1,'s')
                     if self.sleep <= 0 : self.sleep = 0
                     n = 2

                elif words0 == 'source': # See: sr_post.1 sr_watch.1
                     self.source = words1
                     n = 2

                elif words0 in ['source_from_exchange','sfe']: # See: sr_sarra.8
                     if (words1 is None ) or words[0][0:1] == '-' : 
                        self.source_from_exchange = True
                        n = 1
                     else :
                        self.source_from_exchange = self.isTrue(words1)
                        n = 2

                elif words0 == 'statehost':  # MG FIXME to be documented somewhere ???
                     self.statehost = True
                     self.hostform = 'short'
                     if words1 is None or words[0][0:1] == '-':
                        n = 1
                     elif words1.lower() in ['short', 'fqdn']:
                        self.hostform = words1.lower()
                        n = 2
                     else:
                        if not self.isTrue(words1):
                            self.statehost = False
                        n = 2

                elif words0 == 'strip': # See: sr_config.7 
                     if words1.isnumeric() :
                        self.strip  = int(words1)
                        self.pstrip = None
                     else:                   
                        self.strip  = 0
                        self.logger.debug("FIXME: pstrip=%s" % words1 )
                        if sys.platform == 'win32': # why windows does this? no clue...
                             self.pstrip = words1.replace('\\\\','/')
                        else:
                             self.pstrip = words1
                     n = 2

                elif words0 in ['subtopic','sub'] : # See: sr_config.7 

                     if self.isNone(words1):
                         self.subtopic = "None"
                         self.bindings=[] 
                     else:
                         self.subtopic = words1

                         key = self.topic_prefix + '.' + self.subtopic
                         key = key.replace(' ','%20')
                         if key[-2:] == '.#' :
                            key = key[:-2].replace('#','%23') + '.#'
                         else:               
                            key = key.replace('#','%23') 

                         self.exchange = self.get_exchange_option()
                         self.bindings.append( (self.exchange,key) )
                         self.logger.debug("BINDINGS")
                         self.logger.debug("BINDINGS %s"% self.bindings)

                     n = 2

                elif words0 == 'sum': # See: sr_config.7 
                     self.sumflg = words1
                     ok = self.validate_sum()
                     if not ok : 
                        self.logger.error("unknown checksum specified: %s, should be one of: %s or z" % ( self.sumflg, ', '.join(self.sumalgos.keys()) ) )
                        needexit = True
                     n = 2

                elif words0 == 'timeout': # See: sr_sarra.8
                     # timeout setting is in sec 
                     self.timeout = int(self.duration_from_str(words1,'s'))
                     if self.timeout <= 0 : self.timeout = None
                     n = 2

                elif words0 == 'to': # See: sr_config.7
                     self.to_clusters = words1
                     n = 2

                elif words0 in [ 'tls_rigour', 'tls_rigor', 'tlsr' ]: 
                     self.tls_rigour = words1.lower()
                     if self.tls_rigour == 'lax' :
                         self.tlsctx = ssl.create_default_context()
                         self.tlsctx.check_hostname = False
                         self.tlsctx.verify_mode = ssl.CERT_NONE

                     elif self.tls_rigour == 'strict' :
                         self.tlsctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
                         self.tlsctx.options |= ssl.OP_NO_TLSv1
                         self.tlsctx.options |= ssl.OP_NO_TLSv1_1
                         self.tlsctx.check_hostname = True
                         self.tlsctx.verify_mode = ssl.CERT_REQUIRED
                         self.tlsctx.load_default_certs()
                         # TODO Find a way to reintroduce certificate revocation (CRL) in the future
                         #  self.tlsctx.verify_flags = ssl.VERIFY_CRL_CHECK_CHAIN
                         #  https://github.com/MetPX/sarracenia/issues/330


                     elif self.tls_rigour == 'normal' :
                         pass
                     else:
                         self.logger.warning("option tls_rigour must be one of:  lax, normal, strict")
                         
                     n = 2

                elif words0 in ['topic_prefix','tp'] : # See: sr_config.7 
                     self.topic_prefix = words1
                     if 'v03.' in words1:
                         self.version = 'v03'
                     else:
                         self.version = 'v02'

                elif words0 in ['post_base_url','pbu','url','u','post_url']: # See: sr_config.7 
                     if words0 in ['url','u'] : self.logger.warning("option url deprecated please use post_base_url")
                     if words1.lower() == 'none' : self.post_base_url = None
                     else:
                           self.url = urllib.parse.urlparse(words1)
                           self.post_base_url = words1
                     n = 2

                elif words0 == 'use_amqplib': # See: sr_subscribe.1
                     if ((words1 is None) or words[0][0:1] == '-') and not self.use_pika and amqplib_available:
                        self.use_amqplib = True
                        n = 1
                     elif not self.use_pika and amqplib_available:
                        self.use_amqplib = self.isTrue(words1)
                        n = 2
                     else:
                        n = 2

                elif words0 == 'use_pika': # See: sr_subscribe.1
                     if ((words1 is None) or words[0][0:1] == '-') and not self.use_amqplib and pika_available:
                        self.use_pika = True
                        n = 1
                     elif not self.use_amqplib and pika_available:
                        self.use_pika = self.isTrue(words1)
                        n = 2
                     else:
                        n = 2

                elif words0 == 'users':  # See: sr_audit.1
                     if (words1 is None) or words[0][0:1] == '-' : 
                        self.users_flag = True
                        n = 1
                     else :
                        self.users_flag = self.isTrue(words1)
                        n = 2

                elif words0 == 'vip': # See: sr_poll.1, sr_winnow.1
                     self.vip = words1
                     n = 2

                elif words0 in [ 'windows_run', 'wr'  ] : # See: sr_post.1 sr_watch.1
                        known_runs = [ 'exe', 'pyw', 'py' ]
                        if words1 in known_runs:
                            self.windows_run = words1
                        else:
                            self.logger.error("unknown choice of what to run on Windows: %s, should be one of: %s (default: %s)" % \
                                ( words1, known_runs, self.windows_run ) )

                        n = 2

                elif words0 in [ 'xattr_disable', 'xattr_disabled', 'xd' ]   : # FIXME! what is this?
                     if (words1 is None) or words[0][0:1] == '-' : 
                        xattr_disabled = True
                        n = 1
                     else :
                        xattr_disabled = self.isTrue(words1)
                        n = 2
                     if xattr_disabled:
                        self.logger.info("checksum caching in file attributes has been disabled")
                        disable_xattr()

                else :
                     # if unknown option is supplied, create a list for the values 
                     # FIXME: if specifying values on command line, this breaks (including all options)
                     #        dunno solution.  having it take all values allows options with > 1 word, which is very useful
                     #        see post_override plugin.
                     #
                     value = self.varsub(' '.join(words[1:]))
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
                self.logger.error("sr_config/option 4: problem evaluating option %s" % words[0])
                self.logger.debug('Exception details: ', exc_info=True)

        if needexit :
           os._exit(1)

        return n

    def overwrite_defaults(self):
        self.logger.debug("sr_config overwrite_defaults")

    def print_configdir(self,prefix,configdir):

        print("\n%s: ( %s )" % (prefix,configdir))
        if py2old: columns=80
        else:
                   term = get_terminal_size((80,20))
                   columns=term.columns

        i=0
        if not os.path.isdir(configdir): 
           print('')
           return

        for confname in sorted( os.listdir(configdir) ):
            if confname[0] == '.' or confname[-1] == '~' : continue
            if os.path.isdir(configdir+os.sep+confname) : continue
            if ( ((i+1)*21) >= columns ): 
                 print('')
                 i=0
            i+=1
            print( "%20s " % confname, end='' )

        print("\n", flush=True)

    def set_sumalgo(self,sumflg):
        self.logger.debug("sr_config set_sumalgo %s" % sumflg)

        if sumflg == self.lastflg : return

        flgs = sumflg

        if len(sumflg) > 2 and sumflg[:2] in ['z,']:
           flgs = sumflg[2:]

        if flgs == self.lastflg : return

        if flgs in [ '0', 'L', 'R' ]:
           self.sumalgo = self.sumalgos['0']
           self.lastflg = flgs
           return

        try   : 
                self.sumalgo = self.sumalgos[flgs]
                self.lastflg = flgs
        except:
                self.logger.error("sumflg %s not working... set to 'd'" % sumflg)
                self.logger.debug('Exception details: ', exc_info=True)
                self.lastflg = 'd'
                self.sumalgo = self.sumalgos['d']

    def setlog(self, interactive=False):
        base_log_format = '%(asctime)s [%(levelname)s] %(message)s'
        if logging.getLogger().hasHandlers():
            for h in logging.getLogger().handlers:
                h.close()
                logging.getLogger().removeHandler(h)
        self.logger = logging.getLogger()
        self.logger.setLevel(self.loglevel)

        if interactive or not self.logpath:
            logging.basicConfig(format=base_log_format, level=self.loglevel)
            self.logger.debug("logging to the console with {}".format(self.logger))
        else:
            handler = self.create_handler(base_log_format, logging.DEBUG)
            self.logger.addHandler(handler)
            if sys.platform != 'win32':
                os.dup2( handler.stream.fileno(), 1 )
                os.dup2( handler.stream.fileno(), 2 )
                # replaced below with os.dup2 calls above, see issue #293
                #sys.stdout = StdFileLogWrapper(handler, 1)
                #sys.stderr = StdFileLogWrapper(handler, 2)
            self.logger.debug("logging to file ({}) with {}".format(self.logpath, self.logger))

    def create_handler(self, log_format, level):
        if self.lr_interval > 0 and self.lr_backupCount > 0:
            os.makedirs(os.path.dirname(self.logpath), exist_ok=True)
            handler = handlers.TimedRotatingFileHandler(self.logpath, when=self.lr_when, interval=self.lr_interval,
                                                        backupCount=self.lr_backupCount)
        else:
            handler = logging.FileHandler(self.logpath)
        handler.setFormatter(logging.Formatter(log_format))
        handler.setLevel(level)
        if self.chmod_log:
            os.chmod(self.logpath, self.chmod_log)
        return handler

    def validate_urlstr(self,urlstr):
        # check url and add credentials if needed from credential file
        ok, details = self.credentials.get(urlstr)
        if details == None :
           self.logger.error("bad credential %s (No details returned)" % urlstr)
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

        if not sumflg in ['L','R'] and not sumflg in self.sumalgos: return False

        try :
                 self.set_sumalgo(sumflg)
        except :
                 self.logger.error("sr_config/validate_sum 5: sum invalid (%s)" % self.sumflg)
                 self.logger.debug('Exception details: ', exc_info=True)
                 return False
        return True

    def wget_config(self,urlstr,path,remote_config_url=False):
        self.logger.debug("wget_config %s %s" % (urlstr,path))

        try :
                req  = urllib.request.Request(urlstr)
                resp = urllib.request.urlopen(req)
                if os.path.isfile(path) :
                   try:
                           info = resp.info()
                           ts = time.strptime(info.get('Last-Modified'),"%a, %d %b %Y %H:%M:%S %Z")
                           last_mod_remote = time.mktime(ts)
                           last_mod_local  = os.stat(path).st_mtime
                           if last_mod_remote <= last_mod_local:
                              self.logger.info("file %s is up to date (%s)" % (path,urlstr))
                              return True
                   except: 
                           self.logger.error("could not compare modification dates... downloading")
                           self.logger.debug('Exception details: ', exc_info=True)

                fp = open(path+'.downloading','wb')

                # top program config only needs to keep the url
                # we set option remote_config_url with the urlstr
                # at the first line of the config...
                # includes/plugins  etc... may be left as url in the config...
                # as the urlstr is kept in the config this option would be useless
                # (and damagable for plugins)

                if remote_config_url :
                   fp.write(bytes("remote_config_url %s\n"%urlstr,'utf-8'))

                while True:
                      chunk = resp.read(8192)
                      if not chunk : break
                      fp.write(chunk)
                fp.close()

                try   : os.unlink(path)
                except: pass
                os.rename(path+'.downloading',path)

                self.logger.info("file %s downloaded (%s)" % (path,urlstr))

                return True

        except urllib.error.HTTPError as e:
               if os.path.isfile(path) :
                     self.logger.warning('file %s could not be processed1 (%s)' % (path,urlstr))
                     self.logger.warning('resume with the one on the server')
               else:
                     self.logger.error('Download failed 0: %s' % urlstr)                    
                     self.logger.error('Server couldn\'t fulfill the request')
                     self.logger.error('Error code: %s, %s' % (e.code, e.reason))

        except urllib.error.URLError as e:
               if os.path.isfile(path) :
                     self.logger.warning('file %s could not be processed2 (%s)' % (path,urlstr))
                     self.logger.warning('resume with the one on the server')
               else:
                     self.logger.error('Download failed 1: %s' % urlstr)                                    
                     self.logger.error('Failed to reach server. Reason: %s' % e.reason)            

        except Exception as e:
               if os.path.isfile(path) :
                     self.logger.warning('file %s could not be processed3 (%s) %s' % (path,urlstr,e.reason))
                     self.logger.warning('resume with the one on the server')
               else:
                     self.logger.error('Download failed 2: %s %s' % (urlstr, e.reason) )
                     self.logger.debug('Exception details: ', exc_info=True)

        try   : os.unlink(path+'.downloading')
        except: pass

        if os.path.isfile(path) :
           self.logger.warning("continue using existing %s"%path)

        return False


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

        if '${DD}' in cdir :
           DD = time.strftime("%d", time.gmtime()) 
           new_dir = new_dir.replace('${DD}',DD)

        if '${HH}' in cdir :
           HH = time.strftime("%H", time.gmtime()) 
           new_dir = new_dir.replace('${HH}',HH)

        if '${YYYY}' in cdir : 
           YYYY = time.strftime("%Y", time.gmtime())
           new_dir = new_dir.replace('${YYYY}',YYYY)

        if '${MM}' in cdir : 
           MM = time.strftime("%m", time.gmtime())
           new_dir = new_dir.replace('${MM}',MM)

        if '${JJJ}' in cdir : 
           JJJ = time.strftime("%j", time.gmtime()) 
           new_dir = new_dir.replace('${JJJ}',JJJ)


        # Parsing cdir to subtract time from it in the following formats
        # time unit can be: sec/mins/hours/days/weeks

        # ${YYYY-[number][time_unit]}
        offset_check = re.search(r'\$\{YYYY-(\d+)(\D)\}', cdir)
        if offset_check:
          seconds = self.duration_from_str(''.join(offset_check.group(1,2)), 's') 

          epoch  = time.mktime(time.gmtime()) - seconds
          YYYY1D = time.strftime("%Y", time.localtime(epoch) ) 
          new_dir = re.sub('\$\{YYYY-\d+\D\}',YYYY1D, new_dir)

        # ${MM-[number][time_unit]}
        offset_check = re.search(r'\$\{MM-(\d+)(\D)\}', cdir)
        if offset_check:
          seconds = self.duration_from_str(''.join(offset_check.group(1,2)), 's') 

          epoch = time.mktime(time.gmtime()) - seconds
          MM1D  =  time.strftime("%m", time.localtime(epoch) ) 
          new_dir = re.sub('\$\{MM-\d+\D\}',MM1D, new_dir)

        # ${JJJ-[number][time_unit]}
        offset_check = re.search(r'\$\{JJJ-(\d+)(\D)\}', cdir)
        if offset_check:
          seconds = self.duration_from_str(''.join(offset_check.group(1,2)), 's') 

          epoch = time.mktime(time.gmtime()) - seconds
          JJJ1D = time.strftime("%j", time.localtime(epoch) )
          new_dir = re.sub('\$\{JJJ-\d+\D\}',JJJ1D, new_dir)

        # ${YYYYMMDD-[number][time_unit]}
        offset_check = re.search(r'\$\{YYYYMMDD-(\d+)(\D)\}', cdir)  
        if offset_check:
          seconds = self.duration_from_str(''.join(offset_check.group(1,2)), 's') 

          epoch = time.mktime(time.gmtime()) - seconds
          YYYYMMDD = time.strftime("%Y%m%d", time.localtime(epoch) )
          new_dir = re.sub('\$\{YYYYMMDD-\d+\D\}', YYYYMMDD, new_dir) 

        new_dir = self.varsub(new_dir)

        return new_dir  
