import logging
from sarracenia.flowcb import FlowCB
import hashlib
logger = logging.getLogger(__name__)


class Distbydir(FlowCB):
    """
      Override the hash of the identity field so that products can be grouped by directory in the relPath
      this ensures that all products received from the same directory get posted to the same
      exchange when post_exchangeSplit is active.

      settings:

      python path index      0          1       2       3
      msg['relPath'] = my_favourite/second44/third33/thefile.txt

      distbydir_offset = -2 ... hashes "third33"
      distbydir_offset = 1  ... hashes "second44"

      can pick, using python indexing, any element of the path.
    """
    def __init__(self, options):
        super().__init__(options,logger)

        # setting it to -2 means the last directory in a path.
        self.o.add_option( 'distbydir_offset', 'count', -2 )

    def after_accept(self, worklist):
        for m in worklist.incoming:
            m['_deleteOnPost'] |= set(['exchangeSplitOverride'])
            m['exchangeSplitOverride'] = int(hashlib.md5(m['relPath'].split('/')[self.o.distbydir_offset]).hexdigest()[0])


