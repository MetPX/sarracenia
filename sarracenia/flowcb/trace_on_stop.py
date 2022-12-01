"""
This plugin prints a traceback when the program is stopped

  plugin trace_on_stop

"""
import io
import logging
import traceback
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class TRACE_ON_STOP(FlowCB):
    def __init__(self):
        pass

    def on_stop(self):
        self.LOG_TRACE()
        return True

    def LOG_TRACE(self):
        tb_output = io.StringIO()
        traceback.print_stack(None, None, tb_output)
        logger.info("\n\n****************************************\n" + \
                             "***** PRINTING TRACEBACK FROM STOP *****\n" + \
                             "****************************************\n" + \
                           "\n" + tb_output.getvalue()             + "\n" + \
                           "\n****************************************\n")
        tb_output.close()
