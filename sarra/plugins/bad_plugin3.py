#!/usr/bin/python3

"""
  example of mis-formed plugin.
  Error: self.on_message improperly set.

usage:

on_message bad_plugin3

blacklab% ./sr_subscribe.py foreground clean_f90.conf
2018-01-05 10:22:11,049 [ERROR] plugin bad_plugin3: self.on_message improperly set. Could not determine plugin class
b

"""

class Bad_Plugin3(object): 

    def __init__(self,parent):
        parent.logger.debug("log_all initialized")
          
    def on_message(self,parent):
        msg = parent.msg
        parent.logger.info("log_all message accepted: %s %s%s topic=%s lag=%g %s" % \
           ( msg.pubtime, msg.baseurl, msg.relpath, msg.topic, msg.get_elapse(), msg.hdrstr ) )
        return True
          
bad_plugin3 = Bad_Plugin3(self)  

self.on_message = None # <-- ERROR: should be bad_plugin3.<something> (usually *on_message*)
