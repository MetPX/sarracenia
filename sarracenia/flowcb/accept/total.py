#!/usr/bin/python3
"""
  msg_total
  
  give a running total of the messages received from a broker.
  as this is an on_msg 

  NOTE: BYTE COUNT DOES NOT MATCH msg_log:
  accumulate the number of messages and the bytes transferred in the messages over a period of time.
  the bytes represent the message traffic, not the file traffic, msg_log reports file byte counts.

  options:

  msg_total_interval -- how often the total is updated. (default: 5)
  msg_total_maxlag  -- if the message flow indicates that messages are 'late', emit warnings.
                    (default 60)
  msg_total_count -- how many messages to process before stopping the program.

  dependency:
     requires python3-humanize module.

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

        # make parent know about these possible options

        self.o.declare_option('msg_total_interval')
        self.o.declare_option('msg_total_maxlag')
        self.o.declare_option('msg_total_count')

        if hasattr(self.o, 'msg_total_count'):
            if type(self.o.msg_total_count) is list:
                self.o.msg_total_count = int(self.o.msg_total_count[0])
        else:
            self.o.msg_total_count = 0

        if hasattr(self.o, 'msg_total_maxlag'):
            if type(self.o.msg_total_maxlag) is list:
                self.o.msg_total_maxlag = int(self.o.msg_total_maxlag[0])
        else:
            self.o.msg_total_maxlag = 60

        if hasattr(self.o, 'msg_total_interval'):
            if type(self.o.msg_total_interval) is list:
                self.o.msg_total_interval = int(self.o.msg_total_interval[0])
        else:
            self.o.msg_total_interval = 5

        now = nowflt()

        self.o.msg_total_last = now
        self.o.msg_total_start = now
        self.o.msg_total_msgcount = 0
        self.o.msg_total_bytecount = 0
        self.o.msg_total_msgcount = 0
        self.o.msg_total_bytecount = 0
        self.o.msg_total_lag = 0
        logger.debug("msg_total: initialized, interval=%d, maxlag=%d" % \
            ( self.o.msg_total_interval, self.o.msg_total_maxlag ) )

    def after_accept(self,worklist):
        new_incoming = []
        for message in worklist.incoming:

            # FIXME so far don't see 'isRetry' as an entry in the message dictionary -> could cause an error
            if message['isRetry']:
                new_incoming.append(message)
                continue

            if (self.o.msg_total_msgcount == 0):
                logger.info("msg_total: 0 messages received: 0 msg/s, 0.0 bytes/s, lag: 0.0 s (RESET)")

            msgtime = timestr2flt(message['pubtime'])
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
            if self.o.msg_total_interval > now - self.o.msg_total_last:
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

            if lag > self.o.msg_total_maxlag:
                logger.warn("total: Excessive lag! Messages posted %s " %
                            humanize.naturaltime(datetime.timedelta(seconds=lag)))
                #FIXME: should we reject here? worklist.rejected.append(message) ?

            self.o.msg_total_last = now

            if (self.o.msg_total_count > 0) and (self.o.msg_total_msgcount >=self.o.msg_total_count):
                os._exit(0)

        worklist.incoming = new_incoming



