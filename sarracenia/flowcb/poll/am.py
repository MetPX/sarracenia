#!/usr/bin/python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#

"""
Sundew migration

sarracenia.flowcb.poll.am.AM is a sarracenia version 3 plugin used to migrate the message reception of sundew 
AM (Alphanumeric Messaging) protocol.

By: André LeBlanc, Autumn 2022
"""

import logging, socket, struct, time, sys, os
from sarracenia.flowcb import FlowCB 
from sarracenia.config import Config

default_options = {'download': False, 'logReject': False, 'logFormat': '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s', 'logLevel': 'info', 'sleep': 0.1, 'vip': None}
logger = logging.getLogger(__name__)


class AM(FlowCB):

    def __init__(self, options, port=0, remoteHost='None'):
        
        self.o = options
        # self.o = super().__init__(options)

        # Set logger options
        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, self.o['logLevel'].upper()))
        else:
            logger.setLevel(logging.INFO)
        logging.basicConfig(format=self.o['logFormat'])

        # Initialise server variables
        self.am = Config()
        self.am.add_option('onlySync','flag', False)
        self.am.add_option('patternAM','str','80sII4sIIII20s')
        self.am.add_option('sizeAM', 'count', struct.calcsize(self.am.patternAM))
        self.am.add_option('port', 'count', port) 
        self.am.add_option('remoteHost', 'str', remoteHost) 
        self.limit = 32678
        self.inBuffer = None

        # Initialise socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Establish connection and send bytes through socket
        self.conn = self.__establishconn__()

    def __establishconn__(self):
        """
        Overview: 
            Establish a connexion with remote server.

        Pseudocode:
            Bind to socket
            Listen for a reply from remote server
            Accept connexion
        
        Return:
            connected instance
        """      

        logger.info("poll/am.py: Socket binding with IP %s, port %d" % (self.am.remoteHost ,self.am.port))

        if self.am.remoteHost == 'None':
            raise Exception("poll/am.py: No remote host was specified.")

        c1, c2 = (0, 0)
        flag = True
        
        while True:

            """
            try:
                if pid != 0:    
                    # Bind socket to all interfaces and listen
                    self.s.bind(('', self.am.port)) 
                    self.s.listen(1)
                    logger.info("poll/am.py: Socket binded.")


                # Master process closes the loop. Make child continue, make parent stay.
                if flag == True:  
                    pid = os.fork()
                    flag == False

                try:
                    if pid == 0:
                        pass
                    else:
                        # Accept the connection from socket
                        logger.info("poll/am.py: Trying to accept connection.")
                        conn, self.am.remoteHost = self.s.accept()
                        flag = True
                        break 
                   
                except TypeError:
                    logger.info("poll/am.py: Couldn't accept connection. Retrying.")
                    time.sleep(1)
                
            except socket.error or OSError:
                logger.info("poll/am.py: Bind failed. Retrying.")
                time.sleep(5)
            """

            
            try:
                # Bind socket to all interfaces and listen
                self.s.bind(('', self.am.port)) 
                self.s.listen(1)
                logger.info("poll/am.py: Socket binded.")

                try:
                    # Accept the connection from socket
                    logger.info("poll/am.py: Trying to accept connection.")
                    conn, self.am.remoteHost = self.s.accept()
                    break    

                except TypeError:
                    logger.info("poll/am.py: Couldn't accept connection. Retrying.")
                    time.sleep(1)
                
            except socket.error or OSError:
                logger.info("poll/am.py: Bind failed. Retrying.")
                time.sleep(5)

        logger.info("poll/am.py: Socket binded to IP %s and on port %d", self.am.remoteHost, self.am.port)     

        self.s.close()

        return conn               

    def AddBuffer(self):
        """
        Overview:
            Add buffer data from remote server
        
        Pseudocde:
            Receive data from remote server
            if only want to sync buffer:
                Ignore all error logs

        Return:
            None
        """

        while True:
            try:
                # Receive data from socket
                tmp = self.conn.recv(self.limit)

                if tmp == '':
                    if not self.am.onlySync:
                        logger.exception("poll/am.py: Connection was lost")
                        raise Exception("poll/am.py: Connection was lost")
                
                logger.info("poll/am.py: Message length - %d Bytes, Data received from socket - %s" % (len(tmp),tmp))
                
                self.inBuffer = tmp
                # self.conn.close
                break   

            except socket.error:
                (type, value, tb) = sys.exc_info()

                logger.warning("Type: %s, Value: %s, [socket.recv(%d)]" % (type, value, self.limit))
                self.conn.close()

                if not self.am.onlySync:
                    logger.exception("poll/am.py: Connection was lost")
                    raise Exception("poll/am.py: Connection was lost")
                
                break 

    def CheckNextMsgStatus(self):
        """
        Overview:
            Test integrity of message prior to unpacking it

        Pseudocode:
            Get buffer data
            if buffer len at least 80 bytes:
                unpack data
                return OK
            else
                return INCOMPLETE
        """

        self.AddBuffer()

        logger.info("poll/am.py: Verifying message integrity.")
        
        # Only unpack data if buffer length satisfactory
        if len(self.inBuffer) >= self.am.sizeAM:
            (header, src_inet, dst_inet, threads, start, length, firsttime, timestamp, future) = \
                    struct.unpack(self.am.patternAM,self.inBuffer[0:self.am.sizeAM])
        else:
            return 'INCOMPLETE'

        length = socket.ntohl(length)

        if len(self.inBuffer) >= self.am.sizeAM + length:
            return 'OK'
        else:
            logger.info("poll/am.py: Verification failure. Exiting poll.")
            return 'INCOMPLETE'

    def poll(self):
        """
        Overview: 
            Unwrap data
        
        Pseudocode:
            Get data and check integrity
            if OK
                unpack data
                return (data, packet length)
            else
                return ('', 0)
        """

        status = self.CheckNextMsgStatus()

        if status == 'OK':
            (header,src_inet,dst_inet,threads,start,length,firsttime,timestamp,future) = \
                     struct.unpack(self.am.patternAM,self.inBuffer[0:self.am.sizeAM])

            length = socket.ntohl(length)

            msg = self.inBuffer[self.am.sizeAM:self.am.sizeAM + length]

            logger.info("poll/am.py: Gather successful.")

            return (msg, self.am.sizeAM + length)
        else:
            return '',0                

# Debug
'''
am = AM(default_options, 5002, '127.0.0.1')
while True:
    res = am.poll()
'''

if __name__ == '__main__':
    am = AM(default_options, 5002, '127.0.0.1')
    while True:
        am.poll()