"""
Plugin hourtree.py:
    When receiving a file, insert an hourly directory into the local delivery path hierarchy.

Example:
    input A/B/c.gif  --> output A/B/<hour>/c.gif

Usage:
    flowcb sarracenia.flowcb.accept.hourtree.HourTree

"""

import logging
import sys, os, os.path, time, stat
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class HourTree(FlowCB):
    def __init__(self, options):
        super().__init__(options,logger)

    def after_accept(self, worklist):
        for message in worklist.incoming:
            datestr = time.strftime('%H', time.localtime())  # pick the hour.
            message['new_dir'] += '/' + datestr  # append the hourly element to the directory tree.

            # insert the additional hourly directory into the path of the file to be written.
            new_fname = message['new_file'].split('/')
            message['new_file'] = '/'.join(new_fname[0:-1]) + '/' + datestr + '/' + new_fname[-1]
