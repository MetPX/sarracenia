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

class Wmo00_write(FlowCB):


    def __init__(self,options) :
        super().__init__(options,logger)
        self.o.add_option(option='work_directory', kind='str', default_value="/tmp")
        self.o.add_option(option='wmo_origin_CCCC', kind='str', default_value="XXXX")
        self.o.add_option(option='wmo_type_marker', kind='str', default_value="a")

        # FIXME: note for later, assign first digit based on node number in cluster.
        logger.info( f" hostname: {self.o.hostname} ")
        hostname_end = self.o.hostname.split('.')[0][-1]
        if hostname_end.isnumeric():
             self.sequence_first_digit=int(hostname_end)
             logger.info( f"sequence number first digit set to match last digit of hostname: {self.sequence_first_digit} ") 
        else:
             self.sequence_first_digit=random.randint(0,9)
             logger.info( f"sequence number first digit randomized: {self.sequence_first_digit} ") 

        # FIXME: does starting point matter?
        self.sequence_file=os.path.dirname(self.o.pid_filename) + f"/sequence_{self.o.no:02d}.txt"

        logger.info( f"sequence number second digit matches instance number: {self.o.no} ") 

        self.thisday=time.gmtime().tm_mday

        if os.path.isfile(self.sequence_file):
            with open(self.sequence_file,'r') as sf:
                seq_data=sf.read().split(' ')
                self.thisday=int(seq_data[0])
                self.sequence=int(seq_data[1])
            logger.info( f"read main sequence number from file: {self.sequence} ") 
        else:
            self.sequence=0
            logger.info( f"main sequence initialized: {self.sequence} ") 



    def after_accept(self,worklist):

        if len(worklist.incoming) == 0:
            return

        today=time.gmtime().tm_mday
        if today != self.thisday:
            self.thisday=today
            self.sequence=1

        grouped_file=f"{self.o.work_directory}/{self.o.wmo_origin_CCCC}{self.sequence_first_digit}{self.o.no:02d}{self.sequence:06d}.{self.o.wmo_type_marker}"
        output_file=open(grouped_file,"wb")
        output_length=0
        record_no=1
        old_incoming=worklist.incoming
        worklist.incoming=[]
        new_incoming=[]
        for m in old_incoming:
            logger.info( f" getting: {m['baseUrl']}{m['relPath']} " )
            input_data =m.getContent(self.o)

            if len(input_data) < 12:
                logger.error( f" file only {len(input_data)} bytes long, too small for a valid WMO message" )
                continue

            # if it starts with SOH already, assume valid, otherwise encapsulate.
            data_sum='unknown'
            if input_data[8:11] !=  b'00\x01' :
                if input_data[0] != SOH  : 
                   # does it start with the AHL? or does it have the length header?
                   n3hdr = ( input_data[0:3] == b'\r\r\n' ) and input_data[3:6].decode('ascii').isnumeric() and ( input_data[6:9] == b'\r\r\n'  )

                   n5hdr = ( input_data[0:3] == b'\r\r\n' ) and input_data[3:8].decode('ascii').isnumeric() and ( input_data[8:11] == b'\r\r\n' )

                   # Add length header if missing.
                   # length is the length of the payload + the SOH and ETX chars.
                   if n3hdr or n5hdr:
                       if n3hdr:
                           data_sum=hashlib.md5(input_data[10:-1]).hexdigest()
                       else:
                           data_sum=hashlib.md5(input_data[12:-1]).hexdigest()

                       input_data="\1".encode('ascii') + input_data + "\3".encode('ascii')
                   else:
                       data_sum=hashlib.md5(input_data).hexdigest()
                       # 13 ==  size of the first envelope ... SOH\r\r\n 5 digits\r\r\n <payload> ETX.)
                       #   how many bytes needed for envelope:   1     4        9    12 ....      13.
                       input_data= (f"\1\r\r\n{len(input_data)+13:05d}\r\r\n").encode('ascii') + input_data + "\3".encode('ascii')
                else:
                    logger.info( "looks like a valid WMO inner envelope." )
                    n5hdr = ( input_data[1:4] == b'\r\r\n' ) and input_data[4:9].decode('ascii').isnumeric() \
                            and ( input_data[9:12] == b'\r\r\n'  )
                    payload_start = 12 if n5hdr else 10 
                    logger.info( f" n5hdr={n5hdr} to be checksummed: {input_data[payload_start:-1]}" )
                    data_sum=hashlib.md5(input_data[payload_start:-1]).hexdigest()

                # the len on the inner and outer headers is the same afaict.
                # the \0 is a format identifier.
                output_record = f"{len(input_data):08d}\0\0".encode('ascii') + input_data


            else:
                logger.info("valid WMO outer envelope")
                output_record=input_data
                n5hdr = ( input_data[11:14] == b'\r\r\n' ) and input_data[14:19].decode('ascii').isnumeric() \
                        and ( input_data[19:22] == b'\r\r\n'  )
                payload_start = 22 if n5hdr else 20
                data_sum=hashlib.md5(input_data[payload_start:-1]).hexdigest()

            output_file.write( output_record )
            output_length+=len(input_data)+10
            logger.info( f"appended {len(input_data)} to {grouped_file}, offset now: {output_length} sum: {data_sum}")
            record_no+=1

        output_file.close()
        msg = sarracenia.Message.fromFileData(grouped_file, self.o, os.stat(grouped_file))

        logger.info( f" grouped_file {grouped_file} {msg['size']} bytes, {record_no-1} records" )
        worklist.incoming=[ msg ]

        self.sequence+=1
        if self.sequence > 999999:
            self.sequence == 0

      

    def on_stop(self):

        with open(self.sequence_file, "w") as sf:
            sf.write( f"{self.thisday} {self.sequence}" )

        pass

