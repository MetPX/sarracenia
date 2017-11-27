#!/usr/bin/python3

"""
 poll_pulse: a kind of keepalive and client messaging mechanism

 usage:
     in an sr_poll configuration file:
     the post broker user must be the admin 
     because we pulse on all exchanges

 do_poll poll_pulse.py

"""


class POLL_SCRIPT(object): 

   def __init__(self,parent):

       # fake destination

       if not hasattr(parent,'destination') or not parent.destination:
          parent.destination = parent.post_broker.geturl()

       self.last_pulse_message = None
          
   def perform(self,parent):
       logger      = parent.logger

       # we should sleep at least 2 mins

       if parent.sleep == 0 : parent.sleep = 120

       # message_ttl if not set is 2 * sleep

       if not parent.message_ttl : parent.message_ttl = int(parent.sleep * 1000)

       # pulse 

       parent.post_pulse()

       return False

poll_script = POLL_SCRIPT(self)
self.do_poll = poll_script.perform
