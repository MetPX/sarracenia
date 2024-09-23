import datetime
import logging
import pytest
from tests.conftest import *
#from unittest.mock import Mock

import sarracenia.config
import sarracenia.flowcb.scheduled
import time

logger = logging.getLogger(__name__)


def build_options():
     o = sarracenia.config.default_config()
     o.component = 'flow'
     o.config = 'ex1'
     o.action = 'start'

     o.parse_line( o.component, o.config, "flow/ex1", 1, "no 1" )
     o.parse_line( o.component, o.config, "", 1, "no 1" )
     o.finalize()
     return o

def test_schedules():

     options= build_options()
     options.scheduled_time=[ "12:40", "7:37" ]

     today=datetime.datetime.fromtimestamp(time.time(),datetime.timezone.utc)
     midnight=datetime.time(0,0,tzinfo=datetime.timezone.utc)
     midnight= datetime.datetime.combine(today,midnight)
     

     me=sarracenia.flowcb.scheduled.Scheduled(options)
     me.update_appointments(midnight)
     assert( len(me.appointments) == 2 ) 

     logger.info( f"set two appointments at specific times: {me.appointments=} {len(me.appointments)=}" )
     logger.info( f" {len(me.appointments)=}" )
 

     options = build_options()
     options.scheduled_hour= [ '1','3','5',' 7',' 9',' 13','21','23']
     options.scheduled_minute= [ '1,3,5',' 7',' 9',' 13',' 15',' 51','53' ]

     me=sarracenia.flowcb.scheduled.Scheduled(options)
     me.update_appointments(midnight)

     logger.info( f"set 72 appointments" )
     assert( len(me.appointments) == 72 ) 

     #logger.error( f" {me.appointments=} {len(me.appointments)=}" )
     #logger.error( f" HOHO {len(me.appointments)=}" )

     """
       this should work? but does not... dunno why... worth fixing but not part of #1206

       seems to barf on only having 1 scheduled hour... so maybe you need both?
     """
     #options = build_options()
     #options.scheduled_hour= [ '1' ]
     #options.scheduled_minute= []
     #me=sarracenia.flowcb.scheduled.Scheduled(options)
     #me.update_appointments(midnight)
     #assert( len(me.appointments) == 1 ) 

     #logger.error( f" {me.appointments=} {len(me.appointments)=}" )
     #logger.error( f" HOHO {len(me.appointments)=}" )
     
     """
         with both hour and minute specified... it works.

     """
     options = build_options()
     options.scheduled_hour= []
     options.scheduled_minute= []
     options.scheduled_time= []
     me=sarracenia.flowcb.scheduled.Scheduled(options)
     me.update_appointments(midnight)

     sample_time= datetime.time(hour=12, minute=5, tzinfo=datetime.timezone.utc )
     now=datetime.datetime.now(datetime.timezone.utc )
     sample_time= datetime.datetime.combine(now,sample_time)

     logger.info( f"default schedule (should be 300 second interval) {me.appointments=}" )
     assert( len(me.appointments) == 0 ) 

     me.calc_next_gather_time( sample_time )
     how_long = me.next_gather_time - sample_time
     logger.info( f" {how_long.total_seconds()=} until next poll. " )
     assert( how_long.total_seconds() <= 300 )


     logger.info( f"1 appointment at 01:01 each day..." )
     options = build_options()
     options = build_options()
     options.scheduled_hour= [ '1' ]
     options.scheduled_minute= [ '1' ]
     me=sarracenia.flowcb.scheduled.Scheduled(options)
     me.update_appointments(midnight)
     assert( len(me.appointments) == 1 ) 

     logger.info( f"pretending the time is 00:05 today" )
     sample_time= datetime.time(hour=0, minute=5, tzinfo=datetime.timezone.utc )
     now=datetime.datetime.now(datetime.timezone.utc )
     sample_time= datetime.datetime.combine(now,sample_time)

     me.calc_next_gather_time( sample_time )
     how_long = me.next_gather_time - sample_time
     logger.info( f" {how_long.total_seconds()=} until next poll. " )
     assert( how_long.total_seconds() == 3360 )

     options = build_options()
     options.scheduled_interval= [ 3600 ]
     options.scheduled_hour= [ ]
     options.scheduled_minute= [ ]
     me=sarracenia.flowcb.scheduled.Scheduled(options)
     me.update_appointments(midnight)
     assert( len(me.appointments) == 0 ) 

     logger.info( f"pretending the time is 00:05 today" )
     me.calc_next_gather_time( sample_time )
     how_long = me.next_gather_time - sample_time
     logger.info( f" {how_long.total_seconds()=} until next poll. " )
     assert( how_long.total_seconds() == 3600 )

     #logger.error( f" {me.appointments=} {len(me.appointments)=}" )
     #logger.error( f" HOHO {len(me.appointments)=}" )
     
     options.scheduled_hour= []
     options.scheduled_minute= []
     options.scheduled_time=[ "12:40", "7:37" ]
     me=sarracenia.flowcb.scheduled.Scheduled(options)
     me.update_appointments(midnight)
     assert( len(me.appointments) == 2 ) 

     logger.info( f"pretending the time is 00:05 today" )
     me.calc_next_gather_time( sample_time )
     how_long = me.next_gather_time - sample_time
     logger.info( f" {how_long.total_seconds()=} until next poll. " )
     assert( how_long.total_seconds() == 3600 )


     logger.info( f"Setting 4 appointments: 2:02, 4:02, 12:40, 7:37 ...")
     options= build_options()
     options.scheduled_hour= [ "2", "4" ]
     options.scheduled_minute= [ "2" ]
     options.scheduled_time=[ "12:40", "7:37" ]
     me=sarracenia.flowcb.scheduled.Scheduled(options)
     me.update_appointments(midnight)

     assert( len(me.appointments) == 4 ) 

     logger.info( f"pretending the time is 00:05 today" )
     me.calc_next_gather_time( sample_time )
     how_long = me.next_gather_time - sample_time
     logger.info( f" {how_long.total_seconds()=} until next poll. " )
     assert( how_long.total_seconds() == 7020 )

     """
       expect appointments at 2:00, and 4:00
     """
     logger.info( f"setting two appointments at 2:00, and 4:00 today" )
     options= build_options()
     options.scheduled_hour= [ "2", "4" ]
     options.scheduled_minute= [ ]
     options.scheduled_time=[ ]
     me=sarracenia.flowcb.scheduled.Scheduled(options)
     me.update_appointments(midnight)

     assert( len(me.appointments) == 2 ) 

     logger.info( f"pretending the time is 00:05 today" )
     me.calc_next_gather_time( sample_time )
     how_long = me.next_gather_time - sample_time
     logger.info( f" {how_long.total_seconds()=} until next poll. " )
     assert( how_long.total_seconds() == 6900 )

     """
       expect appointments at :02, and :04 every hour.
     """
     logger.info( f"setting appointments at :02, and :04 every hour" )
     options= build_options()
     options.scheduled_minute= [ "2", "4" ]
     options.scheduled_hour= [ ]
     options.scheduled_time=[ ]
     me=sarracenia.flowcb.scheduled.Scheduled(options)
     me.update_appointments(midnight)

     assert( len(me.appointments) == 48 ) 

     logger.info( f"pretending the time is 00:05 today" )
     me.calc_next_gather_time( sample_time )
     how_long = me.next_gather_time - sample_time
     logger.info( f" {how_long.total_seconds()=} until next poll. " )
     assert( how_long.total_seconds() == 3420 )

     #logger.error( f" {me.appointments=} {len(me.appointments)=}" )
     #logger.error( f" HOHO {len(me.appointments)=}" )
 
