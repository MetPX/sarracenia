#!/usr/bin/python3

"""
  default on_heartbeat pulse processing...
  if pulse is emitted for a while, and than missing
  we will issue a reconnection.

  caveat 1 : once pulsing has started... it must continue
             if poll_pulse stops the process will verify the connection,
                  (isAlive) and if that fails, trigger a reconnection
             every heartbeat

  caveat 2 : receiving pulse messages will not behave as expected for
             process with N instances because we cannot guarantee that each
             one of them receives its own pulse...

  because of caveat #2, the pulse frequency should be reasonably high... once a minute?
  but in the case of caveat #2, you only need multiple instances if the flow is too high for one.
  so maybe this is never a problem?  would be a problem if flows are extremely uneven (high for short periods.)

"""

class Hb_Pulse(object): 

    def __init__(self,parent):
        self.init(parent)
        self.skip_first         = True

    def init(self,parent):
        self.last_time          = time.time()
        self.last_message_count = parent.message_count
        self.last_publish_count = parent.publish_count
        self.last_pulse_count   = parent.pulse_count
          
    def perform(self,parent):

        if self.skip_first :
           self.init(parent)
           self.skip_first = False

        self.logger     = parent.logger
        self.logger.info( "hb_pulse message_count %d publish_count %d " %  \
            ( parent.message_count, parent.publish_count ) )

        # something wrong when consuming ?

        if hasattr(parent,'consumer') :
           if parent.message_count <= self.last_message_count:
              if parent.pulse_count <=  self.last_pulse_count:
                 if parent.consumer.isAlive() :
                    self.logger.info("hb_pulse received neither message nor pulse, but confirmed broker connection remains alive")
                 else:
                    self.logger.warning("hb_pulse no pulse, and no connection... reconnecting")
                    parent.close()
                    parent.connect()

           # keep these counts
           self.last_message_count = parent.message_count
           self.last_pulse_count   = parent.pulse_count
           
        # something wrong when publishing ?

        if hasattr(parent,'publisher') :
           if parent.publish_count <= self.last_publish_count:
              if parent.publisher.isAlive() :
                 self.logger.debug("hb_pulse no messages receive but still connected.")
              else:
                 self.logger.warning("hb_pulse connection problem...reconnecting")
                 parent.close()
                 parent.connect()

           # keep the count
           self.last_publish_count = parent.publish_count

        return True

hb_pulse = Hb_Pulse(self)

self.on_heartbeat = hb_pulse.perform

