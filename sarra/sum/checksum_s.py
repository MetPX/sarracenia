#!/usr/bin/env python3

from hashlib import sha512

try :
         from sr_checksum       import *
except :
         from sarra.sr_checksum import *

# ===================================
# checksum_s class
# ===================================

class checksum_s(sr_checksum):
      """
      The SHA512 algorithm to checksum the entire file, which is called 's'.
      """

      def get_value(self):
          return self.filehash.hexdigest()

      def registered_as(self):
          return 's'

      def set_path(self,path):
          self.filehash = sha512()

      def update(self,chunk):
          if type(chunk) == bytes : self.filehash.update(chunk)
          else                    : self.filehash.update(bytes(chunk,'utf-8'))

self.add_sumalgo=checksum_s()

