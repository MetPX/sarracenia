#!/usr/bin/python3

"""
  Null plugin to supress default logging (shorter logs.)

"""

class File_Quiet(object): 

    def __init__(self,parent):
          pass
          
    def perform(self,parent):
        return True

file_quiet = File_Quiet(self)

self.on_file = file_quiet.perform

