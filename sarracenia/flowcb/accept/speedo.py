"""
Plugin speedo.py:
    Gives a *speedometer* reading on the messages going through an exchange.
    as this is an after_accept
    Accumulate the number of messages and the bytes they represent over a period of time.

Options:
    msgSpeedoInterval -> how often the speedometer is updated. (default: 5)
    msg_speedo_maxlag  -> if the message flow indicates that messages are 'late', emit warnings. (default 60)

Usage: 
    callback accept.speedo
    msgSpeedoInterval x
    msg_speedo_maxlag y
"""

import os, stat, time
import calendar
import datetime

from sarracenia import timestr2flt, nowflt, naturalSize, naturalTime
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

        if hasattr(self.o, 'msgSpeedoInterval'):
            if type(self.o.msgSpeedoInterval) is list:
                self.o.msgSpeedoInterval = int(self.o.msgSpeedoInterval[0])
        else:
            self.o.msgSpeedoInterval = 5

        now = nowflt()
        self.o.msg_speedo_last = now
        self.o.msg_speedo_msgcount = 0
        self.o.msg_speedo_bytecount = 0

    def after_accept(self, worklist):
        for message in worklist.incoming:
            msgtime = timestr2flt(message['pubTime'])
            now = nowflt()
            self.o.msg_speedo_msgcount = self.o.msg_speedo_msgcount + 1

            (method, psize, ptot, prem, pno) = message['partstr'].split(',')

            self.o.msg_speedo_bytecount = self.o.msg_speedo_bytecount + int(
                psize)

            #not time to report yet.
            if self.o.msgSpeedoInterval > now - self.o.msg_speedo_last:
                continue

            lag = now - msgtime
            logger.info(
                "speedo: %3d messages received: %5.2g msg/s, %s bytes/s, lag: %4.2g s"
                % (self.o.msg_speedo_msgcount, self.o.msg_speedo_msgcount /
                   (now - self.o.msg_speedo_last),
                   naturalSize(self.o.msg_speedo_bytecount / (now - self.o.msg_speedo_last),), lag))

            # Set the maximum age, in seconds, of a message to retrieve.

            if lag > self.o.msg_speedo_maxlag:
                logger.warning(
                    "speedo: Excessive lag! Messages posted %s " %
                    naturalTime(datetime.timedelta(seconds=lag)))

            self.o.msg_speedo_last = now
            self.o.msg_speedo_msgcount = 0
            self.o.msg_speedo_bytecount = 0
