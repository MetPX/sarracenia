#!/usr/bin/python3

"""
  default on_file handler logs that the file has been received.
  prints a simple notice.

"""

import os,stat,time

class File_Log(object): 

    def __init__(self,parent):
          pass
          
    def perform(self,parent):

        parent.logger.info("file_log downloaded to: %s" % parent.msg.local_file)
        return True

file_log = File_Log(self)

self.on_file = file_log.perform

