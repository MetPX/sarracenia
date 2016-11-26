#!/usr/bin/python3

"""
  Example use of do_download option.

  Custom downloading method to work with the message_download on_message plugin.
  See that plugin for more detailed information.
  
  This downloader will be invoked when an unknown protocol scheme is specified as a URL (we use 'wget')
  the script replaces 'download' by 'http' in the protocol, and then spawns a wget binary to perform
  an efficient download. 

  note that because this involves a for exec to launch a binary, it would be best to only launch this sort
  of download for larger files. the message_download implements this threshold behaviour.

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

      msg.urlstr = msg.urlstr.replace("download:","http:")
      logger.info("wwget! downloading: from: %s to %s using: %s" % (msg.url, msg.local_file, msg.urlstr))
      result =  subprocess.run( [ "/usr/bin/wget" , msg.urlstr ] )
      
      if (result.returncode == 0):  # Success!
         if parent.reportback:
            msg.report_publish(201,'Downloaded')
         return True
         
      if parent.reportback:
         msg.report_publish(499,'wget download failed')
      return False 

wget_download = WGET_DOWNLOAD()
self.do_download = wget_download.perform

