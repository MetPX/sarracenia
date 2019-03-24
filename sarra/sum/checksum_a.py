#!/usr/bin/env python3

import random

try :
         from sr_checksum       import *
except :
         from sarra.sr_checksum import *

# ===================================
# checksum_a class
# ===================================

class checksum_a(sr_checksum):
      """
      Trivial minimalist checksumming algorithm, returns rand int for any file.
      """

      def set_value(self, value ):
          self.value = value

      def get_value(self):
          return self.value

      def registered_as(self):
          return 'a'

self.add_sumalgo=checksum_a()

