#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, 2008-2022
#

import sarracenia.moth
import copy


import datetime
import html.parser
import logging
import os
import paramiko

import sarracenia

if sarracenia.extras['ftppoll']['present']:
    import dateparser
    import pytz

import sarracenia.config
from sarracenia.flowcb import FlowCB
import sarracenia.transfer
import stat
import sys, time

logger = logging.getLogger(__name__)


def file_size_fix(str_value) -> int:
    try:

        factor = 1
        if str_value[-1] in 'bB': str_value = str_value[:-1]
        elif str_value[-1] in 'kK': factor = 1024
        elif str_value[-1] in 'mM': factor = 1024 * 1024
        elif str_value[-1] in 'gG': factor = 1024 * 1024 * 1024
        elif str_value[-1] in 'tT': factor = 1024 * 1024 * 1024 * 1024
        if str_value[-1].isalpha(): str_value = str_value[:-1]

        fsize = (float(str_value) + 0.5) * factor
        isize = int(fsize)

    except:
        logger.debug("bad size %s" % str_value)
        return 0

    return isize


file_type_dict = {
    'l': 0o120000,  # symbolic link
    's': 0o140000,  # socket file
    '-': 0o100000,  # regular file
    'b': 0o060000,  # block device
    'd': 0o040000,  # directory
    'c': 0o020000,  # character device
    'p': 0o010000  # fifo (named pipe)
}


def modstr2num(m) -> int:
    mode = 0
    if (m[0] == 'r'): mode += 4
    if (m[1] == 'w'): mode += 2
    if (m[2] == 'x'): mode += 1
    return mode


def filemode(self, modstr) -> int:
    mode = 0
    mode += file_type_dict[modstr[0]]
    mode += modstr2num(modstr[1:4]) << 6
    mode += modstr2num(modstr[4:7]) << 3
    mode += modstr2num(modstr[7:10])
    return mode


def fileid(self, id) -> int:
    if id.isnumeric():
        return int(id)
    else:
        return None


