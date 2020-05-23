
import sarra.moth
import copy
from sarra.flow import Flow
import logging

logger = logging.getLogger( '__name__' )


class Shovel(Flow):

     default_options = { 'download' : False }

     @classmethod
     def assimilate(cls,obj):
         obj.__class__ = Shovel

     def name(self):
         return 'shovel'

     def __init__( self ):

         Shovel.assimilate(self)

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

