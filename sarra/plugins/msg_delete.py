#!/usr/bin/python3

"""
  the default on_msg handler for sr_log.
  prints a simple notice.

"""

class Msg_Delete(object): 

    def __init__(self,parent):
        parent.logger.debug("msg_delete initialized")
          
    def perform(self,parent):
 
        import os
        msg = parent.msg
        #parent.logger.info("msg_delete received: %s %s%s topic=%s lag=%g %s" % \
        #   tuple( msg.notice.split()[0:3] + [ msg.topic, msg.get_elapse(), msg.hdrstr ] ) )
        parent.logger.info("msg_delete: %s/%s" % (msg.new_dir, msg.new_file))
        os.unlink( "%s/%s" % (msg.new_dir, msg.new_file) )
        return True

msg_delete = Msg_Delete(self)

self.on_message = msg_delete.perform

