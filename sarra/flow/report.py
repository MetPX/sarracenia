import sarra.moth
import copy
from sarra.flow import Flow
import logging

logger = logging.getLogger(__name__)

default_options = {'accept_unmatched': True, 'suppress_duplicates': 0}


class Report(Flow):
    def __init__(self, options):

        super().__init__(options)
        self.plugins['load'].append('sarra.flowcb.gather.message.Message')

        if hasattr(self.o, 'post_exchange'):
            self.plugins['load'].append('sarra.flowcb.post.message.Message')
