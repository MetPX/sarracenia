#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-
"""
MetPX Copyright (C) 2004-2015 Shared Services Canada
MetPX comes with ABSOLUTELY NO WARRANTY; For details type see the file
named COPYING in the root of the source directory tree.

###############################################################################
# Name: bulletin.py
#
# Authors: Louis-Philippe Thriault
#
# Date: December 2004
#
# Description: Main class for bulletins
#
# Revision History:
#   2004/12 -- Louis-Philippe Thriault
#   2004/12 -- Louis-Philippe Thriault et Pierre
#   2006/05 -- Michel Grenier... time tools + modules in alpha order 
#   2015-04-10  DP          Investigate & apply code changes for Python 3.
#   2015-05-13  DP          Replace six.moves.range with Python 3 range.
###############################################################################
"""


import time
import string, traceback, sys
from sarracenia.bulletin.bufr import Bufr
from sarracenia.bulletin.grib import Grib

__version__ = '2.0'

class bulletinException(Exception):
    """bulletin exception class: FIXME not very useful documentation, when needed?"""
    pass

class Bulletin:
    """Abstract class for bulletins, with all protocol independent features.
    
    methods that return an exception must be defined by derived classes.
    
    A bulletin is internally represented by a list of strings, separated by 
    the lineSeparator attribute.

    """

    def __init__(self, stringBulletin, logger, lineSeparator='\n',finalLineSeparator='\n',wmo_id=[]):
        """The AHL of a bulletin is checked during instantiation.  To skip the check,
        override verifyHeader in a derived class.

            * parameters to the constructor
            
            stringBulletin          String

                                    - The bulletin as a string.

            logger                  Objet log

                                    - Logging object 

            finalLineSeparator      String

                                    - line separator (output.)

            lineSeparator           String

                                    - line separator (in the stringBulletin)


            * Attributes (internal use only)

            errorBulletin  tuple (default=None)
                  - is set once the 'specific' (protocol? derived class?) 
                    processing is done.
                  When an error is detected.
                  - errorBulletin[0] is the set to the message. 
                  - errorBulletin[1:] is open to for use by derived classes.

            bulletin                list of strings [str]
                  - after call to getBulletin, this contains the entire 
                    bulletin with lineSeparator as the line separator.
        """
        self.logger = logger
        self.errorBulletin = None
        self.lineSeparator = lineSeparator
        self.finalLineSeparator = finalLineSeparator
        self.dataType = None
        self.wmo_id = wmo_id

        # time stuff
        self.arrival     = None
        self.emission    = None
        self.delay       = None
        self.age         = None

        self.ep_arrival  = -1
        self.ep_emission = -1

        # splitlinesBulletin
        #self.bulletin = self.splitlinesBulletin(stringBulletin.lstrip(lineSeparator))
        self.bulletin = self.splitlinesBulletin(stringBulletin)
        # Normalization the header (trim spaces before and after) 
        self.setHeader(self.getHeader().strip())

        self.verifyHeader()

        self.logger.veryverbose("newBulletin: %s" % stringBulletin)

    def compute_Age(self, ep_now=None):
        """compute_Age() -
         
           Compute the age of the bulletin
           the age is given by  age = now-emission 
           were age, now and emission are integer, epocal in second

        """

        if ep_now == None : ep_now = time.mktime(time.localtime())
        self.age = ep_now - self.ep_emission

    def compute_Delay(self):
        """compute_Delay() -
         
           Compute attribute delay which corresponds to  arrival-emission
           delay is an integer in seconds

        """

        self.delay = self.ep_arrival - self.ep_emission

    def compute_Emission(self):
        """compute_Emission() -
        
           compute emission of bulletin
           emission is a character string of the form YYYYMMDDhhmmss
           ep_emission is its epocal correspondant

        """

        # if there is an error with the bulletin do nothing

        if self.errorBulletin != None: return

        # arrival must be set, it is needed to give a date to the emission 
        # because the emission is often ddMMHH

        if self.arrival == None : return

        # emission was already provided/computed

        if self.emission != None and self.ep_emission != -1 : return

        # double check the day hour minute within the bulletin's header

        YYGGGg = ''
        try:
            header = self.getHeader().split()
            YYGGGg = header[2]
            day    = int(YYGGGg[:2])
            hr     = int(YYGGGg[2:4])
            mn     = int(YYGGGg[4:])
            if day <= 0 or day > 31 : return
            if hr  <  0 or hr >= 24 : return
            if mn  <  0 or mn >= 60: return
        except:
            return

        # if the arrival day is the same as the one in header... we are done

        if YYGGGg[:2] == self.arrival[6:8]:
            try:
                self.emission    = self.arrival[0:6] + YYGGGg + "00"
                timeStruct       = time.strptime(self.emission, '%Y%m%d%H%M%S')
                self.ep_emission = time.mktime(timeStruct)
            except : pass
            return

        # try to go forward 1 day... 

        ep_day = self.ep_arrival + 24 * 60 * 60
        day    = time.strftime('%d',time.localtime(ep_day))

        if day == YYGGGg[:2]:
            try:
                self.emission    = time.strftime('%Y%m%d',time.localtime(ep_day))
                self.emission   += YYGGGg[2:] + "00"
                timeStruct       = time.strptime(self.emission, '%Y%m%d%H%M%S')
                self.ep_emission = time.mktime(timeStruct)
            except : pass
            return

        # go backward in time until the emission day is reached
        # prevent endless loop with a count lower than 31 days

        count  = 0
        day    = self.arrival[6:8]
        ep_day = self.ep_arrival
        while day != YYGGGg[:2] and count <= 31:
            ep_day = ep_day - 24 * 60 * 60
            day    = time.strftime('%d',time.localtime(ep_day))
            count  = count + 1

        if count == 32 : return

        try:
            self.emission    = time.strftime('%Y%m%d',time.localtime(ep_day))
            self.emission   += YYGGGg[2:] + "00"
            timeStruct       = time.strptime(self.emission, '%Y%m%d%H%M%S')
            self.ep_emission = time.mktime(timeStruct)
        except : pass


    def doSpecificProcessing(self):
        """doSpecificProcessing()
        
           Apply protocol or derived type specific processing to bulletin.

        """
        raise bulletinException('Mthode non implante (mthode abstraite doSpecificProcessing)')

    def getAge(self, ep_now=None ):
        """getAge() -> (TypeErreur)

           Return the age of the bulletin

        """

        self.computeAge(ep_now)
        return self.age

    def getBBB(self):
        """getBBB() -> (TypeErreur)

           Return None if BBB not present or in error.
           Otherwise return the bulletin's BBB
           Remove testing since it is done in verifyHeader

        """

        header = self.getHeader().split()
        if len(header) != 4 : return None

        BBB = header[3]

        return BBB

    def getBulletin(self, includeError=False, useFinalLineSeparator=True):
        """getBulletin([includeError]) -> bulletin

           bulletin     : String

           includeError:        Bool
               - If True, include error in bulletin body.

           useFinalLineSeparator:       Bool
               - If True, use finalLineSeparator

           returns the bulletin text.

        """
        if useFinalLineSeparator:
            marqueur = self.finalLineSeparator
        else:
            marqueur = self.lineSeparator

        if self.errorBulletin == None:
            retbyteslst = []
            for i in range(0, len(self.bulletin)):
                if type(self.bulletin[i]) != bytes:
                    retbyteslst.append(bytes(self.bulletin[i],'utf-8'))
                else:
                    retbyteslst.append(self.bulletin[i])
            marqueurbytes = marqueur
            if type(marqueurbytes) != bytes:
                marqueurbytes = bytes(marqueur,'utf-8')
            return marqueurbytes.join(retbyteslst)
        else:
            if includeError:
                retstr = ("### " + self.errorBulletin[0] + marqueur +  "PROBLEM BULLETIN" + marqueur + marqueur.join(self.bulletin))
                return bytes(retstr, 'utf-8')
            else:
                return bytes(marqueur.join(self.bulletin),'utf-8')

    def getDataType(self):
        """getDataType() -> dataType

           dataType:    String, value is one of 'BI' or 'AN'.
               - determine whether the bulletin is binary or alphanumeric

        """
        if self.dataType != None:
            return self.dataType

        for ligne in self.bulletin:
            if (ligne.lstrip()[:4] == b'BUFR' or ligne.lstrip()[:4] == b'GRIB' or ligne.lstrip()[:4] == b'\211PNG') :
                # Il faut que le BUFR/GRIB soit au dbut d'une ligne
                self.dataType = 'BI'
                break

        # Si le bulletin n'est pas binaire, il est alphanumrique
        if self.dataType == None: self.dataType = 'AN'

        return self.dataType

    def getError(self):
        """getError() -> (TypeErreur)

        Return None if no errors were detected in the bulletin.
        Otherwise return a tuple with a description as the first element.
        remaining elements undefined.

        """
        return self.errorBulletin

    def getHeader(self):
        """getHeader() -> header

           header       : String

           Return the header (first line) of bulletin.
        """
        objbul = self.bulletin[0]
        if type(objbul) == bytes:
            try:
                objbul = objbul.decode('utf-8')
            except:
                import traceback
                self.logger.info('bulletin.getHeader() - 1st Line read problem')
                self.logger.error(traceback.format_exc())
                #pass
        return objbul

    def getLength(self):
        """getLength() -> longueur

           longueur     : int

           return bulletin length (including lineSeparators)

        """
        return len(self.getBulletin())

    def getLogger(self):
        """getLogger() -> objet_logger

           Retourne logger attribute.

        """
        return self.logger

    def getOrigin(self):
        """getOrigin() -> origine

           origine      : String

           Return the originating station (2nd field of header) (ie. CWAO)
        """
        return self.getHeader().split(' ')[1]

    def getStation(self):
        """getStation() -> station

           station      : String

           Return the station (i.e. CYUL), None if not found.
        """


        #print(" ********************* BULLETIN GET STATION APPELE ")

        station = None
        try:
            premiereLignePleine = ""
            deuxiemeLignePleine = ""
            bulletin = self.bulletin

            # special case, need to get the next full line.
            i = 0
            for ligne in bulletin[1:]:
                i += 1
                premiereLignePleine = ligne
                if len(premiereLignePleine) > 1:
                   if len(bulletin) > i+1 : deuxiemeLignePleine = bulletin[i+1]
                   break

            #print " ********************* header = ", bulletin[0][0:7]
            # switch depends on bulletin type.
            if bulletin[0][0:2] == "SA":
                if bulletin[1].split()[0] in ["METAR","LWIS"]:
                    station = premiereLignePleine.split()[1]
                else:
                    station = premiereLignePleine.split()[0]

            elif bulletin[0][0:2] == "SP":
                station = premiereLignePleine.split()[1]

            elif bulletin[0][0:2] in ["SI","SM"]:
                station = premiereLignePleine.split()[0]
                if station == "AAXX" :
                   if deuxiemeLignePleine != "":
                      station = deuxiemeLignePleine.split()[0]
                   else:
                      station = None

            #elif bulletin[0][0:6] in ["SRCN40","SXCN40","SRMT60","SXAK50", "SRND20", "SRND30"]:
            elif bulletin[0][0:6] in self.wmo_id:
                station = premiereLignePleine.split()[0]

            elif bulletin[0][0:2] in ["FC","FT"]:
                if premiereLignePleine.split()[1] == "AMD":
                    station = premiereLignePleine.split()[2]
                else:
                    station = premiereLignePleine.split()[1]

            elif bulletin[0][0:2] in ["UE","UG","UK","UL","UQ","US"]:
                parts = premiereLignePleine.split()
                if parts[0][:2] in ['EE', 'II', 'QQ', 'UU']:
                    station = parts[1]
                elif parts[0][:2] in ['PP', 'TT']:
                    station = parts[2]
                else:
                    station = None

            elif bulletin[0][0:2] in ["RA","MA","CA"]:
                station = premiereLignePleine.split()[0].split('/')[0]

        except Exception:
            station = None

        if station != None:
            while len(station) > 1 and station[0] == '?':
                station = station[1:]
            if station[0] != '?' :
                station = station.split('?')[0]
                if station[-1] == '=' : station = station[:-1]
            else:
                station = None

        self.station = station

        return station

    def getType(self):
        """getType() -> type

           type         : String

           Return TT (bulletin type, first two letters of AHL) ... ie.: SA, FT,
        """
        return self.getHeader()[:2]

    def replaceChar(self,oldchars,newchars):
        """replaceChar(oldchars,newchars)

           oldchars,newchars    : String

           Replace oldchars by newchars in a bulletin.  
           Skip over GRIB & BUFR data 

           purpose:

                substitutions in doSpecifiProcessing.

        """
        for i in range(len(self.bulletin)):
            if self.bulletin[i].lstrip()[:4] != b'GRIB' and self.bulletin[i].lstrip()[:4] != b'BUFR' and self.bulletin[i].lstrip()[:4] != b'\211PNG':
               strBulletin = self.bulletin[i]
               convert2bytes = False
               if type(strBulletin) == bytes:
                   convert2bytes = True
                   strBulletin = strBulletin.decode('utf-8')
               strBulletin = strBulletin.replace(oldchars,newchars)
               if convert2bytes and type(strBulletin) == str:
                   strBulletin = bytes(strBulletin, 'utf-8')
               self.bulletin[i] = strBulletin

    def setArrivalEp(self,ep_arrival):
        """setArrivalEp(ep_arrival)

           Assign the arrival attribute of bulletin
           ep_arrival is an integer expressing time in epochal seconds

        """ 

        self.ep_arrival = ep_arrival
        self.arrival    = time.strftime('%Y%m%d%H%M%S',time.localtime(ep_arrival))

        self.compute_Emission()
        self.compute_Delay()
        self.compute_Age()

    def setArrivalStr(self,arrivalStr):
        """setArrivalStr(arrivalStr)

           Assign arrival attribute of bulletin
           arrivalStr is a character string of the form YYYYMMDDhhmmss

        """

        self.arrival    = arrivalStr
        timeStruct      = time.strptime(arrivalStr[:14], '%Y%m%d%H%M%S')
        self.ep_arrival = time.mktime(timeStruct)

        self.compute_Emission()
        self.compute_Delay()
        self.compute_Age()

    def setError(self, msg):
        """setError(msg)

           msg: String
                - error message to set.

           Set the bulletin Error flag.  
           How the message is used depends on the message type.
        """
        if self.errorBulletin == None:
            self.errorBulletin = [msg]

    def setHeader(self, header):
        """setHeader(header)

           header       : String

           umm... set the bulletin header? not much help here...

        """
        self.bulletin[0] = header

        self.logger.debug("new bulletin header: %s",header)

    def setLogger(self,logger):
        """setLogger(logger)

           set Logger attribute.

        """
        self.logger = logger

    def splitlinesBulletin(self,stringBulletin):
        """splitlinesBulletin(stringBulletin) -> listeLignes

           stringBulletin       : String
           listeLignes          : Liste

           Return a list of bulletin lines.  Do not use string.splitlines() since
           it will not work with binary data.

           Binary data start with GRIB or BUFR and end with 77777

           Purpose:

                initial split of bulletins to allow change of lineseparator as required.
                or after setting a line separator to split again (call getBulletin, then split again.)

           N.B.: GRIB & BUFR data is normalized by removing all data after 77777
                 and adding a line separator.

        """
        try:
            estBinaire = False

            # On dtermine si le bulletin est binaire
            # determine if the bulletin is binary.
            for ligne in stringBulletin.splitlines():
                if ligne.lstrip()[:4] == b'BUFR' or ligne.lstrip()[:4] == b'GRIB' or ligne.lstrip()[:4] == b'\211PNG' :
                    # Il faut que le BUFR/GRIB soit au dbut d'une ligne
                    # BUFR/GRIB must be at the beginning of a line.
                    estBinaire = True
                    break
            if estBinaire:
                if stringBulletin.find(b'GRIB') != -1:
                    # for GRIB data, do a binary split.
                    # TODO check if grib is valid  grib.valid  and if not react 
                    grib = Grib(stringBulletin)

                    ub = stringBulletin[:grib.begin].decode('utf-8')
                    b = ub.split(self.lineSeparator)

                    # If the last token is a '', then there is a blank last line.
                    # it is removed, because we will add it back later.
                    # Si le dernier token est un '', c'est qu'il y avait
                    # un \n  la fin, et on enlve puisque entre 2 lments de la liste,
                    # on insre un \n
                    if b[-1] == '':
                        b.pop(-1)
                    b = b + [stringBulletin[grib.begin:grib.last]] + ['']
                    return b

                elif stringBulletin.find(b'BUFR') != -1:
                    # for a BUFR bulletin, do a BUFR split...
                    bufr = Bufr(stringBulletin)

                    ub = stringBulletin[:bufr.begin].decode('utf-8')
                    b = ub.split(self.lineSeparator)

                    # Si le dernier token est un '', c'est qu'il y avait
                    # un \n  la fin, et on enlve puisque entre 2 lments de la liste,
                    # on insre un \n
                    if b[-1] == '':
                        b.pop(-1)

                    b = b + [stringBulletin[bufr.begin:bufr.last]] + ['']

                    if bufr.valid:
                       self.emission    = bufr.observation
                       self.ep_emission = bufr.ep_observation
                    else:
                       self.logger.warning('Bufr without a valid internal date in section 1')
                       self.logger.warning('Use date from bulletin header')

                    return b

                elif stringBulletin.find(b'\211PNG') != -1:
                # for a PNG pictural bulletin do nothing...

                    png_begin = stringBulletin.find(b'\211PNG')
                    ub = stringBulletin[:png_begin].decode('utf-8')

                    b = ub.split(self.lineSeparator)

                    # Si le dernier token est un '', c'est qu'il y avait
                    # un \n  la fin, et on enlve puisque entre 2 lments de la liste,
                    # on insre un \n
                    if b[-1] == '':
                        b.pop(-1)
                    b = b + [stringBulletin[png_begin:]] + ['']
                    return b
            else:
                if type(stringBulletin) == bytes:
                    strBulletin = stringBulletin.decode('utf-8')
                else:
                    strBulletin = stringBulletin
                # The bulletin is alphanumeric... 
                #return stringBulletin.split(self.lineSeparator)
                return strBulletin.split(self.lineSeparator)
        except Exception as e:
            self.logger.exception('Error splitting bulletin:\n' + ''.join(traceback.format_exception(Exception, e,sys.exc_info()[2])))
            self.setError('Error splitting bulletin into lines')
            return stringBulletin.split(self.lineSeparator)

    def verifyHeader(self):
        """verifyHeader()

           Flag if there is an error in the header.

           purpose:

                called by init, overrid in derived class to suppress.

        """
        header = self.getHeader()

        # remove duplicate spaces
        tokens = header.split()
        # Python 3 - might have a decode issue?
        header = ' '.join(tokens)
        # Python 3 - ignore "cannot convert"
        #header = tokens.decode('ascii', 'ignore')
        #for token in tokens:
        #    header += token.decode('ascii', 'ignore').encode('utf-8')
        #    #header += ' ' + token.decode('ascii').encode('utf-8')   
        self.setHeader(header)

        if header == '':
            self.setError('empty header')
            return

        tokens = header.split()

        if len(tokens) < 3:
            self.setError('incomplete header (less than 3 fields)')
            return

        if len(tokens[2]) > 6: # On enleve les ['z', 'Z'] ou ['utc', 'UTC']  s'ils sont presents dans le groupe JJHHMM
            tokens[2] = tokens[2][0:6]
            self.logger.info("header normalized (%s): truncated the DDHHMM group (>6 characters)" % str(header))
            self.setHeader(' '.join(tokens))
            tokens = self.getHeader().split()

        if not tokens[0].isalnum() or len(tokens[0]) not in [4,5,6] or \
           not tokens[1].isalnum() or len(tokens[1]) not in [4,5,6] or \
           not tokens[2].isdigit() or len(tokens[2]) != 6 or \
           not (0 <  int(tokens[2][:2]) <= 31) or not(00 <= int(tokens[2][2:4]) <= 23) or \
           not(00 <= int(tokens[2][4:]) <= 59):

            self.setError('malformed header (some of the first 3 fields corrupt)')
            return

        if len(tokens) == 3:
            return

        if not tokens[3].isalpha() or len(tokens[3]) != 3 or tokens[3][0] not in ['C','A','R','P']:
            #self.setError('Entete non conforme (champ BBB incorrect')
            self.logger.info("Header normalized: fourth and later fields removed.") 
            parts = self.getHeader().split()
            del parts[3:]
            self.setHeader(' '.join(parts))
            return

        if len(tokens) == 5 and \
                (not tokens[4].isalpha() or len(tokens[4]) != 3 or tokens[4][0] not in ['C','A','R','P']):

            #self.setError('malformed header4 (second BBB field corrupt)')
            self.logger.info("header normalized: fifth and later fields removed")
            parts = self.getHeader().split()
            del parts[4:]
            self.setHeader(' '.join(parts))
            return

        if len(tokens) > 5:

            #self.setError('Entete non conforme (plus de 5 champs')
            self.logger.info("header normalized: sixth and later fields removed")
            parts = self.getHeader().split()
            del parts[5:]
            self.setHeader(' '.join(parts))
            return


