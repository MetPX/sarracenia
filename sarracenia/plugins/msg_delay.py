#!/usr/bin/python3
"""
  This plugin delays processing of messages by *message_delay* seconds


  msg_delay 30
  on_message msg_delay

  every message will be at least 30 seconds old before it is forwarded by this plugin.

"""
from sarracenia import timestr2flt, nowflt, nowstr


class Msg_Delay(object):
    def __init__(self, parent):
        parent.logger.debug("msg_log initialized")
        parent.declare_option('msg_delay')
        if hasattr(parent, 'msg_delay') and type(parent.msg_delay) is list:
            parent.msg_delay = int(parent.msg_delay[0])
        elif not hasattr(parent, 'msg_delay'):
            parent.msg_delay = 300

    def on_message(self, parent):
        if not 'delay' in parent.msg.headers:
            parent.msg.headers['delay'] = nowstr()

        # Test msg delay
        elapsedtime = nowflt() - timestr2flt(parent.msg.headers['pubTime'])
        if 0 < elapsedtime < 1:
            parent.logger.debug("msg_delay received msg")
        else:
            parent.logger.info(
                "trying msg with {:.3f}s elapsed".format(elapsedtime))
        if elapsedtime < parent.msg_delay:
            dbg_msg = "message not old enough, sleeping for {:.3f} seconds"
            parent.logger.debug(
                dbg_msg.format(elapsedtime, parent.msg_delay - elapsedtime))
            parent.consumer.sleep_now = parent.consumer.sleep_min
            parent.consumer.msg_to_retry()
            parent.msg.isRetry = False
            return False

        return True


self.plugin = 'Msg_Delay'
