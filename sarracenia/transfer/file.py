#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#
# sr_file.py : python3 utility tools for file processing
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Aug 23 10:41:32 EDT 2018
#  Last Revision  : Feb  5 09:48:34 EST 2016
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 2 of the License.
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

from sarracenia.transfer import Transfer

import os, stat, subprocess, sys, time

import logging

logger = logging.getLogger(__name__)

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
# require   logger
#           options.credentials
#           options.destination
#           options.batch
#           options.chmod
#           options.chmod_dir
#     opt   options.bytes_per_second
#     opt   options.bufsize


class File(Transfer):
    def __init__(self, proto, options):
        super().__init__(proto, options)

        self.o.add_option("accel_cp_command", "str", "/usr/bin/cp %s %d")
        logger.debug("sr_file __init__")
        self.cwd = None

    def registered_as():
        return ['file']

    # cd
    def cd(self, path):
        """
           proto classes are used for remote sessions, so this 
           cd is for REMOTE directory... when file remote as a protocol it is for the source.
           should not change the "local" working directory when downloading.
        """
        logger.debug("sr_file cd %s" % path)
        #os.chdir(path)
        self.cwd = path
        self.path = path

    def check_is_connected(self):
        return True

    # chmod
    def chmod(self, perm, path):
        logger.debug("sr_file chmod %s %s" % ("{0:o}".format(perm), path))
        os.chmod(path, perm)

    # close
    def close(self):
        logger.debug("sr_file close")
        return

    # connect
    def connect(self):
        logger.debug("sr_file connect %s" % self.o.destination)

        self.recursive = True
        self.connected = True

        return True

    # delete
    def delete(self, path):
        logger.debug("sr_file rm %s" % path)
        os.unlink(path)

    # get
    def get(self,
            msg,
            remote_file,
            local_file,
            remote_offset=0,
            local_offset=0,
            length=0):

        # open local file
        if (remote_file[0] != os.sep) and self.cwd:
            remote_path = self.cwd + os.sep + remote_file
        else:
            remote_path = remote_file

        #logger.debug( "get %s %s (cwd: %s) %d" % (remote_path,local_file,os.getcwd(), local_offset))

        if not os.path.exists( remote_path ):
           logger.warning( "file to read not found %s" % (remote_path) )
           return 0

        src = self.local_read_open(remote_path, remote_offset)
        dst = self.local_write_open(local_file, local_offset)

        # initialize sumalgo
        if self.sumalgo: self.sumalgo.set_path(remote_file)

        # download
        rw_length = self.read_write(src, dst, length)

        # close
        self.local_write_close(dst)

        return rw_length

    def getAccelerated(self, msg, remote_file, local_file, length=0):

        base_url = msg['baseUrl'].replace('file:', '')
        if base_url[-1] == '/':
            base_url = base_url[0:-1]
        arg1 = base_url + self.cwd + os.sep + remote_file
        arg1 = arg1.replace(' ', '\ ')
        arg2 = local_file

        cmd = self.o.accel_cp_command.replace( '%s', arg1 ) 
        cmd = cmd.replace( '%d', arg2 ).split()

        logger.info("accel_cp:  %s" % ' '.join(cmd))
        p = subprocess.Popen(cmd)
        p.wait()
        if p.returncode != 0:
            return -1
        sz = os.stat(arg2).st_size
        return sz


    def getcwd(self):
        return os.getcwd()

    # ls
    def ls(self):
        logger.debug("sr_file ls")
        self.entries = {}
        self.root = self.path
        self.ls_python(self.path)
        return self.entries

    def ls_python(self, dpath):
        for x in os.listdir(dpath):
            dst = dpath + '/' + x
            if os.path.isdir(dst):
                if self.recursive: self.ls_python(dst)
                continue
            relpath = dst.replace(self.root, '', 1)
            if relpath[0] == '/': relpath = relpath[1:]

            lstat = os.stat(dst)
            line = stat.filemode(lstat.st_mode)
            line += ' %d %d %d' % (lstat.st_nlink, lstat.st_uid, lstat.st_gid)
            line += ' %d' % lstat.st_size
            line += ' %s' % time.strftime("%b %d %H:%M",
                                          time.localtime(lstat.st_mtime))
            line += ' %s' % relpath
            self.entries[relpath] = line


# file_insert
# called by file_process (general file:// processing)


