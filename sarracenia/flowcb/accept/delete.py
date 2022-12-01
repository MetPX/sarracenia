"""
Plugin delete.py:
    the default after_accept handler for log.
    prints a simple notice. # FIXME is this doc accurate? seems it is also modifying a message.

Usage:
    flowcb sarracenia.flowcb.accept.downloadbaseurl.DownloadBaseUrl
"""

import logging
import os
from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)


class Delete(FlowCB):
    def __init__(self, options):
        self.o = options
        logger.debug("msg_delete initialized")

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:
            f = "%s/%s" % (message['new_dir'], message['new_file'])
            logger.info("msg_delete: %s" % f)
            try:
                os.unlink(f)
                os.unlink(f.replace('/cfr/', '/cfile/'))
            except OSError as err:
                logger.error("could not unlink {}: {}".format(f, err))
                logger.debug("Exception details:", exc_info=True)
                self.o.consumer.sleep_now = self.o.consumer.sleep_min
                self.o.consumer.msg_to_retry()
                worklist.rejected.append(message)

            new_incoming.append(message)
        worklist.incoming = new_incoming
