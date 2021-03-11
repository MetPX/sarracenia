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
# sr_sftp.py : python3 utility tools for sftp usage in sarracenia
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Nov 23 21:08:09 UTC 2017
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

import logging, paramiko, os, subprocess, sys, time
from paramiko import *
from stat import *

from sarracenia.transfer import Transfer
from sarracenia.transfer import alarm_cancel, alarm_set, alarm_raise

import logging

logger = logging.getLogger(__name__)

#============================================================
# sftp protocol in sarracenia supports/uses :
#
# connect
# close
#
# if a source    : get    (remote,local)
#                  ls     ()
#                  cd     (dir)
#                  delete (path)
#
# if a sender    : put    (local,remote)
#                  cd     (dir)
#                  mkdir  (dir)
#                  umask  ()
#                  chmod  (perm)
#                  rename (old,new)
#
# SFTP : supports remote file seek... so 'I' part possible
#
#
# require
#           options.credentials
#           options.destination
#           options.batch
#           options.chmod
#           options.chmod_dir
#     opt   options.kbytes_ps
#     opt   options.bufsize


class Sftp(Transfer):
    def __init__(self, proto, options):

        super().__init__(proto, options)

        logger.debug("sr_sftp __init__")

        self.o.add_option("accel_scp_command", "str", "/usr/bin/scp %s %d")
        # sftp command times out after 20 secs
        # this setting is different from the computed timeout (protocol)

        self.connected = False
        self.sftp = None
        self.ssh = None
        self.seek = True

        self.batch = 0
        self.connected = False
        self.ssh_config = None

        try:
            self.ssh_config = paramiko.SSHConfig()
            ssh_config = os.path.expanduser('~/.ssh/config')
            if os.path.isfile(ssh_config):
                fp = open(ssh_config, 'r')
                self.ssh_config.parse(fp)
                fp.close()
        except:
            logger.error("sr_sftp/__init__: unable to load ssh config %s" %
                         ssh_config)
            logger.debug('Exception details: ', exc_info=True)

    def registered_as():
        return ['sftp', 'scp', 'ssh', 'fish']

    # cd
    def cd(self, path):
        logger.debug("sr_sftp cd %s" % path)
        alarm_set(self.o.timeout)
        self.sftp.chdir(self.originalDir)
        self.sftp.chdir(path)
        self.pwd = path
        alarm_cancel()

    # cd forced
    def cd_forced(self, perm, path):
        logger.debug("sr_sftp cd_forced %d %s" % (perm, path))

        # try to go directly to path

        alarm_set(self.o.timeout)
        self.sftp.chdir(self.originalDir)
        try:
            self.sftp.chdir(path)
            alarm_cancel()
            return
        except:
            pass
        alarm_cancel()

        # need to create subdir

        subdirs = path.split("/")
        if path[0:1] == "/": subdirs[0] = "/" + subdirs[0]

        for d in subdirs:
            if d == '': continue
            # try to go directly to subdir
            try:
                alarm_set(self.o.timeout)
                self.sftp.chdir(d)
                alarm_cancel()
                continue
            except:
                pass

            # create and go to subdir
            alarm_set(self.o.timeout)
            self.sftp.mkdir(d, self.o.chmod_dir)
            self.sftp.chdir(d)
            alarm_cancel()

    def check_is_connected(self):
        logger.debug("sr_sftp check_is_connected")

        if self.sftp == None: return False
        if not self.connected: return False

        if self.destination != self.o.destination:
            self.close()
            return False

        self.batch = self.batch + 1
        if self.batch > self.o.batch:
            self.close()
            return False

        # really connected, getcwd would not work, send_ignore would not work... so chdir used
        try:
            alarm_set(self.o.timeout)
            self.sftp.chdir(self.originalDir)
            alarm_cancel()
        except:
            self.close()
            return False

        return True

    # chmod
    def chmod(self, perm, path):
        logger.debug("sr_sftp chmod %s %s" % ("{0:o}".format(perm), path))
        alarm_set(self.o.timeout)
        self.sftp.chmod(path, perm)
        alarm_cancel()

    # close
    def close(self):
        logger.debug("sr_sftp close")

        old_sftp = self.sftp
        old_ssh = self.ssh

        self.init()

        alarm_set(self.o.timeout)
        try:
            old_sftp.close()
        except:
            pass
        try:
            old_ssh.close()
        except:
            pass
        alarm_cancel()

    # connect...
    def connect(self):

        logger.debug("sr_sftp connect %s" % self.o.destination)

        if self.connected: self.close()

        self.connected = False
        self.destination = self.o.destination

        if not self.credentials(): return False

        alarm_set(self.o.timeout)
        try:

            sublogger = logging.getLogger('paramiko')
            sublogger.setLevel(logging.CRITICAL)
            self.ssh = paramiko.SSHClient()
            # FIXME this should be an option... for security reasons... not forced
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.password:
                self.ssh.connect(self.host,self.port,self.user,self.password, \
                                 pkey=None,key_filename=self.ssh_keyfile,\
                                 timeout=self.o.timeout,allow_agent=False,look_for_keys=False)
            else:
                self.ssh.connect(self.host,self.port,self.user,self.password, \
                                 pkey=None,key_filename=self.ssh_keyfile,\
                                 timeout=self.o.timeout)
            #if ssh_keyfile != None :
            #  key=DSSKey.from_private_key_file(ssh_keyfile,password=None)

            sftp = self.ssh.open_sftp()
            if self.o.timeout != None:
                logger.debug("sr_sftp connect setting timeout %f" %
                             self.o.timeout)
                channel = sftp.get_channel()
                channel.settimeout(self.o.timeout)

            sftp.chdir('.')
            self.originalDir = sftp.getcwd()
            self.pwd = self.originalDir

            self.connected = True
            self.sftp = sftp

            # FIXME #367 index cache init should only happen when polling, not sender.
            self.file_index_cache = self.o.cfg_run_dir + os.sep + '.dest_file_index'
            if os.path.isfile(self.file_index_cache): self.load_file_index()
            else: self.init_file_index()

            #alarm_cancel()
            return True

        except:
            logger.error("sr_sftp/connect: unable to connect to %s (user:%s)" %
                         (self.host, self.user))
            logger.debug('Exception details: ', exc_info=True)

        alarm_cancel()
        return False

    # credentials...
    def credentials(self):
        logger.debug("sr_sftp credentials %s" % self.destination)

        try:
            ok, details = self.o.credentials.get(self.destination)
            if details: url = details.url

            self.host = url.hostname
            self.port = url.port
            self.user = url.username
            self.password = url.password
            self.ssh_keyfile = details.ssh_keyfile

            if url.username == '': self.user = None
            if url.password == '': self.password = None
            if url.port == '': self.port = None
            if self.ssh_keyfile: self.password = None

            if self.port == None: self.port = 22

            logger.debug("h u:p s = %s:%d %s:%s %s" %
                         (self.host, self.port, self.user, self.password,
                          self.ssh_keyfile))

            if self.ssh_config == None: return True

            if self.user        == None or \
             ( self.ssh_keyfile == None and self.password == None):
                logger.debug("check in ssh_config")
                for key, value in self.ssh_config.lookup(self.host).items():
                    if key == "hostname":
                        self.host = value
                    elif key == "user":
                        self.user = value
                    elif key == "port":
                        self.port = int(value)
                    elif key == "identityfile":
                        self.ssh_keyfile = os.path.expanduser(value[0])

            logger.debug("h u:p s = %s:%d %s:%s %s" %
                         (self.host, self.port, self.user, self.password,
                          self.ssh_keyfile))
            return True

        except:
            logger.error(
                "sr_sftp/credentials: unable to get credentials for %s" %
                self.destination)
            logger.debug('Exception details: ', exc_info=True)

        return False

    # delete
    # MG sneak rmdir here in case 'R' message implies a directory (remote mirroring)
    def delete(self, path):
        logger.debug("sr_sftp rm %s" % path)

        alarm_set(self.o.timeout)
        # check if the file is there... if not we are done,no error
        try:
            s = self.sftp.lstat(path)
        except:
            alarm_cancel()
            return

        # proceed with file/link removal
        if not S_ISDIR(s.st_mode):
            logger.debug("sr_sftp remove %s" % path)
            self.sftp.remove(path)

        # proceed with directory removal
        else:
            logger.debug("sr_sftp rmdir %s" % path)
            self.sftp.rmdir(path)

        alarm_cancel()

    # symlink
    def symlink(self, link, path):
        logger.debug("sr_sftp symlink %s %s" % (link, path))
        alarm_set(self.o.timeout)
        self.sftp.symlink(link, path)
        alarm_cancel()

    # get

    def get(self,
            msg,
            remote_file,
            local_file,
            remote_offset=0,
            local_offset=0,
            length=0):
        logger.debug(
            "sr_sftp get %s %s %d %d %d" %
            (remote_file, local_file, remote_offset, local_offset, length))

        alarm_set(2 * self.o.timeout)
        rfp = self.sftp.file(remote_file, 'rb', self.o.bufsize)
        if remote_offset != 0: rfp.seek(remote_offset, 0)
        rfp.settimeout(1.0 * self.o.timeout)
        alarm_cancel()

        # read from rfp and write to local_file

        rw_length = self.read_writelocal(remote_file, rfp, local_file,
                                         local_offset, length)

        # close

        alarm_set(self.o.timeout)
        rfp.close()
        alarm_cancel()

        return rw_length

    def getAccelerated(self, msg, remote_file, local_file, length=0):

        base_url = msg['baseUrl'].replace('sftp://', '')
        if base_url[-1] == '/':
            base_url = base_url[0:-1]
        arg1 = base_url + ':' + self.pwd + os.sep + remote_file
        arg1 = arg1.replace(' ', '\ ')
        arg2 = local_file

        cmd = self.o.accel_scp_command.replace( '%s', arg1 )
        cmd = cmd.replace( '%d', arg2 ).split()
        logger.info("accel_sftp:  %s" % ' '.join(cmd))
        p = subprocess.Popen(cmd)
        p.wait()
        if p.returncode != 0:
            return -1
        sz = os.stat(arg2).st_size
        return sz

    # getcwd
    def getcwd(self):
        alarm_set(self.o.timeout)
        cwd = self.sftp.getcwd() if self.sftp else None
        alarm_cancel()
        return cwd

    # init_file_index
    def init_file_index(self):
        logger.debug("sr_sftp init_file_index")
        dir_fils = self.sftp.listdir()
        logger.debug("sr_sftp listdir(): %s" % dir_fils)
        if dir_fils:
            dir_attr = self.sftp.listdir_attr()
            alarm_cancel()
            for index in range(len(dir_fils)):
                attr = dir_attr[index]
                line = attr.__str__()
                fil = dir_fils[index]
                self.ls_file_index(fil, line)
        else:
            alarm_cancel()
        if hasattr(self, 'file_index'): self.write_file_index()

    # load_file_index
    def load_file_index(self):
        logger.debug("sr_sftp load_file_index")
        alarm_cancel()
        try:
            with open(self.file_index_cache, 'r') as fp:
                index = int(fp.read())
                self.file_index = index
        except:
            logger.error(
                "load_file_index: Unable to determine file index from %s" %
                self.file_index_cache)

    # ls
    def ls(self):
        logger.debug("sr_sftp ls")
        self.entries = {}
        # timeout is at least 30 secs, say we wait for max 5 mins
        alarm_set(self.o.timeout)
        dir_attr = self.sftp.listdir_attr()
        alarm_cancel()
        for index in range(len(dir_attr)):
            attr = dir_attr[index]
            line = attr.__str__()
            self.line_callback(line)
        #logger.debug("sr_sftp ls = %s" % self.entries )
        return self.entries

    # line_callback: ls[filename] = 'stripped_file_description'
    def line_callback(self, iline):
        #logger.debug("sr_sftp line_callback %s" % iline)

        oline = iline
        oline = oline.strip('\n')
        oline = oline.strip()
        oline = oline.replace('\t', ' ')
        opart1 = oline.split(' ')
        opart2 = []

        for p in opart1:
            if p == '': continue
            opart2.append(p)
        # else case is in the event of unlikely race condition
        if hasattr(self, 'file_index'):
            fil = ' '.join(opart2[self.file_index:])
        else:
            fil = ' '.join(opart2[8:])
        # next line is for backwards compatibility only
        # FIXME: 2020/08/01 caused error, so removed during v3 port.
        #if not self.o.ls_file_index in [-1,len(opart2)-1] : fil =  ' '.join(opart2[self.o.ls_file_index:])
        line = ' '.join(opart2)

        self.entries[fil] = line

    # ls_file_index
    def ls_file_index(self, ifil, iline):
        oline = iline
        oline = oline.strip('\n')
        oline = oline.strip()
        oline = oline.replace('\t', ' ')
        opart1 = oline.split(' ')
        opart2 = []

        for p in opart1:
            if p == '': continue
            opart2.append(p)

        try:
            file_index = opart2.index(ifil)
            self.file_index = file_index
        except:
            pass

    # mkdir
    def mkdir(self, remote_dir):
        logger.debug("sr_sftp mkdir %s" % remote_dir)
        alarm_set(self.o.timeout)
        self.sftp.mkdir(remote_dir, self.o.chmod_dir)
        alarm_cancel()

    # put
    def put(self,
            msg,
            local_file,
            remote_file,
            local_offset=0,
            remote_offset=0,
            length=0):
        logger.debug(
            "sr_sftp put %s %s %d %d %d" %
            (local_file, remote_file, local_offset, remote_offset, length))

        # simple file

        alarm_set(2 * self.o.timeout)

        if length == 0:
            rfp = self.sftp.file(remote_file, 'wb', self.o.bufsize)
            rfp.settimeout(1.0 * self.o.timeout)

        # parts
        else:
            try:
                self.sftp.stat(remote_file)
            except:
                rfp = self.sftp.file(remote_file, 'wb', self.o.bufsize)
                rfp.close()

            rfp = self.sftp.file(remote_file, 'r+b', self.o.bufsize)
            rfp.settimeout(1.0 * self.o.timeout)
            if remote_offset != 0: rfp.seek(remote_offset, 0)

        alarm_cancel()

        # read from local_file and write to rfp

        rw_length = self.readlocal_write(local_file, local_offset, length, rfp)

        # no sparse file... truncate where we are at

        alarm_set(self.o.timeout)
        self.fpos = remote_offset + rw_length
        if length != 0: rfp.truncate(self.fpos)
        rfp.close()
        alarm_cancel()

        return rw_length

    def putAccelerated(self, msg, local_file, remote_file, length=0):

        dest_baseUrl = self.o.destination.replace('sftp://', '')
        if dest_baseUrl[-1] == '/':
            dest_baseUrl = dest_baseUrl[0:-1]
        arg2 = dest_baseUrl + ':' + msg['new_dir'] + os.sep + remote_file
        arg2 = arg2.replace(' ', '\ ')
        arg1 = local_file

        cmd = self.o.accel_scp_command.replace( '%s', arg1 )
        cmd = cmd.replace( '%d', arg2 ).split()

        logger.info("accel_sftp:  %s" % ' '.join(cmd))
        p = subprocess.Popen(cmd)
        p.wait()
        if p.returncode != 0:
            return -1
        # FIXME: faking success... not sure how to check really.
        sz = int(msg['size'])
        return sz

    # rename
    def rename(self, remote_old, remote_new):
        logger.debug("sr_sftp rename %s %s" % (remote_old, remote_new))
        try:
            self.delete(remote_new)
        except:
            pass
        alarm_set(self.o.timeout)
        self.sftp.rename(remote_old, remote_new)
        alarm_cancel()

    # rmdir
    def rmdir(self, path):
        logger.debug("sr_sftp rmdir %s " % path)
        alarm_set(self.o.timeout)
        self.sftp.rmdir(path)
        alarm_cancel()

    # utime
    def utime(self, path, tup):
        logger.debug("sr_sftp utime %s %s " % (path, tup))
        alarm_set(self.o.timeout)
        self.sftp.utime(path, tup)
        alarm_cancel()

    # write_file_index
    def write_file_index(self):
        logger.debug("sr_sftp write_file_index")
        try:
            with open(self.file_index_cache, 'w') as fp:
                fp.write(str(self.file_index))
        except:
            logger.warning("Unable to write file_index to cache file %s" %
                           self.file_index_cache)
