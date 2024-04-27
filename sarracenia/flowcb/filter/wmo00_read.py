"""
Usage:
    callback convert.wmo00_write

    WMO-386 manual SFTP/FTP file naming convention

    https://library.wmo.int/viewer/35800/?offset=#page=157&viewer=picture&o=bookmark&n=0&q=

    takes input WMO bulletins, and puts them in a grouping file.

    batch --> sets how many messages per grouping file, WMO standard says 100 max.

    sleep --> can use used to produce collections once every *sleep* seconds.

    maximum message rate = sleep*batch



"""

from curses.ascii import SOH,ETX
from sarracenia.flowcb import FlowCB
import hashlib
import logging, random, subprocess, os
import os
import random
import sarracenia
import time

logger = logging.getLogger(__name__)

class Wmo00_read(FlowCB):

    def __init__(self,options) :
        super().__init__(options,logger)
        self.o.add_option(option='work_directory', kind='str', default_value="/tmp")
        self.o.baseDir=self.o.work_directory

    def after_accept(self,worklist):

        if len(worklist.incoming) == 0:
            return

        old_incoming=worklist.incoming
        worklist.incoming=[]
        for m in old_incoming:
            logger.info( f" getting: {m['baseUrl']}{m['relPath']} " )
            input_data =m.getContent(self.o)

            if len(input_data) < 12:
                logger.error( f" file only {len(input_data)} bytes long, too small for a valid WMO message" )
                continue

            record_count=1
            current=0
            while current+13 < len(input_data):
                logger.info( f"at byte {current} record {record_count} in stream" )
                # should be at start of record, 8 bytes recordlength.
                try:
                    payload_len_str = input_data[current:current+8]
                    payload_len = int(payload_len_str)
                except:
                    logger.error( f"corrupt grouping file expected 8 digit ascii length. Got: {payload_len_str}" )
                    logger.error( f"skipping rest of file" )
                    current=len(input_data)
                    continue
                
                if current+payload_len > len(input_data):
                    logger.error( f"record corrupt, length goes past end of file" ) 
                    current=len(input_data)
                    continue

                # skip first len header.
                logger.info( f"consuming 10 byte initial header, payload length is: {payload_len}" )
                current += 10 

                # skip second nnn wrapper.
                if input_data[current+9] == '\r': # 3 digit len header
                    # type.SOH\r\r\n nnn \r\r\n  -->11 bytes
                    logger.info("consuming 3 digit nnn header")
                    payload=input_data[current+10:current+payload_len-1]
                else: # 5 digit length header
                    logger.info("consuming 5 digit nnnnn header")
                    payload=input_data[current+12:current+payload_len-1]
                     
                current += payload_len

                firstCr=payload.find( b'\r')

                ahl=payload[0:firstCr].decode('ascii')

                if len(ahl) < 18:
                    logger.error( f"invalid AHL {ahl} could not build file name, skipping...")
                    continue

                filename=ahl.replace(' ','_') + '_' + hashlib.md5(payload).hexdigest()
                TT=ahl[0:2] 
                AA=ahl[2:4]
                ii=ahl[4:6]
                CCCC=ahl[7:11]

                YY=ahl[12:14]
                GG=ahl[14:16]
                gg=ahl[16:18]

                if len(ahl) > 19:
                    RRR=ahl[19:22]
                else:
                    RRR=None

                logger.info( f" ready to write {len(payload)} bytes to {filename} " )
                logger.info( f" TT={TT}, AA={AA}, ii={ii}, YY={YY}, GG={GG}, gg={gg} RRR={RRR}" )

                directory=f"{self.o.work_directory}/{TT}/{CCCC}/{GG}"
                fname=f"{directory}/{filename}"

                logger.info( f" fname={fname}" )

                if not os.path.isdir(directory):
                    os.makedirs(directory, self.o.permDirDefault, True)
                 
                with open(fname,"wb") as f:
                     f.write(payload)
                msg = sarracenia.Message.fromFileData(fname, self.o, os.stat(fname))
                worklist.incoming.append(msg)
                record_count += 1

            logger.info( f" done with: {m['baseUrl']}{m['relPath']} records: {record_count}" )
        logger.info( f"Done." )
      

