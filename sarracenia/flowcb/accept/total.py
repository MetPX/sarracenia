#!/usr/bin/python3
"""
Plugin total.py:
    Give a running total of the messages received from a broker.
    as this is an after_accept 
    
    NOTE: BYTE COUNT DOES NOT MATCH msg_log:
    accumulate the number of messages and the bytes transferred in the messages over a period of time.
    the bytes represent the message traffic, not the file traffic, msg_log reports file byte counts.

Options:
    - msgTotalInterval -> how often the total is updated. (default: 5)
    - msgTotalMaxlag  -> if the message flow indicates that messages are 'late', emit warnings. (default 60)
    - msgTotalCount -> how many messages to process before stopping the program.

Dependency:
    requires python3-humanize module.

Usage:
    callback accept.total

"""

import os, stat, time
import calendar
import humanize
import datetime
import sys
from sarracenia import timeflt2str, timestr2flt, nowflt
import logging
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class Total(FlowCB):
    def __init__(self, options):
        """
           set defaults for options.  can be overridden in config file.
        """
        self.o = options

        # make self.o know about these possible options FIXME: is the kind ? str? or flt?
        self.o.add_option('msgTotalInterval', 'str')
        self.o.add_option('msgTotalMaxlag', 'str')
        self.o.add_option('msgTotalCount', 'str')

        if hasattr(self.o, 'msgTotalCount'):
            if type(self.o.msgTotalCount) is list:
                self.o.msgTotalCount = int(self.o.msgTotalCount[0])
        else:
            self.o.msgTotalCount = 0

        if hasattr(self.o, 'msgTotalMaxlag'):
            if type(self.o.msgTotalMaxlag) is list:
                self.o.msgTotalMaxlag = int(self.o.msgTotalMaxlag[0])
        else:
            self.o.msgTotalMaxlag = 60

        if hasattr(self.o, 'msgTotalInterval'):
            if type(self.o.msgTotalInterval) is list:
                self.o.msgTotalInterval = int(self.o.msgTotalInterval[0])
        else:
            self.o.msgTotalInterval = 5

        now = nowflt()

        self.o.msg_total_last = now
        self.o.msg_total_start = now
        self.o.msg_total_msgcount = 0
        self.o.msg_total_bytecount = 0
        self.o.msg_total_msgcount = 0
        self.o.msg_total_bytecount = 0
        self.o.msg_total_lag = 0
        logger.debug("msg_total: initialized, interval=%d, maxlag=%d" % \
            ( self.o.msgTotalInterval, self.o.msgTotalMaxlag ) )

    def after_accept(self,worklist):
        new_incoming = []
        for message in worklist.incoming:

            # FIXME so far don't see 'isRetry' as an entry in the message dictionary -> could cause an error
            if message['isRetry']:
                new_incoming.append(message)
                continue

            if (self.o.msg_total_msgcount == 0):
                logger.info("msg_total: 0 messages received: 0 msg/s, 0.0 bytes/s, lag: 0.0 s (RESET)")

            msgtime = timestr2flt(message['pubTime'])
            now = nowflt()

            self.o.msg_total_msgcount = self.o.msg_total_msgcount + 1

            lag = now - msgtime
            self.o.msg_total_lag = self.o.msg_total_lag + lag

            # guess the size of the message payload, ignoring overheads.
            self.o.msg_total_bytecount += (len(self.o.msg['exchange']) +
                                           len(self.o.msg['topic']) +
                                           len(self.o.msg['notice']) +
                                           len(self.o.msg['hdrstr']))

            #not time to report yet.
            if self.o.msgTotalInterval > now - self.o.msg_total_last:
                new_incoming.append(message)
                continue

            logger.info(
                "msg_total: %3d messages received: %5.2g msg/s, %s bytes/s, lag: %4.2g s"
                %
                (self.o.msg_total_msgcount, self.o.msg_total_msgcount /
                 (now - self.o.msg_total_start),
                 humanize.naturalsize(
                     self.o.msg_total_bytecount / (now - self.o.msg_total_start), binary=True,
                     gnu=True), self.o.msg_total_lag / self.o.msg_total_msgcount))
            # Set the maximum age, in seconds, of a message to retrieve.

            if lag > self.o.msgTotalMaxlag:
                logger.warn("total: Excessive lag! Messages posted %s " %
                            humanize.naturaltime(datetime.timedelta(seconds=lag)))
                #FIXME: should we reject here? worklist.rejected.append(message) ?

            self.o.msg_total_last = now

            if (self.o.msgTotalCount > 0) and (self.o.msg_total_msgcount >=self.o.msgTotalCount):
                os._exit(0)

        worklist.incoming = new_incoming



