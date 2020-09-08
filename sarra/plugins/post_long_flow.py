#!/usr/bin/python3
"""
  This plugin is strictly for self-test purposes.

  post_long - creates a header 'toolong' that is longer than 255 characters, and so gets truncated.
  Each header in a message that is too long should generate a warning message in the sarra log.
  flow_test checks for the 'truncated' error message.

  put some utf characters in there to make it interesting... (truncation complex.)
"""

import os, stat, time


class Override(object):
    def __init__(self, parent):
        pass

    def perform(self, parent):
        logger = parent.logger
        msg = parent.msg

        parent.logger.info('setting toolong header')
        parent.msg.headers['toolong'] = '1234567890ßñç' * 26

        return True


override = Override(self)
self.on_post = override.perform
