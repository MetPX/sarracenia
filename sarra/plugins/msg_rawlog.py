#!/usr/bin/python3

"""
  a on_msg callback to print the content of the AMQP message.
  one can see clearly the difference between v02 and v03 messages.

"""

class Msg_rawLog(object): 

    def __init__(self,parent):
        parent.logger.debug("msg_rawlog initialized")
          
    def on_message(self,parent):
        msg = parent.msg
        parent.logger.info("msg_rawlog received: body=%s properties=%s topic=%s lag=%g " % \
           (parent.consumer.raw_msg.body, parent.consumer.raw_msg.properties, msg.topic, msg.get_elapse() ) )
        return True

msg_rawlog = Msg_rawLog(self)

self.on_message = msg_rawlog.on_message

