
import sarra.moth
import copy
from sarra.flow import Flow
import logging

logger = logging.getLogger( '__name__' )

default_options = { 
    'download' : False, 
    'accept_unmatched': True, 
    'suppress_duplicates': 0
}

class Shovel(Flow):


     @classmethod
     def assimilate(cls,obj):
         obj.__class__ = Shovel

     def name(self):
         return 'shovel'

     def __init__( self ):

         logger.error('hoho... shoveling!')
         self.plugins['load'].append('sarra.plugin.gather.message.Message')
         self.plugins['load'].append('sarra.plugin.post.message.Message')
         Shovel.assimilate(self)