def file_insert(options, msg):
    logger.debug("file_insert")

    fp = open(msg['relPath'], 'rb')
    if msg.partflg == 'i': fp.seek(msg['offset'], 0)

    ok = file_write_length(fp, msg, options.bufsize, msg.filesize, options)

    fp.close()

    return ok


# file_insert_part
# called by file_reassemble : rebuiding file from parts
#
# when inserting, anything that goes wrong means that
# another process is working with this part_file
# so errors are ignored silently
#
# Returns True if the file has been fully assembled, otherwise False


def file_insert_part(options, msg, part_file):
    logger.debug("file_insert_part %s" % part_file)
    chk = msg.sumalgo
    try:
        # file disappeared ...
        # probably inserted by another process in parallel
        if not os.path.isfile(part_file):
            logger.dedbug("file doesn't exist %s" % part_file)
            return False

        # file with wrong size
        # probably being written now by another process in parallel
        lstat = os.stat(part_file)
        fsiz = lstat[stat.ST_SIZE]
        if fsiz != msg['length']:
            logger.debug("file not complete yet %s %d %d" %
                         (part_file, fsiz, msg['length']))
            return False

        # proceed with insertion
        fp = open(part_file, 'rb')
        ft = open(msg['target_file'], 'r+b')
        ft.seek(msg['offset'], 0)

        # no worry with length, read all of part_file
        # compute onfly_checksum ...
        bufsize = options.bufsize
        if bufsize > msg['length']: bufsize = msg['length']
        if chk: chk.set_path(os.path.basename(msg['target_file']))

        i = 0
        while i < msg['length']:
            buf = fp.read(bufsize)
            if not buf: break
            ft.write(buf)
            if chk: chk.update(buf)
            i += len(buf)

        if ft.tell() >= msg.filesize:
            ft.truncate()

        ft.close()
        fp.close()

        if i != msg['length']:
            logger.error("file_insert_part file currupted %s" % part_file)
            logger.error("read up to  %d of %d " % (i, msg['length']))
            lstat = os.stat(part_file)
            fsiz = lstat[stat.ST_SIZE]
            logger.error("part filesize  %d " % (fsiz))

        # set checksum in msg
        if chk:
            msg.onfly_checksum = "{},{}".format(chk.registered_as(),
                                                chk.get_value())

    # oops something went wrong
    except:
        logger.info("sr_file/file_insert_part: did not insert %s " % part_file)
        logger.debug('Exception details: ', exc_info=True)
        return False

    # success: log insertion

    # publish now, if needed, that it is inserted

    # FIXME: Need to figure out when/how to further post messages about the partitions
    #if msg.publisher :
    #   msg.set_topic('v02.post',msg.target_relpath)
    #   if chk :
    #      if    msg.sumflg == 'z' :
    #            msg.set_sum(msg.checksum,msg.onfly_checksum)
    #      else: msg.set_sum(msg.sumflg,  msg.onfly_checksum)
    #
    #   options.__on_post__()
    return True


# file_link
# called by file_process (general file:// processing)


def file_link(msg):

    try:
        os.unlink(msg['new_file'])
    except:
        pass
    try:
        os.link(msg['relPath'], msg['new_file'])
    except:
        return False

    msg.compute_local_checksum()
    msg.onfly_checksum = "{},{}".format(msg.sumflg, msg.local_checksum)

    return True


# file_process (general file:// processing)


