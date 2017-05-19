#!/usr/bin/python3

"""
 poll_script: an sample do_poll option usage for sr_poll.
              run a script that produces a filename per line, post each one.

 options:

 poll_script_command
     command to run that emits a file name on it's own 1 file per line.
     Each line of output will be interpreted as a file name to be posted.

 
"""

import os,stat,time
import calendar

class POLL_SCRIPT(object): 


   def __init__(self,parent):
      if not hasattr(parent,'poll_script_command'):
         parent.poll_script_command= [ '/usr/bin/find', \
            '/local/home/peter/test/dd', '-type', 'f', '-print'  ]
      pass
          
   def perform(self,parent):
      logger = parent.logger
      msg    = parent.msg

      import subprocess

      cmd = parent.poll_script_command

      #logger.debug("poll_script msg inbound: %s " % vars(msg) )
      #logger.debug("poll_script parent inbound: %s " % vars(parent) )
      logger.debug("poll_script invoking: %s " % cmd )
      
      # run the shell script, for loop processes each line of output 
      #      as an absolute path to a file name.
      proc =  subprocess.Popen( cmd, stdout=subprocess.PIPE )
      
      for line in proc.stdout:
          fname = line.rstrip().decode("utf-8") 
          logger.debug("poll_script fname is: %s " % fname )

          msg.urlstr = parent.destination  + '/' + fname
          logger.debug("poll_script urlstr is: %s " % msg.urlstr )

          msg.url = urllib.parse.urlparse(msg.urlstr)

          fst = os.stat(fname)
          msg.partstr = '1,%s,1,0,0' % fst.st_size
          msg.sumstr  = '0,0'

          logger.debug(\
              "poll_script exchange: %s url: %s to_cluster: %s partstr: %s " \
              % (parent.exchange, msg.url, parent.to_clusters, msg.partstr) )
          ok = parent.poster.post(parent.exchange,msg.url,parent.to_clusters, msg.partstr,msg.sumstr)


      return True 


poll_script = POLL_SCRIPT(self)
self.do_poll = poll_script.perform

