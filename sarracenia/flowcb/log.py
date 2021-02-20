from sarracenia.flowcb import FlowCB
import logging

logger = logging.getLogger(__name__)


class Log(FlowCB):
    def __init__(self, options):

        # FIXME: should a logging module have a logLevel setting?
        #        just put in a cookie cutter for now...
        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, options.logLevel.upper()))
        else:
            logger.setLevel(logging.INFO)

    def on_filter(self, worklist):
        for msg in worklist.incoming:
            logger.info("accepted: %s " % msg)

    def on_work(self, worklist):
        for msg in worklist.ok:
            logger.info("worked successfully: %s " % msg)


