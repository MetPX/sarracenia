#!/usr/bin/python3

"""
  Example use of do_download option.

  Custom downloading method to work with the message_wget on_message plugin.
  
  This downloader will be invoked when an unknown protocol scheme is specified as a URL (we use 'wget')
  the script replaces 'wget' by 'http' in the protocol, and then spawns a wget binary to perform
  an efficient download. 

  note that because this involves a for exec to launch a binary, it would be best to only launch this sort
  of download for larger files. the message_wget implements this threshold behaviour.

  Caveat:
       This downloader just uses the name that wget will set for a file on download,
       no options about local file naming are implemented.

"""

import os,stat,time
import calendar

class WGET_DOWNLOAD(object): 


   def __init__(self):

      pass
          
   def perform(self,parent):
      logger = parent.logger
      msg    = parent.msg

      import subprocess

      logger.info("wwget! downloading: from: %s to %s " % (msg.url, msg.local_file))
      
      msg.urlstr = msg.urlstr.replace("wget:","http:")

      result =  subprocess.run( [ "/usr/bin/wget" , msg.urlstr ] )
      
      return (result.returncode == 0)


wget_download = WGET_DOWNLOAD()
self.do_download = wget_download.perform

