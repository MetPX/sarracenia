"""
Description:
    sr3 equivalent of the V2 configuration cvt_bulletin_filename_from_content
    Add bulletin data (full header, timestamp, station ID, BBB) to incomplete filename

    Works essentially the same way as its v2 counterpart, except it can get the bulletin file contents 2 ways.
       1. By the sr3 message content
       2. By opening and reading the path to the file directly.
    The plugin captures what was done on the V2 converter and ties it up with Sundew source code logic to make it more generalized.
    What it can do that the V2 plugin cannot:
        - Add the station ID in the filename
        - Add the BBB in the filename
        - Fetch bulletin data multiple ways

    Decoding of the data is done in the same way of the encoder in flowcb/gather/am.py


Examples:

    RAW Ninjo file (4 letter station ID)
       WACN07 CWAO 082327
       CZEG AIRMET E1 VALID 080105/080505 CWEG-

       Output filename: WACN07_CWAO_082327_CZEG__00001
    
    Another RAW Ninjo file
       FTCN32 CWAO 100500 AAM
       (...)

       Output filename: FTCN32_CWAO_100500_AAM__00002

    A CACN bulletin missing the correct filename
       Input filename: CA__12345

       Contents:
        CACN00 CWAO 141600
        PQU

       Output filename: CACN00_CWAO_141600_PQU__00003

    A ISA binary bulletin
       Input filename: ISAA41_CYZX_162000__00035 

       Contents:
        ISAA41_CYZX_162000
        BUFR

       Output filename: ISAA41_CYZX_162000___00035  

Usage:
   callback rename.raw2bulletin

Contributions:
    Andre LeBlanc - First author (2024/02)

Improvements:
    Delegate some of the generalized methods to a parent class. To be callable by other plugins.
"""

from sarracenia.flowcb import FlowCB
import logging
from base64 import b64decode
import time, datetime

logger = logging.getLogger(__name__)

