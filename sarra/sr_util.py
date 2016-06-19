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
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Feb  4 09:09:03 EST 2016
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

import os,stat,time,sys
import urllib
import urllib.parse
from hashlib import md5

"""

A single checksum class is chosen by the source of data being injected into the network.
The following checksum classes are alternatives that are built-in.  Sources may define 
new algorithms that need to be added to networks.

checksums are used by:
    sr_post to generate the initial post.
    sr_post to compare against cached values to see if a given block is the same as what was already posted.
    sr_sarra to ensure that the post received is accurate before echoing further.
    sr_subscribe to compare the post with the file which is already on disk.
    sr_winnow to determine if a given post has been seen before.


The API of a checksum class (in calling sequence order):
   __init__   -- initialize the value of a checksum for a part.
   set_path   -- identify the checksumming algorithm to be used by update.
   update     -- given this chunk of the file, update the checksum for the part
   get_value  -- return the current calculated checksum value.

The API allows for checksums to be calculated while transfer is in progress 
rather than after the fact as a second pass through the data.  

"""
# ===================================
# checksum_0 class
# ===================================

class checksum_0(object):
      """
      Trivial minimalist checksumming algorithm, returns 0 for any file.
      """
      def __init__(self):
          self.value = '0'

      def get_value(self):
          return self.value

      def update(self,chunk):
          pass

      def set_path(self,path):
          pass

# ===================================
# checksum_d class
# ===================================

class checksum_d(object):
      """
      The default algorithm is to do a checksum of the entire contents of the file, which is called 'd'.
      """
      def __init__(self):
          self.value = '0'

      def get_value(self):
          self.value = self.filehash.hexdigest()
          return self.value

      def update(self,chunk):
          self.filehash.update(chunk)

      def set_path(self,path):
          self.filehash = md5()

# ===================================
# checksum_n class
# ===================================

class checksum_n(object):
      """
      when there is more than one processing chain producing products, it can happen that files are equivalent
      without being identical, for example if each server tags a product with ''generated on server 16', then
      the generation tags will differ.   The simplest option for checksumming then is to use the name of the
      product, which is generally the same from all the processing chains.  
      """
      def __init__(self):
          self.value = '0'

      def get_value(self):
          return self.value

      def update(self,chunk):
          pass

      def set_path(self,path):
          filename   = os.path.basename(path)
          self.value = md5(bytes(filename,'utf-8')).hexdigest()
