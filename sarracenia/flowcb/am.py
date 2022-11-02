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

# TODO: Update method descriptions and file description

import logging, socket, struct, time, sys, os
import urllib.parse
import pathlib
import sarracenia
import sarracenia.config
from sarracenia.flowcb import FlowCB

# default_options = {'download': False, 'logReject': False, 'logFormat': '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s', 'logLevel': 'info', 'sleep': 0.1, 'vip': None}
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
        self.inBuffer = bytes()
        self.limit = 32678
        self.o.add_option('onlySync','flag', False)
        self.o.add_option('patternAM','str','80sII4sIIII20s')
        self.o.add_option('sizeAM', 'count', struct.calcsize(self.o.patternAM))
        self.host = self.url.netloc.split(':')[0]
        self.port = int(self.url.netloc.split(':')[1])
        self.childlist = []
        self.o.timeCopy = True
        self.remoteHost = None

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

        if self.host == 'None':
            raise Exception("No remote host was specified.")

        try:
            # Bind socket to all interfaces and listen
            self.s.bind((self.host, self.port)) 
            self.s.listen(1)
            logger.info("Socket listening on remote host %s and port %d.", self.host, self.port)
            self.flag = True
        except socket.error as e:
                logger.info(f"Parent process bind failed. Retrying. Error: {e.args}")
                time.sleep(5)
        
        child_inst = 2

        while True:
            
                try:
                    # Accept the connection from socket
                    logger.info("Trying to accept connection from child process.")
                    conn, self.remoteHost = self.s.accept()
                    
                    # Parent process stays in the loop searching for other connections. 
                    # Child will proceed accepting or refusing connection.
                    pid = os.fork()

                    if pid == 0:
                        # Break from the loop if process is child
                        # TODO: Log to file with correct instance ID
                        # TODO: Write the pid file for the instance, so that sr status | stop | sanity
                        # FIXME: Is this done??
                        self.s.close()
                        break                    

                    elif pid == -1:
                        raise logger.exception("Connection could not fork. Exiting.") 
                    else:
                        # Stay in loop if process is parent 
                        self.childlist.append(pid)

                        pidfilename = sarracenia.config.get_pid_filename(
                        None, self.o.component, self.o.config, child_inst)

                        with open(pidfilename, 'w') as pfn:
                            pfn.write('%d' % pid)
                            
                        conn.close()
                        pass
                   
                except TypeError:
                    logger.info("Couldn't accept connection. Retrying.")
                    time.sleep(1)
                
                """
            try:
            
                # Bind socket to all interfaces and listen
                self.s.bind(('', self.port)) 
                self.s.listen(1)
                logger.info("Socket bound.")

                try:
                    # Accept the connection from socket
                    logger.info("Trying to accept connection.")
                    conn, self.remoteHost = self.s.accept()
                    break    

                except TypeError:
                    logger.info("Couldn't accept connection. Retrying.")
                    time.sleep(1)
                
            except socket.error or OSError:
                logger.info("Bind failed. Retrying.")
                time.sleep(5)          
            """            

        logger.info("Connection accepted with IP %s on port %d", self.remoteHost, self.port)     

        return conn                       


    def on_start(self):
        self.conn = self.__establishconn__()
    

    def on_stop(self):
        # Kill all child processes gathered in list
        for child_pid in self.childlist:
            os.kill(child_pid, 9)
        
        self.conn.close()


    def AddBuffer(self):
        """
        Overview::
            Add buffer data from remote server
        
        Pseudocode::
            Receive data from remote server
            if only want to sync buffer:
                Ignore all error logs

        Return::
            None
        """

        try:
            # Receive data from socket
            tmp = self.conn.recv(self.limit)


            if tmp == '':
                if not self.o.onlySync:
                    logger.exception("Connection was lost")
                    raise Exception("Connection was lost")
            
            logger.info("Message length - %d Bytes, Data received from socket - %s" % (len(tmp),tmp))
            
            self.inBuffer = self.inBuffer + tmp

        except socket.error:
            (type, value, tb) = sys.exc_info()

            logger.warning("Type: %s, Value: %s, [socket.recv(%d)]" % (type, value, self.limit))
            
            if not self.o.onlySync:
                logger.exception("Connection was lost")
                raise Exception("Connection was lost")
            

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

        logger.info("Verifying message integrity.")
        
        # Only unpack data if buffer length satisfactory
        if len(self.inBuffer) >= self.o.sizeAM:
            # TODO: Add variables to options with self.o.add_option?
            (header, src_inet, dst_inet, threads, start, length, firsttime, timestamp, future) = \
                    struct.unpack(self.o.patternAM,self.inBuffer[0:self.o.sizeAM])
        else:
            return 'INCOMPLETE'

        length = socket.ntohl(length)
        
        if len(self.inBuffer) >= self.o.sizeAM + length:
            return 'OK'
        else:
            return 'INCOMPLETE'


    def unwrapmsg(self):

        status = self.CheckNextMsgStatus()

        if status == 'OK':
            (self.header,src_inet,dst_inet,threads,start,length,firsttime,timestamp,future) = \
                    struct.unpack(self.o.patternAM,self.inBuffer[0:self.o.sizeAM])

            length = socket.ntohl(length)

            bulletin = self.inBuffer[self.o.sizeAM:self.o.sizeAM + length]
            longlen = self.o.sizeAM + length
            logger.info("Gather successful.")
            return (bulletin, longlen)
        
        else:
            return '', 0


    def gather(self):
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
        self.AddBuffer()

        newmsg = []

        while True:
            status = self.CheckNextMsgStatus()
            
            if status == 'INCOMPLETE':
                break

            if status == 'OK':
                ## TODO: Add corrupt data verifier?
                (bulletin, longlen) = self.unwrapmsg()

                self.inBuffer = self.inBuffer[longlen:]

                #Debug
                logger.info(f"Bulletin contents: {bulletin}")
                logger.info(f"Bulletin length: {longlen}")       

                # Create a file for new messages and let sarracenia format data
                # TODO: Change file path to end @ CACN00 CWAO 281900 WRR <-
                filepath = self.o.directory + os.sep + self.header.split(b'\0',1)[0].decode('iso-8859-1').replace(' ', '_') 
                file = open(filepath, 'wb')
                file.write(bulletin)
                file.close()
                st = os.stat(filepath)

                sarramsg = sarracenia.Message.fromFileData(filepath,self.o, lstat=st)
                newmsg.append(sarramsg)

        return newmsg    
                                

# Debug
# if __name__ == '__main__':
    # am = AM(default_options, 5002, '127.0.0.1')
    # while True:
        # am.poll()