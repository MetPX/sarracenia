#!/usr/bin/env python3

from hashlib import md5

try :
         from sr_checksum       import *
except :
         from sarra.sr_checksum import *

# ===================================
# checksum_n class
# ===================================

class checksum_n(sr_checksum):
      """
      when there is more than one processing chain producing products, it can happen that files are equivalent
      without being identical, for example if each server tags a product with ''generated on server 16', then
      the generation tags will differ.   The simplest option for checksumming then is to use the name of the
      product, which is generally the same from all the processing chains.  
      """

      def registered_as(self):
          return 'n'

      def set_path(self,path):
          filename   = os.path.basename(path)
          self.value = md5(bytes(filename,'utf-8')).hexdigest()

self.add_sumalgo=checksum_n()

