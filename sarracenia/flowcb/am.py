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

import logging, socket, struct, time, sys, os, signal
import urllib.parse
import ipaddress
import sarracenia
import sarracenia.config
from sarracenia.flowcb import FlowCB
from random import randint

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

        # Initialise server variables
        self.inBuffer = bytes()
        self.limit = 32678
        self.patternAM = '80sII4siIII20s'
        self.sizeAM = struct.calcsize(self.patternAM)
        self.o.add_option('AllowIPs', 'list', [])
        self.host = self.url.netloc.split(':')[0]
        self.port = int(self.url.netloc.split(':')[1])
        self.minnum = 00000
        self.maxnum = 99999
        self.remoteHost = None

        # Initialise socket
        ## Create a TCP socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Add signal handler
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

 
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
            raise Exception("No host was specified.")

        try:
            # Bind socket to all interfaces and listen
            self.s.bind((self.host, self.port)) 
            self.s.listen(1)
            logger.info("Socket listening on host %s and port %d.", self.host, self.port)
        except socket.error as e:
                logger.info(f"Parent process bind failed. Retrying. Error: {e.args}")
                time.sleep(5)
        
        child_inst = 2

        while True:
            
                try:
                    # Accept the connection from socket
                    logger.info("Trying to accept connection.")

                    try:
                        conn, self.remoteHost = self.s.accept()
                        time.sleep(1)

                    except Exception as e:
                        logger.error(f"Stopping accept. Leaving. Error: {e}")
                        sys.exit(0)   

                    if self.o.AllowIPs:
                        if self.remoteHost[0] not in self.o.AllowIPs:
                            logger.debug(f"Connection to IP {self.remoteHost[0]} rejected. Not a part of the Accepted IPs list.")
                            conn.close()
                            continue
                    
                    # Parent process stays in the loop searching for other connections. 
                    # Child will proceed accepting or refusing connection.
                    pid = os.fork()

                    if pid == 0:
                        # Break from the loop if process is child
                        self.s.close()

                        ## Set the logfiles properly
                        sarracenia.config.cfglogs(self.o, self.o.component, self.o.config, self.o.logLevel, child_inst)

                        self.o.no = child_inst
                        logger.info(f"Starting up service with host {self.remoteHost[0]}")
                        break                    

                    elif pid == -1:
                        raise logger.exception("Connection could not fork. Exiting.")
                    else:
                        # Stay in loop if process is parent 
                        pidfilename = sarracenia.config.get_pid_filename(
                        None, self.o.component, self.o.config, child_inst)

                        with open(pidfilename, 'w') as pfn:
                            pfn.write('%d' % pid)

                        conn.close()
                        logger.info(f"Forked child from host {self.remoteHost[0]} with instance number {child_inst} and pid {pid}")

                        child_inst += 1

                        pass
                   
                except TypeError:
                    logger.error("Couldn't accept connection. Retrying.")
                    time.sleep(1)
                
        logger.info("Connection accepted with IP %s on port %d", self.remoteHost, self.port)     

        return conn                       


    def on_start(self):
        # Set ipadresses in proper format
        for IP in self.o.AllowIPs:
            IP = ipaddress.ip_address(IP)

        if self.o.no != 1:
            pidfilename = sarracenia.config.get_pid_filename(None, self.o.component, self.o.config, self.o.no)
            if os.path.exists(pidfilename):
                os.unlink(pidfilename)
            sys.exit(0)
        self.conn = self.__establishconn__()
    

    def on_stop(self):
        logger.info("On stop called. Exiting.")
        self.s.close()
        if self.o.no == 1:
            pass
        else:
            self.conn.close()
        sys.exit(0)
        

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
            try:
                tmp = self.conn.recv(self.limit)
            except Exception as e:
                tmp = ''
                logger.error(f"Reception has been interrupted. Closing connection. Error message: {e}")


            if tmp == '':
                logger.error("Connection was lost. Exiting.")
                raise Exception()
            
            self.inBuffer = self.inBuffer + tmp

        except socket.error:
            (type, value, tb) = sys.exc_info()

            logger.warning("Type: %s, Value: %s, [socket.recv(%d)]" % (type, value, self.limit))
            
            # if not self.o.onlySync:
                # logger.exception("Connection was lost")
                # raise Exception("Connection was lost")
            

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

        # Only unpack data if buffer length satisfactory
        if len(self.inBuffer) >= self.sizeAM:
            (header, src_inet, dst_inet, threads, start, length, firsttime, timestamp, future) = \
                    struct.unpack(self.patternAM,self.inBuffer[0:self.sizeAM])
        else:
            return 'INCOMPLETE'

        length = socket.ntohl(length)
        # Debug
        # logger.info(f"Buffer contents: {self.inBuffer}")
        
        if len(self.inBuffer) >= self.sizeAM + length:
            return 'OK'
        else:
            return 'INCOMPLETE'


    def unwrapmsg(self):

        status = self.CheckNextMsgStatus()

        if status == 'OK':
            (self.header,src_inet,dst_inet,threads,start,length,firsttime,timestamp,future) = \
                    struct.unpack(self.patternAM,self.inBuffer[0:self.sizeAM])

            length = socket.ntohl(length)

            bulletin = self.inBuffer[self.sizeAM:self.sizeAM + length]
            longlen = self.sizeAM + length
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
                ## FIXME: Add corrupt data verifier?
                (bulletin, longlen) = self.unwrapmsg()

                self.inBuffer = self.inBuffer[longlen:]

                logger.debug(f"Bulletin length: {longlen - 128}") 
                logger.debug(f"Bulletin contents: {bulletin}")

                # Create a file for new messages and let sarracenia format data
                parse = self.header.split(b'\0',1)
                bulletinHeader = parse[0].decode('iso-8859-1').replace(' ', '_')

                try:
                    # Filenames have the following naming scheme:
                    #   1. Header
                    #   2. Counter (makes filename unique for each bulletin)
                    #   IF A* or R* present in header, include in filename
                    filepath = self.o.directory + os.sep + bulletinHeader + '__' +  f"{randint(self.minnum, self.maxnum)}".zfill(len(str(self.maxnum)))

                    file = open(filepath, 'wb')
                    file.write(bulletin)
                    file.close()
                    st = os.stat(filepath)

                    sarramsg = sarracenia.Message.fromFileData(filepath, self.o, lstat=st)
                    newmsg.append(sarramsg)

                except:
                    logger.error("Unable to generate bulletin file.")

        return newmsg 