#!/usr/bin/env python3

#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Shared Services Canada, 2019
#

"""
 Second version configuration parser

"""

import os
import re
import copy
import argparse
import socket
import logging
import appdirs

from random import randint

try :
   from sr_util        import *
   from sr_credentials import *

except :
   from sarra.sr_util        import *
   from sarra.sr_credentials import *


"""
   re-write of configuration parser.
   
   Still very incomplete, it does just enough to work with sr.py for now.
   Not usable as a replacement for sr_config.py (yet!) 

"""


class Config:

   credentials = None

   def __init__(self,parent=None, appdir_stuff={ 'appauthor':'science.gc.ca', 'appname':'sarra' }):

       self.bindings =  []
       self.__broker = None
       self.__post_broker = None

       if Config.credentials is None:
          Config.credentials=sr_credentials()
          Config.credentials.read( 
              appdirs.user_config_dir( appdir_stuff['appname'], 
                                       appdir_stuff['appauthor']  ) 
              + os.sep + "credentials.conf" )
       # FIXME... Linux only for now, no appdirs
       self.directory = None

       if parent is None:
          self.env = copy.deepcopy(os.environ)
       else:
          for i in parent:
              setattr(self,i,parent[i])

       self.exchanges = []
       self.post_exchanges = []
       self.filename = None
       self.flatten = '/'
       self.hostname = socket.getfqdn()
       self.masks =  []
       self.instances = 1
       self.mirror = False
       self.strip = 0
       self.pstrip = False
       self.randid = "%04x" % random.randint(0,65536)
       self.tls_rigour = 'normal'
       self.topic_prefix = 'v02.post'
       self.users = {}


   def _validate_urlstr(self,urlstr):
       # check url and add credentials if needed from credential file
       ok, details = Config.credentials.get(urlstr)
       if details == None :
           logging.error("bad credential %s" % urlstr)
           return False, urllib.parse.urlparse(urlstr)
       return True, details.url

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
       elif type(word) in [ bool, int ]:
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
       #regex = re.compile( arguments[0] )
       if len(arguments) > 1:
            fn=arguments[1]
       else:
            fn=self.filename
   
       return ( arguments[0], self.directory, fn,  \
                option.lower() in ['accept','get'], \
                self.mirror, self.strip, self.pstrip )


   def dump(self):
       """ print out what the configuration looks like.
       """

       for k in sorted( self.__dict__.keys()):
           if k in ['env']:
              print('skipping %s' % k)
           else:
              print( "%s=%s" % ( k, getattr(self,k) ))

   def dictify(self):
      """
      return a dict version of the cfg... 
      """
      cd=self.__dict__

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


   def _parse_binding(self, subtopic):
       """
         FIXME: see original parse, with substitions for url encoding.
                also should sqwawk about error if no exchange or topic_prefix defined.
                also None to reset to empty, not done.
       """
       if hasattr(self,'exchange') and hasattr(self,'topic_prefix'):
           self.bindings.append( (self.topic_prefix,  self.exchange, subtopic) )


   def _parse_declare(self, words):

       if words[0] in  [ 'env', 'envvar', 'var', 'value' ]:
           name, value = words[1].split('=')
           self.env[name] = value
       elif words[0] in [ 'source' , 'subscriber', 'subscribe' ]:
           self.users[words[1]] = words[0] 
       elif words[0] in [ 'exchange' ]:
           self.exchanges.append( words[1] ) 


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
           elif line[0] in [ 'include' ]:
               try:
                   self.parse_file( line[1] )
               except:
                   print( "failed to parse: %s" % line[1] )
           elif line[0] in [ 'subtopic' ]:
               self._parse_binding( line[1] )
           else:
               setattr( self, line[0] , ' '.join(line[1:]) )
  
   def fill_missing_options(self):
       """ 
         There are default options that apply only if they are not overridden... 
       """ 
       if self.broker is not None:
          if not hasattr(self,'exchange') or self.exchange is None:
              self.exchange = 'xs_%s' % self.broker.username
 
          if hasattr(self,'exchange_suffix'):
                  self.exchange += '_%s' % self.exchange_suffix

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
    
            if not hasattr(namespace,'exchange'):
               raise 'exchange needed before subtopic'
    
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
        
        parser.add_argument('--accept_unmatched', default=self.accept_unmatch, type=bool, nargs='?', help='default selection, if nothing matches' )
        parser.add_argument('--action', '-a', nargs='?', \
           choices=[ 'add', 'cleanup', 'edit', 'declare', 'disable', 'edit', 'enable', 'foreground', 'list', 'log', 'remove', 'rename', 'restart', 'sanity', 'setup', 'start', 'stop', 'status' ], help='action to take on the specified configurations' )
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
        parser.add_argument('--component', choices=[ 'audit', 'cpost', 'cpump', 'poll', 'post', 'sarra', 'sender', 'shovel' 'subscribe', 'watch', 'winnow' ], \
            nargs='?', help='which component to look for a configuration for')
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
        parser.add_argument('--no', type=int, help='instance number of this process')
        parser.add_argument('--queue_name', nargs='?', help='name of AMQP consumer queue to create')
        parser.add_argument('--post_broker', nargs='?', help='broker to post downloaded files to')
        #parser.add_argument('--post_baseUrl', help='base url of the files announced')
        parser.add_argument('--post_exchange', nargs='?', help='root of the topic tree to announce')
        parser.add_argument('--post_exchange_split', type=int, nargs='?', help='split output into different exchanges 00,01,...')
        parser.add_argument('--post_topic_prefix', nargs='?', help='allows simultaneous use of multiple versions and types of messages')
        parser.add_argument('--topic_prefix', nargs='?', default=self.topic_prefix, help='allows simultaneous use of multiple versions and types of messages')
        parser.add_argument('--select', nargs=1, action='append', help='client-side filtering: accept/reject <regexp>' )
        parser.add_argument('--subtopic', nargs=1, action=Config.AddBinding, help='server-side filtering: MQTT subtopic, wilcards # to match rest, + to match one topic' )

        if isPost:
            parser.add_argument( 'path', nargs='+', help='files to post' )
        else:
            parser.add_argument('action', nargs='?', \
               choices=[ 'add', 'cleanup', 'edit', 'declare', 'disable', 'edit', 'enable', 'foreground', 'list', 'log', 'remove', 'rename', 'restart', 'sanity', 'setup', 'start', 'stop', 'status' ], help='action to take on the specified configurations' )
            parser.add_argument( 'configurations', nargs='*', help='configurations to operate on' )

        args = parser.parse_args()
        #FIXME need to apply _varsub

        self.merge(args)

