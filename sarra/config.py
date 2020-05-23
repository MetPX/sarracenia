#!/usr/bin/env python3

#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Shared Services Canada, 2019
#

"""
 Second version configuration parser

"""

import appdirs
import argparse
import copy
import inspect
import logging
import os
import pathlib
import re
import shutil
import socket

from random import randint

from sarra.sr_util import * 
from sarra.sr_credentials  import *


import sarra.flow
import sarra.flow.shovel
import sarra.moth
import sarra.moth.amqp




"""
   re-write of configuration parser.
   
   Still very incomplete, it does just enough to work with sr.py for now.
   Not usable as a replacement for sr_config.py (yet!) 

   FIXME: respect appdir stuff using an environment variable.
   for not just hard coded as a class variable appdir_stuff

   start with some helper functions.

   then declare sarra.Config class

   follow by the one_config entry point that allows a configuration to be read
   in one call.
"""

def get_package_lib_dir():
    return os.path.dirname(inspect.getfile(Config))

def get_site_config_dir():
    return appdirs.site_config_dir( 
          Config.appdir_stuff['appname'], 
          Config.appdir_stuff['appauthor']  ) 

def get_user_cache_dir():
    return appdirs.user_cache_dir( 
          Config.appdir_stuff['appname'], 
          Config.appdir_stuff['appauthor']  ) 

def get_user_config_dir():
    return appdirs.user_config_dir( 
          Config.appdir_stuff['appname'], 
          Config.appdir_stuff['appauthor']  ) 


def get_pid_filename(component, configuration, no):
   """
     return the file name for the pid file for the specified instance.
   """
   piddir = appdirs.user_cache_dir( Config.appdir_stuff['appname'], Config.appdir_stuff['appauthor']  ) 
   piddir += os.sep + component + os.sep

   if configuration[-5:] == '.conf':
      configuration=configuration[:-5]
   piddir += configuration + os.sep

   return piddir + os.sep + 'sr_' + component + '_' + configuration + '_%02d' % no + '.pid'


def get_log_filename(component, configuration, no):
   """
      return the name of a single logfile for a single instance.
   """
   logdir = appdirs.user_cache_dir( Config.appdir_stuff['appname'],
           Config.appdir_stuff['appauthor']  ) + os.sep + 'log'

   if configuration is None:
      configuration=''
   else:
      configuration='_' + configuration

   if configuration[-5:] == '.conf':
      configuration=configuration[:-5]

   return logdir + os.sep + 'sr_' + component + configuration + '_%02d' % no + '.log'
       
def wget_config(urlstr,path,remote_config_url=False):
    logger.debug("wget_config %s %s" % (urlstr,path))

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
                          logger.info("file %s is up to date (%s)" % (path,urlstr))
                          return True
               except:
                       logger.error("could not compare modification dates... downloading")
                       logger.debug('Exception details: ', exc_info=True)

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

            logger.info("file %s downloaded (%s)" % (path,urlstr))

            return True

    except urllib.error.HTTPError as e:
           if os.path.isfile(path) :
                 logger.warning('file %s could not be processed1 (%s)' % (path,urlstr))
                 logger.warning('resume with the one on the server')
           else:
                 logger.error('Download failed 0: %s' % urlstr)
                 logger.error('Server couldn\'t fulfill the request')
                 logger.error('Error code: %s, %s' % (e.code, e.reason))

    except urllib.error.URLError as e:
           if os.path.isfile(path) :
                 logger.warning('file %s could not be processed2 (%s)' % (path,urlstr))
                 logger.warning('resume with the one on the server')
           else:
                 logger.error('Download failed 1: %s' % urlstr)
                 logger.error('Failed to reach server. Reason: %s' % e.reason)

    except Exception as e:
           if os.path.isfile(path) :
                 logger.warning('file %s could not be processed3 (%s) %s' % (path,urlstr,e.reason))
                 logger.warning('resume with the one on the server')
           else:
                 logger.error('Download failed 2: %s %s' % (urlstr, e.reason) )
                 logger.debug('Exception details: ', exc_info=True)

    try   : os.unlink(path+'.downloading')
    except: pass


    if os.path.isfile(path) :
       logger.warning("continue using existing %s"%path)

    return False


