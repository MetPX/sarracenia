# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
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

import sarracenia

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
#           options.sendTo
#           options.batch
#           options.permDefault
#           options.permDirDefault
#     opt   options.byteRateMax
#     opt   options.bufSize


class File(Transfer):
    """
        Transfer sub-class for local file i/o.

    """
    def __init__(self, proto, options):
        super().__init__(proto, options)

        self.o.add_option("accelCpCommand", "str", "/usr/bin/cp %s %d")
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
        logger.debug("sr_file connect %s" % self.o.sendTo)

        self.recursive = True
        self.connected = True

        return True

    # delete
    def delete(self, path):
        p = os.path.join( self.cwd, path )
        logger.debug("sr_file rm %s" % p)
        os.unlink(p)

    # get
    def get(self,
            msg,
            remote_file,
            local_file,
            remote_offset=0,
            local_offset=0,
            length=0, exactLength=False):

        remote_path = self.cwd + os.sep + remote_file

        logger.debug( "get %s %s (cwd: %s) %d" % (remote_path,local_file,os.getcwd(), local_offset))

        if not os.path.exists(remote_path):
            logger.warning("file to read not found %s" % (remote_path))
            return -1

        src = self.local_read_open(remote_path, remote_offset)
        dst = self.local_write_open(local_file, local_offset)

        # initialize sumalgo
        if self.sumalgo: self.sumalgo.set_path(remote_file)

        # download
        rw_length = self.read_write(src, dst, length)

        # close
        self.local_write_close(dst)

        return rw_length

    def getAccelerated(self, msg, remote_file, local_file, length=0, remote_offset=0, exactLength=False):

        base_url = msg['baseUrl'].replace('file:', '')
        if base_url[-1] == '/':
            base_url = base_url[0:-1]
        arg1 = base_url + self.cwd + os.sep + remote_file
        arg1 = arg1.replace(' ', '\\ ')
        arg2 = local_file

        cmd = self.o.accelCpCommand.replace('%s', arg1)
        cmd = cmd.replace('%d', arg2).split()

        logger.info("accel_cp:  %s" % ' '.join(cmd))
        p = subprocess.Popen(cmd)
        p.wait()
        if p.returncode != 0:
            return -1
        sz = os.stat(arg2).st_size
        return sz

    def getcwd(self):
        return self.cwd

    def stat(self,path,message=None):
        spath = path if path[0] == '/' else self.path + '/' + path
        try:
             return sarracenia.stat(spath)
        except:
             return None
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

            self.entries[relpath] = sarracenia.stat(dst)


# file_insert
# called by file_process (general file:// processing)


def file_insert(options, msg):
    logger.debug("file_insert")

    fp = open(msg['relPath'], 'rb')
    if msg.partflg == 'i': fp.seek(msg['offset'], 0)

    ok = file_write_length(fp, msg, options.bufSize, msg.filesize, options)

    fp.close()

    return ok


def file_link(msg):

    try:
        os.unlink(msg['new_file'])
    except:
        pass
    try:
        os.link(msg['fileOp']['link'], os.path.join(self.cwd,msg['new_file']))
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
        curdir = self.cwd
    except:
        curdir = None

    if curdir != options.msg['new_dir']:
        os.chdir(options.msg['new_dir'])

    # try link if no inserts

    p=os.path.join(self.cwd,msg['relPath'])

    if msg.partflg == '1' or \
       (msg.partflg == 'p' and  msg.in_partfile) :
        ok = file_link(msg)
        if ok:
            if options.delete:
                try:
                    os.unlink(p)
                except:
                    logger.error("delete of link to %s failed" % p)
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
                    os.unlink(p)
                except:
                    logger.error("delete of %s after copy failed" % p)

        if ok: return ok

    except:
        logger.error('sr_file/file_process error')
        logger.debug('Exception details: ', exc_info=True)

    logger.error("could not copy %s in %s" % (p, msg['new_file']))

    return False


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
    if options.permCopy and 'mode' in h:
        try:
            mod = int(h['mode'], base=8)
        except:
            mod = 0
        if mod > 0: os.chmod(msg['new_file'], mod)

    if options.timeCopy and 'mtime' in h and h['mtime']:
        os.utime(msg['new_file'],
                 times=(timestr2flt(h['atime']), timestr2flt(h['mtime'])))

    if chk:
        msg.onfly_checksum = "{},{}".format(chk.registered_as(), chk.value)

    return True


# file_truncate
# called under file_reassemble (itself and its file_insert_part)
# when inserting lastchunk, file may need to be truncated


def file_truncate(options, msg):

    # will do this when processing the last chunk
    # whenever that is

    if (not options.randomize) and (not msg.lastchunk): return

    try:
        lstat = sarracenia.stat(msg['target_file'])
        fsiz = lstat.st_size

        if fsiz > msg.filesize:
            fp = open(msg['target_file'], 'r+b')
            fp.truncate(msg.filesize)
            fp.close()

        msg['subtopic'] = msg['relPath'].split(os.sep)[1:-1]
        msg['_deleteOnPost'] |= set(['subtopic'])
        #msg.set_topic(options.post_topicPrefix,msg.target_relpath)

    except:
        pass
