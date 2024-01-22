from sarracenia.flow import Flow
import logging

logger = logging.getLogger(__name__)

default_options = {'acceptUnmatched': True, 'download': True}


class Sarra(Flow):
    """
       * download files from a remote server to the local one
       * modify the messages so they refer to the downloaded files.
       * re-post them to another exchange for the next other subscribers.
    """
    def __init__(self, options):

        super().__init__(options)
        self.plugins['load'].insert(
            0, 'sarracenia.flowcb.gather.message.Message')

        if hasattr(self.o, 'post_exchange'):
            self.plugins['load'].insert(
                0, 'sarracenia.flowcb.post.message.Message')
