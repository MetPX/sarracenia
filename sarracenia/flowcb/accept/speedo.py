#!/usr/bin/python3
"""
  msg_speedo
  
  give a *speedometer* reading on the messages going through an exchange.
  as this is an on_msg 

  accumulate the number of messages and the bytes they represent over a period of time.
  options:

  msg_speedo_interval -- how often the speedometer is updated. (default: 5)
  msg_speedo_maxlag  -- if the message flow indicates that messages are 'late', emit warnings.
                    (default 60)

  dependency:
     requires python3-humanize module.

"""

import os, stat, time
import calendar
import humanize
import datetime
from sarracenia import timestr2flt, nowflt
import logging
from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)

class Speedo(FlowCB):
    def __init__(self, options):
        """
           set defaults for options.  can be overridden in config file.
        """
        self.o = options
        if hasattr(self.o, 'msg_speedo_maxlag'):
            if type(self.o.msg_speedo_maxlag) is list:
                self.o.msg_speedo_maxlag = int(self.o.msg_speedo_maxlag[0])
        else:
            self.o.msg_speedo_maxlag = 60
        logger.debug("speedo init: 2 ")

        if hasattr(self.o, 'msg_speedo_interval'):
            if type(self.o.msg_speedo_interval) is list:
                self.o.msg_speedo_interval = int(self.o.msg_speedo_interval[0])
        else:
            self.o.msg_speedo_interval = 5

        now = nowflt()
        self.o.msg_speedo_last = now
        self.o.msg_speedo_msgcount = 0
        self.o.msg_speedo_bytecount = 0

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:
            msgtime = timestr2flt(message['pubTime'])
            now = nowflt()
            self.o.msg_speedo_msgcount = self.o.msg_speedo_msgcount + 1

            (method, psize, ptot, prem, pno) = msg['partstr'].split(',')

            self.o.msg_speedo_bytecount = self.o.msg_speedo_bytecount + int(psize)

            #not time to report yet.
            if self.o.msg_speedo_interval > now - self.o.msg_speedo_last:
                new_incoming.append(message)
                continue

            lag = now - msgtime
            logger.info("speedo: %3d messages received: %5.2g msg/s, %s bytes/s, lag: %4.2g s"
                % (self.o.msg_speedo_msgcount, self.o.msg_speedo_msgcount /
                   (now - self.o.msg_speedo_last),
                   humanize.naturalsize(self.o.msg_speedo_bytecount /
                                        (now - self.o.msg_speedo_last),
                                        binary=True,
                                        gnu=True), lag))

            # Set the maximum age, in seconds, of a message to retrieve.

            if lag > self.o.msg_speedo_maxlag:
                logger.warning("speedo: Excessive lag! Messages posted %s " %
                               humanize.naturaltime(datetime.timedelta(seconds=lag)))

            self.o.msg_speedo_last = now
            self.o.msg_speedo_msgcount = 0
            self.o.msg_speedo_bytecount = 0
            new_incoming.append(message)
            #TODO not sure if we should be rejecting mesaages anywhere
        worklist.incoming = new_incoming
