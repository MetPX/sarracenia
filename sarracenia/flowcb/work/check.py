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

    def reset_metrics(self):
        self.checksum_mismatches=0
        self.size_mismatches=0
        self.ok=0
        self.bad_content=0

    def on_start(self):
        logger.info("")
        self.reset_metrics()

    def content_check(self,local_file) -> bool:
        """
           return True if content is ok, false otherwise.
        """
        logger.info("no content check implemented")
        return True

    def after_work(self, worklist):

        for msg in worklist.ok:
    
            local_file = os.path.join( msg['new_dir'], msg['new_file'] )
            logger.info("start local file %s " % local_file )

            if 'fileOp' in msg:
                logger.warning("ignore unordinary files fileOps")
                if 'directory' in msg['fileOp']:
                    os.unlink(local_file)
                else:
                    os.unlink(local_file)
                continue

            logger.info("identity     %s " % msg['identity'] )
            logger.info("filesize   %s " % msg['size'])
    
            lstat = os.stat(local_file)
            fsiz = lstat[stat.ST_SIZE]
    
            if fsiz != msg['size']:
                logger.error( "filesize differ (corrupted ?)  lf %d  msg %d" % (fsiz, msg['size']) )
                self.size_mismatches+=1
    
            self.o.post_baseUrl = msg['baseUrl']
            self.o.identity_method = msg['identity']['method']
            downloaded_msg = sarracenia.Message.fromFileData( local_file, self.o, lstat ) 
         
      
            if downloaded_msg['identity'] != msg['identity']:
                logger.error(
                    "checksum differ (corrupted ?)  lf %s  msg %s" %
                    (downloaded_msg['identity'], msg['identity']))
                self.checksum_mismatches+=1

            if self.content_check(local_file):
                os.unlink(local_file)
                logger.info( f"checked out ok {local_file}" )
                self.ok+=1
            else:
                self.bad_content+=1

    def metricsReport(self) -> dict:
        return { 'checked_ok': self.ok, 
                 'checked_size_mismatches': self.size_mismatches, 
                 'checked_checksum_mismatches': self.checksum_mismatches,
                 'checked_bad_content': self.bad_content
                 }

    def on_housekeeping(self) -> None:
        self.reset_metrics()
