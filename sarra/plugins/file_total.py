#!/usr/bin/python3

"""
  file_total
  
  give a running total of the messages going through an exchange.
  as this is an on_msg 

  accumulate the number of messages and the bytes they represent over a period of time.
  options:

  file_total_interval -- how often the total is updated. (default: 5)
  file_total_maxlag  -- if the message flow indicates that messages are 'late', emit warnings.
                    (default 60)

  dependency:
     requires python3-humanize module.

"""

import os,stat,time

class File_Total(object): 


    def __init__(self,parent):
        """
           set defaults for options.  can be overridden in config file.
        """
        logger = parent.logger

        # make parent know about these possible options

        parent.declare_option('file_total_interval')
        parent.declare_option('file_total_maxlag')

        if hasattr(parent,'file_total_maxlag'):
            if type(parent.file_total_maxlag) is list:
                parent.file_total_maxlag=int(parent.file_total_maxlag[0])
        else:
            parent.file_total_maxlag=60

        logger.debug("speedo init: 2 " )

        if hasattr(parent,'file_total_interval'):
            if type(parent.file_total_interval) is list:
                parent.file_total_interval=int(parent.file_total_interval[0])
        else:
            parent.file_total_interval=5

        now=time.time()

        parent.file_total_last = now
        parent.file_total_start = now
        parent.file_total_msgcount=0
        parent.file_total_bytecount=0
        parent.file_total_msgcount=0
        parent.file_total_bytecount=0
        parent.file_total_lag=0
        logger.debug("file_total: initialized, interval=%d, maxlag=%d" % \
            ( parent.file_total_interval, parent.file_total_maxlag ) )
          
    def perform(self,parent):
        logger = parent.logger
        msg    = parent.msg

        import calendar
        import humanize
        import datetime
        from sarra.sr_util import timestr2flt

        if ( parent.file_total_bytecount==0 ) :
            logger.info("file_total: 0 files received: 0 msg/s, 0.0 bytes/s, lag: 0.0 s (RESET)"  )

        msgtime=timestr2flt(msg.pubtime)
        now=time.time()

        parent.file_total_msgcount = parent.file_total_msgcount + 1

        lag=now-msgtime
        parent.file_total_lag = parent.file_total_lag + lag

        (method,psize,ptot,prem,pno) = msg.partstr.split(',')

        parent.file_total_bytecount = parent.file_total_bytecount + int(psize)
        
        #not time to report yet.
        if parent.file_total_interval > now-parent.file_total_last :
           return True

        logger.info("file_total: %3d files received: %5.2g msg/s, %s bytes/s, lag: %4.2g s" % ( 
            parent.file_total_msgcount,
	    parent.file_total_msgcount/(now-parent.file_total_start),
	    humanize.naturalsize(parent.file_total_bytecount/(now-parent.file_total_start),binary=True,gnu=True),
            parent.file_total_lag/parent.file_total_msgcount ))
        # Set the maximum age, in seconds, of a message to retrieve.

        if lag > parent.file_total_maxlag :
           logger.warn("total: Excessive lag! downloading too slowly/late %s behind" % 
               humanize.naturaltime(datetime.timedelta(seconds=lag)))

        parent.file_total_last = now

        return True

file_total = File_Total(self)

self.on_file = file_total.perform

