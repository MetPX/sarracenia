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
# sr_util.py : python3 utility mostly for checksum and file part
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Jun Hu         - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Sep 22 10:41:32 EDT 2015
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

import os,stat,time
import urllib
import urllib.parse
from hashlib import md5

# ===================================
# Checksum class
# ===================================

class Checksum:
      def __init__(self):
          self.checksum = self.checksum_d

      def from_list(self,flgs):
          self.checksum = self.checksum_d
          if   flgs == 'd' :
             self.checksum = self.checksum_d
          elif flgs == 'n' :
             self.checksum = self.checksum_n
          elif flgs == '0' :
             self.checksum = self.checksum_0
          else :
             exec(compile(open(flgs).read(), flgs, 'exec'))

      # checksum_0 = checksum for flag 0

      def checksum_0(self, filepath, offset=0, length=0 ):
          return '0'

      # checksum_d = checksum for flag d

      def checksum_d(self, filepath, offset=0, length=0 ):
          f = open(filepath,'rb')
          if offset != 0 : f.seek(offset,0)
          if length != 0 : data = f.read(length)
          else:            data = f.read()
          f.close()
          return md5(data).hexdigest()

      # checksum_n = checksum for flag n

      def checksum_n( self, filepath, offset=0, length=0 ):
          filename = os.path.basename(filepath)
          return md5(bytes(filename,'utf-8')).hexdigest()

# ===================================
# chunk size from a string value
# ===================================

def chunksize_from_str(str_value):
    factor = 1
    if str_value[-1] in 'bB'   : str_value = str_value[:-1]
    if str_value[-1] in 'kK'   : factor = 1024
    if str_value[-1] in 'mM'   : factor = 1024 * 1024
    if str_value[-1] in 'gG'   : factor = 1024 * 1024 * 1024
    if str_value[-1] in 'tT'   : factor = 1024 * 1024 * 1024 * 1024
    if str_value[-1].isalpha() : str_value = str_value[:-1]
    chunksize = int(str_value) * factor

    return chunksize

class Chunk:

    def __init__(self, chunksize, chksum, filepath ):

        self.chunksize     = chunksize
        self.chksum        = chksum
        self.filepath      = filepath

        lstat              = os.stat(filepath)
        self.fsiz          = lstat[stat.ST_SIZE]

        self.chunksize     = self.fsiz
        self.block_count   = 1
        self.remainder     = 0

        if chunksize != 0 and chunksize < self.fsiz :
           self.chunksize   = chunksize
           self.block_count = int(self.fsiz / self.chunksize)
           self.remainder   = self.fsiz % self.chunksize
           if self.remainder > 0 : self.block_count = self.block_count + 1

    def get_Nblock(self):
           return self.block_count

    def get(self,current_block):

        if current_block >= self.block_count : return None

        if self.block_count == 1 :
           data_sum  = self.chksum(self.filepath,0,self.fsiz)
           return (self.fsiz, 1, 0, 0, data_sum)

        data_sum = self.chksum(self.filepath,current_block*self.chunksize,self.chunksize)

        return (self.chunksize, self.block_count, self.remainder, current_block, data_sum) 
