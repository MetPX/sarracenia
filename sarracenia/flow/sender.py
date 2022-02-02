import sarracenia.moth
import copy
from sarracenia.flow import Flow
import logging
import urllib.parse

logger = logging.getLogger(__name__)

default_options = {'acceptUnmatched': True, 'download': True}


class Sender(Flow):
    def __init__(self, options):

        super().__init__(options)
        self.plugins['load'].insert(0, 'sarracenia.flowcb.gather.message.Message')

        if hasattr(self.o, 'post_exchange'):
            self.plugins['load'].insert(0, 'sarracenia.flowcb.post.message.Message')

        self.scheme = urllib.parse.urlparse(self.o.destination).scheme

    def do(self):

        self.do_send()

        logger.debug('processing %d messages worked!' % len(self.worklist.ok))
