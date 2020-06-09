
import sarra.moth
import copy
from sarra.flow import Flow
import logging

logger = logging.getLogger( '__name__' )


class Winnow(Flow):

     default_options = { 
         'download' : False, 
         'accept_unmatched': True, 
         'suppress_duplicates': 300
     }

     @classmethod
     def assimilate(cls,obj):
         obj.__class__ = Winnow

     def name(self):
         return 'winnow'

     def __init__( self ):

         logger.error('hoho... winnowing!')
         self.plugins['load'].append('sarra.plugin.gather.message.Message')
         Winnow.assimilate(self)

     def report( self ):
         """
         winnows inherently do not do anything substantive to a file, so suppress reports.
         """
         pass

