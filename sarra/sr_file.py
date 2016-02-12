#!/usr/bin/python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SarraDocumentation
#
# sr_file.py : python3 utility tools for file processing
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Feb  5 09:48:34 EST 2016
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, 
#  but WITHOUT ANY WARRANTY; without even the implied warranty of 
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#
#

import os, stat, sys

# file_insert
# called by file_process (general file:// processing)

def file_insert( parent,msg ) :
    parent.logger.debug("file_insert")

    # file must exists
    if not os.path.isfile(msg.url.path):
       fp = open(msg.url.path,'w')
       fp.close()

    fp = open(msg.url.path,'r+b')
    if msg.partflg == 'i' : fp.seek(msg.offset,0)

    ok = file_write_length(fp, msg, parent.bufsize )

    fp.close()

    return ok


# file_insert_part
# called by file_reassemble : rebuiding file from parts
#
# when inserting, anything that goes wrong means that
# another process is working with this part_file
# so errors are ignored silently 

def file_insert_part(parent,msg,part_file):
    parent.logger.debug("file_insert_part %s" % part_file)
    chk = msg.sumalgo
    try :
             # file disappeared ...
             # probably inserted by another process in parallel
             if not os.path.isfile(part_file):
                parent.logger.debug("file doesnt exist %s" % part_file)
                return False

             # file with wrong size
             # probably being written now by another process in parallel

             lstat    = os.stat(part_file)
             fsiz     = lstat[stat.ST_SIZE] 
             if fsiz != msg.length : 
                parent.logger.debug("file wrong size %s %d %d" % (part_file,fsiz,msg.length))
                return False

             # proceed with insertion

             fp = open(part_file,'rb')
             ft = open(msg.target_file,'r+b')
             ft.seek(msg.offset,0)

             # no worry with length, read all of part_file
             # compute onfly_checksum ...

             bufsize = parent.bufsize
             if bufsize > msg.length : bufsize = msg.length

             if chk : chk.set_path(os.path.basename(msg.target_file))

             i  = 0
             while i<msg.length :
                   buf = fp.read(bufsize)
                   if not buf: break
                   ft.write(buf)
                   if chk : chk.update(buf)
                   i  += len(buf)

             ft.close()
             fp.close()

             if i != msg.length :
                msg.logger.error("file_insert_part file currupted %s" % part_file)
                msg.logger.error("read up to  %d of %d " % (i,msg.length) )
                lstat   = os.stat(part_file)
                fsiz    = lstat[stat.ST_SIZE] 
                msg.logger.error("part filesize  %d " % (fsiz) )

             # set checksum in msg
             if chk : msg.onfly_checksum = chk.get_value()

             # remove inserted part file

             try    : os.unlink(part_file)
             except : pass

             # run on part... if provided

             if parent.on_part :
                ok = parent.on_part(parent)
                if not ok : 
                   msg.logger.warning("inserted but rejected by on_part %s " % part_file)
                   msg.logger.warning("the file may not be correctly reassemble %s " % msg.target_file)
                   return ok

    # oops something went wrong

    except :
             (stype, svalue, tb) = sys.exc_info()
             msg.logger.debug("Type: %s, Value: %s,  ..." % (stype, svalue))
             msg.logger.debug("did not insert %s " % part_file)
             return False

    # success: log insertion

    msg.log_publish(201,'Inserted')

    # publish now, if needed, that it is inserted

    if msg.publisher : 
       msg.set_topic_url('v02.post',msg.target_url)
       msg.set_notice(msg.target_url,msg.time)
       if chk :
          if    msg.sumflg == 'z' :
                msg.set_sum(msg.checksum,msg.onfly_checksum)
          else: msg.set_sum(msg.sumflg,  msg.onfly_checksum)

       parent.__on_post__()
       msg.log_publish(201,'Publish')

    # if lastchunk, check if file needs to be truncated
    file_truncate(parent,msg)

    # ok we reassembled the file and it is the last chunk... call on_file
    if msg.lastchunk : 
       msg.logger.warning("file assumed complete with last part %s" % msg.target_file)
       if parent.on_file:
          ok = parent.on_file(parent)
          return ok

    return True


# file_link
# called by file_process (general file:// processing)

def file_link( msg ) :

    try    : os.unlink(msg.local_file)
    except : pass
    try    : os.link(msg.url.path,msg.local_file)
    except : return False

    msg.compute_local_checksum()
    msg.onfly_checksum = msg.local_checksum

    msg.log_publish( 201, 'Linked')

    return True

