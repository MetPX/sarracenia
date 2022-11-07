from sarracenia.flow import Flow
import logging
import urllib.parse

logger = logging.getLogger(__name__)

default_options = {'acceptUnmatched': True, 'download': True}


class Sender(Flow):
    """
       * subscribe to a stream of messages about local files.
       * send the files to a remote server.
       * modify the messages to refer to the remote file copies.
       * post the messages for subscribers of the remote server.
    """
    def __init__(self, options):

        super().__init__(options)
        self.plugins['load'].insert(
            0, 'sarracenia.flowcb.gather.message.Message')

        if hasattr(self.o, 'post_exchange'):
            self.plugins['load'].insert(
                0, 'sarracenia.flowcb.post.message.Message')

        self.scheme = urllib.parse.urlparse(self.o.remoteUrl).scheme

    def do(self):

        self.do_send()

        logger.debug('processing %d messages worked!' % len(self.worklist.ok))
