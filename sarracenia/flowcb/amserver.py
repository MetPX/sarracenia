# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) His Majesty The King in Right of Canada, Environment Canada, 2008-2020
#

"""
Description:
    AM Server         

    This is a sr3 plugin built to migrate the reception of ECCC's
    proprietary Alpha Manager(AM) socket protocol.

    For more information on the origins of AM and Sundew visit https://github.com/MetPX/Sundew/blob/main/doc/historical/Origins.rst

    Code overview:
        To start, when on_start is called, the socket binds, listens and afterwards accepts a connection when one is received from a remote host.
        The receiver acts like an amtcp server. Instances are split into child/parent once an outbound connection is accepted.
        The child proceeds to the receiver service while the parent stays and keeps accepting connections.   
        In the service, bulletins are received and are stored locally inside of a given filepath.

    Options:
        AllowIPs (list): Filters outbound connections with provided IPs. All other IPs won't be accepted. 
        If unselected, accept all IPs. 

        directory (string): Specifies the directory where the bulletin files are to be stored. 

    NOTE: AM protocol cannot correct data corruption and cannot be stopped without data loss.
    Precautions should be taken during maintenance interventions.

Platform:
    Linux/Mac: because of process forking, this will not work on Windows. 

Usage:
    flowcb amserver
    See sarracenia/examples/flow/amserver.conf for an example config file.

Author:
    André LeBlanc, ANL, Autumn 2022
"""

import logging, socket, struct, time, sys, os, signal, ipaddress
import urllib.parse
import sarracenia
import sarracenia.config
from sarracenia.flowcb import FlowCB
from random import randint

logger = logging.getLogger(__name__)

class Amserver(FlowCB):

    def __init__(self, options):
        
        self.o = options

        # Set logger options
        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, self.o.logLevel.upper()))
        else:
            logger.setLevel(logging.INFO)
        logging.basicConfig(format=self.o.logFormat)

        self.url = urllib.parse.urlparse(self.o.remoteUrl)

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
        ## Override outer signal handler with a default one to exit correctly.
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

 
    def __WaitForRemoteConnection__(self):

        if self.host == 'None':
            raise Exception("No host was specified. Exiting.")

        try:
            # Bind socket to specified host and listen
            self.s.bind((self.host, self.port)) 
            self.s.listen(1)
            logger.info("Socket listening on host %s and port %d.", self.host, self.port)
        except socket.error as e:
                logger.error(f"Bind failed. Retrying. Error message: {e.args}")
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
                        logger.error(f"Stopping accept. Exiting. Error message: {e}")
                        sys.exit(0)   

                    if self.o.AllowIPs:
                        if self.remoteHost[0] not in self.o.AllowIPs:
                            logger.debug(f"Connection to IP {self.remoteHost[0]} rejected. Not a part of the Accepted IPs list.")
                            conn.close()
                            continue
                    
                    # Instance forks
                    ## Instance 1 (Parent, pid=child_pid): Stays in the loop trying to accept other connections. 
                    ## Instance 2 (Child, pid=0): Exits loop. Proceeds to initialise the service with the remote host.
                    pid = os.fork()

                    if pid == 0:
                        ## Close the unconnected socket instance as it is unused in the service.
                        self.s.close()

                        ## Set the logfiles properly
                        sarracenia.config.cfglogs(self.o, self.o.component, self.o.config, self.o.logLevel, child_inst)

                        self.o.no = child_inst
                        logger.info(f"Starting up service with host {self.remoteHost[0]}")
                        break                    

                    elif pid == -1:
                        raise logger.exception("Connection could not fork. Exiting.")
        
                    else:
                        pidfilename = sarracenia.config.get_pid_filename(
                        None, self.o.component, self.o.config, child_inst)

                        with open(pidfilename, 'w') as pfn:
                            pfn.write('%d' % pid)

                        ## Close the connected socket instance as it is unused in the parent
                        conn.close()
                        logger.info(f"Forked child from host {self.remoteHost[0]} with instance number {child_inst} and pid {pid}")

                        child_inst += 1
                        pass
                   
                except Exception:
                    logger.error(f"Couldn't accept connection. Parent or child failed. Retrying to accept.")
                    # self.s.close()
                    # conn.close()
                    time.sleep(1)
                
        logger.info("Connection accepted with IP %s on port %d. Starting service.", self.remoteHost[0], self.port)     

        return conn                       


    def on_start(self):
        # Set ipadresses in proper format
        for IP in self.o.AllowIPs:
            IP = ipaddress.ip_address(IP)

        # If there are remaining instances, delete their filepaths and exit.
        if self.o.no != 1:
            pidfilename = sarracenia.config.get_pid_filename(None, self.o.component, self.o.config, self.o.no)
            if os.path.exists(pidfilename):
                os.unlink(pidfilename)
            sys.exit(0)
        
        self.conn = self.__WaitForRemoteConnection__()
    

    def on_stop(self):
        logger.info("On stop called. Exiting.")

        # Close all socket connections (from parent and children) and exit.
        self.s.close()
        if self.o.no == 1:
            pass
        else:
            self.conn.close()
        sys.exit(0)
        

    def AddBuffer(self):
        # try:
        try:
            tmp = self.conn.recv(self.limit)

        except Exception as e:
            tmp = ''
            logger.error(f"Reception has been interrupted. Closing connection and exiting. Error message: {e}")

        if tmp == '':
            self.conn.close()
            raise Exception()
        
        self.inBuffer = self.inBuffer + tmp

        # except socket.error:
            # (type, value, tb) = sys.exc_info()
            # logger.warning("Type: %s, Value: %s, [socket.recv(%d)]" % (type, value, self.limit))
            
            
    def CheckNextMsgStatus(self):

        # Only unpack data if a bulletin is received
        ## When unpacking, the length of the header is vital since it allows the receiver to extract the bulletin contents from the buffer.
        ## AND it determines if all the bulletin contents are available inside the buffer.
        if len(self.inBuffer) >= self.sizeAM:
            (header, src_inet, dst_inet, threads, start, length, firsttime, timestamp, future) = \
                    struct.unpack(self.patternAM,self.inBuffer[0:self.sizeAM])
        else:
            return 'INCOMPLETE'

        length = socket.ntohl(length)

        # logger.debug(f"Buffer contents: {self.inBuffer}")
        
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

            logger.debug("Gather successful.")

            return (bulletin, longlen)
        
        else:
            return '', 0


    def gather(self):

        self.AddBuffer()

        newmsg = []

        while True:
            status = self.CheckNextMsgStatus()
            
            if status == 'INCOMPLETE':
                break

            if status == 'OK':
                (bulletin, longlen) = self.unwrapmsg()

                # Set buffer for next bulletin ingestion
                self.inBuffer = self.inBuffer[longlen:]

                logger.debug(f"Bulletin contents: {bulletin}")

                parse = self.header.split(b'\0',1)
                bulletinHeader = parse[0].decode('iso-8859-1').replace(' ', '_')

                # Create a file for new messages and let sarracenia format the data
                try:
                    ## Filenames have the following naming scheme:
                    ##   1. Bulletin header
                    ##   2. Counter (makes filename unique for each bulletin)
                    ##   IF A* or R* present in header, include in filename
                    ##
                    ##   Example: SXVX65_KWNB_181800_RRB__99705
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
