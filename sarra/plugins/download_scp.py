#!/usr/bin/python3

"""
 download_scp: an example do_download option usage.

  This launches the 'scp' command with appropriate arguments to perform a file transfer.

  This demonstrates a custom downloading method to work with the message_download on_message 
  plugin.  See that plugin source for more detailed documentation.
  
  This downloader expects to be invoked for the 'download' URL scheme is specified as a URL.

  while the scp command is used by default, it can be overridden with the download_scp_command option.

  Samnple usage:

  download_scp_command /usr/bin/ssh cetus bbcp

  do_download download_scp

  will instead of instead of invoking scp, it will invoke the ssh command to initiate a connection to a host named 'cetus'
  and run a bbcp command from there.   To the command will be appended the appropriate source and destination file specifications
  as per ssh/scp expectations.

"""

import os,stat,time
import calendar

class SCP_DOWNLOAD(object): 


   def __init__(self,parent):
      if not hasattr(parent,'download_scp_command'):
         parent.download_scp_command= [ '/usr/bin/scp' ]
      pass
          
   def perform(self,parent):
      logger = parent.logger
      msg    = parent.msg

      import subprocess

      # rebuild an scp compatible source specification from the provide url ( proto://user@host// --> user@host: )
      sourcefile = msg.url.hostname + ':' + msg.url.path

      if msg.url.username:
           sourcefile = msg.url.username +'@' + sourcefile

      cmd = parent.download_scp_command[0].split() + [ sourcefile, msg.new_file ] 

      logger.debug("download_scp invoking: %s " % cmd )
      
      result =  subprocess.call( cmd )
      
      if (result == 0):  # Success!
         if parent.reportback:
            msg.report_publish(201,'Downloaded')
         return True
         
      #Failure!

      if parent.reportback:
         msg.report_publish(499,'download_scp failed invocation of: %s ' % cmd )

      return False 


scp_download = SCP_DOWNLOAD(self)
self.do_download = scp_download.perform

