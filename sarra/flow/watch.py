
import sarra.moth
import copy
from sarra.flow import Flow
import logging

logger = logging.getLogger( __name__ )


default_options = { 
    'accept_unmatched': True, 
    'blocksize': 1,
    'bufsize' : 1024*1024,
    'download' : False, 
    'events': 'create|delete|link|modify',
    'follow_symlinks': False,
    'force_polling': False,
    'inflight': None,
    'part_ext' : 'Part', 
    'partflg': '1',
    'post_baseDir': None,
    'preserve_mode': True,
    'preserve_time': True,
    'randomize': False,
    'rename': None,
    'sumflg': 'sha512',
    'post_on_start': False,
    'sleep': 5,
    'suppress_duplicates': 0
}

class Watch(Flow):


     @classmethod
     def assimilate(cls,obj):
         obj.__class__ = Watch

     def name(self):
         return 'watch'

     def __init__( self ):

         logger.info('watching!')
         self.plugins['load'].append('sarra.plugin.gather.file.File')
         self.plugins['load'].append('sarra.plugin.post.message.Message')
         Watch.assimilate(self)
