#!/usr/bin/python3
"""
   Override message header for products that are posted.

   This can be useful or necessary when re-distributing beyond the original intended
   destinations.
   
  for example company A delivers to their own DMZ server.  ACME is a client of them,
  and so subscribes to the ADMZ server, but the to_cluster=ADMZ, when ACME downloads, they
  need to override the destination to specify the distribution within ACME.

  sample use:

  post_override to_clusters ACME
  post_override_del from_cluster

  on_post post_override


"""

import logging
import sys, os, os.path, time, stat
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class PostOverride(FlowCB):
    def __init__(self, options):
        self.o = options

        self.o.add_option('post_override', 'str')
        self.o.add_option('post_override_del', 'str')
        if hasattr(self.o, 'post_override'):
            logger.info('post_override settings: %s' % self.o.post_override)

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:

            if hasattr(self.o, 'post_override'):
                for o in self.o.post_override:
                    (osetting, ovalue) = o.split()
                    logger.debug('post_override applying: header:%s value:%s' %  ( osetting, ovalue ) )
                    message['headers'][osetting] = ovalue
                    new_incoming.append(message)


            if hasattr(self.o, 'post_override_del'):
                for od in self.o.post_override_del:
                    if od in message['headers']:
                        logger.debug('post_override deleting: header:%s ' % od)
                        del message['headers'][od]
                        new_incoming.append(message)
        worklist.incoming  = new_incoming