def file_process(options):
    logger.debug("file_process")

    msg = options.msg

    # FIXME - MG - DOMINIC's LOCAL FILE MIRRORING BUG CASE
    # say file.txt does not exist
    # sequential commands in script
    # touch file.txt
    # mv file.txt newfile.txt
    # under libsrshim generate 3 amqp messages :
    # 1- download/copy file.txt
    # 2- move message 1 :  remove file.txt with newname newfile.txt
    # 3- move message 2 :  download newfile.txt with oldname file.txt
    # message (1) will never be processed fast enough ... and will fail
    # message (2) removing of a file not there is considered successfull
    # message (3) is the one that will guaranty the the newfile.txt is there and mirroring is ok.
    #
    # message (1) fails.. in previous version a bug was preventing an error (and causing file.txt rebirth with size 0)
    # In current version, returning that this message fails would put it under the retry process for ever and for nothing.
    # I decided for the moment to warn and to return success... it preserves old behavior without the 0 byte file generated

    if not os.path.isfile(msg['relPath']):
        logger.warning("%s moved or removed since announced" % msg['relPath'])
        return True

    try:
        curdir = os.getcwd()
    except:
        curdir = None

    if curdir != options.msg['new_dir']:
        os.chdir(options.msg['new_dir'])

    # try link if no inserts

    if msg.partflg == '1' or \
       (msg.partflg == 'p' and  msg.in_partfile) :
        ok = file_link(msg)
        if ok:
            if options.delete:
                try:
                    os.unlink(msg['relPath'])
                except:
                    logger.error("delete of link to %s failed" %
                                 (msg['relPath']))
            return ok

    # This part is for 2 reasons : insert part
    # or copy file if preceeding link did not work
    try:
        ok = file_insert(options, msg)
        if options.delete:
            if msg.partflg.startswith('i'):
                logger.info("delete unimplemented for in-place part files %s" %
                            (msg['relPath']))
            else:
                try:
                    os.unlink(msg['relPath'])
                except:
                    logger.error("delete of %s after copy failed" %
                                 (msg['relPath']))

        if ok: return ok

    except:
        logger.error('sr_file/file_process error')
        logger.debug('Exception details: ', exc_info=True)

    logger.error("could not copy %s in %s" % (msg['relPath'], msg['new_file']))

    return False


# file_reassemble : rebuiding file from parts
# when ever a part file is processed (inserted or written in part_file)
# this module is called to try inserting any part_file left


def file_reassemble(msg, options):
    logger.debug("file_reassemble")

    if not hasattr(msg, 'target_file') or msg['target_file'] == None:
        return False

    try:
        curdir = os.getcwd()
    except:
        curdir = None

    if curdir != options.msg['new_dir']:
        os.chdir(options.msg['new_dir'])

    # target file does not exit yet... check for first partition if it's fully downloaded then create target_file

    if not os.path.isfile(msg['target_file']):
        msg['blocks']['number'] = 0
        #msg.set_parts('i',msg['blocks']['size'],msg['blocks']['count'],msg['blocks']['remainder'],msg['blocks']['number'])
        msg.set_suffix()
        part_file = msg['target_file'] + msg.suffix

        if os.path.isfile(part_file):
            lstat = os.stat(part_file)
            fsiz = lstat[stat.ST_SIZE]
            if fsiz != msg['length']:
                logger.debug("file not complete yet %s %d %d" %
                             (part_file, fsiz, msg['length']))
                return False

            # Creating empty target file because part 0 is ready to get written
            ftarget = open(msg['target_file'], 'wb')
            ftarget.close()
            logger.info('Created new target file: %s' % msg['target_file'])

        else:
            logger.debug(
                'Waiting for partition 0 or target file to begin assembling...'
            )
            return False

    # check target file size and pick starting part from that

    lstat = os.stat(msg['target_file'])
    fsiz = lstat[stat.ST_SIZE]
    i = int(fsiz / msg['blocks']['size'])

    while i < msg['blocks']['count']:

        # setting block i in message
        current_block = i
        msg['blocks']['number'] = i

        #msg.set_parts('i',msg['blocks']['size'],msg['blocks']['count'],msg['blocks']['remainder'],msg['blocks']['number'])
        msg.set_suffix()

        # set part file

        part_file = msg['target_file'] + msg.suffix
        if not os.path.isfile(part_file):
            logger.debug("part file %s not found, stop insertion" % part_file)
            # break and not return because we want to check the lastchunk processing
            break

        # check for insertion (size may have changed)

        lstat = os.stat(msg['target_file'])
        fsiz = lstat[stat.ST_SIZE]
        if msg['offset'] > fsiz:
            logger.debug(
                "part file %s not ready for insertion (fsiz %d, offset %d)" %
                (part_file, fsiz, msg['offset']))
            return False

        # insertion attempt... should work unless there is some race condition
        ok = file_insert_part(options, msg, part_file)
        if not ok: return False

        # verify the inserted portion
        if (msg.sumstr != msg.onfly_checksum):
            # Retry once
            logger.warning('Insertion did not complete properly, retrying...')
            #logger.warning('Partition\'s checksum: '+ msg.sumstr.split(',')[1]+ ' Inserted sum: '+msg.onfly_checksum)

            ok = file_insert_part(options, msg, part_file)
            if not ok: return False

        # remove inserted part file
        try:
            os.unlink(part_file)
        except:
            logger.info('Unable to delete part file: %s' % part_file)

        logger.info("Verified ingestion : block = %d of %d" %
                    (i, msg['blocks']['count']))
        i = i + 1

    # because of randomize need a better way to check if complete
    lstat = os.stat(msg['target_file'])
    fsiz = lstat[stat.ST_SIZE]

    if (fsiz == msg.filesize
        ):  # Make sure target_relpath and new_baseurl are defined...
        file_truncate(options, msg)

        partstr = '1,%d,1,0,0' % fsiz
        sumstr = compute_sumstr(options, msg['target_file'], fsiz, 0)

        msg['new_file'] = msg['target_file']
        msg.set_file(msg.target_relpath, sumstr)

        msg.headers['parts'] = partstr
        msg.headers['sum'] = sumstr

        # If sr_watch is reassembling through the plugin
        if not hasattr(options, 'inplace') or not options.inplace:
            for plugin in options.on_file_list:
                ok = plugin(options)
                if not ok: return False
        return True

    return False