def config_path(subdir,config, mandatory=True, ctype='conf'):
    """
    Given a subdir/config look for file in configish places.

    return Tuple:   Found (True/False), path_of_file_found|config_that_was_not_found
    """
    logger.debug("config_path = %s %s" % (subdir,config))

    if config == None : return False,None

    # remote config

    if config.startswith('http:') :
       urlstr = config
       name   = os.path.basename(config)
       if not name.endswith(ctype) : name += '.' + ctype
       path   = get_user_config_dir() + os.sep + subdir + os.sep + name
       config = name

       logger.debug("http url %s path %s name %s" % (urlstr,path,name))

       # do not allow plugin (Peter's mandatory decision)
       # because plugins may need system or python packages
       # that may not be installed on the current server.
       if subdir == 'plugins' :
          logger.error("it is not allowed to download plugins")
       else :
          ok = Config.wget_config(urlstr,path)

    # priority 1 : config given is a valid path

    logger.debug("config_path %s " % config )
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

    config_path = os.path.join(get_user_config_dir(), subdir, config_name + ext)
    logger.debug("config_path %s " % config_path )

    if os.path.isfile(config_path) :
       return True,config_path

    # priority 3 : config given to site config

    config_path = os.path.join(get_site_config_dir(), subdir, config_name + ext)
    logger.debug("config_path %s " % config_path )

    if os.path.isfile(config_path) :
       return True,config_path

    # priority 4 : plugins

    if subdir == 'plugins' :
        config_path = get_package_lib_dir() + os.sep + 'plugins' + os.sep + config_name + ext
        logger.debug("config_path %s " % config_path )
        if os.path.isfile(config_path) :
           return True,config_path

    # return bad file ... 
    if mandatory :
       if subdir == 'plugins' : logger.error("script not found %s" % config)
       elif config_name != 'plugins' : logger.error("file not found %s" % config)

    return False,config




