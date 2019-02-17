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

        # make parent know about these possible options

        parent.declare_option('msg_total_interval')
        parent.declare_option('msg_total_maxlag')

        if hasattr(parent,'msg_total_maxlag'):
            if type(parent.msg_total_maxlag) is list:
                parent.msg_total_maxlag=int(parent.msg_total_maxlag[0])
        else:
            parent.msg_total_maxlag=60

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
        parent.msg_total_lag=0
        logger.debug("msg_total: initialized, interval=%d, maxlag=%d" % \
            ( parent.msg_total_interval, parent.msg_total_maxlag ) )

        parent.msg_total_cache_file  = parent.user_cache_dir + os.sep
        parent.msg_total_cache_file += 'msg_total_plugin_%.4d.vars' % parent.instance

    def on_message(self,parent):


        logger = parent.logger
        msg    = parent.msg

        if msg.isRetry : return True

        import calendar
        import humanize
        import datetime
        from sarra.sr_util import timestr2flt

        if (parent.msg_total_msgcount == 0): 
            logger.info("msg_total: 0 messages received: 0 msg/s, 0.0 bytes/s, lag: 0.0 s (RESET)"  )

        msgtime=timestr2flt(msg.pubtime)
        now=time.time()

        parent.msg_total_msgcount = parent.msg_total_msgcount + 1

        lag=now-msgtime
        parent.msg_total_lag = parent.msg_total_lag + lag

        # message with sum 'R' and 'L' have no partstr
        if parent.msg.partstr :
          (method,psize,ptot,prem,pno) = msg.partstr.split(',')
          parent.msg_total_bytecount   = parent.msg_total_bytecount + int(psize)
        
        #not time to report yet.
        if parent.msg_total_interval > now-parent.msg_total_last :
           return True

        logger.info("msg_total: %3d messages received: %5.2g msg/s, %s bytes/s, lag: %4.2g s" % ( 
            parent.msg_total_msgcount,
	    parent.msg_total_msgcount/(now-parent.msg_total_start),
	    humanize.naturalsize(parent.msg_total_bytecount/(now-parent.msg_total_start),binary=True,gnu=True),
            parent.msg_total_lag/parent.msg_total_msgcount ))
        # Set the maximum age, in seconds, of a message to retrieve.

        if lag > parent.msg_total_maxlag :
           logger.warn("total: Excessive lag! Messages posted %s " % 
               humanize.naturaltime(datetime.timedelta(seconds=lag)))

        parent.msg_total_last = now

        return True

    # restoring accounting variables
    def on_start(self,parent):

        parent.msg_total_cache_file  = parent.user_cache_dir + os.sep
        parent.msg_total_cache_file += 'msg_total_plugin_%.4d.vars' % parent.instance

        if not os.path.isfile(parent.msg_total_cache_file) : return True

        fp=open(parent.msg_total_cache_file,'r')
        line = fp.read(8192)
        fp.close()

        line  = line.strip('\n')
        words = line.split()

        parent.msg_total_last      = float(words[0])
        parent.msg_total_start     = float(words[1])
        parent.msg_total_msgcount  = int  (words[2])
        parent.msg_total_bytecount = int  (words[3])
        parent.msg_total_lag       = float(words[4])

        return True

    # saving accounting variables
    def on_stop(self,parent):

        line  = '%f ' % parent.msg_total_last
        line += '%f ' % parent.msg_total_start
        line += '%d ' % parent.msg_total_msgcount
        line += '%d ' % parent.msg_total_bytecount
        line += '%f\n'% parent.msg_total_lag

        fp=open(parent.msg_total_cache_file,'w')
        fp.write(line)
        fp.close()

        return True

self.plugin='Msg_Total'
