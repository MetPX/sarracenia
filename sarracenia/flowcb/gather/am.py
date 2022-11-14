#!/usr/bin/python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#

"""
Sundew migration

An AM (Alphanumeric Messaging) receiver to further migrate advance the migration to sr3.

Usage:

"""

import logging, socket, struct, copy, time#, string, sys, traceback
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class AM(FlowCB):

    def __init__(self, options):
        pass

    def __establishconn__(self):
        

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        s.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)

        if self.am.type == 'slave':
            logger.info("Socket binding with port %d",self.am.port)
            while True:
                try:
                    s.bind(('',self.am.port))
                    break
                except socket.error:
                    logger.info("Bind failed")
                    time.sleep(10)