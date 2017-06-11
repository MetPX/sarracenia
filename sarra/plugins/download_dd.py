#!/usr/bin/python3

"""
  download_dd: an example do_download option usage.

  This launches the 'dd' command with appropriate arguments to perform a file transfer.
  This is an example that understands inline-partitioned files.  The parts header is parsed,
  and a dd for each slice of the file is invoked.  The optimal file io blocksize can be selected 
  with *download_dd_blocksize*

  The stripe size (part of the file to assign to each dd invoked) is set by the post command.
  Matching post:

  sr_post -sum 0 -blocksize 512 -c ../A.conf poll_script.py

  (similarly could specify *blocksize* for sr_watch.)

  Sample usage:

  on_message msg_download

  download_dd_command /bin/dd 
  download_dd_blocksize 4k

  do_download download_dd

  
"""

import os,stat,time
import calendar

class DD_DOWNLOAD(object): 


   def __init__(self,parent):
      if not hasattr(parent,'download_dd_command'):
         parent.download_dd_command= [ "/bin/dd conv=sparse status=progress " ]

      if not hasattr(parent,'download_dd_blocksize'):
         parent.download_dd_blocksize= [ "4096" ]

      parent.download_dd_blocksize = int( parent.download_dd_blocksize[0] )
      pass
          
   def perform(self,parent):
      logger = parent.logger
      msg    = parent.msg

      import subprocess

      args = [ "if=%s" % msg.url.path, "of=%s" % msg.new_file, \
         "bs=%d" % parent.download_dd_blocksize ] 

      # parse 'parts' header to find slice to transfer.
      ( method, sz, nparts, rem, partnum ) = msg.headers[ 'parts' ].split(',')
      sz=int(sz)
      nparts=int(nparts)
      rem=int(rem)
      partnum=int(partnum)

      offset = ( sz * partnum )  / parent.download_dd_blocksize

      if ( method == 'i' ): 
          args += [ "skip=%d" % offset ]  # offset from start of output file.
          args += [ "seek=%d" % offset ]  # offset from start of input file.
          args += [ "count=%d" % ( sz / parent.download_dd_blocksize ) ] # number of blocks to transfer.

          if ( sz % parent.download_dd_blocksize ) != 0 :
              logger.error("download_dd partition size %d (from sr_post), must be divisible by blockize (from plugin option): %d " % (sz, parent.download_dd_blocksize) )
              return False


      cmd = parent.download_dd_command[0].split() + args

      logger.info("download_dd invoking: %s " % cmd )
      
      result =  subprocess.call( cmd )
      
      if (result == 0):  # Success!
         if parent.reportback:
            msg.report_publish(201,'Downloaded')
         if hasattr(parent,'chmod'):
            os.chmod(msg.new_file, parent.chmod)
         return True
         
      #Failure!

      if parent.reportback:
         msg.report_publish(499,'download_dd failed invocation of: %s ' % cmd )

      return False 


dd_download = DD_DOWNLOAD(self)
self.do_download = dd_download.perform

