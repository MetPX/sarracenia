"""
Usage:
    callback filter.wmo00_accumulate

    takes input WMO bulletins, and puts them in a accumulated file suitable 
    sending to a GTS peer that expects WMO-00 format messages.

    There is a corresponding filter.wmo00_split module for reception of such data.

    batch --> sets how many messages per accumulated file, WMO standard says 100 max.
    sleep --> can use used to produce collections once every *sleep* seconds.

    maximum message rate = sleep*batch

    options:

    wmo00_work_directory  setting is the directory where the accumulated file will be assembled.
    wmo00_origin_CCCC the WMO Origin code for the centre emitting the file.
    wmo00_type_marker typically just 'a' for alphanumeric or 'b' for binary, or 'ua' 'ub'
                    for urgent bulletins of either type. used as a filename suffix.
    
    Usage note: about type_marker, historically, there was a division between alphanumeric 
    and binary bulletins. As time has progressed, it has become increasingly unclear what 
    the distinction means. It seems most people just ship everything over the alphanumeric 
    channel. so 'a'' seems to be ok for everybody. It isn't worth the hassle to set up 
    separate channels for alpha and binary, which looks like an obsolete practice on the GTS.


    options not usually set:

    wmo00_byteCountMax ... maximum size for an individual product to be inserted into a accumulated file.
                           (default from: WMO standard says 500,000 bytes)

    wmo00_accumulatedByteCountMax ... maximum size for the group file.
                          (default from: WMO standard says 100 products * 500,000 bytes each ?) 

references:

    WMO-386 manual SFTP/FTP file naming convention

    https://library.wmo.int/viewer/35800/?offset=#page=157&viewer=picture&o=bookmark&n=0&q=

implementation notes:

    This module calculates checksums for data with all WMO headers removed, and writes them to the log.
    The companion filter.wmo00_split puts checksums on the same basis as the end of the filenames.
    
    for rountrip testing, just call both from the same module.  the output of one, is good as input
    for the other.

    encountered "WMO" bulletins with three different formats:

    just starting with the header UANT32 CWAO ...
    with an inner WMO header    SOH\r\r\nnnnnn\r\rnUANT32 CWAO ...  ETX
       * note: nnn is also a permitted value.
       * value of nnn is unknown... sometimes it matches length, sometimes an unknown number
       * does not appear to be a sequence number.
    with an outer WMO header    999999999\0\0SOH ... 

    * The WMO00 output file has to have both headers for each item.
    * Since the presence/absence of the headers on input cannot be recorded 
      the corresponding wmo00_split module just has to pick a format to write out.

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

class Wmo00_accumulate(FlowCB):


    def __init__(self,options) :
        super().__init__(options,logger)
        self.o.add_option(option='wmo00_work_directory', kind='str', default_value="/tmp")
        self.o.add_option(option='wmo00_origin_CCCC', kind='str', default_value="XXXX")
        self.o.add_option(option='wmo00_type_marker', kind='str', default_value="a")
        self.o.add_option(option='wmo00_encapsulate', kind='flag', default_value=True)
        self.o.add_option(option='wmo00_byteCountMax', kind='size', default_value=500000)
        self.o.add_option(option='wmo00_accumulatedByteCountMax', kind='size', default_value=50000000)

        if self.o.batch > 100:
            logger.warning( f"batch limits how many products fit into one accumulated file.")
            logger.warning( f"WMO says this should not exceed 100: batch: {self.o.batch} ")

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

        self.sequence_second_digit=self.o.no%10
        if self.o.no > 10:
            logger.info( f"instance numbers > 10 accumulated file names can clash. {self.sequence_second_digit} ") 

        logger.info( f"sequence number second digit matches instance number: {self.sequence_second_digit} ") 

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

    def open_accumulated_file(self):

        self.accumulated_file=f"{self.o.wmo00_work_directory}/{self.o.wmo00_origin_CCCC}{self.sequence_first_digit}{self.sequence_second_digit:01d}{self.sequence:06d}.{self.o.wmo00_type_marker}"

        self.sequence += 1
        if self.sequence > 999999:
            self.sequence = 0

        return open(self.accumulated_file,"wb")


    def after_accept(self,worklist):

        if len(worklist.incoming) == 0:
            return

        today=time.gmtime().tm_mday
        if today != self.thisday:
            self.thisday=today
            self.sequence=0

        output_file=self.open_accumulated_file()
        output_length=0
        record_no=1
        old_incoming=worklist.incoming
        worklist.incoming=[]
        new_incoming=[]
        for m in old_incoming:
            logger.info( f" getting: {m['baseUrl']}{m['relPath']} " )
            input_data =m.getContent(self.o)

            if len(input_data) < 12:
                logger.error( f"file only {len(input_data)} bytes long, too small for a valid WMO message" )
                continue

            if len(input_data) > self.o.wmo00_byteCountMax:
                logger.error( f"files must be smaller than {self.o.wmo00_byteCountMax}" )
                continue

            # 22 is the maximum size of an envelope that might be added to the input if it doesn't have it.
            if output_length + len(input_data) + 22  > self.o.wmo00_accumulatedByteCountMax :
                output_file.close()
                msg = sarracenia.Message.fromFileData(self.accumulated_file, self.o, os.stat(self.accumulated_file))
                logger.info( f"accumulated file {self.accumulated_file} written {msg['size']} bytes, {record_no-1} records" )
                worklist.incoming.append(msg)
                output_file=self.open_accumulated_file()
                output_length=0
                record_no=1

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
                       offset = 2 if n5hdr else 0
                       if self.o.wmo00_encapsulate:
                           data_sum=hashlib.md5(input_data[offset:]).hexdigest()
                       else:
                           data_sum=hashlib.md5(input_data[10+offset:-1]).hexdigest()

                       input_data="\1".encode('ascii') + input_data + "\3".encode('ascii')
                   else:
                       data_sum=hashlib.md5(input_data).hexdigest()
                       # 13 ==  size of the first envelope ... SOH\r\r\n 5 digits\r\r\n <payload> ETX.)
                       #   how many bytes needed for envelope:   1     4        9    12 ....      13.
                       input_data= (f"\1\r\r\n{len(input_data)+13:05d}\r\r\n").encode('ascii') + input_data + "\3".encode('ascii')
                else:
                    logger.debug( "looks like a valid WMO inner envelope." )
                    n5hdr = ( input_data[1:4] == b'\r\r\n' ) and input_data[4:9].decode('ascii').isnumeric() \
                            and ( input_data[9:12] == b'\r\r\n'  )
                    payload_start = 12 if n5hdr else 10 
                    #logger.debug( f" n5hdr={n5hdr} to be checksummed: {input_data[payload_start:-1]}" )
                    if self.o.wmo00_encapsulate:
                        data_sum=hashlib.md5(input_data).hexdigest()
                    else:
                        data_sum=hashlib.md5(input_data[payload_start:-1]).hexdigest()

                # the len on the inner and outer headers is the same afaict.
                # the \0 is a format identifier.
                output_record = f"{len(input_data):08d}\0\0".encode('ascii') + input_data


            else:
                logger.debug("valid WMO outer envelope")
                output_record=input_data
                n5hdr = ( input_data[11:14] == b'\r\r\n' ) and input_data[14:19].decode('ascii').isnumeric() \
                        and ( input_data[19:22] == b'\r\r\n'  )
                payload_start = 22 if n5hdr else 20
                if self.o.wmo00_encapsulate:
                    data_sum=hashlib.md5(input_data[10:]).hexdigest()
                else:
                    data_sum=hashlib.md5(input_data[payload_start:-1]).hexdigest()

            output_file.write( output_record )
            output_length += len(input_data)+10
            logger.info( f"appended {len(input_data)} to {self.accumulated_file}, offset now: {output_length} sum: {data_sum}")
            record_no+=1

        output_file.close()
        msg = sarracenia.Message.fromFileData(self.accumulated_file, self.o, os.stat(self.accumulated_file))

        if msg['size'] > 0 : 
            logger.info( f"accumulated file {self.accumulated_file} written {msg['size']} bytes, {record_no-1} records" )
            worklist.incoming.append(msg)
        else:
            logger.debug( f"empty accumulated file {self.accumulated_file} being removed and reused." )
            os.unlink( self.accumulated_file )
            #re-use the sequence number.
            if self.sequence > 0:
                self.sequence -= 1

      

    def on_stop(self):

        with open(self.sequence_file, "w") as sf:
            sf.write( f"{self.thisday} {self.sequence}" )

        pass

