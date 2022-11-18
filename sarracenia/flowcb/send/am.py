#!/usr/bin/python3
#
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
        None

    NOTE: AM cannot correct data corruption and AM cannot be stopped without data loss.
    Precautions should be taken during maintenance interventions.

Usage:
    flowcb sarracenia.flowcb.send.am.AM
    See sarracenia/examples/sender/am_send.conf for an example config file.

Author:
    André LeBlanc, ANL, Autumn 2022
"""

import logging, socket, struct, time, sys, signal, os
import urllib.parse
from sarracenia.flowcb import FlowCB

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

        self.url = urllib.parse.urlparse(self.o.remoteUrl)

        self.threadnum = 255
        self.host = self.url.netloc.split(':')[0]
        self.port = int(self.url.netloc.split(':')[1])
        self.patternAM = '80sII4siIII20s'

        # Initialise socket
        ## Create a TCP/IP socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    def wrapmsg(self, sarra_msg): 

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
        # logger.debug(f"Message contents: {msg}")
        
        return msg

    def __ConnectToRemote__(self): 

        if self.host == 'None':
            raise Exception("No remote host specified. Connection cannot not be established")

        logger.info("Trying to connect to remote host %s and port %d" % (str(self.host) , self.port))

        while True:
            try:
                time.sleep(1)
                self.s.connect((socket.gethostbyname(self.host), self.port))
                break

            except socket.error:
                    (type, value, tb) = sys.exc_info()
                    logger.error("Type: %s, Value: %s, Sleeping 30 seconds ..." % (type, value))
                    time.sleep(30)

        logger.info("Connection established with %s",str(self.host))

    
    def on_start(self):
        self.__ConnectToRemote__()
    
    def on_stop(self):
        self.s.close()

    def reEstablishConnection(self):
        # Use exponential backoff to try and reconnect to remote host
        for iter in range(1,6):
            try:
                self.s.connect((socket.gethostbyname(self.host), self.port))
                break
        
            except socket.error:
                logger.error("Trying to reestablish connection in %d seconds" % (2**iter))
                time.sleep(2**iter)
            

    def send(self, msg):
        try:
            packed_msg = self.wrapmsg(msg)
            try:
                bytesSent = self.s.send(packed_msg)

                # Check if went okay
                if bytesSent != len(packed_msg):
                    return False
                else:
                    return True
                
            except socket.error as e:
                logger.error("Bulletin not sent: %s",str(e.args))
                logger.info("Closing socket connection and attempting to reconnect")
                self.s.close()
                self.reEstablishConnection()
                return False

        except Exception as e:
            raise Exception("Msg wrap error: %s", str(e.args))