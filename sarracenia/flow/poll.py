#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, 2008-2021
#

import sarracenia.moth
import copy
import dateparser
import datetime
import logging
import os
import paramiko

import sarracenia 
import sarracenia.config
from sarracenia.flow import Flow
import sarracenia.transfer
import stat
import pytz
import sys, time



logger = logging.getLogger(__name__)

default_options = {
    'accept_unmatched': False,
    'blocksize': 1,
    'bufsize': 1024 * 1024,
    'poll_builtinGather': True,
    'chmod': 0o400,
    'destination': None,
    'follow_symlinks': False,
    'force_polling': False,
    'inflight': None,
    'integrity_method': 'cod,sha512',
    'part_ext': 'Part',
    'partflg': '1',
    'post_baseDir': None,
    'preserve_mode': True,
    'preserve_time': True,
    'randomize': False,
    'rename': None,
    'post_on_start': False,
    'sleep': -1,
    'nodupe_ttl': 7*60*60,
    'nodupe_fileAgeMax': 30*24*60*60,
}


#  'sumflg': 'cod,md5',


class Poll(Flow):
    def __init__(self, options):

        super().__init__(options)

        self.plugins['load'].append('sarracenia.flowcb.line_to_SFTPattributes.Line_To_SFTPattributes')

        if options.vip:
            self.plugins['load'].insert(0,'sarracenia.flowcb.gather.message.Message')

        self.plugins['load'].insert(0,'sarracenia.flowcb.post.message.Message')

        # check destination

        self.details = None
        if self.o.destination is not None:
            ok, self.details = sarracenia.config.Config.credentials.get(
                self.o.destination)

        if self.o.destination is None or self.details == None:
            logger.error("destination option incorrect or missing\n")
            sys.exit(1)

        if self.o.post_baseUrl is None:
            self.o.post_baseUrl = self.details.url.geturl()
            if self.o.post_baseUrl[-1] != '/': self.o.post_baseUrl += '/'
            if self.o.post_baseUrl.startswith('file:'):
                self.o.post_baseUrl = 'file:'
            if self.details.url.password:
                self.o.post_baseUrl = self.o.post_baseUrl.replace(
                    ':' + self.details.url.password, '')

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

    def cd(self, path):
        try:
            self.dest.cd(path)
            return True
        except:
            logger.warning("sr_poll/cd: could not cd to directory %s" % path)
        return False



    def gather(self):

        super().gather()

        if self.have_vip:
            if len(self.plugins['poll']) > 0:
                for plugin in self.plugins['poll']:
                     new_incoming = plugin()
            else:
                new_incoming = self.poll()

            if len(new_incoming) > 0:
                self.worklist.incoming.extend(new_incoming)
       


    def lsdir(self):
        try:
            ls = self.dest.ls()
            new_ls = {}
            new_dir = {}
            # del ls['']  # For some reason with FTP the first line of the ls causes an index out of bounds error becuase it contains only "total ..." in line_mode.py

            # apply selection on the list

            for f in ls:
                matched = False
                line = ls[f]

                if 'on_line' in self.plugins:
                    for plugin in self.plugins['on_line']:
                        line = plugin(line)
                        if (line is None) or (line == ""): break
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

        # when not sleeping
        #if not self.sleeping :
        if True:
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
            if os.path.isfile(path):
                try:
                    lstat = os.stat(path)
                except:
                    lstat = None
                ok = sarracenia.Message.fromFileInfo(path, self.o, lstat)
                return ok

        post_relPath = destDir + '/' + remote_file

        logger.debug('desc: type: %s, value: %s' % ( type(desc), desc) )

        if type(desc) == str:
            line = desc.split()
            st = paramiko.SFTPAttributes()
            st.st_size = int(line[4])
            # actionally only need to convert normalized time to number here...
            # just being lazy...
            lstime = dateparser.parse( line[5] + " " + line[6] ).timestamp()
            st.st_mtime = lstime
            st.st_atime = lstime

            desc=st

        msg = sarracenia.Message.fromFileInfo(post_relPath, self.o, desc)

        if self.o.integrity_method and (',' in self.o.integrity_method):
            m, v = self.o.integrity_method.split(',')
            msg['integrity'] = {'method': m, 'value': v}

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
            msgs.extend(self.poll_file_post(desc, destDir, remote_file))
        return msgs

    # =============
    # for all directories, get urls to post
    # if True is returned it means : no sleep, retry on return
    # False means, go to sleep and retry after sleep seconds
    # =============

    def poll(self):

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
                         self.o.destination)
            logger.debug('Exception details: ', exc_info=True)
            logger.error("Sleeping 30 secs and retry")
            time.sleep(30)
            return []

        if hasattr(self.dest, 'file_index'):
            self.dest_file_index = self.dest.file_index
        # loop on all directories where there are pulls to do

        for destDir in self.pulls:

            # setup of poll directory info

            self.pulllst = self.pulls[destDir]

            path = destDir
            path = path.replace('${', '')
            path = path.replace('}', '')
            path = path.replace('/', '_')
            lsPath = self.o.cfg_run_dir + os.sep + 'ls' + path

            currentDir = self.o.set_dir_pattern(destDir)

            if currentDir == '': currentDir = destDir
            msgs.extend(self.poll_directory(currentDir, lsPath))
            logger.debug('poll_directory returned: %s' % len(msgs))

        # close connection

        try:
            self.dest.close()
        except:
            pass

        return msgs
