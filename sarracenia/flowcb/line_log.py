#!/usr/bin/env python3
"""

  the default on_line handler for sr_poll. Verifies file are ok to download.
  uses parent.chmod setting as a mask to identify minimum permissions required to download file.

  means owner must have read permission...

sample line from sftp server:

  with following setting:

  chmod 400 

  this would be accepted:
  -rwxrwxr-x 1 1000 1000 8123 24 Mar 22:54 2017-03-25-0254-CL2D-AUTO-minute-swob.xml

  this would be rejected:
  --wxrwxr-x 1 1000 1000 8123 24 Mar 22:54 2017-03-25-0254-CL2D-AUTO-minute-swob.xml

"""

import logging
from sarracenia.flowcb import FlowCB

logger = logging.getLogger('__name__')


class Line_Log(FlowCB):
    def __init__(self, options):
        logger.debug("line_log initialized ")
        self.o = options
        logger.setLevel( getattr( logging, option.logLevel.upper() ) )

    def on_line(self, line):

        logger.info("line_log: reading: %s" % (line))
        return line
