#!/usr/bin/
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#

"""
Sundew migration

sarracenia.flowcb.send.am.AM is a sarracenia version 3 plugin used to encode and send messages with 
the AM (Alpha numeric) protocol. This protocol is being migrated to mexpx-sr3 to retire sundew.

By: André LeBlanc, Autumn 2022
"""

import logging, socket, struct, time, sys
import urllib.parse
from sarracenia.flowcb import FlowCB
from sarracenia.config import Config


logger = logging.getLogger(__name__)

class AM(FlowCB):
    
    def __init__(self, options):
             
        self.o = options

        # Set logger options
        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, self.o.logLevel.upper()))
        else:
            logger.setLevel(logging.INFO)
        logging.basicConfig(format=self.o.logFormat) 

        self.url = urllib.parse.urlparse(self.o.destination)

        # Initialise format variables
        self.threadnum = 255

        self.host = self.url.netloc.split(':')[0]
        self.port = int(self.url.netloc.split(':')[1])

        # Add config options
        self.o.add_option('patternAM', 'str', '80sII4siIII20s')
        # FIXME: Does this make sens?
        self.o.add_option('host', 'str', f'{self.host}')
        self.o.add_option('port', 'int', f'{self.port}')

        # Initialise socket
        ## Create a TCP/IP socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def wrapmsg(self, data): 
        """
        Overview: 
            Wrap message in appropriate bytes format, performing necessary byte swaps and wrap with AM header

        Pseudocode:
            Construct AM header
            Perform bite swaps AND init miscellaneous variables
            Wrap header with message

        Return:
            Message with AM header
        """

        # Establish connection and send bytes through socket
        # self.__establishconn__()

        logger.info("Commencing message wrap.")

        s = struct.Struct(self.o.patternAM)
        size = struct.calcsize('80s')

        # debug
        # data = 'FTXX60 KWBC 101451\nTAF\nTAF KLSV 101500Z 1015/1121 06009KT 9999 SKC QNH3010INS\n      BECMG 1104/1105 03012G18KT 9999 FEW250 QNH3015INS\n      BECMG 1110/1111 03009KT 9999 SKC QNH3012INS TX17/1022Z\n      TN05/1115Z=\nTAF KNMM 1015/1115 02007KT 9999 FEW150 BKN250 QNH2988INS\n      BECMG 1020/1021 36010G15KT 9999 SCT050 BKN220 QNH2970INS\n      BECMG 1102/1104 VRB06KT 9999 FEW010 SCT015 OVC030 QNH2965INS\n      TEMPO 1108/1114 VRB05KT 4800 BR OVC008 AUTOMATED SENSOR\n      METWATCH 1105 TIL 1111 T22/1020Z T14/1112Z FN20082=\nTAF KNUW 1015/1115 12007KT 9999 VCSH SCT018 BKN040 OVC055\n      QNH3037INS\n     FM101800 12008KT 9999 SCT025 BKN050 BKN250 QNH3036INS\n     FM110000 10008KT 9999 SCT020 SCT035 BKN150 BKN250 QNH3026INS\n      TEMPO 1102/1108 VRB05KT 9999 BKN020 OVC035\n     FM111000 09007KT 9999 FEW020 SCT080 BKN100 OVC200 QNH3017INS\n      T08/1023Z T02/1112Z FS30046=\n'
    

        # Construct AM header
        header = data[0:size]

        ## Attach rest of header with NULLs and replace NULL w/ Carriage return
        nulheader = ['\0' for i in range(size)]
        nulheaderstr = ''.join(nulheader)
        header = header + nulheaderstr[len(header):]

        ## Perform bite swaps AND init miscellaneous variables
        # print(len(data))
        length = socket.htonl(len(data.lstrip('\n')))

        firsttime = socket.htonl(int(time.time()))
        timestamp = socket.htonl(int(time.time()))
        threadnum = chr(0) + chr(self.o.threadnum) + chr(0) + chr(0)
        future = '\0'
        start, src_inet, dst_inet = (0, 0, 0)

        # Wrap message
        packedheader = s.pack(header.replace('\n','\x00',1).encode('iso-8859-1'), src_inet, dst_inet, threadnum.encode('iso-8859-1'), start
                                   , length, firsttime, timestamp, future.encode('iso-8859-1'))
        
        # Add message at the end of the header
        msg = packedheader + data.encode('iso-8859-1')

        logger.info("Message has been packed.")
        # Debug
        logger.info(f"Message contents: {msg}")
        
        return msg

    def __establishconn__(self): #TODO add message data
        """
        Overview: 
            Establish connection through socket (with specified host IP and port #)

        Pseudocode:
            Init socket
            while true:
                Try to connect w/ host IP and port #
                If error:
                    sleep 30 seconds
                    retry

        Return:
            Socket struct
        """       

        logger.info("Binding socket to port %d",self.port)

        if self.host == 'None':
            raise Exception("No remote host specified. Connection will not be established")

        logger.info("Trying to connect remote host %s", str(self.host) )

        while True:
            try:
                self.s.connect((socket.gethostbyname(self.host), self.port))
                break

            except socket.error:
                    (type, value, tb) = sys.exc_info()
                    logger.error("Type: %s, Value: %s, Sleeping 30 seconds ..." % (type, value))
                    time.sleep(30)

        logger.info("Connection established with %s",str(self.host))

    
    # def on_start(self):
        # self.__establishconn__()
    
    # def on_stop(self):
        # self.s.close()


    # FIXME: Get the path from the message and read the data from that path. Test and clean afterwards
    def send(self, msg):
        """
        Overview: 
            Send AM message through socket

        Pseudocode:
            Wrap message
            Send with socket
            If error arises:
                retry sending to socket

        Return:
            0 on Failure
            1 on Success
            AND 
            # of bytes sent
        """

        # Debug
        logger.info(f"Sarracenia message: {msg}")

        try:
            # Wrap message
            packed_msg = self.wrapmsg(msg)

            # Try to send data through socket. If can't raise an error and display error in logs.
            try:
                # Establish connection and send bytes through socket
                self.__establishconn__()

                bytesSent = self.s.send(packed_msg)

                # Check if went okay
                if bytesSent != len(packed_msg):
                    return False
                else:
                    return True
                
            except socket.error as e:
                logger.error("Message not sent: %s",str(e.args))

                # If could not send, try to reconnect to socket
                logger.info("Closing socket connection.")
                self.s.close()

        except BaseException as e:
            logger.error("msg wrap error: %s", str(e.args))
            raise BaseException("msg wrap error: %s", str(e.args))

# Debug
# if __name__ == '__main__':
    # am_recv_man = am.AM(default_options)
    # am_recv_man.am.poll = 5002 
    # am_recv_man.am.remoteHost = '127.0.0.1'
    # am_send_man = AM(default_options)
    # while True:
        # res = am_recv_man.poll()
        # recbytesnum = am_send_man.send()
    
# am_send_man = AM(default_options)
# rec = am_send_man.send()



