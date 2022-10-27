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
import urllib.parse
import sarracenia
from sarracenia.flowcb import FlowCB

default_options = {'download': False, 'logReject': False, 'logFormat': '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s', 'logLevel': 'info', 'sleep': 0.1, 'vip': None}
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

        # Initialise server variables
        self.inBuffer = None
        self.limit = 32678
        self.o.add_option('onlySync','flag', False)
        self.o.add_option('patternAM','str','80sII4sIIII20s')
        self.o.add_option('sizeAM', 'count', struct.calcsize(self.o.patternAM))
        self.o.remoteHost = self.url.netloc.split(':')[0]
        self.o.port = int(self.url.netloc.split(':')[1])
        self.o.timeCopy = True


        # Initialise socket
        ## Create a TCP/IP socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

 
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

        if self.o.remoteHost == 'None':
            raise Exception("No remote host was specified.")

        pid = 0

        while True:

            try:
                if pid == 0:    
                    # Bind socket to all interfaces and listen
                    self.s.bind(('', self.o.port)) 
                    self.s.listen(1)
                    logger.info("Socket binded to host %s and port %d.", self.o.remoteHost, self.o.port)
                    self.flag = True

                # Parent process stays in the loop searching for other connections. 
                # Child will proceed accepting or refusing connection.
                if self.flag == True:  
                    pid = os.fork()
                    self.flag = False

                try:
                    if pid == 0:
                        pass
                    else:
                        # Accept the connection from socket
                        logger.info("Trying to accept connection from child process")
                        conn, self.o.remoteHost = self.s.accept()
                        break 
                   
                except TypeError:
                    logger.info("Couldn't accept connection. Retrying.")
                    time.sleep(1)
                
            except socket.error or OSError:
                # logger.info("Parent process bind failed. Retrying.")
                time.sleep(10)
        """
             try:
                # Bind socket to all interfaces and listen
                self.s.bind(('', self.o.port)) 
                self.s.listen(1)
                logger.info("Socket bound.")

                try:
                    # Accept the connection from socket
                    logger.info("Trying to accept connection.")
                    conn, self.o.remoteHost = self.s.accept()
                    break    

                except TypeError:
                    logger.info("Couldn't accept connection. Retrying.")
                    time.sleep(1)
                
            except socket.error or OSError:
                logger.info("Bind failed. Retrying.")
                time.sleep(5)          
        """ 

        logger.info("Socket binded to IP %s and on port %d", self.o.remoteHost, self.o.port)     

        self.s.close()

        return conn               

    def on_start(self):
        self.conn = self.__establishconn__()
    
    def on_stop(self): 
        self.conn.close()

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
                    if not self.o.onlySync:
                        logger.exception("Connection was lost")
                        raise Exception("Connection was lost")
                
                logger.info("Message length - %d Bytes, Data received from socket - %s" % (len(tmp),tmp))
                
                self.inBuffer = tmp
                break   

            except socket.error:
                (type, value, tb) = sys.exc_info()

                logger.warning("Type: %s, Value: %s, [socket.recv(%d)]" % (type, value, self.limit))
                self.conn.close()

                if not self.o.onlySync:
                    logger.exception("Connection was lost")
                    raise Exception("Connection was lost")
                
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

        logger.info("Verifying message integrity.")
        
        # Only unpack data if buffer length satisfactory
        if len(self.inBuffer) >= self.o.sizeAM:
            (header, src_inet, dst_inet, threads, start, length, firsttime, timestamp, future) = \
                    struct.unpack(self.o.patternAM,self.inBuffer[0:self.o.sizeAM])
        else:
            return 'INCOMPLETE'

        length = socket.ntohl(length)

        if len(self.inBuffer) >= self.o.sizeAM + length:
            return 'OK'
        else:
            logger.info("Verification failure. Exiting poll.")
            return 'INCOMPLETE'

    def poll(self):
        """
        Overview: 
            Unwrap data
        
        Pseudocode:
            Get data and check integrity
            if OK
                Unpack data
                Create file and let sarracenia format data
                return sarramsg
            else
                return []
        """

        status = self.CheckNextMsgStatus()
        
        # Unpack data
        if status == 'OK':
            (header,src_inet,dst_inet,threads,start,length,firsttime,timestamp,future) = \
                     struct.unpack(self.o.patternAM,self.inBuffer[0:self.o.sizeAM])

            length = socket.ntohl(length)

            msg = self.inBuffer[self.o.sizeAM:self.o.sizeAM + length]
            logger.info("Gather successful.")

            newmsg = []

            # Create a file for new messages and let sarracenia format data
            filepath = self.o.directory + os.sep + header.split(b'\0',1)[0].decode('iso-8859-1').replace(' ', '_') 
            file = open(filepath, 'wb')
            file.write(msg)
            file.close()
            st = os.stat(filepath)

            sarramsg = sarracenia.Message.fromFileData(filepath,self.o, lstat=st)
            newmsg.append(sarramsg)

            return newmsg
        else:
            return []                

# Debug
# if __name__ == '__main__':
    # am = AM(default_options, 5002, '127.0.0.1')
    # while True:
        # am.poll()