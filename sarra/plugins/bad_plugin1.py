#!/usr/bin/python3

"""
  example of mis-formed plugin.
  Error: instance variable is not lowercase version of Classname

usage:

on_message bad_plugin1

blacklab% ./sr_subscribe.py foreground clean_f90.conf
2018-01-05 10:15:09,761 [ERROR] on_message plugin bad_plugin1 incorrect: plugin Bad_Plugin1 class must be instanced as bad_plugin1
blacklab%

"""

class Bad_Plugin1(object): 

    def __init__(self,parent):
        parent.logger.debug("log_all initialized")
          
    def on_message(self,parent):
        msg = parent.msg
        parent.logger.info("log_all message accepted: %s %s%s topic=%s lag=%g %s" % \
           tuple( msg.notice.split()[0:3] + [ msg.topic, msg.get_elapse(), msg.hdrstr ] ) )
        return True
          
hoho = Bad_Plugin1(self)  # <-- ERROR: must be named bad_plugin1, not hoho

self.on_message = hoho.on_message

