#!/usr/bin/env python3
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

import os, stat, sys, time

#============================================================
# file protocol in sarracenia supports/uses :
#
# connect
# close
#
# if a source    : get    (remote,local)
#                  ls     ()
#                  cd     (dir)
#                  delete (path)
#
# require   parent.logger
#           parent.credentials
#           parent.destination 
#           parent.batch 
#           parent.chmod
#           parent.chmod_dir
#     opt   parent.kbytes_ps
#     opt   parent.bufsize

class sr_file():
    def __init__(self, parent) :
        parent.logger.debug("sr_file __init__")

        self.logger      = parent.logger
        self.parent      = parent 

    # cd
    def cd(self, path):
        self.logger.debug("sr_file cd %s" % path)
        os.chdir(path)
        self.path = path

    # chmod
    def chmod(self,perm,path):
        self.logger.debug("sr_file chmod %s %s" % ( "{0:o}".format(perm),path))
        os.chmod(path,perm)

    # close
    def close(self):
        self.logger.debug("sr_file close")
        return

    # connect
    def connect(self):
        self.logger.debug("sr_file connect %s" % self.parent.destination)

        self.recursive   = True
        self.destination = self.parent.destination
        self.timeout     = self.parent.timeout

        self.kbytes_ps = 0
        self.bufsize   = 8192

        if hasattr(self.parent,'kbytes_ps') : self.kbytes_ps = self.parent.kbytes_ps
        if hasattr(self.parent,'bufsize')   : self.bufsize   = self.parent.bufsize

        self.connected   = True

        return True

    # delete
    def delete(self, path):
        self.logger.debug("sr_file rm %s" % path)
        os.unlink(path)

    # ls
    def ls(self):
        self.logger.debug("sr_file ls")
        self.entries  = {}
        self.root = self.path
        self.ls_python(self.path)
        return self.entries

    def ls_python(self,dpath):
        for x in os.listdir(dpath):
            dst = dpath + os.sep + x
            if os.path.isdir(dst):
               if self.recursive : self.ls_python(dst)
               continue
            relpath = dst.replace(self.root,'',1)
            if relpath[0] == '/' : relpath = relpath[1:]

            lstat = os.stat(dst)
            line  = stat.filemode(lstat.st_mode)
            line += ' %d %d %d' % (lstat.st_nlink,lstat.st_uid,lstat.st_gid)
            line += ' %d' % lstat.st_size
            line += ' %s' % time.strftime("%b %d %H:%M", time.localtime(lstat.st_mtime))
            line += ' %s' % relpath
            self.entries[relpath] = line



# file_insert
# called by file_process (general file:// processing)

def file_insert( parent,msg ) :
    parent.logger.debug("file_insert")

    # file must exists
    if not os.path.isfile(msg.relpath):
       fp = open(msg.relpath,'w')
       fp.close()

    fp = open(msg.relpath,'r+b')
    if msg.partflg == 'i' : fp.seek(msg.offset,0)

    ok = file_write_length(fp, msg, parent.bufsize, msg.filesize )

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

             if ft.tell() >= msg.filesize:
                 ft.truncate()

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

    msg.report_publish(201,'Inserted')

    # publish now, if needed, that it is inserted

    if msg.publisher : 
       msg.set_topic('v02.post',msg.target_relpath)
       msg.set_notice(msg.new_baseurl,msg.target_relpath,msg.time)
       if chk :
          if    msg.sumflg == 'z' :
                msg.set_sum(msg.checksum,msg.onfly_checksum)
          else: msg.set_sum(msg.sumflg,  msg.onfly_checksum)

       parent.__on_post__()
       msg.report_publish(201,'Publish')

    # if lastchunk, check if file needs to be truncated
    file_truncate(parent,msg)

    # ok we reassembled the file and it is the last chunk... call on_file
    if msg.lastchunk : 
       msg.logger.warning("file assumed complete with last part %s" % msg.target_file)
       #if parent.on_file:
       #   ok = parent.on_file(parent)
       for plugin in parent.on_file_list:
          ok = plugin(parent)
          if not ok: return False

    return True


# file_link
# called by file_process (general file:// processing)

def file_link( msg ) :

    try    : os.unlink(msg.new_file)
    except : pass
    try    : os.link(msg.relpath,msg.new_file)
    except : return False

    msg.compute_local_checksum()
    msg.onfly_checksum = msg.local_checksum

    msg.report_publish( 201, 'Linked')

    return True

# file_process (general file:// processing)

