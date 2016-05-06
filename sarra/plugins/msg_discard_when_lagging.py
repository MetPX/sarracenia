#!/usr/bin/python3

"""
 Discard messages if they are too old, so that rather than downloading
 obsolete data, only current data will be retrieved.

 this should be used as an on_msg script. 
 For each announcement, check how old it is, and if it exceeds the threshold in the 
 routine, discard the message by returning False, after printing a local log message saying so.
 
 The message can be used to gauge whether the number of instances or internet link are sufficient
 to transfer the data selected.  if the lag keeps increasing, then likely instances should be 
 increased.

 It is mandatory to set the threshold for discarding messages (in seconds) in the configuration 
 file. For example:

 discard_maxlag 10

 will result in messages which are more than 10 seconds old being skipped. 

 If this option is not set, every message received will result in an error message.


"""

import os,stat,time

class Transformer(object): 


    def __init__(self,parent):
        pass
          
    def perform(self,parent):
        logger = parent.logger
        msg    = parent.msg

        import calendar

        mt=msg.time
        then=calendar.timegm(time.strptime(mt[:mt.find('.')],"%Y%m%d%H%M%S")) + float(mt[mt.find('.'):])
        now=time.time()

        # Set the maximum age, in seconds, of a message to retrieve.
        lag=now-then

        if lag > int(parent.discard_maxlag) :
           logger.info("discard_when_lagging, Excessive lag: %g sec. Skipping download of: %s, " % (lag, msg.local_file))
           return False

        return True

transformer = Transformer(self)
self.on_message = transformer.perform

