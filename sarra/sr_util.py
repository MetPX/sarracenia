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

# ===================================
# checksum_0 class
# ===================================

class checksum_0(object):
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
      def __init__(self):
          self.value = '0'

      def get_value(self):
          return self.value

      def update(self,chunk):
          pass

      def set_path(self,path):
          filename   = os.path.basename(path)
          self.value = md5(bytes(filename,'utf-8')).hexdigest()
