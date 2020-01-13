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



class sr_cfg2:

   logger = None
   credentials = None

   def __init__(self,logger,user_config_dir,parent=None):

       self.bindings =  []
       self.__broker = None
       self.__post_broker = None
       sr_cfg2.logger = logger

       if sr_cfg2.credentials is None:
          sr_cfg2.credentials=sr_credentials(sr_cfg2.logger)
          sr_cfg2.credentials.read( user_config_dir + os.sep + "credentials.conf" )

       # FIXME... Linux only for now, no appdirs
       self.directory = None

       if parent is None:
          self.env = copy.deepcopy(os.environ)

       self.exchanges = []
       self.filename = None
       self.flatten = '/'
       self.hostname = socket.getfqdn()
       self.masks =  []
       self.mirror = False
       self.strip = 0
       self.pstrip = False
       self.randid = "%04x" % random.randint(0,65536)
       self.tls_rigour = 'normal'
       self.topic_prefix = 'v02.post'
       self.users = {}


   def _validate_urlstr(self,urlstr):
       # check url and add credentials if needed from credential file
       ok, details = sr_cfg2.credentials.get(urlstr)
       if details == None :
           self.logger.error("bad credential %s" % urlstr)
           return False, urllib.parse.urlparse(urlstr)
       return True, details.url

   @property
   def broker(self):
       return self.__broker

   @broker.setter
   def broker(self,v):
       if type(v) is str:
           self.logger.warning( "setting broker to: %s" % v )
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
          self.logger.warning( "setting post_broker to: %s" % v )
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

       for k in sorted( self.__dict__.keys()):
           print( "%s=%s" % ( k, getattr(self,k) ))


   def _merge_field(self, key, value ):
       if key == 'masks':
          self.masks += value
       else:
          if value is not None:
              setattr(self,key,value)


   def merge(self, oth):

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
           self.bindings.append( (self.exchange, self.topic_prefix + '.' + subtopic) )


   def _parse_declare(self, words):

       if words[0] in  [ 'env', 'envvar', 'var', 'value' ]:
           name, value = words[1].split('=')
           self.env[name] = value
       elif words[0] in [ 'source' , 'subscriber', 'subscribe' ]:
           self.users[words[0]] = words[1:] 
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
               self.parse_file( line[1] )
           elif line[0] in [ 'subtopic' ]:
               self._parse_binding( line[1] )
           else:
               setattr( self, line[0] , ' '.join(line[1:]) )
  
   def parse_args(self, isPost=False):
        """
           FIXME, many FIXME notes below. this is a currently unusable placeholder.
           have not figured this out yet. many issues.
        """
        
        parser=argparse.ArgumentParser( \
             description='Subscribe to one peer, and post what is downloaded' ,\
             formatter_class=argparse.ArgumentDefaultsHelpFormatter )
        
        #FIXME accept/reject processing missing here.
        parser.add_argument('--accept_unmatched', type=bool, default=False, nargs='?', help='default selection, if nothing matches' )
        parser.add_argument('--action', '-a', nargs='?', \
           choices=[ 'add', 'cleanup', 'edit', 'declare', 'disable', 'edit', 'enable', 'foreground', 'list', 'log', 'remove', 'rename', 'restart', 'sanity', 'setup', 'start', 'stop', 'status' ], help='action to take on the specified configurations' )
        parser.add_argument('--admin', default='amqp://admin@' + self.hostname, help='amqp://user@host of peer to manage')
        parser.add_argument('--attempts', type=int, default=3, nargs='?', help='how many times to try before queuing for retry')
        parser.add_argument('--base_dir', '-bd', default=None, nargs='?', help="path to root of tree for relPaths in messages.")
        parser.add_argument('--batch', type=int, default=100, nargs='?', help='how many transfers per each connection')
        parser.add_argument('--blocksize', type=int, default=0, nargs='?', help='size to partition files. 0-guess, 1-never, any other number: that size')
        """
           FIXME:  Most of this is gobblygook place holder stuff, by copying from wmo-mesh example.
           Don't really need this to work right now, so just leaving it around as-is.  Challenges:

           -- sizing units,  K, M, G, 
           -- time units s,h,m,d
           -- what to do with verbos.
           -- accept/reject whole mess requires extension deriving a class from argparse.Action.
           
        """
        parser.add_argument('--broker', default=None, nargs='?', help='amqp://user:pw@host of peer to subscribe to')
        #parser.add_argument('--clean_session', type=bool, default=False, help='start a new session, or resume old one?')
        #parser.add_argument('--clientid', default=host, help='like an AMQP queue name, identifies a group of subscribers')
        parser.add_argument('--component', choices=[ 'audit', 'cpost', 'cpump', 'poll', 'post', 'sarra', 'sender', 'shovel' 'subscribe', 'watch', 'winnow' ], \
            nargs='?', help='which component to look for a configuration for')
        #parser.add_argument('--dir_prefix', default='data', help='local sub-directory to put data in')
        #parser.add_argument('--download', type=bool, default=True, help='should download data ?')
        #parser.add_argument('--encoding', choices=[ 'text', 'binary', 'guess'], help='encode payload in base64 (for binary) or text (utf-8)')
        parser.add_argument('--exchange', default='xpublic', nargs='?', help='root of the topic tree to subscribe to')

        """
        FIXME: in previous parser, exchange is a modifier for bindings, can have several different values for different subtopic bindings.
           as currently coded, just a single value that over-writes previous setting, so only binding to a single exchange is possible.
        """
        
        #parser.add_argument('--inline', dest='inline', action='store_true', help='include file data in the message')
        #parser.add_argument('--inline_max', type=int, default=1024, help='maximum message size to inline')
        
        #parser.set_defaults( encoding='guess', inline=False )
        
        #parser.add_argument('--lag_warn', default=120, type=int, help='in seconds, warn if messages older than that')
        #parser.add_argument('--lag_drop', default=7200, type=int, help='in seconds, drop messages older than that')
        
        # the web server address for the source of the locally published tree.
        parser.add_argument('--post_broker', default=None, nargs='?', help='broker to post downloaded files to')
        #parser.add_argument('--post_baseUrl', default='http://' + self.hostname + ':8000/data', help='base url of the files announced')
        parser.add_argument('--post_exchange', default='xpublic', nargs='?', help='root of the topic tree to announce')
        parser.add_argument('--post_exchange_split', type=int, default=0, nargs='?', help='split output into different exchanges 00,01,...')
        parser.add_argument('--post_topic_prefix', default='/v03/post', nargs='?', help='allows simultaneous use of multiple versions and types of messages')
        #parser.add_argument('--select', nargs=1, action='append', help='client-side filtering: accept/reject <regexp>' )
        #parser.add_argument('--subtopic', nargs=1, action='append', help='server-side filtering: MQTT subtopic, wilcards # to match rest, + to match one topic' )
        parser.add_argument('--verbose', default=1, type=int, nargs='?', help='how chatty to be 0-rather quiet ... 3-quite chatty really')

        if isPost:
            parser.add_argument( 'path', nargs='+', help='files to post' )
        else:
            parser.add_argument('action', nargs='?', \
               choices=[ 'add', 'cleanup', 'edit', 'declare', 'disable', 'edit', 'enable', 'foreground', 'list', 'log', 'remove', 'rename', 'restart', 'sanity', 'setup', 'start', 'stop', 'status' ], help='action to take on the specified configurations' )
            parser.add_argument( 'configurations', nargs='+', help='configurations to operate on' )

        args = parser.parse_args()
        #FIXME need to apply _varsub

        self.merge(args)


if __name__ == "__main__" :

    logger = logging.getLogger()
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG)
    logger.setLevel( logging.ERROR )

    default_cfg = sr_cfg2(logger,appdirs.user_config_dir( 'sarra-test','science.gc.ca' ))
    default_cfg.override( { 'program_name':'sr_shovel', 'config':'t_dd1_f00' , 'directory':'${PWD}' } )
    os.chdir("/home/peter/.config/sarra")
    default_cfg.parse_file("default.conf")

    cfg = copy.deepcopy(default_cfg)

    os.chdir("shovel")
    cfg.parse_file("t_dd1_f00.conf")

    # FIXME... overrides with defaults, instead of only is non-default specified.
    #    unclear how to combine with config file.
    cfg.parse_args()

    #pp = pprint.PrettyPrinter(depth=6) 
    #pp.pprint(cfg)

    cfg.dump()

    print( "cfg.broker.password: %s" % cfg.broker.password )
    print( "cfg.broker.netloc: %s" % cfg.broker.netloc )
    if '@' in cfg.broker.netloc:
        host=cfg.broker.netloc.split('@')[1]
    print( "host: %s" % host )
    #print( "cfg.action: %s" % cfg.action )
    #print( "cfg.configurations: %s" % cfg.configurations )
