import logging
from sarracenia import nowflt, timestr2flt
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)



class Log(FlowCB):
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
        logger.info( 'initialized with: %s' % self.o.logEvents )
        self.file_bytes=0
        self.lag_cumulative=0 
        self.lag_max=0 
        self.message_bytes=0
        self.message_count=0
        self.reject_count=0

    def gather(self):
        if set ( ['gather', 'all'] ) & self.o.logEvents:
            logger.info('')

        return []

    def after_accept(self, worklist):

        self.reject_count += len(worklist.rejected)
        self.message_count += len(worklist.incoming)
        now=nowflt()

        if set ( ['reject', 'all'] ) & self.o.logEvents:
            for msg in worklist.rejected:
                if 'report' in msg:
                    logger.info("rejected: %d %s " % ( msg['report']['code'], msg['report']['message'] ) )
                else:
                    logger.info("rejected: %s " % msg.dumps() )

        for msg in worklist.incoming:

            lag = now - timestr2flt(msg['pubTime'])
            self.lag_cumulative += lag
            if lag > self.lag_max:
               self.lag_max = lag
            self.message_bytes += len(msg)
            if 'size' in msg:
                self.file_bytes += msg['size']

            if set ( ['after_accept', 'all'] ) & self.o.logEvents:
                logger.info("accepted: (lag: %g ) %s " % ( lag, msg.dumps() ) )
                

    def after_work(self, worklist):
        if set ( ['reject', 'all'] ) & self.o.logEvents:
            for msg in worklist.rejected:
                if 'report' in msg:
                    logger.info("rejected: %d %s " % ( msg['report']['code'], msg['report']['message'] ) )
                else:
                    logger.info("rejected: %s " % msg.dumps() )

        if set ( ['after_work', 'all'] ) & self.o.logEvents:
            for msg in worklist.ok:
                logger.info("worked successfully: %s " % msg.dumps() )

    def _stats(self):
        logger.info( "messages_received: %d, accepted: %d, rejected: %d ( bytes: %s )" %
            ( self.message_count+self.reject_count, self.message_count, self.reject_count, self.message_bytes ) )
        logger.info( "files_accepted: cumulative bytes: %d" % self.file_bytes )  
        if self.message_count > 0:
            logger.info( "lag: average: %g, maximum: %g " % ( self.lag_cumulative/self.message_count, self.lag_max ) )

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