class Config:

   v2entry_points = [ 'do_download', 'do_get', 'do_poll', 'do_put', 'do_send',
       'on_message', 'on_data', 'on_file', 'on_heartbeat', 'on_housekeeping', 'on_html_page', 'on_line',  
       'on_part', 'on_post', 'on_report', 'on_start', 'on_stop', 'on_watch', 'plugin' ]
   components =  [ 'audit', 'cpost', 'cpump', 'poll', 'post', 'sarra', 'sender', 'shovel', 'subscribe', 'watch', 'winnow' ]

   actions = [ 'add', 'cleanup', 'edit', 'declare', 'disable', 'edit', 'enable', 'foreground', 'list', 'remove', 'restart', 'sanity', 'setup', 'show', 'start', 'stop', 'status' ]

   # lookup in dictionary, respond with canonical version.
   appdir_stuff = { 'appauthor':'science.gc.ca', 'appname':'sarra' }

   synonyms = { 
     'accept_unmatch': 'accempt_unmatched',
     'cache' : 'suppress_duplicates', 
     'no_duplicates' : 'suppress_duplicates', 
     'caching' : 'suppress_duplicates', 
     'cache_basis': 'suppress_duplicates_basis',  'instance' : 'instances',
     'chmod' : 'default_mode', 'chmod_dir' : 'default_dir_mode',
     'chmod_log' : 'default_log_mode',
     'heartbeat' : 'housekeeping',
     'logdays': 'lr_backupCount',
     'logrotate_interval': 'lr_interval',
     \
   }
   credentials = None


   def __init__(self,parent=None ):

       self.bindings =  []
       self.__admin = None
       self.__broker = None
       self.__post_broker = None

       if Config.credentials is None:
          Config.credentials=sr_credentials()
          Config.credentials.read( get_user_config_dir()
              + os.sep + "credentials.conf" )
       # FIXME... Linux only for now, no appdirs
       self.directory = None

       if parent is None:
          self.env = copy.deepcopy(os.environ)
       else:
          for i in parent:
              setattr(self,i,parent[i])

       self.chmod = 0o0
       self.chmod_dir = 0o775
       self.chmod_log = 0o600

       self.declared_exchanges = []
       self.env = {}
       self.v2plugins = {}
       self.plugins = []
       self.exchange = None
       self.filename = None
       self.flatten = '/'
       self.hostname = socket.getfqdn()
       self.sleep = 0.1 
       self.housekeeping = 30
       self.inline = False
       self.inline_max = 4096
       self.inline_encoding = 'guess'
       self.lr_backupCount = 5
       self.lr_interval = 1
       self.lr_when = 'midnight'
       self.masks =  []
       self.instances = 1
       self.mirror = False
       self.post_exchanges = []
       self.pstrip = False
       self.randid = "%04x" % random.randint(0,65536)
       self.settings = {}
       self.strip = 0
       self.tls_rigour = 'normal'
       self.topic_prefix = 'v02.post'
       self.users = {}
       self.vip = None


   def _validate_urlstr(self,urlstr):
       # check url and add credentials if needed from credential file
       ok, details = Config.credentials.get(urlstr)
       if details is None :
           logging.error("bad credential %s" % urlstr)
           return False, urllib.parse.urlparse(urlstr)
       return True, details.url

   @property
   def admin(self):
       return self.__admin

   @admin.setter
   def admin(self,v):
       if type(v) is str:
           ok, url = self._validate_urlstr(v)
           if ok:
               self.__admin = url
       else:
           self.__admin = v

   @property
   def broker(self):
       return self.__broker

   @broker.setter
   def broker(self,v):
       if type(v) is str:
           ok, url = self._validate_urlstr(v)
           if ok:
               self.__broker = url
       else:
           self.__broker = v

   @property
   def post_broker(self):
       return self.__post_broker

   @post_broker.setter
   def post_broker(self,v):
       if type(v) is str:
          ok, url = self._validate_urlstr(v)
          if ok:
             self.__post_broker = url
       else:
          self.__post_broker = v


   def _varsub(self, word):
       """ substitute variable values from options
       """

       if word is None:
           return word
       elif type(word) in [ bool, int, float ]:
           return word
       elif not '$' in word:
           return word

       result = word
       if ( '${BROKER_USER}' in word ) and hasattr(self,'broker') and hasattr(self.broker,'username'):
           result = result.replace('${BROKER_USER}',self.broker.username)
           # FIXME: would this work also automagically if BROKER.USERNAME ?

       if not '$' in result:
           return result
       
       elst = []
       plst = result.split('}')
       for parts in plst :
           try:
               if '{' in parts : elst.append((parts.split('{'))[1])
           except: pass
       for E in elst :
           if E in [ 'PROGRAM' ]:
              e = 'program_name'
           else:
              e = E.lower()
           if hasattr(self, e ):
               repval = getattr( self, e )
               if type(repval) is list:
                  repval = repval[0]
               result = result.replace('${'+E+'}',repval)
               continue
       
           if E in self.env.keys():
               result = result.replace('${'+E+'}',self.env[E])
               if sys.platform == 'win32':
                   result = result.replace('\\','/')
       return result


   def _build_mask(self, option, arguments):
       """ return new entry to be appended to list of masks
       """
       regex = re.compile( arguments[0] )
       if len(arguments) > 1:
            fn=arguments[1]
       else:
            fn=self.filename
   
       return ( arguments[0], self.directory, fn, regex, option.lower() in ['accept','get'], self.mirror, self.strip, self.pstrip, self.flatten )


   def dump(self):
       """ print out what the configuration looks like.
       """
       term = shutil.get_terminal_size((80,20))
       mxcolumns=term.columns
       column=0
       for k in sorted( self.__dict__.keys()):
           v=getattr(self,k)
           if type(v) == urllib.parse.ParseResult:
              v = v.scheme + '://' + v.username + '@' + v.hostname
           ks = str(k)
           vs = str(v)
           if len(vs) > mxcolumns/2:
                vs = vs[0:int(mxcolumns/2)] + '...'
           last_column=column
           column += len(ks) + len(vs) + 3
           if column >= mxcolumns:
               print(',')
               column=len(ks) + len(vs) + 1
           elif last_column > 0:
               print(', ', end='')
           print( ks+'='+vs, end='' )
       print('')

   def dictify(self):
      """
      return a dict version of the cfg... 
      """
      cd=self.__dict__

      if hasattr(self,'admin'):
         cd['admin'] = self.admin

      if hasattr(self,'broker'):
         cd['broker'] = self.broker

      if hasattr(self,'post_broker'):
         cd['post_broker'] = self.post_broker

      return cd

   def _merge_field(self, key, value ):
       if key == 'masks':
          self.masks += value
       else:
          if value is not None:
              setattr(self,key,value)


   def merge(self, oth):
       """ 
       merge to lists of options.

       merge two lists of options if one is cumulative then merge, 
       otherwise if not None, then take value from oth
       """

       if type(oth) == dict:
           for k in oth.keys():
              self._merge_field( k, self._varsub(oth[k]) )
       else:
           for k in oth.__dict__.keys():
              self._merge_field( k, self._varsub(getattr(oth,k)) )
   

   def _override_field(self, key, value ):
       if key == 'masks':
          self.masks += value
       else:
          setattr(self,key,value)


   def override(self, oth):
       """
       override a value in a set of options.

       why override() method and not just assign values to the dictionary?
       in the configuration file, there are various ways to have variable substituion.
       override invokes those, so that they are properly interpreted.  Otherwise,
       you just end up with a literal value.
       """

       if type(oth) == dict:
           for k in oth.keys():
              self._override_field( k, self._varsub(oth[k]) )
       else:
           for k in oth.__dict__.keys():
              self._override_field( k, self._varsub(getattr(oth,k)) )

   def _resolve_exchange(self):
       if not hasattr(self,'exchange') or self.exchange is None:
          self.exchange = 'xs_%s' % self.broker.username
 
          if hasattr(self,'exchange_suffix'):
             self.exchange += '_%s' % self.exchange_suffix
       
          if hasattr(self,'exchange_split') and hasattr(self,'no') and ( self.no > 0 ):
             self.exchange += "%02d" % self.no


   def _parse_binding(self, subtopic):
       """
         FIXME: see original parse, with substitions for url encoding.
                also should sqwawk about error if no exchange or topic_prefix defined.
                also None to reset to empty, not done.
       """
       self._resolve_exchange()
       if hasattr(self,'exchange') and hasattr(self,'topic_prefix'):
           self.bindings.append( (self.topic_prefix,  self.exchange, subtopic) )

   def _parse_v2plugin(self, entryPoint, value ):
       """
       config file parsing for a v2 plugin.

       """
       if not entryPoint in Config.v2entry_points:
           logging.error( "undefined entry point: {} skipped".format(entryPoint) )
           return

       if not entryPoint in self.v2plugins:
           self.v2plugins[entryPoint] = [ value ] 
       else:
           self.v2plugins[entryPoint].append( value )

   def _parse_declare(self, words):

       if words[0] in  [ 'env', 'envvar', 'var', 'value' ]:
           name, value = words[1].split('=')
           self.env[name] = value
       elif words[0] in [ 'option', 'o' ]:
           self._parse_option(words[1],words[2:])
       elif words[0] in [ 'source' , 'subscriber', 'subscribe' ]:
           self.users[words[1]] = words[0] 
       elif words[0] in [ 'exchange' ]:
           self.declared_exchanges.append( words[1] ) 

   def _parse_setting(self, opt, value ):
       """
          v3 plugin accept options for specific modules.
    
          parsed from:
          set sarra.plugins.log.msg.Log.level debug

          example:   
          opt= sarra.plugins.log.msg.Log.level  value = debug

          results in:
          self.settings[ sarra.plugins.log.msg.Log ][level] = debug

          options should be fed to plugin class on instantiation.
          stripped of class... 
               options = { 'level' : 'debug' }
    

       """
       opt_class = '.'.join(opt.split('.')[:-1])
       opt_var   = opt.split('.')[-1]
       if opt_class not in self.settings:
          self.settings[opt_class] = {}

       self.settings[opt_class][opt_var] = ' '.join(value) 

   def parse_file(self, cfg):
       """ add settings in file to self
       """
       for l in open(cfg, "r").readlines():
           line = l.split()
           if (len(line) < 1) or (line[0].startswith('#')):
               continue
   
           line = list( map( lambda x : self._varsub(x), line ) )

           if line[0] in [ 'accept', 'reject', 'get' ]:
               self.masks.append( self._build_mask( line[0], line[1:] ) )
           elif line[0] in [ 'declare' ]:
               self._parse_declare( line[1:] )
           elif line[0] in [ 'include', 'config' ]:
               try:
                   self.parse_file( line[1] )
               except:
                   print( "failed to parse: %s" % line[1] )
           elif line[0] in [ 'subtopic' ]:
               self._parse_binding( line[1] )
           elif line[0] in [ 'import' ]:
               self.plugins.append( line[1] )
           elif line[0] in [ 'set', 'setting', 's' ]:
               self._parse_setting(line[1], line[2:])
           elif line[0] in Config.v2entry_points:
               if line[1] in self.plugins:
                   self.plugins.remove( line[1] )
               self._parse_v2plugin(line[0],line[1])
           elif line[0] in [ 'no-import' ]:
               self._parse_v3unplugin(line[1])
           else:
               k=line[0]
               if k in Config.synonyms:
                  k=Config.synonyms[k]
               setattr( self, k, ' '.join(line[1:]) )

  
   def fill_missing_options(self,component,config):
       """ 
         There are default options that apply only if they are not overridden... 
       """ 
       
       if hasattr(self,'suppress_duplicates'): 
           if (type(self.suppress_duplicates) is str):
               if isTrue(self.suppress_duplicates):
                   self.suppress_duplicates=300
               else:
                   self.suppress_duplicates=durationToSeconds(self.suppress_duplicates)
       else:
           self.suppress_duplicates=0
          
       if not hasattr(self,'suppress_duplicates_basis'): 
           self.suppress_duplicates_basis='data'

       # FIXME: note that v2 *user_cache_dir* is, v3 called:  cfg_run_dir
       if not hasattr(self, 'cfg_run_dir'):
          if config[-5:] == '.conf':
              cfg=config[:-5]
          else:
              cfg=config
          self.cfg_run_dir = os.path.join( get_user_cache_dir(), component, cfg )

       if self.broker is not None:
          self._resolve_exchange()

          queuefile = appdirs.user_cache_dir( Config.appdir_stuff['appname'],
               Config.appdir_stuff['appauthor']  )
          queuefile += os.sep + component + os.sep + config[0:-5] 
          queuefile += os.sep + 'sr_' + component + '.' + config[0:-5] + '.' + self.broker.username 

          if hasattr(self,'exchange_split') and hasattr(self,'no') and ( self.no > 0 ):
              queuefile += "%02d" % self.no
          queuefile  += '.qname'

          if not hasattr(self,'queue_name'):
             if os.path.isfile( queuefile ) :
                 f = open(queuefile,'r')
                 self.queue_name = f.read()
                 f.close()
             else:
                 queue_name = 'q_' + self.broker.username + '.sr_' + component +  '.' + config[0:-5]
                 if hasattr(self,'queue_suffix'): queue_name += '.' + self.queue_suffix
                 queue_name += '.'  + str(random.randint(0,100000000)).zfill(8)
                 queue_name += '.'  + str(random.randint(0,100000000)).zfill(8)
                 self.queue_name = queue_name

          if not os.path.isdir( os.path.dirname(queuefile) ):
              pathlib.Path(os.path.dirname(queuefile)).mkdir(parents=True, exist_ok=True)

          if self.queue_name is not None:
              f=open( queuefile, 'w' )
              f.write( self.queue_name )
              f.close()


       if self.post_broker is not None:
          if not hasattr(self,'post_exchange') or self.post_exchange is None:
              self.post_exchange = 'xs_%s' % self.post_broker.username
 
          if hasattr(self,'post_exchange_suffix'):
                  self.post_exchange += '_%s' % self.post_exchange_suffix

          if hasattr(self,'post_exchange_split'):
                  l = [] 
                  for i in range(0,int(self.post_exchange_split)):
                      y = self.post_exchange + '%02d' %  i
                      l.append(y)
                  self.post_exchange = l
          else:
                  self.post_exchange = [ self.post_exchange ]

       if ( self.bindings == [] and hasattr(self,'exchange') ):
          self.bindings = [ ( self.topic_prefix, self.exchange, '#' ) ] 

   class AddBinding(argparse.Action):
        """
        called by argparse to deal with queue bindings.
        """
        def __call__(self, parser, namespace, values, option_string):
    
            if values == 'None':
                namespace.bindings = []
    
            namespace._resolve_exchange()
    
            if not hasattr(namespace,'topic_prefix'):
               raise 'topic_prefix needed before subtopic'
    
            namespace.bindings.append( ( namespace.topic_prefix, namespace.exchange, values ) )


   def parse_args(self, isPost=False):
        """
           Use argparse.parser to modify defaults.
           FIXME, many FIXME notes below. this is a currently unusable placeholder.
           have not figured this out yet. many issues.
        """
        
        parser=argparse.ArgumentParser( \
             description='Subscribe to one peer, and post what is downloaded' ,\
             formatter_class=argparse.ArgumentDefaultsHelpFormatter )
        
        parser.add_argument('--accept_unmatched', default=self.accept_unmatched, type=bool, nargs='?', help='default selection, if nothing matches' )
        parser.add_argument('--action', '-a', nargs='?', choices=Config.actions, 
             help='action to take on the specified configurations' )
        parser.add_argument('--admin', help='amqp://user@host of peer to manage')
        parser.add_argument('--attempts', type=int, nargs='?', help='how many times to try before queuing for retry')
        parser.add_argument('--base_dir', '-bd', nargs='?', help="path to root of tree for relPaths in messages.")
        parser.add_argument('--batch', type=int, nargs='?', help='how many transfers per each connection')
        parser.add_argument('--blocksize', type=int, nargs='?', help='size to partition files. 0-guess, 1-never, any other number: that size')
        """
           FIXME:  Most of this is gobblygook place holder stuff, by copying from wmo-mesh example.
           Don't really need this to work right now, so just leaving it around as-is.  Challenges:

           -- sizing units,  K, M, G, 
           -- time units s,h,m,d
           -- what to do with verbos.
           -- accept/reject whole mess requires extension deriving a class from argparse.Action.
           
        """
        parser.add_argument('--broker', nargs='?', help='amqp://user:pw@host of peer to subscribe to')
        #parser.add_argument('--clean_session', type=bool, help='start a new session, or resume old one?')
        #parser.add_argument('--clientid', help='like an AMQP queue name, identifies a group of subscribers')
        #parser.add_argument('--component', choices=Config.components, nargs='?', \
        #          help='which component to look for a configuration for' )
        parser.add_argument('--dangerWillRobinson', action='store_true', default=False, help='Confirm you want to do something dangerous')
        parser.add_argument('--debug', action='store_true', help='pring debugging output (very verbose)')
        #parser.add_argument('--dir_prefix', help='local sub-directory to put data in')
        #parser.add_argument('--download', type=bool, help='should download data ?')
        parser.add_argument('--exchange', nargs='?', default=self.exchange, help='root of the topic tree to subscribe to')

        """
        FIXME: in previous parser, exchange is a modifier for bindings, can have several different values for different subtopic bindings.
           as currently coded, just a single value that over-writes previous setting, so only binding to a single exchange is possible.
        """
        
        parser.add_argument('--inline', dest='inline', default=self.inline, action='store_true', help='include file data in the message')
        parser.add_argument('--inline_encoding', choices=[ 'text', 'binary', 'guess'], default=self.inline_encoding, help='encode payload in base64 (for binary) or text (utf-8)')
        parser.add_argument('--inline_max', type=int, default=self.inline_max, help='maximum message size to inline')
        parser.add_argument('--instances', type=int, help='number of processes to run per configuration')
        
        parser.set_defaults( bindings=[] )

        #parser.add_argument('--lag_warn', type=int, help='in seconds, warn if messages older than that')
        #parser.add_argument('--lag_drop', type=int, help='in seconds, drop messages older than that')
        
        # the web server address for the source of the locally published tree.
        parser.add_argument('--loglevel', choices=[ 'notset', 'debug', 'info', 'warning', 'error', 'critical' ], help='encode payload in base64 (for binary) or text (utf-8)')
        parser.add_argument('--no', type=int, help='instance number of this process')
        parser.add_argument('--queue_name', nargs='?', help='name of AMQP consumer queue to create')
        parser.add_argument('--post_broker', nargs='?', help='broker to post downloaded files to')
        #parser.add_argument('--post_baseUrl', help='base url of the files announced')
        parser.add_argument('--post_exchange', nargs='?', help='root of the topic tree to announce')
        parser.add_argument('--post_exchange_split', type=int, nargs='?', help='split output into different exchanges 00,01,...')
        parser.add_argument('--post_topic_prefix', nargs='?', help='allows simultaneous use of multiple versions and types of messages')
        parser.add_argument('--topic_prefix', nargs='?', default=self.topic_prefix, help='allows simultaneous use of multiple versions and types of messages')
        #FIXME: select/accept/reject in parser not implemented.
        parser.add_argument('--select', nargs=1, action='append', help='client-side filtering: accept/reject <regexp>' )
        parser.add_argument('--subtopic', nargs=1, action=Config.AddBinding, help='server-side filtering: MQTT subtopic, wilcards # to match rest, + to match one topic' )

        if isPost:
            parser.add_argument( 'path', nargs='+', help='files to post' )
        else:
            parser.add_argument('action', nargs='?', choices=Config.actions, help='action to take on the specified configurations' )
            parser.add_argument( 'configurations', nargs='*', help='configurations to operate on' )

        args = parser.parse_args()
        #FIXME need to apply _varsub

        self.merge(args)


