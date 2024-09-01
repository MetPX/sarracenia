from sarracenia.flow import Flow
import logging

logger = logging.getLogger(__name__)

default_options = {
    'acceptUnmatched': True,
    'blockSize': 1,
    'bufSize': 1024 * 1024,
    'follow_symlinks': False,
    'force_polling': False,
    'inflight': None,
    'part_ext': 'Part',
    'partflg': '1',
    'post_baseDir': None,
    'permCopy': True,
    'timeCopy': True,
    'randomize': False,
    'post_on_start': False,
    'sleep': -1,
    'nodupe_ttl': 0
}

#'sumflg': 'sha512',


class Post(Flow):
    """
       post messages about local files. 
    """
    def __init__(self, options):

        super().__init__(options)
        self.plugins['load'].insert(0, 'sarracenia.flowcb.gather.file.File')
        self.plugins['load'].insert(0,
                                    'sarracenia.flowcb.post.message.Message')
