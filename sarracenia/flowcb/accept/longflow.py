#!/usr/bin/python3
"""
  This plugin is strictly for self-test purposes.

  post_long - creates a header 'toolong' that is longer than 255 characters, and so gets truncated.
  Each header in a message that is too long should generate a warning message in the sarra log.
  flow_test checks for the 'truncated' error message.

  put some utf characters in there to make it interesting... (truncation complex.)
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





