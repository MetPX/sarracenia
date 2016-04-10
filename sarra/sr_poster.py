#!/usr/bin/python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SarraDocumentation
#
# sr_poster.py : python3 wraps for publishing products
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  first shot     : Dec 23 12:30:53 EST 2015
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

import os,sys,random,shelve

try :    
         from sr_amqp           import *
         from sr_config         import *
         from sr_message        import *
         from sr_util           import *
except : 
         from sarra.sr_amqp     import *
         from sarra.sr_config   import *
         from sarra.sr_message  import *
         from sarra.sr_util     import *

# class sr_poster

class sr_poster:

    def __init__(self, parent, loop=True):
        self.logger         = parent.logger
        self.logger.debug("sr_poster __init__")
        self.parent         = parent
        self.loop           = loop
        self.cache          = None

        self.broker         = parent.post_broker
        self.topic_prefix   = parent.topic_prefix
        self.subtopic       = parent.subtopic
        self.bufsize        = parent.bufsize
        self.caching        = parent.caching
        self.batch          = parent.batch

        self.build_connection()
        self.build_publisher()
        self.get_message()

        # total = 1 sec span than .5 for other iteration
        self.sleep_list = [0.01,0.03,0.06,0.15,0.25,0.5]
        self.sleep_idx  = 0
        self.sleep_max  = 5

    def build_connection(self):
        self.logger.debug("sr_poster build_broker")

        self.logger.info("Output AMQP  broker(%s) user(%s) vhost(%s)" % \
                        (self.broker.hostname,self.broker.username,self.broker.path) )

        self.hc      = HostConnect( logger = self.logger )
        self.hc.loop = self.loop
        self.hc.set_url(self.broker)
        self.hc.connect()

    def build_publisher(self):
        self.logger.debug("sr_poster build_publisher")

        self.publisher = Publisher(self.hc)
        self.publisher.build()

    def cache_close(self):
        self.logger.debug("sr_poster cache_close")
        self.logger.debug("sr_poster caching %s" % self.caching)
        self.logger.debug("sr_poster cache %s" % self.cache)
        if not self.caching   : return
        if self.cache == None : return
        #self.logger.debug("save cache and release lock")
        self.logger.debug("save cache")
        self.cache.close()
        #os.unlink(self.cache_lock)
        self.cache = None

    def cache_files_set(self):
        self.logger.debug("sr_poster cache_files_set")

        self.cache_file = None
        #self.cache_lock = None

        if not hasattr(self.parent,'watch_path') : 
           self.logger.error("could not cache posting... no watch_path")
           self.caching = False
           return

        if self.parent.blocksize == 0: 
           self.logger.error("could not cache posting... no fix blocksize")
           self.caching = False
           return

        self.cache_file  = self.parent.user_cache_dir 
        self.cache_file += '/' + self.parent.watch_path.replace('/','_')
        self.cache_file += '_%d' % self.parent.blocksize

        #self.cache_lock  = self.cache_file + '.lck'


    def cache_reset(self):
        self.logger.debug("sr_poster cache_reset")

        self.cache_files_set()
        self.logger.debug("cache_file = %s" % self.cache_file)
        #self.logger.debug("cache_lock = %s" % self.cache_lock)

        # unfortunately have to try several implementation extensions...
        if self.cache_file:
           try   : os.unlink(self.cache_file)
           except: pass
           try   : os.unlink(self.cache_file+'.pag')
           except: pass
           try   : os.unlink(self.cache_file+'.dir')
           except: pass
           try   : os.unlink(self.cache_file+'.db')
           except: pass
           try   : os.unlink(self.cache_file+'.dat')
           except: pass

        #if self.cache_lock:
        #   try   : os.unlink(self.cache_lock)
        #   except: pass

        self.logger.info("posting cache was reset...")

        os._exit(0)


    def cache_load(self):
        self.logger.debug("sr_poster cache_load")
        if not self.caching : return

        self.cache_files_set()
        self.logger.debug("cache_file = %s" % self.cache_file)
        #self.logger.debug("cache_lock = %s" % self.cache_lock)

        if not self.cache_file: return

        self.cache_acces = 0

        # increase sleeping time when it taks more time..
        #self.logger.debug("check for lock file %s" % self.cache_lock)
        #while os.path.exists(self.cache_lock) :
        #      self.logger.debug("cache locked sleeping for %f" % self.sleep_list[self.sleep_idx])
        #      time.sleep(self.sleep_list[self.sleep_idx])
        #      self.sleep_idx = self.sleep_idx + 1
        #      if self.sleep_idx > self.sleep_max : self.sleep_idx = self.sleep_max

        # out of the loop will start over with a short sleep time
        #self.sleep_idx = 0

        #self.logger.debug("acquiring lock")
        #f=open(self.cache_lock,'wb')
        #f.write(b'lock')
        #f.close()

        self.logger.debug("load cache")
        self.cache = shelve.open(self.cache_file)

    def cache_save(self):
        self.logger.debug("sr_poster cache_save")
        if not self.caching       : return
        if not self.cache         : return
        if self.parent.batch <= 0 : return
        batch_reached = self.cache_acces % self.parent.batch
        if batch_reached     != 0 : return
        self.logger.debug("sr_poster cache_save sync")
        self.cache.sync()

    def close(self):
        self.logger.debug("sr_poster close")
        self.cache_close()
        self.hc.close()

    def get_message(self):
        self.logger.debug("sr_poster get_message")

        if not hasattr(self.parent,'msg'):
           self.parent.msg = sr_message(self.parent)

        self.msg           = self.parent.msg
        self.msg.user      = self.broker.username
        self.msg.publisher = self.publisher

    def post(self,exchange,url,to_clusters,partstr=None,sumstr=None,rename=None,filename=None):
        self.logger.debug("sr_poster post")

        # if caching is enabled make sure it was not already posted
        if self.caching :
           key    = url.path

           # new
           if not key in self.cache :
                kdict = {}
                kdict[partstr]  = sumstr
                self.cache[key] = kdict
                 
           # delete
           elif sumstr == 'R,0':
                del self.cache[key]

           # modified, or repost
           else:
                kdict = self.cache[key]
                if partstr in kdict and kdict[partstr] == sumstr :
                   self.logger.info("skipped already posted %s %s %s" % (url.path,partstr,sumstr))
                   return True
                kdict[partstr]  = sumstr
                self.cache[key] = kdict

           self.cache_acces += 1
           self.cache_save()

        # set message exchange
        self.msg.exchange = exchange
        
        # set message topic
        self.msg.set_topic_url(self.topic_prefix,url)
        if self.subtopic != None :
           self.msg.set_topic_usr(self.topic_prefix,self.subtopic)

        # set message notice
        self.msg.set_notice(url)

        # set message headers
        self.msg.headers = {}

        self.msg.headers['to_clusters'] = to_clusters

        if partstr  != None : self.msg.headers['parts']        = partstr
        if sumstr   != None : self.msg.headers['sum']          = sumstr
        if rename   != None : self.msg.headers['rename']       = rename

        # optional

        if self.parent.cluster != None : self.msg.headers['from_cluster'] = self.parent.cluster
        if self.parent.source  != None : self.msg.headers['source']       = self.parent.source
        if self.parent.flow    != None : self.msg.headers['flow']         = self.parent.flow
        if filename            != None : self.msg.headers['filename']     = filename

        ok = self.parent.__on_post__()
        return ok

    def post_local_file(self,path,exchange,url,to_clusters,sumflg='d',rename=None):
        self.logger.debug("sr_poster post_local_file")
    
        # set partstr

        lstat   = os.stat(path)
        fsiz    = lstat[stat.ST_SIZE]
        partstr = '1,%d,1,0,0' % fsiz

        # set sumstr

        self.parent.set_sumalgo(sumflg)
        sumalgo = self.parent.sumalgo

        if   sumflg == 'R' :
             sumstr = 'R,0'

        elif len(sumflg) > 2 and sumflg[:2] == 'z,' :
             sumstr = sumflg

        # compute checksum
        else:
              sumalgo.set_path(path)

              fp = open(path,'rb')
              i  = 0
              while i<fsiz :
                    buf = fp.read(self.bufsize)
                    if not buf: break
                    sumalgo.update(buf)
                    i  += len(buf)
              fp.close()

              checksum = sumalgo.get_value()
              sumstr   = '%s,%s' % (sumflg,checksum)

        # post

        filename = os.path.basename(path)

        ok = self.post(exchange,url,to_clusters,partstr,sumstr,rename,filename)

        self.logger.debug("sr_poster post_local_file")

        return ok

    def post_local_inplace(self,path,exchange,url,to_clusters,chunksize=0,sumflg='d',rename=None):
        self.logger.debug("sr_poster post_local_inplace")

        ok       = False
        lstat    = os.stat(path)
        fsiz     = lstat[stat.ST_SIZE]

        # file too small for chunksize

        if chunksize <= 0 or chunksize >= fsiz : 
           ok = self.post_local_file(path,exchange,url,to_clusters,sumflg,rename)
           return ok

        # count blocks and remainder

        block_count = int(fsiz/chunksize)
        remainder   =     fsiz%chunksize
        if remainder > 0 : block_count = block_count + 1

        # info setup

        self.parent.set_sumalgo(sumflg)
        sumalgo  = self.parent.sumalgo
        filename = os.path.basename(path)
        blocks   = list(range(0,block_count))

        # randomize chunks

        if self.parent.randomize :
           i = 0
           while i < block_count/2+1 :
               j         = random.randint(0,block_count-1)
               tmp       = blocks[j]
               blocks[j] = blocks[i]
               blocks[i] = tmp
               i = i + 1


        # loop on chunks

        i = 0
        while i < block_count :
              current_block = blocks[i]

              offset = current_block * chunksize
              length = chunksize

              last   = current_block == block_count-1
              if last and remainder > 0 :
                 length = remainder

              # set partstr

              partstr = 'i,%d,%d,%d,%d' %\
                        (chunksize,block_count,remainder,current_block)

              # compute checksum if needed

              if len(sumflg) > 2 and sumflg[:2] == 'z,' :
                 sumstr = sumflg
              else:
                 bufsize = self.bufsize
                 if length < bufsize : bufsize = length

                 sumalgo.set_path(path)

                 fp = open(path,'rb')
                 if offset != 0 : fp.seek(offset,0)
                 t  = 0
                 while t<length :
                       buf = fp.read(bufsize)
                       if not buf: break
                       sumalgo.update(buf)
                       t  += len(buf)
                 fp.close()

                 checksum = sumalgo.get_value()
                 sumstr   = '%s,%s' % (sumflg,checksum)

              # post

              ok = self.post(exchange,url,to_clusters,partstr,sumstr,rename,filename)
              if not ok : return ok

              # reconnect ?

              if self.parent.reconnect:
                 self.logger.info("Reconnect")
                 self.hc.reconnect()

              i = i + 1

        return ok

    def post_local_part(self,path,exchange,url,to_clusters,rename=None):
        self.logger.debug("sr_poster post_local_part")

        # verify part suffix is ok

        ok,message = self.msg.verify_part_suffix(path)
        if not ok:
           self.logger.error("partflg set to p but %s for file  %s " % (message,path))
           return ok

        # make sure suffix is also in rename

        if rename != None and not self.msg.suffix in rename :
           rename += self.msg.suffix

        # set partstr

        partstr = 'p,%d,%d,%d,%d' %\
                   (self.msg.chunksize,self.msg.block_count,self.msg.remainder,self.msg.current_block)


        # set sumstr

        sumstr   = '%s,%s' % (self.msg.sumflg,self.msg.checksum)

        filename = os.path.basename(path)

        ok = self.post(exchange,url,to_clusters,partstr,sumstr,rename,filename)

        return ok

