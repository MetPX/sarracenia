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

        if os.path.isfile(self.sequence_file):
            with open(self.sequence_file,'r') as sf:
                self.sequence=int(sf.read())
            logger.info( f"read main sequence number from file: {self.sequence} ") 
        else:
            self.sequence=0
            logger.info( f"main sequence initialized: {self.sequence} ") 

        self.thisday=time.gmtime().tm_mday


    def after_accept(self,worklist):

        if len(worklist.incoming) == 0:
            return

        today=time.gmtime().tm_mday
        if today != self.thisday:
            self.thisday=today
            self.sequence=1

        grouped_file=f"{self.o.work_directory}/{self.o.wmo_origin_CCCC}{self.sequence_first_digit}{self.o.no:02d}{self.sequence:06d}.{self.o.wmo_type_marker}"
        output_file=open(grouped_file,"wb")

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
            if input_data[0] != SOH :

               # does it start with the AHL? or does it have the length header?
               has_len_hdr = ( input_data[0:3] == '\r\r\n' and (str(input_data[3:6]).isnumeric() and input_data[6:9] == '\r\r\n'  )
                    or  (str(input_data[3:8]).isnumeric() and input_data[8:11] == '\r\r\n'  ))

               # Add length header if missing.
               # length is the length of the payload + the SOH and ETX chars.
               if has_len_hdr:
                   input_data="\1".encode('ascii') + input_data + "\3".encode('ascii')
               else:
                   # 13 ==  size of the first envelope ... SOH\r\r\n 5 digits\r\r\n <payload> ETX.)
                   #   how many bytes needed for envelope:   1     4        9    12 ....      13.
                   input_data= (f"\1\r\r\n{len(input_data)+13:05d}\r\r\n").encode('ascii') + input_data + "\3".encode('ascii')

            # the len on the inner and outer headers is the same afaict.
            # the \0 is a format identifier.
            output_record = f"{len(input_data):08d}\0\0".encode('ascii') + input_data
            output_file.write( output_record )
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
            sf.write( f"{self.sequence}" )

        pass

