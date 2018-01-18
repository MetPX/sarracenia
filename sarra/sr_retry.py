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

        self.activity   = True

        # message to work with

        self.message    = raw_message(self.logger)
        self.last_body  = None

        # initialize all retry path if retry_path is provided

        if hasattr(self.parent,'retry_path') : self.init()

    def add_msg_to_state_file(self,message,done=False):
        #self.logger.debug("DEBUG add to state file %s %s %s" % (os.path.basename(self.state_path),message.body,done))
        self.state_fp = self.msg_append_to_file(self.state_fp,self.state_path,message,done)
        # performance issue... only do before close
        #os.fsync(self.state_fp)

    def add_msg_to_new_file(self,message):
        #self.logger.debug("DEBUG add to new file %s %s" % (os.path.basename(self.new_path),message.body))
        self.new_fp = self.msg_append_to_file(self.new_fp,self.new_path,message)
        # performance issue... only do before close
        #os.fsync(self.new_fp)

    def close(self):
        self.last_body = None
        try   : self.heart_fp.close()
        except: pass
        try   :
                os.fsync(self.new_fp)
                self.new_fp.close()
        except: pass
        try   : self.retry_fp.close()
        except: pass
        try   : 
                os.fsync(self.state_fp)
                self.state_fp.close()
        except: pass
        self.heart_fp = None
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

        if done:
           headers = {}
           headers['_retry_tag_'] = 'done'

        json_line = json.dumps( [ topic, headers, notice ], sort_keys=True ) + '\n' 

        return json_line

    def get(self):
        ok = False

        while not ok :
              ok, message = self.get_retry()

        self.activity = True

        return message

    def get_retry(self):
        self.retry_fp, message = self.msg_get_from_file(self.retry_fp, self.retry_path)

        # FIXME MG as discussed with Peter
        # no heartbeat in get ...
        # if no message (and new or state file there)
        # we wait for heartbeat to present retry messages
        self.last_message = message

        if not message :
           try   : os.unlink(self.retry_path)
           except: pass
           self.retry_fp = None
           #self.logger.debug("MG DEBUG retry get return None")
           return True,None

        self.last_message = message.body

        # validation

        if not self.is_valid(message):
           #self.logger.error("MG invalid %s" % message.body)
           return False,None

        #self.logger.error("MG return %s" % message.body)
        message.isRetry = True

        return True,message

    def init(self):

        # retry messages

        self.retry_path = self.parent.retry_path
        self.retry_work = self.retry_path        + '.work'
        self.retry_fp   = None

        # newer retries

        self.new_path   = self.parent.retry_path + '.new'
        self.new_work   = self.new_path          + '.work'
        self.new_fp     = None

        # state retry messages

        self.state_path = self.parent.retry_path + '.state'
        self.state_work = self.state_path        + '.work'
        self.state_fp   = None

        # working file at heartbeat

        self.heart_path = self.parent.retry_path + '.heart'
        self.heart_fp   = None

    def is_done(self,message):
        headers = message.properties['application_headers']
        done    = '_retry_tag_' in headers and headers['_retry_tag_'] == 'done'

        #self.logger.debug("DEBUG retry message %s  DONE=%s" % (message.body,done))

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

        #self.logger.debug("DEBUG message is %d seconds old, retry_ttl is %d" % (msg_age, self.retry_ttl ) )

        return expired

    def is_valid(self,message):
        # validation

        if self.is_expired(message):
           self.logger.debug("expired message skipped %s" % message.body)
           return False

        if self.is_done(message):
           self.logger.debug("done message skipped %s" % message.body)
           return False

        return True

    def msg_append_to_file(self,fp,path,message,done=False):
        if fp == None :
           present = os.path.isfile(path)
           if not present :
                            fp = open(path,'w')
                            #self.logger.debug("DEBUG %s is created" % path)
           else           :
                            #self.logger.debug("DEBUG %s is appended" % path)
                            fp = open(path,'r+')
                            fp.seek(0,2)

        line = self.encode(message,done)

        fp.write( line )
        fp.flush()

        self.activity = True

        return fp

    def msg_get_from_file(self,fp,path):
        if fp == None :
           if not os.path.isfile(path) : return None,None
           #self.logger.debug("DEBUG %s open read" % path)
           fp = open(path,'r')

        line = fp.readline()
        if not line :
           try   : fp.close()
           except: pass
           return None,None

        msg = self.decode(line)
        # a corrupted line : go to the next
        if msg == None : return self.msg_get_from_file(fp,path)

        return fp,msg

    def on_heartbeat(self,parent):
        self.logger.info("sr_retry on_heartbeat")

        if not self.activity : return

        now          = time.time()
        marker_body  = self.last_body
        marker_valid = marker_body != None
        #self.logger.debug("marker_body1 = %s" % marker_body)

        # put this in try/except in case ctrl-c breaks something

        try:
             self.close()
             try   : os.unlink(self.heart_path)
             except: pass
             fp = open(self.heart_path,'w')
             fp.close()

             # rename to working file to avoid corruption

             if not os.path.isfile(self.retry_work) :
                fp = open(self.retry_work,'w')
                fp.close()
                if os.path.isfile(self.retry_path) : os.rename(self.retry_path,self.retry_work)

             if not os.path.isfile(self.state_work):
                fp = open(self.state_work,'w')
                fp.close()
                if os.path.isfile(self.state_path) : os.rename(self.state_path,self.state_work)

             if not os.path.isfile(self.new_work):
                fp = open(self.new_work,'w')
                fp.close()
                if os.path.isfile(self.new_path) : os.rename(self.new_path,self.new_work)

             # state to heart

             #self.logger.debug("MG DEBUG has state %s" % os.path.isfile(self.state_path))
     
             i    = 0
             N    = 0
             last = None

             fp   = None
             while True:
                   fp, message = self.msg_get_from_file(fp, self.state_work)
                   if not message : break
                   i = i + 1
                   last  = message.body
                   valid = self.is_valid(message)
                   if not valid: continue
                   #self.logger.debug("DEBUG flush retry to state %s" % message.body)
                   self.heart_fp = self.msg_append_to_file(self.heart_fp,self.heart_path,message)
                   N = N + 1
             try   : fp.close()
             except: pass

             if not marker_body and last :
                marker_body  = last
                marker_valid = valid
             #self.logger.debug("marker_body2 = %s" % marker_body)

             #self.logger.debug("MG DEBUG took %d out of the %d state" % (N,i))

             # remaining of retry to heart
     
             #self.logger.debug("MG DEBUG has retry %s" % os.path.isfile(self.retry_path))
     
             i   = 0
             j   = N

             fp   = None
             while True:
                   fp, message = self.msg_get_from_file(fp, self.retry_work)
                   if not message : break
                   i = i + 1
                   if marker_body :
                      if marker_body != message.body : continue
                      marker_body = None
                      continue
                   if not self.is_valid(message): continue
                   #self.logger.debug("MG DEBUG flush retry to state %s" % message.body)
                   self.heart_fp = self.msg_append_to_file(self.heart_fp,self.heart_path,message)
                   N = N + 1
             try   : fp.close()
             except: pass

             #self.logger.debug("MG DEBUG took %d out of the %d retry" % (N-j,i))
     
             # new to heart
     
             #self.logger.debug("MG DEBUG has new %s" % os.path.isfile(self.new_path))
     
             i   = 0
             j   = N

             fp   = None
             while True:
                   fp, message = self.msg_get_from_file(fp, self.new_work)
                   if not message : break
                   i = i + 1
                   if not self.is_valid(message): continue
                   #self.logger.debug("MG DEBUG flush retry to state %s" % message.body)
                   self.heart_fp = self.msg_append_to_file(self.heart_fp,self.heart_path,message)
                   N = N + 1
             try   : fp.close()
             except: pass
     
             #self.logger.debug("MG DEBUG took %d out of the %d new" % (N-j,i))
     
             # close heart
     
             try   : close(self.heart_fp)
             except: pass

        except:
                self.logger.error("on_heartbeat something went wrong")
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))

        # no more retry

        if N == 0 :
           self.logger.info("No retry in list")
           try   : os.unlink(self.heart_path)
           except: pass


        # heartbeat file becomes new retry

        else:
           self.logger.info("Number of messages in retry list %d" % N)
           try   : os.rename(self.heart_path,self.retry_path)
           except: 
                   self.logger.error("Something went wrong with rename")

        # cleanup
        try   : os.unlink(self.state_work)
        except: pass
        try   : os.unlink(self.retry_work)
        except: pass
        try   : os.unlink(self.new_work)
        except: pass

        self.last_body = None
        self.activity  = False
        elapse         = time.time()-now
        self.logger.info("sr_retry on_heartbeat elapse %f" % elapse)

    def on_start(self,parent):
        self.logger.info("sr_retry on_start")
        
        if not os.path.isfile(self.retry_path): return

        retry_age = os.stat(self.retry_path)[stat.ST_MTIME]

        if os.path.isfile(self.state_path):
           state_age = os.stat(self.state_path)[stat.ST_MTIME]
           if retry_age > state_age : os.unlink(self.state_path)

        if os.path.isfile(self.new_path):
           new_age = os.stat(self.new_path)[stat.ST_MTIME]
           if retry_age > new_age : os.unlink(self.new_path)

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

    if not done :

       if msg.properties['application_headers']['my_header_attr'] != \
          message.properties['application_headers']['my_header_attr']:
          retry.logger.error("encode_decode headers (done %s)" % done)

    if done :


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

    # at end file fp is none

    if fp != None : retry.logger.error("append_get returned file pointer should have been None")

    os.unlink(path)

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
             retry.logger.error("THIS heartbeat")
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
             if a_count == 2 : break

    # ctrl_c heartbeat
    
    retry.close()
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

    now   = time.time()

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
    e = time.time() - now

    print("test elapse = %f " % e)

    # performance test

    json_line = '["v02.post.sent_by_tsource2send", {"atime": "20180118151049.356378078", "from_cluster": "localhost", "mode": "644", "mtime": "20180118151048", "parts": "1,69,1,0,0", "source": "tsource", "sum": "d,c35f14e247931c3185d5dc69c5cd543e", "to_clusters": "localhost"}, "20180118151050.45 ftp://anonymous@localhost:2121 /sent_by_tsource2send/SXAK50_KWAL_181510___58785"]'

    i   = 0
    top = 100000
    now = time.time()
    while i<top:
          i = i+1
          topic, headers, notice = json.loads(json_line)
          json_line = json.dumps( [ topic, headers, notice ], sort_keys=True )

    e=time.time()-now
    print("json loads/dumps (%d) %f" % (i,e))

    retry.message.delivery_info['exchange']         = "test"
    retry.message.delivery_info['routing_key']      = topic
    retry.message.properties['application_headers'] = headers
    retry.message.body                              = notice

    i   = 0
    now = time.time()
    while i<top:
          i = i+1
          line  = retry.encode(message)
          msg   = retry.decode(line)

    e=time.time()-now
    print("json encode/decode not done (%d) %f" % (i,e))

    i   = 0
    now = time.time()
    while i<top:
          i = i+1
          line  = retry.encode(message,True)
          msg   = retry.decode(line)
          del msg.properties['application_headers']['_retry_tag_']

    e=time.time()-now
    print("json encode/decode done (%d) %f" % (i,e))

    fp  = None
    path= "/tmp/ftest1"
    try: os.unlink(path)
    except:pass

    i   = 0
    now = time.time()
    while i<top:
          i = i+1
          fp = retry.msg_append_to_file(fp,path,message)
    fp.close()

    e=time.time()-now
    print("msg_append_to_file (%d) %f" % (i,e))


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
