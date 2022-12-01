"""
Plugin printlag.py:
     This is an after_accept plugin.
     print a message indicating how old messages received are.
     this should be used as an on_part script. For each part received it will print a line
     in the local log that looks like this:

     2015-12-23 22:54:30,328 [INFO] posted: 20151224035429.115 (lag: 1.21364 seconds ago) to deliver: /home/peter/test/dd/bulletins/alphanumeric/20151224/SA/EGGY/03/SAUK32_EGGY_240350__EGAA_64042,

     the number printed after "lag:" the time between the moment the message was originally posted on the server,
     and the time the script was called, which is very near the end of writing the file to local disk.

     This can be used to gauge whether the number of instances or internet link are sufficient
     to transfer the data selected.  if the lag keeps increasing, then something must be done.

Usage:
    flowcb sarracenia.flowcb.accept.printlag.PrintLag

"""
import calendar
import logging
import os
import stat
import time
from sarracenia import timestr2flt, nowflt
from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)


class PrintLag(FlowCB):
    def __init__(self, options):
        self.o = options
        pass

    def after_accept(self, worklsit):
        for message in worklsit.incoming:
            then = timestr2flt(message['pubTime'])
            now = nowflt()

            logger.info(
                "print_lag, posted: %s, lag: %.2f sec. to deliver: %s, " %
                (message['pubTime'], (now - then), message['new_file']))
