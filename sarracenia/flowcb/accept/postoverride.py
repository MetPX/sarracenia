"""
Plugin postoverride.py:
    Override message header for products that are posted. This can be useful or necessary 
    when re-distributing beyond the original intended destinations.

Example:
    for example company A delivers to their own DMZ server. ACME is a client of them,
    and so subscribes to the ADMZ server, but the to_cluster=ADMZ, when ACME downloads, they
    need to override the destination to specify the distribution within ACME.
    * postOverride to_clusters ACME
    * postOverrideDel from_cluster

Usage: 
    flowcb sarracenia.flowcb.accept.postoverride.PostOverride
    postOverride x y
    postOverrideDel z

"""

import logging
import copy
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class PostOverride(FlowCB):
    def __init__(self, options):
        super().__init__(options,logger)
        self.o.add_option('postOverride', 'list')
        self.o.add_option('postOverrideDel', 'list')
        if hasattr(self.o, 'postOverride'):
            logger.info('postOverride settings: %s' % self.o.postOverride)

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:

            if hasattr(self.o, 'postOverride') and self.o.postOverride != [None]:
                for o in self.o.postOverride:
                    (osetting, ovalue) = o.split()
                    logger.debug('postOverride applying: header:%s value:%s' % (osetting, ovalue))
                    message['headers'][osetting] = ovalue
                    new_incoming.append(copy.deepcopy(message))

            if hasattr(self.o, 'postOverrideDel'):
                for od in self.o.postOverrideDel:
                    if od in message['headers']:
                        logger.debug('postOverride deleting: header:%s ' % od)
                        del message['headers'][od]
                        new_incoming.append(copy.deepcopy(message))
        worklist.incoming = new_incoming
