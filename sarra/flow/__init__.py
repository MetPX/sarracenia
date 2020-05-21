
import logging
import netifaces
import os
from sarra.v2wrapper import V2Wrapper

# v3 plugin architecture...
import sarra.plugin
import time
import types

from abc import ABCMeta, abstractmethod

from sarra.nodupe import NoDupe

from sarra.sr_util import nowflt

logger = logging.getLogger( __name__ )


class Flow:
    __metaclass__ = ABCMeta
    """
      implement the General Algorithm from the Concepts Guide.
      just pure program logic all the start, status, stop, log & instance management taken care of elsewhere.
      
      need to know whether to sleep between passes  
      o.sleep - an interval (floating point number of seconds)
      o.housekeeping - 
    """
  
    def __init__(self,o=None):

       
       self._stop_requested = False

       # override? or merge... hmm...
       if o is not None:
           self.o = o
       else:
           # FIXME: set o.sleep, o.housekeeping
           self.o = types.SimpleNamespace()
           self.o.sleep = 10
           self.o.housekeeping = 30

       self.v3plugins = {}



       # FIXME: open cache, get masks. 
       if o.suppress_duplicates > 0:
           logger.info('NoDupe is on' )
           self.o.noDupe = NoDupe(o)
           if hasattr(self.o,'v3plugins'):
                self.o.v3plugins.append('sarra.plugin.nodupe.NoDupe') 
           else:
                self.o.v3plugins =[ 'sarra.plugin.nodupe.NoDupe' ]

       # FIXME: open new_worklist
       # FIXME: initialize retry_list
       # FIXME: initialize vip 
       self.o.vip = None

       # FIXME: open retry
 
       # initialize plugins.
       if hasattr( o, 'v2plugins' ):
           logger.info('plugins: %s' % o.v2plugins )
           vw = V2Wrapper( self.o )
           for e in o.v2plugins:
               logger.info('resolving: %s' % e)
               for v in o.v2plugins[e]:
                   vw.add( e, v )
           self.v2plugins = vw
           logger.info( 'v2 plugins initialized')
       
       if hasattr( o, 'v3plugins'):
           self._loadV3Plugins(self.o.v3plugins)

       logger.info('shovel constructor')
       #self.o.dump()
   
    
    def _loadV3Plugins(self,plugins_to_load):

        logger.info( 'v3 plugins to load: %s' % ( plugins_to_load ) )
        for c in plugins_to_load: 
            plugin = sarra.plugin.load_library( c, self.o )
            logger.info( 'v3 plugin loading: %s an instance of: %s' % ( c, plugin ) )
            for entry_point in sarra.plugin.entry_points:
                 if hasattr( plugin, entry_point ):
                    fn = getattr( plugin, entry_point )
                    if callable(fn):
                        logger.info( 'v3 registering %s/%s' % (c, entry_point))
                        if entry_point in self.v3plugins:
                           self.v3plugins[entry_point].append(fn)
                        else:
                           self.v3plugins[entry_point] = [ fn ]
        logger.info( 'v3 plugins initialized')
 
    def _runV3Plugins(self,entry_point):

        if hasattr(self,'v3plugins') and ( entry_point in self.v3plugins ):
           for p in self.v3plugins[entry_point]:
               self.new_worklist = p(self.new_worklist)
               if len(self.new_worklist) == 0:
                  return


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

    def run(self):
        """
          check if stop_requested once in a while, but never return otherwise.
        """

        next_housekeeping=nowflt()+self.o.housekeeping

        if self.o.sleep > 0:
            last_time = nowflt()
       
        while True:

           if self._stop_requested:
               self.close()
               break

           if self.has_vip():
               worklist = self.gather()
               self.filter()
               self.do()
               self.post()
               self.report()
         
           now = nowflt()
           if now > next_housekeeping:
               logger.info('on_housekeeping')
               next_housekeeping=now+self.o.housekeeping

           if self.o.sleep > 0:
               elapsed = now - last_time
               if elapsed < self.o.sleep:
                   stime=self.o.sleep-elapsed
                   if stime > 60:  # if sleeping for a long time, debug output is good...
                       logger.debug("sleeping for more than 60 seconds: %g seconds. Elapsed since wakeup: %g Sleep setting: %g " % ( stime, elapsed, self.o.sleep ) )
               try:
                   time.sleep(stime)
               except:
                   logger.info("flow woken abnormally from sleep")

               last_time = now

    def filter(self):
        # apply cache, reject.
        # apply masks, reject.

        self.filtered_worklist = []
        for m in self.new_worklist:
            url = m['baseUrl'] + os.sep + m['relPath']
            matched=False
            for mask in self.o.masks:
                #logger.info('filter - checking: %s' % str(mask) )
                pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask
                if mask_regexp.match( url ):
                    matched=True
                    if not accepting:
                        if self.o.log_reject:
                            logger.info( "reject: mask=%s strip=%s pattern=%s" % (str(mask), strip, m) ) 
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
                
        self.new_worklist=[]
        for m in self.filtered_worklist:
            self.v2plugins.run('on_message', m)
            self.new_worklist.append(m)

        self._runV3Plugins('on_messages')
        # apply on_message plugins.
        logger.debug('filter - done')

    @abstractmethod
    def housekeeping(self):
        logger.info('housekeeping - started')

        self.v2plugins.housekeeping()

        for p in self.v3plugins['on_housekeeping']:
            p()

        logger.info('housekeeping - done')

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
    def report( self ):
        # post reports
        # apply on_report plugins
        logger.info('report -unimplemented')

    @abstractmethod 
    def close( self ):
        logger.info('closing')
