#!/usr/bin/python3
"""
  Implements inter-pump routing by filtering destinations.  

  this is placed on a sr_sarra process copying data between pumps.  Whenever it gets a message, it looks at the destination
  and processing only continues if it is beleived that that message is a valid destination for the local pump.

  sample settings:

  msg_to_clusters DDI
  msg_to_clusters DD

  on_message msg_to_clusters

  The local pump will select messages destined for the DD or DDI clusters, and reject those for DDSR, which isn't in the list.


"""

import os, stat, time
import logging
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class ToCluster(FlowCB):
    def __init__(self, options):
        self.o = options
        if not hasattr(self.o, 'msg_to_clusters'):
            logger.info("msg_to_clusters setting mandatory")
            return

        logger.info("msg_to_clusters valid destinations: %s " % self.o.msg_to_clusters)

    def on_message(self):
        return (self.o.msg['headers']['to_clusters'] in self.o.msg_to_clusters)

