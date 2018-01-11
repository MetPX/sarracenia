#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SarraDocumentation
#
# sr_retry.py : python3 standalone retry logic/testing
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  first shot     : Wed Jan 10 16:06:16 UTC 2018
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, 
#  but WITHOUT ANY WARRANTY; without even the implied warranty of 
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#

import os,json,sys,time

try :
         from sr_config          import *
         from sr_util            import *
except :
         from sarra.sr_config    import *
         from sarra.sr_util      import *

# class sr_retry

class sr_retry:
    def __init__(self, parent ):
        parent.logger.debug("sr_retry __init__")

        self.logger     = parent.logger
        self.parent     = parent

        self.retry_ttl  = self.parent.retry_ttl

        # message to work with

        self.message    = raw_message(self.logger)

        # initialize all retry path if retry_path is provided

        if hasattr(self.parent,'retry_path') : self.init()

    def add_msg_to_state_file(self,message,done=False):
        self.state_fp = self.msg_append_to_file(self.state_fp,self.state_path,message,done)
        if done : return
        self.logger.debug("confirmed added to the state list %s" % message.body)

    def add_msg_to_new_file(self,message):
        self.new_fp = self.msg_append_to_file(self.new_fp,self.new_path,message)
        self.logger.debug("confirmed added to the retry list %s" % message.body)

    def close(self):
        try   : self.new_fp.close()
        except: pass
        try   : self.retry_fp.close()
        except: pass
        try   : self.state_fp.close()
        except: pass
        self.new_fp   = None
        self.retry_fp = None
        self.state_fp = None

    def decode(self, line ):
        try:
            topic, headers, notice = json.loads(line)
        except:
            self.logger.error("corrupted line in retry file: %s " % line)
            return None

        self.message.delivery_info['exchange']         = self.parent.exchange
        self.message.delivery_info['routing_key']      = topic
        self.message.properties['application_headers'] = headers
        self.message.body                              = notice

        return self.message

    def encode(self, message, done=False ):
        topic   = message.delivery_info['routing_key']
        headers = message.properties['application_headers']
        notice  = message.body

        if type(notice) == bytes: notice = notice.decode("utf-8")

        if done: headers['_retry_tag_'] = 'done'

        json_line = json.dumps( [ topic, headers, notice ], sort_keys=True ) + '\n' 

        return json_line

    def get(self):

        self.retry_fp, message = self.msg_get_from_file(self.retry_fp, self.retry_path)

        # FIXME MG as discussed with Peter
        # no heartbeat in get ...
        # if no message (and new or state file there)
        # we wait for heartbeat to present retry messages
        if not message : return None

        # go to next valid
        while self.is_expired(message):
              self.add_msg_to_state_file(message,done=True)
              self.retry_fp, message = self.msg_get_from_file(self.retry_fp, self.retry_path)
              if not message : return None

        self.message.isRetry = True

        return self.message

    def init(self):

        # retry messages

        self.retry_path = self.parent.retry_path
        self.retry_fp   = None

        # newer retries

        self.new_path   = self.parent.retry_path + '.new'
        self.new_fp     = None

        # state retry messages

        self.state_path = self.parent.retry_path + '.state'
        self.state_fp   = None

        # working file at heartbeat

        self.heart_path = self.parent.retry_path + '.heart'
        self.heart_fp   = None

    def is_done(self,message):
        headers = message.properties['application_headers']
        done    = '_retry_tag_' in headers and headers['_retry_tag_'] == 'done'

        if done : self.logger.debug("done    retry message skipped %s (heartbeat)" % message.body)
        return done

    def is_expired(self,message):
        # no expiry
        if self.retry_ttl == None: return False
        if self.retry_ttl <= 0   : return False

        # compute message age
        notice   = message.body
        parts    = notice.split()
        msg_time = timestr2flt(parts[0])
        msg_age  = time.time() - msg_time

        # expired ?

        expired = msg_age > self.retry_ttl

        if expired : self.logger.debug("expired retry message skipped %s" % notice)
        self.logger.debug("message is %d seconds old, retry_ttl is %d" % (msg_age, self.retry_ttl ) )

        return expired

    def msg_append_to_file(self,fp,path,message,done=False):
        if fp == None :
           present = os.path.isfile(path)
           if not present : fp = open(path,'w')
           else           :
                            fp = open(path,'r+')
                            fp.seek(0,2)

        line = self.encode(message,done)

        fp.write( line )
        fp.flush()
        os.fsync(fp)

        return fp

    def msg_get_from_file(self,fp,path):
        if fp == None :
           if not os.path.isfile(path) : return None,None
           fp = open(path,'r')

        line = fp.readline()
        if not line :
           try   : fp.close()
           except: pass
           try   : os.unlink(path)
           except: pass
           return None,None

        msg = self.decode(line)

        return fp,msg

    def msg_transfer_retry_to_state(self):
        if self.retry_fp == None : return

        while True:
            msg = self.get()
            if not msg : break
            self.add_msg_to_state_file(msg)

    def on_heartbeat(self,parent):

        # flush remaining of retry messages in state file

        self.msg_transfer_retry_to_state()

        # close all files
        self.close()

        # state -> heartbeat file

        last_notice = None

        while True:
              self.state_fp, message = self.msg_get_from_file(self.state_fp, self.state_path)
              if not message : break
              last_notice = message.body
              if self.is_done(message)   : continue
              if self.is_expired(message): continue
              self.heart_fp = self.msg_append_to_file(self.heart_fp,self.heart_path,message)

        try   : close(self.heart_fp)
        except: pass
        self.heart_fp   = None

        # retry -> heartbeat file

        while True:
              self.retry_fp, message = self.msg_get_from_file(self.retry_fp, self.retry_path)
              if not message : break
              if last_notice and message.notice != last_notice : continue
              self.heart_fp = self.msg_append_to_file(self.heart_fp,self.heart_path,message)

        try   : close(self.heart_fp)
        except: pass
        self.heart_fp   = None

        # new -> heartbeat file

        while True:
              self.new_fp, message = self.msg_get_from_file(self.new_fp, self.new_path)
              if not message : break
              self.heart_fp = self.msg_append_to_file(self.heart_fp,self.heart_path,message)

        try   : close(self.heart_fp)
        except: pass
        self.heart_fp   = None

        # heartbeat file becomes new retry

        try   : os.rename(self.heart_path,self.retry_path)
        except: pass

