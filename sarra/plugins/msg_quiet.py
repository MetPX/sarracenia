#!/usr/bin/python3

"""
  Null plugin to supress default messaging (shorter logs.)

"""

class Msg_Quiet(object): 

    def __init__(self,parent):
          pass
          
    def perform(self,parent):
        return True

msg_quiet = Msg_Quiet(self)

self.on_message = msg_quiet.perform

