import logging
import paramiko
import re

import sarracenia
from sarracenia.filemetadata import FmdStat
from sarracenia.flowcb import FlowCB

import datetime
import json
import time


logger = logging.getLogger(__name__)

class Scheduled(FlowCB):

    """
    Scheduled flow callback plugin arranges to post url's
    at scheduled times. 
    
    usage:

    In the configuration file, need::
 
        callback scheduled

    and the schedule can be a specified as:
    
    * scheduled_interval 1m   (once a minute) a duration
    * scheduled_hour  4,9    at 4Z and 9Z every day.
    * scheduled_minute 33,45  within scheduled hours which minutes.
    
    Scheduled_interval takes precedence over the others, making it
    easier to specify an interval for testing/debugging purposes.
    
    use in code (for subclassing):
   
    from sarracenia.scheduled import Scheduled 

    class hoho(Scheduled):
         replace the gather() routine...
         keep the top lines "until time to run"
         replace whatever is below.
         will only run when it should.

    """

    def __init__(self,options,class_logger=logger):
        super().__init__(options,class_logger)
        # if logLevel is set for a subclass, apply it here too
        if hasattr(self.o,'logLevel') and logger:
            logger.setLevel(getattr(logging, self.o.logLevel.upper()))
        
        self.o.add_option( 'scheduled_interval', 'duration', 0 )
        self.o.add_option( 'scheduled_hour', 'list', [] )
        self.o.add_option( 'scheduled_minute', 'list', [] )
        self.o.add_option( 'scheduled_time', 'list', [] )
        
        self.housekeeping_needed=False

        self.sched_times = sum([ x.split(',') for x in self.o.scheduled_time],[])
        #self.sched_times.sort()

        sched_hours = sum([ x.split(',') for x in self.o.scheduled_hour],[])
        if sched_hours == [] : sched_hours = list(range(0,24))
        self.hours = list(map( lambda x: int(x), sched_hours ))
        #self.hours.sort()
        logger.debug( f"hours {self.hours}" )

        sched_min = sum([ x.split(',') for x in self.o.scheduled_minute ],[])
        if sched_min == [] : sched_min = [0]
        self.minutes = list(map( lambda x: int(x), sched_min))
        #self.minutes.sort()

        self.default_wait=datetime.timedelta(seconds=300)

        logger.debug( f'minutes: {self.minutes}')

        now=datetime.datetime.fromtimestamp(time.time(),datetime.timezone.utc)
        self.update_appointments(now)
        self.first_interval=True

        if self.o.scheduled_interval <= 0 and not self.appointments:
            logger.warning(f"no scheduled_interval or appointments (combination of scheduled_hour and scheduled_minute) set defaulting to every {self.default_wait.seconds} seconds")

        # Determine the next gather time
        # For scheduled_interval, gather immediately after starting
        if self.o.scheduled_interval and self.o.scheduled_interval > 0:
            self.next_gather_time = now
        else:
            self.next_gather_time = None
            self.calc_next_gather_time()

        self.last_gather_time = 0

    def update_appointments(self,when):
        """
          # make a flat list from values where comma separated on a single or multiple lines.

          set self.appointments to a list of when something needs to be run during the current day.
        """
        self.appointments=[]
        if self.o.scheduled_minute or self.o.scheduled_hour:
            for h in self.hours:
               for m in self.minutes:
                   if ( h > when.hour ) or ((h == when.hour) and ( m >= when.minute )):
                       appointment = datetime.time(h, m, tzinfo=datetime.timezone.utc )
                       next_time = datetime.datetime.combine(when,appointment)
                       self.appointments.append(next_time)
                   else:
                       pass # that time is passed for today.
        if self.o.scheduled_time:
            for time in self.sched_times:
                hour,minute=time.split(':')
                hour = int(hour)
                minute = int(minute)
                if ( hour > when.hour ) or ((hour == when.hour) and ( minute >= when.minute )):
                    appointment = datetime.time(hour, minute, tzinfo=datetime.timezone.utc )
                    next_time = datetime.datetime.combine(when,appointment)
                    self.appointments.append(next_time)
                else:
                    pass # that time is passed for today.
        
        self.appointments.sort()
        logger.info( f"for {when}: {self.appointments_to_string()} ")

    def appointments_to_string(self):
        return json.dumps(list(map( lambda x: str(x), self.appointments)))

    def calc_next_gather_time(self, last_gather=0):
        if self.next_gather_time in self.appointments:
            self.appointments.remove(self.next_gather_time)
        if last_gather == 0:
            last_gather = datetime.datetime.now(datetime.timezone.utc)
        
        # Scheduled interval overrides other options
        if self.o.scheduled_interval and self.o.scheduled_interval > 0:
            self.next_gather_time = last_gather + datetime.timedelta(seconds=self.o.scheduled_interval)
            logger.debug(f"next gather should be in {self.o.scheduled_interval}s, scheduled for {self.next_gather_time}")
        
        # No scheduled interval --> try to use configured schedule
        elif len(self.o.scheduled_hour) > 0 or len(self.o.scheduled_minute) > 0 or len(self.o.scheduled_time) > 0:
            next_appointment=None
            missed_appointments=[]
            for t in self.appointments: 
                if last_gather < t: 
                    next_appointment=t
                    break
                else:
                    logger.info( f'already too late to {t} skipping' )
                    missed_appointments.append(t)

            if missed_appointments:
                for ma in missed_appointments:
                    self.appointments.remove(ma)

            if next_appointment is None:
                # done for the day...
                tomorrow = datetime.datetime.fromtimestamp(time.time(),datetime.timezone.utc)+datetime.timedelta(days=1)
                midnight = datetime.time(0,0,tzinfo=datetime.timezone.utc)
                midnight = datetime.datetime.combine(tomorrow,midnight)
                self.update_appointments(midnight)
                next_appointment=self.appointments[0]

            self.next_gather_time = next_appointment
            logger.debug(f"next gather scheduled for {self.next_gather_time} from appointments {self.appointments_to_string()}")

        # No scheduled interval and no scheduled hour/minutes/time
        else:
            self.next_gather_time = last_gather + self.default_wait
            logger.debug(f"next gather should be in {self.default_wait.seconds}s, scheduled for {self.next_gather_time} (default_wait")

    def ready_to_gather(self):
        current_time = datetime.datetime.now(datetime.timezone.utc )
        if current_time >= self.next_gather_time and not self.stop_requested:
            late = (current_time - self.next_gather_time).total_seconds()
            logger.info(f"--> yes, now >= {self.next_gather_time} ({late}s late)")
            # NOTE: could also pass self.next_gather_time to calc_next_gather_time to get more precise intervals
            # See https://github.com/MetPX/sarracenia/issues/1214#issuecomment-2344711046 for discussion.
            self.calc_next_gather_time(current_time)
            self.last_gather_time = current_time
            return True
        else:
            logger.debug(f"--> no, next gather scheduled for {self.next_gather_time}")

    def gather(self, messageCountMax):
        if self.ready_to_gather():
            # always post the same file at different time
            gathered_messages = []
            for relPath in self.o.path:
                st = FmdStat()
                m = sarracenia.Message.fromFileInfo(relPath, self.o, st)
                gathered_messages.append(m)
            return (True, gathered_messages)
        else:
            logger.debug(f"nothing to do")
            return (False, [])

    def on_housekeeping(self):
        logger.info(f"next gather scheduled for {self.next_gather_time}")
        n_appointments = len(self.appointments)
        if n_appointments > 0:
            logger.info(f"{n_appointments} appointments remaining for today")
            logger.debug(f"remaining appointments: {self.appointments_to_string()}")
        self.housekeeping_needed = False

if __name__ == '__main__':
    
        import sarracenia.config
        import types    
        import sarracenia.flow
        options = sarracenia.config.default_config()
        flow = sarracenia.flow.Flow(options)
        flow.o.scheduled_hour= [ '1','3','5',' 7',' 9',' 13','21','23']
        flow.o.scheduled_minute= [ '1,3,5',' 7',' 9',' 13',' 15',' 51','53' ]
        logging.basicConfig(level=logging.DEBUG)

        when=datetime.datetime.fromtimestamp(time.time(),datetime.timezone.utc)

        me = Scheduled(flow.o)
        me.update_appointments(when)
        
        flow.o.scheduled_hour= [ '1' ]
        me = Scheduled(flow.o)
        me.update_appointments(when)
    
        """
            for unit testing should be able to change when, and self.o.scheduled_x to cover 
            many different test cases.
        """

        while True:
            logger.info("hoho!")
            me.wait_until_next()
            logger.info("Do Something!")
