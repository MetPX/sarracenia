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

class sr_cache():

    def __init__(self, parent ):
        parent.logger.debug("sr_cache init")

        self.parent        = parent
        self.logger        = parent.logger

        self.expire        = parent.caching
        self.cache_file    = parent.user_cache_dir + os.sep + 'cache'
        self.fp            = None

        self.on_cache_list = self.parent.on_cache_list
        self.last_expire   = time.time()

        parent.logger.debug("sr_cache file %s" % self.cache_file)
        self.load()

        #if parent.nbr_instances > 1 :

    def add(self, key, path, part):
        self.logger.debug("sr_cache add")
        now = time.time()
        self.cacheDict[key] = [now,path,part]
        self.fp.write("%s %f %s %s\n"%(key,now,path,part))

        # cache expire roll
        self.check_expire()

    def clean(self):
        self.logger.debug("sr_cache clean")
        self.fp.close()
        os.unlink(self.cache_file)

        self.fp = open(self.cache_file,'w')
        newDict = {}
        now     = time.time()
        for key in self.cacheDict.keys() :
            lst = self.cacheDict[key]
            ttl = now - lst[0]
            if ttl > self.expire : continue
            newDict[key] = lst
            self.fp.write("%s %f %s %s\n"%(key,lst[0],lst[1],lst[2]))
        
    def clear(self):
        self.logger.debug("sr_cache clear")
        self.cacheDict = {}
        os.unlink(self.cache_file)
        self.fp = open(self.cache_file,'w')

    def close(self):
        self.logger.debug("sr_cache close")
        self.fp.flush()
        self.fp.close()
        self.fp = None

    def find(self, key):
        self.logger.debug("sr_cache find")
        return key in self.cacheDict

    def check_expire(self):
        self.logger.debug("sr_cache check_expire")
        now    = time.time()
        elapse = now - self.last_expire
        if elapse > self.expire :
           self.__on_cache__()
           self.last_expire = now

    def load(self):
        self.logger.debug("sr_cache load")
        self.cacheDict  = {}

        # create file if not existing
        if not os.path.isfile(self.cache_file) :
           self.fp = open(self.cache_file,'w')
           self.fp.close()

        # open file for append... keep file open for add
        now = time.time()
        self.fp = open(self.cache_file,'r+')
        while True :
              line  = self.fp.readline()
              if not line : break
              words = line.split()
              ctime = float(words[1])
              ttl   = now - ctime
              if ttl > self.expire : continue
              words[1] = ctime
              self.cacheDict[words[0]] = words[1:]

    def __on_cache__(self):
        self.logger.debug("__on_cache__")

        # invoke on_cache when provided
        for plugin in self.on_cache_list:
           if not plugin(self): return False

        self.clean()

        return True

    def touch(self,key):
        self.logger.debug("sr_cache touch")
        lst    = self.cacheDict[key]
        lst[1] = time.time()

        self.cacheDict[key] = lst


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
          self.debug   = print
          self.error   = print
          self.info    = print
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

    optH = "caching 10"
    cfg.option( optH.split()  )

    # check creation addition close
    cache = sr_cache(cfg)
    cache.add('key1','file1','part1')
    cache.add('key2','file2','part2')
    logger.debug(cache.cacheDict)
    cache.close()

    cache = sr_cache(cfg)
    print(cache.cacheDict)

    time.sleep(10)
    cache.add('key3','file3','part3')
    cache.close()

    time.sleep(5)
    cache = sr_cache(cfg)
    print(cache.cacheDict)
    cache.close()

    #add 10000 entries
    cache = sr_cache(cfg)
    i = 0
    now = time.time()
    while i<10000 :
          cache.add('key%d'%i,'file%d'%i,'part%d'%i)
          i = i + 1
    cache.close()
    print("elapse %f"%(time.time()-now))


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
