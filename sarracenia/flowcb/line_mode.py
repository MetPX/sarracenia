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

logger = logging.getLogger(__name__)


class Line_Mode(FlowCB):
    def __init__(self, options):

        self.o = options

        if not hasattr(options, 'chmod'):
            self.o.chmod = 0o4

        logger.setLevel( getattr( logging, options.logLevel.upper() ) )

        logger.debug(
            "line_mode initialized mask (from chmod setting) is: %03o " %
            self.o.chmod)

    def modstr2num(self, m):
        mode = 0
        if (m[0] == 'r'): mode += 4
        if (m[1] == 'w'): mode += 2
        if (m[2] == 'x'): mode += 1
        return mode

    def on_line(self, line):

        parts = line.split()

        modstr = parts[0]

        mode = 0
        mode += self.modstr2num(modstr[1:4]) << 6
        mode += self.modstr2num(modstr[4:7]) << 3
        mode += self.modstr2num(modstr[7:10])

        #logger.info("line_mode: %s mode: %03o" %  ( line, mode ) )

        if ((mode & self.o.chmod) == self.o.chmod):
            return line
        else:
            return None
