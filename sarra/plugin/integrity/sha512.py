#!/usr/bin/env python3

from hashlib import sha512

from sarra.plugin.integrity import Integrity
from base64 import b64decode, b64encode


# ===================================
# checksum_s class
# ===================================

class Sha512(Integrity):
      """
      The SHA512 algorithm to checksum the entire file, which is called 's'.
      """
      @classmethod
      def assimilate(cls,obj):
         obj.__class__ = Sha512

      def __init__(self):
         Sha512.assimilate(self)

      def get_value(self):
          return b64encode(self.filehash.digest()).decode('utf-8')

      def registered_as():
          return 's'

      def set_path(self,path):
          self.filehash = sha512()

      def update(self,chunk):
          if type(chunk) == bytes : self.filehash.update(chunk)
          else                    : self.filehash.update(bytes(chunk,'utf-8'))

