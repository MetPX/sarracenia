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


class ToCluster(object):
    def __init__(self, parent):

        if not hasattr(parent, 'msg_to_clusters'):
            parent.logger.info("msg_to_clusters setting mandatory")
            return

        parent.logger.info("msg_to_clusters valid destinations: %s " %
                           parent.msg_to_clusters)

    def on_message(self, parent):
        return (parent.msg.headers['to_clusters'] in parent.msg_to_clusters)


tocluster = ToCluster(self)
self.on_message = tocluster.on_message
