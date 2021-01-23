#!/usr/bin/python3
"""
  This plugin delays processing of messages by *message_delay* seconds


  msg_fdelay 30
  plugin msg_fdelay

  every message will be at least 30 seconds old before it is forwarded by this plugin.

"""
from sarracenia import timestr2flt, nowstr, nowflt


class Msg_FDelay(object):
    def __init__(self, parent):
        parent.declare_option('msg_fdelay')
        if hasattr(parent, 'msg_fdelay') and type(parent.msg_fdelay) is list:
            parent.msg_fdelay = int(parent.msg_fdelay[0])
        elif not hasattr(parent, 'msg_fdelay'):
            parent.msg_fdelay = 60

    def on_message(self, parent):
        import os
        import stat

        # Prepare msg delay test
        if parent.msg.sumflg == 'R':
            # 'R' msg will be removed by itself
            return False

        # Test msg delay
        elapsedtime = nowflt() - timestr2flt(parent.msg.headers['pubTime'])
        if elapsedtime < parent.msg_fdelay:
            dbg_msg = "message not old enough, sleeping for {:.3f} seconds"
            parent.logger.debug(
                dbg_msg.format(elapsedtime, parent.msg_fdelay - elapsedtime))
            parent.consumer.sleep_now = parent.consumer.sleep_min
            parent.consumer.msg_to_retry()
            parent.msg.isRetry = False
            return False

        # Prepare file delay test
        if '/cfr/' in parent.msg.new_dir:
            f = os.path.join(parent.msg.new_dir, parent.msg.new_file)
        else:
            f = parent.msg.relpath
        if not os.path.exists(f):
            parent.logger.error("did not find file {}".format(f))
            return False

        # Test file delay
        filetime = os.stat(f)[stat.ST_MTIME]
        elapsedtime = nowflt() - filetime
        if elapsedtime < parent.msg_fdelay:
            dbg_msg = "file not old enough, sleeping for {:.3f} seconds"
            parent.logger.debug(
                dbg_msg.format(elapsedtime, parent.msg_fdelay - elapsedtime))
            parent.consumer.sleep_now = parent.consumer.sleep_min
            parent.consumer.msg_to_retry()
            parent.msg.isRetry = False
            return False

        return True


self.plugin = 'Msg_FDelay'
