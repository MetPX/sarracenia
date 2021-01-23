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


class Line_Mode(object):
    def __init__(self, parent):
        if not hasattr(parent, 'chmod'):
            parent.chmod = 0o4

        parent.logger.debug(
            "line_mode initialized mask (from chmod setting) is: %03o " %
            parent.chmod)

    def modstr2num(self, m):
        mode = 0
        if (m[0] == 'r'): mode += 4
        if (m[1] == 'w'): mode += 2
        if (m[2] == 'x'): mode += 1
        return mode

    def perform(self, parent):

        parts = parent.line.split()

        modstr = parts[0]

        mode = 0
        mode += self.modstr2num(modstr[1:4]) << 6
        mode += self.modstr2num(modstr[4:7]) << 3
        mode += self.modstr2num(modstr[7:10])

        #parent.logger.info("line_mode: %s mode: %03o" %  ( parent.line, mode ) )

        return ((mode & parent.chmod) == parent.chmod)


line_mode = Line_Mode(self)

self.on_line = line_mode.perform
