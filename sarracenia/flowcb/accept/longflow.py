"""
Plugin longflow.py:
    This plugin is strictly for self-test purposes.
    Creates a header 'toolong' that is longer than 255 characters, and so gets truncated.
    Each header in a message that is too long should generate a warning message in the sarra log.
    flow_test checks for the 'truncated' error message.
    Put some utf characters in there to make it interesting... (truncation complex.)

Usage:
    flowcb sarracenia.flowcb.accept.longflow.LongFlow
"""

import logging
import os, stat, time
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class LongFlow(FlowCB):
    def __init__(self, options):
        self.o = options

    def after_accept(self, worklist):
        for message in worklist.incoming:
            logger.info('setting toolong header')
            message['headers']['toolong'] = '1234567890ßñç' * 26
