
import sarra.moth
import copy
from sarra.flow import Flow
import logging

logger = logging.getLogger( __name__ )

default_options = { 
    'accept_unmatched': True, 
    'download': True
}

class Sarra(Flow):


    @classmethod
    def assimilate(cls,obj):
        obj.__class__ = Sarra

    def name(self):
        return 'sarra'

    def __init__( self ):

        self.plugins['load'].append('sarra.plugin.gather.message.Message')

        if hasattr(self.o,'post_exchange'):
            self.plugins['load'].append('sarra.plugin.post.message.Message')

        Sarra.assimilate(self)


    def do( self ):

        if self.o.download:
            self.do_download()
        else:
            # mark all remaining messages as done.
            self.worklist.ok = self.worklist.incoming
            self.worklist.incoming = []

        logger.info('processing %d messages worked!' % len(self.worklist.ok) )

