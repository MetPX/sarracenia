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

from sarracenia import timeflt2str, timestr2flt, nowflt


class Msg_Total(object):
    def __init__(self, parent):
        """
           set defaults for options.  can be overridden in config file.
        """
        logger = parent.logger

        # make parent know about these possible options

        parent.declare_option('msg_total_interval')
        parent.declare_option('msg_total_maxlag')
        parent.declare_option('msg_total_count')

        if hasattr(parent, 'msg_total_count'):
            if type(parent.msg_total_count) is list:
                parent.msg_total_count = int(parent.msg_total_count[0])
        else:
            parent.msg_total_count = 0

        if hasattr(parent, 'msg_total_maxlag'):
            if type(parent.msg_total_maxlag) is list:
                parent.msg_total_maxlag = int(parent.msg_total_maxlag[0])
        else:
            parent.msg_total_maxlag = 60

        if hasattr(parent, 'msg_total_interval'):
            if type(parent.msg_total_interval) is list:
                parent.msg_total_interval = int(parent.msg_total_interval[0])
        else:
            parent.msg_total_interval = 5

        now = nowflt()

        parent.msg_total_last = now
        parent.msg_total_start = now
        parent.msg_total_msgcount = 0
        parent.msg_total_bytecount = 0
        parent.msg_total_msgcount = 0
        parent.msg_total_bytecount = 0
        parent.msg_total_lag = 0
        logger.debug("msg_total: initialized, interval=%d, maxlag=%d" % \
            ( parent.msg_total_interval, parent.msg_total_maxlag ) )

    def on_message(self, parent):
        logger = parent.logger
        msg = parent.msg

        if msg.isRetry: return True

        import calendar
        import humanize
        import datetime
        import sys

        if (parent.msg_total_msgcount == 0):
            logger.info(
                "msg_total: 0 messages received: 0 msg/s, 0.0 bytes/s, lag: 0.0 s (RESET)"
            )

        msgtime = timestr2flt(msg.pubtime)
        now = nowflt()

        parent.msg_total_msgcount = parent.msg_total_msgcount + 1

        lag = now - msgtime
        parent.msg_total_lag = parent.msg_total_lag + lag

        # guess the size of the message payload, ignoring overheads.
        parent.msg_total_bytecount += (len(parent.msg.exchange) +
                                       len(parent.msg.topic) +
                                       len(parent.msg.notice) +
                                       len(parent.msg.hdrstr))

        #not time to report yet.
        if parent.msg_total_interval > now - parent.msg_total_last:
            return True

        logger.info(
            "msg_total: %3d messages received: %5.2g msg/s, %s bytes/s, lag: %4.2g s"
            %
            (parent.msg_total_msgcount, parent.msg_total_msgcount /
             (now - parent.msg_total_start),
             humanize.naturalsize(
                 parent.msg_total_bytecount / (now - parent.msg_total_start),
                 binary=True,
                 gnu=True), parent.msg_total_lag / parent.msg_total_msgcount))
        # Set the maximum age, in seconds, of a message to retrieve.

        if lag > parent.msg_total_maxlag:
            logger.warn("total: Excessive lag! Messages posted %s " %
                        humanize.naturaltime(datetime.timedelta(seconds=lag)))

        parent.msg_total_last = now

        if (parent.msg_total_count > 0) and (parent.msg_total_msgcount >=
                                             parent.msg_total_count):
            os._exit(0)

        return True


msg_total = Msg_Total(self)

self.on_message = msg_total.on_message