class Raw2bulletin(FlowCB):

    def __init__(self,options) :
        super().__init__(options,logger)
        self.seq = 0
        self.binary = 0
        # Need to redeclare these options to have their default values be initialized.
        self.o.add_option('inputCharset', 'str', 'utf-8')
        self.o.add_option('binaryInitialCharacters', 'list', [b'BUFR' , b'GRIB', b'\211PNG'])

    # If file was converted, get rid of extensions it had
    def after_accept(self,worklist):

        good_msgs = []

        for msg in worklist.incoming:

            path = msg['new_dir'] + '/' + msg['new_file']

            data = self.getData(msg, path)

            # AM bulletins that need their filename rewritten with data should only have two chars before the first underscore
            # This is in concordance with Sundew logic -> https://github.com/MetPX/Sundew/blob/main/lib/bulletinAm.py#L70-L71
            # These messages are still good, so we will add them to the good_msgs list
            # if len(filenameFirstChars) != 2 and self.binary: 
            #     good_msgs.append(msg)
            #     continue

            if data == None:
                worklist.rejected.append(msg)
                continue
            
            lines  = data.split('\n')
            #first_line  = lines[0].strip('\r')
            #first_line  = first_line.strip(' ')
            #first_line  = first_line.strip('\t')
            first_line  = lines[0].split(' ')

            # Build header from bulletin
            header = self.buildHeader(first_line)
            if header == None:
                logger.error("Unable to fetch header contents. Skipping message")
                worklist.rejected.append(msg)
                continue
            
            # Get the station timestamp from bulletin
            if len(header.split('_')) == 2:
                ddhhmm = self.getTime(data)
                if ddhhmm == None:
                    logger.error("Unable to get julian time.")
            else:
                ddhhmm = ''
            
            # Get the BBB from bulletin
            BBB = self.getBBB(first_line)

            # Get the station ID from bulletin
            stn_id = self.getStation(data)

            # Generate a sequence (random ints)
            seq = self.getSequence()

            # Rename file with data fetched
            try:
                # We can't disseminate bulletins downstream if they're missing the timestamp, but we want to keep the bulletins to troubleshoot source problems
                # We'll append "_PROBLEM" to the filename to be able to identify erronous bulletins
                if ddhhmm == None:
                    timehandler = datetime.datetime.now()

                    # Add current time as new timestamp to filename
                    new_file = header + "_" + timehandler.strftime('%d%H%M') + "_" + BBB + "_" + stn_id + "_" + seq + "_PROBLEM"

                    # Write the file manually as the messages don't get posted downstream.
                    # The message won't also get downloaded further downstream
                    msg['new_file'] = new_file
                    new_path = msg['new_dir'] + '/' + msg['new_file']

                    with open(new_path, 'w') as f: f.write(data)

                    logger.error(f"New filename (for problem file): {new_file}")
                    raise Exception
                elif ddhhmm == '':
                    new_file = header + "_" + BBB + "_" + stn_id + "_" + seq
                else:
                    new_file = header + "_" + ddhhmm + "_" + BBB + "_" + stn_id + "_" + seq

                msg['new_file'] = new_file
                new_path = msg['new_dir'] + '/' + msg['new_file']

                logger.info(f"New filename (with path): {new_path}")

                good_msgs.append(msg)

            except Exception as e:
                logger.error(f"Error in renaming. Error message: {e}")
                worklist.rejected.append(msg)
                continue

        worklist.incoming = good_msgs


    def getData(self, msg, path):
        """Get the bulletin data.
           We can either get the bulletin data via
               1. Sarracenia message content
               2. Locally downloaded file
        """

        # Read file data from message or from file path directly if message content not found.
        # For the binary data, only extract first line (header) as that is all we need. The ascii decoding fails with the rest of the bulletin (usually).
        try:

            self.binary = 0
            if msg['content']:
                data = msg['content']['value']

                # Change from b64. We want to get the header from the raw binary data. Not retrievable in b64 format
                if msg['content']['encoding'] == 'base64':
                    data = b64decode(data).splitlines()[0].decode('ascii')
                    self.binary = 1

            else:

                fp = open(path, 'rb')
                data = fp.read()
                fp.close()

                # Decode data, only text. The raw binary data contains the header in which we're interested.
                # Integrate inputCharset
                if data.splitlines()[1][:4] not in self.o.binaryInitialCharacters:
                    data = data.decode(self.o.inputCharset)
                else:
                    data = data.splitlines()[0].decode('ascii')
                    self.binary = 1


            return data

        except Exception as e:
            logger.error(f"Could not fetch file data of from either message content or {path}. Error details: {e}")
            return None


    def getSequence(self):
        """ sequence number to make the file unique...
        """
        self.seq = self.seq + 1
        if self.seq > 99999:
            self.seq = 1
        return str(self.seq).zfill(5)


    def getStation(self, data):
        """Extracted from Sundew code: https://github.com/MetPX/Sundew/blob/main/lib/bulletin.py#L327-L408
           Get the station ID from the bulletin contents.
           Examples:
              CACN00 CWAO -> Station ID located on second line.
              FTCN32 CWAO -> Station ID located on first line (with header)
        """

        station = ''

        # There is no station in a binary bulletin
        if self.binary:
            return station

        data = data.lstrip('\n')
        data = data.split('\n')

        try:
            premiereLignePleine = ""
            deuxiemeLignePleine = ""

            # special case, need to get the next full line.
            i = 0
            for ligne in data[1:]:
                i += 1
                premiereLignePleine = ligne
                if len(premiereLignePleine) > 1:
                    if len(data) > i+1 : deuxiemeLignePleine = data[i+1]
                    break

            #print " ********************* header = ", data[0][0:7]
            # switch depends on bulletin type.
            if data[0][0:2] == "SA":
                if data[1].split()[0] in ["METAR","LWIS"]:
                    station = premiereLignePleine.split()[1]
                else:
                    station = premiereLignePleine.split()[0]

            elif data[0][0:2] == "SP":
                station = premiereLignePleine.split()[1]

            elif data[0][0:2] in ["SI","SM"]:
                station = premiereLignePleine.split()[0]
                if station == "AAXX" :
                    if deuxiemeLignePleine != "" :
                        station = deuxiemeLignePleine.split()[0]
                    else :
                        station = ''

            elif data[0][0:6] in ["SRCN40","SXCN40","SRMT60","SXAK50", "SRND20", "SRND30"]:
            #elif data[0][0:6] in self.wmo_id:
                station = premiereLignePleine.split()[0]

            elif data[0][0:2] in ["FC","FT"]:
                if premiereLignePleine.split()[1] == "AMD":
                    station = premiereLignePleine.split()[2]
                else:
                    station = premiereLignePleine.split()[1]

            elif data[0][0:2] in ["UE","UG","UK","UL","UQ","US"]:
                parts = premiereLignePleine.split()
                if parts[0][:2] in ['EE', 'II', 'QQ', 'UU']:
                    station = parts[1]
                elif parts[0][:2] in ['PP', 'TT']:
                    station = parts[2]
                else:
                    station = ''

            elif data[0][0:2] in ["RA","MA","CA"]:
                station = premiereLignePleine.split()[0].split('/')[0]
            
        except Exception:
            station = ''
        
        if station != '' :
            while len(station) > 1 and station[0] == '?' :
                station = station[1:]
            if station[0] != '?' :
                station = station.split('?')[0]
                if station[-1] == '=' : station = station[:-1]
            else :
                station = ''

        return station


    def getBBB(self, first_line):
        """Get the BBB. If none found, return empty string.
           The BBB is the field of the bulletin header that states if it was amended or not.
        """

        if len(first_line) != 4: 
            BBB = ''
        else:
            BBB = first_line[3]

        return BBB

    def buildHeader(self, first_line):
        """ Build header from file contents
        """

        try:
            T1T2A1A2ii = first_line[0]
            CCCC       = first_line[1]

            if len(first_line) >= 3:
                YYGGgg = first_line[2]
                header = T1T2A1A2ii + "_" + CCCC + "_" + YYGGgg
            else:  
                header = T1T2A1A2ii + "_" + CCCC # + "_" + YYGGgg

        except Exception:
            header = None

        return header


    def getTime(self, data):
        """ extract time from the data of the ca station
            the data's first line looks like this : x,yyyy,jul,hhmm,...
            where x is an integer of no importance, followed by obs'time
            yyyy = year
            jul  = julian day
            hhmm = hour and mins
        """

        try:
            parts = data.split(',')

            if len(parts) < 4: return None

            year = parts[1]
            jul = parts[2]
            hhmm = parts[3]

            # passe-passe pour le jour julien en float parfois ?
            f = float(jul)
            i = int(f)
            jul = '%s' % i
            # fin de la passe-passe

            # strange 0 filler

            while len(hhmm) < 4:
                hhmm = '0' + hhmm
            while len(jul) < 3:
                jul = '0' + jul

            # problematic 2400 for 00z

            if hhmm != '2400':
                emissionStr = year + jul + hhmm
                timeStruct = time.strptime(emissionStr, '%Y%j%H%M')
                ddHHMM = time.strftime("%d%H%M", timeStruct)
                return ddHHMM

            # sometime hhmm is 2400, to avoid exception
            # set time to 00, increase by 24 hr

            jul00 = year + jul + '0000'
            timeStruct = time.strptime(jul00, '%Y%j%H%M')
            ep_emission = time.mktime(timeStruct) + 24 * 60 * 60
            timeStruct = time.localtime(self.ep_emission)
            ddHHMM = time.strftime('%d%H%M', timeStruct)
            return ddHHMM
        except Exception as e:
            return None