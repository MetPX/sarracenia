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
# sr_cache.py : python3 program that generalise caching for sr programs, it is used as a time based buffer that
#               prevents, when activated, identical files (of some kinds) from being processed more than once.
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

import os

import urllib.parse


#============================================================
# sr_cache supports/uses :
#
# cache_file : default ~/.cache/sarra/'pgm'/'cfg'/recent_files_0001.cache
#              each line in file is
#              sum time path part
#
# cache_dict : {}  
#              cache_dict[sum] = {path1*part1: time1, path2*part2: time2, ...}
#
from sarra.sr_util import nowflt


class sr_cache():
    def __init__(self, parent ):
        parent.logger.debug("sr_cache init")

        self.parent        = parent
        self.logger        = parent.logger

        self.expire        = parent.caching

        self.cache_dict    = {}
        self.cache_file    = None
        self.cache_hit     = None
        self.fp            = None

        self.cache_basis =  parent.cache_basis

        self.last_expire   = nowflt()
        self.count         = 0

    def check(self, key, path, part):

        if part is None:
             self.logger.debug("sr_cache check basis=%s part0=%s key0=%s" % (self.cache_basis, "None", key[0]) )
        else:
             self.logger.debug("sr_cache check basis=%s part0=%s key0=%s" % (self.cache_basis, part[0], key[0]) )

        # not found 
        self.cache_hit = None

        # set time and value
        now   = nowflt()
        relpath = self.__get_relpath(path)
        qpath = urllib.parse.quote(relpath)

     
        #override part, when using n because n should be same regardless of size.
        if (key[0] == 'n' ) and (part[0] not in [ 'p', 'i' ]):
             value = '%s' % (relpath)
        else:
             value = '%s*%s' % (relpath, part)

        if key not in self.cache_dict :
           self.logger.debug("adding a new entry in cache")
           kdict = {}
           kdict[value] = now
           self.cache_dict[key] = kdict
           self.fp.write("%s %f %s %s\n"%(key,now,qpath,part))
           self.count += 1
           return True

        self.logger.debug("sum already in cache: key value={}".format(value))
        kdict   = self.cache_dict[key]
        present = value in kdict
        kdict[value] = now

        # differ or newer, write to file
        self.fp.write("%s %f %s %s\n"%(key,now,qpath,part))
        self.count += 1

        if present:
           self.logger.debug("updated time of old entry: value={}".format(value))
           self.cache_hit = value
           return False
        else:
           self.logger.debug("added value={}".format(value))

        if part is None or part[0] not in "pi":
           self.logger.debug("new entry, not a part: part={}".format(part))
           return True

        ptoken = part.split(',')
        if len(ptoken) < 4 :
           self.logger.debug("new entry, weird part: ptoken={}".format(ptoken))
           return True

        # build a wiser dict value without
        # block_count and remainder (ptoken 2 and 3)
        # FIXME the remainder of this method is wrong. It will trivially have a match because we just
        #  added the entry in kdict, then we will always find the value and return false. It will not change
        #  anything at all though. Worst, the cache hit will falsely indicate that we hit an old entry. Then,
        #  partitioned files would be lost. And why are we removing blktot and brem to do such a check.
        pvalue = value
        pvalue = pvalue.replace(','+ptoken[2],'',10)
        pvalue = pvalue.replace(','+ptoken[3],'',10)

        # check every key in kdict
        # build a similar value to compare with pvalue

        for value in kdict :
            kvalue = value
            kvalue = kvalue.replace(','+ptoken[2],'',10)
            kvalue = kvalue.replace(','+ptoken[3],'',10)

            # if we find the value... its in cache... its old

            if pvalue == kvalue :
               self.cache_hit = value
               return False

        # FIXME variable value was overwritten by loop variable value. Using pvalue is safer here
        #  for when the loop bug will be fixed.
        self.logger.debug("did not find it... its new: pvalue={}".format(pvalue))

        return True

    def check_msg(self, msg):
        self.logger.debug("sr_cache check_msg")

        relpath = self.__get_relpath(msg.relpath)
        sumstr  = msg.headers['sum']
        partstr = relpath

        if sumstr[0] not in ['R','L'] :
           partstr = msg.headers['parts']

        return self.check(sumstr,relpath,partstr)

    def __get_relpath(self, path):
        if self.cache_basis == 'name':
            result = path.split('/')[-1]
        elif self.cache_basis == 'path':
            result = path
        elif self.cache_basis == 'data':
            result = "data"
        else:
            raise ValueError("invalid cache basis: cache_basis={}".format(self.cache_basis))
        return result

    def clean(self, persist=False, delpath=None):
        self.logger.debug("sr_cache clean")

        # create refreshed dict

        now        = nowflt()
        new_dict   = {}
        self.count = 0

        if delpath is not None:
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
                if len(parts) > 1:
                    part  = parts[1]
                else:
                    part  = None

                if qpath == qdelpath  : continue

                ndict[value] = t
                self.count  += 1

                if persist:
                    self.fp.write("%s %f %s %s\n"%(key,t,qpath,part))

            if len(ndict) > 0 : new_dict[key] = ndict

        # set cleaned cache_dict
        self.cache_dict = new_dict

    def close(self, unlink=False):
        self.logger.debug("sr_cache close")
        try:
            self.fp.flush()
            self.fp.close()
        except Exception as err:
            self.logger.warning('did not close: cache_file={}, err={}'.format(self.cache_file, err))
            self.logger.debug('Exception details:', exc_info=True)
        self.fp = None

        if unlink:
            try:
                os.unlink(self.cache_file)
            except Exception as err:
                self.logger.warning("did not unlink: cache_file={}: err={}".format(self.cache_file, err))
                self.logger.debug('Exception details:', exc_info=True)
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
        self.clean(persist=True, delpath=delpath)

    def free(self):
        self.logger.debug("sr_cache free")
        self.cache_dict = {}
        self.count      = 0
        try:
            os.unlink(self.cache_file)
        except Exception as err:
            self.logger.warning("did not unlink: cache_file={}, err={}".format(self.cache_file, err))
            self.logger.debug('Exception details:', exc_info=True)
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
        now = nowflt()

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
                  
                  if (key[0] == 'n' ) and (part[0] not in [ 'p', 'i' ]):
                      value = '%s' % path
                  else:
                      value = '%s*%s' % (path, part)

                  # skip expired entry

                  ttl   = now - ctime
                  if ttl > self.expire : continue

              except Exception as err:
                  err_msg_fmt = "load corrupted: lineno={}, cache_file={}, err={}"
                  self.logger.error(err_msg_fmt.format(lineno, self.cache_file, err))
                  self.logger.debug('Exception details:', exc_info=True)
                  continue

              #  add info in cache

              if key in self.cache_dict : kdict = self.cache_dict[key]
              else:                       kdict = {}

              if not value in kdict     : self.count += 1

              kdict[value]         = ctime
              self.cache_dict[key] = kdict


    def open(self, cache_file = None):

        self.cache_file = cache_file

        if cache_file is None :
           self.cache_file  = self.parent.user_cache_dir + os.sep 
           self.cache_file += 'recent_files_%.3d.cache' % self.parent.instance

        self.load()

    def save(self):
        self.logger.debug("sr_cache save")

        # close,remove file
        if self.fp : self.fp.close()
        try:
            os.unlink(self.cache_file)
        except Exception as err:
            self.logger.warning("did not unlink: cache_file={}, err={}".format(self.cache_file, err))
            self.logger.debug('Exception details:', exc_info=True)
        # new empty file, write unexpired entries
        try:
            self.fp = open(self.cache_file,'w')
            self.clean(persist=True)
        except Exception as err:
            self.logger.warning("did not clean: cache_file={}, err={}".format(self.cache_file, err))
            self.logger.debug('Exception details:', exc_info=True)

    def check_expire(self):
        self.logger.debug("sr_cache check_expire")
        now = nowflt()

        elapse = now - self.last_expire
        if elapse > self.expire :
           self.last_expire = now
           self.clean()

