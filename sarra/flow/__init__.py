
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

default_options = {  
  'accept_unmatched' : False,
  'download'     : False,
  'housekeeping' : 30,     
  'loglevel'     : 'info',
         'sleep' : 0.1,   
           'vip' : None
}

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
          worklist.failed    --> messages for which processing failed.

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
  
    def __init__(self,cfg=None):

       """

       """
       
       self._stop_requested = False


       self.o = types.SimpleNamespace()

       for k in default_options:
            setattr( self.o, k, default_options[k] )

       component = cfg.configurations[0].split(os.sep)[0]
       component_found=False
       subclass_names=[]
       logger.error( 'flow.__subclasses__() returns: %s' % Flow.__subclasses__() )
       for subclass in Flow.__subclasses__() :
           subclass_names.append(subclass.name(self))
           if component == subclass.name(self):
              component_found=True
              break 

       logger.info( 'valid flows: %s' % subclass_names )
       if not component_found:
           logger.critical( 'unknown flow. valid choices: %s' % subclass_names )
           return

       for k in subclass.default_options:
            setattr( self.o, k, subclass.default_options[k] )

       alist = [ a for a in dir(cfg) if not a.startswith('__') ]

       for a in alist:
            setattr( self.o, a, getattr(cfg,a) )

       # override? or merge... hmm...

       self.plugins = {}
       self.plugins['load'] = []

       # FIXME: open new worklist
       self.worklist = types.SimpleNamespace()
       self.worklist.ok = []
       self.worklist.incoming = []
       self.worklist.rejected = []

       #FIXME: load retry from disk?
       self.worklist.failed = []


       # open cache, get masks. 
       if self.o.suppress_duplicates > 0:
           # prepend...
           self.plugins['load'] = [ 'sarra.plugin.nodupe.NoDupe' ]


       # FIXME: open retry


       # initialize plugins.
       if hasattr( self.o, 'v2plugins' ):
           self.plugins['load'].append( 'sarra.plugin.v2wrapper.V2Wrapper' )
 
       if hasattr( self.o, 'plugins'):
           self.plugins['load'].extend( self.o.plugins )

       self.loadPlugins( self.plugins['load'] )


       logger.info('shovel constructor')
       self.o.dump()

       if hasattr(self.o,'broker'):
             od = sarra.moth.default_options
             od.update( self.o.dictify() )
             self.consumer = sarra.moth.Moth( self.o.broker, od, is_subscriber=True )

       if hasattr(self.o,'post_broker'):
             props = sarra.moth.default_options
             props.update ( {
                 'broker':self.o.post_broker, 'exchange':self.o.post_exchange,
             } )
             self.poster = sarra.moth.Moth( self.o.post_broker, props, is_subscriber=False )

       subclass.__init__(self)
   
    
    def loadPlugins(self, plugins_to_load):

        logger.info( 'plugins to load: %s' % ( plugins_to_load ) )
        for c in plugins_to_load: 
            plugin = sarra.plugin.load_library( c, self.o )
            logger.info( 'plugin loading: %s an instance of: %s' % ( c, plugin ) )
            for entry_point in sarra.plugin.entry_points:
                 if hasattr( plugin, entry_point ):
                    fn = getattr( plugin, entry_point )
                    if callable(fn):
                        logger.info( 'registering %s/%s' % (c, entry_point))
                        if entry_point in self.plugins:
                           self.plugins[entry_point].append(fn)
                        else:
                           self.plugins[entry_point] = [ fn ]
        logger.info( 'plugins initialized')
 
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
        self.consumer.close()
        self.poster.close()
        logger.info( 'flow/close completed cleanly' )


    def ack( self, mlist ):
         for m in mlist:
             self.consumer.ack( m )

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

               self.ackWorklist( 'D do' )

               # need to acknowledge incoming here, because posting will delete message-id
               self.ack(self.worklist.incoming)

               self.post()

               # post should have moved stuff from incoming to others, 
               # but they were already acked above.
               self.worklist.incoming=[]
               self.worklist.ok=[]
               self.worklist.rejected=[]

               self.report()
         
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
                   continue
               try:
                   time.sleep(stime)
               except:
                   logger.info("flow woken abnormally from sleep")

               last_time = now








    def filter(self):

        logger.debug('start')
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
                    m['newDir'] = os.getcwd()
                    # FIXME... missing FileOption processing.
                    m['newFile'] = os.path.basename(m['relPath'])
                    m['_deleteOnPost'].extend( [ 'newDir', 'newFile' ] )
                    self.filtered_worklist.append(m)
                elif self.o.log_reject:
                    logger.info( "reject: unmatched pattern=%s" % (url) )
                    self.worklist.rejected.append(m)
                
        # apply on_messages plugins.
        self._runPluginsWorklist('on_messages')

        logger.debug('done')

    @abstractmethod
    def gather(self):
        self.worklist.incoming= self.consumer.newMessages()

 
    @abstractmethod 
    def do( self ):

        # mark all remaining messages as done.
        self.worklist.ok = self.worklist.incoming
        self.worklist.incoming = []
        logger.info('unimplemented, assuming everything worked...')
  
    @abstractmethod 
    def post( self ):
        for m in self.worklist.incoming:
             # FIXME: outlet = url, outlet=json.
             self.poster.putNewMessage(m)
             self.worklist.ok.append(m)

        self.worklist.incoming=[]

    @abstractmethod 
    def report( self ):
        # post reports
        # apply on_report plugins
        logger.info('unimplemented')

import sarra.flow.shovel
import sarra.flow.winnow
