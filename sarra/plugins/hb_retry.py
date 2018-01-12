#!/usr/bin/python3

class RETRY(object): 

   def __init__(self,parent):
       self.retry = None

   def on_start(self,parent):
       parent.logger.info("hb_retry on_start")

       if not hasattr(parent,'consumer'): return
       if not hasattr(parent.consumer, "retry" ): return

       self.retry = parent.consumer.retry
       self.retry.on_heartbeat(parent)

       return True

   def on_heartbeat(self,parent):
       parent.logger.info("hb_retry on_heartbeat")

       if self.retry : self.retry.on_heartbeat(parent)

       return True

self.plugin='RETRY'
