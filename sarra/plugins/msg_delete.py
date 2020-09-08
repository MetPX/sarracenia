#!/usr/bin/python3
"""
  the default on_msg handler for sr_log.
  prints a simple notice.

"""


class Msg_Delete(object):
    def __init__(self, parent):
        parent.logger.debug("msg_delete initialized")

    def on_message(self, parent):
        import os

        msg = parent.msg

        f = "%s/%s" % (msg.new_dir, msg.new_file)
        parent.logger.info("msg_delete: %s" % f)
        try:
            os.unlink(f)
            os.unlink(f.replace('/cfr/', '/cfile/'))
        except OSError as err:
            parent.logger.error("could not unlink {}: {}".format(f, err))
            parent.logger.debug("Exception details:", exc_info=True)
            parent.consumer.sleep_now = parent.consumer.sleep_min
            parent.consumer.msg_to_retry()
            parent.msg.isRetry = False
            return False

        return True


msg_delete = Msg_Delete(self)

self.on_message = msg_delete.on_message
