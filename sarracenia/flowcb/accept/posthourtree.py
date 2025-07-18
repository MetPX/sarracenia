"""
Plugin posthourtree.py:
    When posting a file, insert an hourly directory into the delivery path hierarchy.

Example:
    input A/B/c.gif  --> output A/B/<hour>/c.gif

Usage:
    callback accept.posthourtree

"""
import logging
import sys, os, os.path, time, stat
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Posthourtree(FlowCB):
    def __init__(self, options):
        super().__init__(options, logger)

    def after_accept(self, worklist):
        for message in worklist.incoming:
            datestr = time.strftime('%H', time.gmtime())  # pick the hour
            # insert the hour into the rename header of the message to be posted.
            message['new_dir'] += '/' + datestr 
            logger.info(  f"post_hour_tree: new_dir: {message['new_dir']}" )
