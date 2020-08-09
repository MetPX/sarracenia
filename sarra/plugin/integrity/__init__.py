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


from abc import ABCMeta, abstractmethod


logger = logging.getLogger( __name__ )

class Integrity:
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self,method):
        #default established
        method=None
        default='sha512'
        for sc in Integrity.__subclasses__():
            if method == sc.__name__.lower():
               break
            if 'sha512' == sc.__name__.lower():
               default_sc = sc

        if method is None:
           sc = default_sc

        sc.__init__(self)
   

    @abstractmethod
    def get_method(self):
        return type(self).__name__.lower()

#   @abstractmethod
#   def get_value(self):
#       """
#       return the current value of the checksum calculation.
#       """
#
#   @abstractmethod
#   def registered_as(self):
#       """
#       return a one letter string identifying the algorithm.
#       """
#
#   @abstractmethod
#   def set_path(self,path):
#       """
#       start a checksum for the given path... initialize.
#       """
#
#   @abstractmethod
#   def update(self,chunk):
#       """
#       update the checksum based on the given bytes from the file (sequential access assumed.)
#       """

##sum_dir = os.path.dirname( os.path.abspath( __file__ ) )
#print( 'path: %s' % sum_dir )
#sums = os.listdir( sum_dir )
#for s in os.listdir( sum_dir ):
#   if not s[-3:] == '.py':
#       continue
#   if s == '__init__.py':
#       continue
#
#   sc='sarra.plugin.integrity.' + s[:-3]
#   exec( 'import ' + sc )

import sarra.plugin.integrity.arbitrary
import sarra.plugin.integrity.md5name
import sarra.plugin.integrity.md5
import sarra.plugin.integrity.random
import sarra.plugin.integrity.sha512

known_methods = []
for sc in Integrity.__subclasses__() :
    known_methods.append( sc.__name__.lower() )
