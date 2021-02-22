import sarracenia.moth
import copy
from sarracenia.flow import Flow
import logging

logger = logging.getLogger(__name__)

default_options = {'accept_unmatched': True, 'download': True}


class Sarra(Flow):
    def __init__(self, options):

        super().__init__(options)
        self.plugins['load'].append('sarracenia.flowcb.gather.message.Message')

        if hasattr(self.o, 'post_exchange'):
            self.plugins['load'].append('sarracenia.flowcb.post.message.Message')

    def do(self):

        if self.o.download:
            self.do_download()
        else:
            # mark all remaining messages as done.
            self.worklist.ok = self.worklist.incoming
            self.worklist.incoming = []

        logger.debug('processing %d messages worked!' % len(self.worklist.ok))
