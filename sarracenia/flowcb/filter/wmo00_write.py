"""
Usage:
    callback convert.wmo00_write

    WMO-386 manual SFTP/FTP file naming convention

    https://library.wmo.int/viewer/35800/?offset=#page=157&viewer=picture&o=bookmark&n=0&q=

"""

from curses.ascii import SOH,ETX
from sarracenia.flowcb import FlowCB
import logging, random, subprocess, os
import os
import sarracenia

logger = logging.getLogger(__name__)

class Wmo00_write(FlowCB):


    def __init__(self,options) :
        super().__init__(options,logger)
        self.o.add_option(option='work_directory', kind='str', default_value="/tmp")
        self.o.add_option(option='wmo_origin_CCCC', kind='str', default_value="XXXX")
        self.o.add_option(option='wmo_type_marker', kind='str', default_value="a")

        # FIXME: note for later, assign first digit based on node number in cluster.
        self.sequence_first_digit=0

        # FIXME: does starting point matter?
        self.sequence=0

    def after_accept(self,worklist):

        if len(worklist.incoming) == 0:
            return

        grouped_file=f"{self.o.work_directory}/{self.o.wmo_origin_CCCC}{self.sequence_first_digit}{self.sequence:05d}.{self.o.wmo_type_marker}"
        output_file=open(grouped_file,"w")

        sequence_no=1
        new_incoming=[]
        for m in worklist.incoming:
            input_data =m.getContent(self.o)

            # length is the payload + the SOH and ETX chars.
            # the \0 is a format identifier.
            output_record = f"{len(input_data)+2:08d}\0\r\r\n{sequence_no:03d}\r\r\n{SOH}{input_data}{ETX}"
            output_file.write( output_record )
            sequence_no+=1

        output_file.close()
        msg = sarracenia.Message.fromFileData(grouped_file, self.o, os.stat(grouped_file))

        logger.info( f" grouped_file {grouped_file} {msg['size']} bytes, {sequence_no-1} records" )
        worklist.incoming=[ msg ]
        self.sequence+=1


