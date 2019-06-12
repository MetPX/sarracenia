#!/usr/bin/python3

"""
This plugin should be used in a sr_sender 
It registeres for ftp/sftp 
and does nothing but logging the sending message
as if it was a sundew pxSender process

No files are actually being sent

Sample usage:

  plugin pxSender_log.py

The purpose is to prepare sr_sender configurations
and just log as a pxSender process to verify that
the conversion was correct

Bash scripds can be run on logs to make sure all products
and renaming were addressed properly

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

       self.pxSender_print(parent,src,dest)

       return True

   def do_send(self,parent):
       msg    = parent.msg

       src  = parent.document_root + msg.relpath
       src  = src.replace(' ','\ ')

       dest = parent.destination + msg.new_dir + os.sep + msg.new_file

       self.pxSender_print(parent,src,dest)

       return True

   def pxSender_print(self,parent,src,dest):
       logger = parent.logger
       msg    = parent.msg
       
       if msg.headers['sum'][0] == 'L' : return True
       if msg.headers['sum'][0] == 'R' : return True

       # file size
       parts = msg.partstr.split(',')
       if parts[0] == '1':
           sz=int(parts[1])
       else:
           sz=int(parts[1])*int(parts[2])

       logger.info("(%d Bytes) File %s delivered to %s (lat=0.1,speed=0.1)",sz,src,dest)

   def registered_as(self) :
       return self.registered_list

self.plugin='PXSENDER_LOG'
