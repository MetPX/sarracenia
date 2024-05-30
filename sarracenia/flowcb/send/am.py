# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) His Majesty The King in Right of Canada, Environment Canada, 2008-2020
#

"""
Description:
    Sundew migration

    This is a sr3 plugin built to migrate the sender of ECCC's
    proprietary Alpha Manager(AM) socket protocol.

    For more information on the origins of AM and Sundew visit https://github.com/MetPX/Sundew/blob/main/doc/historical/Origins.rst

    Code overview:
        To start, when on_start is called, the socket is instiated and attempts to connect with a remote host with the IP and port # specified in the config file.
        Once the send method is called, the bulletin is wrapped with a 128 byte header which contains the bulletin length, thread number, timestamps, etc.
        The wrapped bulletin is then individually sent through the socket.
        If the send is successful, return True. If not, return False.

    Options:
        MaxBulLen (int): Specify the maximum length of the bulletin. If the bulletin is too big, reject.

    NOTE: AM cannot correct data corruption and AM cannot be stopped without data loss.
    Precautions should be taken during maintenance interventions.

Usage:
    flowcb sarracenia.flowcb.send.am.AM
    See sarracenia/examples/sender/am_send.conf for an example config file.

Author:
    André LeBlanc, ANL, Autumn 2022
"""

import logging, socket, struct, time, signal, sys, os
import urllib.parse
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class Am(FlowCB):
    
    def __init__(self, options):
             
        super().__init__(options,logger)

        self.url = urllib.parse.urlparse(self.o.sendTo)

        self.threadnum = 255
        self.host = self.url.netloc.split(':')[0]
        self.port = int(self.url.netloc.split(':')[1])
        self.patternAM = '80sII4siIII20s'

        self.o.add_option('MaxBulLen', 'count', 32768)

        # Initialise socket
        ## Create a TCP/IP socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 2)

        # Add signal handler
        ## Override outer signal handler with a default one to exit correctly.
        signal.signal(signal.SIGTERM, signal.SIG_DFL)


    def wrapbulletin(self, sarra_msg): 

        logger.info("Commencing message wrap.")

        s = struct.Struct(self.patternAM)
        size = struct.calcsize('80s')

        msg_path = sarra_msg['new_relPath']
        msg_file = open(os.sep + msg_path, 'rb')
        data = msg_file.read()
        msg_file.close()

        # Construct msg header
        strdata = data.decode('iso-8859-1')
        header = strdata[0:size]

        # Step out of the function if the bulletin size is too big
        if len(strdata) > self.o.MaxBulLen:
            raise Exception(f"Bulletin length too long. Bulletin limit length: {self.o.MaxBulLen}. Latest bulletin length: {len(strdata)}. Path to bulletin: {msg_path}")

        ## Attach rest of header with NULLs (if not long enough)
        nulheader = ['\0' for _ in range(size)]
        nulheaderstr = ''.join(nulheader)
        header = header + nulheaderstr[len(header):]

        ## Perform bite swaps AND init miscellaneous header parameters
        length = socket.htonl(len(strdata.lstrip('\n')))

        firsttime = socket.htonl(int(time.time()))
        timestamp = socket.htonl(int(time.time()))
        threadnum = chr(0) + chr(self.threadnum) + chr(0) + chr(0)
        future = '\0'
        start, src_inet, dst_inet = (0, 0, 0)

        # Wrap bulletin
        ## Replace first line feed with NULL
        packedheader = s.pack(header.replace('\n','\x00',1).encode('iso-8859-1'), src_inet, dst_inet, threadnum.encode('iso-8859-1'), start
                                   , length, firsttime, timestamp, future.encode('iso-8859-1'))
        
        msg = packedheader + data

        logger.debug("Message has been packed.")
        # llogger.debug(f"Message contents: {msg}")
        
        return msg

    def on_stop(self):
        self.s.close()

    def reEstablishConnection(self):
        # Use exponential backoff to try and connect or reconnect to remote host
        
        if self.host == 'None':
            raise Exception("No remote host specified.")

        logger.info("Trying to connect to remote host %s and port %d" % (str(self.host) , self.port))

        backoff_range = 1
        while True:
            try:
                # Initialise socket
                ## Create a TCP/IP socket
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 2)

                time.sleep(1)
                self.s.connect((socket.gethostbyname(self.host), self.port))
                break
                
            except socket.error as e:
                logger.debug("Error msg: %s" % str(e.args))
                logger.error("Trying to establish connection in %d seconds" % (2**backoff_range))
                self.s.close()
                time.sleep(2**backoff_range)
                if backoff_range < 6:
                    backoff_range += 1


    def send(self, bulletin):
        try:
            self.packed_bulletin = self.wrapbulletin(bulletin)

            while True:
                try:
                    bytesSent = self.s.send(self.packed_bulletin)

                    # Check if went okay
                    return bytesSent == len(self.packed_bulletin)
                    
                except socket.error as e:
                    logger.debug("Bulletin not sent. Error message: %s",str(e.args))
                    logger.error("Connection interrupted. Attempting to reconnect")
                    self.s.close()
                    self.reEstablishConnection()

        except Exception as e:
            raise Exception("Generalized error handler. Error message: %s", str(e.args))
