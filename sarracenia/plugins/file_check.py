#!/usr/bin/python3
"""
  For Production deployments, see: part_check instead of this file (file_check)  

  As file_check re-reads the entire file, re-calculates from scratch, which is very inefficient 
  compared to part_check which takes care of checksum calc done as the files are downloaded.
  NOTE: it also deletes the downloaded file after checking!

STATUS:
  This is more for debugging, internal testing, and reference.
  20171212: not sure if it has been fixed after the local->new transition.

"""
import os, stat, time
from hashlib import md5


class Transformer(object):
    def __init__(self, parent):
        pass

    def perform(self, parent):
        logger = parent.logger
        msg = parent.msg

        logger.info("check_file local file %s " % msg.new_file)
        logger.info("check_file partflg    %s " % msg.partflg)
        logger.info("check_file sumflg     %s " % msg.sumflg)
        logger.info("check_file filesize   %s " % msg.filesize)
        logger.info("check_file offset     %d " % msg.offset)
        logger.info("check_file length     %d " % msg.length)

        if msg.partflg != '1' or msg.sumflg != 'd':
            logger.warning("ignore parts or not md5sum on data")
            os.unlink(msg.new_file)
            return False

        lstat = os.stat(msg.new_file)
        fsiz = lstat[stat.ST_SIZE]

        if fsiz != msg.filesize:
            logger.error(
                "check_file filesize differ (corrupted ?)  lf %d  msg %d" %
                fsiz, msg.filesize)
            os.unlink(msg.new_file)
            return False

        f = open(msg.new_file, 'rb')
        if msg.offset != 0: f.seek(msg.offset, 0)
        if msg.length != 0: data = f.read(msg.length)
        else: data = f.read()
        f.close()
        fsum = md5(data).hexdigest()

        if fsum != msg.checksum:
            logger.error(
                "check_file checksum differ (corrupted ?)  lf %s  msg %s" %
                fsum, msg.checksum)

        os.unlink(msg.new_file)
        return False


transformer = Transformer(self)
self.on_file = transformer.perform
