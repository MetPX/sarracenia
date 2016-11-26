#!/usr/bin/python3

"""
  Example use of do_download option.

  Custom downloading method to work with the message_scp on_message plugin.
  
  This downloader will be invoked when an unknown protocol scheme is specified as a URL (we use 'download')

  note that because this involves a for exec to launch a binary, it would be best to only launch this sort
  of download for larger files. the message_scp implements this threshold behaviour.

"""

import os,stat,time
import calendar

class SCP_DOWNLOAD(object): 


   def __init__(self):

      pass
          
   def perform(self,parent):
      logger = parent.logger
      msg    = parent.msg

      import subprocess

      sourcefile = msg.url.hostname + ':' + msg.url.path

      if msg.url.username:
           sourcefile = msg.usr.username +'@' + sourcefile

      cmd = [ "/usr/bin/scp" , sourcefile, msg.local_file ] 

      logger.info("download invoking: %s " % cmd )
      
      result =  subprocess.run( cmd )
      
      if (result.returncode == 0):  # Success!
         if parent.reportback:
            msg.report_publish(201,'Downloaded')
         return True
         
      #Failure!

      if parent.reportback:
         msg.report_publish(499,'scp download failed')

      return False 


scp_download = SCP_DOWNLOAD()
self.do_download = scp_download.perform

