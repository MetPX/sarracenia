
from sarra.moth import Moth
from sarra.flow import Flow
import logging

logger = logging.getLogger( '__name__' )

class Shovel(Flow):

     def __init__( self, o ):

         super().__init__(o)

         if hasattr(o,'broker'):
             od = o.dictify()
             self.consumer = Moth( o.broker, od, is_subscriber=True )

         if hasattr(o,'post_broker'):
             self.poster = Moth( o.post_broker, {
                  'broker':o.post_broker, 'exchange':o.post_exchange }, 
                  is_subscriber=False )
 
     def gather( self ): 
  
         self.worklist.incoming=[]
         m = self.consumer.getNewMessage() 
         # raw message has... m.body, m.t
         # FIXME: perhaps if becomes while...
         if m is not None:
              self.worklist.incoming.append( m )

         #logger.info( 'shovel/gather work_list: %s' % self.worklist.incoming ) 

         return

     def post( self ):
         #logger.info( 'shovel/post work_list: %s' % self.worklist.incoming ) 
         for m in self.worklist.incoming:
             # FIXME: outlet = url, outlet=json.
             self.poster.putNewMessage(m)

     def close( self ):
         super().close()
         self.consumer.close()
         self.poster.close()
         logger.info( 'shovel/close completed cleanly' )
 
     def ack( self, mlist ):
         for m in mlist:
             self.consumer.ack( m )

     #def do( self ):
     #    pass

     
     def report( self ):
         """
         shovels inherently do not do anything substantive to a file, so suppress reports.
         """
         pass