# ===================================
# self_test
# ===================================

class test_logger:
      def silence(self,str):
          pass
      def terror(self,str):
          print("ERROR %s" % str)

      def __init__(self):
          self.debug   = self.silence
          self.error   = self.terror
          self.info    = self.silence
          self.warning = self.silence

# test encode/decode
def test_retry_encode_decode(retry,message,done=False):

    if done : line  = retry.encode(message,done)
    else    : line  = retry.encode(message)
    msg   = retry.decode(line)

    if msg.body != message.body :
       retry.logger.error("encode_decode body (done %s)" % done)

    if msg.delivery_info['exchange'] != message.delivery_info['exchange'] :
       retry.logger.error("encode_decode exchange (done %s)" % done)

    if msg.delivery_info['routing_key'] != message.delivery_info['routing_key'] :
       retry.logger.error("encode_decode routing_key (done %s)" % done)

    if msg.properties['application_headers']['my_header_attr'] != \
       message.properties['application_headers']['my_header_attr']:
       retry.logger.error("encode_decode headers (done %s)" % done)

    if not done : return

    if not '_retry_tag_' in msg.properties['application_headers'] :
       retry.logger.error("encode_decode retry_tag not present")

    if '_retry_tag_' in msg.properties['application_headers'] and \
       msg.properties['application_headers']['_retry_tag_'] != 'done':
       retry.logger.error("encode_decode retry_tag != done")

    # test is_done

    if not retry.is_done(msg):
       retry.logger.error("encode_decode is_done method")

    return

# test is_expired methods
def test_retry_is_expired(retry,message):

    retry.retry_ttl = 100000

    if retry.is_expired(message):
       retry.logger.error("is_expired expires too soon ")

    time.sleep(1)
    retry.retry_ttl = 1

    if not retry.is_expired(message):
       retry.logger.error("is_expired should have expired ")

    retry.retry_ttl = 100000

