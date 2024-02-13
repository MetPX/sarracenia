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

Usage:
   callback rename.raw2bulletin

Contributions:
    Andre LeBlanc - First author (2024/02)

Improvements:
    Delegate some of the generalized methods to a parent class. To be callable by other plugins.
    Add more Sundew logic if ever some bulletins end up failing when implemented
"""

from sarracenia.flowcb import FlowCB
import logging
from base64 import b64encode
import time

logger = logging.getLogger(__name__)

class Raw2bulletin(FlowCB):

    def __init__(self,options) :
        super().__init__(options,logger)
        self.seq = 0
        # self.o.add_option('headers2rename', 'list', ['CA', 'MA' , 'RA'])
        # Need to redeclare these options to have their default values be initialized.
        self.o.add_option('inputCharset', 'str', 'utf-8')
        self.o.add_option('binaryInitialCharacters', 'list', [b'BUFR' , b'GRIB', b'\211PNG'])

    # If file was converted, get rid of extensions it had
    def after_accept(self,worklist):

        good_msgs = []

        for msg in worklist.incoming:

            path = msg['new_dir'] + '/' + msg['new_file']

            filenameFirstChars = msg['new_file'].split('_')[0]

            # AM bulletins that need their filename rewritten with data should only have two chars before the first underscore
            # This is concordance with Sundew logic -> https://github.com/MetPX/Sundew/blob/main/lib/bulletinAm.py#L70-L71
            # These messages are still good, so we will add them to the good_msgs list
            if len(filenameFirstChars) != 2:
                good_msgs.append(msg)
                continue

            data = self.getData(msg, path)

            if data == None:
                worklist.rejected.append(msg)
                continue
            
            ### Alternative to check for bulletins that need their filename rewritten ###

            # ok = 0
            # for header in self.o.headers2rename:
            # 	_len = len(header)
            # 	# Check if first chars of header match the ones we want to rename
            # 	if data.split(b'\n')[0][0:_len] == header:
            # 		ok = 1
            # 		break
            
            # # If nothing has matched, skip to the next iteration
            # if ok == 0:
            # 	continue

            lines  = data.split('\n')
            #first_line  = lines[0].strip('\r')
            #first_line  = first_line.strip(' ')
            #first_line  = first_line.strip('\t')
            first_line  = lines[0].split(' ')

            ddhhmm = None

            # Build header from bulletin
            header = self.buildHeader(first_line)
            if header == None:
                logger.error("Unable to fetch header contents. Skipping message")
                worklist.rejected.append(msg)
                continue
            
            # Get the station timestamp from the file contents
            ddhhmm = self.getTime(data)
            if ddhhmm == None:
                logger.error("Unable to get julian time. Skipping message")
                worklist.rejected.append(msg)
                continue
            
            # Get the BBB
            BBB = self.getBBB(first_line)

            # Get the station ID
            stn_id = self.getStation(data)

            # Get sequence (random ints)
            seq = self.getSequence()

            # Rename file with data fetched
            try:
                new_file = header + "_" + ddhhmm + "_" + BBB + "_" + stn_id + "_" + seq

                msg['new_file'] = new_file
                new_path = msg['new_dir'] + '/' + msg['new_file']

                logger.info(f"New filename (with path): {new_path}")

                good_msgs.append(msg)

            except Exception as e:
                logger.error(f"Unable to rename filename. Error message: {e}")
                worklist.rejected.append(msg)
                continue

        worklist.incoming = good_msgs


    def getData(self, msg, path):

        # Read file data from message or from file path directly if message content not found.
        try:

            binary = 0
            if msg['content']:
                data = msg['content']['value']
            else:

                fp = open(path, 'rb')
                data = fp.read()
                # bulletin = Bulletin(data)
                fp.close()

                # Decode data, binary and text. Integrate inputCharset
                if data.splitlines()[1][:4] in self.o.binaryInitialCharacters:
                    binary = 1

                if not binary:
                    data = data.decode(self.o.inputCharset)
                else:
                    data = b64encode(data).decode('ascii')

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
           Some station ID's are located on different lines (depends on the bulletin)
           Use stn_id_loc to determine which line holds the station ID.
           Examples:
              CACN00 CWAO -> Station ID located on second line.
              FTCN32 CWAO -> Station ID located on first line (with header)
        """

        station = ''
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
            # YYGGgg     = parts[2]

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
