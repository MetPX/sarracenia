#!/usr/bin/python3

"""
  citypage_check.  debugging plugin.

  delete pages that are OK, leave the bad ones.

  we have a problem with how citypages are being posted.
  a lot of incomplete ones. they are getting posted while they are being
  re-written.

usage:

on_file file_citypage_check


"""
import os,stat,time
from hashlib import md5

class Transformer(object): 
      def __init__(self,parent):
          pass

      def perform(self,parent):
          logger = parent.logger
          msg    = parent.msg

          bad=False

          logger.info("check_file local file %s partflg %s, sumflg %s " % \
              ( msg.new_file, msg.partflg, msg.sumflg ) )
          logger.info("check_file file size  %s, offset %d, length %d. " % \
              ( msg.filesize, msg.offset, msg.length) )

          if msg.partflg != '1' or msg.sumflg != 'd'  :
             logger.warning("ignore parts or not md5sum on data")
             return False

          lstat  = os.stat(msg.new_file)
          fsiz   = lstat[stat.ST_SIZE]

          if fsiz != msg.filesize :
             logger.error("check_file filesize differ (corrupted ?)  lf %d  msg %d" % ( fsiz, msg.filesize ) )
             return False

          f = open(msg.new_file,'rb')
          if msg.offset != 0 : f.seek(msg.offset,0)
          if msg.length != 0 : data = f.read(msg.length)
          else:                data = f.read()
          f.close()
          fsum =  md5(data).hexdigest()

          if fsum != msg.checksum :
             logger.error("check_file checksum differ (corrupted ?)  lf %s  msg %s" % ( fsum, msg.checksum ) )
             bad=True

          if "</siteData>" not in data.decode('iso8859-1'):
             logger.error("check_file does not have </siteData> in it, XML incomplete" )
             bad=True

          if not bad:
             os.unlink(msg.new_file)

          return True

transformer = Transformer(self)
self.on_file = transformer.perform

