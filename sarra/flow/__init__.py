
import copy
import logging
import netifaces
import os

# v3 plugin architecture...
import sarra.plugin
import time
import types

from abc import ABCMeta, abstractmethod

from sarra.sr_util import nowflt

logger = logging.getLogger( __name__ )


class Flow:
    __metaclass__ = ABCMeta
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
          worklist.retry    --> messages for which processing failed.

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
  
    def __init__(self,o=None):

       """

         o.sleep
         o.housekeeping
         o.vip
      
       """
       
       self._stop_requested = False

       # override? or merge... hmm...
       if o is not None:
           self.o = o
           logger.info('dump options;')
           o.dump()
       else:
           # FIXME: set o.sleep, o.housekeeping
           self.o = types.SimpleNamespace()
           self.o.sleep = 10
           self.o.housekeeping = 30
           # FIXME: initialize vip 
           self.o.vip = None

       self.plugins = {}
       self.plugins['load'] = []

       # FIXME: open new worklist
       self.worklist = types.SimpleNamespace()
       self.worklist.ok = []
       self.worklist.incoming = []
       self.worklist.rejected = []

       #FIXME: load retry from disk?
       self.worklist.retry = []


       # open cache, get masks. 
       if o.suppress_duplicates > 0:
           # prepend...
           self.plugins['load'] = [ 'sarra.plugin.nodupe.NoDupe' ]


       # FIXME: open retry


       # initialize plugins.
       if hasattr( o, 'v2plugins' ):
           self.plugins['load'].append( 'sarra.plugin.v2wrapper.V2Wrapper' )
 
       if hasattr( o, 'plugins'):
           self.plugins['load'].extend( self.o.plugins )

       self._loadPlugins( self.plugins['load'] )


       logger.info('shovel constructor')
       #self.o.dump()
   
    
    def _loadPlugins(self, plugins_to_load):

        logger.info( 'v3 plugins to load: %s' % ( plugins_to_load ) )
        for c in plugins_to_load: 
            plugin = sarra.plugin.load_library( c, self.o )
            logger.info( 'v3 plugin loading: %s an instance of: %s' % ( c, plugin ) )
            for entry_point in sarra.plugin.entry_points:
                 if hasattr( plugin, entry_point ):
                    fn = getattr( plugin, entry_point )
                    if callable(fn):
                        logger.info( 'v3 registering %s/%s' % (c, entry_point))
                        if entry_point in self.plugins:
                           self.plugins[entry_point].append(fn)
                        else:
                           self.plugins[entry_point] = [ fn ]
        logger.info( 'v3 plugins initialized')
 
    def _runPluginsWorklist(self,entry_point):

        if hasattr(self,'plugins') and ( entry_point in self.plugins ):
           for p in self.plugins[entry_point]:
               p(self.worklist)
               if len(self.worklist.incoming) == 0:
                  return

    def _runPluginsTime(self,entry_point):
        for p in self.plugins[entry_point]:
            logger.info('%s... p is %s' % (entry_point, p ) )
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
        logger.info('flow closing')
        self._runPluginsTime('on_stop')

    def run(self):
        """
          check if stop_requested once in a while, but never return otherwise.
        """

        next_housekeeping=nowflt()+self.o.housekeeping

        current_sleep = self.o.sleep
        if self.o.sleep > 0:
            last_time = nowflt()
   
        #logger.info(" all v3 plugins: %s" % self.plugins )
        self._runPluginsTime('on_start')

        while True:

           if self._stop_requested:
               self.close()
               break

           if self.has_vip():
               self.gather()
               if len(self.worklist.incoming) == 0:
                   if (current_sleep < 1):
                       current_sleep *= 2
               else:
                   current_sleep = self.o.sleep
                   self.filter()
                   self.do()
                   self.post()
                   self.report()
         
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
                   logger.debug( 'worked too long to sleep!')
                   continue
               try:
                   time.sleep(stime)
               except:
                   logger.info("flow woken abnormally from sleep")

               last_time = now

    def filter(self):

        logger.debug('filter - start')
        self.filtered_worklist = []
        for m in self.worklist.incoming:
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
                            logger.info( "reject: mask=%s strip=%s pattern=%s" % (str(mask), strip, m) ) 
                            self.worklist.rejected.append(m)
                            break
                    # FIXME... missing dir mapping with mirror, strip, etc...
                    m['newDir'] = maskDir
                    # FIXME... missing FileOption processing.
                    m['newFile'] = os.path.basename(m['relPath'])
                    m['_deleteOnPost'].extend( [ 'newDir', 'newFile' ] )
                    self.filtered_worklist.append(m)
                    logger.debug( "isMatchingPattern: accepted mask=%s strip=%s" % (str(mask), strip) )
                    break

            if not matched:
                if self.o.accept_unmatched:
                    logger.debug( "accept: unmatched pattern=%s" % (url) )
                    # FIXME... missing dir mapping with mirror, strip, etc...
                    m['newDir'] = maskDir
                    # FIXME... missing FileOption processing.
                    m['newFile'] = os.path.basename(m['relPath'])
                    m['_deleteOnPost'].extend( [ 'newDir', 'newFile' ] )
                    self.filtered_worklist.append(m)
                elif self.o.log_reject:
                    logger.info( "reject: unmatched pattern=%s" % (url) )
                    self.worklist.rejected.append(m)
                
        # apply on_messages plugins.
        self._runPluginsWorklist('on_messages')

        self.ack(self.worklist.ok)
        self.worklist.ok=[]
        self.ack(self.worklist.rejected)
        self.worklist.rejected=[]

        logger.debug('filter - done')

    @abstractmethod
    def gather(self):
        logger.info('gather - unimplemented')
 
    @abstractmethod 
    def do( self ):
        logger.info('do - unimplemented')
  
    @abstractmethod 
    def post( self ):
        # post messages
        # apply on_post plugins
        logger.info('post - unimplemented')
   
    @abstractmethod 
    def ack( self, m ):
        # acknowledge_messages
        logger.info('ack - unimplemented')

    @abstractmethod 
    def report( self ):
        # post reports
        # apply on_report plugins
        logger.info('report -unimplemented')

