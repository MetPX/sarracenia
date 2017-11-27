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
        self.last_pulse_count   = parent.pulse_count
          
    def perform(self,parent):
        self.logger     = parent.logger
        self.logger.debug("heartbeat_pulse_check")

        # something wrong ?

        if parent.message_count <= self.last_message_count:
           if parent.pulse_count <=  self.last_pulse_count:
              self.logger.warning("No message received, no pulse received")
              self.logger.warning("Reconnecting")
              if hasattr(parent,'consumer') :
                 if parent.consumer.isAlive() :
                    self.logger.warning("has no message and no pulse but is alive")
                 else:
                    parent.close()
                    parent.connect()

        # keep these value
        self.last_message_count = parent.message_count
        self.last_pulse_count   = parent.pulse_count
           
        return True

heartbeat_pulse = Heartbeat_Pulse(self)

self.on_heartbeat = heartbeat_pulse.perform

