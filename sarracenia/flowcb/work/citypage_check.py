#!/usr/bin/python3
"""
  For Production deployments, see: part_check instead of this file (file_check)  

  As check re-reads the entire file, re-calculates from scratch, which is very inefficient 
  compared to part_check which takes care of checksum calc done as the files are downloaded.
  NOTE: it also deletes the downloaded file after checking!

Usage:

   callback work.check

STATUS:
  This is more for debugging, internal testing, and reference.
  20171212: not sure if it has been fixed after the local->new transition.

"""
import os, stat, time
from hashlib import md5
import logging

import sarracenia
from sarracenia.flowcb.work.check import Check

logger = logging.getLogger(__name__)

class Citypage_check(Check):

    def content_check(self, local_file) -> bool:
        logger.info(" start")
        f = open(local_file, 'rb')
        data = f.read()
        f.close()

        bad = False
        if "</siteData>" not in data.decode('iso8859-1'):
            logger.error( "does not have </siteData> in it, XML incomplete saving...")
            return False
        logger.info(" done")
        return True
