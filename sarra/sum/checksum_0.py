#!/usr/bin/env python3

import random

try :
         from sr_checksum       import *
except :
         from sarra.sr_checksum import *

# ===================================
# checksum_0 class
# ===================================

class checksum_0(sr_checksum):
      """
      Trivial minimalist checksumming algorithm, returns 0 for any file.
      """

      def get_value(self):
          return '%.4d' % random.randint(0,9999)

      def registered_as(self):
          return '0'

self.add_sumalgo=checksum_0()

