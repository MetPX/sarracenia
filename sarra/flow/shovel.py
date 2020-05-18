
from sarra.tmpc import TMPC
from sarra.flow import Flow
import logging

logger = logging.getLogger( '__name__' )

class Shovel(Flow):

     def __init__( self, o ):

         super().__init__(o)

         logger.info( 'shovel/__init__ 1' ) 
         if hasattr(o,'broker'):
             od = o.dictify()
             self.consumer = TMPC( o.broker, od, is_subscriber=True )

         logger.info( 'shovel/__init__ 2' ) 
         if hasattr(o,'post_broker'):
             self.poster = TMPC( o.post_broker, {
                  'broker':o.post_broker, 'exchange':o.resolved_exchanges }, 
                  is_subscriber=False )
         logger.info( 'shovel/__init__ 3' ) 
 
     def gather( self ):
         raw_message = self.consumer.getNewMessage() 
         # raw message has... m.body, m.t

         msg = json.loads( raw_message )
         return

     def post( self ):
         for m in self.new_worklist:
             mj = json.dumps(m)

             # FIXME: outlet = url, outlet=json.
             self.poster.putNewMessage(mj)

     def close( self ):
         self.consumer.close()
         self.poster.close()
