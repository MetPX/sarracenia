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

    def update_appointments(self,when):
        """
          # make a flat list from values where comma separated on a single or multiple lines.

          set self.appointments to a list of when something needs to be run during the current day.
        """
        self.appointments=[]
        for h in self.hours:
           for m in self.minutes:
               if ( h > when.hour ) or ((h == when.hour) and ( m >= when.minute )):
                   appointment = datetime.time(h, m, tzinfo=datetime.timezone.utc )
                   next_time = datetime.datetime.combine(when,appointment)
                   self.appointments.append(next_time)
               else:
                   pass # that time is passed for today.

        logger.info( f"for {when}: {json.dumps(list(map( lambda x: str(x), self.appointments))) } ")


    def __init__(self,options,logger=logger):
        super().__init__(options,logger)
        self.o.add_option( 'scheduled_interval', 'duration', 0 )
        self.o.add_option( 'scheduled_hour', 'list', [] )
        self.o.add_option( 'scheduled_minute', 'list', [] )
        
        self.housekeeping_needed=False
        self.interrupted=None

        sched_hours = sum([ x.split(',') for x in self.o.scheduled_hour],[])
        self.hours = list(map( lambda x: int(x), sched_hours ))
        self.hours.sort()
        logger.debug( f"hours {self.hours}" )

        sched_min = sum([ x.split(',') for x in self.o.scheduled_minute ],[])
        self.minutes = list(map( lambda x: int(x), sched_min))
        self.minutes.sort()
        logger.debug( f'minutes: {self.minutes}')

        now=datetime.datetime.fromtimestamp(time.time(),datetime.timezone.utc)
        self.update_appointments(now)

    def gather(self,messageCountMax):

        # for next expected post
        self.wait_until_next()

        if self.stop_requested or self.housekeeping_needed:
            return []

        logger.info('time to run')

        # always post the same file at different time
        gathered_messages = []

        for relPath in self.o.path:
            st = FmdStat()
            m = sarracenia.Message.fromFileInfo(relPath, self.o, st)
            gathered_messages.append(m)

        return gathered_messages

    def on_housekeeping(self):

        self.housekeeping_needed = False


    def wait_seconds(self,sleepfor):
        """
           sleep for the given number of seconds, like time.sleep() but broken into
           shorter naps to be able to honour stop_requested, or when housekeeping is needed.
           
        """

        housekeeping=datetime.timedelta(seconds=self.o.housekeeping)
        nap=datetime.timedelta(seconds=10)

        if self.interrupted:
            sleepfor = self.interrupted
            now = datetime.datetime.fromtimestamp(time.time(),datetime.timezone.utc)

            # update sleep remaining based on how long other processing took.
            interruption_duration= now-self.interrupted_when
            sleepfor -= interruption_duration

        if sleepfor < nap:
            nap=sleepfor
    
        sleptfor=datetime.timedelta(seconds=0)

        while sleepfor > datetime.timedelta(seconds=0):
            time.sleep(nap.total_seconds())
            if self.stop_requested:
                return

            # how long is left to sleep.
            sleepfor -= nap
            self.interrupted=sleepfor
            self.interrupted_when = datetime.datetime.fromtimestamp(time.time(),datetime.timezone.utc)

            sleptfor += nap
            if sleptfor > housekeeping:
                self.housekeeping_needed=True
                return

        # got to the end of the interval...
        self.interrupted=None
       
    def wait_until( self, appointment ):

        now = datetime.datetime.fromtimestamp(time.time(),datetime.timezone.utc)

        sleepfor=appointment-now

        logger.info( f"{appointment} duration: {sleepfor}" )
        self.wait_seconds( sleepfor )


    def wait_until_next( self ):

        if self.o.scheduled_interval > 0:
            self.wait_seconds(datetime.timedelta(seconds=self.o.scheduled_interval))
            return

        if ( len(self.o.scheduled_hour) > 0 ) or ( len(self.o.scheduled_minute) > 0 ):
            now = datetime.datetime.fromtimestamp(time.time(),datetime.timezone.utc)
            next_appointment=None
            for t in self.appointments: 
                if now < t: 
                    next_appointment=t
                    break

            if next_appointment is None:
                # done for the day...
                tomorrow = datetime.date.today()+datetime.timedelta(days=1)
                midnight = datetime.time(0,0,tzinfo=datetime.timezone.utc)
                midnight = datetime.datetime.combine(tomorrow,midnight)
                self.update_appointments(midnight)
                next_appointment=self.appointments[0]

            self.wait_until(next_appointment)
            if self.interrupted:
                logger.info( f"sleep interrupted, returning for housekeeping." )
            else:
                self.appointments.remove(next_appointment)
                logger.info( f"ok {len(self.appointments)} appointments left today" )


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
