"""
   print the age of files written (compare current time to mtime of message.)
   usage:

   flowcb work.age

"""

import os, stat, time
import logging
from sarracenia.flowcb import FlowCB
from sarracenia import nowflt, timestr2flt

logger = logging.getLogger(__name__)


class Age(FlowCB):

    def __init__(self, options):
        logger.debug("file_age initialized")
        self.o = options

    def after_work(self, worklist):
        for m in worklist.ok:
            if not 'mtime' in m:
                return None
            completed = timestr2flt(m['timeCompleted'])
            mtime = timestr2flt(m['mtime'])
            age = completed - mtime
            logger.info("file %s is %d seconds old" % (m['new_file'], age))
