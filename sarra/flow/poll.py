
import sarra.moth
import copy
from sarra.flow import Flow
import logging

logger = logging.getLogger( '__name__' )


default_options = { 
    'accept_unmatched': False, 
    'blocksize': 1,
    'bufsize' : 1024*1024,
    'chmod' : 0o400,
    'destination': None,
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
    'sumflg': 'cod,md5',
    'post_on_start': False,
    'sleep': -1,
    'suppress_duplicates': 0
}

class Poll(Flow):


     @classmethod
     def assimilate(cls,obj):
         obj.__class__ = Poll

     def name(self):
         return 'poll'

     def __init__( self ):

         logger.info('polling!')
         self.plugins['load'].append('sarra.plugin.gather.remote.Remote')
         self.plugins['load'].append('sarra.plugin.post.message.Message')
         Poll.assimilate(self)
