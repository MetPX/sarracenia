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
#  Jun Hu         - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Sep 22 10:41:32 EDT 2015
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

def file_insert( msg ) :

    # file must exists
    if not os.path.isfile(msg.url.path):
       fp = open(msg.url.path,'w')
       fp.close

    fp = open(msg.url.path,'r+b')
    if msg.partflg == 'i' : fp.seek(msg.offset,0)

    ok = file_write_length(fp, msg )

    fp.close()

    return ok

# when inserting, anything that goes wrong means that
# another process is working with this part_file
# so errors are ignored silently 

def file_insert_part(msg,part_file):
    try :
             # file disappeared ...
             # probably inserted by another process in parallel
             if not os.path.isfile(part_file): return False

             # file with wrong size
             # probably being written now by another process in parallel

             lstat    = os.stat(part_file)
             fsiz     = lstat[stat.ST_SIZE] 
             if fsiz != msg.length : return False

             # proceed with insertion

             fp = open(part_file,'rb')
             ft = open(msg.target_file,'r+b')
             ft.seek(msg.offset,0)

             # no worry with length, read all of part_file
             i  = 0
             while i<msg.length :
                   buf = fp.read(msg.bufsize)
                   ft.write(buf)
                   i  += len(buf)

             ft.close()
             fp.close()


             # remove inserted part file

             try    : os.unlink(part_file)
             except : pass

    # oops something went wrong

    except :
             msg.logger.debug("did not insert %s " % part_file)
             return False

    # success: log insertion

    msg.code    = 201
    msg.message = 'Inserted'
    msg.log_info()

    # publish now, if needed, that it is inserted

    if msg.amqp_pub == None : return True

    msg.set_topic_url('v02.post',msg.target_url)
    msg.set_notice(msg.target_url,msg.time)
    msg.code    = 201
    msg.message = 'Published'
    msg.publish()

    return True

def file_link( msg ) :

    try    : os.unlink(msg.local_file)
    except : pass
    try    : os.link(msg.url.path,msg.local_file)
    except : return False

    msg.code    = 201
    msg.message = 'Linked'
    msg.log_info()

    return True

def file_process( msg ) :

    # try link if no inserts

    if msg.partflg == '1' or \
       (msg.partflg == 'p' and  msg.in_partfile) :
       ok = file_link(msg)
       if ok : return ok

    try :
             ok = file_insert(msg)
             if ok : return ok

    except : pass

    msg.code    = 499
    msg.message = 'Not Copied'
    msg.log_error()

    return False

# when ever a part file is processed (inserted or written in part_file)
# this module is called to try inserting any part_file left

def file_reassemble(msg):

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
          partstr = '%s,%d,%d,%d,%d' %\
                    ('i',msg.chunksize,msg.block_count,msg.remainder,msg.current_block)
          msg.set_parts_str(partstr)
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
             return


          # insertion attempt... should work unless there is some race condition

          ok = file_insert_part(msg,part_file)
          # break and not return because we want to check the lastchunk processing
          if not ok : break


          i = i + 1

    # out of the look... 
    # check if file needs to be truncated
    file_truncate(msg)

# write exact length

def file_write_length(req,msg):
    # file should exists
    if not os.path.isfile(msg.local_file) :
       fp = open(msg.local_file,'w')
       fp.close()

    # file open read/modify binary
    fp = open(msg.local_file,'r+b')
    if msg.local_offset != 0 : fp.seek(msg.local_offset,0)

    nc = int(msg.length/msg.bufsize)
    r  =     msg.length%msg.bufsize

    # read/write bufsize "nc" times
    i  = 0
    while i < nc :
          chunk = req.read(msg.bufsize)
          fp.write(chunk)
          i = i + 1

    # remaining
    if r > 0 :
       chunk = req.read(r)
       fp.write(chunk)

    fp.close()

    msg.code    = 201
    msg.message = 'Copied'
    msg.log_info()

    return True

def file_truncate(msg):

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
                msg.code    = 205
                msg.message = 'Reset Content :truncated'
                msg.log_info()

    except : pass
