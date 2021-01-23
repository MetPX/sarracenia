#!/usr/bin/python3
"""
default on_heartbeat handler that gives messages info

"""
from sarracenia import nowflt


class Hb_Message(object):
    def __init__(self, parent):

        self.msg_count = 0
        self.msg_maxlag = -1

    def on_heartbeat(self, parent):
        logger = parent.logger

        if hasattr(parent, 'consumer'):
            self.msg_count = parent.consumer.msg_queue.declare()

        logger.info("hb_message queued=%d maxlag=%f" %
                    (self.msg_count, self.msg_maxlag))

        self.msg_maxlag = -1

        return True

    def on_message(self, parent):

        if hasattr(parent, 'msg'):
            now = nowflt()
            lag = now - parent.msg.tbegin
            if lag > self.msg_maxlag: self.msg_maxlag = lag

        return True


self.plugin = 'Hb_Message'
