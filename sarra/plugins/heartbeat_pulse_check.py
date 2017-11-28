#!/usr/bin/python3

"""
  default on_heartbeat pulse processing...
  if pulse is emitted for a while, and than missing
  we will issue a reconnection.

  caveat 1 : once pulsing has started... it must continue
             if poll_pulse stops the process will trigger a reconnection
             every heartbeat

  caveat 2 : receiving pulse messages will not behave as expected for
             process with N instances because we cannot guaranty that each
             one of them receives its own pulse...
"""

class Heartbeat_Pulse(object): 

    def __init__(self,parent):
        self.last_time          = time.time()
        self.last_message_count = parent.message_count
        self.last_publish_count = parent.publish_count
        self.last_pulse_count   = parent.pulse_count
          
    def perform(self,parent):
        self.logger     = parent.logger
        self.logger.debug("heartbeat_pulse_check")

        # something wrong when consuming ?

        if hasattr(parent,'consumer') :
           if parent.message_count <= self.last_message_count:
              if parent.pulse_count <=  self.last_pulse_count:
                 if parent.consumer.isAlive() :
                    self.logger.info("received neither message nor pulse, but confirmed broker connection remains alive")
                 else:
                    self.logger.warning("connection problem...reconnecting")
                    parent.close()
                    parent.connect()

           # keep these counts
           self.last_message_count = parent.message_count
           self.last_pulse_count   = parent.pulse_count
           

        # something wrong when publishing ?

        if hasattr(parent,'publisher') :
           if parent.publish_count <= self.last_publish_count:
              if parent.publisher.isAlive() :
                 self.logger.debug("has not published but is alive")
              else:
                 self.logger.warning("connection problem...reconnecting")
                 parent.close()
                 parent.connect()

           # keep the count
           self.last_publish_count = parent.publish_count

        return True

heartbeat_pulse = Heartbeat_Pulse(self)

self.on_heartbeat = heartbeat_pulse.perform

