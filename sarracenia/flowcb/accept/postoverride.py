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
import sys, os, os.path, time, stat
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class PostOverride(FlowCB):
    def __init__(self, options):
        self.o = options

        self.o.add_option('postOverride', 'str')
        self.o.add_option('postOverrideDel', 'str')
        if hasattr(self.o, 'postOverride'):
            logger.info('postOverride settings: %s' % self.o.postOverride)

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:

            if hasattr(self.o, 'postOverride'):
                for o in self.o.postOverride:
                    (osetting, ovalue) = o.split()
                    logger.debug('postOverride applying: header:%s value:%s' %
                                 (osetting, ovalue))
                    message['headers'][osetting] = ovalue
                    new_incoming.append(message)

            if hasattr(self.o, 'postOverrideDel'):
                for od in self.o.postOverrideDel:
                    if od in message['headers']:
                        logger.debug('postOverride deleting: header:%s ' % od)
                        del message['headers'][od]
                        new_incoming.append(message)
        worklist.incoming = new_incoming
