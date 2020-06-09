
import sarra.moth
import copy
from sarra.flow import Flow
import logging

logger = logging.getLogger( '__name__' )


class Shovel(Flow):

     default_options = { 
         'download' : False, 
         'accept_unmatched': True, 
         'suppress_duplicates': 0
     }

     @classmethod
     def assimilate(cls,obj):
         obj.__class__ = Shovel

     def name(self):
         return 'shovel'

     def __init__( self ):

         logger.error('hoho... shoveling!')
         self.plugins['load'].append('sarra.plugin.gather.message.Message')
         Shovel.assimilate(self)

     def report( self ):
         """
         shovels inherently do not do anything substantive to a file, so suppress reports.
         """
         pass

