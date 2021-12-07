#!/usr/bin/python3
"""
Plugin skipold.py:
    Discard messages if they are too old, so that rather than downloading
    obsolete data, only current data will be retrieved. This should be used as an after_accept script.

    For each announcement, check how old it is, and if it exceeds the threshold in the
    routine, discard the message by appending to worklist.rejected, after printing a local log message saying so.

    The message can be used to gauge whether the number of instances or internet link are sufficient
    to transfer the data selected.  If the lag keeps increasing, then likely instances should be
    increased.

Options:
    It is mandatory to set the threshold for discarding messages (in seconds) in the configuration  file.
        - skipThreshold 10

    This will result in messages which are more than 10 seconds old being skipped.
    default is one hour (3600 seconds.)

Usage: 
    flowcb sarracenia.flowcb.accept.skipold.SkipOld
    skipThreshold x
"""

import calendar
import logging
import os
import stat
import time
from sarracenia import timestr2flt, nowflt
from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)


class SkipOld(FlowCB):
    def __init__(self, options):
        self.o = options
        if not hasattr(self.o, 'skipThreshold'):
            self.o.skipThreshold = 3600
        else:
            if type(self.o.skipThreshold) is list:
                self.o.skipThreshold = int(self.o.skipThreshold[0])

    def after_accept(self, worklist):
        new_incoming = []

        for message in worklist.incoming:
            then = timestr2flt(message['pubTime'])
            now = nowflt()

            # Set the maximum age, in seconds, of a message to retrieve.
            lag = now - then

            if lag > int(self.o.skipThreshold):
                logger.info("SkipOld, Excessive lag: %g sec. Skipping download of: %s, " % (lag, message['new_file']))
                worklist.rejected.append(m)
                continue

            new_incoming.append(message)
        worklist.incoming = new_incoming
