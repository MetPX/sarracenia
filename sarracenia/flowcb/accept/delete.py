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

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:
            f = "%s/%s" % (message['new_dir'], message['new_file'])
            try:
                os.unlink(f)
                os.unlink(f.replace('/cfr/', '/cfile/'))
                logger.info("deleted: %s and the cfile version." % f)
            except OSError as err:
                logger.error("could not unlink {}: {}".format(f, err))
                logger.debug("Exception details:", exc_info=True)
                self.o.consumer.sleep_now = self.o.consumer.sleep_min
                self.o.consumer.msg_to_retry()
                worklist.rejected.append(message)

            new_incoming.append(message)
        worklist.incoming = new_incoming
