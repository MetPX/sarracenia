#!/usr/bin/python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#

"""
Sundew migration

sarracenia.flowcb.gather.am.AM is a sarracenia version 3 plugin used to receive messages with 
the AM (Alphanumeric Messaging) protocol.

By: André LeBlanc, Autumn 2022
"""

import logging, socket, struct, time, sys
from sarracenia.flowcb import FlowCB 
from sarracenia.config import Config

FORMAT ='%(asctime)s %(message)s'
logging.basicConfig(filename='sarracenia/flowcb/gather/sarra-am-rec.log', format=FORMAT) #TODO change log path
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class AM(FlowCB):

    def __init__(self, options):
        self.o = options
        

        self.am = Config()
        self.am.add_option('keepAlive','flag', False)
        self.am.add_option('onlySync','flag', True)
        self.am.add_option('patternAM','str','80sII4sIIII20s')
        self.am.add_option('sizeAM', 'count', struct.calcsize(self.am.patternAM))
        self.am.add_option('port', 'count', 5002) # Put count because it's integer type - 5002 test value
        self.am.add_option('connected', 'flag', False)
        self.am.add_option('remoteHost', 'str', '127.0.0.1') # localhost test value
        self.limit = 32678
        self.inBuffer = None

        # Initialise socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Establish connection and send bytes through socket
        self.conn = self.__establishconn__()

    def __establishconn__(self):
        """
        
        """        
        logger.info("gather/am.py: Socket binding with IP %s, port %d" % (self.am.remoteHost ,self.am.port))

        while True:
            try:
                self.s.bind(('', self.am.port)) 
                self.s.listen(1)
                conn, addr = self.s.accept()
                self.am.connected = True
                break
            except socket.error:
                logger.info("gather/am.py: Bind failed. Retrying.")
                time.sleep(10)

        """
        if self.flow.keepAlive:
            self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
            logger.info('gather/am.py: SO_KEEPALIVE set to 1')
        else:
            self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,0)
            logger.info('gather/am.py: SO_KEEPALIVE set to 0')      
        """
        logger.info("gather/am.py: Socket binded to IP %s and on port %d", self.am.remoteHost, self.am.port)     

        return conn               

    def SyncInBuffer(self):
        """
        
        """

        while True:
            try:
                tmp = self.conn.recv(self.limit)

                if tmp == '':
                    self.am.connected = False
                    if self.am.onlySync:
                        logger.exception("gather/am.py: Connection was lost")
                        raise Exception("gather/am.py: Connection was lost")
                
                logger.info("gather/am.py: Message length - %d Bytes, Data received from socket - %s" % (len(tmp),tmp))
                
                self.inBuffer = tmp
                break   

            except socket.error:
                self.s.close()

                (type, value, tb) = sys.exc_info()

                # Normally, this error is generated when a SIGHUP signal is sent and the system call (socket.recv(32768))
                # is interrupted
                logger.warning("Type: %s, Value: %s, [socket.recv(%d)]" % (type, value, self.limit))
                break

    def CheckNextMsgStatus(self):
        """
        
        """
        logger.info("gather/am.py: Verifying message integrity.")

        self.SyncInBuffer()

        if len(self.inBuffer) >= self.am.sizeAM:
            (header, src_inet, dst_inet, threads, start, length, firsttime, timestamp, future) = \
                    struct.unpack(self.am.patternAM,self.inBuffer[0:self.am.sizeAM])
        else:
            return 'INCOMPLETE'

        length = socket.ntohl(length)

        if len(self.inBuffer) >= self.am.sizeAM + length:
            return 'OK'
        else:
            logger.info("gather/am.py: Verification failure. Exiting gather.")
            return 'INCOMPLETE'

    def unwrapmsg(self):
        """

        """

        status = self.CheckNextMsgStatus()

        if status == 'OK':
            (header,src_inet,dst_inet,threads,start,length,firsttime,timestamp,future) = \
                     struct.unpack(self.am.patternAM,self.inBuffer[0:self.am.sizeAM])

            length = socket.ntohl(length)

            msg = self.inBuffer[self.am.sizeAM:self.am.sizeAM + length]

            logger.info("gather/am.py: Gather successful.")

            return (msg, self.am.sizeAM + length)
        else:
            return '',0                

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

am = AM(default_options)
res = am.unwrapmsg()
print(res)