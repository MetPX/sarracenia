import logging
import sarracenia.flowcb

logger = logging.getLogger(__name__)


class Sample(sarracenia.flowcb.FlowCB):
    def __init__(self, options):

        self.o = options

        # implement class specific logging priority.
        logger.setLevel(getattr(logging, self.o.logLevel.upper()))

        # declare a module specific setting.
        options.add_option('announce_list', 'list')

    def on_start(self):

        logger.info('announce_list: %s' % self.o.announce_list)
