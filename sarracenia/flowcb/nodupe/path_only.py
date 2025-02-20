import logging
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Path_only(FlowCB):
    """
      Compared to path, path_only also ignores the checksum, size, modification time, etc. so that
      all messages with the same relPath are considered duplicates.
    """
    def after_accept(self, worklist):
        for m in worklist.incoming:
            if not 'nodupe_override' in m:
                m['_deleteOnPost'] |= set(['nodupe_override'])
                m['nodupe_override'] = {}
            
            # don't need m['nodupe_override']['path'] = m['relPath']
            # it already gets set to relPath by default
            m['nodupe_override']['key'] = m['relPath']
