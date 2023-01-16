import logging
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Data(FlowCB):
    """
       duplicate suppression based on data alone. Overrides the path used for lookups
       in the cache so that all files have the same name, and so if the checksum
       is the same, regardless of file name, it is considered a duplicate.
    """
    def after_accept(self, worklist):
        for m in worklist.incoming:
            if not 'nodupe_override' in m:
                m['_deleteOnPost'] |= set(['nodupe_override'])
                m['nodupe_override'] = {}
            m['nodupe_override']['path'] = 'data'
