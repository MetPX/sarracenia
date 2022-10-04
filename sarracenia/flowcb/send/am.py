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

See https://github.com/MetPX/Sundew/blob/main/lib/socketManagerAm.py for more information on original protocol software.

Usage:

By: André LeBlanc, Autumn 2022
"""

import logging, socket, struct, copy, time, curses.ascii, sys

from regex import D
from sarracenia.flowcb.gather import file
from sarracenia.flowcb import FlowCB
from sarracenia.config import Config

logger = logging.getLogger(__name__)

class AM(FlowCB):
    
    def __init__(self, options):
        
        "FIXME remove?" 
        self.o = options
        
        # Fetch message contents (returns list)
        # self.msg = gather(options)

        # Initialise port and message header variables
        ## Initialise port variables
        self.am = Config()
        self.am.add_option('type', 'str' , 'master')
        self.am.add_option('port', 'count', 5002) # Put count because it's integer type - 5002 test value
        self.am.add_option('connected', 'flag', False)
        self.am.add_option('remoteHost', 'str', '127.0.0.1') # localhost test value

        ## Initialise message header variables
        self.am.add_option('src_inet', 'count', 0)
        self.am.add_option('dst_inet', 'count', 0) 
        self.am.add_option('start', 'count', 0) 
        self.am.add_option('future', 'str', chr(curses.ascii.NUL)) 
        self.am.add_option('threadnum', 'str', '025500')
        self.am.add_option('patternRec', 'str', '80sII4sIIII20s')

        ## Initialise methods
        # self.am.add_option('__wrapmsg__', '', )
        # self.am.add_option('__establishconn__', '', )
        # self.am.add_option('__sendmsg__', '', )

    def wrapmsg(self): #, msg 
        """
        Wrap Message with Appropriate headers1

        Format headers
        Convert data accordingly with struct
        Pack msg

        return packed msg
        """

        logger.debug("/-----Commencing message wrap.-----/")

        size = struct.calcsize('80s')
        # tmp = copy.deepcopy(self.msg)

        # Debug with Sundew receiver
        tmpstr = 'SACN31CWAO300651METARBGBW131550Z21010KT8000-RADZBKN006OVC01203/00Q1009RMK5SC8SC='
        tmp = []
        for i in tmpstr:
            tmp.append(i)
        
        # Create AM header
        header = list(tmp[0:size])
        strHeader = ''.join(header)
        strHeader.replace(chr(curses.ascii.LF), chr(curses.ascii.NUL), 1)
        bytesHeader = bytes(strHeader, 'utf-8')

        ## Create miscellaneous header parameters
        length = socket.htonl(len(tmp))
        firsttime = socket.htonl(int(time.time()))
        timestamp = socket.htonl(int(time.time()))

        # Create msg package
        packedheader = struct.pack(self.am.patternRec, bytesHeader, self.am.src_inet, self.am.dst_inet, bytes(self.am.threadnum, 'utf-8'), self.am.start
                                   , length, firsttime, timestamp, bytes(self.am.future, 'utf-8'))
        
        # Add header to message
        # TODO Change msg for self.msg (debug)
        # header.remove(str(curses.ascii.LF))
        msg = packedheader + bytes(''.join(header), 'utf-8')

        return msg

    def __establishconn__(self):
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

        logger.info("Binding socket to port %d",self.am.port)

        if self.am.remoteHost == None:
            raise logger.exception("No remote host specified. Connection will not be established")

        logger.info("Trying to connect remote host %s", str(self.am.remoteHost) )

        while True:
            try:
                s.connect((socket.gethostbyname(self.am.remoteHost), self.am.port))
                break

            except socket.error:
                    (type, value, tb) = sys.exc_info()
                    logger.error("Type: %s, Value: %s, Sleeping 30 seconds ..." % (type, value))
                    time.sleep(30)

        logger.info("Connexion established with %s",str(self.am.remoteHost))
        self.am.connected = True

        return s

    def sendmsg(self):
        """
        Send message through socket

        Wrap message
        Send with socket

        return 0 on Failure
        return 1 on Success
        AND 
        # of bytes sent
        """

        try:
            # Prepare message for sending
            data = self.wrapmsg()
            
            # Try to send data through socket. If can't raise an error and display error in logs.
            try:
                # Send bytes through socket
                s = self.__establishconn__()
                bytesSent = s.send(data)

                # Check if went okay
                if bytesSent != len(data):
                    self.connected = False
                    return(0, bytesSent)
                else:
                    return(1, bytesSent)
                
            except socket.error as e:
                logger.error("am.sendmsg: Message not sent: %s",str(e.args))
                self.connected = False
                socket.socket.close()
                # FIXME Attempt to reconnect?

        except Exception as e:
            logger.error("am.wrapmsg: wrap error: %s", str(e.args))
            raise



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
ammanager.wrapmsg()
recbytesnum = ammanager.sendmsg()
print(recbytesnum)
    




