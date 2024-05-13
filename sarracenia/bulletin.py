import logging
import time 
import re
from base64 import b64decode

logger = logging.getLogger(__name__)


class Bulletin:
    """
        Parent class to be callable by all bulletin handling processes.

        Holds general methods that are applicable to either
            Modifying bulletin file contents
            Modifying bulletin filenames

        Also holds some code used in CA bulletins uniquely.

        Spawned from analysts realizing that lots of bulletin handlers/plugins use the same methods repeatedly.
        This is in turn will reduce duplicate code throughout.

        Usage:
            from sarracenia.bulletin import Bulletin
    """

    def __init__(self):
        self.seq = 0
        self.binary = 0

    def _verifyYear(self, bulletin_year):
        """ Derived from missing https://github.com/MetPX/Sundew/blob/main/lib/bulletinAm.py -> tokIsYear
            Checks if the year that was appended to the bulletin contents is valid or not.
            This is only applicable for CA type bulletins (based on Sundew code).
        """

        ltime = time.localtime()
        current_year  = time.strftime("%Y",ltime )
        previous_year = str(int(current_year) - 1)

        # Prevent all bulletins being rejected on a new year for a couple of minutes. Check for previous year as well
        if bulletin_year == current_year or bulletin_year == previous_year    : return True
        if len(bulletin_year) !=    4       : return False
        if bulletin_year[:1]  !=  '2'       : return False

        return True

    def verifyHeader(self, header, charset):
        """Derived from Sundew -> https://github.com/MetPX/Sundew/blob/main/lib/bulletin.py#L601-L671.
           Verifies the integrity of the bulletin header. Flag if there is an error in the header.
           Called by the buildHeader method.
        """

        isProblem = False
        rebuild = 0

        # Remove duplicate spaces
        tokens = header.split(b' ')
        header = b' '.join(tokens)

        if header==b'':
            logger.error("Header is empty when it shouldn't be.")
            isProblem = True
            return header, isProblem
 
        tokens = header.split(b' ')

        # Header can't miss the timestamp. Don't raise an error however, as we want these bulletins added as a PROBLEM file locally. 
        if len(tokens) < 3:
            logger.error('Incomplete header (less than 3 fields)')
            return header, isProblem

        # Remove the ['z', 'Z'] or ['utc', 'UTC'] if they're present in the group DDHHmm
        if len(tokens[2]) > 6: 
            tokens[2] = tokens[2][0:6]
            logger.info("Header normalized (%s): truncated the DDHHMM group (>6 characters)" % str(header))
            rebuild = 1

        # Verify first three fields, T1T2AiA2ii CCCC DDHHmm -> https://www.weather.gov/tg/headef 
        if not tokens[0].isalnum() or len(tokens[0]) not in [4,5,6] or \
           not tokens[1].isalnum() or len(tokens[1]) not in [4,5,6] or \
           not tokens[2].isdigit() or len(tokens[2]) != 6 or \
           not (0 <  int(tokens[2][:2]) <= 31) or not(00 <= int(tokens[2][2:4]) <= 23) or \
           not(00 <= int(tokens[2][4:]) <= 59):
            logger.error('Malformed header (some of the first 3 fields corrupt).')
            isProblem = True
            return header, isProblem

        # If there is no BBB or more, return to prevent error
        if len(tokens) == 3:
            if rebuild:
                header = b' '.join(tokens)
            return header, isProblem

        # Verify BBB field(s) -> https://www.weather.gov/tg/headef. Remove it if it's corrupted.
        if not tokens[3].isalpha() or len(tokens[3]) != 3 or tokens[3].decode(charset)[0] not in ['C','A','R','P']:
            logger.info("Header normalized: fourth and later fields removed.") 
            del tokens[3:]
            rebuild = 1

        if len(tokens) == 5 and \
                (not tokens[4].isalpha() or len(tokens[4]) != 3 or tokens[4].decode(charset)[0] not in ['C','A','R','P']):
            logger.info("Header normalized: fifth and later fields removed")
            del tokens[4:]
            rebuild = 1

        if len(tokens) > 5:
            logger.info("Header normalized: sixth and later fields removed")
            del tokens[5:]
            rebuild = 1

        if rebuild:
            header = b' '.join(tokens)

        return header,isProblem

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

            # Added to SR3
            # The station needs to be alphanumeric, between 3 and 5 characters. If not, don't assign a station
            if re.search('^[a-zA-Z0-9]{3,5}$', station) == None:
                station = None

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

            year = parts[1]
            jul = parts[2]
            hhmm = parts[3]

            if parts[0][:2] == "CA":
                # Need to verify time for CA bulletins.
                if not self._verifyYear(year):
                    logger.error("Unable to verify year from julian time.")
                    return None

            if len(parts) < 4: return None

            # Julian days shouldn't be float type. Reject them when found. They should only be integers.
            if '.' in jul:
                logger.error("Julian days can't be of float type.")
                return None

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
            timeStruct = time.localtime(ep_emission)
            ddHHMM = time.strftime('%d%H%M', timeStruct)
            return ddHHMM
        except Exception as e:
            return None