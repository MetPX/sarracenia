from sarracenia.flow import Flow
import logging

logger = logging.getLogger(__name__)

default_options = {'acceptUnmatched': False, 'download': True, 'mirror': False}


class Subscribe(Flow):
    """
       * subscribe to messages about files.
       * download the corresponding files.
    """
    def __init__(self, options):

        super().__init__(options)
        self.plugins['load'].insert(
            0, 'sarracenia.flowcb.gather.message.Message')

        if hasattr(self.o, 'post_exchange'):
            self.plugins['load'].insert(
                0, 'sarracenia.flowcb.post.message.Message')

    def do(self):

        if self.o.download:
            self.do_download()
        else:
            # mark all remaining messages as done.
            self.worklist.ok = self.worklist.incoming
            self.worklist.incoming = []

        logger.debug('processing %d messages worked!' % len(self.worklist.ok))
