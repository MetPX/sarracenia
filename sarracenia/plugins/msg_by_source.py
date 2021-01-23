#!/usr/bin/python3
"""
  Select messages whose source is the same as the 'msg_by_source' setting.

  msg_by_source Alice
  msg_by_source Bob

  on_message msg_by_source

  will result in all messages from from Alice & Bob being selected.

"""

import os, stat, time


class Transformer(object):
    def __init__(self, parent):

        parent.declare_option('msg_by_source')

        if not hasattr(parent, 'msg_by_source'):
            parent.logger.info("msg_by_source setting mandatory")
            return

        parent.logger.info("msg_by_source is %s " % parent.msg_by_source)

    def on_message(self, parent):
        return (parent.msg.headers['source'] in parent.msg_by_source)


transformer = Transformer(self)
self.on_message = transformer.on_message
