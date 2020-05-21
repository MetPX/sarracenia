
from sarra.tmpc import TMPC
from sarra.flow import Flow
import logging

logger = logging.getLogger( '__name__' )

class Shovel(Flow):

     def __init__( self, o ):

         super().__init__(o)

         if hasattr(o,'broker'):
             od = o.dictify()
             self.consumer = TMPC( o.broker, od, is_subscriber=True )

         if hasattr(o,'post_broker'):
             self.poster = TMPC( o.post_broker, {
                  'broker':o.post_broker, 'exchange':o.post_exchange }, 
                  is_subscriber=False )
 
     def gather( self ): 
  
         self.new_worklist=[]
         m = self.consumer.getNewMessage() 
         # raw message has... m.body, m.t
         # FIXME: perhaps if becomes while...
         if m is not None:
              self.new_worklist.append( m )

         #logger.info( 'shovel/gather work_list: %s' % self.new_worklist ) 

         return

     def post( self ):
         #logger.info( 'shovel/post work_list: %s' % self.new_worklist ) 
         for m in self.new_worklist:
             # FIXME: outlet = url, outlet=json.
             self.poster.putNewMessage(m)

     def close( self ):
         super().close()
         self.consumer.close()
         self.poster.close()
         logger.info( 'shovel/close completed cleanly' )
 
     #def do( self ):
     #    pass

     
     def report( self ):
         """
         shovels inherently do not do anything substantive to a file, so suppress reports.
         """
         pass

