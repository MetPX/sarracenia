
import sarra.moth
import copy
from sarra.flow import Flow
import logging

logger = logging.getLogger( __name__ )

default_options = { 
    'download' : False, 
    'accept_unmatched': True, 
    'suppress_duplicates': 300
}

class Winnow(Flow):


     @classmethod
     def assimilate(cls,obj):
         obj.__class__ = Winnow

     def name(self):
         return 'winnow'

     def __init__( self ):

         self.plugins['load'].append('sarra.plugin.gather.message.Message')
         self.plugins['load'].append('sarra.plugin.post.message.Message')
         Winnow.assimilate(self)
