import logging
from sarracenia.flowcb import FlowCB
from sarracenia import msg_dumps

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
        self.o.add_option( 'log_events', 'set', [ 'after_accept' ] )
        logger.info( 'initialized with: %s' % self.o.log_events )

    def gather(self):
        if set ( ['gather', 'all'] ) & self.o.log_events:
            logger.info('')

        return []

    def after_accept(self, worklist):

        if set ( ['reject', 'all'] ) & self.o.log_events:
            for msg in worklist.rejected:
                if 'report' in msg:
                    logger.info("rejected: %d %s " % ( msg['report']['code'], msg['report']['message'] ) )
                else:
                    logger.info("rejected: %s " % msg_dumps(msg) )

        if set ( ['after_accept', 'all'] ) & self.o.log_events:
            for msg in worklist.incoming:
                logger.info("accepted: %s " % msg_dumps(msg) )

    def after_work(self, worklist):
        if set ( ['reject', 'all'] ) & self.o.log_events:
            for msg in worklist.rejected:
                if 'report' in msg:
                    logger.info("rejected: %d %s " % ( msg['report']['code'], msg['report']['message'] ) )
                else:
                    logger.info("rejected: %s " % msg_dumps(msg) )

        if set ( ['after_work', 'all'] ) & self.o.log_events:
            for msg in worklist.ok:
                logger.info("worked successfully: %s " % msg_dumps(msg) )


    def on_stop(self):
        if set ( ['on_stop', 'all'] ) & self.o.log_events:
            logger.info("stopping")

    def on_start(self):
        if set ( ['on_start', 'all'] ) & self.o.log_events:
            logger.info("starting")

    def on_housekeeping(self):
        if set ( ['on_housekeeping', 'all'] ) & self.o.log_events:
            logger.info("housekeeping")

    def post(self, worklist):
        if set ( ['post', 'all'] ) & self.o.log_events:
            for msg in worklist.ok:
                logger.info("posting %s" % msg )
