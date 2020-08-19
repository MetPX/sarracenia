
import copy
import logging
import netifaces
import os

# v3 plugin architecture...
import sarra.plugin
import sarra.plugin.integrity

import stat
import time
import types
import urllib.parse

from sarra import timestr2flt,timeflt2str

# from sr_util...
from sarra.sr_xattr import *

# for v2 subscriber routines...
import json,os,sys,time

from sys import platform as _platform

from base64 import b64decode, b64encode
from mimetypes import guess_type
# end v2 subscriber


from abc import ABCMeta, abstractmethod

from sarra import nowflt

logger = logging.getLogger( __name__ )

default_options = {  
  'accept_unmatched' : False,
  'attempts' : 3,
  'bytes_per_second' : None,
  'download'     : False,
  'housekeeping' : 30,     
  'log_reject'     : False,
  'logFormat'    : '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s',
  'logLevel'     : 'info',
  'preserve_mode': True,
  'preserve_time': True,
         'sleep' : 0.1,   
  'topic_prefix' : 'v02.post',
           'vip' : None
}

class Flow:
    """
    Implement the General Algorithm from the Concepts Guide.
    just pure program logic all the start, status, stop, log & instance management taken care of elsewhere.
      need to know whether to sleep between passes  
      o.sleep - an interval (floating point number of seconds)
      o.housekeeping - 

      A flow processes worklists of messages

      worklist given to plugins...

          worklist.incoming --> new messages to continue processing
          worklist.ok       --> successfully processed
          worklist.rejected --> messages to not be further processed.
          worklist.failed   --> messages for which processing failed.

      Initially all messages are placed in incoming.
      if a plugin decides:
      
      - a message is not relevant, it is moved to rejected.
      - all processing has been done, it moves it to ok.
      - an operation failed and it should be retried later, move to retry

    plugins must not remove messages from all worklists, re-classify them.
    it is necessary to put rejected messages in the appropriate worklist
    so they can be acknowledged as received.

    filter 

     
    """
    __metaclass__ = ABCMeta
  
    def __init__(self,cfg=None):

       """
       The cfg is should be an sarra/config object.
       """
       
       self._stop_requested = False

       me='flow'
       logging.basicConfig(format='%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s', level=logging.DEBUG)

       #self.o = types.SimpleNamespace()
       #
       #for k in default_options:
       #     setattr( self.o, k, default_options[k] )
       #
       #component = cfg.configurations[0].split(os.sep)[0]

       self.o = cfg

       if not hasattr(self.o,'post_topic_prefix'):
           self.o.post_topic_prefix=self.o.topic_prefix

       subclass=None
       subclass_names=[]
       #logger.debug( 'flow.__subclasses__() returns: %s' % Flow.__subclasses__() )
       for sc in Flow.__subclasses__() :
           subclass_names.append(sc.name(self))
           if self.o.program_name == sc.name(self):
              subclass=sc

       #logger.info( 'valid flows: %s' % subclass_names )
       if subclass is None:
           logger.critical( 'unknown flow. valid choices: %s' % subclass_names )
           return

       #for k in subclass.default_options:
       #     setattr( self.o, k, subclass.default_options[k] )
       #alist = [ a for a in dir(cfg) if not a.startswith('__') ]
       #for a in alist:
       #     #logger.debug( 'self.o.%s = %s' % ( a, getattr(cfg,a) ) )
       #     setattr( self.o, a, getattr(cfg,a) )

       logging.basicConfig( format=self.o.logFormat, level=getattr(logging, self.o.logLevel.upper()) ) 
       #logger.debug( '%s logLevel set to: %s ' % ( me, self.o.logLevel ) )
   
       # override? or merge... hmm...

       self.plugins = {}
       for entry_point in sarra.plugin.entry_points:
           self.plugins[ entry_point ] = []

       # FIXME: open new worklist
       self.worklist = types.SimpleNamespace()
       self.worklist.ok = []
       self.worklist.incoming = []
       self.worklist.rejected = []
       self.worklist.failed = []


       self.plugins['load'] = [ 'sarra.plugin.retry.Retry' ]

       # open cache, get masks. 
       if self.o.suppress_duplicates > 0:
           # prepend...
           self.plugins['load'].append( 'sarra.plugin.nodupe.NoDupe' )

       
       # FIXME: open retry


       if hasattr( self.o, 'plugins'):
           self.plugins['load'].extend( self.o.plugins )

       # initialize plugins.
       if hasattr( self.o, 'v2plugins' ):
           self.plugins['load'].append( 'sarra.plugin.v2wrapper.V2Wrapper' )
 
       subclass.__init__(self)

       self.loadPlugins( self.plugins['load'] )

       # transport stuff.. for download, get, put, etc...
       self.scheme = None
       self.cdir   = None
       self.proto  = None
    
    def loadPlugins(self, plugins_to_load):

        #logger.info( 'plugins to load: %s' % ( plugins_to_load ) )
        for c in plugins_to_load: 
            plugin = sarra.plugin.load_library( c, self.o )
            #logger.info( 'plugin loading: %s an instance of: %s' % ( c, plugin ) )
            for entry_point in sarra.plugin.entry_points:
                if hasattr( plugin, entry_point ):
                    fn = getattr( plugin, entry_point )
                    if callable(fn):
                        #logger.info( 'registering %s/%s' % (c, entry_point))
                        if entry_point in self.plugins:
                           self.plugins[entry_point].append(fn)
                        else:
                           self.plugins[entry_point] = [ fn ]

 
            if not ( hasattr(plugin,'registered_as') and callable( getattr( plugin, 'registered_as' ) ) ):
                continue

            schemes = plugin.registered_as()
            for schemed_entry_point in sarra.plugin.schemed_entry_points:
                if not hasattr(plugin, schemed_entry_point ) :
                    continue

                fn = getattr( plugin, schemed_entry_point) 
                if not callable( fn ):
                    continue

                for s in schemes:
                    if not s in self.plugins:
                        self.plugins[s] = {}
                
                    self.plugins[s][schemed_entry_point] = fn
                     
        #logger.info( 'plugins initialized')
        self.o.check_undeclared_options()
 
    def _runPluginsWorklist(self,entry_point):

        if hasattr(self,'plugins') and ( entry_point in self.plugins ):
           for p in self.plugins[entry_point]:
               p(self.worklist)
               if len(self.worklist.incoming) == 0:
                  return

    def _runPluginsTime(self,entry_point):
        for p in self.plugins[entry_point]:
            p()
    

    def has_vip(self):
        # no vip given... standalone always has vip.
        if self.o.vip == None:
           return True

        for i in netifaces.interfaces():
            for a in netifaces.ifaddresses(i):
                j=0
                while( j < len(netifaces.ifaddresses(i)[a]) ) :
                    if self.o.vip in netifaces.ifaddresses(i)[a][j].get('addr'):
                       return True
                    j+=1
        return False

    def please_stop(self):
        self._stop_requested = True

    @abstractmethod 
    def close( self ):

        self._runPluginsTime('on_stop')
        logger.info( 'flow/close completed cleanly' )


    def ack( self, mlist ):
        if "ack" in self.plugins:
            for p in self.plugins["ack"]:
                p(mlist)

    def ackWorklist(self,desc):
        logger.debug( '%s incoming: %d, ok: %d, rejected: %d, failed: %d' % ( 
                    desc,
                    len(self.worklist.incoming), len(self.worklist.ok), 
                    len(self.worklist.rejected), len(self.worklist.failed)) )

        self.ack(self.worklist.ok)
        self.worklist.ok=[]
        self.ack(self.worklist.rejected)
        self.worklist.rejected=[]


    def run(self):
        """
          check if stop_requested once in a while, but never return otherwise.
        """

        logger.debug( "working directory: %s" % os.getcwd() )

        next_housekeeping=nowflt()+self.o.housekeeping

        current_sleep = self.o.sleep
        if self.o.sleep > 0:
            last_time = nowflt()
   
        #logger.info(" all v3 plugins: %s" % self.plugins )
        self._runPluginsTime('on_start')
        spamming=True

        while True:

           if self._stop_requested:
               self.close()
               break

           if self.has_vip():
               self.gather()
               self.ackWorklist( 'A gathered' )

               if ( len(self.worklist.incoming) == 0 ):
                   spamming=True
               else:
                   current_sleep = self.o.sleep

               self.filter()

               self.ackWorklist( 'B filtered' )

               self.do()

               # need to acknowledge here, because posting will delete message-id
               self.ack(self.worklist.ok)
               self.ack(self.worklist.failed)

               self.post()

               self.report()
         
               self.worklist.ok=[]
               self.worklist.failed=[]

           if self.o.sleep < 0 :
                self.close()
                break

           if spamming and (current_sleep < 5):
                current_sleep *= 2

           now = nowflt()
           if now > next_housekeeping:
               logger.info('on_housekeeping')
               self._runPluginsTime('on_housekeeping')
               next_housekeeping=now+self.o.housekeeping

           if current_sleep > 0:
               elapsed = now - last_time
               if elapsed < current_sleep:
                   stime=current_sleep-elapsed
                   if stime > 60:  # if sleeping for a long time, debug output is good...
                       logger.debug("sleeping for more than 60 seconds: %g seconds. Elapsed since wakeup: %g Sleep setting: %g " % ( stime, elapsed, self.o.sleep ) )
               else:
                   #logger.debug( 'worked too long to sleep!')
                   last_time = now
                   continue

               try:
                   time.sleep(stime)
               except:
                   logger.info("flow woken abnormally from sleep")

               last_time = now

    def filter(self):

        logger.debug('start')
        filtered_worklist = []
        for m in self.worklist.incoming:
            #logger.warning('message: %s ' % m)
            url = m['baseUrl'] + os.sep + m['relPath']

            # apply masks, reject.
            matched=False
            for mask in self.o.masks:
                #logger.info('filter - checking: %s' % str(mask) )
                pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask

                if mask_regexp.match( url ):
                    matched=True
                    if not accepting:
                        if self.o.log_reject:
                            logger.info( "reject: mask=%s strip=%s url=%s" % (str(mask), strip, url) ) 
                            self.worklist.rejected.append(m)
                            break
                    # FIXME... missing dir mapping with mirror, strip, etc...
                    self.o.set_newMessageFields(m, url, pattern, maskDir, maskFileOption, mirror, strip, pstrip, flatten )

                    filtered_worklist.append(m)
                    logger.debug( "isMatchingPattern: accepted mask=%s strip=%s" % (str(mask), strip) )
                    break

            if not matched:
                if self.o.accept_unmatched:
                    logger.debug( "accept: unmatched pattern=%s" % (url) )
                    # FIXME... missing dir mapping with mirror, strip, etc...
                    self.o.set_newMessageFields(m, url, None, self.o.currentDir, self.o.filename, 
                       self.o.mirror, self.o.strip, self.o.pstrip, self.o.flatten )
                    filtered_worklist.append(m)
                elif self.o.log_reject:
                    logger.info( "reject: unmatched pattern=%s" % (url) )
                    self.worklist.rejected.append(m)
                
        self.worklist.incoming=filtered_worklist
        # apply on_messages plugins.
        self._runPluginsWorklist('on_messages')

        logger.debug('done')

    @abstractmethod
    def gather(self):
        self.worklist.incoming=[]
        for p in self.plugins["gather"]:
           new_incoming=p()
           if len(new_incoming) > 0:
              self.worklist.incoming.extend(new_incoming) 
 
    @abstractmethod 
    def do( self ):

        # mark all remaining messages as done.
        self.worklist.ok = self.worklist.incoming
        self.worklist.incoming = []
        logger.info('processing %d messages worked!' % len(self.worklist.ok) )
  
    @abstractmethod 
    def post( self ):

        logger.debug( 'on_post starting for %d messages' % len(self.worklist.ok) )

        self._runPluginsWorklist('on_posts')
        for p in self.plugins["post"]:
             p(self.worklist)

    @abstractmethod 
    def report( self ):
        # post reports
        # apply on_report plugins
        #logger.info('unimplemented')
        pass



    def write_inline_file(self,msg):
        """
           write local file based on a message with inlined content.

        """
        # make sure directory exists, create it if not
        if not os.path.isdir(msg['new_dir']):
            try:
                os.makedirs(msg['new_dir'],0o775,True)
            except Exception as ex:
                logger.warning( "making %s: %s" % ( newdir, ex ) )

        logger.debug( "data inlined with message, no need to download" )
        path = msg['new_dir'] + os.path.sep + msg['new_file']
        #path = msg['new_relPath']

        try:
            f = os.fdopen(os.open( path, os.O_RDWR | os.O_CREAT), 'rb+')
        except Exception as ex:
            logger.warning( "could not open %s to write: %s" % ( path, ex ) )
            return False
   
        if msg[ 'content' ][ 'encoding' ] == 'base64':
            data = b64decode( msg[ 'content' ]['value'] ) 
        else:
            data = msg[ 'content' ]['value'].encode('utf-8')

        if msg['integrity']['method'] == 'cod':
            algo_method = msg['integrity']['value']
        else:
            algo_method = msg['integrity']['method']

        onfly_algo = sarra.plugin.integrity.Integrity( algo_method )
        data_algo = sarra.plugin.integrity.Integrity( algo_method )
        onfly_algo.set_path(path)
        data_algo.set_path(path)
            
        onfly_algo.update(data)
        #msg.onfly_checksum = "{},{}".format(onfly_algo.registered_as(), onfly_algo.get_value())

        msg['onfly_checksum'] = { 'method': algo_method, 'value': onfly_algo.get_value()  }

        try:
            for p in self.plugins['on_data']:
                data = p(data)

        except Exception as ex:
            logger.warning( "plugin failed: %s" % ( p, ex ) )
            return False
   
        data_algo.update(data)

        #FIXME: If data is changed by plugins, need to update content header.
        #       current code will reproduce the upstream message without mofification.
        #       need to think about whether that is OK or not.

        msg['data_checksum'] = { 'method': algo_method, 'value': data_algo.get_value()  }

        msg['_deleteOnPost'].extend( [ 'onfly_checksum', 'data_checksum' ] )

        try:
            f.write( data )
            f.truncate()
            f.close()
            self.set_local_file_attributes( path, msg)

        except Exception as ex:
            logger.warning( "failed writing and finalizing: %s" % ( path, ex ) )
            return False
   
        return True

    def compute_local_checksum(self):

        if supports_extended_attributes:
            try:
                x = sr_xattr( msg['new_path'] )
                s = x.get( 'integrity' )
           
                if s:
                   msg['local_integrity'] = x.get( 'integrity' )
                   msg['_deleteOnPost'].extend( [ 'local_checksum' ] )
                   return

            except:
                pass

        local_integrity = sarra.plugin.integrity.Integrity( msg['integrity']['method'] )
        local_integrity.update_file( msg['new_path'] )
        msg['local_integrity'] = { 'method':  msg['integrity']['method'], 'value': local_integrity.get_value()  }
        msg['_deleteOnPost'].extend( [ 'local_integrity' ] )


    def file_should_be_downloaded(self,msg):
        """
          determine whether a comparison of local_file and message metadata indicates that it is new enough
          that writing the file locally is warranted.

          return True to say downloading is warranted.

             False if the file in the message represents the same or an older version that what is corrently on disk.

          origin: refactor & translation of v2: content_should_not_be downloaded
        """
        # FIXME... 
        if not os.path.isfile(msg['new_path']):
            return True

        # assert 

        lstat = os.stat( msg['new_path'] )
        fsiz  = lstat[stat.ST_SIZE]

        # FIXME... local_offset... offset within the local file... partitioned... who knows?
        #   part of partitioning deferral.
        #end   = self.local_offset + self.length
        end = msg['size']

        # compare sizes... if (sr_subscribe is downloading partitions into taget file) and (target_file isn't fully done)
        # This check prevents random halting of subscriber (inplace on) if the messages come in non-sequential order
        # target_file is the same as new_file unless the file is partitioned.
        # FIXME If the file is partitioned, then it is the new_file with a partition suffix.
        #if ('self.target_file == msg['new_file'] ) and ( fsiz != msg['size'] ):

        if ( fsiz != msg['size'] ):
            logger.debug("%s file size different, so cannot be the same" % (fname ) )
            return True

       # compare dates...

        if 'mtime' in msg:
            new_mtime = timestr2flt(msg[ 'mtime' ])
            old_mtime=0.0

            if self.o.preserve_time :
               old_mtime = lstat.st_mtime
            elif supports_extended_attributes:
               try:
                   x = sr_xattr( msg['new_path'] )
                   old_mtime = timestr2flt(x.get( 'mtime' ))
               except:
                   pass

            if new_mtime <= old_mtime:
               logger.debug("%s new version not newer" % ( msg['new_path'] ) )
               if self.o.log_reject:
                   logger.info("rejected: mtime not newer %s " % ( msg['new_path'] ) )
               return False
            else:
               logger.debug("{} new version is {} newer (new: {} vs old: {} )".format( msg['new_path'], new_mtime-old_mtime, new_mtime, old_mtime ))

        if msg['integrity']['method']  in [ 'random', 'md5name', 'cod'] :
            logger.debug("content_match %s sum 0/n/z never matches" % (msg['new_path'] ) )
            return True

        if end > fsiz :
           logger.debug("content_match file not big enough... considered different")
           return True

        try   : self.compute_local_checksum(msg)
        except:
                logger.debug("something went wrong when computing local checksum... considered different")
                return True

        logger.debug( "checksum in message: %s vs. local: %s" % ( self.local_checksum, self.checksum ) )

        if msg['local_integrity'] == msg['integrity']:
            if self.o.log_reject:
                 logger.info( "rejected: same checksum %s " % (fname ) )
            return False
        else:
            return True




    def do_download(self):
        """
           do download work for self.worklist.incoming, placing files:
                successfully downloaded in worklist.ok
                temporary failures in worklist.failed
                permanent failures (or files not to be downloaded) in worklist.rejected

        """
        
        if self.o.notify_only:
           self.worklist.ok = self.worklist.incoming
           self.worklist.incoming = []
           return

        for msg in self.worklist.incoming:

            new_path = msg['new_dir'] + os.path.sep + msg['new_file']

            # establish new_inflight_path which is the file to download into initially.
            if self.o.inflight == None or (('blocks' in msg) and ( msg['blocks']['method'] == 'inplace' )):
               new_inflight_path= msg['new_file']
            elif type(self.o.inflight) == str :
               if self.o.inflight == '.' :
                   new_inflight_path = '.' + new_file
               elif self.o.inflight[-1] == '/' :
                   if not os.path.isdir(self.o.inflight):
                       try:  
                          os.mkdir(self.o.inflight)
                          os.chmod(self.o.inflight,self.o.chmod_dir)
                       except:pass
                   new_inflight_path  = self.o.inflight + new_file
               elif self.o.inflight[0] == '.' :
                   new_inflight_path  = new_file + self.o.inflight
            else:
                #inflight is interval: minimum the age of the source file, as per message.
                logger.error('interval inflight setting: %s, not for remote.' % self.o.inflight )
                # FIXME... what to do?                
                self.worklist.rejected.append(msg)
                continue

            msg[ 'new_inflight_path' ] = new_inflight_path
            msg[ 'new_path' ] = new_path
            msg['_deleteOnPost'].extend( [ 'new_path', 'new_inflight_path' ] )
            # assert new_inflight_path is set.

            if os.path.exists(msg['new_inflight_path']):
                 logger.warning('inflight file already exists. race condition, deferring transfer of %s' % msg['new_path'] )
                 self.worklist.failed.append(msg)
                 continue

            # FIXME: decision of whether to download, goes here.
            if not self.file_should_be_downloaded(msg):
                self.worklist.rejected.append(msg)
                continue

            # am downloading content.
            if 'content' in msg.keys():
                if self.write_inline_file(msg):
                    self.worklist.ok.append(msg)
                else:
                    self.worklist.rejected.append(msg)
            else:
                parsed_url = urllib.parse.urlparse( msg['baseUrl'] )
                self.scheme = parsed_url.scheme

                i=1
                while i <= self.o.attempts :
                    ok = self.download( msg, self.o )
                    i = i+1
                    if ok: 
                        logger.info("downloaded ok: %s" % new_path )
                        self.worklist.ok.append(msg)
                        break
                    logger.warning("downloading again, attempt %d" % i)
                       
                if not ok:
                    logger.warning("gave up downloading for now" )
                    self.worklist.failed.append(msg)


        self.worklist.incoming=[]        

    # v2 sr_util.py ... generic sr_transport imported here...

    # generalized download...
    def download( self, msg, options ):

        self.o = options

        logger.debug("%s_transport download" % self.scheme)

        token       = msg['relPath'].split('/')
        cdir        = '/'.join(token[:-1])
        remote_file = token[-1]
        urlstr      = msg['baseUrl'] + '/' + msg['relPath']
        new_inflight_path    = ''

        new_dir     = msg['new_dir']
        new_file    = msg['new_file']

        try:    curdir = os.getcwd()
        except: curdir = None

        if curdir != new_dir:
            # make sure directory exists, create it if not
            if not os.path.isdir(new_dir):
                try: 
                   os.makedirs(new_dir,0o775,True)
                except Exception as ex:
                   logger.warning( "making %s: %s" % ( new_dir, ex ) )
                   logger.debug('Exception details:', exc_info=True)
            os.chdir(new_dir)

        logger.info("FIXME new_dir=%s, new_file=%s" % (new_dir, new_file) )

        try :
                options.destination = msg['baseUrl']

                if (self.proto is None) or not self.proto.check_is_connected() :
                   logger.debug("%s_transport download connects" % self.scheme)
                   self.proto = sarra.transfer.Protocol(self.scheme,self.o)
                   logger.debug( "HOHO proto %s " % type(self.proto) )
                   ok = self.proto.connect()
                   if not ok : 
                       self.proto = None
                       return False
                   logger.debug('connected')

                #=================================
                # if parts, check that the protol supports it
                #=================================

                #if not hasattr(proto,'seek') and ('blocks' in msg) and ( msg['blocks']['method'] == 'inplace' ):
                #   logger.error("%s, inplace part file not supported" % self.scheme)
                #   return False
                
                cwd = None
                if hasattr(self.proto,'getcwd') : cwd = self.proto.getcwd()

                logger.debug( " proto %s " % type(self.proto) )
                if cwd != cdir :
                   logger.debug("%s_transport download cd to %s" % (self.scheme,cdir))
                   self.proto.cd(cdir)
    
                remote_offset = 0
                if  ('blocks' in msg) and ( msg['blocks']['method'] == 'inplace' ): remote_offset = msg['offset']
    
                block_length = msg['size']
                str_range = ''
                if ('blocks' in msg) and ( msg['blocks']['method'] == 'inplace' ) :
                   block_length=msg['blocks']['size']
                   str_range = 'bytes=%d-%d'%(remote_offset,remote_offset+block_length-1)
    
                #download file
    
                logger.debug('Beginning fetch of %s %s into %s %d-%d' % 
                    (urlstr,str_range,new_file,msg['local_offset'],msg['local_offset']+block_length-1))
    
                # FIXME  locking for i parts in temporary file ... should stay lock
                # and file_reassemble... take into account the locking

                self.proto.set_sumalgo(msg['integrity']['method'])

                if options.inflight == None or (('blocks' in msg) and ( msg['blocks']['method'] == 'inplace' )):
                   new_inflight_path=new_file
                elif type(options.inflight) == str :
                   if options.inflight == '.' :
                       new_inflight_path = '.' + new_file
                   elif options.inflight[-1] == '/' :
                       try:  
                          os.mkdir(options.inflight)
                          os.chmod(options.inflight,options.chmod_dir)
                       except:pass
                       new_inflight_path  = options.inflight + new_file
                   elif options.inflight[0] == '.' :
                       new_inflight_path  = new_file + options.inflight
                else:
                    logger.error('inflight setting: %s, not for remote.' % options.inflight )

                self.proto.set_path( new_inflight_path )
                len_written = self.get( msg, remote_file, new_inflight_path, remote_offset, msg['local_offset'], block_length)

                if ( len_written == block_length ):
                       if ( new_inflight_path != new_file ):
                           if os.path.isfile(new_file) : 
                               os.remove(new_file)
                           os.rename(new_inflight_path, new_file)
                else:
                    logger.error('incomplete download only %d of expected %d bytes for %s' % (len_written, block_length, new_inflight_path) )

                logger.debug('proto.checksum={}, msg.sumstr={}'.format(self.proto.checksum, msg['integrity']))
                msg['onfly_checksum'] = self.proto.get_sumstr()
                msg['data_checksum'] = self.proto.data_checksum
                msg['_deleteOnPost'].extend( [ 'onfly_checksum', 'data_checksum' ] )

                # fix message if no partflg (means file size unknown until now)
                if not 'blocks' in msg : 
                    msg['size'] = self.proto.fpos 
    
                # fix permission 
                self.set_local_file_attributes(new_file,msg)

                if options.delete and hasattr(self.proto,'delete') :
                   try   :
                           self.proto.delete(remote_file)
                           logger.debug ('file deleted on remote site %s' % remote_file)
                   except:
                           logger.error('unable to delete remote file %s' % remote_file)
                           logger.debug('Exception details: ', exc_info=True)

                if ( len_written != block_length ):
                    return False

        except:
                #closing on problem
                try: 
                    self.proto.close()
                    self.cdir  = None
                    self.proto = None
                except : pass
    
                logger.error("Download failed 3 %s" % urlstr)
                logger.debug('Exception details: ', exc_info=True)
                if os.path.isfile(new_inflight_path) :
                    os.remove(new_inflight_path)
                return False
        return True

    # generalized get...
    def get( self, msg, remote_file, local_file, remote_offset, local_offset, length ):

        scheme = urllib.parse.urlparse( msg['baseUrl'] ).scheme
        if ((hasattr(self,'plugins') and ( 'do_get' in self.plugins )) and \
            scheme in self.plugins['do_get'] ):
            return self.plugins[scheme]['do_get']( msg, remote_file, local_file, remote_offset, local_offset, length )
        else:
            return self.proto.get(remote_file, local_file, remote_offset, local_offset, length)

    # generalized put...
    def put(self, msg, local_file, remote_file, local_offset=0, remote_offset=0, length=0 ):

        scheme = urllib.parse.urlparse( msg['baseUrl'] ).scheme
        if (hasattr(self,'plugins') and ( 'do_put' in self.plugins )) and \
            ( scheme in self.plugins['do_put'] ):
            return self.plugins[scheme]['do_put']( msg, local_file, remote_file, local_offset, remote_offset, length )
        else:
            return self.proto.put(local_file, remote_file, local_offset, remote_offset, length)


    # generalized send...
    def send( self, msg, options ):
        self.o = options
        logger.debug("%s_transport send %s %s" % (self.scheme,msg['new_dir'], msg['new_file'] ) )

        local_path = msg['relPath']
        local_dir  = os.path.dirname( local_path).replace('\\','/')
        local_file = os.path.basename(local_path).replace('\\','/')
        new_dir    = msg['new_dir'].replace('\\','/')
        new_file   = msg['new_file'].replace('\\','/')
        new_inflight_path   = None

        try:    curdir = os.getcwd()
        except: curdir = None

        if curdir != local_dir:
           os.chdir(local_dir)

        try :

                if (self.proto is None) or not self.proto.check_is_connected() :
                   logger.debug("%s_transport send connects" % self.scheme)
                   self.proto = sarra.transfer.Protocol(self.scheme,options)
                   ok = self.proto.connect()
                   if not ok : return False
                   self.cdir = None

                #=================================
                # if parts, check that the protol supports it
                #=================================

                if not hasattr(proto,'seek') and ('blocks' in msg) and ( msg['blocks']['method'] == 'inplace' ):
                   logger.error("%s, inplace part file not supported" % self.scheme)
                   return False

                #=================================
                # if umask, check that the protocol supports it ... 
                #=================================

                inflight = options.inflight
                if not hasattr(proto,'umask') and options.inflight == 'umask' :
                   logger.warning("%s, umask not supported" % self.scheme)
                   inflight = None

                #=================================
                # if renaming used, check that the protocol supports it ... 
                #=================================

                if not hasattr(proto,'rename') and options.inflight.startswith('.') :
                   logger.warning("%s, rename not supported" % self.scheme)
                   inflight = None

                #=================================
                # remote set to new_dir
                #=================================
                
                cwd = None
                if hasattr(proto,'getcwd') : cwd = proto.getcwd()
                if cwd != new_dir :
                   logger.debug("%s_transport send cd to %s" % (self.scheme,new_dir))
                   proto.cd_forced(775,new_dir)

                #=================================
                # delete event
                #=================================

                if msg.sumflg == 'R' :
                   if hasattr(proto,'delete') :
                      logger.debug("message is to remove %s" % new_file)
                      proto.delete(new_file)
                      return True
                   logger.error("%s, delete not supported" % self.scheme)
                   return False

                #=================================
                # link event
                #=================================

                if msg.sumflg == 'L' :
                   if hasattr(proto,'symlink') :
                      logger.debug("message is to link %s to: %s" % ( new_file, msg.headers['link'] ))
                      proto.symlink(msg.headers['link'],new_file)
                      return True
                   logger.error("%s, symlink not supported" % self.scheme)
                   return False

                #=================================
                # send event
                #=================================

                # the file does not exist... warn, sleep and return false for the next attempt
                if not os.path.exists(local_file):
                   logger.warning("product collision or base_dir not set, file %s does not exist" % local_file)
                   time.sleep(0.01)
                   return False

                offset = 0
                if  ('blocks' in msg) and ( msg['blocks']['method'] == 'inplace' ): offset = msg.offset

                new_offset = msg.local_offset
    
                str_range = ''
                if ('blocks' in msg) and ( msg['blocks']['method'] == 'inplace' ) :
                   str_range = 'bytes=%d-%d'%(offset,offset+msg.length-1)
    
                #upload file
    
                if inflight == None or (('blocks' in msg) and ( msg['blocks']['method'] == 'inplace' )) :
                   self.put(msg, local_file, new_file, offset, new_offset, msg.length)
                elif inflight == '.' :
                   new_inflight_path = '.'  + new_file
                   self.put(msg, local_file, new_inflight_path )
                   self.proto.rename(new_inflight_path, new_file)
                elif inflight[0] == '.' :
                   new_inflight_path = new_file + inflight
                   self.self.put(msg, local_file, new_inflight_path )
                   proto.rename(new_inflight_path, new_file)
                elif options.inflight[-1] == '/' :
                   try :
                          self.proto.cd_forced(775,new_dir+'/'+options.inflight)
                          self.proto.cd_forced(775,new_dir)
                   except:pass
                   new_inflight_path  = options.inflight + new_file
                   self.put(msg, local_file,new_inflight_path)
                   self.proto.rename(new_inflight_path, new_file)
                elif inflight == 'umask' :
                   self.proto.umask()
                   self.put(msg, local_file, new_file)

                # fix permission 

                self.set_remote_file_attributes(proto,new_file,msg)
    
                logger.info('Sent: %s %s into %s/%s %d-%d' % 
                    (local_path,str_range,new_dir,new_file,offset,offset+msg.length-1))

        except Exception as err:

                #removing lock if left over
                if new_inflight_path != None and hasattr(proto,'delete') :
                   try   : self.proto.delete(new_inflight_path)
                   except: pass

                #closing on problem
                try    : 
                    self.proto.close()
                    self.cdir  = None
                    self.proto = None
                    
                except : pass

                logger.error("Delivery failed %s" % msg['new_dir']+'/'+msg['new_file'])
                logger.debug('Exception details: ', exc_info=True)

                return False
        return True

    # set_local_file_attributes
    def set_local_file_attributes(self,local_file, msg) :
        """
           after a file has been written, restore permissions and ownership if necessary.
        """
        #logger.debug("sr_transport set_local_file_attributes %s" % local_file)

        # if the file is not partitioned, the the onfly_checksum is for the whole file.
        # cache it here, along with the mtime.
        if ( not 'blocks' in msg ) : 
           if 'onfly_checksum' in msg:
               sumstr = msg['onfly_checksum']
           else:
               sumstr = msg['integrity']

           x = sr_xattr( local_file )
           x.set( 'integrity' , sumstr )

           if self.o.preserve_time and 'mtime' in msg and msg['mtime'] :
               x.set( 'mtime' , msg['mtime'] )
           else:
               st = os.stat(local_file)
               mtime = timeflt2str( st.st_mtime )
               x.set( 'mtime' , mtime )
           x.persist()

        mode = 0
        if self.o.preserve_mode and 'mode' in msg :
           try: 
               mode = int( msg['mode'], base=8)
           except: 
               mode = 0
           if mode > 0 : 
               os.chmod( local_file, mode )

        if mode == 0 and  self.o.chmod !=0 : 
           os.chmod( local_file, self.o.chmod )

        if self.o.preserve_time and 'mtime' in msg and msg['mtime'] :
           mtime = timestr2flt( msg[ 'mtime' ] )
           atime = mtime
           if 'atime' in msg and msg['atime'] :
               atime  =  timestr2flt( msg[ 'atime' ] )
           os.utime( local_file, (atime, mtime))

    # set_remote_file_attributes
    def set_remote_file_attributes(self, proto, remote_file, msg) :
        #logger.debug("sr_transport set_remote_file_attributes %s" % remote_file)

        if hasattr(proto,'chmod') :
           mode = 0
           if self.o.preserve_mode and 'mode' in msg :
              try   : mode = int( msg['mode'], base=8)
              except: mode = 0
              if mode > 0 :
                 try   : proto.chmod( mode, remote_file )
                 except: pass

           if mode == 0 and  self.o.chmod !=0 : 
              try   : proto.chmod( self.o.chmod, remote_file )
              except: pass

        if hasattr(proto,'chmod') :
           if self.o.preserve_time and 'mtime' in msg and msg['mtime'] :
              mtime = timestr2flt( msg[ 'mtime' ] )
              atime = mtime
              if 'atime' in msg and msg['atime'] :
                  atime  =  timestr2flt( msg[ 'atime' ] )
              try   : proto.utime( remote_file, (atime, mtime))
              except: pass


    # v2 sr_util sr_transport stuff. end.

    # v2 subscribe routines start here

    #=================================
    # determine a file from a relpath
    #
    # returns None,None,None     if resulting file is rejected (reject/on_message)
    # returns None,None,newrelp  if resulting file is already up to date (newname only)
    # returns dir,file,relpath   of the file determined by the message and argument relpath
    #
    #=================================

    def determine_move_file(self,name,relpath):

        # build a working message from msg
        w_msg = sr_message(self)
        w_msg.exchange = msg.exchange + ''
        w_msg.notice   = msg.notice   + ''
        w_msg.topic    = msg.topic    + ''

        w_msg     = msg.copy()
        w_msg.add_headers = msg.add_headers.copy()
        w_msg.del_headers = msg.del_headers.copy()

        # set working message  with relpath info

        w_msg.set_topic (self.post_topic_prefix, relpath )
        w_msg.set_notice(msg.baseurl,relpath,msg.pubtime)

        w_msg.parse_v02_post()

        # make use of accept/reject on working message
        self.use_pattern = self.masks != []

        if self.use_pattern :

           # Adjust url to account for sundew extension if present, and files do not already include the names.
           if urllib.parse.urlparse(w_msg.urlstr).path.count(":") < 1 and 'sundew_extension' in w_msg.keys() :
              urlstr = w_msg.urlstr + ':' + w_msg[ 'sundew_extension' ]
           else:
              urlstr = w_msg.urlstr

           #logger.debug("determine_move_file, path being matched: %s " % ( urlstr )  )

           if not self.isMatchingPattern(urlstr,self.accept_unmatch) :
              logger.debug("Rejected by accept/reject options")
              return None,None,None

        elif not self.accept_unmatch :
              #logger.debug("determine_move_file, un_match: %s " % ( urlstr )  )
              return None,None,None

        # get a copy of received message

        saved_msg = msg

        # user working message to validate with on_message

        msg = w_msg
        self.set_new()
        msg.set_new()

        # invocation of _on_message processing for file that was moved.
        logger.info("while processing file rename calling on_message for oldname %s (in case the name changes)" % ( msg.urlstr )  )
        ok = self.__on_message__()
        if not ok : return None,None,None

        # ok what we have found

        #logger.debug("W new_dir     = %s" % msg['new_dir'])
        #logger.debug("W new_file    = %s" % msg['new_file'])
        #logger.debug("W new_baseurl = %s" % msg.new_baseurl)
        #logger.debug("W new_relpath = %s" % msg.new_relpath)

        # set the directory of the file we try to determine

        found = True
        try   : os.chdir(msg['new_dir'])
        except: found = False

        if not found:
           logger.info("directory containing old file (%s) to be renamed is not present, so download required." % msg['new_dir'])
           pass

        # if it is for 'newname' verify if the files are the same

        if found and name == 'newname' :
    
           if not self.overwrite and msg.partstr and msg.content_should_not_be_downloaded() :
              if self.reportback : msg.report_publish(304,'Not modified2')
              #logger.warning("not modified %s" % msg['new_file'])
              msg['new_dir']  = None
              msg['new_file'] = None

        # if it is for 'oldname' verify if the file exists

        if found and name == 'oldname' :
    
           if not os.path.exists(msg['new_file']):
              logger.info("file to move %s not present in destination tree (download needed.)" % msg['new_file'])
              msg['new_dir']  = None
              msg['new_file'] = None

        # prepare results
        tdir  = msg['new_dir']
        tfile = msg['new_file']
        trelp = msg.new_relpath

        # restore original message and settings

        msg = saved_msg
        self.set_new()
        msg.set_new()

        ok = self.__on_message__()

        try   : os.chdir(msg['new_dir'])
        except: pass

        # return results
        #logger.debug( "determine_move_file returning: %s %s %s" % ( tdir, tfile, trelp ))
        return tdir,tfile,trelp

    # =============
    # doit_download
    # =============

    def doit_download(self,msg,parent=None):
        #logger.debug("%s doit_download" % self.program_name)

        """
        FIXME: 201612-PAS There is perhaps several bug here:
            -- no_download is not consulted. In no_download, mkdir, deletes and links should not happen.
            -- on_file/on_part processing is not invoked for links or deletions, should it?
               do we need on_link? on_delete? ugh...
            
        """

        need_download = True

        #=================================
        # move event: case 1
        # sum has 'R,' and  msg['newname'] provided
        # Try to move oldfile from notice to newfile from headers['newname']
        # If the move is performed or not, we continue in the module because
        # the 'R,' meaning delete old file will be performed next
        # and the move message will be (corrected and) propagated that way
        #=================================

        newname = None
        if 'newname' in msg :
           #logger.warning("%s doit_download - newname=%s" % (self.program_name, msg['newname']) )
           newname = msg['newname']

           # it means that the message notice contains info about oldpath
           oldpath = msg['new_dir'] + '/' + msg['new_file']

           # we can do something if the oldpath exists
           if os.path.exists(oldpath) : 

              # determine the 'move to' file (accept/reject ok and on_message ok)
              newdir,newfile,newrelp = self.determine_move_file('newname',msg['newname'])
              if newrelp != None : newname = newrelp

              if newfile != None :
                 newpath = newdir + '/' + newfile

                 # only if the newpath doesnt exist
                 if not os.path.exists(newpath):

                    # make sure directory exists, create it if not
                    if not os.path.isdir(newdir):
                       try: 
                           os.makedirs(newdir,0o775,True)
                       except Exception as ex:
                           logger.warning( "making %s: %s" % ( newdir, ex ) )
                           logger.debug('Exception details:', exc_info=True)

                       #MG FIXME : except: return False  maybe ?

                    # move
                    try   : 
                            # file link
                            if os.path.isfile(oldpath) or os.path.islink(oldpath) :
                               os.link(oldpath,newpath)
                               logger.info("move %s to %s (hardlink)" % (oldpath,newpath))
                            # dir rename
                            if os.path.isdir( oldpath) : 
                               os.rename(oldpath,newpath)
                               logger.info("move %s to %s (rename)" % (oldpath,newpath))
                            if self.reportback: msg.report_publish(201, 'moved')
                            need_download = False
                    except Exception as ex:
                            logger.warning( "mv %s %s: %s" % ( oldpath, newdir, ex ) )
                            logger.debug('Exception details:', exc_info=True)
                    #MG FIXME : except: return False  maybe ?

                 # if the newpath exists log a message in debug only
                 else : 
                    logger.warning("could not move %s to %s (file exists)" % (oldpath,newpath))
              else:
                    logger.debug("new file ready to move? (file exists)")

        #=================================
        # move event: case 2
        # msg['oldname'] provided
        # Try to move oldfile from headers['oldname'] to newfile from notice
        # If the move is performed we are done (post and) return True
        # If it doesnt work, continue and the file will be downloaded normally
        #=================================

        oldname = None
        if 'oldname' in msg :
           #logger.debug("%s doit_download - oldname=%s" % (self.program_name, msg['oldname']) )
           oldname = msg['oldname']

           # set 'move to' file
           newpath = msg['new_dir'] + '/' + msg['new_file']

           # determine oldfile infos 

           olddir,oldfile,oldrelp = self.determine_move_file('oldname',msg['oldname'])
           if oldrelp != None : oldname = oldrelp

           #logger.debug("%s doit_download - oldname=%s -back from determine_move... oldfile=%s" % \
           #    (self.program_name, msg['oldname'], oldfile) )

           if oldfile != None :
              #logger.warning("%s doit_download 4" % (self.program_name) )
              oldpath = olddir + '/' + oldfile

              # oldfile exists: try to link it to newfile
              # if it doesnt work... pass... the newfile will be downloaded

              if os.path.exists(oldpath) : 

                 if not os.path.isdir(msg['new_dir']):
                    try: 
                        os.makedirs(msg['new_dir'],0o775,True)
                    except Exception as ex:
                        logger.warning( "making %s: %s" % ( msg['new_dir'], ex ) )
                        logger.debug('Exception details:', exc_info=True)

                 # move
                 ok = True
                 #logger.warning("%s doit_download - oldname=%s about to mv" % (self.program_name, msg['oldname']) )
                 try   : 
                         if os.path.isfile(oldpath) or os.path.islink(oldpath) :
                            os.link(oldpath,newpath)
                            logger.info("move %s to %s (hardlink)" % (oldpath,newpath))
                         elif os.path.isdir( oldpath) : 
                            os.rename(oldpath,newpath)
                            logger.info("move %s to %s (rename)" % (oldpath,newpath))
                         else:
                            logger.error("did not move %s to %s (rename)" % (oldpath,newpath))
                         need_download = False
                 except:
                     ok = False
                     logger.debug('Exception details:', exc_info=True)

                 if ok  :
                          logger.info("file moved %s to %s" % (oldpath,newpath) )
                          need_download = False
                          if self.reportback: msg.report_publish(201, 'moved')

                          msg.set_topic(self.post_topic_prefix,msg.new_relpath)
                          msg.set_notice(msg.new_baseurl,msg.new_relpath,msg.pubtime)
                          msg['oldname'] = oldname
                          if self.post_broker :
                             ok = self.__on_post__()
                             if ok and self.reportback : msg.report_publish(201,'Published')
                          else:
                             if   self.outlet == 'json' :
                                  print("%s" % json_line )
                             elif self.outlet == 'url'  :
                                  print("%s" % '/'.join(msg.notice.split()[1:3]) )
                          if msg.isRetry: self.consumer.msg_worked()
                          return True

                 logger.debug("could not move %s to %s (hardlink)" % (oldpath,newpath))
                 logger.info("newfile %s will be downloaded" % newpath)
           else:
                 logger.debug("oldfile is None, so newpath=%s will be downloaded." % (newpath) )
        #=================================
        # delete event, try to delete the local product given by message
        #=================================

        if msg.event == 'delete' : 

           logger.debug("message is to remove %s" % msg['new_file'])

           if not 'delete' in self.events and not 'newname' in msg : 
              logger.info("message to remove %s ignored (events setting)" % msg['new_file'])
              if msg.isRetry: self.consumer.msg_worked()
              return True

           path = msg['new_dir'] + '/' + msg['new_file']

           try : 
               if os.path.isfile(path) : os.unlink(path)
               if os.path.islink(path) : os.unlink(path)
               if os.path.isdir (path) : os.rmdir (path)
               logger.info("removed %s" % path)
               if self.reportback: msg.report_publish(201, 'removed')
           except:
               logger.error("sr_subscribe/doit_download: could not remove %s." % path)
               logger.debug('Exception details: ', exc_info=True)
               if self.reportback:
                   msg.report_publish(500, 'remove failed')

           msg.set_topic(self.post_topic_prefix,msg.new_relpath)
           msg.set_notice(msg.new_baseurl,msg.new_relpath,msg.pubtime)
           if 'newname' in msg : msg['newname'] = newname
           if self.post_broker :
              ok = self.__on_post__()
              if ok and self.reportback : msg.report_publish(201,'Published')
           else:
              if   self.outlet == 'json' :
                   self.__print_json( msg )
              elif self.outlet == 'url'  :
                   print("%s" % '/'.join(msg.notice.split()[1:3]) )

           if msg.isRetry: self.consumer.msg_worked()
           return True

        #=================================
        # link event, try to link the local product given by message
        #=================================

        if msg.event == 'link' :
           logger.debug("message is to link %s to %s" % ( msg['new_file'], msg[ 'link' ] ) )
           if not 'link' in self.events: 
              logger.info("message to link %s to %s ignored (events setting)" %  \
                                            ( msg['new_file'], msg[ 'link' ] ) )
              if msg.isRetry: self.consumer.msg_worked()
              return True

           if not os.path.isdir(msg['new_dir']):
              try: 
                 os.makedirs(msg['new_dir'],0o775,True)
              except Exception as ex:
                 logger.warning( "making %s: %s" % ( msg['new_dir'], ex ) )
                 logger.debug('Exception details:', exc_info=True)

           ok = True
           try : 
               path = msg['new_dir'] + '/' + msg['new_file']

               if os.path.isfile(path) : os.unlink(path)
               if os.path.islink(path) : os.unlink(path)
               if os.path.isdir (path) : os.rmdir (path)
               os.symlink( msg[ 'link' ], path )
               logger.info("%s symlinked to %s " % (msg['new_file'], msg[ 'link' ]) )
               if self.reportback: msg.report_publish(201,'linked')
           except:
               ok = False
               logger.error("symlink of %s %s failed." % (msg['new_file'], msg[ 'link' ]) )
               logger.debug('Exception details:', exc_info=True)
               if self.reportback: msg.report_publish(500, 'symlink failed')

           if ok :
              msg.set_topic(self.post_topic_prefix,msg.new_relpath)
              msg.set_notice(msg.new_baseurl,msg.new_relpath,msg.pubtime)
              if self.post_broker :
                 ok = self.__on_post__()
                 if ok and self.reportback : msg.report_publish(201,'Published')
              else:
                 if   self.outlet == 'json' :
                      self.__print_json( msg )
                 elif self.outlet == 'url'  :
                      print("%s" % '/'.join(msg.notice.split()[1:3]) )

           if msg.isRetry: self.consumer.msg_worked()
           return True

        #=================================
        # prepare download 
        # the post_base_dir should exists : it the starting point of the downloads
        # make sure local directory where the file will be downloaded exists
        #=================================
        # Caveat, where the local directory has sundew substitutions, it is normal for 
        # that directory not to exist ( e.g. /home/peter/test/dd/{RYYYY} )
        # FIXME: should we remove the substitutions and check the root of the root?
        #=================================

        if self.post_base_dir and not '{' in self.post_base_dir :
           if not os.path.isdir(self.post_base_dir) :
              logger.error("directory %s does not exist" % self.post_base_dir)
              # FIXME not sure ... retry on problems ?
              #if msg.isRetry: self.consumer.msg_to_retry()
              return False

        # pass no warning it may already exists
        try: 
           os.makedirs(msg['new_dir'],0o775,True)
        except Exception as ex: 
           logger.warning( "making %s: %s" % ( msg['new_dir'], ex ) )
           logger.debug('Exception details:', exc_info=True)

        try    : os.chdir(msg['new_dir'])
        except :
            logger.error("could not cd to directory %s" % msg['new_dir'])
            logger.debug('Exception details:', exc_info=True)

        #=================================
        # overwrite False, user asked that if the announced file already exists,
        # verify checksum to avoid an unnecessary download
        #=================================

        if not self.overwrite and msg.content_should_not_be_downloaded() :
           if self.reportback: msg.report_publish(304, 'not modified3')
           logger.debug("file not modified %s " % msg['new_file'])


           # if we are processing an entire file... we are done
           if msg.partflg == '1' :
              if msg.isRetry: self.consumer.msg_worked()
              return False

           need_download = False


        #=================================
        # attempt downloads
        #=================================

        if need_download :


           msg.onfly_checksum = None
           msg.ondata_checksum = None

           # skip checksum computation for sumflg = '0'

           if msg.sumflg[0] == '0':
               msg.sumalgo = None

           # N attempts to download
           i  = 1
           while i <= self.attempts :
                 if i != 1:
                     logger.warning("downloading again, attempt %d" % i)

                 ok = self.__do_download__(msg)
                 if ok : break
                 # dont force on retry 
                 if msg.isRetry : break
                 i = i + 1

           # could not download ...

           if not ok:
              if self.retry_mode : self.consumer.msg_to_retry()
              return False

           # after download we dont propagate renaming... once used get rid of it
           if 'rename'  in msg : 
               del msg['rename']
               # FIXME: worry about publishing after a rename.
               # the relpath should be replaced by rename value for downstream
               # because the file was written to rename.
               # not sure if this happens or not.

           # if we can set the checksum for downloaded data correctly, we should do so
           # to prevent loops.
           if msg.onfly_checksum :

                # after download : setting of sum for 'z' flag ...
                if len(msg.sumflg) > 2 and msg.sumflg[:2] == 'z,':
                    new_checksum=msg.onfly_checksum.split(',')[-1]
                else:
                    new_checksum=None

                if ( msg.sumflg[0] not in ['a', 'z'] ) and ( msg.onfly_checksum != msg.sumstr ):
                   # onfly checksum is different from the message, avoid loops by overwriting. 
                   # except if the algorithm is arbitrary, and therefore cannot be calculated.
                   logger.warning("onfly_checksum %s differ from message %s" %
                                      (msg.onfly_checksum, msg.sumstr))
                   new_checksum=msg.onfly_checksum.split(',')[-1]
                
                if self.on_data_list :
                   # if there was transformation happening during the transfer, 
                   # we should used the checksum from the transformed data.
                   logger.debug("setting checksum from on_data: %s" % msg.data_checksum )
                   new_checksum=msg.data_checksum
 
                if new_checksum :
                   # set the value so that if it gets posted later, it is correct.
                   msg.set_sum(msg.sumflg.split(',')[-1], new_checksum)

                   try:
                          path = msg['new_dir'] + '/' + msg['new_file']

                          x = sr_xattr(path)

                          if 'mtime' in msg:
                              x.set( 'mtime', msg['mtime'] )

                          new_sumstr = msg.sumflg+','+new_checksum
                          if x.get('sum') != new_sumstr:
                              x.set('sum', new_sumstr)
                          x.persist()

                   except Exception as ex:
                          logger.warning( "failed to set sattributes %s" % path )
                          logger.debug('Exception details:', exc_info=True)

                   # tell upstream that we changed the checksum.
                   if self.reportback:
                       if new_checksum == msg.onfly_checksum :
                            msg.report_publish(205,'Reset Content : checksum')
                       else:
                            msg.report_publish(203,'Non-Authoritative Information: transformed during download')


           # if the part should have been inplace... but could not

           if self.inplace and msg.in_partfile :
              if self.reportback: msg.report_publish(307,'Temporary Redirect')

           # got it : call on_part (for all parts, a file being consider
           # a 1 part product... we run on_part in all cases)

           for plugin in self.on_part_list :

              self.__plugin_backward_compat_setup__()

              if not plugin(self):
                 # plugin discarded it ... but the message worked
                 if msg.isRetry: self.consumer.msg_worked()
                 return False

              self.__plugin_backward_compat_repare__()


           # running on_file : if it is a file, or 
           # it is a part and we are not running "inplace" (discard True)
           # or we are running in place and it is the last part.

           if self.on_file_list :
              """
                 *** FIXME ***: When reassembled, lastchunk is inserted last and therefore
                 calling on_file on lastchunk is accurate... Here, the lastchunk was inserted
                 directly into the target file... The decision of directly inserting the part
                 into the file is based on the file'size being bigger or equal to part's offset.
                 It may be the case that we were at the point of inserting the last chunk...
                 BUT IT IS POSSIBLE THAT,WHEN OVERWRITING A FILE WITH PARTS BEING SENT IN PARALLEL,
                 THE PROGRAM INSERTS THE LASTCHUNK BEFORE THE END OF COLLECTING THE FILE'PARTS...
                 HENCE AN INAPPROPRIATE CALL TO on_file ... 

                 2016/12 FIXME:  I do not understand the (not self.inplace) clause... if it is a part file
                  if it handled by on_part above, if it is the last part, it is called by reassembly below
                  do not understand why calling on this condition.

                  If think this will be called for every partition file, which I think is wrong.

              """

              if (msg.partflg == '1') or  \
                       (msg.partflg != '1' and ( \
                             (not self.inplace) or \
                             (self.inplace and (msg.lastchunk and not msg.in_partfile)))):

                 if not self.__on_file__():
                    # plugin discarded it ... but the message worked
                    if msg.isRetry: self.consumer.msg_worked()
                    return False

           # inline option
           if  (not ( msg.event in [ 'link',  'delete' ] )  ) and \
               (msg.partflg == '1' ) and ( self.post_version == 'v03' ) \
               and self.inline :

               fname = msg['new_dir'] + os.path.sep + msg['new_file']
               fs = os.stat( fname )
               if fs.st_size < self.inline_max :

                   if self.inline_encoding == 'guess':
                      e = guess_type(fname)[0]
                      binary = not e or not ('text' in e )
                   else:
                      binary = (self.inline_encoding != 'text' )

                   try: 
                       f = open(fname , 'rb')
                       d = f.read()
                       f.close()

                       if binary:
                           msg[ "content" ] = { "encoding": "base64", "value": b64encode(d).decode('utf-8') }
                       else:
                           try:
                               msg[ "content" ] = { "encoding": "utf-8", "value": d.decode('utf-8') }
                           except:
                               msg[ "content" ] = { "encoding": "base64", "value": b64encode(d).decode('utf-8') }
                               logger.debug('Exception details:', exc_info=True)

                       logger.debug( "inlined data for %s" % msg['new_file'] )

                   except:
                       logger.error("failled trying to inline %s" % msg['new_file'])
                       logger.debug('Exception details:', exc_info=True)

           # discard option
           if self.discard :
              try    :
                        os.unlink(msg['new_file'])
                        logger.debug("Discarded  %s" % msg['new_file'])
              except :
                        logger.error("Could not discard")
                        logger.debug('Exception details: ', exc_info=True)
              if msg.isRetry: self.consumer.msg_worked()
              return False


        #=================================
        # publish our download
        #=================================

        if msg.partflg != '1' :
           if self.inplace : msg.change_partflg('i')
           else            : msg.change_partflg('p')

        msg.set_topic(self.post_topic_prefix,msg.new_relpath)
        msg.set_notice(msg.new_baseurl,msg.new_relpath,msg.pubtime)
        if 'oldname' in msg : msg['oldname'] = oldname
        if self.post_broker :
           ok = self.__on_post__()
           if ok and self.reportback: msg.report_publish(201,'Published')
        else:
           if   self.outlet == 'json' :
                self.__print_json( msg )
           elif self.outlet == 'url'  :
                print("%s" % '/'.join(msg.notice.split()[1:3]) )

        #=================================
        # if we processed a file we are done
        #=================================

        if msg.partflg == '1' :
           if msg.isRetry: self.consumer.msg_worked()
           return True

        #=================================
        # if we processed a part (downloaded or not)
        # it can make a difference for parts that wait reassembly
        #=================================
   
        if self.inplace : file_reassemble(self)

        """
        FIXME: 2016/10 - PAS: suspect a bug: pretty sure on_file plugin should run after reassembly complete.
                         2016/12 - ok I get it: on_file is called in the inplace case above.
                                   for the parts case, it is called from reassemble correctly.
                                  
        FIXME: 2016/10 - PAS: suspect a bug: pretty sure discard should run after reassembly complete.
                    2016/12 - well maybe not, if it is discarding parts, it is probably better... hmm..
        """
        if msg.isRetry: self.consumer.msg_worked()
        return True


    # v2 subscribe routines end here

import sarra.flow.shovel
import sarra.flow.winnow
import sarra.flow.post
import sarra.flow.watch
import sarra.flow.poll
import sarra.flow.subscribe
