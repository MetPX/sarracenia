#!/usr/bin/python3

"""
  Null plugin to supress default logging (shorter logs.)

"""

class Post_Quiet(object): 

    def __init__(self,parent):
          pass
          
    def perform(self,parent):
        return True

post_quiet = Post_Quiet(self)

self.on_post = post_quiet.perform

