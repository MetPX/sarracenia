#!/usr/bin/python3

"""
  msg_total
  
  give a running total of the messages going through an exchange.
  as this is an on_msg 

  accumulate the number of messages and the bytes they represent over a period of time.
  options:

  msg_total_interval -- how often the total is updated. (default: 5)
  msg_total_maxlag  -- if the message flow indicates that messages are 'late', emit warnings.
                    (default 60)

  dependency:
     requires python3-humanize module.

"""

import os,stat,time

class Msg_Total(object): 


    def __init__(self,parent):
        """
           set defaults for options.  can be overridden in config file.
        """
        logger = parent.logger

        if hasattr(parent,'msg_total_maxlag'):
            if type(parent.msg_total_maxlag) is list:
                parent.msg_total_maxlag=int(parent.msg_total_maxlag[0])
        else:
            parent.msg_total_maxlag=60

        logger.debug("speedo init: 2 " )

        if hasattr(parent,'msg_total_interval'):
            if type(parent.msg_total_interval) is list:
                parent.msg_total_interval=int(parent.msg_total_interval[0])
        else:
            parent.msg_total_interval=5

        now=time.time()

        parent.msg_total_last = now
        parent.msg_total_start = now
        parent.msg_total_msgcount=0
        parent.msg_total_bytecount=0
        parent.msg_total_cum_msgcount=0
        parent.msg_total_cum_bytecount=0
        parent.msg_total_lag=0

          
    def perform(self,parent):
        logger = parent.logger
        msg    = parent.msg

        import calendar
        import humanize
        import datetime

        mt=msg.time
        msgtime=calendar.timegm(time.strptime(mt[:mt.find('.')],"%Y%m%d%H%M%S")) + float(mt[mt.find('.'):])
        now=time.time()

        parent.msg_total_msgcount = parent.msg_total_msgcount + 1
        parent.msg_total_cum_msgcount = parent.msg_total_cum_msgcount + 1

        lag=now-msgtime
        parent.msg_total_lag = parent.msg_total_lag + lag

        (method,psize,ptot,prem,pno) = msg.partstr.split(',')

        parent.msg_total_bytecount = parent.msg_total_bytecount + int(psize)
        parent.msg_total_cum_bytecount = parent.msg_total_cum_bytecount + int(psize)
        
        #not time to report yet.
        if parent.msg_total_interval > now-parent.msg_total_last :
           return True


        #logger.info("t now: %3d messages received: %5.2g msg/s, %s bytes/s, lag: %4.2g s" % ( 
        #    parent.msg_total_msgcount,
	#    parent.msg_total_msgcount/(now-parent.msg_total_last),
	#    humanize.naturalsize(parent.msg_total_bytecount/(now-parent.msg_total_last),binary=True,gnu=True),
        #    lag))
        logger.info("msg_total: %3d messages received: %5.2g msg/s, %s bytes/s, lag: %4.2g s" % ( 
            parent.msg_total_cum_msgcount,
	    parent.msg_total_cum_msgcount/(now-parent.msg_total_start),
	    humanize.naturalsize(parent.msg_total_cum_bytecount/(now-parent.msg_total_start),binary=True,gnu=True),
            parent.msg_total_lag/parent.msg_total_cum_msgcount ))
        # Set the maximum age, in seconds, of a message to retrieve.

        if lag > parent.msg_total_maxlag :
           logger.warn("total: Excessive lag! Messages posted %s " % 
               humanize.naturaltime(datetime.timedelta(seconds=lag)))

        parent.msg_total_last = now
        parent.msg_total_msgcount = 0
        parent.msg_total_bytecount = 0

        return True

total = Msg_Total(self)

self.on_message = total.perform

