from sarracenia.flow import Flow
import logging

logger = logging.getLogger(__name__)

default_options = {'acceptUnmatched': True, 'nodupe_ttl': 0}


class Shovel(Flow):
    """
       * subscribe to some messages.
       * post them somewhere else.
    """
    def __init__(self, options):

        super().__init__(options)
        self.plugins['load'].insert(
            0, 'sarracenia.flowcb.gather.message.Message')
        self.plugins['load'].insert(0,
                                    'sarracenia.flowcb.post.message.Message')
