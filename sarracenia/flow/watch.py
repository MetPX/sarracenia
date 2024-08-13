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
    'sumflg': 'sha512',
    'post_on_start': False,
    'sleep': 5,
    'nodupe_ttl': 0
}


class Watch(Flow):
    """
      * create messages for files that appear in a directory.

    """
    def __init__(self, options):

        super().__init__(options)
        logger.info('watching!')
        self.plugins['load'].insert(0, 'sarracenia.flowcb.gather.file.File')
        self.plugins['load'].insert(0,
                                    'sarracenia.flowcb.post.message.Message')
