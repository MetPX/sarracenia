#!/usr/bin/python3
"""
Plugin posttotalsave.py:
    Gives a running total of the messages going through an exchange as this is an after_accept plugin.
    Accumulate the number of messages and the bytes they represent over a period of time.

Options:
    postTotalInterval -- how often the total is updated. (default: 5)
    postTotalMaxlag  -- if the message flow indicates that messages are 'late', emit warnings.(default 60)

Usage:
    flowcb sarracenia.flowcb.accept.posttotalsave.PostTotalSave
    postTotalInterval x
    postTotalMaxlag y



"""
import calendar
import datetime
import humanize
import logging
import os, stat, time
from sarracenia import timestr2flt, nowfltlt
from sarracenia.flowcb import FlowCB

logger = logging.getLogger('__name__')

class PostTotalSave(FlowCB):
    def __init__(self, options):
        """
           set defaults for options.  can be overridden in config file.
        """
        self.o = options

        # make parent know about these possible options #FIXME should these really be str?
        self.o.add_option('postTotalInterval', 'str')
        self.o.add_option('post_total_maxlag', 'str')

        if hasattr(self.o, 'post_total_maxlag'):
            if type(self.o.post_total_maxlag) is list:
                self.o.post_total_maxlag = int(self.o.post_total_maxlag[0])
        else:
            self.o.post_total_maxlag = 60

        logger.debug("speedo init: 2 ")

        if hasattr(self.o, 'postTotalInterval'):
            if type(self.o.postTotalInterval) is list:
                self.o.postTotalInterval = int(self.o.postTotalInterval[0])
        else:
            self.o.postTotalInterval = 5

        now = nowflt()

        self.o.post_total_last = now
        self.o.post_total_start = now
        self.o.post_total_msgcount = 0
        self.o.post_total_bytecount = 0
        self.o.post_total_lag = 0
        logger.debug( "post_total: initialized, interval=%d, maxlag=%d" % \
             ( self.o.postTotalInterval, self.o.post_total_maxlag ) )

        self.o.post_total_cache_file = self.o.user_cache_dir + os.sep
        self.o.post_total_cache_file += 'post_total_plugin_%.4d.vars' % self.o.instances

    def after_accept(self, worklist):
        for message in worlist.incoming:
            if self.o.post_total_msgcount == 0:
                logger.info("post_total: 0 messages posted: 0 msg/s, 0.0 bytes/s, lag: 0.0 s (RESET)")

            msgtime = timestr2flt(message['pubTime'])
            now = nowflt()

            self.o.post_total_msgcount = self.o.post_total_msgcount + 1

            lag = now - msgtime
            self.o.post_total_lag = self.o.post_total_lag + lag

            #(method,psize,ptot,prem,pno) = message['partstr'].split(',')
            #self.o.post_total_bytecount = self.o.post_total_bytecount + int(psize)

            #not time to report yet.
            if self.o.postTotalInterval > now - self.o.post_total_last:
                continue

            logger.info("post_total: %3d messages posted: %5.2g msg/s, lag: %4.2g s" %
                (self.o.post_total_msgcount, self.o.post_total_msgcount (now - self.o.post_total_start),
                 self.o.post_total_lag / self.o.post_total_msgcount))
            # Set the maximum age, in seconds, of a message to retrieve.

            if lag > self.o.post_total_maxlag:
                logger.warn("total: Excessive lag! Messages posted %s " %
                            humanize.naturaltime(datetime.timedelta(seconds=lag)))

            self.o.post_total_last = now


    # restoring accounting variables
    def on_start(self):

        self.o.post_total_cache_file = self.o.user_cache_dir + os.sep
        self.o.post_total_cache_file += 'post_total_plugin_%.4d.vars' % self.o.instances

        if not os.path.isfile(self.o.post_total_cache_file): return True

        fp = open(self.o.post_total_cache_file, 'r')
        line = fp.read(8192)
        fp.close()

        line = line.strip('\n')
        words = line.split()

        if len(words) > 4:
            self.o.post_total_last = float(words[0])
            self.o.post_total_start = float(words[1])
            self.o.post_total_msgcount = int(words[2])
            self.o.post_total_bytecount = int(words[3])
            self.o.post_total_lag = float(words[4])
        else:
            self.o.logger.error("missing cached variables in file: {}".format(self.o.post_total_cache_file))
            return False
        return True

    # saving accounting variables
    def on_stop(self, parent):

        line = '%f ' % self.o.post_total_last
        line += '%f ' % self.o.post_total_start
        line += '%d ' % self.o.post_total_msgcount
        line += '%d ' % self.o.post_total_bytecount
        line += '%f\n' % self.o.post_total_lag

        fp = open(self.o.post_total_cache_file, 'w')
        fp.write(line)
        fp.close()

        return True

