#!/usr/bin/python3
"""
  msg_2localfile:  this is a helper script to work with converters (filters) and senders.

  What a data pump advertises, it will usually use Web URL, but if one is
  on a server where the files are available, it is more efficient to access 
  them as local files, and so this plugin turn the message's notice Web URL
  into a File URL (file:/d1/d2/.../fn)
   
  Normal usage:

  A Web URL in an amqp message is hold in the following values:

  parent.msg.baseurl (ex.: http://localhost)  and
  parent.msg.relpath (ex.: /<data>/<src>/d3/.../fn)

  We will save these values before their modification :

  parent.msg.saved_baseurl = parent.msg.baseurl
  parent.msg.saved_relpath = parent.msg.relpath

  We will than turned them into an absolute File Url
  (Note if a base_dir was set it prefix the relpath)

  parent.msg.baseurl = 'file:'
  parent.msg.relpath = [base_dir] + parent.msg.relpath


  Example 

  base_dir /var/www/html

  message pubtime=20171003131233.494 baseurl=http://localhost relpath=/20171003/CMOE/productx.gif

  on_message msg_2localfile  
  -------------------------

     # will receive this

       parent.msg.baseurl  is  'http://localhost'
       parent.msg.relpath  is  '/20171003/CMOE/GIF/productx.gif'

     # will copy/save these values

       parent.msg.saved_baseurl = parent.msg.baseurl
       parent.msg.saved_relpath = parent.msg.relpath

     # turn the original values into a File URL

       parent.msg.baseurl = 'file:'

       if parent.base_dir :
          parent.msg.relpath = parent.base_dir + '/' + parent.msg.relpath
          parent.msg.relpath = parent.msg.relpath.replace('//','/')


  A sequence of on_message plugins can perform various changes to the message and/or
  to the product...  so here lets pretend we have an on_message plugin that converts
  gif to png  and prepare the proper message for it

  on_message msg_gif2png
  ----------------------

  After the msg_2localfile this script could performed something like:

  # build the absolute path of the png product

  new_path = parent.msg.relpath.replace('GIF','PNG')
  new_path[-4:] = '.png'

  # proceed to the conversion gif2png

  ok = self.gif2png(gifpath=parent.msg.relpath,pngpath=new_path)

  # change the message to announce the new png product

  if ok :
     parent.msg.baseurl = parent.msg.saved_baseurl
     parent.msg.relpath = new_path
     if parent.base_dir :
        parent.msg.relpath = new_path.replace(parent.base_dir,'',1)

  else :
     parent.logger.error(...
     return False

  # we are ok... proceed with this png file

  return True

"""

class Msg_2LocalFile():

    def __init__(self,parent):
        self.parent = parent

    def on_message(self,parent):
        l = parent.logger
        m = parent.msg

        if m.baseurl == 'file:' : return True

        m.saved_baseurl = m.baseurl
        m.saved_relpath = m.relpath

        m.baseurl = 'file:'
       
        if parent.base_dir and not m.relpath.startswith(parent.base_dir) :
           m.relpath = parent.base_dir + '/' + m.relpath
           m.relpath.replace('//','/')

        return True

msg_2localfile=Msg_2LocalFile(None)

self.on_message=msg_2localfile.on_message
