#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
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
#  the Free Software Foundation; version 2 of the License.
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
from _codecs import decode, encode

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
        #self.logger.debug("DEBUG add to state file %s %s %s" % (os.path.basename(self.state_path),message.body,done))
        self.state_fp = self.msg_append_to_file(self.state_fp,self.state_path,message,done)
        # performance issue... only do before close
        #os.fsync(self.state_fp)

    def add_msg_to_new_file(self,message):
        #self.logger.debug("DEBUG add to new file %s %s" % (os.path.basename(self.new_path),message.body))
        self.new_fp = self.msg_append_to_file(self.new_fp,self.new_path,message)
        # performance issue... only do before close
        #os.fsync(self.new_fp)

    def cleanup(self):

        if os.path.exists(self.parent.retry_path):
            os.unlink(self.parent.retry_path)

        if hasattr(self.parent,'retry_work') : 
            if os.path.exists(self.parent.retry_work):
                os.unlink(self.parent.retry_work)


    def close(self):
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

    def msgFromJSON(self, line ):
        try:
            topic, headers, notice  = json.loads(line)
        except ValueError:
            self.logger.error("corrupted line in retry file: %s " % line)
            self.logger.debug("Error information: ", exc_info=True)
            return None

        self.logger.debug('Decoding msg from json: topic={}, headers={}, notice={}'.format(topic, headers, notice))
        self.message.delivery_info['exchange']         = self.parent.exchange
        self.message.delivery_info['routing_key']      = topic
        self.message.properties['application_headers'] = headers
        self.message.body                              = notice
        ( self.message.pubtime, self.message.baseurl, self.message.relpath ) = notice.split()

        return self.message

    def msgToJSON(self, message, done=False ):
        self.logger.debug('Encoding msg to json: message={}'.format(vars(message)))
        topic   = message.delivery_info['routing_key']

        if message.body[0] == '[' : # early v03 message to persist, 
           ( message.pubtime, message.baseurl, message.relpath, headers ) = json.loads( message.body )
           notice  = "%s %s %s" % ( message.pubtime, message.baseurl, message.relpath )
        elif message.body[0] == '{' : # late v03 message to persist, 
           headers = json.loads( message.body )
           message.pubtime = headers[ "pubTime" ]
           message.baseurl = headers[ "baseUrl" ]
           message.relpath = headers[ "relPath" ]
           notice  = "%s %s %s" % ( message.pubtime, message.baseurl, message.relpath )
           if 'integrity' in headers.keys():
               # v3 has no sum, must add it here
               sum_algo_map = { "a":"arbitrary", "d": "md5", "s": "sha512", "n": "md5name", 
                                "0": "random", "L": "link", "R": "remove", "z": "cod" }
               sum_algo_map = {v: k for k, v in sum_algo_map.items()}
               sumstr = sum_algo_map[headers['integrity']['method']]
               if sumstr == '0':
                   sumstr = '{},{}'.format(sumstr, headers['integrity']['value'])
               elif sumstr == 'z':
                   sumstr = '{},{}'.format(sumstr, sum_algo_map[headers['integrity']['value']])
               else:
                   decoded_value = encode(decode(headers['integrity']['value'].encode('utf-8'), 'base64'),
                                          'hex').decode('utf-8').strip()
                   sumstr = '{},{}'.format(sumstr, decoded_value)
               headers['sum'] = sumstr
               del headers['integrity']
           if 'size' in headers.keys():
               parts_map = {'inplace': 'i', 'partitioned': 'p'}
               if 'blocks' not in headers.keys():
                   partstr = "%s,%s,%s,%s,%s" % ('1', headers['size'], '1', '0', '0')
               else:
                   partstr = "%s,%s,%s,%s,%s" % (parts_map[headers['blocks']['method']], headers['blocks']['size'],
                                                 headers['blocks']['count'], headers['blocks']['remainder'],
                                                 headers['blocks']['number'])
                   del headers['blocks']
               del headers['size']
               headers['parts'] = partstr
        else:
           headers = message.properties['application_headers']
           if type(message.body) == bytes:
               notice = message.body.decode("utf-8")
           else:
               notice = message.body

        if done:
            headers['_retry_tag_'] = 'done'
        return json.dumps([topic, headers, notice], sort_keys=True) + '\n'

    def get(self):
        ok = False

        while not ok :
              ok, message = self.get_retry()

        return message

    def get_retry(self):
        self.retry_fp, message = self.msg_get_from_file(self.retry_fp, self.retry_path)

        # FIXME MG as discussed with Peter
        # no heartbeat in get ...
        # if no message (and new or state file there)
        # we wait for heartbeat to present retry messages
        if not message :
           try   : os.unlink(self.retry_path)
           except: pass
           self.retry_fp = None
           #self.logger.debug("MG DEBUG retry get return None")
           return True,None

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

    def in_cache(self,message):
        relpath = '/'.join(message.body.split()[1:])
        sumstr  = message.properties['application_headers']['sum']
        partstr = relpath
        if 'parts' in message.properties['application_headers'] :
            partstr = message.properties['application_headers']['parts']
        cache_key = relpath + ' ' + sumstr + ' ' + partstr
        if cache_key in self.retry_cache : return True
        self.retry_cache[cache_key] = True
        return False

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
        msg_time = timestr2flt(message.pubtime)
        msg_age  = time.time() - msg_time

        # expired ?

        expired = msg_age > (self.retry_ttl/1000)

        #self.logger.debug("DEBUG message is %d seconds old, retry_ttl is %d" % (msg_age, self.retry_ttl ) )

        return expired

    def is_valid(self,message):
        # validation

        # log is info... it is good to log a retry message that expires
        if self.is_expired(message):
           self.logger.info("expired message skipped %s" % message.body)
           return False

        # log is debug... the retry message was processed
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
                            #fp = open(path,'r+')
                            #fp.seek(0,2)
                            fp = open(path,'a')

        try:
           line = self.msgToJSON(message,done)
           fp.write( line )
           fp.flush()
        except:
           self.logger.error("failed to serialize message to JSON: %s" % message.body)
           self.logger.debug('Exception details:', exc_info=True)
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

        msg = self.msgFromJSON(line)
        # a corrupted line : go to the next
        if msg == None : return self.msg_get_from_file(fp,path)

        return fp,msg

    def on_heartbeat(self,parent):
        self.logger.info("sr_retry on_heartbeat")

        # finish retry before reshuffling all retries entries

        if os.path.isfile(self.retry_path) and self.retry_fp != None : 
           self.logger.info("sr_retry resuming with retry file")
           return

        now               = time.time()
        self.retry_cache  = {}
        N    = 0

        # put this in try/except in case ctrl-c breaks something

        try:
             self.close()
             try   : os.unlink(self.heart_path)
             except: pass
             fp = open(self.heart_path,'w')
             fp.close()

             # rename to working file to avoid corruption

             if not os.path.isfile(self.retry_work) :
                if os.path.isfile(self.retry_path) : 
                    os.rename(self.retry_path,self.retry_work)
                else:
                    fp = open(self.retry_work,'w')
                    fp.close()

             if not os.path.isfile(self.state_work):
                if os.path.isfile(self.state_path) : 
                    os.rename(self.state_path,self.state_work)
                else:
                    fp = open(self.state_work,'w')
                    fp.close()

             if not os.path.isfile(self.new_work):
                if os.path.isfile(self.new_path) : 
                    os.rename(self.new_path,self.new_work)
                else:
                    fp = open(self.new_work,'w')
                    fp.close()

             # state to heart

             #self.logger.debug("MG DEBUG has state %s" % os.path.isfile(self.state_path))
     
             i    = 0
             last = None

             fp   = None
             while True:
                   fp, message = self.msg_get_from_file(fp, self.state_work)
                   if not message : break
                   i = i + 1
                   #self.logger.debug("DEBUG message %s" % vars(message))
                   if self.in_cache(message): continue
                   valid = self.is_valid(message)
                   if not valid: continue

                   #self.logger.debug("DEBUG flush retry to state %s" % message.body)
                   self.heart_fp = self.msg_append_to_file(self.heart_fp,self.heart_path,message)
                   N = N + 1
             try   : fp.close()
             except: pass

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
                   #self.logger.debug("DEBUG message %s" % vars(message))
                   if self.in_cache(message): continue
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

                   if self.in_cache(message): continue
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
                self.logger.error("sr_retry/on_heartbeat: something went wrong")
                self.logger.debug('Exception details: ', exc_info=True)

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

