#!/usr/bin/python3
"""
   print the age of files written (compare current time to mtime of message.)
   usage:


   on_file file_age


"""

import os, stat, time
import logging
from sarracenia.flowcb import FlowCB
from sarracenia import nowflt, timestr2flt

logger = logging.getLogger(__name__)

class File_Age(FlowCB):
    def __init__(self, options):
        logger.debug("file_age initialized")
        self.o = options

    def on_file(self):
        if not 'mtime' in self.o.msg['headers'].keys():
            return None

        now = nowflt()
        mtime = timestr2flt(self.o.msg['headers']['mtime'])
        age = now - mtime
        logger.info("file_age %g seconds for %s" %
                           (age, self.o.msg['new_file']))
        return None