def default_config( component ):

    cfg = Config()

    cfg.override(  { 'program_name':component, 'directory': os.getcwd(), 'accept_unmatched':True } )
    cfg.override( sarra.moth.default_options )
    cfg.override( sarra.moth.amqp.default_options )

    if component in [ 'shovel' ]:
        cfg.override(  sarra.flow.default_options )
        cfg.override(  sarra.flow.shovel.default_options )

    for g in [ "admin.conf", "default.conf" ]:
        if os.path.exists( get_user_config_dir() + os.sep + g ):
           cfg.parse_file( get_user_config_dir() + os.sep + g )

    return cfg


def one_config( component, config ):

    """
      single call return a fully parsed single configuration for a single component to run.

      read in admin.conf and default.conf

      apply component default overrides ( maps to: component/check ?)
      read in component/config.conf
      parse arguments from command line.
      return config instance item.

      
      appdir_stuff can be to override file locations for testing during development.

    """
    default_cfg = default_config( component )

    store_pwd=os.getcwd()

    os.chdir( get_user_config_dir() )

    for g in [ "admin.conf", "default.conf" ]:
        if os.path.exists( g ):
           default_cfg.parse_file( g )

    cfg = copy.deepcopy(default_cfg)

    os.chdir(component)

    if config[-5:] != '.conf' :
        fname = config + '.conf'
    else:
        fname = config

    cfg.parse_file(fname)

    os.chdir(store_pwd)

    cfg.parse_args()

    cfg.fill_missing_options(component,config)


    #pp = pprint.PrettyPrinter(depth=6) 
    #pp.pprint(cfg)


    return cfg

