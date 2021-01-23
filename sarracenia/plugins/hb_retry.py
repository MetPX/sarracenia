#!/usr/bin/python3


class RETRY(object):
    def __init__(self, parent):
        pass

    def on_heartbeat(self, parent):
        parent.logger.info("hb_retry on_heartbeat")

        if not parent.retry_mode: return True

        if not hasattr(parent, 'consumer'): return True

        parent.consumer.retry.on_heartbeat(parent)

        return True


self.plugin = 'RETRY'
