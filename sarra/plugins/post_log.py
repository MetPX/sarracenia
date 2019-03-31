#!/usr/bin/python3

"""
  default on_file handler logs that the file has been posted.
  prints a simple notice.

  post_log_format raw|old|compact
"""

class Post_Log(object): 

    def __init__(self,parent):
        parent.declare_option('post_log_format')
        parent.logger.debug( "post_log initialized" )
        if not hasattr(parent, 'post_log_format' ):
            parent.post_log_format=[ 'old' ]
          
    def perform(self,parent):

        msg = parent.msg
        f = parent.post_log_format

        if 'compact' in f :
            parent.logger.info("post_log %s %s lag=%s version=%s baseurl=%s relpath=%s " % \
                ( 'compact', msg.pubtime, msg.get_elapse(), msg.version, msg.baseurl, msg.relpath ) )
        elif 'v03' in f:
            parent.logger.info("post_log %s %s lag=%s headers=%s " % \
                ( 'v03', msg.pubtime, msg.get_elapse(), msg.headers ) )
        elif 'v03' in f:
            parent.logger.info("post_log %s %s lag=%s headers=%s " % \
                ( 'v03', msg.pubtime, msg.get_elapse(), msg.headers ) )
        elif 'old' in f:
            parent.logger.info("post_log notice=%s %s %s headers=%s" % \
                ( msg.pubtime, msg.baseurl, msg.relpath, msg.headers ) )

        return True

post_log = Post_Log(self)

self.on_post = post_log.perform

