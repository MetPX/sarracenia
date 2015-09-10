#!/usr/bin/python3

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


def write_to_file(this,req,lfile,loffset,length) :
        bufsize = 10 * 1024 * 1024
        # file should exists
        if not os.path.isfile(lfile) :
           fp = open(lfile,'w')
           fp.close()

        # file open read/modify binary
        fp = open(lfile,'r+b')
        if loffset != 0 : fp.seek(loffset,0)

        nc = int(length/bufsize)
        r  = length % bufsize

        # loop on bufsize if needed
        i  = 0
        while i < nc :
              chunk = req.read(bufsize)
              if len(chunk) != bufsize :
                 this.logger.debug('length %d and bufsize = %d' % (len(chunk),bufsize))
                 this.logger.error('1 source data differ from notification... abort')
                 if i > 0 : this.logger.error('product corrupted')
                 return False,417,'Expectation Failed'
              fp.write(chunk)
              i = i + 1

        # remaining
        if r > 0 :
           chunk = req.read(r)
           if len(chunk) != r :
              this.logger.debug('length %d and remainder = %d' % (len(chunk),r))
              this.logger.error('2 source data differ from notification... abort')
              return False,417,'Expectation Failed'
           fp.write(chunk)

        fp.close()

        return True,201,'Created (Downloaded)'

# ===================================
# Seek info
# ===================================

def Seekinfo( chunksize, block_count, remainder, current_block ):
    chunksize     = int(chunksize)
    block_count   = int(block_count)
    remainder     = int(remainder)
    current_block = int(current_block)

    offset = current_block * chunksize
    length = chunksize
    if remainder > 0 and current_block == block_count-1 : length = remainder

    fsiz   = block_count * chunksize
    if remainder > 0 : fsiz = fsiz - chunksize + remainder

    return offset,length,fsiz
