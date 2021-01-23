#!/usr/bin/python3
"""
   print the age of files written (compare current time to mtime of message.)
   usage:


   on_file file_age


"""

import os, stat, time

from sarracenia import nowflt, timestr2flt


class File_Age(object):
    def __init__(self, parent):
        parent.logger.debug("file_age initialized")

    def perform(self, parent):
        import time

        if not 'mtime' in parent.msg.headers.keys():
            return True

        now = nowflt()
        mtime = timestr2flt(parent.msg.headers['mtime'])
        age = now - mtime
        parent.logger.info("file_age %g seconds for %s" %
                           (age, parent.msg.new_file))
        return True


file_age = File_Age(self)

self.on_file = file_age.perform
