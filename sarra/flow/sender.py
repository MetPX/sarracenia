import sarra.moth
import copy
from sarra.flow import Flow
import logging
import urllib.parse

logger = logging.getLogger(__name__)

default_options = {'accept_unmatched': True, 'download': True}


class Sender(Flow):
    @classmethod
    def assimilate(cls, obj):
        obj.__class__ = Sender

    def name(self):
        return 'sender'

    def __init__(self):

        self.plugins['load'].append('sarra.plugin.gather.message.Message')

        if hasattr(self.o, 'post_exchange'):
            self.plugins['load'].append('sarra.plugin.post.message.Message')

        Sender.assimilate(self)
        self.scheme = urllib.parse.urlparse(self.o.destination).scheme

    def do(self):

        self.do_send()

        logger.info('processing %d messages worked!' % len(self.worklist.ok))
