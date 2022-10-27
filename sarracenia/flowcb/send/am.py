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

import logging, socket, struct, time, sys, signal, os
import urllib.parse
from sarracenia.flowcb import FlowCB


logger = logging.getLogger(__name__)

class AM(FlowCB):
    
    def __init__(self, options):
             
        # self.o = super().__init__(options)

        # Set logger options
        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, self.o['logLevel'].upper()))
        else:
            logger.setLevel(logging.INFO)
        logging.basicConfig(format=self.o['logFormat']) 

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

        signal.signal(signal.SIGTERM, signal.SIG_DFL)


    def wrapmsg(self, sarra_msg): 
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

        msg_path = sarra_msg['new_relPath']
        msg_file = open(os.sep + msg_path, 'rb')
        data = msg_file.read()
        msg_file.close()

        # Construct AM header
        strdata = data.decode('iso-8859-1')
        header = strdata[0:size]

        ## Attach rest of header with NULLs and replace NULL w/ Carriage return
        nulheader = ['\0' for i in range(size)]
        nulheaderstr = ''.join(nulheader)
        header = header + nulheaderstr[len(header):]

        ## Perform bite swaps AND init miscellaneous variables
        length = socket.htonl(len(strdata.lstrip('\n')))

        firsttime = socket.htonl(int(time.time()))
        timestamp = socket.htonl(int(time.time()))
        threadnum = chr(0) + chr(self.threadnum) + chr(0) + chr(0)
        future = '\0'
        start, src_inet, dst_inet = (0, 0, 0)

        # Wrap message
        packedheader = s.pack(header.replace('\n','\x00',1).encode('iso-8859-1'), src_inet, dst_inet, threadnum.encode('iso-8859-1'), start
                                   , length, firsttime, timestamp, future.encode('iso-8859-1'))
        
        # Add message at the end of the header
        msg = packedheader + data

        logger.info("Message has been packed.")
        # Debug
        logger.info(f"Message contents: {msg}")
        
        return msg

    def __establishconn__(self): 
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

    
    def on_start(self):
        self.__establishconn__()
    
    def on_stop(self):
        self.s.close()


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

        try:
            # Wrap message
            packed_msg = self.wrapmsg(msg)

            # Try to send data through socket. If can't raise an error and display error in logs.
            try:
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

        except Exception as e:
            logger.error("msg wrap error: %s", str(e.args))
            # raise Exception("msg wrap error: %s", str(e.args))