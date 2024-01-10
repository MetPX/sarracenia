#!/usr/bin/env python3 
# -*- coding: iso-8859-1 -*-

"""
MetPX Copyright (C) 2004-2015 Shared Services Canada
MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file
named COPYING in the root of the source directory tree.

###############################################################################
# Name: Grib.py
#
# Author: Peter Silva
#         Michel Grenier
#
# Date: 2006-04-26
#
# Description: A class to process GRIB messages.
#
# Revision History:
#   2015-04-14  DP          Investigate & apply code changes for Python 3.
###############################################################################
"""

import array, time
import string, traceback, sys

__version__ = '1.0'

class Grib:
    """This class is a very basic GRIB processing.

    end()    returns where the GRIB message ends
    start()  returns where the GRIB message starts
    length() the length according to the grib's header.
    validate() make sure the messages looks ok...
    version() returns the GRIB message version...

    Auteur: Michel Grenier
    Date:   Mars   2006
    """

    def __init__(self,stringBulletin):
        self.bulletin = stringBulletin

        self.set(stringBulletin)

    def set(self,stringBulletin):
        self.bulletin = stringBulletin

        self.begin = -1
        self.last  = -1
        self.len   = -1
        self.valid = True
        self.version = -1

        self.validate()

    def len3(self,str):
        """return the length of the GRIB message when the format is on 
        3 bytes...
        """

        a = array.array('B',str)

        i = 1
        p = int(a[0])
        while i<3 : 
              l = p * 256 + int(a[i])
              p = l
              i = i + 1

        return l

    def len8(self,str):
        """return the length of the GRIB message when the format is on 
        8 bytes...
        """

        a = array.array('B',str)

        i = 1
        p = int(a[0])
        while i<8 : 
              l = p * 256 + int(a[i])
              p = l
              i = i + 1

        return l

    def end(self):
        """check that the end is ok and return its position
        """

        e = self.begin + self.len;

        if self.bulletin[e-4:e] != b"7777" :
           self.valid = False
           return -1

        self.last = e

        return e

    def getVersion(self):
        """get the version for that grib
        """

        b = self.begin

        a = array.array('B',self.bulletin[b+7:b+8])
        v = int(a[0])

        if v < 1  or v > 2 :
           v = -1

        self.version = v

        return v

    def length(self):
        """return the length of the GRIB message
        """

        if not self.valid :
           return -1

        b = self.begin
        l = -1

        if self.version == 1 :
           l = self.len3(self.bulletin[b+4:b+8])

        if self.version == 2 :
           l = self.len8(self.bulletin[b+8:b+16])

        if l < 0 or l > len(self.bulletin[b:]) :
           self.valid = False
           return -1

        self.len = l

        return l

    def start(self):
        """return the position where the GRIB message starts 
        """

        self.begin = self.bulletin.find(b'GRIB')

        if self.begin == -1 : self.valid = False

        return self.begin

    def validate(self):
        """Verifie que tout semble correct avec le GRIB
        """

        if self.bulletin == None : return False

        self.start()
        self.getVersion()
        self.length()
        self.end()

        return self.valid


