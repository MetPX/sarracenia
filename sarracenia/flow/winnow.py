from sarracenia.flow import Flow
import logging

logger = logging.getLogger(__name__)

default_options = {
        'acceptUnmatched': True, 
        'nodupe_ttl': 300,
        'logDuplicates': True
}


class Winnow(Flow):
    """
       * subscribe to a stream of messages.
       * suppress duplicates,
       * post the thinned out stream somewhere else.
    """
    def __init__(self, options):

        super().__init__(options)
        self.plugins['load'].insert(
            0, 'sarracenia.flowcb.gather.message.Message')
        self.plugins['load'].insert(0,
                                    'sarracenia.flowcb.post.message.Message')