class Poll(FlowCB):
    """
      The Poll flow callback class implements the main logic for polling remote resources.
      the *poll* routine returns a list of messages for new files to be filtered. 

      when instantiated with options, the options honoured include:

      * pollUrl - the URL of the server to be polled.

      * post_baseURL - parameter for messages to be returned. Also used to look
        up credentials to help subscribers with retrieval.

      * masks - These are the directories at the pollUrl to poll.
        derived from the accept/reject clauses, but filtering should happen later.
        entire directories are listed at this point.

      * timezone - interpret listings from an FTP server as being in the given timezone 
        (as per `pytz <pypi.org/project/pytz>`_

      * chmod - used to identify the minimum permissions to accept for a file to
        be included in a polling result.

      * integrity_method - parameter for how to build integrity checksum for messages.
        as these are usually remote files, the default is typically "cod" (calculate on download)

      * rename - parameter used to to put in messages built to specify the rename field contents.

      * options are passed to sarracenia.Transfer classes for their use as well.


      Poll uses sarracenia.transfer (ftp, sftp, https, etc... )classes to 
      requests lists of files using those protocols using built-in logic.  

      Internally, Poll normalizes the listings received by placing them into paramiko.SFTPAttributes
      metadata records (similar to stat records) and builds a Sarracenia.Message from them.
      The *poll* routine does one pass of this, returning a list of Sarracenia.Messages.

      To customize: 

      * one can add new sarracenia.transfer protocols, each implementing the *ls* entry point
        to be compatible with this polling routine, ideally the entry point would return a
        list of paramiko.SFTPAttributes for each file in a directory listing.
        This can be used to implement polling of structured remote resources such as S3 or webdav.

      * one can deal with different formats of HTTP pages by overriding the handle_data entry point,
        as done in `nasa_mls_nrt.py <nasa_mls_nrt.py>`_ plugin 

      * for traditional file servers, the listing format should be decypherable with the built-in processing.

      * sftp file servers provide paramiko.SFTPAttributes naturally which are timezone agnostic.

      * for some FTP servers, one may need to specify the *timezone* option to override the UTC default.

      * If there are problems with date or line formats, one can sub-class poll, and override only the on_line
        routine to deal with that.


    """
    def handle_starttag(self, tag, attrs):
        for attr in attrs:
            c, n = attr
            if c == "href":
                self.myfname = n.strip().strip('\t')

    def handle_data(self, data):
        """
           routine called from html.parser to deal with a single line.
           if the line is about a file, then create a new entry for it
           with a metadata available from SFTPAttributes.

           this can be overridden by subclassing to deal with new web sites.
        """

        if self.myfname == None: return
        if self.myfname == data: return

        words = data.split()

        if len(words) != 3:
            self.myfname = None
            return

        sdate = words[0] + ' ' + words[1]
        try:
            t = time.strptime(sdate, '%d-%b-%Y %H:%M')
        except:
            t = time.strptime(sdate, '%Y-%m-%d %H:%M')
        mydate = time.strftime('%b %d %H:%M', t)

        self.mysize = file_size_fix(words[-1])

        entry = paramiko.SFTPAttributes()
        entry.st_mtime = time.mktime(t)

        if self.myfname[-1] != '/':
            entry.st_mode = 0o755
        else:
            entry.st_mode = stat.S_IFDIR | 0o755

        self.entries[self.myfname] = entry
        self.myfname = None

    def on_html_page(self, data) -> dict:
        """
           called once per directory or page of HTML, invokes html.parser, returns
           a dictionary of file entries.
        """
        self.entries = {}
        self.myfname = None

        self.parser.feed(data)
        self.parser.close()

        return self.entries

    def on_html_parser_init(self):
        # HTML Parsing stuff.
        self.parser = html.parser.HTMLParser()
        self.parser.handle_starttag = self.handle_starttag
        self.parser.handle_data = self.handle_data

    """
      HTML Parsing begine

    """

    def __init__(self, options):

        self.o = options

        # check pollUrl

        self.details = None
        if self.o.pollUrl is not None:
            ok, self.details = sarracenia.config.Config.credentials.get(
                self.o.pollUrl)

        if self.o.pollUrl is None or self.details == None:
            logger.error("pollUrl option incorrect or missing\n")
            sys.exit(1)
        
        if self.o.post_baseUrl is None:
            self.o.post_baseUrl = self.details.url.geturl()
            if self.o.post_baseUrl[-1] != '/': self.o.post_baseUrl += '/'
            if self.o.post_baseUrl.startswith('file:'):
                self.o.post_baseUrl = 'file:'
            if self.details.url.password:
                self.o.post_baseUrl = self.o.post_baseUrl.replace(
                    ':' + self.details.url.password, '')

        self.o.remoteUrl = self.o.pollUrl

        self.dest = sarracenia.transfer.Transfer.factory(
            self.details.url.scheme, self.o)

        if self.dest is None:
            logger.critical("unsupported polling protocol")

        # rebuild mask as pulls instructions
        # pulls[directory] = [mask1,mask2...]

        self.pulls = {}
        for mask in self.o.masks:
            pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask
            logger.debug(mask)
            if not maskDir in self.pulls:
                self.pulls[maskDir] = []
            self.pulls[maskDir].append(mask)

        self.on_html_parser_init()

    def cd(self, path):
        try:
            self.dest.cd(path)
            return True
        except:
            logger.warning("sr_poll/cd: could not cd to directory %s" % path)
        return False

    def filedate(self, line):

        if not sarracenia.extras['ftppoll']['present']:
           logger.error('need dateparser library to deal with polling of ftp servers, no date parsed')
           return 0

        line_split = line.split()
        file_date = line_split[5] + " " + line_split[6] + " " + line_split[7]
        current_date = datetime.datetime.now(pytz.utc)
        # case 1: the date contains '-' implies the date is in 1 string not 3 seperate ones, and H:M is also provided
        if "-" in file_date: file_date = line_split[5] + " " + line_split[6]
        standard_date_format = dateparser.parse(
            file_date,
            settings={
                'RELATIVE_BASE': datetime.datetime(current_date.year, 1, 1),
                'TIMEZONE': self.o.timezone,  #turn this into an option - should be EST for mtl
                'TO_TIMEZONE': 'UTC'
            })
        if standard_date_format is not None:
            # case 2: the year was not given, it is defaulted to 1900. Must find which year (this one or last one).
            if standard_date_format.month - current_date.month >= 6:
                standard_date_format = standard_date_format.replace(
                    year=(current_date.year - 1))
        timestamp = datetime.datetime.timestamp(standard_date_format)
        return timestamp

    def on_line(self, line) -> paramiko.SFTPAttributes:
        """
           default line processing, converts a file listing into an SFTPAttributes.
           does nothing if input is already an SFTPAttributes item, returning it unchanged.
           verifies that file is accessible (based on self.o.chmod pattern to establish minimum permissions.)
        """
        if type(line) is paramiko.SFTPAttributes:
            sftp_obj = line
        elif type(line) is str and len(line.split()) > 7:
            parts = line.split()
            sftp_obj = paramiko.SFTPAttributes()
            sftp_obj.st_mode = filemode(self,parts[0])
            sftp_obj.st_uid = fileid(self,parts[2])
            sftp_obj.st_gid = fileid(self,parts[3])
            sftp_obj.st_size = int(parts[4])
            sftp_obj.st_mtime = self.filedate(line)
            sftp_obj.filename = parts[-1]
            sftp_obj.longname = line
        if 'sftp_obj' in locals() and ((sftp_obj.st_mode
                                        & self.o.chmod) == self.o.chmod):
            return sftp_obj
        else:
            return None

    def lsdir(self):

        try:
            ls = self.dest.ls()

            if type(ls) is bytes:
                ls = self.on_html_page(ls.decode('utf-8'))

            new_ls = {}
            new_dir = {}
            # del ls['']  # For some reason with FTP the first line of the ls causes an index out of bounds error becuase it contains only "total ..." in line_mode.py

            # apply selection on the list

            for f in ls:
                matched = False
                line = ls[f]

                line = self.on_line(line)
                if (line is None) or (line == ""):
                    continue
                if stat.S_ISDIR(line.st_mode):
                    new_dir[f] = line
                else:
                    new_ls[f] = line

            return True, new_ls, new_dir
        except Exception as e:
            logger.warning("dest.lsdir: Could not ls directory")
            logger.debug("Exception details:", exc_info=True)

        return False, {}, {}

    def poll_directory(self, pdir, lspath):
        #logger.debug("poll_directory %s %s" % (pdir, lspath))
        npost = 0
        msgs = []

        # cd to that directory

        logger.debug(" cd %s" % pdir)
        ok = self.cd(pdir)
        if not ok: return []

        # ls that directory

        ok, file_dict, dir_dict = self.lsdir()
        if not ok: return []

        filelst = file_dict.keys()
        desclst = file_dict

        logger.debug("poll_directory: new files found %d" % len(filelst))

        # post poll list

        msgs.extend(self.poll_list_post(pdir, desclst, filelst))

        # poll in children directory

        sdir = sorted(dir_dict.keys())
        for d in sdir:
            if d == '.' or d == '..': continue

            d_lspath = lspath + '_' + d
            d_pdir = pdir + os.sep + d

            msgs.extend(self.poll_directory(d_pdir, d_lspath))

        return msgs

    def poll_file_post(self, desc, destDir, remote_file):

        FileOption = None
        for mask in self.pulllst:
            pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask
            if mask_regexp.match(remote_file) and accepting:
                FileOption = maskFileOption

        path = destDir + '/' + remote_file

        # posting a localfile
        if self.o.post_baseUrl.startswith('file:'):
            if os.path.isfile(path) or os.path.islink(path):
                try:
                    lstat = sarracenia.stat(path)
                except:
                    lstat = None

                ok = sarracenia.Message.fromFileInfo(path, self.o, lstat)
                if os.path.islink(path):
                    if 'size' in msg:
                        del msg['size']
                    if not self.o.follow_symlinks:
                        try: 
                            ok['fileOp'] = { 'link': os.readlink(path) } 
                            if 'Integrity' in msg:
                                 del ok['Integrity']
                        except:
                            logger.error("cannot read link %s message dropped" % path)
                            logger.debug('Exception details: ', exc_info=True)
                            ok=None
                return ok

        post_relPath = destDir + '/' + remote_file

        logger.debug('desc: type: %s, value: %s' % (type(desc), desc))

        if type(desc) == str:
            line = desc.split()
            st = paramiko.SFTPAttributes()
            st.st_size = int(line[4])
            # actionally only need to convert normalized time to number here...
            # just being lazy...
            lstime = dateparser.parse(line[5] + " " + line[6]).timestamp()
            st.st_mtime = lstime
            st.st_atime = lstime

            desc = st

        msg = sarracenia.Message.fromFileInfo(post_relPath, self.o, desc)

        if stat.S_ISLNK(desc.st_mode):
            if not self.o.follow_symlinks:
                try: 
                    msg['fileOp'] = { 'link': self.dest.readlink(path) }
                except:
                    logger.error("cannot read link %s message dropped" % post_relPath)
                    logger.debug('Exception details: ', exc_info=True)
                    return None

        if self.o.integrity_method and (',' in self.o.integrity_method):
            m, v = self.o.integrity_method.split(',')
            msg['integrity'] = {'method': m, 'value': v}

        # If there is a file operation, and it isn't a rename, then some fields are irrelevant/wrong.
        if 'fileOp' in msg and 'rename' not in msg['fileOp']: 
            if 'Integrity' in msg:
                del msg['Integrity']
            if 'size' in msg:
                del msg['size']

        this_rename = self.o.rename

        # FIX ME generalized fileOption
        if FileOption is not None:
            parts = FileOption.split('=')
            option = parts[0].strip()
            if option == 'rename' and len(parts) == 2:
                this_rename = parts[1].strip()

        if this_rename is not None and this_rename[-1] == '/':
            this_rename += remote_file

        if this_rename is not None:
            msg['rename'] = this_rename

        return [msg]

    def poll_list_post(self, destDir, desclst, filelst):

        n = 0
        msgs = []

        for idx, remote_file in enumerate(filelst):
            desc = desclst[remote_file]
 
            new_msgs = self.poll_file_post(desc, destDir, remote_file)
            if new_msgs:
                msgs.extend(new_msgs)
        return msgs

    # =============
    # for all directories, get urls to post
    # if True is returned it means : no sleep, retry on return
    # False means, go to sleep and retry after sleep seconds
    # =============

    def poll(self) -> list:

        # General Attributes

        self.pulllst = []

        msgs = []
        # number of post files

        npost = 0

        # connection did not work

        try:
            self.dest.connect()
        except:
            logger.error("sr_poll/post_new_url: unable to connect to %s" %
                         self.o.pollUrl)
            logger.debug('Exception details: ', exc_info=True)
            logger.error("Sleeping 30 secs and retry")
            time.sleep(30)
            return []

        # loop on all directories where there are pulls to do

        for destDir in self.pulls:

            # setup of poll directory info

            self.pulllst = self.pulls[destDir]

            path = destDir
            path = path.replace('${', '')
            path = path.replace('}', '')
            path = path.replace('/', '_')
            lsPath = self.o.cfg_run_dir + os.sep + 'ls' + path

            currentDir = self.o.variableExpansion(destDir)

            if currentDir == '': currentDir = destDir
            msgs.extend(self.poll_directory(currentDir, lsPath))
            logger.debug('poll_directory returned: %s' % len(msgs))

        # close connection

        try:
            self.dest.close()
        except:
            pass

        return msgs
