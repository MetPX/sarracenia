#!/usr/bin/python3

"""
 poll_script: an sample do_poll option usage for sr_poll.
              run a script that produces a filename per line, post each one.

 usage:
     in an sr_poll configuration file:

 poll_script_command  /usr/bin/find /tmp -type f -print
 do_poll poll_script.py

 options:

 poll_script_command
     command to run that emits a file name on it's own 1 file per line.
     Each line of output will be interpreted as a file name to be posted.


example:
   poll_script_command find /home/peter/test -type f -print

what shows up in sr_poll log:
2017-05-19 07:58:16,354 [INFO] post_log notice=20170519115816.355 sftp://peter@localhost//home/peter/test/nws/ddsr1.cmc.ec.gc.ca/20170126/nws-internet/2canada/bulletins_normal_priority/170126140923_0615,09e93cc4-e3d1-11e6-a204-000000000000,228,20170126140923 headers={'from_cluster': 'localhost', 'sum': '0,0', 'parts': '1,195,1,0,0', 'to_clusters': 'ALL'}
2017-05-19 07:58:16,355 [INFO] post_log notice=20170519115816.355 sftp://peter@localhost//home/peter/test/nws/ddsr1.cmc.ec.gc.ca/20170126/nws-internet/2canada/bulletins_normal_priority/170126141014_0669,27efe290-e3d1-11e6-8009-000000000000,228,20170126141014 headers={'from_cluster': 'localhost', 'sum': '0,0', 'parts': '1,9236,1,0,0', 'to_clusters': 'ALL'}
^

 
"""

import os,stat,time
import calendar

class POLL_SCRIPT(object): 


   def __init__(self,parent):
      if not hasattr(parent,'poll_script_command'):
         parent.poll_script_command= [ '/usr/bin/find', '/tmp', '-type', 'f', '-print'  ]
      else:
         if ' ' in parent.poll_script_command[0]:
             parent.poll_script_command = parent.poll_script_command[0].split(' ')
      pass
          
   def perform(self,parent):
      logger = parent.logger
      msg    = parent.msg

      import subprocess
      try:
           from sr_util import timestr2flt
      except:
           from sarra.sr_util import timestr2flt



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
          mtimestr = timeflt2str(fst.st_mtime)
          atimestr = timeflt2str(fst.st_atime)

          logger.debug(\
              "poll_script exchange: %s url: %s to_cluster: %s partstr: %s " \
              % (parent.exchange, msg.url, parent.to_clusters, msg.partstr) )
          ok = parent.post(parent.exchange,parent.destination,fname,parent.to_clusters, msg.partstr,msg.sumstr, \
               mtime=mtimestr, atime=atimestr)


      return True 


poll_script = POLL_SCRIPT(self)
self.do_poll = poll_script.perform