# ===================================
# self_test
# ===================================

class test_logger:
      """

        Instead of using the real logging classes, when doing self-test, override with the test logger.
        test logger prints to stdout.  to suppress logginc set the logging routing to self.silence.

      """
      def silence(self,str):
          """
          to removed prints from output
          """
          pass

      def __init__(self):
          self.debug   = self.silence
          self.error   = print
          self.info    = self.silence
          self.warning = print

class sr_cfg_plus(sr_config):
      def __init__(self,config=None,args=None):
          sr_config.__init__(self,config,args)

      def __on_post__(self):
          return self.msg.publish()

def self_test():

    try :
            logger = test_logger()

            #setup consumer to catch first post
            cfg = sr_cfg_plus()

            cfg.defaults()
            cfg.general()
	     
            cfg.logger         = logger
            cfg.debug          = False
            ok, cfg.post_broker    = cfg.validate_urlstr("amqp://tsource@localhost/")
            ok, cfg.broker         = cfg.validate_urlstr("amqp://tsub@localhost/")

            poster = sr_poster(cfg)

            fp = open("toto","wb")
            fp.write(b"abcdefghijklmnopqrstuvwxyz")
            fp.close()

            path        = os.getcwd() + os.sep + "toto"
            exchange    = "xs_tsource"
            url         = urllib.parse.urlparse("file://" + path)
            to_clusters = "ALL"

            poster.post_local_file(path,exchange,url,to_clusters)
            poster.post_local_inplace(path,exchange,url,to_clusters,chunksize=10)
            cfg.randomize    = True
            cfg.reconnect    = True
            poster.post_local_inplace(path,exchange,url,to_clusters,chunksize=10)
            cfg.randomize    = False
            cfg.reconnect    = False

            part = ".26.12.0.1.d.Part"
            path_part = path + part
            url_part  = urllib.parse.urlparse("file://" + path_part)
            try:   os.unlink(path_part)
            except:pass
            os.link(path, path_part)
            poster.post_local_part(path_part,exchange,url_part,to_clusters)

            poster.post_local_file(path,exchange,url,to_clusters,sumflg='0')
            poster.post_local_file(path,exchange,url,to_clusters,sumflg='n')
            poster.post_local_file(path,exchange,url,to_clusters,sumflg='z,d')

            cfg.cluster      = "mycluster"
            cfg.source       = "mysource"
            cfg.flow         = "myflow"
            cfg.topic_prefix = "mytopic_prefix"
            cfg.subtopic     = "mysubtopic"

            poster.post_local_file(path,exchange,url,to_clusters,sumflg='d',rename="/local/renamed")
            poster.post_local_inplace(path,exchange,url,to_clusters,chunksize=10,sumflg='d',rename="/local/renamed")
            poster.post_local_part(path_part,exchange,url_part,to_clusters,rename="/local/renamed")

            os.unlink(path)
            os.unlink(path_part)

            poster.close()
    except:
            (stype, svalue, tb) = sys.exc_info()
            logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
            print("sr_poster **** FAILED")
            sys.exit(1)


    print("sr_poster TEST PASSED")
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
