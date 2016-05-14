#!/usr/bin/python3

"""
<<<<<<< HEAD
  default on_file handler logs that the file has been received.
=======
  the default on_msg handler for sr_log.
>>>>>>> f5988286f06dadc4846955490f0e41bd050cbf10
  prints a simple notice.

"""

<<<<<<< HEAD
import os,stat,time

=======
>>>>>>> f5988286f06dadc4846955490f0e41bd050cbf10
class Post_Log(object): 

    def __init__(self,parent):
          pass
          
    def perform(self,parent):
<<<<<<< HEAD

        msg = parent.msg
        parent.logger.info("post_log notice=%s headers=%s" % ( msg.notice, msg.headers))
=======
        msg = parent.msg
        parent.logger.info("msg_log received: %s topic=%s lag=%g %s" % \
           ( msg.notice, msg.topic, msg.get_elapse(), msg.hdrstr ) )
>>>>>>> f5988286f06dadc4846955490f0e41bd050cbf10
        return True

post_log = Post_Log(self)

self.on_post = post_log.perform

