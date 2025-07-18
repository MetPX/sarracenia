"""
Usage:
    callback convert.wmo00_split

    For use on reception of GTS WMO-00 format files from GTS nodes.

    Takes input WMO-00 grouping files, and outputs individual bulletins.
    Such files are produced by convert.wmo00_accumulate.

arguments:

    wmo00_work_directory   ... root of the tree to place the files in.
    wmo00_tree             ... flag write a tree or just flat? (default True)
    wmo00_encapsulate      ... write files with more headers.

    wmo00_encapsulate includes the inner header of WMO files::

    keep SOH + \r\r\n nnnnn \r\r\n AHL \r\r\n payload ETX
    
    When off, the files start with TTAAii (the AHL) as the first bytes.


    The tree is: TT/CCCC/GG

    e.g. wmo00_work_directory=/tmp/wmo00, tree=on

    writes:

    /tmp/wmo00/SA/CWAO/16/SACN88_CWAO_271630_02b49e5de0a3197a2a1c8d6f588ed585


Output:
    data without any WMO encapsulation (no SOH/ETX) 
    This means the first characters in the file is the AHL.
    
    
references:
    WMO-386 manual SFTP/FTP file naming convention

    https://library.wmo.int/viewer/35800/?offset=#page=157&viewer=picture&o=bookmark&n=0&q=



"""

from sarracenia.flowcb import FlowCB
import hashlib
import logging, random, subprocess, os
import os
import random
import sarracenia
import time

logger = logging.getLogger(__name__)

class Wmo00_split(FlowCB):

    def __init__(self,options) :
        super().__init__(options,logger)
        self.o.add_option(option='wmo00_work_directory', kind='str', default_value="/tmp")
        self.o.add_option(option='wmo00_tree', kind='flag', default_value=True)
        self.o.add_option(option='wmo00_encapsulate', kind='flag', default_value=True)
        self.o.baseDir=self.o.wmo00_work_directory

    def after_accept(self,worklist):

        if len(worklist.incoming) == 0:
            return

        old_incoming=worklist.incoming
        worklist.incoming=[]
        for m in old_incoming:
            logger.info( f"getting: {m['baseUrl']}{m['relPath']} " )
            input_data =m.getContent(self.o)

            if len(input_data) < 12:
                logger.error( f"file only {len(input_data)} bytes long, too small for a valid WMO message" )
                continue

            record_count=1
            current=0
            while current+13 < len(input_data):
                logger.debug( f"at byte {current} record {record_count} in stream" )
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
                logger.debug( f"consuming 10 byte outer header, payload length is: {payload_len}" )
                current += 10 

                if self.o.wmo00_encapsulate:
                    encapsulated_payload = input_data[current:current+payload_len]

                # skip second nnn wrapper.

                # type.SOH\r\r\n nnn \r\r\n  -->11 bytes
                payload_start= 10 if input_data[current+9] == b'\r' else 12
                logger.debug("consuming n-digit inner digit header")
                payload=input_data[current+payload_start:current+payload_len-1]
                     
                current += payload_len

                firstCr=payload.find( b'\r')

                ahl=payload[0:firstCr].decode('ascii')

                if len(ahl) < 18:
                    logger.error( f"invalid AHL {ahl} could not build file name, skipping...")
                    continue

                filename=ahl.replace(' ','_') 
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
                    filename += '_'

                if self.o.wmo00_encapsulate:
                    filename += '_' + hashlib.md5(encapsulated_payload).hexdigest()
                else:
                    filename += '_' + hashlib.md5(payload).hexdigest()

                logger.debug( f"TT={TT}, AA={AA}, ii={ii}, YY={YY}, GG={GG}, gg={gg} RRR={RRR}" )

                if self.o.wmo00_tree:
                    directory=f"{self.o.wmo00_work_directory}/{TT}/{CCCC}/{GG}"
                else:
                    directory=self.o.wmo00_work_directory

                fname=f"{directory}/{filename}"


                if not os.path.isdir(directory):
                    os.makedirs(directory, self.o.permDirDefault, True)
                 
                with open(fname,"wb") as f:
                    if self.o.wmo00_encapsulate:
                        f.write(encapsulated_payload)
                        logger.info( f"wrote {len(encapsulated_payload)} bytes to {fname} " )
                    else:
                        f.write(payload)
                        logger.info( f"wrote {len(payload)} bytes to {fname} " )
                msg = sarracenia.Message.fromFileData(fname, self.o, os.stat(fname))
                worklist.incoming.append(msg)
                record_count += 1

            logger.info( f"done with: {m['baseUrl']}{m['relPath']} records: {record_count}" )
