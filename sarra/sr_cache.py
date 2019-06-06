#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
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
#

import os,sys,time

import urllib.parse


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

        self.cache_basis =  parent.cache_basis

        self.last_expire   = time.time()
        self.count         = 0

    def check(self, key, path, part):
        self.logger.debug("sr_cache check basis=%s" % self.cache_basis )

        # set time and value
        now   = time.time()

        if self.cache_basis == 'name':
            relpath = path.split('/')[-1]
        elif self.cache_basis == 'path':
            relpath = path
        elif self.cache_basis == 'data':
            relpath = "data"

        qpath = urllib.parse.quote(relpath)
        value = '%s*%s' % (relpath,part)

        # new... add
        if not key in self.cache_dict :
           self.logger.debug("new")
           kdict = {}
           kdict[value] = now
           self.cache_dict[key] = kdict
           self.fp.write("%s %f %s %s\n"%(key,now,qpath,part))
           self.count += 1
           return True

        # key (sum) in cache ... 
        # if value "path part" already there update its time
        # if value "path part" not there add it 
        # this ends up to be the same code

        kdict   = self.cache_dict[key]
        present = value in kdict
        kdict[value] = now

        if not present : self.logger.debug("differ")

        # differ or newer, write to file

        self.fp.write("%s %f %s %s\n"%(key,now,qpath,part))
        self.count += 1
        return not present

    def check_msg(self, msg):
        self.logger.debug("sr_cache check_msg")

        if self.cache_basis == 'name':
            relpath = msg.relpath.split('/')[-1]
        elif self.cache_basis == 'path':
            relpath = msg.relpath
        elif self.cache_basis == 'data':
            relpath = "data"

        sumstr  = msg.headers['sum']
        partstr = relpath

        if sumstr[0] not in ['R','L'] :
           partstr = msg.headers['parts']

        return self.check(sumstr,relpath,partstr)

    def clean(self, fp = None, delpath = None):
        self.logger.debug("sr_cache clean")

        # create refreshed dict

        now        = time.time()
        new_dict   = {}
        self.count = 0

        if delpath != None:
            qdelpath = urllib.parse.quote(delpath)
        else:
            qdelpath = None

        # from  cache[sum] = [(time,[path,part]), ... ]
        for key in self.cache_dict.keys() :
            ndict = {}
            kdict = self.cache_dict[key]

            for value in kdict :
                # expired or keep
                t   = kdict[value]
                ttl = now - t
                if ttl > self.expire : continue

                parts = value.split('*')
                path  = parts[0]
                qpath = urllib.parse.quote(path)
                part  = parts[1]

                if qpath == qdelpath  : continue

                ndict[value] = t
                self.count  += 1

                if fp : fp.write("%s %f %s %s\n"%(key,t,qpath,part))

            if len(ndict) > 0 : new_dict[key] = ndict

        # set cleaned cache_dict
        self.cache_dict = new_dict

    def close(self, unlink=False):
        self.logger.debug("sr_cache close")
        try   :
                self.fp.flush()
                self.fp.close()
        except: pass
        self.fp = None

        if unlink:
           try   : os.unlink(self.cache_file)
           except: pass

        self.cache_dict = {}
        self.count      = 0

    def delete_path(self, delpath):
        self.logger.debug("sr_cache delete_path")

        # close,remove file, open new empty file
        self.fp.close()
        if os.path.exists( self.cache_file ):
            os.unlink( self.cache_file )
        self.fp = open(self.cache_file,'w')

        # clean cache removing delpath

        self.clean(self.fp, delpath)

    def free(self):
        self.logger.debug("sr_cache free")
        self.cache_dict = {}
        self.count      = 0
        try   : os.unlink(self.cache_file)
        except: pass
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
        lineno=0
        while True :
              # read line, parse words
              line  = self.fp.readline()
              if not line : break
              lineno += 1

              # words  = [ sum, time, path, part ]
              try:
                  words    = line.split()
                  key      = words[0]
                  ctime    = float(words[1])
                  qpath     = words[2]
                  path     = urllib.parse.unquote(qpath)
                  part     = words[3]
                  value    = '%s*%s' % (path,part)

                  # skip expired entry

                  ttl   = now - ctime
                  if ttl > self.expire : continue

              except: # skip corrupted line.
                  self.logger.error("sr_cache load corrupted line %d in %s" % ( lineno, self.cache_file) )
                  continue

              #  add info in cache

              if key in self.cache_dict : kdict = self.cache_dict[key]
              else:                       kdict = {}

              if not value in kdict     : self.count += 1

              kdict[value]         = ctime
              self.cache_dict[key] = kdict


    def open(self, cache_file = None):

        self.cache_file = cache_file

        if cache_file == None :
           self.cache_file  = self.parent.user_cache_dir + os.sep 
           self.cache_file += 'recent_files_%.3d.cache' % self.parent.instance

        self.load()

    def save(self):
        self.logger.debug("sr_cache save")

        # close,remove file
        if self.fp : self.fp.close()
        try   : 
                os.unlink(self.cache_file)
        except: pass

        # new empty file, write unexpired entries
        try   : 
                self.fp = open(self.cache_file,'w')
                self.clean(self.fp)
        except: pass


    def check_expire(self):
        self.logger.debug("sr_cache check_expire")
        now    = time.time()
        elapse = now - self.last_expire
        if elapse > self.expire :
           self.last_expire = now
           self.clean()

