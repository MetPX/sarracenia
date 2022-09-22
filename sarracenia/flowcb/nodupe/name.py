import logging
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Name(FlowCB):
    """
      Override the the comparison so that files with the same name,
      regardless of what directory they are in, are considered the same.
      This is useful when receiving data from two different sources (two different trees)
      and winnowing between them.
    """
    def __init__(self, options):
        self.o = options

    def after_accept(self, worklist):
        for m in worklist.incoming:
            if not 'nodupe_override' in m:
                m['_deleteOnPost'] |= set(['nodupe_override'])
                m['nodupe_override'] = {}

            m['nodupe_override']['path'] = m['relPath'].split('/')[-1]
            m['nodupe_override']['key'] = m['relPath'].split('/')[-1]
