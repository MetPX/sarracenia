# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, 2008-2021
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

import ftplib, os, subprocess, sys, time, ssl
import logging
from sarracenia.transfer import Transfer
from sarracenia.transfer import alarm_cancel, alarm_set, alarm_raise
from urllib.parse import unquote

logger = logging.getLogger(__name__)

class IMPLICIT_FTP_TLS(ftplib.FTP_TLS):
    """ FTP_TLS subclass that automatically wraps sockets in SSL to support implicit FTPS.
        Copied from https://stackoverflow.com/questions/12164470/python-ftp-implicit-tls-connection-issue
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sock = None

    @property
    def sock(self):
        """Return the socket."""
        return self._sock

    @sock.setter
    def sock(self, value):
        """When modifying the socket, ensure that it is ssl wrapped."""
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value)
        self._sock = value

class Ftp(Transfer):
    """
    File Transfer Protocol (FTP)  ( https://datatracker.ietf.org/doc/html/rfc959 )
    sarracenia transfer protocol subclass supports/uses additional custom options:

    * accelFtpputCommand (default: '/usr/bin/ncftpput %s %d' )
    * accelFtpgetCommand (default: '/usr/bin/ncftpget %s %d' )

    built using: ftplib ( https://docs.python.org/3/library/ftplib.html )
    """
    def __init__(self, proto, options):

        super().__init__(proto, options)

        self.o.add_option('accelFtpputCommand', 'str',
                          '/usr/bin/ncftpput %s %d')
        self.o.add_option('accelFtpgetCommand', 'str',
                          '/usr/bin/ncftpget %s %d')

        self.o.add_option('ftpFilenameEncoding', 'str', 'utf-8' )

        logger.debug("sr_ftp __init__")
        self.connected = False
        self.ftp = None
        self.details = None
        self.batch = 0

    def registered_as():
        return ['ftp']

    # cd
    def cd(self, path):
        logger.debug("sr_ftp cd %s" % path)

        alarm_set(self.o.timeout)
        try:
            self.ftp.cwd(self.originalDir)
            self.ftp.cwd(path)
            self.pwd = path
        finally:
            alarm_cancel()

    def cd_forced(self, path):
        logger.debug("sr_ftp cd_forced %o %s" % (self.o.permDirDefault, path))

        # try to go directly to path

        alarm_set(self.o.timeout)
        try:
            self.ftp.cwd(self.originalDir)
            self.ftp.cwd(path)
            return
        except:
            pass
        finally:
            alarm_cancel()

        # need to create subdir

        subdirs = path.split("/")
        if path[0:1] == "/": subdirs[0] = "/" + subdirs[0]

        for d in subdirs:
            if d == '': continue
            # try to go directly to subdir
            try:
                alarm_set(self.o.timeout)
                self.ftp.cwd(d)
                continue
            except:
                pass
            finally:
                alarm_cancel()

            # create
            alarm_set(self.o.timeout)
            try:
                self.ftp.mkd(d)
            finally:
                alarm_cancel()

            # chmod
            alarm_set(self.o.timeout)
            try:
                self.ftp.voidcmd('SITE CHMOD ' + "{0:o}".format(self.o.permDirDefault) + ' ' + d)
            finally:
                alarm_cancel()

            # cd
            alarm_set(self.o.timeout)
            try:
                self.ftp.cwd(d)
            finally:
                alarm_cancel()

    # check_is_connected

    def check_is_connected(self):
        logger.debug("sr_ftp check_is_connected")

        if self.ftp == None: return False
        if not self.connected: return False

        if self.sendTo != self.o.sendTo:
            self.close()
            return False

        self.batch = self.batch + 1
        if self.batch > self.o.batch:
            self.close()
            return False

        # really connected
        try:
            cwd = self.getcwd()
        except:
            self.close()
            return False

        return True

    # chmod
    def chmod(self, perm, path):
        logger.debug("sr_ftp chmod %s %s" % (str(perm), path))
        alarm_set(self.o.timeout)
        try:
            self.ftp.voidcmd('SITE CHMOD ' + "{0:o}".format(perm) + ' ' + path)
        finally:
            alarm_cancel()

    # close
    def close(self):
        logger.debug("sr_ftp close")

        old_ftp = self.ftp

        self.init()
        alarm_set(self.o.timeout)

        try:
            old_ftp.quit()
        except:
            pass
        alarm_cancel()

    # connect...
    def connect(self):
        logger.debug("sr_ftp connect %s" % self.o.sendTo)

        self.connected = False
        self.sendTo = self.o.sendTo

        if not self.credentials(): return False

        # timeout alarm 100 secs to connect
        alarm_set(self.o.timeout)

        try:
            expire = -999
            if self.o.timeout: expire = self.o.timeout
            if self.port == '' or self.port == None: 
                if self.implicit_ftps:
                    self.port = 990
                else:
                    self.port = 21

            # plain FTP with no encryption (usually port 21)
            if not self.tls:
                ftp = ftplib.FTP()
                ftp.encoding = 'utf-8'
                ftp.connect(self.host, self.port, timeout=expire)
                ftp.login(self.user, unquote(self.password))
            # implicit FTPS (usually port 990)
            elif self.tls and self.implicit_ftps:
                ftp = IMPLICIT_FTP_TLS()
                ftp.encoding = self.o.ftpFilenameEncoding
                ftp.connect(host=self.host, port=self.port, timeout=expire)
                ftp.login(user=self.user, passwd=unquote(self.password))
                if self.prot_p:
                    ftp.prot_p()
            # explicit FTPS (port 21)
            else:
                # ftplib supports FTPS with TLS
                ftp = ftplib.FTP_TLS(self.host,
                                     self.user,
                                     unquote(self.password),
                                     timeout=expire)
                ftp.encoding = self.o.ftpFilenameEncoding
                if self.prot_p: ftp.prot_p()
                # needed only if prot_p then set back to prot_c
                #else          : ftp.prot_c()

            ftp.set_pasv(self.passive)

            self.originalDir = '.'

            try:
                self.originalDir = ftp.pwd()
            except:
                logger.warning("Unable to ftp.pwd")
                logger.debug('Exception details: ', exc_info=True)

            self.pwd = self.originalDir
            self.connected = True
            self.ftp = ftp

        except:
            logger.error("Unable to connect to %s (user:%s)" %
                         (self.host, self.user))
            logger.debug('Exception details: ', exc_info=True)

        alarm_cancel()
        return self.connected

    # credentials...
    def credentials(self):
        logger.debug("sr_ftp credentials %s" % self.sendTo)

        try:
            ok, details = self.o.credentials.get(self.sendTo)
            if details: url = details.url

            self.host = url.hostname
            self.port = url.port
            self.user = url.username
            self.password = url.password

            self.passive = details.passive
            self.binary = details.binary
            self.tls = details.tls
            self.prot_p = details.prot_p
            self.implicit_ftps = details.implicit_ftps

            return True

        except:
            logger.error(
                "sr_ftp/credentials: unable to get credentials for %s" %
                self.sendTo)
            logger.debug('Exception details: ', exc_info=True)

        return False

    # delete
    def delete(self, path):
        logger.debug("sr_ftp rm %s" % path)
        alarm_set(self.o.timeout)
        # if delete does not work (file not found) run pwd to see if connection is ok
        try:
            self.ftp.delete(path)
        except:
            d = self.ftp.pwd()
        alarm_cancel()

    # get
    def get(self,
            msg,
            remote_file,
            local_file,
            remote_offset=0,
            local_offset=0,
            length=0, exactLength=False):
        logger.debug("sr_ftp get %s %s %d" %
                     (remote_file, local_file, local_offset))

        # open local file
        dst = self.local_write_open(local_file, local_offset)

        # initialize sumalgo
        if self.sumalgo: self.sumalgo.set_path(remote_file)

        # download
        self.write_chunk_init(dst)

        try:
            if self.binary:
                self.ftp.retrbinary('RETR ' + remote_file, self.write_chunk,
                                self.o.bufSize)
            else:
                self.ftp.retrlines('RETR ' + remote_file, self.write_chunk)
        except Exception as Ex:
            logger.error( f"failed to get {remote_file} to {local_file}: {Ex}" )

        rw_length = self.write_chunk_end()

        # close
        self.local_write_close(dst)

        return rw_length

    def getAccelerated(self, msg, remote_file, local_file, length=0, remote_offset=0, exactLength=False):

        base_url = msg['baseUrl']
        if base_url[-1] == '/':
            base_url = base_url[0:-1]
        arg1 = base_url + self.pwd + os.sep + remote_file
        arg1 = arg1.replace(' ', '\\ ')
        arg2 = local_file

        cmd = self.o.accelFtpgetCommand.replace('%s', arg1)
        cmd = cmd.replace('%d', arg2).split()

        logger.info("accel_ftp:  %s" % ' '.join(cmd))
        p = subprocess.Popen(cmd)
        p.wait()
        if p.returncode != 0:
            return -1
        sz = os.stat(arg2).st_size
        return sz

    # getcwd
    def getcwd(self):
        alarm_set(self.o.timeout)
        try:
            pwd = self.ftp.pwd()
        finally:
            alarm_cancel()

        return pwd

    # ls
    def ls(self):
        logger.debug("sr_ftp ls")
        self.entries = {}
        alarm_set(self.o.timeout)
        try:
            self.ftp.retrlines('LIST', self.line_callback)
        finally:
            alarm_cancel()

        logger.debug("sr_ftp ls = (size: %d) %s ..." % (len(self.entries), str(self.entries)[0:255]))
        return self.entries

    # line_callback: entries[filename] = 'stripped_file_description'
    def line_callback(self, iline):
        #logger.debug("sr_ftp line_callback %s" % iline)

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

        # on linux, there are 8 fields, with spaces, perhaps more...
        if len(opart2) > 7:
            # university of Wisconsin as an ftp server that has an extra auth field.
            if opart2[4].isnumeric(): # normal linux case.
                fil = ' '.join(opart2[8:])
            else:  # U. Wisconsin case.
                fil = ' '.join(opart2[9:])
        else:
            # guess it is on windows... 
            fil = ' '.join(opart2[3:])

        line = ' '.join(opart2)

        self.entries[fil] = line

    # mkdir
    def mkdir(self, remote_dir):
        logger.debug("sr_ftp mkdir %s" % remote_dir)
        alarm_set(self.o.timeout)
        try:
            self.ftp.mkd(remote_dir)
        finally:
            alarm_cancel()

        alarm_set(self.o.timeout)
        try:
            self.ftp.voidcmd('SITE CHMOD ' +
                         "{0:o}".format(self.o.permDirDefault) + ' ' +
                         remote_dir)
        finally:
            alarm_cancel()

    # put
    def put(self,
            msg,
            local_file,
            remote_file,
            local_offset=0,
            remote_offset=0,
            length=0):
        logger.debug("sr_ftp put %s %s" % (local_file, remote_file))

        # open
        src = self.local_read_open(local_file, local_offset)

        # upload
        self.write_chunk_init(None)
        try:
            if self.binary:
                self.ftp.storbinary("STOR " + remote_file, src, self.o.bufSize,
                                self.write_chunk)
            else:
                self.ftp.storlines("STOR " + remote_file, src, self.write_chunk)
        except Exception as Ex:
            logger.error( f"failed to put {remote_file} to {local_file}: {Ex}" )

        rw_length = self.write_chunk_end()

        # close
        self.local_read_close(src)

        return rw_length

    def putAccelerated(self, msg, local_file, remote_file, length=0):

        dest_baseUrl = self.o.sendTo
        if dest_baseUrl[-1] == '/':
            dest_baseUrl = dest_baseUrl[0:-1]
        arg2 = dest_baseUrl + msg['new_dir'] + os.sep + remote_file
        arg2 = arg2.replace(' ', '\\ ')
        arg1 = local_file

        cmd = self.o.accelFtpputCommand.replace('%s', arg1)
        cmd = cmd.replace('%d', arg2).split()

        logger.info("accel_ftp:  %s" % ' '.join(cmd))
        p = subprocess.Popen(cmd)
        p.wait()
        if p.returncode != 0:
            return -1
        # FIXME: faking success... not sure how to check really.
        sz = int(msg['size'])
        return sz

    # rename
    def rename(self, remote_old, remote_new):
        logger.debug("sr_ftp rename %s %s" % (remote_old, remote_new))
        alarm_set(self.o.timeout)
        try:
            self.ftp.rename(remote_old, remote_new)
        finally:
            alarm_cancel()

    # rmdir
    def rmdir(self, path):
        logger.debug("sr_ftp rmdir %s" % path)
        alarm_set(self.o.timeout)
        try:
            self.ftp.rmd(path)
        finally:
            alarm_cancel()

    # umask
    def umask(self):
        logger.debug("sr_ftp umask")
        alarm_set(self.o.timeout)
        try:
            self.ftp.voidcmd('SITE UMASK 777')
        finally:
            alarm_cancel()
