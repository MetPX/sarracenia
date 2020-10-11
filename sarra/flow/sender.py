import sarra.moth
import copy
from sarra.flow import Flow
import logging
import urllib.parse

logger = logging.getLogger(__name__)

default_options = {'accept_unmatched': True, 'download': True}


class Sender(Flow):
    def __init__(self, options):

        super().__init__(options)
        self.plugins['load'].append('sarra.flowcb.gather.message.Message')

        if hasattr(self.o, 'post_exchange'):
            self.plugins['load'].append('sarra.flowcb.post.message.Message')

        self.scheme = urllib.parse.urlparse(self.o.destination).scheme

    def do(self):

        self.do_send()

        logger.info('processing %d messages worked!' % len(self.worklist.ok))
