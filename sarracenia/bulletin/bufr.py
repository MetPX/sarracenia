#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-

"""
MetPX Copyright (C) 2004-2015 Shared Services Canada
MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file
named COPYING in the root of the source directory tree.

###############################################################################
# Name: Bufr.py
#
# Authors: Michel Grenier
#
# Date: 2006-04-26 
#
# Description: A class to process BUFR messages.
#
# Revision History: 
#   2015-04-10  DP          Investigate & apply code changes for Python 3.
###############################################################################
"""
import array
import logging
import time

__version__ = '1.0'

logger = logging.getLogger(__name__)

class Bufr:
    """This class is a very basic BUFR processing.

    end()    returns where the BUFR message ends
    start()  returns where the BUFR message starts
    length() the length according to the bufr's header.
    validate() make sure the messages looks ok...

    Auteur: Michel Grenier
    Date:   Mars   2006
    """
    
    def __init__(self,stringBulletin):
        self.set(stringBulletin)


    def set(self,stringBulletin):
        self.bulletin  = stringBulletin

        self.array = array.array('B',self.bulletin)
        self.size  = len(self.bulletin)
        self.valid = True

        self.begin = 0
        self.last  = self.size

        if self.bulletin == None :
           self.valid    =  False
           return

        try    :
                 self.section0()
                 if self.valid == False : return
                 self.checkEOB()
                 if self.valid == False : return
                 self.section1()
                 if self.valid == False : return
                 self.observation_date()

        except :
                 self.valid = False

    def checkEOB(self):
        """check that the end is ok and return its position
        """
        if self.valid == False : return

        e = self.s0 + self.length;
        
        if self.bulletin[e-4:e] != b"7777" :
            self.valid = False

    def integer2bytes(self,i):
        """return an integer made of the 3 bytes starting at i
        """
        a = self.array

        return  ( int(a[i]) * 256 ) + int(a[i+1]) 

    def integer3bytes(self,i):
        """return an integer made of the 3 bytes starting at i
        """
        a = self.array

        return  ( int(a[i]) * 256 + int(a[i+1]) ) * 256 + int(a[i+2])

    def observation_date(self):
        """derive observation date from section 1
        """
        if self.valid == False : return

        self.observation    = '%.4d' % self.s1_year
        self.observation   += '%.2d' % self.s1_month
        self.observation   += '%.2d' % self.s1_day
        self.observation   += '%.2d' % self.s1_hour
        self.observation   += '%.2d' % self.s1_min

        timeStruct          = time.strptime(self.observation, '%Y%m%d%H%M%S')
        self.ep_observation = time.mktime(timeStruct)

    # section 0
    #             bytes  0 1 2 3    BUFR
    #             bytes  4 5 6      total length of bufr message
    #             byte   7          bufr edition number

    def section0(self):

        self.valid = False

        if self.size < 8 : return

        self.s0 = self.bulletin.find(b'BUFR')
        if self.s0 == -1 : return

        self.begin = self.s0
        self.last  = self.size - self.s0

        b0  = self.s0
        b4  = self.s0 + 4
        b7  = self.s0 + 7

        self.length = self.integer3bytes(b4)
        if self.length > self.size-self.s0 : return

        self.version = int(self.array[b7])

        self.last  = self.s0 + self.length

        self.valid = True

        return

    # section 1 

    def section1(self):

        self.valid = False

        # for now version <= 4 the few first bytes are
        #             bytes  0 1 2      length of section 1
        #             bytes  3          bufr master table
        self.s1 = self.s0 + 8

        if self.s1+17 > self.size : return

        b0 = self.s1
        self.s1_length = self.integer3bytes(b0)
        if self.s1_length > self.size-self.s1 : return

        # section 1   DESCRIPTION DE LA VERSION 2 ET 3
        #             bytes  0 1 2      length of section 1
        #             bytes  3          bufr master table
        #             byte   4          origination subcenter
        #             byte   5          origination center
        #             byte   6          update sequence number
        #             byte   7          bit 1 = 0/1 means optional section n/y
        #             byte   8          data category
        #             byte   9          data subcategory
        #             byte  10          version no for master table
        #             byte  11          version no for local  table
        #             byte  12          year of century
        #             byte  13          month
        #             byte  14          day
        #             byte  15          hour
        #             byte  16          min
        #             byte  17          reserved
        if self.version <= 3:


           # uncomment anything you need

           #self.s1_master_table        = int(self.array[b0+3])
           #self.s1_subcenter           = int(self.array[b0+4])
           #self.s1_center              = int(self.array[b0+5])
           #self.s1_update_sequence     = int(self.array[b0+6])
           #self.s1_optional_section    = int(self.array[b0+7])
           #self.s1_data_category       = int(self.array[b0+8])
           #self.s1_data_subcategory    = int(self.array[b0+9])
           #self.s1_data_master_version = int(self.array[b0+10])
           #self.s1_data_local_version  = int(self.array[b0+11])

           self.s1_century             = int(self.array[b0+12])
           self.s1_year                = 2000 + self.s1_century
           self.s1_month               = int(self.array[b0+13])
           self.s1_day                 = int(self.array[b0+14])
           self.s1_hour                = int(self.array[b0+15])
           self.s1_min                 = int(self.array[b0+16])
           self.s1_sec                 = 0

           now=time.localtime()
           yc=int(time.strftime('%y',now))
           if self.s1_century < 0 or self.s1_century > yc+1 : return

           if self.s1_month   < 1 or self.s1_month   > 12 : return
           if self.s1_day     < 1 or self.s1_day     > 31: return
           if self.s1_hour    < 0 or self.s1_hour    > 23: return
           if self.s1_min     < 0 or self.s1_min     > 59: return

        # section 1   DESCRIPTION DE LA VERSION 4
        #             bytes  0 1 2      length of section 1
        #             bytes  3          bufr master table
        #             byte   4-5        origination subcenter
        #             byte   6-7        origination center
        #             byte   8          update sequence number
        #             byte   9          bit 1 = 0/1 means optional section n/y
        #             byte  10          data category
        #             byte  11          international data subcategory
        #             byte  12          local data subcategory
        #             byte  13          version no for master table
        #             byte  14          version no for local  table
        #             byte  15-16       year
        #             byte  17          month
        #             byte  18          day
        #             byte  19          hour
        #             byte  20          min
        #             byte  21          sec
        #             byte  22          reserved
        if self.version == 4:
            self.s1 = self.s0 + 8

            if self.s1+22 > self.size: return

            b0  = self.s1
            self.s1_length = self.integer3bytes(b0)
            if self.s1_length > self.size-self.s1 : return

            # uncomment anything you need

            #self.s1_master_table           = int(self.array[b0+3])
            #self.s1_subcenter              = self.integer2bytes(b0+5)
            #self.s1_center                 = self.integer2bytes(b0+7)
            #self.s1_update_sequence        = int(self.array[b0+8])
            #self.s1_optional_section       = int(self.array[b0+9])
            #self.s1_data_category          = int(self.array[b0+10])
            #self.s1_data_subcategory       = int(self.array[b0+11])
            #self.s1_data_local_subcategory = int(self.array[b0+12])
            #self.s1_data_master_version    = int(self.array[b0+13])
            #self.s1_data_local_version     = int(self.array[b0+14])

            self.s1_year                   = self.integer2bytes(b0+15)
            self.s1_month                  = int(self.array[b0+17])
            self.s1_day                    = int(self.array[b0+18])
            self.s1_hour                   = int(self.array[b0+19])
            self.s1_min                    = int(self.array[b0+20])
            self.s1_sec                    = int(self.array[b0+21])

            if self.s1_month   < 1 or self.s1_month   > 12: return
            if self.s1_day     < 1 or self.s1_day     > 31 : return
            if self.s1_hour    < 0 or self.s1_hour    > 23 : return
            if self.s1_min     < 0 or self.s1_min     > 59: return
            if self.s1_sec     < 0 or self.s1_sec     > 59: return

        self.valid = True

        return
