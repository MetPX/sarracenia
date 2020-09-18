#!/usr/bin/python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SarraDocumentation
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

import os
import logging

import functools

#from abc import ABCMeta, abstractmethod

from base64 import b64encode

logger = logging.getLogger(__name__)


class Integrity:
    #__metaclass__ = ABCMeta

    @staticmethod
    def factory(method='sha512'):

        found = False
        for sc in Integrity.__subclasses__():
            Found = method == sc.__name__.lower()
            if Found:
                break

        return sc() if Found else None

    def get_method(self):
        return type(self).__name__.lower()

    def update_file(self, path):
        """
         read the entire file, check sum it. 
         this is kind of last resort as it cost an extra file read.
         It is better to call update( as the file is being read for other reasons.
       """
        self.set_path(path)
        with open(path, 'rb') as f:
            for data in iter(functools.partial(f.read, 1024 * 1024), b''):
                self.update(data)

    def get_value(self):
        """
        return the current value of the checksum calculation.
        """
        return b64encode(self.filehash.digest()).decode('utf-8')


# required methods in subclasses:
#
#   def registered_as(self):
#       """
#       return a one letter string identifying the algorithm.
#       """
#
#   def set_path(self,path):
#       """
#       start a checksum for the given path... initialize.
#       """
#
#   def update(self,chunk):
#       """
#       update the checksum based on the given bytes from the file (sequential access assumed.)
#       """

import sarra.plugin.integrity.arbitrary
import sarra.plugin.integrity.md5name
import sarra.plugin.integrity.md5
import sarra.plugin.integrity.random
import sarra.plugin.integrity.sha512

known_methods = []
for sc in Integrity.__subclasses__():
    known_methods.append(sc.__name__.lower())
