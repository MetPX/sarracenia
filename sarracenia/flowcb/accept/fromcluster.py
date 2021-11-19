#!/usr/bin/python3
"""
  This is used inter-pump report routing.
  Select messages whose cluster is the same as the 'msg_by_cluster' setting.

  msg_from_cluster DDI
  msg_from_cluster DD

  on_message msg_from_cluster

  will select messages originating from the DD or DDI clusters.

"""

import logging
import os
import stat
import time
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class FromCluster(FlowCB):
    def __init__(self, options):
        self.o = options
        # FIXME would this ever be the case or is this a new name in V3? 'msg_from_cluster'
        if not hasattr(self.o, 'msg_from_cluster'):
            logger.info("msg_from_cluster setting mandatory")
            return

        logger.info("msg_from_cluster is %s " % self.o.msg_from_cluster)

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:
            if message['headers']['from_cluster'] in message['msg_from_cluster']:
                new_incoming.append(message)
            else:
                worklist.rejected.append(message)
        worklist.incoming = new_incoming

