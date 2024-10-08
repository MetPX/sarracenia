

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

        super().__init__(options,logger)
        self.o.add_option('logEvents', 'set',
                          ['after_accept', 'on_housekeeping'])
        self.o.add_option('logMessageDump', 'flag', False)
        logger.debug(f'{self.o.component} initialized with: logEvents: {self.o.logEvents},  logMessageDump: {self.o.logMessageDump}')
        if self.o.component in ['sender']:
            self.action_verb = 'sent'
        elif self.o.component in ['subscribe', 'sarra' ]:
            self.action_verb = 'downloaded'
        elif self.o.component in ['post', 'poll', 'watch']:
            self.action_verb = 'noticed'
        elif self.o.component in [ 'flow', 'shovel', 'winnow']:
            self.action_verb = self.o.component + 'ed'
        else:
            self.action_verb = 'done'
        self.started = nowflt()
 
        self.rxTopicSeparator='.'
        if hasattr(options,'broker') and options.broker and options.broker.url.scheme.startswith('mqtt'):
            self.rxTopicSeparator='/'

        self.__reset()

    def __reset(self):
        self.last_housekeeping = nowflt()
        self.fileBytes = 0
        self.lagTotal = 0
        self.lagMax = 0
        self.msgCount = 0
        self.rejectCount = 0
        self.transferCount = 0

    def metricsReport(self):
        return { 'lagMax': self.lagMax, 'lagTotal':self.lagTotal, 'lagMessageCount':self.msgCount, 'rejectCount':self.rejectCount }

    def gather(self, messageCountMax):
        if set(['gather']) & self.o.logEvents:
            logger.info( f' messageCountMax: {messageCountMax} ')

        return (True, [])

    def _messageStr(self, msg):
        if self.o.logMessageDump:
            return msg.dumps()
        else:
            return msg.getIDStr()

    def _messageAcceptStr(self,msg):
        if self.o.logMessageDump:
            return msg.dumps()

        s = " "
        if 'exchange' in msg:
            s+= f"exchange: {msg['exchange']} "
        if 'subtopic' in msg:
            s+= f"subtopic: {self.rxTopicSeparator.join(msg['subtopic'])} "
        if 'fileOp' in msg:
            op=','.join(msg['fileOp'].keys())

            if op in ['link']:
                s+= f"a link to {msg['fileOp']['link']} with baseUrl: {msg['baseUrl']} "
            elif op in ['rename']:
                s+= f"a rename {msg['fileOp']['rename']} with baseUrl: {msg['baseUrl']} "
            else:
                s+= f"a {op} with baseUrl: {msg['baseUrl']} "
        else:
            s+= f"a file with baseUrl: {msg['baseUrl']} "
        if 'relPath' in msg:
            s+= f"relPath: {msg['relPath']} "
            if 'sundew_extension' in msg:
                s+=f"sundew_extension: {msg['sundew_extension']} "
        if 'retrievePath' in msg:
            s+= f"retrievePath: {msg['retrievePath']} "
        if 'rename' in msg:
            s+= f"rename: {msg['rename']} "
        if 'identity' in msg and 'value' in msg['identity']:
            s+=f"id: {msg['identity']['value'][0:7]} "
        if 'size' in msg:
            s+=f"size: {msg['size']} "
        return s
        
    def _messagePostStr(self,msg):
        if self.o.logMessageDump:
            return msg.dumps()

        s = "to "
        if 'post_exchange' in msg and ('post_topic' in msg) and \
            not msg['post_topic'].startswith(msg['post_exchange']) :
            s+= f"exchange: {msg['post_exchange']} " 
        if 'post_topic' in msg:
            s+= f"topic: {msg['post_topic']} "

        if 'fileOp' in msg:
            op=','.join(msg['fileOp'].keys())

            if op in ['link']:
                s+= f"a link to {msg['fileOp']['link']} "
            elif op in ['rename']:
                s+= f"a rename {msg['fileOp']['rename']} "
            else:
                s+= f"a {op} "
        else:
            s+= f"a file "

        if 'baseUrl' in msg:
            s+= f"with baseUrl: {msg['baseUrl']} "

        if 'relPath' in msg:
            s+= f"relPath: {msg['relPath']} "
        if 'retrievePath' in msg:
            s+= f"retrievePath: {msg['retrievePath']} "
        if 'rename' in msg:
            s+= f"rename: {msg['rename']} "
        if 'size' in msg:
            s+=f"size: {msg['size']} "
        if 'identity' in msg and 'value' in msg['identity']:
            s+=f"id: {msg['identity']['value'][0:7]} "

        return s

    def after_accept(self, worklist):

        self.rejectCount += len(worklist.rejected)
        self.msgCount += len(worklist.incoming)
        now = nowflt()

        if set(['reject']) & self.o.logEvents:
            for msg in worklist.rejected:
                if 'report' in msg:
                    logger.info(
                        "%s rejected: %d %s " %
                        (msg['relPath'], msg['report']['code'], msg['report']['message']))
                else:
                    logger.info("rejected: %s " % self._messageAcceptStr(msg))
        
        elif 'nodupe' in self.o.logEvents:
            for msg in worklist.rejected:
                if 'report' in msg and msg['report']['code'] in [ 304 ]:
                    logger.info(
                        "%s rejected: %d %s " %
                        (msg.getIDStr(), msg['report']['code'], msg['report']['message']))

        for msg in worklist.incoming:

            lag = now - timestr2flt(msg['pubTime'])
            self.lagTotal += lag
            if lag > self.lagMax:
                self.lagMax = lag
            if set(['after_accept']) & self.o.logEvents:
                logger.info( f"accepted: (lag: {lag:.2f} ) {self._messageAcceptStr(msg)}" )

    def after_post(self, worklist):
        if set(['after_post']) & self.o.logEvents:
            for msg in worklist.ok:
                logger.info("posted %s" % self._messagePostStr(msg))
            for msg in worklist.failed:
                logger.info("failed to post, queued to retry %s" % self._messagePostStr(msg))

    def after_work(self, worklist):
        self.rejectCount += len(worklist.rejected)
        self.transferCount += len(worklist.ok)
        if set(['reject']) & self.o.logEvents:
            for msg in worklist.rejected:
                if 'report' in msg:
                    logger.info(
                        "rejected: %d %s " %
                        (msg['report']['code'], msg['report']['message']))
                else:
                    logger.info("rejected: %s " % self._messageStr(msg))

        elif 'nodupe' in self.o.logEvents:
            for msg in worklist.rejected:
                if 'report' in msg and msg['report']['code'] in [ 304 ]:
                    logger.info(
                        "%s rejected: %d %s " %
                        (msg.getIDStr(), msg['report']['code'], msg['report']['message']))

        for msg in worklist.ok:
            if 'size' in msg:
                self.fileBytes += msg['size']
                
            if not self.o.download:
                continue

            if set(['after_work']) & self.o.logEvents:
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

                if ('new_dir' in msg) and ('new_file' in msg):
                    logger.info("%s ok: %s " %
                                (verb, msg['new_dir'] + '/' + msg['new_file']))
                elif 'relPath' in msg:
                    logger.info("%s ok: relPath: %s " % (verb, msg['relPath'] ))

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

    def on_cleanup(self):
        logger.info("hello")
    
    def on_declare(self):
        logger.info("hello")
    
    def on_stop(self):
        if set(['on_stop']) & self.o.logEvents:
            self.stats()
            logger.info("stopping")

    def on_start(self):
        if set(['on_start']) & self.o.logEvents:
            self.stats()
            logger.info("starting")

    def on_housekeeping(self):
        if set(['on_housekeeping']) & self.o.logEvents:
            self.stats()
            logger.debug("housekeeping")
        self.__reset()