# file_process (general file:// processing)

def file_process( parent ) :
    parent.logger.debug("file_process")

    msg = parent.msg

    # try link if no inserts

    if msg.partflg == '1' or \
       (msg.partflg == 'p' and  msg.in_partfile) :
       ok = file_link(msg)
       if ok : return ok

    # This part is for 2 reasons : insert part
    # or copy file if preceeding link did not work
    try :
             ok = file_insert(parent,msg)
             if ok : return ok

    except : 
             (stype, svalue, tb) = sys.exc_info()
             msg.logger.debug("Type: %s, Value: %s,  ..." % (stype, svalue))

    msg.log_publish(499,'Not Copied')
    msg.logger.error("could not copy %s in %s"%(msg.url.path,msg.local_file))

    return False

# file_reassemble : rebuiding file from parts
# when ever a part file is processed (inserted or written in part_file)
# this module is called to try inserting any part_file left

def file_reassemble(parent):
    parent.logger.debug("file_reassemble")

    msg = parent.msg

    # target file does not exit yet

    if not os.path.isfile(msg.target_file) :
       msg.logger.debug("insert_from_parts: target_file not found %s" % msg.target_file)
       return

    # check target file size and pick starting part from that

    lstat   = os.stat(msg.target_file)
    fsiz    = lstat[stat.ST_SIZE] 
    i       = int(fsiz /msg.chunksize)

    msg.logger.debug("verify ingestion : block = %d of %d" % (i,msg.block_count))
       
    while i < msg.block_count:

          # setting block i in message

          msg.current_block = i
          msg.set_parts('i',msg.chunksize,msg.block_count,msg.remainder,msg.current_block)
          msg.set_suffix()

          # set part file

          part_file = msg.target_file + msg.suffix
          if not os.path.isfile(part_file) :
             msg.logger.debug("part file %s not found, stop insertion" % part_file)
             # break and not return because we want to check the lastchunk processing
             break

          # check for insertion (size may have changed)

          lstat   = os.stat(msg.target_file)
          fsiz    = lstat[stat.ST_SIZE] 
          if msg.offset > fsiz :
             msg.logger.debug("part file %s no ready for insertion (fsiz %d, offset %d)" % (part_file,fsiz,msg.offset))
             break


          # insertion attempt... should work unless there is some race condition

          ok = file_insert_part(parent,msg,part_file)
          # break and not return because we want to check the lastchunk processing
          if not ok : break
          i = i + 1

    # if lastchunk, check if file needs to be truncated
    file_truncate(parent,msg)



# file_write_length
# called by file_process->file_insert (general file:// processing)

def file_write_length(req,msg,bufsize):
    msg.logger.debug("file_write_length")

    msg.onfly_checksum = None

    chk = msg.sumalgo
    msg.logger.debug("file_write_length chk = %s" % chk)
    if chk : chk.set_path(os.path.basename(msg.local_file))

    # file should exists
    if not os.path.isfile(msg.local_file) :
       fp = open(msg.local_file,'w')
       fp.close()

    # file open read/modify binary
    fp = open(msg.local_file,'r+b')
    if msg.local_offset != 0 : fp.seek(msg.local_offset,0)

    nc = int(msg.length/bufsize)
    r  =     msg.length%bufsize

    # read/write bufsize "nc" times
    i  = 0
    while i < nc :
          chunk = req.read(bufsize)
          fp.write(chunk)
          if chk : chk.update(chunk)
          i = i + 1

    # remaining
    if r > 0 :
       chunk = req.read(r)
       fp.write(chunk)
       if chk : chk.update(chunk)

    fp.close()
  
    if chk : msg.onfly_checksum = chk.get_value()

    msg.log_publish(201,'Copied')

    return True

# file_truncate
# called under file_reassemble (itself and its file_insert_part)
# when inserting lastchunk, file may need to be truncated

def file_truncate(parent,msg):

    # will do this when processing the last chunk
    # whenever that is
    if not msg.lastchunk : return

    try :
             lstat   = os.stat(msg.target_file)
             fsiz    = lstat[stat.ST_SIZE] 

             if fsiz > msg.filesize :
                fp = open(msg.target_file,'r+b')
                fp.truncate(msg.filesize)
                fp.close()

                msg.set_topic_url('v02.post',msg.target_url)
                msg.set_notice(msg.target_url,msg.time)
                msg.log_publish(205, 'Reset Content :truncated')

    except : pass

