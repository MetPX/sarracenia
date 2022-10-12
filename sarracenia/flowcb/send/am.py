#!/usr/bin/python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#

"""
Sundew migration

sarracenia.flowcb.send.am.AM is a sarracenia version 3 plugin used to encode and send messages with 
the AM protocol.

By: André LeBlanc, Autumn 2022
"""

import logging, socket, struct, copy, time, curses.ascii, sys

from sarracenia.flowcb import FlowCB
from sarracenia.flowcb.poll import Poll
from sarracenia.config import Config

FORMAT ='%(asctime)s %(message)s'
logging.basicConfig(filename='sarracenia/flowcb/send/sarra-am-send.log', format=FORMAT) #TODO change log path
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AM(FlowCB):
    
    def __init__(self, options):
             
        self.o = options

        # Initialise port variables
        self.am = Config()
        self.am.add_option('port', 'count', 5002) # Put count because it's integer type - 5002 test value
        self.am.add_option('connected', 'flag', False)
        self.am.add_option('remoteHost', 'str', 'None') # localhost test value

        # Initialise format variables
        self.am.add_option('threadnum', 'count', 127)
        self.am.add_option('patternAM', 'str', '80sII4sIIII20s')

        ## Initialise methods
        # self.am.add_option('__wrapmsg__', '', )
        # self.am.add_option('__establishconn__', '', )
        # self.am.add_option('__sendmsg__', '', )

        # Initialise socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Establish connection and send bytes through socket
        self.__establishconn__()

    def wrapmsg(self): 
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

        # TODO: Discard of messages of 32KB size

        # Fetch raw message (returns list type)
        # Poller = Poll()
        # msg = Poller.poll()

        logger.info("send/am.py: Commencing message wrap.")

        s = struct.Struct(self.am.patternRec)
        size = struct.calcsize('80s')
        # data = copy.deepcopy(msg)

        # debug
        data = 'SACN31 CWAO 300651\nMETAR\nBGBW 131550Z 21010KT 8000 -RADZ BKN006 OVC012 03/00 Q1009 RMK 5SC\n     8SC='
        
        # Construct AM header
        ## Only keep data prior to first LF
        """
        ''.join(tmp)   
        """
        header = data.split('\n')[0]

        ## Attach rest of header with NULLs
        nulheader = ['\0' for i in range(size)]
        nulheaderstr = ''.join(nulheader)
        header = header + nulheaderstr[len(header):]

        ## Perform bite swaps AND init miscellaneous variables
        length = socket.htonl(len(data))
        firsttime = socket.htonl(int(time.time()))
        timestamp = socket.htonl(int(time.time()))
        threadnum = chr(0) + chr(self.am.threadnum) + chr(0) + chr(0)
        future = chr(curses.ascii.NUL)
        start, src_inet, dst_inet = (0, 0, 0)

        # Wrap message
        packedheader = s.pack(header.encode('ascii'), src_inet, dst_inet, threadnum.encode('utf-8'), start
                                   , length, firsttime, timestamp, future.encode('ascii'))
        
        # Add message at the end of the header
        msg = packedheader + data.encode('ascii')

        logger.info("send/am.py: Message packed.")
        
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

        logger.info("send/am.py: Binding socket to port %d",self.am.port)

        if self.am.remoteHost == 'None':
            logger.exception("send/am.py: No remote host specified. Connection will not be established")
            raise Exception("send/am.py: No remote host specified. Connection will not be established")

        logger.info("send/am.py: Trying to connect remote host %s", str(self.am.remoteHost) )

        while True:
            try:
                self.s.connect((socket.gethostbyname(self.am.remoteHost), self.am.port))
                break

            except socket.error:
                    (type, value, tb) = sys.exc_info()
                    logger.error("send/am.py: Type: %s, Value: %s, Sleeping 30 seconds ..." % (type, value))
                    time.sleep(30)

        logger.info("send/am.py: Connexion established with %s",str(self.am.remoteHost))
        self.am.connected = True

    def sendmsg(self):
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
            logger.info("send/am.py: First attempt at sending data.")

            # Try to send data through socket. If can't raise an error and display error in logs.
            try:
                # Establish connection and send bytes through socket
                # s = self.__establishconn__()

                bytesSent = self.s.send(data)

                # Check if went okay
                if bytesSent != len(data):
                    self.am.connected = False
                    return(0, bytesSent)
                else:
                    return(1, bytesSent)
                
            except socket.error as e:
                logger.error("send/am.py: Message not sent: %s",str(e.args))
                self.am.connected = False

                # If could not send, try to reconnect to socket
                logger.info("send/am.py: Closing socket connection.")
                self.s.close()

        except Exception as e:
            logger.error("send/am.py: msg wrap error: %s", str(e.args))
            raise e("send/am.py: msg wrap error: %s", str(e.args))



# Debug
default_options = {
    'accelThreshold': 0,
    'batch': 100,
    'acceptUnmatched': False,
    'attempts': 3,
    'byteRateMax': None,
    'destination': None,
    'discard': False,
    'download': False,
    'fileEvents': None,
    'housekeeping': 300,
    'logReject': False,
    'logFormat':
    '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s',
    'logLevel': 'info',
    'mirror': True,
    'permCopy': True,
    'timeCopy': True,
    'messageCountMax': 0,
    'messageRateMax': 0,
    'messageRateMin': 0,
    'sleep': 0.1,
    'topicPrefix': ['v03'],
    'vip': None
}

# Debug
ammanager = AM(default_options)
recbytesnum = ammanager.sendmsg()
    




