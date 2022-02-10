
import logging
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)



class Data(FlowCB):
    def __init__(self, options):
        self.o = options

    def after_accept(self, worklist ):
        for m in worklist.incoming:
            if not 'nodupe_override' in m:
                m['_deleteOnPost'] |= set( [ 'nodupe_override' ] )
                m['nodupe_override'] = {}
            m['nodupe_override']['path'] = 'data'

