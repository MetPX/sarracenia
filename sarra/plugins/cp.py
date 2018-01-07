#!/usr/bin/python3
"""
  cp : an example do_download option usage.

  This launches the UNIX 'cp' command with appropriate arguments to perform a file transfer.
  This downloader expects to be invoked for the 'download' URL scheme is specified as a URL.
  while the cp command is used by default, it can be overridden with the cp_command option.

  Samnple usage:

  cp_command /usr/bin/cp -p 

  do_download cp

  will instead of instead of invoking cp, it will invoke the cp -p command. To the command will be 
  appended the appropriate source and destination file specifications as per cp command expectations.
  Trigger an alternate method for downloading bigger files.

  This is a means of invoking a more efficient binary downloader when it makes sense to do so in place
  of the built-in pythjon interpreted downloader, typically for larger files. Set the cp_threshold to the
  maximum size of the file to download using built in methods. Default: 10M (ten megabytes)

  if a file larger than 10M is advertised, then the URL scheme is replaced 'http' -> 'download'

  This means the do_download plugin (download_wget) will be invoked for that file.

  example, if you see a file url with an sftp protocol, and larger than 10 megabytes, the trigger the substition:

  cp_threshold 10M
  cp_protocol  'sftp'

  See end of file for more APPLICATION NOTES.

"""

import os,stat,time
import calendar

class CP(object): 

   import urllib.parse

   def __init__(self,parent):

      parent.declare_option( 'cp_command' )
      parent.declare_option( 'cp_threshold' )
      parent.declare_option( 'cp_protocol' )


   def on_start(self,parent):

      if not hasattr(parent,'cp_command'):
         parent.cp_command= [ '/usr/bin/cp' ]

      if not hasattr( parent, "cp_threshold" ):
             parent.cp_threshold = [ "10M" ]

      if not hasattr( parent, "cp_protocol" ):
             parent.cp_protocol = [ "http" ]
          

   def on_msssage(self,parent):

      logger = parent.logger
      msg    = parent.msg

      if type(parent.cp_threshold) is list:
          parent.cp_threshold = parent.chunksize_from_str( parent.cp_threshold[0] )

      if msg.headers['sum'][0] == 'L' or msg.headers['sum'][0] == 'R' : return True

      parts = msg.partstr.split(',')
      if parts[0] == '1':
          sz=int(parts[1])
      else:
          sz=int(parts[1])*int(parts[2])

      logger.debug("cp sz: %d, threshold: %d download: %s to %s, " % ( \
          sz, parent.cp_threshold, parent.msg.urlstr, msg.new_file ) )
      if sz >= parent.cp_threshold :
          for p in parent.cp_protocol :
              parent.msg.urlstr = msg.urlstr.replace(p,"download")

          parent.msg.url = urllib.parse.urlparse(msg.urlstr)
          logger.info("cp triggering alternate method for: %s to %s, " % (parent.msg.urlstr, msg.new_file))

      return True


   def do_download(self,parent):
      logger = parent.logger
      msg    = parent.msg

      import subprocess

      # rebuild an scp compatible source specification from the provide url ( proto://user@host// --> user@host: )

      cmd = parent.cp_command[0].split() + [ msg.url.path, msg.new_dir + os.sep + msg.new_file ] 

      logger.debug("cp invoking: %s " % cmd )
      
      result =  subprocess.call( cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL )
      
      if (result == 0):  # Success!
         if parent.reportback:
            msg.report_publish(201,'Downloaded')
         if hasattr(parent,'chmod'):
            os.chmod(msg.new_file, parent.chmod)
         return True
         
      #Failure!

      if parent.reportback:
         msg.report_publish(499,'cp failed invocation of: %s ' % cmd )

      return False 


cp = CP(self)
self.do_download = cp.do_download

"""
  APPLICATION NOTES:

    - The built-in downloading logic is pretty good in almost all cases. It is rarely adviseable to use
      this functionality from a performance perspective.

    - Ideal use case:  LAN/Short-haul link with very high bandwidth, where lare peak i/o rates are achievable
      given adequate disk and network connections, such as a high speed LAN. Even there, it should only
      be used for larger files.  

    - Where there is a large tree with many small files, it is very likely that the built-in downloader
      is more efficient than forking any other downloader because, in addition to saving the fork/exec/reap
      overhead, the built-in downloader preserves connections to be used for multiple downloads, so 
      connection establishement, log-in etc.. is not needed for every file. It is actually going
      to be about as efficient as possible for the small file case, as those overheads dominate
      the transfer time.
 
    - As a file gets bigger, the transfer time will eventually dominate the setup-time, and at that
      point, it can make sense to switch to a forking download. Experience with actual configurations
      is needed to pick a good threshold for that. Default of 10M is a reasonable first guess.

    - The native downloader does partitioning of files for passage through multiple pumps and is preferable
      for that case to avoid the 'capybara through an anaconda' syndrome. In cases 'dataless' transfers.
      Where the data does not traverse any pump, this is not a consideration.
     
    - For most long-haul use cases, the bounding constraint is the bandwidth on the link so again
      the built-in downloader is likely close to optimal. Partitioning of the file enables portions of it
      to be delivered and for post-processing tasks, such as anti-virus to overlap with the file transfer.
      when using alternate schemes wihout partitioning, one must await until the complet file has arrived.

"""
