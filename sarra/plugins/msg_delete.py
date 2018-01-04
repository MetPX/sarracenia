#!/usr/bin/python3

"""
  the default on_msg handler for sr_log.
  prints a simple notice.

"""

class Msg_Delete(object): 

    def __init__(self,parent):
        parent.logger.debug("msg_delete initialized")
          
    def on_message(self,parent):
 
        import os
        msg = parent.msg

        f="%s/%s" % (msg.new_dir, msg.new_file) 
        parent.logger.info("msg_delete: %s" % f)
        try:
            if os.path.exists(f):
                os.unlink( f );
        except:
            pass

        return True

msg_delete = Msg_Delete(self)

self.on_message = msg_delete.on_message