# test msg_append_get_file
def test_retry_msg_append_get_file(retry,message):
    i  = 0 
    fp = None

    path = retry.retry_path

    while i < 100 :
          i = i+1
          r = i%2

          message.body = '%s xyz://user@host /my/terrible/path%.10d' % (timeflt2str(time.time()),i)

          # message to retry
          if r == 0 : fp = retry.msg_append_to_file(fp,path,message)

          # message done
          else:       fp = retry.msg_append_to_file(fp,path,message,True)

          try   : del message.properties['application_headers']['_retry_tag_']
          except: pass

          # make sure close/append works for every entry
          fp.close()
          fp = None

    # test msg_get_from_file : read previous mixed message

    r = 0
    d = 0
    t = 0
    while True :

          fp, msg = retry.msg_get_from_file(fp,path)
          if not msg : break
          if retry.is_done(msg): d = d + 1
          else                 : r = r + 1
          t = t + 1

    if t != 100: retry.logger.error("append_get file incomplete (%d/100)" % t)
    if d != 50 : retry.logger.error("append_get should have 50 done (%d/100)" % d) 
    if r != 50 : retry.logger.error("append_get should have 50 todo (%d/100)" % r)

    # at end file is unlinked and fp is none

    if os.path.isfile(path) : retry.logger.error("append_get retry_path should have been deleted")

    if fp != None : retry.logger.error("append_get returned file pointer should have been None")

# test retry_get simple
def test_retry_get_simple(retry,message):

    # first case... retry.get with nothing

    if retry.get(): retry.logger.error("append_get retry.get message should be None")

    # second case... retry.get with 3 retry messages

    fp   = None
    path = retry.retry_path
    i    = 0 
    while i < 3 :
          i = i+1
          message.body = '%s xyz://user@host /my/terrible/path%.10d' % (timeflt2str(time.time()),i)
          fp = retry.msg_append_to_file(fp,path,message)
    fp.close()

    # read them in
    t = 0
    while True :
          msg = retry.get()
          if not msg : break
          t = t + 1

    if t != 3 : retry.logger.error("get simple problem reading 3 retry messages")

    if os.path.isfile(path): retry.logger.error("get simple complete reading implies unlink")

# overall case
def test_retry_overall(retry,message):

    # retry file has 10 messages...  half fails   ... and every 4 messages processed one new added
    # on_heartbeat every time needed

    # add 10 messages to retry file
    fp        = None
    msg_count = 0 
    while msg_count < 10 :
          message.body = '%s xyz://user@host /my/terrible/path%.10d' % (timeflt2str(time.time()),msg_count)
          fp = retry.msg_append_to_file(fp,retry.retry_path,message)
          msg_count = msg_count + 1
    fp.close()

    # read them with half success

    i       = 0
    h_done  = 1 # heartbeat done
    h_count = 0 # heartbeat count
    d_count = 0 # done      count
    f_count = 0 # failed    count
    while True :
          msg = retry.get()

          # heartbeat or done
          if not msg :
             if h_done : break
             retry.on_heartbeat(retry.parent)
             h_count = h_count + 1
             h_done  = 1
             continue
          h_done = 0

          # processing another message
          i = i+1

          # success or fail
          r = i%2
          if r == 1 :
             retry.add_msg_to_state_file(msg)
             f_count = f_count + 1
          else :
             retry.add_msg_to_state_file(msg,done=True)
             d_count = d_count + 1

          # every 4 success add a new retry
          r = i % 4
          if r == 0 :
             try   : del message.properties['application_headers']['_retry_tag_']
             except: pass
             message.body = '%s xyz://user@host /my/terrible/path%.10d' % (timeflt2str(time.time()),msg_count)
             retry.add_msg_to_new_file(message)
             msg_count = msg_count + 1

    # msg_count != done d_count ...

    if msg_count != d_count :
        retry.logger.error("overall count failed msg_count %d  done_count %d ( failed %d, heartb %d)" % \
       (msg_count,d_count,f_count,h_count))

    if os.path.isfile(retry.retry_path) :  retry.logger.error("overall retry_path completely read, should have been deleted")


