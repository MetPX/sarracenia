# -*- coding: iso-8859-1 -*-
# MetPX Copyright (C) 2004-2006  Environment Canada
# MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file
# named COPYING in the root of the source directory tree.
#
# Author:
# 2004 - Louis-Phillippe Thériault.
#

"""Derived classs for AM protocol bulletins """

import time
import struct
import string
import logging
import curses
import curses.ascii
# import sarracenia.bulletin as bulletin
from sarracenia.bulletin import Bulletin

logger = logging.getLogger(__name__)

class BulletinAm(Bulletin):
    # __doc__ = bulletin.bulletin.__doc__ + \
    """
    Concrete Implementation of a bulletin class.

    Implantation pour un usage concret de la classe bulletin

            * information to pass to the constructor

            mapEntetes              dict (default=None)

                                    - a mapping of headers to stations.
                                      to build the key, take the first two
                                      letters of the header (ie. CA, RA )
                                      and concatenate the station. ie.
                                      CACYUL.  The value is what to add to 
                                      the header to complete it. 
                                      for an SP received from CZPC:
                                       TH["SPCZPC"] = "CN52 CWAO "
                                      
                                    - if None, leave header alone.

            SMHeaderFormat          bool (default=False)

                                    - If true, add "AAXX jjhhmm4\\n"
                                      to the second line of the bulletin. 

    """


    def __init__(self,lineSeparator='\n',mapEntetes=None):
        # bulletin.__init__(self,stringBulletin,logger,lineSeparator='\n')
        self.mapEntetes = mapEntetes
        # self.SMHeaderFormat = SMHeaderFormat

    def doSpecificProcessing(self):
        # __doc__ = bulletin.bulletin.doSpecificProcessing.__doc__ + \
        """AM specific processing.

        """
        self.replaceChar('\r','')

        unBulletin = self.bulletin

        if len(self.getHeader().split()) < 1:
        # If the first line is empty, bad bulletin, do nothing.
            self.verifyHeader()
            return

        # If the bulletin needs a new header and/or modification.
        if self.mapEntetes != None and len(self.getHeader().split()[0]) == 2:
            # Si le premier token est 2 lettres de long

            uneEnteteDeBulletin = None

            premierMot = self.getType()

            station = self.getStation()

            # Fetch de l'ent�te
            if station != None:
                # Construction de la cle
                if premierMot != "SP":
                    uneCle = premierMot + station
                else:
                    uneCle = "SA" + station

                # Fetch de l'entete a inserer
                # FIXME: default should be configurable in px.conf
                if premierMot in ["CA","MA","RA"]:
                    uneEnteteDeBulletin = "CN00 CWAO "
                else:
                    try:
                        uneEnteteDeBulletin = self.mapEntetes[uneCle]
                    except KeyError:
                    # L'entête n'a pu être trouvée
                        uneEnteteDeBulletin = None

            # build header
            if station != None and uneEnteteDeBulletin != None:
                if premierMot == "CA" :
                    uneEnteteDeBulletin = premierMot + uneEnteteDeBulletin + self.getCaFormattedTime()
                elif len(unBulletin[0].split()) == 1:
                    uneEnteteDeBulletin = premierMot + uneEnteteDeBulletin + self.getFormattedSystemTime()
                elif len(unBulletin[0].split()) == 2:
                    uneEnteteDeBulletin = premierMot + uneEnteteDeBulletin + unBulletin[0].split()[1]
                else:
                    uneEnteteDeBulletin = premierMot + uneEnteteDeBulletin + unBulletin[0].split()[1] + ' ' + unBulletin[0].split()[2]

                # Apply the header to the bulletin.
                self.setHeader(uneEnteteDeBulletin)

                # Insert AAXX jjhhmm4 if needed (for SM/SI.)
                if self.getType() in ["SM","SI"]:
                    self.bulletin.insert(1, "AAXX " + self.getHeader().split()[2][0:4] + "4")

            if station == None or uneEnteteDeBulletin == None:
                if station == None:
                    self.setError("station missing from either configuration or bulletin")

                    logger.warning("station not found")
                    logger.warning("Bulletin:\n"+self.getBulletin())

                # Header not found in station configuration file, error.
                elif uneEnteteDeBulletin == None:
                    self.setError("header not found in stations configuration file")

                    logger.warning("Station <" + station + "> not found for prefix <" + premierMot + ">")
                    logger.warning("Bulletin:\n"+self.getBulletin())

        if self.getType() in ['UG','UK','US'] and self.bulletin[1] == '':
            self.bulletin.remove('')

        if self.bulletin[0][0] == '\x01':
            self.replaceChar('\x01','')
            self.replaceChar('\x03\x04','')

        if self.bulletin[0][:6] in ['RACN00']:
            self.replaceChar('\x02','')
            self.replaceChar('\x03','')
            self.replaceChar('\x04','')

        if self.bulletin[0][:4] in ['SACN']:
            self.replaceChar('\x0e','')
            self.replaceChar('\x0f','')


        self.verifyHeader()

    # converting date/time found in CA to our proper header time signature
    def convertCaTime(self,year,jul,hhmm):
        if hhmm != '2400' :
           emissionStr      = year + jul + hhmm
           timeStruct       = time.strptime(emissionStr, '%Y%j%H%M')

           self.emission    = time.strftime("%Y%m%d%H%M%S",timeStruct)
           self.ep_emission = time.mktime(timeStruct)

           ddHHMM     = time.strftime("%d%H%M",timeStruct)
           return ddHHMM

        # sometime hhmm is 2400 which would create an exception if not treated properly
        # in this case : set time to 00, increase by 24 hr, return proper ddHHMM

        jul00      = year + jul + '0000'
        timeStruct = time.strptime(jul00, '%Y%j%H%M')

        self.ep_emission = time.mktime(timeStruct) + 24 * 60 * 60
        timeStruct       = time.localtime(self.ep_emission)
        self.emission    = time.strftime("%Y%m%d%H%M%S",timeStruct)

        ddHHMM     = time.strftime('%d%H%M',timeStruct)
        return ddHHMM

    # converting date/time token found for a CA
    def convertCaToken(self,tok):
        year  = tok[0]
        jul   = string.zfill( tok[1], 3 )
        hhmm  = string.zfill( tok[2], 4 )
        return  self.convertCaTime(year,jul,hhmm)

    # check if token looks like a year
    def tokIsYear(self,tok,year):
        if tok == year : return True

        if len(tok) !=    4            : return False
        if tok[:2]  != '20'            : return False
        if not tok[2] in string.digits : return False
        if not tok[3] in string.digits : return False

        return True

    def getCaFormattedTime(self):
        """getFormattedSystemTime() -> heure

           heure:       String

           Return a string with the local system time.
           ddhhmm : day of month/hour(0-23h)/minutes

           Purpose:

               Generate the time stamp for a bulletin header.
        """

        try :
                 line  = self.bulletin[2]
                 parts = line.split(',')
                 ltime = time.localtime()
                 year  = time.strftime("%Y",ltime )

                 # the date in CACN starts at token 1 or 2 and has format YYYY,jjj,hhmm

                 if self.tokIsYear(parts[1],year) : return self.convertCaToken(parts[1:])
                 if self.tokIsYear(parts[2],year) : return self.convertCaToken(parts[2:])

                 # check if station name in report line... check date after stn name

                 stn = self.bulletin[1]

                 i = -1
                 try    : i = parts.index(stn)
                 except : pass

                 if i != -1 :
                    if self.tokIsYear(parts[i+1],year) : return self.convertCaToken(parts[i+1:])
                    if self.tokIsYear(parts[i+2],year) : return self.convertCaToken(parts[i+2:])
                    if self.tokIsYear(parts[i+3],year) : return self.convertCaToken(parts[i+3:])

                 # sometime the year is skipped
                 jjj = time.strftime("%j", ltime )
                 jul = string.zfill( parts[1], 3 )
                 if jul == jjj :
                    hhmm = string.zfill( parts[2], 4 )
                    return self.convertCaTime(year,jul,hhmm)

        except : pass

        self.setError("incorrect date-time")
        logger.warning("BULLETIN :\n%s" % self.bulletin)
        ddHHMM = time.strftime("%d%H%M",time.localtime())

        return ddHHMM

    def getFormattedSystemTime(self):
        """getFormattedSystemTime() -> heure

           heure:       String

           Return a string with the local system time.
           ddhhmm : day of month/hour(0-23h)/minutes

           Purpose:

               Generate the time stamp for a bulletin header.
        """
        return time.strftime("%d%H%M",time.localtime())

    def verifyHeader(self):
        # __doc__ = bulletin.bulletin.verifyHeader.__doc__ + \
        """
           Override to prevent header verification during instantiation.
        """
        return
