#!/usr/bin/python3

"""
  default on_file handler logs that the file has been received.
  prints a simple notice.

"""

import os,stat,time

class File_Log(object): 

    def __init__(self,parent):
        parent.logger.debug("file_log initialized")
          
    def perform(self,parent):
        import os.path
        parent.logger.info("file_log downloaded to: %s" % os.path.normpath( parent.msg.new_dir + '/' + parent.msg.new_file ) )
        return True

file_log = File_Log(self)

self.on_file = file_log.perform

