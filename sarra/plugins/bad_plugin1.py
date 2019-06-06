#!/usr/bin/python3

"""
  example of mis-formed plugin. in old format.
  Error: instance variable is not lowercase version of Classname

usage:

version >=2.18.1a4:

plugin bad_plugin1


Pre 2.18:
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
           ( msg.pubtime, msg.baseurl, msg.relpath, msg.topic, msg.get_elapse(), msg.hdrstr ) )
        return True
          
""" 
after 2.18.1a4
"""
self.plugin='bad_blugin'  # <-- error plugin must be Mixed case, and string must have same case as Class.



"""
format for release < 2.18.1a4
"""
hoho = Bad_Plugin1(self)  # <-- ERROR: must be named bad_plugin1, not hoho

self.on_message = hoho.on_message

