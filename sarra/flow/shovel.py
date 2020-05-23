
import sarra.moth
import copy
from sarra.flow import Flow
import logging

logger = logging.getLogger( '__name__' )

default_options = { 'download' : False }


class Shovel(Flow):

     def __init__( self, o ):

         super().__init__(o)

         if hasattr(o,'broker'):
             od = o.dictify()
             self.consumer = sarra.moth.Moth( o.broker, od, is_subscriber=True )

         if hasattr(o,'post_broker'):
             props = { 
                 'broker':o.post_broker, 'exchange':o.post_exchange,
                 'loglevel':o.loglevel, 'message_strategy':o.message_strategy
             }
             self.poster = sarra.moth.Moth( o.post_broker, props, is_subscriber=False )
 
     def gather( self ): 
  
         self.worklist.incoming= self.consumer.newMessages()
         #logger.debug( 'shovel/gather work_list: %s' % self.worklist.incoming ) 

         return

     def post( self ):
         #logger.info( 'shovel/post work_list: %s' % self.worklist.incoming ) 

         for m in self.worklist.incoming:
             # FIXME: outlet = url, outlet=json.
             self.poster.putNewMessage(m)
             self.worklist.ok.append(m)

         self.worklist.incoming=[]

     def close( self ):
         super().close()
         self.consumer.close()
         self.poster.close()
         logger.info( 'shovel/close completed cleanly' )
 
     def ack( self, mlist ):
         for m in mlist:
             self.consumer.ack( m )

     def do( self ):
         pass

     
     def report( self ):
         """
         shovels inherently do not do anything substantive to a file, so suppress reports.
         """
         pass

