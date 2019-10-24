#!/usr/bin/python3
"""
  This is used inter-pump report routing.
  Select messages whose cluster is the same as the 'msg_by_cluster' setting.

  msg_from_cluster DDI
  msg_from_cluster DD

  on_message msg_from_cluster

  will select messages originating from the DD or DDI clusters.

"""

import os, stat, time


class Transformer(object):
    def __init__(self, parent):

        if not hasattr(parent, 'msg_from_cluster'):
            parent.logger.info("msg_from_cluster setting mandatory")
            return

        parent.logger.info("msg_from_cluster is %s " % parent.msg_from_cluster)

    def on_message(self, parent):
        return (parent.msg.headers['from_cluster'] in parent.msg_from_cluster)


transformer = Transformer(self)
self.on_message = transformer.on_message
