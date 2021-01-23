#!/usr/bin/python3
"""
  post_total
  
  give a running total of the messages going through an exchange.
  as this is an on_msg 

  accumulate the number of messages and the bytes they represent over a period of time.
  options:

  post_total_interval -- how often the total is updated. (default: 5)
  post_total_maxlag  -- if the message flow indicates that messages are 'late', emit warnings.
                    (default 60)

  dependency:
     requires python3-humanize module.

"""

import os, stat, time

from sarracenia import nowflt


class Post_Total(object):
    def __init__(self, parent):
        """
           set defaults for options.  can be overridden in config file.
        """
        logger = parent.logger

        # make parent know about these possible options

        parent.declare_option('post_total_interval')
        parent.declare_option('post_total_maxlag')

        if hasattr(parent, 'post_total_maxlag'):
            if type(parent.post_total_maxlag) is list:
                parent.post_total_maxlag = int(parent.post_total_maxlag[0])
        else:
            parent.post_total_maxlag = 60

        logger.debug("speedo init: 2 ")

        if hasattr(parent, 'post_total_interval'):
            if type(parent.post_total_interval) is list:
                parent.post_total_interval = int(parent.post_total_interval[0])
        else:
            parent.post_total_interval = 5

        now = nowflt()

        parent.post_total_last = now
        parent.post_total_start = now
        parent.post_total_msgcount = 0
        parent.post_total_bytecount = 0
        parent.post_total_msgcount = 0
        parent.post_total_bytecount = 0
        parent.post_total_lag = 0
        logger.debug( "post_total: initialized, interval=%d, maxlag=%d" % \
             ( parent.post_total_interval, parent.post_total_maxlag ) )

    def perform(self, parent):
        logger = parent.logger
        msg = parent.msg

        import calendar
        import humanize
        import datetime
        from sarracenia import timestr2flt

        if parent.post_total_msgcount == 0:
            logger.info(
                "post_total: 0 messages posted: 0 msg/s, 0.0 bytes/s, lag: 0.0 s (RESET)"
            )

        msgtime = timestr2flt(msg.pubtime)
        now = nowflt()

        parent.post_total_msgcount = parent.post_total_msgcount + 1

        lag = now - msgtime
        parent.post_total_lag = parent.post_total_lag + lag

        #(method,psize,ptot,prem,pno) = msg.partstr.split(',')
        #parent.post_total_bytecount = parent.post_total_bytecount + int(psize)

        #not time to report yet.
        if parent.post_total_interval > now - parent.post_total_last:
            return True

        logger.info(
            "post_total: %3d messages posted: %5.2g msg/s, lag: %4.2g s" %
            (parent.post_total_msgcount, parent.post_total_msgcount /
             (now - parent.post_total_start),
             parent.post_total_lag / parent.post_total_msgcount))
        # Set the maximum age, in seconds, of a message to retrieve.

        if lag > parent.post_total_maxlag:
            logger.warn("total: Excessive lag! Messages posted %s " %
                        humanize.naturaltime(datetime.timedelta(seconds=lag)))

        parent.post_total_last = now

        return True


post_total = Post_Total(self)

self.on_post = post_total.perform
