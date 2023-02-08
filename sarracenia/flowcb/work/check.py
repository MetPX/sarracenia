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
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class Check(FlowCB):

    def after_work(self, worklist):

        for msg in worklist.ok:
            logger.info("check_file local file %s " % msg['new_file'])
    
            if 'fileOp' in msg:
                logger.warning("ignore unordinary files fileOps")
                if 'directory' in msg['fileOp']:
                    os.unlink(msg['rmdir'])
                else:
                    os.unlink(msg['new_file'])
                continue

            logger.info("check_file integrity     %s " % msg['integrity'] )
            logger.info("check_file filesize   %s " % msg['size'])
    
            lstat = os.stat(msg['new_file'])
            fsiz = lstat[stat.ST_SIZE]
    
            if fsiz != msg['size']:
                logger.error( "check_file filesize differ (corrupted ?)  lf %d  msg %d" % (fsiz, msg['size']) )
                os.unlink(msg['new_file'])
                return False
    
            self.o.post_baseUrl = msg['baseUrl']
            self.o.integrity_method = msg['integrity']['method']
            downloaded_msg = sarracenia.Message.fromFileData( msg['new_file'], self.o, lstat ) 
         
      
            if downloaded_msg['integrity'] != msg['integrity']:
                logger.error(
                    "check_file checksum differ (corrupted ?)  lf %s  msg %s" %
                    (downloaded_msg['integrity'], msg['integrity']))
    
            os.unlink(msg['new_file'])
            logger.info( f"checked out ok {msg['new_file']}" )
