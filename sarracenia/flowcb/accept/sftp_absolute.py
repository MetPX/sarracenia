#!/usr/bin/python3
"""
Description:
    SR3 plugin that appends / to SFTP baseUrl's that have no directory on the end.

    In v2 all paths were absolute, in sr3 they are relative. adding this plugin makes
    sr3 behave like v2 when processing sftp urls.

    the value of msg['baseUrl'] in messages is changed:

    sftp://user@host --> sftp://user@host/

    so a subscriber will with a message relPath=a/b/c will download from /a/b/c as it would in v2.
    Without this modification, sr3 would download from ~/a/b/c on the remote.

Usage:                
    flowcb accept.sftp_absolute

"""

import logging
from sarracenia.flowcb import FlowCB
import urllib.parse

logger = logging.getLogger(__name__)

class Sftp_absolute(FlowCB):

      def __init__(self, options) :
          super().__init__(options,logger)

      def after_accept(self, worklist):

          for msg in worklist.incoming:

              if msg['baseUrl'].startswith('sftp:'):
                  u = urllib.parse.urlparse(msg['baseUrl'])
                  if u.path == '':
                      msg['baseUrl'] += '/'
                      logger.info( f"appended / {msg['baseUrl']}")
                  elif u.path[0] != '/':
                      msg['baseUrl'] = u.scheme + '://' + u.netloc + '/' + u.path
                      logger.info( f"prepended / {msg['baseUrl']}")
                  continue
              logger.info( "no baseUrl change")

