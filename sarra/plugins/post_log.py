#!/usr/bin/python3

"""
  default on_file handler logs that the file has been posted.
  prints a simple notice.

"""

class Post_Log(object): 

    def __init__(self,parent):
        parent.logger.debug( "post_log initialized" )
          
    def perform(self,parent):

        msg = parent.msg
        parent.logger.info("post_log notice=%s %s%s headers=%s" % \
            tuple( msg.notice.split()[0:3] + [ msg.headers ] ) )

        return True

post_log = Post_Log(self)

self.on_post = post_log.perform

