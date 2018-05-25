#!/usr/bin/python3
"""

cp : an example do_download option usage.

This launches the UNIX 'cp' command with appropriate arguments to perform a file transfer.
This downloader expects to be invoked for the 'download' URL scheme is specified as a URL.
while the cp command is used by default, it can be overridden with the accel_cp_command option.

<options are placed before do_download in the configuration>

plugin accel_cp

Options:

Starting a subprocess is only faster if the size of the file is over a certain size.
The optimal threshold to depends on the environment and requires trial and error. 
Default is a good guess. 

  accel_cp_threshold 10M

Normally, the plugin replaces 'http' urls for files that exceed the threshold with 'download'
ones, which triggers use of the do_download plugin.  Can change with accel_cp_protocol option.

  accel_cp_protocol  'sftp'

  accel_cp_command /usr/bin/cp -p 

See wget plugin for a more fulsome description.
See end of file for more APPLICATION NOTES.

"""

import os,stat,time
import calendar

class ACCEL_CP(object): 

   import urllib.parse

   def __init__(self,parent):

      parent.declare_option( 'accel_cp_command' )
      parent.declare_option( 'accel_cp_threshold' )
      parent.declare_option( 'accel_cp_protocol' )


   def on_start(self,parent):

      if not hasattr(parent,'accel_cp_command'):
         parent.accel_cp_command= [ '/usr/bin/cp' ]

      if not hasattr( parent, "accel_cp_threshold" ):
             parent.accel_cp_threshold = [ "10M" ]

      if not hasattr( parent, "accel_cp_protocol" ):
             parent.accel_cp_protocol = [ "http" ]

      return True
          

   def on_message(self,parent):

      logger = parent.logger
      msg    = parent.msg

      if type(parent.accel_cp_threshold) is list:
          parent.accel_cp_threshold = parent.chunksize_from_str( parent.accel_cp_threshold[0] )

      if msg.headers['sum'][0] == 'L' or msg.headers['sum'][0] == 'R' : return True

      parts = msg.partstr.split(',')
      if parts[0] == '1':
          sz=int(parts[1])
      else:
          sz=int(parts[1])*int(parts[2])

      logger.debug("cp sz: %d, threshold: %d download: %s to %s, " % ( \
          sz, parent.accel_cp_threshold, parent.msg.urlstr, msg.new_file ) )
      if sz >= parent.accel_cp_threshold :
          for p in parent.accel_cp_protocol :
              parent.msg.urlstr = msg.urlstr.replace(p,"download")

          parent.msg.url = urllib.parse.urlparse(msg.urlstr)
          logger.info("cp triggering alternate method for: %s to %s, " % (parent.msg.urlstr, msg.new_file))

      return True


   def do_download(self,parent):
      logger = parent.logger
      msg    = parent.msg

      import subprocess

      # rebuild an scp compatible source specification from the provide url ( proto://user@host// --> user@host: )

      cmd = parent.accel_cp_command[0].split() + [ msg.url.path, msg.new_dir + os.sep + msg.new_file ] 

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

self.plugin='ACCEL_CP'


"""
  APPLICATION NOTES:

    - The built-in downloading logic is pretty good in almost all cases. It is rarely adviseable to use
      this functionality from a performance perspective. But there are cases where the speedup
      is significant.

    - Ideal use case:  LAN/Short-haul link with very high bandwidth, where lare peak i/o rates 
      are achievable given adequate disk and network connections, such as a high speed LAN. Even 
      there, it should only be used for larger files.  

    - Where there is a large tree with many small files, it is very likely that the built-in downloader
      is more efficient than forking any other downloader because, in addition to saving 
      the fork/exec/reap overhead, the built-in downloader preserves connections to be used 
      for multiple downloads, so connection establishement, log-in etc.. is not needed for 
      every file. It is actually going to be about as efficient as possible for the small 
      file case, as those overheads dominate the transfer time.
 
    - As a file gets bigger, the transfer time will eventually dominate the setup-time, and at that
      point, it can make sense to switch to a forking download. Experience with actual configurations
      is needed to pick a good threshold for that. Default of 10M is a reasonable first guess.

    - The native downloader does partitioning of files for passage through multiple pumps and 
      is preferable for that case to avoid the 'capybara through an anaconda' syndrome. In 
      cases 'dataless' transfers. Where the data does not traverse any pump, this is not 
      a consideration.
     
    - For most long-haul use cases, the bounding constraint is the bandwidth on the link so again
      the built-in downloader is likely close to optimal. Partitioning of the file enables 
      portions of it to be delivered and for post-processing tasks, such as anti-virus to 
      overlap with the file transfer. When using alternate schemes wihout partitioning, 
      one must await until the complete file has arrived.

"""
