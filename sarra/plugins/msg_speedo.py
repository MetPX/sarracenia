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

import os,stat,time

class Msg_Speedo(object): 


    def __init__(self,parent):
        """
           set defaults for options.  can be overridden in config file.
        """
        logger = parent.logger

        if hasattr(parent,'msg_speedo_maxlag'):
            if type(parent.msg_speedo_maxlag) is list:
                parent.msg_speedo_maxlag=int(parent.msg_speedo_maxlag[0])
        else:
            parent.msg_speedo_maxlag=60

        logger.debug("speedo init: 2 " )

        if hasattr(parent,'msg_speedo_interval'):
            if type(parent.msg_speedo_interval) is list:
                parent.msg_speedo_interval=int(parent.msg_speedo_interval[0])
        else:
            parent.msg_speedo_interval=5

        now=time.time()

        parent.msg_speedo_last = now
        parent.msg_speedo_msgcount=0
        parent.msg_speedo_bytecount=0

          
    def perform(self,parent):
        logger = parent.logger
        msg    = parent.msg

        import calendar
        import humanize
        import datetime

        mt=msg.time
        msgtime=calendar.timegm(time.strptime(mt[:mt.find('.')],"%Y%m%d%H%M%S")) + float(mt[mt.find('.'):])
        now=time.time()

        parent.msg_speedo_msgcount = parent.msg_speedo_msgcount + 1

        (method,psize,ptot,prem,pno) = msg.partstr.split(',')

        parent.msg_speedo_bytecount = parent.msg_speedo_bytecount + int(psize)
        
        #not time to report yet.
        if parent.msg_speedo_interval > now-parent.msg_speedo_last :
           return True

        lag=now-msgtime

        logger.info("speedo: %3d messages received: %5.2g msg/s, %s bytes/s, lag: %4.2g s" % ( 
            parent.msg_speedo_msgcount,
	    parent.msg_speedo_msgcount/(now-parent.msg_speedo_last),
	    humanize.naturalsize(parent.msg_speedo_bytecount/(now-parent.msg_speedo_last),binary=True,gnu=True),
            lag))

        # Set the maximum age, in seconds, of a message to retrieve.

        if lag > parent.msg_speedo_maxlag :
           logger.warn("speedo: Excessive lag! Messages posted %s " % 
               humanize.naturaltime(datetime.timedelta(seconds=lag)))

        parent.msg_speedo_last = now
        parent.msg_speedo_msgcount = 0
        parent.msg_speedo_bytecount = 0

        return True

speedo = Msg_Speedo(self)

self.on_message = speedo.perform

