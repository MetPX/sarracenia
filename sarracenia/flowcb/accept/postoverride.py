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

        if self.o.postOverride != None:
            logger.info('postOverride settings: %s' % self.o.postOverride)
        if self.o.postOverrideDel != None:
            logger.info('postOverrideDel settings: %s' % self.o.postOverrideDel)

    def after_accept(self, worklist):
        for message in worklist.incoming:
            
            if self.o.postOverride != None:
                for o in self.o.postOverride:
                    (osetting, ovalue) = o.split()
                    logger.debug('postOverride applying key:%s value:%s' % (osetting, ovalue))
                    message[osetting] = ovalue

            if self.o.postOverrideDel != None:
                for od in self.o.postOverrideDel:
                    if od in message:
                        logger.debug('postOverride deleting key:%s ' % od)
                        del message[od]
