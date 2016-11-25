#!/usr/bin/python3

"""
  Use wget to download bigger files.

  This is a means of invoking a more efficienty binary downloader when it makes sense to do so in place
  of the python scripting downloader, typically for larger files.   Set the msg_wget_threshold to the
  maximum size of the file to download using built in methods.  Default: 10M (ten megabytes)

  if a file larger than 10M is advertised, then the URL scheme is replaced 'http' -> 'wget'

  This means the do_download plugin (download_wget) will be invoked for that file.

  usage:



  msg_wget_threshold 10M

  on_message msg_wget

  do_download download_wget


"""

import os,stat,time
import calendar

class WGET_REWRITE(object): 

      import urllib.parse

      def __init__(self,parent):
          if not hasattr( parent, "msg_wget_threshold" ):
             parent.msg_wget_threshold = [ "10M" ]

          
      def perform(self,parent):
          logger = parent.logger
          msg    = parent.msg

          if type(parent.msg_wget_threshold) is list:
             parent.msg_wget_threshold = parent.chunksize_from_str( parent.msg_wget_threshold[0] )

          parts = msg.partstr.split(',')
          if parts[0] == '1':
              sz=int(parts[1])
          else:
              sz=int(parts[1])*int(parts[2])

          logger.info("wget_ sz: %d, threshold: %d download: %s to %s, " % ( \
                sz, parent.msg_wget_threshold, parent.msg.urlstr, msg.local_file ) )
          if sz > parent.msg_wget_threshold :
              parent.msg.urlstr = msg.urlstr.replace("http:","wget:")
              parent.msg.url = urllib.parse.urlparse(msg.urlstr)
              logger.info("wget_large file: download: %s to %s, " % (parent.msg.urlstr, msg.local_file))

          return True

wget_rewrite = WGET_REWRITE(self)
self.on_message = wget_rewrite.perform