# You can also find this function in sr_post but
# they have both been slightly modified to fit their context
def compute_sumstr(options, path, fsiz, i=0):
    sumstr = ''
    sumflg = options.sumflg

    if sumflg[:2] == 'z,' and len(sumflg) > 2:
        sumstr = sumflg

    else:

        if not sumflg[0] in ['0', 'd', 'n', 's', 'z']: sumflg = 'd'

        options.set_sumalgo(sumflg)
        sumalgo = options.sumalgo
        sumalgo.set_path(path)

        # compute checksum

        if sumflg in ['d', 's']:

            fp = open(path, 'rb')
            fp.seek(i)
            while i < fsiz:
                buf = fp.read(options.bufsize)
                if not buf: break
                sumalgo.update(buf)
                i += len(buf)
            fp.close()

        # setting sumstr

        checksum = sumalgo.get_value()
        sumstr = '%s,%s' % (sumflg, checksum)
    return sumstr


# file_write_length
# called by file_process->file_insert (general file:// processing)


def file_write_length(req, msg, bufsize, filesize, options):
    logger.debug("file_write_length")

    msg.onfly_checksum = None

    chk = msg.sumalgo
    logger.debug("file_write_length chk = %s" % chk)
    if chk: chk.set_path(msg['new_file'])

    # file should exists
    if not os.path.isfile(msg['new_file']):
        fp = open(msg['new_file'], 'w')
        fp.close()

    # file open read/modify binary
    fp = open(msg['new_file'], 'r+b')
    if msg.local_offset != 0: fp.seek(msg.local_offset, 0)

    nc = int(msg['length'] / bufsize)
    r = msg['length'] % bufsize

    # read/write bufsize "nc" times
    i = 0
    while i < nc:
        chunk = req.read(bufsize)
        fp.write(chunk)
        if chk: chk.update(chunk)
        i = i + 1

    # remaining
    if r > 0:
        chunk = req.read(r)
        fp.write(chunk)
        if chk: chk.update(chunk)

    if fp.tell() >= msg.filesize:
        fp.truncate()

    fp.close()

    h = options.msg.headers
    if options.preserve_mode and 'mode' in h:
        try:
            mod = int(h['mode'], base=8)
        except:
            mod = 0
        if mod > 0: os.chmod(msg['new_file'], mod)

    if options.preserve_time and 'mtime' in h and h['mtime']:
        os.utime(msg['new_file'],
                 times=(timestr2flt(h['atime']), timestr2flt(h['mtime'])))

    if chk:
        msg.onfly_checksum = "{},{}".format(chk.registered_as(),
                                            chk.get_value())

    return True


# file_truncate
# called under file_reassemble (itself and its file_insert_part)
# when inserting lastchunk, file may need to be truncated


def file_truncate(options, msg):

    # will do this when processing the last chunk
    # whenever that is

    if (not options.randomize) and (not msg.lastchunk): return

    try:
        lstat = os.stat(msg['target_file'])
        fsiz = lstat[stat.ST_SIZE]

        if fsiz > msg.filesize:
            fp = open(msg['target_file'], 'r+b')
            fp.truncate(msg.filesize)
            fp.close()

        msg['subtopic'] =  msg['relPath'].split(os.sep)[1:-1]
        #msg.set_topic(options.post_topicPrefix,msg.target_relpath)

    except:
        pass