def file_process( parent ) :
    parent.logger.debug("file_process")

    msg = parent.msg

    try:    curdir = os.getcwd()
    except: curdir = None

    if curdir != parent.new_dir:
       os.chdir(parent.new_dir)

    # try link if no inserts

    if msg.partflg == '1' or \
       (msg.partflg == 'p' and  msg.in_partfile) :
       ok = file_link(msg)
       if ok :
          if parent.delete :
              try: 
                  os.unlink(msg.relpath)
              except: 
                  msg.logger.error("delete of link to %s failed"%(msg.relpath))
          return ok

    # This part is for 2 reasons : insert part
    # or copy file if preceeding link did not work
    try :
             ok = file_insert(parent,msg)
             if parent.delete :
                if msg.partflg.startswith('i'):
                   msg.logger.info("delete unimplemented for in-place part files %s" %(msg.relpath))
                else:
                   try: 
                       os.unlink(msg.relpath)
                   except: 
                       msg.logger.error("delete of %s after copy failed"%(msg.relpath))

             if ok : return ok

    except : 
             (stype, svalue, tb) = sys.exc_info()
             msg.logger.debug("Type: %s, Value: %s,  ..." % (stype, svalue))

    msg.report_publish(499,'Not Copied')
    msg.logger.error("could not copy %s in %s"%(msg.relpath,msg.new_file))

    return False

# file_reassemble : rebuiding file from parts
# when ever a part file is processed (inserted or written in part_file)
# this module is called to try inserting any part_file left

def file_reassemble(parent):
    parent.logger.debug("file_reassemble")

    msg = parent.msg

    if not hasattr(msg,'target_file') or msg.target_file == None : return

    try:    curdir = os.getcwd()
    except: curdir = None

    if curdir != parent.new_dir:
       os.chdir(parent.new_dir)

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

def file_write_length(req,msg,bufsize,filesize):
    msg.logger.debug("file_write_length")

    msg.onfly_checksum = None

    chk = msg.sumalgo
    msg.logger.debug("file_write_length chk = %s" % chk)
    if chk : chk.set_path(msg.new_file)

    # file should exists
    if not os.path.isfile(msg.new_file) :
       fp = open(msg.new_file,'w')
       fp.close()

    # file open read/modify binary
    fp = open(msg.new_file,'r+b')
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

    if fp.tell() >= msg.filesize:
       fp.truncate()

    fp.close()
  
    h = self.parent.msg.headers
    if self.parent.preserve_mode and 'mode' in h :
       try   : mod = int( h['mode'], base=8)
       except: mod = 0
       if mod > 0 : os.chmod(msg.new_file, mod )

    if self.parent.preserve_time and 'mtime' in h and h['mtime'] :
        os.utime(msg.new_file, times=( timestr2flt( h['atime']), timestr2flt( h[ 'mtime' ] )))

    if chk : msg.onfly_checksum = chk.get_value()

    msg.report_publish(201,'Copied')

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

                msg.set_topic('v02.post',msg.target_relpath)
                msg.set_notice(msg.new_baseurl,msg.target_relpath,msg.time)
                msg.report_publish(205, 'Reset Content :truncated')

    except : pass


#
#     protocol standardization class
#

