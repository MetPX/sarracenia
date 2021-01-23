#!/usr/bin/python3
"""
This plugin prints a traceback when the program is stopped

  plugin trace_on_stop

"""


class TRACE_ON_STOP(object):
    def __init__(self, parent):
        pass

    def on_stop(self, parent):
        self.logger = parent.logger

        self.LOG_TRACE()

        return True

    def LOG_TRACE(self):
        import io, traceback

        tb_output = io.StringIO()
        traceback.print_stack(None, None, tb_output)
        self.logger.info("\n\n****************************************\n" + \
                             "***** PRINTING TRACEBACK FROM STOP *****\n" + \
                             "****************************************\n" + \
                           "\n" + tb_output.getvalue()             + "\n" + \
                           "\n****************************************\n")
        tb_output.close()


self.plugin = 'TRACE_ON_STOP'
