#!/usr/bin/python3

"""

This plugin a copy of Michel's pxSender_log.py
It IS ONLY LOGGING  NO DOWNLOAD, NO SEND

It provides a do_download to use in sr_subscribe
It provides a do_send     to use in sr_sender

And the announcement is restricted to http,ftp,sftp
it will only LOG

This interest of this plugin is that the log format is
similar to sundew's pxSender

The main purpose of this plugin is to have a tool to 
simulate the routing of products with sarra, without sending
anything.

No files are actually being sent or downloaded

Sample usage:

  simulate on 

(does a load of this plugin secretly)

This is restricted to a mean to verify between logs of sundew
and logs on sarra... when the download or delivery of the products
are exactly the same on both side, taking out the plugin should
simply do the job... and let go of the sundew config

The simulate on option disables checks for existence of files and
directories, which might not exist when not actually transferring files.

"""

import os,stat,time,sys
import calendar

class PXSENDER_LOG(object): 

   import urllib.parse

   def __init__(self,parent):
       self.registered_list = [ 'http', 'ftp','sftp' ]

   def do_download(self,parent):
       parent.on_file_list = []
       msg    = parent.msg

       src  = msg.baseurl + ':' + msg.relpath
       src  = src.replace(' ','\ ')

       dest = msg.new_dir + os.sep + msg.new_file

       logger.info("downloaded to: %s " % msg.new_dir + os.sep + msg.new_file )
       return True

   def registered_as(self) :
       return self.registered_list

   def do_send(self,parent):
       msg    = parent.msg
       logger = parent.logger

       src  = parent.base_dir + msg.relpath
       src  = src.replace(' ','\ ')

       dest = parent.destination + msg.new_dir + os.sep + msg.new_file

       if msg.headers['sum'][0] == 'L' : return True
       if msg.headers['sum'][0] == 'R' : return True

       # file size
       parts = msg.partstr.split(',')
       if parts[0] == '1':
           sz=int(parts[1])
       else:
           sz=int(parts[1])*int(parts[2])

       # 
       # PX logger.info("(%d Bytes) File %s delivered to %s (lat=0.1,speed=0.1)",sz,src,dest)
       #logger.info("(%d Bytes) File %s delivered to %s (lat=0.1,speed=0.1)",sz,src,dest)

       # SR Sends: JAX_NVL:NOAAPORT2:CMC:RADAR_US:BIN:20220113212655  into //space/hall3/sitestore/eccc/cmod/prod/incoming/radar/ldm_data/radar/JAX/202201132126_NVL.nid 0-1317
       logger.info("Sends: %s into %s 0-%d",msg.new_file, msg.new_dir + os.sep + msg.new_file ,sz)
       return True

   def registered_as(self) :
       return self.registered_list

self.plugin='PXSENDER_LOG'
