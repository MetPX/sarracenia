#!/usr/bin/
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#

""",1
Sundew migration

sarracenia.flowcb.send.am.AM is a sarracenia version 3 plugin used to encode and send messages with 
the AM (Alpha numeric) protocol. This protocol is being migrated to mexpx-sr3 to retire sundew.

By: André LeBlanc, Autumn 2022
"""

import logging, socket, struct, time, sys

from sarracenia.flowcb import FlowCB
from sarracenia.config import Config

#TODO: Change encoding format to ISO-8859-1?

default_options = {'logFormat': '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s', 'logLevel': 'info'}
logger = logging.getLogger(__name__)
# sys.setdefaultencoding('iso-8859-1')

class AM(FlowCB):
    
    def __init__(self, options):
             
        self.o = options

        # Set logger options
        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, self.o['logLevel'].upper()))
        else:
            logger.setLevel(logging.INFO)
        logging.basicConfig(format=self.o['logFormat']) 

        # Initialise server variables
        self.am = Config()
        self.am.add_option('port', 'count', 5002)
        self.am.add_option('remoteHost', 'str', '127.0.0.1') 

        # Initialise format variables
        self.am.add_option('threadnum', 'count', 255)
        self.am.add_option('patternAM', 'str', '80sII4sIIII20s')

        # Initialise socket
        ## Create a TCP/IP socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def wrapmsg(self): #TODO: Change msgdata with data 
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

        s = struct.Struct(self.am.patternAM)
        size = struct.calcsize('80s')

        # debug
        data = 'SACN31 CWAO 300651\nMETAR\nBGBW 131550Z 1,21010KT 8000 -RADZ BKN006 OVC012 03/00 Q1009 RMK 5SC\n     8SC=\n'

        # Construct AM header
        header = data[0:size]

        ## Attach rest of header with NULLs and replace NULL w/ Carriage return
        nulheader = ['\0' for i in range(size)]
        nulheaderstr = ''.join(nulheader)
        header = header + nulheaderstr[len(header):]

        ## Perform bite swaps AND init miscellaneous variables
        length = socket.htonl(len(data))
        firsttime = socket.htonl(int(time.time()))
        timestamp = socket.htonl(int(time.time()))
        threadnum = chr(0) + chr(self.am.threadnum) + chr(0) + chr(0)
        future = '\0'
        start, src_inet, dst_inet = (0, 0, 0)

        # Wrap message
        packedheader = s.pack(header.replace('\n','\x00',1).encode('iso-8859-1'), src_inet, dst_inet, threadnum.encode('iso-8859-1'), start
                                   , length, firsttime, timestamp, future.encode('iso-8859-1'))
        
        # Add message at the end of the header
        msg = packedheader + data.encode('iso-8859-1')

        logger.info("Message packed.")
        # Debug
        # logger.info(f"{msg}")
        
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

        logger.info("Binding socket to port %d",self.am.port)

        if self.am.remoteHost == 'None':
            logger.exception("No remote host specified. Connection will not be established")
            raise Exception("No remote host specified. Connection will not be established")

        logger.info("Trying to connect remote host %s", str(self.am.remoteHost) )

        while True:
            try:
                self.s.connect((socket.gethostbyname(self.am.remoteHost), self.am.port))
                break

            except socket.error:
                    (type, value, tb) = sys.exc_info()
                    logger.error("Type: %s, Value: %s, Sleeping 30 seconds ..." % (type, value))
                    time.sleep(30)

        logger.info("Connexion established with %s",str(self.am.remoteHost))

    
    # def on_start(self):
        # self.__establishconn__()
    
    # def on_stop(self):
        # self.s.close()

    def send(self):
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
            data = self.wrapmsg()
            logger.info("First attempt at sending data.")

            # Try to send data through socket. If can't raise an error and display error in logs.
            try:
                # Establish connection and send bytes through socket
                self.__establishconn__()

                bytesSent = self.s.send(data)

                # Check if went okay
                if bytesSent != len(data):
                    return(0, bytesSent)
                else:
                    return(1, bytesSent)
                
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
    
am_send_man = AM(default_options)
rec = am_send_man.send()



