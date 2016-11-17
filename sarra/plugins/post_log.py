#!/usr/bin/python3

"""
<<<<<<< HEAD
  default on_file handler logs that the file has been received.
=======
  the default on_msg handler for sr_log.
>>>>>>> f5988286f06dadc4846955490f0e41bd050cbf10
  prints a simple notice.

"""

class Post_Log(object): 

    def __init__(self,parent):
          pass
          
    def perform(self,parent):

        msg = parent.msg
        parent.logger.info("post_log notice=%s %s%s headers=%s" % \
            tuple( msg.notice.split()[0:3] + [ msg.headers ] ) )

        return True

post_log = Post_Log(self)

self.on_post = post_log.perform

