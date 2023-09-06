"""
Plugin speedo.py:
    Gives a *speedometer* reading on the messages going through an exchange.
    as this is an after_accept
    Accumulate the number of messages and the bytes they represent over a period of time.

Options:
    msgSpeedoInterval -> how often the speedometer is updated. (default: 5)
    msg_speedo_maxlag  -> if the message flow indicates that messages are 'late', emit warnings. (default 60)

Usage: 
    callback accept.speedo
    msgSpeedoInterval x
    msg_speedo_maxlag y
"""


from sarracenia import timestr2flt, nowflt, naturalSize, naturalTime
import logging
from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)


class Speedo(FlowCB):
    def __init__(self, options):
        """
            set defaults for options.  can be overridden in config file.
        """
        super().__init__(options, logger)

        self.o.add_option('msg_speedo_maxlag', 'count', 60)
        #if hasattr(self.o, 'msg_speedo_maxlag'):
        #    if type(self.o.msg_speedo_maxlag) is list:
        #        self.o.msg_speedo_maxlag = int(self.o.msg_speedo_maxlag[0])
        #else:
        #    self.o.msg_speedo_maxlag = 60
        logger.debug("speedo init: 2 ")

        self.o.add_option('msgSpeedoInterval', 'count', 5)
        #if hasattr(self.o, 'msgSpeedoInterval'):
        #    if type(self.o.msgSpeedoInterval) is list:
        #        self.o.msgSpeedoInterval = int(self.o.msgSpeedoInterval[0])
        #else:
        #    self.o.msgSpeedoInterval = 5

        now = nowflt()
        self.msg_speedo_last = now
        self.msg_speedo_msgcount = 0
        self.msg_speedo_bytecount = 0

    def after_accept(self, worklist):
        for message in worklist.incoming:
            msgtime = timestr2flt(message['pubTime'])
            now = nowflt()
            self.msg_speedo_msgcount = self.msg_speedo_msgcount + 1

            (method, psize, ptot, prem, pno) = message['partstr'].split(',')

            self.msg_speedo_bytecount += int(psize)

            #not time to report yet.
            if self.o.msgSpeedoInterval > now - self.msg_speedo_last:
                continue

            lag = now - msgtime
            msgpersec = self.msg_speedo_msgcount / (now - self.msg_speedo_last)
            bytespersec = self.msg_speedo_bytecount / (now - self.msg_speedo_last)
            logger.info("speedo: %3d messages received: %5.4f msg/s, %4.2f bytes/s, lag: %4.0f s" % (self.msg_speedo_msgcount, msgpersec, bytespersec, lag))

            # If lag is higher than max allowed, emmit a warning
            if lag > self.o.msg_speedo_maxlag:
                logger.warning("speedo: Excessive lag! Messages posted %4.0f s ago" % lag)

            self.msg_speedo_last = now
            self.msg_speedo_msgcount = 0
            self.msg_speedo_bytecount = 0
