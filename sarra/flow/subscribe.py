
import sarra.moth
import copy
from sarra.flow import Flow
import logging

logger = logging.getLogger( __name__ )

default_options = { 
    'download' : False, 
    'accept_unmatched': True, 
    'suppress_duplicates': 0
}

class Subscribe(Flow):


    @classmethod
    def assimilate(cls,obj):
        obj.__class__ = Subscribe

    def name(self):
        return 'subscribe'

    def __init__( self ):

        logger.error('hoho... shoveling! options: %s ' % self.o )
        self.o.dump()
        self.plugins['load'].append('sarra.plugin.gather.message.Message')

        if hasattr(self.o,'post_exchange'):
            self.plugins['load'].append('sarra.plugin.post.message.Message')

        Subscribe.assimilate(self)


    def do( self ):

        self.do_download()

        # mark all remaining messages as done.
        #self.worklist.ok = self.worklist.incoming
        #self.worklist.incoming = []
        logger.info('processing %d messages worked!' % len(self.worklist.ok) )

