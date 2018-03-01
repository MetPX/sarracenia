#!/usr/bin/env python3

from hashlib import md5

try :
         from sr_checksum       import *
except :
         from sarra.sr_checksum import *

# ===================================
# checksum_d class
# ===================================

class checksum_d(sr_checksum):
      """
      The default algorithm is to do a checksum of the entire contents of the file, which is called 'd'.
      """

      def get_value(self):
          return self.filehash.hexdigest()

      def registered_as(self):
          return 'd'

      def set_path(self,path):
          self.filehash = md5()

      def update(self,chunk):
          if type(chunk) == bytes : self.filehash.update(chunk)
          else                    : self.filehash.update(bytes(chunk,'utf-8'))


self.add_sumalgo=checksum_d()

