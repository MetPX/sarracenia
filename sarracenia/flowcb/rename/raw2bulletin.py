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

       Output filename: ISAA41_CYZX_162000___00004  

Usage:
    callback rename.raw2bulletin
    --- OR (inside callback) ---
    from sarracenia.flowcb.rename.raw2bulletin import Raw2bulletin
    def __init__():
        super().__init__(options,logger)
        self.renamer = Raw2bulletin(self.o)


Contributions:
    Andre LeBlanc - First author (2024/02)

Improvements:
    Delegate some of the generalized methods to a parent class. To be callable by other plugins.
"""

from sarracenia.flowcb import FlowCB
from sarracenia.bulletin import Bulletin
import logging
import datetime

logger = logging.getLogger(__name__)

class Raw2bulletin(FlowCB):

    def __init__(self,options) :
        super().__init__(options,logger)
        self.seq = 0
        self.binary = 0
        self.bulletinHandler = Bulletin()
        # Need to redeclare these options to have their default values be initialized.
        self.o.add_option('inputCharset', 'str', 'utf-8')
        self.o.add_option('binaryInitialCharacters', 'list', [b'BUFR' , b'GRIB', b'\211PNG'])

    # If file was converted, get rid of extensions it had
    def after_accept(self,worklist):

        new_worklist = []

        for msg in worklist.incoming:
            path = msg['new_dir'] + '/' + msg['new_file']

            data = self.bulletinHandler.getData(msg, path)

            # AM bulletins that need their filename rewritten with data should only have two chars before the first underscore
            # This is in concordance with Sundew logic -> https://github.com/MetPX/Sundew/blob/main/lib/bulletinAm.py#L70-L71
            # These messages are still good, so we will add them to the good_msgs list
            # if len(filenameFirstChars) != 2 and self.binary: 
            #     good_msgs.append(msg)
            #     continue

            if data == None:
                logger.error("No data was found. Skipping message")
                worklist.rejected.append(msg)
                continue
            
            lines  = data.split('\n')
            #first_line  = lines[0].strip('\r')
            #first_line  = first_line.strip(' ')
            #first_line  = first_line.strip('\t')
            first_line  = lines[0].split(' ')

            # Build header from bulletin
            header = self.bulletinHandler.buildHeader(first_line)
            if header == None:
                logger.error("Unable to fetch header contents. Skipping message")
                worklist.rejected.append(msg)
                continue
            
            # Get the station timestamp from bulletin
            if len(header.split('_')) == 2:
                ddhhmm = self.bulletinHandler.getTime(data)
                if ddhhmm == None:
                    logger.error("Unable to get julian time.")
            else:
                ddhhmm = ''
            
            # Get the BBB from bulletin
            BBB = self.bulletinHandler.getBBB(first_line)

            # Get the station ID from bulletin
            stn_id = self.bulletinHandler.getStation(data)

            # Generate a sequence (random ints)
            seq = self.bulletinHandler.getSequence()

            

            # Rename file with data fetched
            try:
                # We can't disseminate bulletins downstream if they're missing the timestamp, but we want to keep the bulletins to troubleshoot source problems
                # We'll append "_PROBLEM" to the filename to be able to identify erronous bulletins
                if ddhhmm == None or msg["isProblem"]:
                    timehandler = datetime.datetime.now()

                    # Add current time as new timestamp to filename
                    new_file = header + "_" + timehandler.strftime('%d%H%M') + "_" + BBB + "_" + stn_id + "_" + seq + "_PROBLEM"

                    # Write the file manually as the messages don't get posted downstream.
                    # The message won't also get downloaded further downstream
                    msg['new_file'] = new_file
                    new_path = msg['new_dir'] + '/' + msg['new_file']

                    # with open(new_path, 'w') as f: f.write(data)

                    logger.error(f"New filename (for problem file): {new_file}")
                elif stn_id == None:
                    new_file = header + "_" + BBB + "_" + '' + "_" + seq + "_PROBLEM"
                    logger.error(f"New filename (for problem file): {new_file}")
                elif ddhhmm == '':
                    new_file = header + "_" + BBB + "_" + stn_id + "_" + seq
                else:
                    new_file = header + "_" + ddhhmm + "_" + BBB + "_" + stn_id + "_" + seq

                msg['new_file'] = new_file
                # We need the rest of the fields to be also updated
                del(msg['relPath'])
                # No longer needed
                del(msg['isProblem'])
                msg.updatePaths(self.o, msg['new_dir'], msg['new_file'])

                logger.info(f"New filename (with path): {msg['relPath']}")
                new_worklist.append(msg)
                
            except Exception as e:
                logger.error(f"Error in renaming. Error message: {e}")
                continue

        worklist.incoming = new_worklist
