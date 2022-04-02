#!/usr/bin/python3

import os, stat, time
from hashlib import md5

from sarracenia import timeflt2str, timestr2flt, nowflt
"""
   Confirm that files downloaded are the ones announced, by comparing the 
   checksums of computed as parts are downloaded with the corresponding 
   announcement.

   In the case of excessive lag (messages are old) only issue a warning about 
   checksum mismatches.  (return True)
   In the case of mismatches with current data, create and error message and
   return False (refusing to process data.)

   part_check_lag_threshold 300
   
   The maximum time (in seconds) a message is considered current is set by 
   the part_check_lag_threshold setting, and defaults to five minutes (300 
   seconds)

   The threshold is necessary because in the event of a communications failure, 
   many messages can queue up.  Multiple versions of the same file can be 
   announced while the communications are ruptured, but when the download 
   occurs, the latest version will always be retrieved.


"""


class PartCheck(object):
    def __init__(self, parent):

        if not hasattr(parent, 'part_check_lag_threshold'):
            parent.part_check_lag_threshold = 300
        else:
            if type(parent.part_check_lag_threshold) is list:
                parent.part_check_lag_threshold = int(
                    parent.part_check_lag_threshold[0])

        return

    def perform(self, parent):
        logger = parent.logger
        msg = parent.msg

        import calendar

        then = timestr2flt(msg.pubtime)
        now = nowflt()
        lag = now - then

        if msg.onfly_checksum != msg.checksum:
            msg = "checksum differ - %s - %s  msg %s" % (
                msg.new_file, parent.onfly_checksum, msg.checksum)
            if lag > parent.part_check_lag_threshold:
                logger.warning(
                    "part_check might just be referring to an older version of file, but "
                    + msg)
                return True
            else:
                logger.error("part_check rejecting " + msg)
                return False

        logger.info("part_check Checksum matched for : %s" % msg.new_file)
        return True


partcheck = PartCheck(self)
self.on_part = partcheck.perform
