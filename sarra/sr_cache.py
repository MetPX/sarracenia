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
# sr_cache.py : python3 program generalise caching for sr programs
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Wed Jul 26 18:57:19 UTC 2017
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
#

import os,sys,time


#============================================================
# sr_cache supports/uses :
#
# cache_file : default ~/.cache/sarra/'pgm'/'cfg'/recent_files_0001.cache
#              each line in file is
#              sum time path part
#
# cache_dict : {}  
#              cache_dict[sum] = [ (time1,[path1,part1]),(time2,[path2,part2])...]
#

class sr_cache():

    def __init__(self, parent ):
        parent.logger.debug("sr_cache init")

        self.parent        = parent
        self.logger        = parent.logger

        self.expire        = parent.caching

        self.cache_dict    = {}
        self.cache_file    = None
        self.fp            = None

        self.last_expire   = time.time()
        self.count         = 0

    def check(self, key, path, part):
        self.logger.debug("sr_cache check")

        # set time and value
        now   = time.time()
        value = [path,part]

        # new... add
        if not key in self.cache_dict :
           self.logger.debug("new")
           self.cache_dict[key] = [(now,value)]
           self.fp.write("%s %f %s %s\n"%(key,now,path,part))
           self.count += 1
           return True

        # key (sum) in cache
        for i,tup in enumerate(self.cache_dict[key]) :
            t,v = tup
            # same path/part update time
            self.logger.debug("compare %s %s" %(v,value))
            if v == value :
               self.cache_dict[key][i] = (now,value)
               return False

        self.logger.debug("differ")

        # key (sum) in cache...
        # same path but not same part ...
        # MG --- does this make sense ? ---

        self.cache_dict[key].append( (now,value) )
        self.fp.write("%s %f %s %s\n"%(key,now,path,part))
        self.count += 1
        return True

    def check_msg(self, msg):
        self.logger.debug("sr_cache check_msg")

        relpath = msg.relpath
        sumstr  = msg.headers['sum']
        partstr = relpath

        if sumstr[0] not in ['R','L'] :
           partstr = msg.headers['parts']

        return self.check(sumstr,relpath,partstr)

    def clean(self):
        self.logger.debug("sr_cache clean")

        # create refreshed dict

        now        = time.time()
        new_dict   = {}
        self.count = 0

        # from  cache[sum] = [(time,[path,part]), ... ]
        for key in self.cache_dict.keys() :
            new_dict[key] = []
            for t,v in self.cache_dict[key] :
                # expired or keep
                ttl = now - t
                if ttl > self.expire : continue
                new_dict[key].append( (t,v) )
                self.count += 1

            if len(new_dict[key]) == 0 :
               del new_dict[key]

        # set cleaned cache_dict
        self.cache_dict = new_dict

    def close(self, unlink=False):
        self.logger.debug("sr_cache close")
        self.fp.flush()
        self.fp.close()
        self.fp = None

        if unlink : os.unlink(self.cache_file)

        self.cache_dict = {}
        self.count      = 0

    def delete_path(self, path):
        self.logger.debug("sr_cache delete_path")

        # close,remove file, open new empty file
        self.fp.close()
        os.unlink(self.cache_file)
        self.fp = open(self.cache_file,'w')

        # write unexpired entries, create refreshed dict
        new_dict   = {}
        now        = time.time()
        self.count = 0

        # from  cache[sum] = [(time,[path,part]),...]
        for key in self.cache_dict.keys():
            new_dict[key] = []
            for t,v in self.cache_dict[key]:

                # expired are skipped
                ttl = now - t
                if ttl > self.expire : continue
                if v[0] == path      : continue

                # save
                new_dict[key].append( (t,v) )
                self.fp.write("%s %f %s %s\n"%(key,t,v[0],v[1]))
                self.count += 1

            # all expired
            if len(new_dict[key]) == 0 :
               del new_dict[key]

        # set cleaned cache_dict and
        # keep file open for append

        self.cache_dict = new_dict

    def free(self):
        self.logger.debug("sr_cache free")
        self.cache_dict = {}
        self.count      = 0
        os.unlink(self.cache_file)
        self.fp = open(self.cache_file,'w')

    def load(self):
        self.logger.debug("sr_cache load")
        self.cache_dict = {}
        self.count      = 0

        # create file if not existing
        if not os.path.isfile(self.cache_file) :
           self.fp = open(self.cache_file,'w')
           self.fp.close()

        # set time 
        now = time.time()

        # open file (read/append)... 
        # read through
        # keep open to append entries

        self.fp = open(self.cache_file,'r+')
        while True :
              # read line, parse words
              line  = self.fp.readline()
              if not line : break

              # words  = [ sum, time, path, part ]
              words    = line.split()
              pathpart = words[2:]

              # skip expired entry
              ctime = float(words[1])
              ttl   = now - ctime
              if ttl > self.expire : continue

              # key = sum and value = ( time, [ path, part ])
              key      = words[0]
              value    = (ctime,pathpart)

              #  key already in cache
              if key in self.cache_dict :
                 v = None
                 for t,v in self.cache_dict[key] :
                     if v == pathpart : break
                 if v == pathpart : continue
                 # key already in cache
                 self.cache_dict[key].append(value)
                 self.count += 1
                 continue

              #  add key
              self.cache_dict[key] = [ value ]
              self.count += 1

    def open(self, cache_file = None):

        self.cache_file = cache_file

        if cache_file == None :
           self.cache_file  = self.parent.user_cache_dir + os.sep 
           self.cache_file += 'recent_files_%.3d.cache' % self.parent.instance

        self.load()

    def save(self):
        self.logger.debug("sr_cache save")

        # close,remove file, open new empty file
        if self.fp : self.fp.close()
        try   : os.unlink(self.cache_file)
        except: pass
        self.fp = open(self.cache_file,'w')

        # write unexpired entries, create refreshed dict
        new_dict   = {}
        now        = time.time()
        self.count = 0

        # from  cache[sum] = [(time,[path,part]),...]
        for key in self.cache_dict.keys():
            new_dict[key] = []
            for t,v in self.cache_dict[key]:

                # expired are skipped
                ttl = now - t
                if ttl > self.expire : continue

                # save
                new_dict[key].append( (t,v) )
                self.fp.write("%s %f %s %s\n"%(key,t,v[0],v[1]))
                self.count += 1

            # all expired
            if len(new_dict[key]) == 0 :
               del new_dict[key]

        # set cleaned cache_dict and
        # keep file open for append

        self.cache_dict = new_dict

    def check_expire(self):
        self.logger.debug("sr_cache check_expire")
        now    = time.time()
        elapse = now - self.last_expire
        if elapse > self.expire :
           self.last_expire = now
           self.clean()

