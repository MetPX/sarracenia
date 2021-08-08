#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#

import sarracenia.moth
import copy
from sarracenia.flow import Flow
import logging
from sarracenia.flowcb.gather import msg_init

import sarracenia.config

import os, sys, time

import sarracenia.transfer

import datetime


logger = logging.getLogger(__name__)

default_options = {
    'accept_unmatched': False,
    'blocksize': 1,
    'bufsize': 1024 * 1024,
    'chmod': 0o400,
    'destination': None,
    'follow_symlinks': False,
    'force_polling': False,
    'inflight': None,
    'integrity_method': 'cod,md5',
    'part_ext': 'Part',
    'partflg': '1',
    'post_baseDir': None,
    'preserve_mode': True,
    'preserve_time': True,
    'randomize': False,
    'rename': None,
    'post_on_start': False,
    'sleep': -1,
    'nodupe_ttl': 0
}


#  'sumflg': 'cod,md5',


class Poll(Flow):
    def __init__(self, options):

        super().__init__(options)
        self.plugins['load'].append('sarracenia.flowcb.line_mode.Line_Mode')
        self.plugins['load'].append('sarracenia.flowcb.post.message.Message')

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


    def _file_date_within_limit(self, date, time_limit):
        """comments:
            This method compares today's date to the file's date by creating a date time object
            Three formats are acceptd so far, more can be added if needed (format on https://strftime.org/ )
            Files with future dates are processed as long as the (future date - todays date) is < time_limit.
            FIXME: french input like Fev will not work - only Feb is accepted for the month
            If year is not provided, this means that the file is < 6 months old, so depending on todays date,
                assign appropriate year (for jan-jun -> assign prev year, for jul-dec assign current year)
            Note: is it possible for a file to be more than 6 months old and have the format Mo Day TIME ? (problematic)
        """
        time_limit = int(time_limit)
        current_date = datetime.datetime.now()
        try:
            date_temp = datetime.datetime.strptime(date, '%d %b %H:%M')
            if date_temp.month - current_date.month >= 6:
                file_date = date_temp.replace(year=(current_date.year - 1))
            else:
                file_date = date_temp.replace(year=current_date.year)
            logger.debug("File date is: " + str(file_date) + " > File is " + str(abs((file_date - current_date).seconds)) + " seconds old")
            return abs((file_date - current_date).seconds) < time_limit
        except Exception as e:
            try:
                date_temp = datetime.datetime.strptime(date, '%b %d %H:%M')
                if date_temp.month - current_date.month >= 6:
                    file_date = date_temp.replace(year=(current_date.year - 1))
                else:
                    file_date = date_temp.replace(year=current_date.year)
                logger.debug("File date is: " + str(file_date) + " > File is " + str(abs((file_date - current_date).seconds)) + " seconds old")
                return abs((file_date - current_date).seconds) < time_limit
            except Exception as e:
                try:
                    file_date = datetime.datetime.strptime(date, '%b %d %Y')
                    logger.debug("File date is: " + str(file_date) + " > File is " + str(abs((file_date - current_date).seconds)) + " seconds old")
                    return abs((file_date - current_date).seconds) < time_limit
                except Exception as e:
                    warning_msg = str(e)
                    print("%s" % warning_msg)
                    return False


    # find differences between current ls and last ls
    # only the newer or modified files will be kept and the ones withing a specific time limit, default 60d


    def differ_ls_file(self, ls, lspath):

        # get new list and description

        new_lst = sorted(ls.keys())

        # get old list and description

        old_ls = self.load_ls_file(lspath)

        # compare

        filelst = []
        desclst = {}

        for f in new_lst:
            # logger.debug("checking %s (%s)" % (f, ls[f]))
            try:
                str1 = ls[f]
                str2 = str1.split()
                # specify input for this routine.
                # ls[f] format controlled by online plugin (line_mode.py)
                # this format could change depending on plugin
                # line_mode.py format "-rwxrwxr-x 1 1000 1000 8123 24 Mar 22:54 2017-03-25-0254-CL2D-AUTO-minute-swob.xml"
                date = str2[5] + " " + str2[6] + " " + str2[7]
                if self._file_date_within_limit(date, self.o.file_time_limit):
                    #logger.debug("File should be processed")

                    # execute rest of code
                    # keep a newer entry
                    if not f in old_ls:
                        # logger.debug("IS NEW %s" % f)
                        filelst.append(f)
                        desclst[f] = ls[f]
                        continue

                    # keep a modified entry
                    if ls[f] != old_ls[f]:
                        # logger.debug("IS DIFFERENT %s from (%s,%s)" %(f, old_ls[f], ls[f]))
                        filelst.append(f)
                        desclst[f] = ls[f]
                        continue
                else:
                    # ignore rest of code and re iterate
                    logger.debug("File should be skipped")
            except:
                pass
            # logger.debug("IS IDENTICAL %s" % f)

        return filelst, desclst

    def gather(self):

        if self.dest != None:
            self.worklist.incoming.extend(self.post_new_urls())
            #logger.debug('post_new_urls returned: %s' %
            #             len(self.worklist.incoming))

    def load_ls_file(self, path):
        lsold = {}

        if not os.path.isfile(path): return lsold
        try:
            file = open(path, 'r')
            lines = file.readlines()
            file.close()

            for line in lines:
                line = line.strip('\n')
                parts = line.split()
                if hasattr(self, 'dest_file_index'):
                    fil = ' '.join(parts[self.dest_file_index:])
                else:
                    fil = parts[-1]
                    if not self.ls_file_index in [-1, len(parts) - 1]:
                        fil = ' '.join(parts[self.ls_file_index:])
                lsold[fil] = line

            return lsold

        except:
            logger.error("load_ls_file: Unable to parse files from %s" % path)

        return lsold

    def lsdir(self):
        try:
            ls = self.dest.ls()
            new_ls = {}
            new_dir = {}

            # apply selection on the list

            for f in ls:
                matched = False
                line = ls[f]

                if 'on_line' in self.plugins:
                    for plugin in self.plugins['on_line']:
                        line = plugin(line)
                        if (line is None) or (line == ""): break
                    if (line is None) or (line == ""): continue

                if line[0] == 'd':
                    d = f.strip(os.sep)
                    new_dir[d] = line
                    continue

                new_ls[f] = line.strip('\n')
            return True, new_ls, new_dir
        except:
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

            # get file list from difference in ls

            filelst, desclst = self.differ_ls_file(file_dict, lspath)
            logger.debug("poll_directory: after differ, len=%d" % len(filelst))

            # post poll list

            msgs.extend(self.poll_list_post(pdir, desclst, filelst))

        # sleeping or not, write the directory file content

        ok = self.write_ls_file(file_dict, lspath)

        # poll in children directory

        sdir = sorted(dir_dict.keys())
        for d in sdir:
            if d == '.' or d == '..': continue

            d_lspath = lspath + '_' + d
            d_pdir = pdir + os.sep + d

            msgs.extend(self.poll_directory(d_pdir, d_lspath))

        return msgs

    #def post(self,post_exchange,post_baseUrl,post_relpath,to_clusters, \
    #              partstr=None,sumstr=None,rename=None,mtime=None,atime=None,mode=None,link=None):
    #
    #   self.msg.exchange = post_exchange
    #
    #   self.msg.set_topic(self.post_topic_prefix,post_relpath)
    #   if self.subtopic != None : self.msg.set_topic_usr(self.post_topic_prefix,self.subtopic)

    #   self.msg.set_notice(post_baseUrl,post_relpath)

    # set message headers
    #   msg = msg_init(

    #   msg['to_clusters'] = to_clusters

    #   if partstr  != None : msg['parts']        = partstr
    #   if sumstr   != None : msg['sum']          = sumstr
    #   if rename   != None : msg['rename']       = rename

    #   if self.preserve_time:
    #       if mtime    != None : msg['mtime']        = mtime
    #       if atime    != None : msg['atime']        = atime

    #   if self.preserve_mode:
    #       if mode     != None : msg['mode']         = "%o" % ( mode & 0o7777 )

    #   if link     != None : msg['link']         = link

    #   if self.cluster != None : msg['from_cluster'] = self.cluster
    #   if self.source  != None : msg['source']       = self.source

    #   logger.debug("Added %s" % (self.msg.notice))

    #   return ok

    def poll_file_post(self, ssiz, destDir, remote_file):

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
                ok = msg_init(path, self.o, lstat)
                return ok

        post_relPath = destDir + '/' + remote_file

        msg = msg_init(post_relPath, self.o, None)

        if self.o.integrity_method and (',' in self.o.integrity_method):
            m, v = self.o.integrity_method.split(',')
            msg['integrity'] = {'method': m, 'value': v}

        try:
            isiz = int(ssiz)
            msg['size'] = isiz
        except:
            pass

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

        #ok = self.post(self, self.o.post_exchange,self.o.post_baseUrl,self.o.post_relPath,self.o.to_clusters, \
        #               self.partstr, self.sumstr,this_rename)

        return [msg]

    def poll_list_post(self, destDir, desclst, filelst):

        n = 0
        msgs = []

        for idx, remote_file in enumerate(filelst):
            desc = desclst[remote_file]
            ssiz = desc.split()[4]

            msgs.extend(self.poll_file_post(ssiz, destDir, remote_file))
        return msgs

    # =============
    # for all directories, get urls to post
    # if True is returned it means : no sleep, retry on return
    # False means, go to sleep and retry after sleep seconds
    # =============

    def post_new_urls(self):

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

    # write ls file

    def write_ls_file(self, ls, lspath):

        if len(ls) == 0:
            try:
                os.unlink(lspath)
            except:
                pass
            return True

        filelst = sorted(ls.keys())

        try:
            fp = open(lspath, 'w')
            for f in filelst:
                fp.write(ls[f] + '\n')
            fp.close()

            return True

        except:
            logger.error("Unable to write ls to file %s" % lspath)

        return False