# ctrl_c case
def test_retry_ctrl_c(retry,message):

    # retry file has 10 messages...  half fails   ... and every 4 messages processed one new added
    # on_heartbeat every time needed

    # add 10 messages to retry file
    fp        = None
    msg_count = 0 
    while msg_count < 10 :
          message.body = '%s xyz://user@host /my/terrible/path%.10d' % (timeflt2str(time.time()),msg_count)
          fp = retry.msg_append_to_file(fp,retry.retry_path,message)
          msg_count = msg_count + 1
    fp.close()

    # read them with half success

    i       = 0
    h_done  = 1 # heartbeat done
    h_count = 0 # heartbeat count
    d_count = 0 # done      count
    f_count = 0 # failed    count
    a_count = 0 # added     count when 4  ctrl_c
    while True :
          msg = retry.get()

          # heartbeat or done
          if not msg :
             if h_done : break
             retry.on_heartbeat(retry.parent)
             h_count = h_count + 1
             h_done  = 1
             continue
          h_done = 0

          # processing another message
          i = i+1

          # success or fail
          r = i%2
          if r == 1 :
             retry.add_msg_to_state_file(msg)
             f_count = f_count + 1
          else :
             retry.add_msg_to_state_file(msg,done=True)
             d_count = d_count + 1

          # every 4 success add a new retry
          r = i % 4
          if r == 0 :
             try   : del message.properties['application_headers']['_retry_tag_']
             except: pass
             message.body = '%s xyz://user@host /my/terrible/path%.10d' % (timeflt2str(time.time()),msg_count)
             retry.add_msg_to_new_file(message)
             msg_count = msg_count + 1
             a_count   = a_count + 1
             if a_count == 1 : break

    # ctrl_c heartbeat
    retry.on_heartbeat(retry.parent)

    # start same loop
    while True :
          msg = retry.get()

          # heartbeat or done
          if not msg :
             if h_done : break
             retry.on_heartbeat(retry.parent)
             h_count = h_count + 1
             h_done  = 1
             continue
          h_done = 0

          # processing another message
          i = i+1

          # success or fail
          r = i%2
          if r == 1 :
             retry.add_msg_to_state_file(msg)
             f_count = f_count + 1
          else :
             retry.add_msg_to_state_file(msg,done=True)
             d_count = d_count + 1

          # every 4 success add a new retry
          r = i % 4
          if r == 0 :
             try   : del message.properties['application_headers']['_retry_tag_']
             except: pass
             message.body = '%s xyz://user@host /my/terrible/path%.10d' % (timeflt2str(time.time()),msg_count)
             retry.add_msg_to_new_file(message)
             msg_count = msg_count + 1
             

    # msg_count != done d_count ...

    if msg_count != d_count :
        retry.logger.error("ctrl_c count failed msg_count %d  done_count %d ( failed %d, heartb %d)" % \
       (msg_count,d_count,f_count,h_count))

    if os.path.isfile(retry.retry_path) :  retry.logger.error("ctrl_c retry_path completely read, should have been deleted")

def self_test():

    retry_path = '/tmp/retry'
    try   : os.unlink(retry_path)
    except: pass
    try   : os.unlink(retry_path+'.new')
    except: pass
    try   : os.unlink(retry_path+'.state')
    except: pass
    try   : os.unlink(retry_path+'.heart')
    except: pass

    logger = test_logger()

    #setup retry parent
    cfg = sr_config()
    cfg.defaults()
    cfg.logger         = logger
    cfg.debug          = True
    cfg.retry_path     = retry_path

    headers = {}
    headers['my_header_attr'] = 'my_header_attr_value'

    notice = '%s xyz://user@host /my/terrible/path%.10d' % (timeflt2str(time.time()),0)

    message = raw_message(logger)

    message.delivery_info['exchange']         = cfg.exchange
    message.delivery_info['routing_key']      = 'my_topic'
    message.properties['application_headers'] = headers
    message.body                              = notice

    retry = sr_retry(cfg)

    # test encode decode methods

    test_retry_encode_decode(retry,message)
    test_retry_encode_decode(retry,message,done=True)

    # test is_expired methods

    test_retry_is_expired(retry,message)

    # test msg_append_to_file : write 100 message to a file

    test_retry_msg_append_get_file(retry,message)

    # test get simplest cases

    test_retry_get_simple(retry,message)

    # test complex case no interrup
    test_retry_overall(retry,message)

    # test ctrl_c
    test_retry_ctrl_c(retry,message)

    # test close

    retry.close()

    sys.exit(0)

# ===================================
# MAIN
# ===================================

def main():

    self_test()
    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()