# ===================================
# self_test
# ===================================

try :    
         from sr_config         import *
except : 
         from sarra.sr_config   import *

class test_logger:
      def silence(self,str):
          pass
      def __init__(self):
          self.debug   = self.silence
          self.error   = print
          self.info    = self.silence
          self.warning = print

def self_test():

    logger = test_logger()

    cfg        = sr_config(config=None,args=['test','--debug','False'])
    cfg.logger = logger
    cfg.config_name = "test"

    cfg.debug  = False
    cfg.defaults()
    cfg.debug  = False

    cfg.general()

    optH = "caching 7"
    cfg.option( optH.split()  )

    # check creation addition close
    cache = sr_cache(cfg)
    cache.open()
    cache.check('key1','file1','part1')
    cache.check('key2','file2','part2')
    cache.check('key1','file1','part1')
    logger.debug(cache.cache_dict)
    cache.close()

    cache = sr_cache(cfg)
    cache.open()
    cache.load()
    logger.debug(cache.cache_dict)
    time.sleep(10)
    cache.check('key3','file3','part3')
    cache.check_expire()
    cache.check('key4','file4','part4')
    logger.debug(cache.cache_dict)
    cache.close()

    time.sleep(10)
    cache = sr_cache(cfg)
    cache.open()
    cache.load()
    logger.debug(cache.cache_dict)
    cache.close()

    #add 10000 entries
    cache = sr_cache(cfg)
    cache.open()
    cache.load()
    i = 0
    now = time.time()
    while i<10000 :
          cache.check('key%d'%i,'file%d'%i,'part%d'%i)
          i = i + 1

    logger.debug(len(cache.cache_dict))
    cache.free()
    logger.debug(cache.cache_dict)
    cache.close()

    #add 10000 entries
    cache = sr_cache(cfg)
    cache.open()
    cache.load()
    i = 0
    now = time.time()
    while i<100 :
          time.sleep(0.1)
          cache.check('key%d'%i,'file%d'%i,'part%d'%i)
          time.sleep(0.1)
          cache.check('key%d'%i,'file%d'%i,'part0%d'%i)
          time.sleep(0.1)
          cache.check('key%d'%i,'file%d'%i,'part1%d'%i)
          time.sleep(0.1)
          cache.check('key%d'%i,'file%d'%i,'part2%d'%i)
          i = i + 1

    cache.delete_path('file12')

    logger.debug(len(cache.cache_dict))
    time.sleep(3)
    cache.clean()
    logger.debug(len(cache.cache_dict))
    time.sleep(3)
    cache.check_expire()
    logger.debug(len(cache.cache_dict))
    time.sleep(3)
    cache.save()
    logger.debug(len(cache.cache_dict))
    cache.close()
    logger.debug("elapse %f"%(time.time()-now))


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
