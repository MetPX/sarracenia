

import logging
from sarracenia import nowflt, timeflt2str, timestr2flt, __version__, naturalSize, naturalTime
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class Log(FlowCB):
    """
       The logging flow callback class.
       logs message at the indicated time. Controlled by:

       logEvents - which entry points to emit log messages at.

       logMessageDump - print literal messages when printing log messages.

       every housekeeping interval, prints:

       * how many messages were received, rejected, %accepted.
       * number of files transferred, their size, and rate in files/s and bytes/s
       * lag: some information about how old the messages are when processed 

    """
    def __init__(self, options):

        # FIXME: should a logging module have a logLevel setting?
        #        just put in a cookie cutter for now...
        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, options.logLevel.upper()))
        else:
            logger.setLevel(logging.INFO)
        logger.setLevel(logging.INFO)
        self.o = options
        self.o.add_option('logEvents', 'set',
                          ['after_accept', 'on_housekeeping'])
        self.o.add_option('logMessageDump', 'flag', False)
        logger.info(f'{self.o.component} initialized with: {self.o.logEvents}')
        if self.o.component in ['sender']:
            self.action_verb = 'sent'
        elif self.o.component in ['post', 'poll', 'watch']:
            self.action_verb = 'noticed'
        elif self.o.component in ['shovel']:
            self.action_verb = 'filtered'
        elif self.o.component in ['flow']:
            self.action_verb = 'flowed'
        else:
            self.action_verb = 'downloaded'
        self.started = nowflt()

        self.__reset()

    def __reset(self):
        self.last_housekeeping = nowflt()
        self.fileBytes = 0
        self.lagTotal = 0
        self.lagMax = 0
        self.msgCount = 0
        self.rejectCount = 0
        self.transferCount = 0

    def gather(self):
        if set(['gather', 'all']) & self.o.logEvents:
            logger.info('')

        return []

    def _messageStr(self, msg):
        if self.o.logMessageDump:
            return msg.dumps()
        else:
            return msg['baseUrl'] + ' ' + msg['relPath']

    def after_accept(self, worklist):

        self.rejectCount += len(worklist.rejected)
        self.msgCount += len(worklist.incoming)
        now = nowflt()

        if set(['reject', 'all']) & self.o.logEvents:
            for msg in worklist.rejected:
                if 'report' in msg:
                    logger.info(
                        "%s rejected: %d %s " %
                        (msg['relPath'], msg['report']['code'], msg['report']['message']))
                else:
                    logger.info("rejected: %s " % self._messageStr(msg))

        for msg in worklist.incoming:

            lag = now - timestr2flt(msg['pubTime'])
            self.lagTotal += lag
            if lag > self.lagMax:
                self.lagMax = lag
            if set(['after_accept', 'all']) & self.o.logEvents:

                logger.info("accepted: (lag: %.2f ) %s " %
                            (lag, self._messageStr(msg)))

    def after_post(self, worklist):
        if set(['after_post', 'all']) & self.o.logEvents:
            for msg in worklist.ok:
                logger.info("posted %s" % msg)
            for msg in worklist.failed:
                logger.info("failed to post, queued to retry %s" % msg)

    def after_work(self, worklist):
        self.rejectCount += len(worklist.rejected)
        self.transferCount += len(worklist.ok)
        if set(['reject', 'all']) & self.o.logEvents:
            for msg in worklist.rejected:
                if 'report' in msg:
                    logger.info(
                        "rejected: %d %s " %
                        (msg['report']['code'], msg['report']['message']))
                else:
                    logger.info("rejected: %s " % self._messageStr(msg))

        for msg in worklist.ok:
            if 'size' in msg:
                self.fileBytes += msg['size']

            if set(['after_work', 'all']) & self.o.logEvents:
                if 'fileOp' in msg :
                    if 'link' in msg['fileOp']:
                        verb = 'linked'
                    elif 'remove' in msg['fileOp']:
                        verb = 'removed'
                    elif 'rename' in msg['fileOp']:
                        verb = 'renamed'
                    else:
                        verb = ','.join(msg['fileOp'].keys())
                elif self.action_verb in ['downloaded'] and 'content' in msg:
                    verb = 'written from message'
                else:
                    verb = self.action_verb

                logger.info("%s ok: %s " %
                            (verb, msg['new_dir'] + '/' + msg['new_file']))
                if self.o.logMessageDump:
                    logger.info('message: %s' % msg.dumps())

    def stats(self):
        tot = self.msgCount + self.rejectCount
        how_long = nowflt() - self.last_housekeeping
        if tot > 0:
            apc = 100 * self.msgCount / tot
            rate = self.msgCount / how_long
        else:
            apc = 0
            rate = 0

        logger.info(
            f"version: {__version__}, started: {naturalTime(nowflt()-self.started)}, last_housekeeping: {how_long:4.1f} seconds ago "
        )
        logger.info(
            "messages received: %d, accepted: %d, rejected: %d   rate accepted: %3.1f%% or %3.1f m/s"
            % (self.msgCount + self.rejectCount, self.msgCount,
               self.rejectCount, apc, rate))
        logger.info( f"files transferred: {self.transferCount} " +\
             f"bytes: {naturalSize(self.fileBytes)} " +\
             f"rate: {naturalSize(self.fileBytes/how_long)}/sec" )
        if self.msgCount > 0:
            logger.info("lag: average: %.2f, maximum: %.2f " %
                        (self.lagTotal / self.msgCount, self.lagMax))

    def on_stop(self):
        if set(['on_stop', 'all']) & self.o.logEvents:
            self.stats()
            logger.info("stopping")

    def on_start(self):
        if set(['on_start', 'all']) & self.o.logEvents:
            self.stats()
            logger.info("starting")

    def on_housekeeping(self):
        if set(['on_housekeeping', 'all']) & self.o.logEvents:
            self.stats()
            logger.info("housekeeping")
        self.__reset()