class sr_file2():
    def __init__(self, parent) :
        parent.logger.debug("sr_file __init__")

        self.logger      = parent.logger
        self.parent      = parent 
        self.kbytes_ps   = 0
        self.bufsize     = 8192

        self.cd          = os.chdir
        self.delete      = os.unlink
        self.getcwd      = os.getcwd
        self.mkdir       = os.mkdir
        self.rename      = os.rename #(try delete before)
        self.rmdir       = os.rmdir
        self.symlink     = os.symlink

        self.close       = self.dummy

        self.batch       = 0
        self.sumalgo     = None
        self.checksum    = None
        self.fpos        = 0

        self.support_delete   = True
        self.support_download = True
        self.support_inplace  = True
        self.support_send     = True


    # cd forced
    def cd_forced(self,perm,path) :
        try   : os.makedirs(path, perm,True)
        except: pass
        os.chdir(path)

    # check_is_connected
    def check_is_connected(self):
        return self.connected

    # chmod
    def chmod(self,perm,path):
        os.chmod(path,perm)

    # connect...
    def connect(self):
        self.connected = False
        if not self.parent.destination.startwith('file:') : return False
        self.connected = True

        self.destination = self.parent.destination

        if hasattr(self.parent,'kbytes_ps') : self.kbytes_ps = self.parent.kbytes_ps
        if hasattr(self.parent,'bufsize')   : self.bufsize   = self.parent.bufsize

        self.originalDir = self.getcwd()
        self.pwd         = self.originalDir

        return True

    def dummy(self):
        return True

    def init_checksum(self,path):

        self.do_sum   = self.sumalgo
        self.checksum = None

        if self.do_sum : self.do_sum.set_path(path)

    def init_throttle(self):

        self.do_throttle = None
        if self.kbytes_ps > 0.0 :
           self.do_throttle = self.throttle
           self.tbytes      = 0.0
           self.tbegin      = time.time()
           self.bytes_ps    = self.kbytes_ps * 1024.0

    # local_close
    def local_close(self):

        # io sync
        self.local_fp.flush()
        os.fsync(self.local_fp)

        # keep current position
        self.fpos = self.local_fp.tell()

        # MG FIXME... this makes no sense
        if filesize != None and self.fpos >= filesize :
           self.local_fp.truncate(filesize) 

        self.local_fp.close()

        if self.do_sum : self.checksum = self.do_sum.get_value()

    # local_open
    def local_open(self,path,offset):

        # needed ... to open r+b file need to exist
        if not os.path.isfile(local_file) :
           local_fp = open(local_file,'w')
           local_fp.close()

        self.local_fp = open(local_file,'r+b')
        if local_offset != 0 : self.local_fp.seek(local_offset,0)

        return self.local_fp

    # local_write
    def local_write(self,chunk):
        self.local_fp.write(chunk)
        if self.do_sum      : self.do_sum.update(chunk)
        if self.do_throttle : self.do_throttle(chunk)

    # set_sumalgo checksum algorithm
    def set_sumalgo(self,sumalgo) :
        self.logger.debug("sr_file set_sumalgo %s" % sumalgo)
        self.sumalgo = sumalgo

    # transfer 
    def transfer(self, remote_file, remote_fp, local_file, local_offset=0, length=0, filesize=None):
        self.logger.debug("sr_file transfer %s %s %d %d" % (remote_file,local_file,local_offset,length))

        # init onfly checksum 

        self.init_checksum(remote_file)

        # init onfly throttle 

        self.init_throttle()

        # open local file 

        fp = self.open_local(local_file,local_offset)

        # get a certain length in file

        if length != 0 : self.transfer_part(remote_fp,length)
        else:            self.transfer_file(remote_fp)
 
        self.local_close()

    # transfer file
    def transfer_file(self,remote_fp) :
        while True :
              chunk = remote_fp.read(self.bufsize)
              if not chunk : break
              self.local_write(chunk)

    # transfer part
    def transfer_part(self,remote_fp,length) :
        nc = int(length/self.bufsize)
        r  = length%self.bufsize

        # read/write bufsize "nc" times
        i  = 0
        while i < nc :
              chunk = remote_fp.read(self.bufsize)
              if not chunk : break
              self.local_write(chunk)
              i = i + 1

        # remaining
        if r > 0 :
           chunk = remote_fp.read(r)
           self.local_write(chunk)


    # throttle
    def throttle(self,buf) :
        self.logger.debug("sr_file throttle")
        self.tbytes = self.tbytes + len(buf)
        span  = self.tbytes / self.bytes_ps
        rspan = time.time() - self.tbegin
        if span > rspan :
           time.sleep(span-rspan)

    # get 
    def get(self, remote_file, local_file, remote_offset=0, local_offset=0, length=0, filesize=None):
        self.logger.debug("sr_file get %s %s %d %d %d" % (remote_file,local_file,remote_offset,local_offset,length))

        rfp = open(remote_file,'rb')
        if remote_offset != 0 : rfp.seek(remote_offset,0)

        self.transfer(remote_file,rfp,local_file,local_offset, length, filesize)

        rfp.close()

    # ls
    def ls(self):
        self.logger.debug("sr_file ls")
        self.entries  = {}
        dir_attr = self.sftp.listdir_attr()
        for index in range(len(dir_attr)):
            attr = dir_attr[index]
            line = attr.__str__()
            self.line_callback(line)
        #self.logger.debug("sr_sftp ls = %s" % self.entries )
        return self.entries

    # line_callback: ls[filename] = 'stripped_file_description'
    def line_callback(self,iline):
        #self.logger.debug("sr_sftp line_callback %s" % iline)

        oline  = iline
        oline  = oline.strip('\n')
        oline  = oline.strip()
        oline  = oline.replace('\t',' ')
        opart1 = oline.split(' ')
        opart2 = []

        for p in opart1 :
            if p == ''  : continue
            opart2.append(p)

        fil  = opart2[-1]
        line = ' '.join(opart2)

        self.entries[fil] = line

    # put
    def put(self, local_file, remote_file, local_offset=0, remote_offset=0, length=0, filesize=None):
        self.logger.debug("sr_sftp put %s %s %d %d %d" % (local_file,remote_file,local_offset,remote_offset,length))
    #
    #   self.get(remote_file,local_file,remote_offset,local_offset,length,filesize)
    #
    #
    #   mod = 0
    #   msg = self.parent.msg
    #   if self.parent.preserve_mode and 'mode' in msg.headers :
    #      mod = int(msg.headers['mode'], base=8)
    #      if mod > 0 : self.chmod( mod )
    #   elif self.parent.chmod !=0 : 
    #      self.chmod( self.parent.chmod )
    #
    #   if self.parent.preserve_time and 'mtime' in msg.headers :
    #      self.utime( ( timestr2flt( msg.headers['atime']), timestr2flt( msg.headers[ 'mtime' ] ))) 


