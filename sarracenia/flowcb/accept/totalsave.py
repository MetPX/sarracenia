#!/usr/bin/python3
"""
Plugin totalsave.py:
    give a running total of the messages going through an exchange as this is an after_accept plugin.
    
    Accumulate the number of messages and the bytes they represent over a period of time.
    options:
       -  msgTotalInterval -> how often the total is updated. (default: 5)
       -  msgTotalMaxlag  -> if the message flow indicates that messages are 'late', emit warnings. (default 60)

Dependency:
     requires python3-humanize module.

Usage:
    flowcb sarracenia.flowcb.accept.totalsave.TotalSave
"""

import os, stat, time
from sarracenia.flowcb import FlowCB
import calendar
import humanize
import datetime
import logger
from sarracenia import timestr2flt, timeflt2str, nowflt

logger = logging.getLogger(__name__)


class TotalSave(FlowCB):
    def __init__(self, options):
        """
           set defaults for options.  can be overridden in config file.
        """
        self.o = options

        # make self.o know about these possible options
        self.o.add_option('msgTotalInterval', 'str')
        self.o.add_option('msgTotalMaxlag', 'str')

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
        self.o.msg_total_lag = 0
        logger.debug("msg_total: initialized, interval=%d, maxlag=%d" % \
                     (self.o.msgTotalInterval, self.o.msgTotalMaxlag))

        self.o.msg_total_cache_file = self.o.user_cache_dir + os.sep
        self.o.msg_total_cache_file += 'msg_total_plugin_%.4d.vars' % self.o.instances

    def after_accept(self, worklist):
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

            # message with sum 'R' and 'L' have no partstr
            if 'partstr' in message.keys():
                (method, psize, ptot, prem, pno) = message['partstr'].split(',')
                self.o.msg_total_bytecount = self.o.msg_total_bytecount + int(psize)

            # not time to report yet.
            if self.o.msgTotalInterval > now - self.o.msg_total_last:
                new_incoming.append(message)
                continue

            logger.info("msg_total: %3d messages received: %5.2g msg/s, %s bytes/s, lag: %4.2g s" %
                        (self.o.msg_total_msgcount, self.o.msg_total_msgcount /
                         (now - self.o.msg_total_start),
                         humanize.naturalsize(
                             self.o.msg_total_bytecount / (now - self.o.msg_total_start),
                             binary=True,
                             gnu=True), self.o.msg_total_lag / self.o.msg_total_msgcount))
            # Set the maximum age, in seconds, of a message to retrieve.

            if lag > self.o.msgTotalMaxlag:
                logger.warning("total: Excessive lag! Messages posted %s " %
                               humanize.naturaltime(datetime.timedelta(seconds=lag)))

            self.o.msg_total_last = now
        worklist.incoming = new_incoming

    # TODO fix this on_start (not sure how to do for v3)
    # restoring accounting variables
    def on_start(self):

        self.o.msg_total_cache_file = self.o.user_cache_dir + os.sep
        self.o.msg_total_cache_file += 'msg_total_plugin_%.4d.vars' % self.o.instances

        if not os.path.isfile(self.o.msg_total_cache_file): return True

        fp = open(self.o.msg_total_cache_file, 'r')
        line = fp.read(8192)
        fp.close()

        line = line.strip('\n')
        words = line.split()
        if len(words) > 4:
            self.o.msg_total_last = float(words[0])
            self.o.msg_total_start = float(words[1])
            self.o.msg_total_msgcount = int(words[2])
            self.o.msg_total_bytecount = int(words[3])
            self.o.msg_total_lag = float(words[4])
        else:
            logger.error("missing cached variables in file: {}".format(self.o.post_total_cache_file))
            return False
        return True
    # TODO fix this on_stop (not sure how to do for v3)
    # saving accounting variables
    def on_stop(self):

        line = '%f ' % self.o.msg_total_last
        line += '%f ' % self.o.msg_total_start
        line += '%d ' % self.o.msg_total_msgcount
        line += '%d ' % self.o.msg_total_bytecount
        line += '%f\n' % self.o.msg_total_lag

        fp = open(self.o.msg_total_cache_file, 'w')
        fp.write(line)
        fp.close()
        return True


