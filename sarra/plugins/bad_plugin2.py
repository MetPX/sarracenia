#!/usr/bin/python3

"""
  example of mis-formed plugin.
  error: missing instantiation of class.

Post 2.18.1a4 *plugin* method:

   plugin bad_plugin2

Individual declaration: 

  on_message bad_plugin2

blacklab% ./sr_subscribe.py foreground clean_f90.conf
2018-01-05 10:16:47,103 [ERROR] sr_config/execfile 2 Type: <class 'NameError'>, Value: name 'bad_plugin2' is not defined
2018-01-05 10:16:47,103 [ERROR] for option on_message plugin bad_plugin2 did not work
blacklab

"""

class Bad_Plugin2(object): 

    def __init__(self,parent):
        parent.logger.debug("log_all initialized")
          
    def on_message(self,parent):
        msg = parent.msg
        parent.logger.info("log_all message accepted: %s %s%s topic=%s lag=%g %s" % \
           ( msg.pubtime, msg.basurl, msg.relpath, msg.topic, msg.get_elapse(), msg.hdrstr ) )
        return True

#bad_plugin2 = Bad_Plugin2(self)  <-- need this line when declaring individual

self.on_message = bad_plugin2.on_message

