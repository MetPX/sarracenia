"""
Plugin posthourtree.py:
    When posting a file, insert an hourly directory into the delivery path hierarchy.

Example:
    input A/B/c.gif  --> output A/B/<hour>/c.gif

Usage:
    flowcb sarracenia.flowcb.accept.posthourtree.PostHourTree

"""
import logging
import sys, os, os.path, time, stat
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class PostHourTree(FlowCB):
    def __init__(self, options):
        self.o = options

    def after_accept(self, worklist):
        for message in worklist.incoming:
            datestr = time.strftime('%H', time.localtime())  # pick the hour
            # insert the hour into the rename header of the message to be posted.
            new_fname = message['headers']['rename'].split('/')
            message['headers']['rename'] = '/'.join(
                new_fname[0:-1]) + '/' + datestr + '/' + new_fname[-1]
            logger.info("post_hour_tree: rename: %s" %
                        message['headers']['rename'])
