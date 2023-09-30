"""
Plugin toclusters.py:
    Implements inter-pump routing by filtering destinations.
    This is placed on a sarra process copying data between pumps.
    Whenever it gets a message, it looks at the destination and processing
    only continues if it is beleived that that message is a valid destination for the local pump.

Options:
    The local pump will select messages destined for the DD or DDI clusters, and reject those for DDSR, which isn't in the list.
        - msgToClusters DDI
        - msgToClusters DD
Usage:
    flowcb sarracenia.flowcb.accept.toclusters.ToClusters
    msgToClusters x
    msgToClusters y
    ...
"""

import os, stat, time
import logging
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class ToClusters(FlowCB):
    def __init__(self, options):
        super().__init__(options,logger)

        self.o.add_option('msgToClusters', 'list')

        if self.o.msgToClusters == None:
            logger.info("msgToClusters setting mandatory")
            return

        logger.info("msgToClusters valid destinations: %s " % self.o.msgToClusters)

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:
            if message['to_clusters'] in self.o.msgToClusters:
                new_incoming.append(message)
            else:
                worklist.rejected.append(message)
        worklist.incoming = new_incoming
