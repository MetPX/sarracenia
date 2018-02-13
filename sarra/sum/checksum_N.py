#!/usr/bin/env python3

from hashlib import sha512

try :
         from sr_checksum       import *
except :
         from sarra.sr_checksum import *

# ===================================
# checksum_N class
# ===================================

class checksum_N(sr_checksum):
      """
      look at C code for more details
      Did this just as a quick shot... not convinced it is ok
      Still put a test below... Use with care
      """

      def registered_as(self):
          return 'N'

      def set_path(self,filename,partstr):
          self.filehash = sha512()
          self.filehash.update(bytes(filename+partstr,'utf-8'))
          self.value = self.filehash.hexdigest()

self.add_sumalgo=checksum_N()