def one_config( component, config, overrides=None, appdir_stuff={ 'appauthor':'science.gc.ca', 'appname':'sarra' } ):

    """
      single call return a fully parsed single configuration for a single component to run.

      read in default.conf
      FIXME: should read admin.conf ?
      apply component default overrides ( maps to: component/check ?)
      read in component/config.conf
      parse arguments from command line.
      return config instance item.

      appdir_stuff can be to override file locations for testing during development.
    """
    default_cfg_dir = appdirs.user_config_dir( appdir_stuff['appname'], appdir_stuff['appauthor']  )
    default_cfg = Config( parent=None, appdir_stuff=appdir_stuff )
    default_cfg.appdir_stuff = appdir_stuff 

    if overrides:
        default_cfg.override( overrides )

    default_cfg.override(  { 'program_name':component, 
          'configurations': [ config ], 
          'directory':'${PWD}', 
          'accept_unmatch':True } )

    store_pwd=os.getcwd()
    os.chdir( default_cfg_dir )
    default_cfg.parse_file("default.conf")
    cfg = copy.deepcopy(default_cfg)

    os.chdir(component)
    cfg.parse_file(config)

    os.chdir(store_pwd)
    # FIXME... overrides with defaults, instead of only if non-default specified.
    #    unclear how to combine with config file.
    cfg.parse_args()

    cfg.fill_missing_options()

    if ( component in [ 'report', 'sarra', 'sender', 'shovel', 'subscribe', 'winnow' ] ) :
         # a consuming component.
       
         queuefile = appdirs.user_cache_dir( appdir_stuff['appname'], appdir_stuff['appauthor']  )
         queuefile += os.sep + component + os.sep + config[0:-5] 
         queuefile += os.sep + 'sr_' + component + '.' + config + '.' + cfg.broker.username 
         if hasattr(cfg,'exchange_split') and hasattr(cfg,'no') and ( cfg.no > 0 ):
              queuefile += "%02d" % cfg.no
         queuefile  += '.qname'

         if not hasattr(cfg,'queue_name'):
             if os.path.isfile( queuefile ) :
                 f = open(queuefile,'r')
                 cfg.queue_name = f.read()
                 f.close()
             else:
                 queue_name = 'q_' + cfg.broker.username + '.sr_' + component +  '.' + config
                 if hasattr(cfg,'queue_suffix'): queue_name += '.' + cfg.queue_suffix
                 queue_name += '.'  + str(random.randint(0,100000000)).zfill(8)
                 queue_name += '.'  + str(random.randint(0,100000000)).zfill(8)
                 cfg.queue_name = queue_name

         logging.error( 'queue_name set to {}'.format(cfg.queue_name) )
         f=open( queuefile, 'w' )
         f.write( cfg.queue_name )
         f.close()

    #pp = pprint.PrettyPrinter(depth=6) 
    #pp.pprint(cfg)


    return cfg

