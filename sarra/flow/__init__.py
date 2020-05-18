
import logging
import netifaces
import sarra.plugins
import time
import types

from sarra.sr_util import nowflt

logger = logging.getLogger( __name__ )

class Flow:
    """
      implement the General Algorithm from the Concepts Guide.
      just pure program logic all the start, status, stop, log & instance management taken care of elsewhere.
      
      need to know whether to sleep between passes  
      o.sleep - an interval (floating point number of seconds)
      o.housekeeping - 
    """
  
    def __init__(self,o=None):

       # FIXME: set o.sleep, o.housekeeping
       self.o = types.SimpleNamespace()
       self.o.sleep = 10
       self.o.housekeeping = 30

       # FIXME: open cache, get masks. 
       # FIXME: open new_worklist
       # FIXME: initialize retry_list
       # FIXME: initialize vip 
       self.o.vip = None

       # FIXME: open retry
 
       # override? or merge... hmm...
       if o is not None:
           self.o = o

       self.o.dump()
    

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


    def run(self):

        next_housekeeping=nowflt()+self.o.housekeeping

        if self.o.sleep > 0:
            last_time = nowflt()
       
        while True:

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
               time.sleep(stime)
               last_time = now

    def filter(self):
        # apply masks, reject.
        # apply on_message plugins.
        logger.info('filter - unimplemented')

#
# sort of an abstract base class, subclass must implement the following entry points:
#
#    def gather(self):
#        logger.info('gather - unimplemented')
# 
#   
#    def do( self ):
#        logger.info('do - unimplemented')
#   
#    def post( self ):
#        # post messages
#        # apply on_post plugins
#        logger.info('post - unimplemented')
   
    def report( self ):
        # post reports
        # apply on_report plugins
        logger.info('report -unimplemented')
