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
          for f in flgs:
              if f == 'n' :
                 self.checksum = self.checksum_n
                 break;
              if f == '0' :
                 self.checksum = self.checksum_0
                 break;
              if f[:2] == 'c=' :
                 exec(compile(open(f[2:]).read(), f[2:], 'exec'))

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

# ==========
# Notice
# ==========

class Notice:
      def __init__(self):
          self.set_time()

          self.chksum = Checksum()

          self.chunksize     = 0
          self.block_count   = 0
          self.remainder     = 0
          self.current_block = 0
          self.str_flags     = ''
          self.data_sum      = ''

          self.source        = ''
          self.lpath         = ''

          self.code          = None
          self.server        = ''
          self.user          = ''
          self.download_time = 0.0

      # get notice from its settings
      def get(self):

          self.notice = self.time   
          self.notice = self.notice + ' %d' % self.chunksize
          self.notice = self.notice + ' %d' % self.block_count
          self.notice = self.notice + ' %d' % self.remainder
          self.notice = self.notice + ' %d' % self.current_block
          self.notice = self.notice + ' %s' % self.str_flags
          self.notice = self.notice + ' %s' % self.data_sum
          self.notice = self.notice + ' %s' % self.source
          self.notice = self.notice + ' %s' % self.lpath

          if self.code != None :
             self.notice = self.notice + ' %s'  % self.code
             self.notice = self.notice + ' %s'  % self.server
             self.notice = self.notice + ' %s'  % self.user
             self.notice = self.notice + ' %s'  % self.download_time
          
          return self.notice

      # set notice from its string
      def from_notice(self,notice):

          parts = notice.split(' ')

          self.time          = parts[0]
          self.chunksize     = int(parts[1])
          self.block_count   = int(parts[2])
          self.remainder     = int(parts[3])
          self.current_block = int(parts[4])
          self.str_flags     = parts[5]
          self.data_sum      = parts[6]

          self.source        = parts[8]
          self.lpath         = parts[9]
          self.dpath         = parts[9]

          sparts = self.dpath.split('/')
          self.dfile         = sparts[-1]

          self.url           = self.source

          if self.url[-1] == os.sep :
             self.url   = self.url + self.lpath

          # log notice
          if len(parts) > 10 :
             self.code          = parts[10]
             self.server        = parts[11]
             self.user          = parts[12]
             self.download_time = parts[13]

      # set notice from its string
      def from_v00_notice(self,notice):

          parts = notice.split(' ')

          self.set_time()
          self.chunksize     = int(parts[1])
          self.block_count   = 1
          self.remainder     = 0
          self.current_block = 0
          self.str_flags     = 'd'
          self.data_sum      = parts[0]

          self.source        = parts[2]
          self.lpath         = parts[3]
          self.dpath         = parts[3]

          sparts = self.dpath.split('/')
          self.dfile         = sparts[-1]

          self.url           = self.source

          if self.url[-1] == '/' :
             self.url   = self.url + self.lpath

      # set chunk info
      def set_chunk(self,chunksize,block_count,remainder,current_block,str_flags,data_sum):
          self.chunksize     = chunksize
          self.block_count   = block_count
          self.remainder     = remainder
          self.current_block = current_block
          self.str_flags     = str_flags
          self.data_sum      = data_sum

      # set log info
      def set_log(self,code,user,download_time=0.0):
          self.code          = None
          self.server        = socket.gethostname()
          self.user          = user
          self.download_time = download_time

      # set source info
      def set_source(self,source,lpath):
          self.source = source
          self.lpath  = lpath

      # set time
      def set_time(self):
          msec = '.%d' % (int(round(time.time() * 1000)) %1000)
          now  = time.strftime("%Y%m%d%H%M%S",time.gmtime()) + msec
          self.time = now

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
