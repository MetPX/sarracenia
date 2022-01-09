import logging
from sarracenia import nowflt, timestr2flt
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class Log(FlowCB):
    """
       The logging flow callback class.
       logs message at the indicated time. Controlled by:

       logEvents - which entry points to emit log messages at.

       logMessageDump - print literal messages when printing log messages.
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
        self.o.add_option( 'logEvents', 'set', [ 'after_accept', 'on_housekeeping' ] )
        self.o.add_option( 'logMessageDump', 'flag', False )
        logger.info( 'initialized with: %s' % self.o.logEvents )
        self.__reset()

    def __reset(self):
        self.fileBytes=0
        self.lagTotal=0 
        self.lagMax=0 
        self.msgBytes=0
        self.msgCount=0
        self.rejectCount=0
        self.transferCount=0

    def gather(self):
        if set ( ['gather', 'all'] ) & self.o.logEvents:
            logger.info('')

        return []

    def _messageStr(self,msg):
        if self.o.logMessageDump:
            return msg.dumps()
        else:
            return msg['baseUrl'] + ' ' + msg['relPath' ] 


    def after_accept(self, worklist):

        self.rejectCount += len(worklist.rejected)
        self.msgCount += len(worklist.incoming)
        now=nowflt()

        if set ( ['reject', 'all'] ) & self.o.logEvents:
            for msg in worklist.rejected:
                if 'report' in msg:
                    logger.info("rejected: %d %s " % ( msg['report']['code'], msg['report']['message'] ) )
                else:
                    logger.info("rejected: %s " % self._messageStr(msg)  )

        for msg in worklist.incoming:

            lag = now - timestr2flt(msg['pubTime'])
            self.lagTotal += lag
            if lag > self.lagMax:
               self.lagMax = lag
            self.msgBytes += len(msg)
            if set ( ['after_accept', 'all'] ) & self.o.logEvents:

                logger.info("accepted: (lag: %g ) %s " % ( lag, self._messageStr(msg) ) )
                

    def after_work(self, worklist):
        self.rejectCount += len(worklist.rejected)
        self.transferCount += len(worklist.ok)
        if set ( ['reject', 'all'] ) & self.o.logEvents:
            for msg in worklist.rejected:
                if 'report' in msg:
                    logger.info("rejected: %d %s " % ( msg['report']['code'], msg['report']['message'] ) )
                else:
                    logger.info("rejected: %s " % self._messageStr(msg) )

        for msg in worklist.ok:
            if 'size' in msg:
                self.fileBytes += msg['size']

            if set ( ['after_work', 'all'] ) & self.o.logEvents:
                if msg['integrity']['method'] in [ 'link', 'remove' ]:
                     verb=msg['integrity']['method'] 
                else:
                     verb='transfer'

                logger.info("%s ok: %s " % ( verb, msg['new_dir'] + '/' + msg['new_file'] ) )
                if self.o.logMessageDump:
                     logger.info('message: %s' % msg.dumps() )

    def _stats(self):
        logger.info( "messages_received: %d, accepted: %d, rejected: %d ( bytes: %s )" %
            ( self.msgCount+self.rejectCount, self.msgCount, self.rejectCount, self.msgBytes ) )
        logger.info( "files transferred: %d, cumulative bytes of data: %d" % ( self.transferCount, self.fileBytes )  )
        if self.msgCount > 0:
            logger.info( "lag: average: %g, maximum: %g " % ( self.lagTotal/self.msgCount, self.lagMax ) )
        self.__reset()

    def on_stop(self):
        if set ( ['on_stop', 'all'] ) & self.o.logEvents:
            self._stats()
            logger.info("stopping")

    def on_start(self):
        if set ( ['on_start', 'all'] ) & self.o.logEvents:
            self._stats()
            logger.info("starting")

    def on_housekeeping(self):
        if set ( ['on_housekeeping', 'all'] ) & self.o.logEvents:
            self._stats()
            logger.info("housekeeping")

    def post(self, worklist):
        if set ( ['post', 'all'] ) & self.o.logEvents:
            for msg in worklist.ok:
                logger.info("posted %s" % msg )
