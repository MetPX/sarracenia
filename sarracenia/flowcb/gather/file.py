#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#

from base64 import b64decode, b64encode
from collections import *
from hashlib import sha512
import json
import logging
from mimetypes import guess_type
import os
import random
from random import choice

from sarracenia import *
from sarracenia.flowcb import FlowCB
from sarracenia.flowcb.gather import msg_init
import sarracenia.integrity
import sarracenia.filemetadata

import stat
from sys import platform as _platform
import sys
import time

from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import PatternMatchingEventHandler

logger = logging.getLogger(__name__)


class SimpleEventHandler(PatternMatchingEventHandler):
    def __init__(self, parent):
        self.on_created = parent.on_created
        self.on_deleted = parent.on_deleted
        self.on_modified = parent.on_modified
        self.on_moved = parent.on_moved
        super().__init__()


class File(FlowCB):
    """
    read the file system, create messages for the files you find.

    this is taken from v2's sr_post.py

    FIXME FIXME FIXME
    FIXME: the sr_post version would post files on the fly as it was traversing trees.
    so it was incremental and had little overhead.  This one is does the whole recursion
    in one gather.

    It will fail horribly for large trees. Need to re-formulate to replace recursion with interation.
    perhaps a good time to use python iterators.
  
    also should likely switch from listdir to scandir
    """
    def on_add(self, event, src, dst):
        #logger.debug("on_add %s %s %s" % ( event, src, dst ) )
        self.new_events['%s %s' % (src, dst)] = (event, src, dst)

    def on_created(self, event):
        # on_created (for SimpleEventHandler)
        self.on_add('create', event.src_path, None)

    def on_deleted(self, event):
        # on_deleted (for SimpleEventHandler)
        self.on_add('delete', event.src_path, None)

    def on_modified(self, event):
        # on_modified (for SimpleEventHandler)
        self.on_add('modify', event.src_path, None)

    def on_moved(self, event):
        # on_moved (for SimpleEventHandler)
        self.on_add('move', event.src_path, event.dest_path)

    def __init__(self, options):
        """ 
        """

        self.o = options
        
        logger.setLevel( getattr( logging, self.o.logLevel.upper() ) )

        logger.debug("%s used to be overwrite_defaults" % self.o.program_name)

        self.obs_watched = []
        self.watch_handler = None
        self.post_topicPrefix = [ "v03" ]

        self.inl = OrderedDict()
        self.new_events = OrderedDict()
        self.left_events = OrderedDict()

        self.o.blocksize = 200 * 1024 * 1024
        self.o.create_modify = ('create' in self.o.events) or (
            'modify' in self.o.events)

    def path_inflight(self, path, lstat):
        """
          check the self.o.inflight, compare fail age against it.
          return True if the file is old enough to be posted.
        """
        #logger.debug("path_inflight %s" % path)

        if not isinstance(self.o.inflight, int):
            #logger.debug("ok inflight unused")
            return False

        if lstat == None:
            #logger.debug("ok lstat None")
            return False

        age = nowflt() - lstat.st_mtime
        if age < self.o.inflight:
            logger.debug("%d vs (inflight setting) %d seconds. Too New!" % \
                (age,self.o.inflight) )
            return True

        return False

    def post_delete(self, path, key=None, value=None):
        #logger.debug("post_delete %s (%s,%s)" % (path, key, value))

        msg = msg_init(path, self.o, None)

        # sumstr
        hash = sha512()
        hash.update(bytes(os.path.basename(path), encoding='utf-8'))
        sumstr = {
            'method': 'remove',
            'value': b64encode(hash.digest()).decode('utf-8')
        }

        # partstr
        partstr = None

        # completing headers
        msg['integrity'] = sumstr

        # used when moving a file
        if key != None:
            msg[key] = value
            if key == 'newname' and self.o.post_baseDir:
                msg['new_dir'] = os.path.dirname(value)
                msg['new_file'] = os.path.basename(value)
                msg[key] = value.replace(self.o.post_baseDir, '')

        return [msg]

    def post_file(self, path, lstat, key=None, value=None):
        #logger.debug("post_file %s" % path)

        # check if it is a part file
        if path.endswith('.' + self.o.part_ext):
            return self.post_file_part(path, lstat)

        # This variable means that part_file_assemble plugin is loaded and will handle posting the original file (being assembled)

        elif hasattr(self, 'suppress_posting_partial_assembled_file'):
            return []

        # check the value of blocksize

        fsiz = lstat[stat.ST_SIZE]
        blksz = self.set_blocksize(self.o.blocksize, fsiz)

        # if we should send the file in parts

        if blksz > 0 and blksz < fsiz:
            return self.post_file_in_parts(path, lstat)

        msg = msg_init(path, self.o, lstat)

        # partstr

        msg["size"] = fsiz

        sumstr = self.compute_sumstr(path, msg)
        #sumstr = { "method": "notImplemented", value: "bad" }

        # complete message
        if ( self.o.post_topicPrefix[0] == 'v03') and self.o.inline and fsiz < self.o.inline_max:

            if self.o.inline_encoding == 'guess':
                e = guess_type(path)[0]
                binary = not e or not ('text' in e)
            else:
                binary = (self.o.inline_encoding == 'text')

            f = open(path, 'rb')
            d = f.read()
            f.close()

            if binary:
                msg["content"] = {
                    "encoding": "base64",
                    "value": b64encode(d).decode('utf-8')
                }
            else:
                try:
                    msg["content"] = {
                        "encoding": "utf-8",
                        "value": d.decode('utf-8')
                    }
                except:
                    msg["content"] = {
                        "encoding": "base64",
                        "value": b64encode(d).decode('utf-8')
                    }

        msg['integrity'] = sumstr

        # used when moving a file

        if key != None:
            msg[key] = value
            if key == 'oldname' and self.o.post_baseDir:
                msg[key] = value.replace(self.o.post_baseDir, '')

        return [msg]

    def compute_sumstr(self, path, msg):
        xattr = sarracenia.filemetadata.FileMetadata(path)

        if self.o.randomize:
            methods = [
                'random', 'md5', 'md5name', 'sha512', 'cod,md5', 'cod,sha512'
            ]
            sumflg = choice(methods)
        elif 'integrity' in xattr.x and 'mtime' in xattr.x:
            if xattr.get('mtime') >= self.msg.headers['mtime']:
                logger.debug("mtime remembered by xattr")
                return xattr.get('integrity')
            else:
                logger.debug("xattr sum too old")
                sumflg = self.o.sumflg
        else:
            sumflg = self.o.sumflg

        xattr.set('mtime', msg['mtime'])

        #logger.debug("sum set by compute_sumstr")

        if sumflg[:4] == 'cod,' and len(sumflg) > 2:
            sumstr = sumflg
        else:
            sumalgo = sarracenia.integrity.Integrity.factory(sumflg)
            sumalgo.set_path(path)

            # compute checksum

            if sumflg in ['md5', 'sha512']:

                fp = open(path, 'rb')
                i = 0
                while i < msg['size']:
                    buf = fp.read(self.o.bufsize)
                    if not buf: break
                    sumalgo.update(buf)
                    i += len(buf)
                fp.close()

            # setting sumstr
            checksum = sumalgo.get_value()
            sumstr = {'method': sumflg, 'value': checksum}

        xattr.set('integrity', sumstr)
        xattr.persist()
        return sumstr

    def post_file_in_parts(self, path, lstat):
        #logger.debug("post_file_in_parts %s" % path )

        msg = msg_init(path, self.o, lstat)

        # check the value of blocksize

        fsiz = lstat[stat.ST_SIZE]
        chunksize = self.set_blocksize(self.blocksize, fsiz)

        # count blocks and remainder

        block_count = int(fsiz / chunksize)
        remainder = fsiz % chunksize
        if remainder > 0: block_count = block_count + 1

        # default sumstr

        sumstr = self.o.sumflg

        # loop on chunks

        blocks = list(range(0, block_count))
        if self.randomize:
            random.shuffle(blocks)
            #blocks = [8, 3, 1, 2, 9, 6, 0, 7, 4, 5] # Testing
            logger.info('Sending partitions in the following order: ' +
                        str(blocks))

        messages = []
        for i in blocks:

            # setting sumalgo for that part

            sumflg = self.o.sumflg

            if sumflg[:2] == 'z,' and len(sumflg) > 2:
                sumstr = sumflg

            else:
                sumflg = self.o.sumflg
                sumalgo = sarracenia.integrity.Integrity.factory(sumflg)
                sumalgo.set_path(path)

            # compute block stuff

            current_block = i

            offset = current_block * chunksize
            length = chunksize

            last = current_block == block_count - 1
            if last and remainder > 0:
                length = remainder

            # set partstr

            partstr = {
                'method': 'inplace',
                'size': chunksize,
                'count': block_count,
                'remainder': remainder,
                'number': current_block
            }
            # compute checksum if needed

            if not self.sumflg in ['random', 'md5name', 'cod']:
                bufsize = self.o.bufsize
                if length < bufsize: bufsize = length

                fp = open(path, 'rb')
                if offset != 0: fp.seek(offset, 0)
                t = 0
                while t < length:
                    buf = fp.read(bufsize)
                    if not buf: break
                    sumalgo.update(buf)
                    t += len(buf)
                fp.close()

                checksum = sumalgo.get_value()
                sumstr = {'method': sumflg, 'value': checksum}

            # complete  message

            msg['integrity'] = sumstr
            messages.extend(copy(deepcopy(msg)))

        return messages

    def post_file_part(self, path, lstat):

        msg = msg_init(path, self.o, lstat)

        # verify suffix

        ok, log_msg, suffix, partstr, sumstr = self.msg.verify_part_suffix(
            path)

        # something went wrong

        if not ok:
            logger.debug("file part extension but %s for file %s" %
                         (log_msg, path))
            return False

        # check rename see if it has the right part suffix (if present)
        if 'rename' in self.msg.headers and not suffix in self.msg.headers[
                'rename']:
            msg['rename'] += suffix

        # complete  message

        msg['parts'] = partstr
        msg['integrity'] = sumstr

        return [msg]

    def post_link(self, path, key=None, value=None):
        #logger.debug("post_link %s" % path )

        msg = msg_init(path, self.o, None)

        # resolve link

        link = os.readlink(path)

        # partstr

        partstr = None

        # sumstr

        hash = sha512()
        hash.update(bytes(link, encoding='utf-8'))
        msg['integrity'] = {
            'method': 'link',
            'value': b64encode(hash.digest()).decode('utf-8')
        }

        # complete headers
        msg['link'] = link

        # used when moving a file

        if key != None: msg[key] = value

        return [msg]

    def post_move(self, src, dst):
        #logger.debug("post_move %s %s" % (src,dst) )

        # watchdog funny ./ added at end of directory path ... removed

        messages = []
        src = src.replace('/./', '/')
        dst = dst.replace('/./', '/')

        if os.path.islink(dst) and self.o.realpath_post:
            dst = os.path.realpath(dst)
            if sys.platform == 'win32':
                dst = dst.replace('\\', '/')

        # file

        if os.path.isfile(dst):
            messages.extend(self.post_delete(src, 'newname', dst))
            messages.extend(self.post_file(dst, os.stat(dst), 'oldname', src))
            return messages

        # link

        if os.path.islink(dst):
            messages.extend(self.post_delete(src, 'newname', dst))
            messages.extend(self.post_link(dst, 'oldname', src))
            return messages

        # directory
        if os.path.isdir(dst):
            for x in os.listdir(dst):

                dst_x = dst + '/' + x
                src_x = src + '/' + x

                messages = self.post_move(src_x, dst_x)

            # directory list to delete at end
            self.move_dir_lst.append((src, dst))

        return messages

    def post1file(self, path, lstat):

        messages = []

        # watchdog funny ./ added at end of directory path ... removed
        path = path.replace('/./', '/')

        # always use / as separator for paths being posted.
        if os.sep != '/':  # windows
            path = path.replace(os.sep, '/')

        # path is a link

        if os.path.islink(path):
            messages.extend(self.post_link(path))

            if self.o.follow_symlinks:
                link = os.readlink(path)
                try:
                    rpath = os.path.realpath(link)
                    if sys.platform == 'win32':
                        rpath = rpath.replace('\\', '/')

                except:
                    return messages

                lstat = None
                if os.path.exists(rpath): lstat = os.stat(rpath)

                messages.extend(self.post1file(rpath, lstat))

            return messages

        # path deleted

        if lstat == None:
            messages.extend(self.post_delete(path))
            return messages

        # path is a file

        if os.path.isfile(path):
            messages.extend(self.post_file(path, lstat))
            return messages

        # at this point it is a create,modify directory
        return messages

    def post1move(self, src, dst):
        #logger.debug("post1move %s %s" % (src,dst) )

        self.move_dir_lst = []

        messages = self.post_move(src, dst)

        for tup in self.move_dir_lst:
            src, dst = tup
            #logger.debug("deleting moved directory %s" % src )
            messages.extend(self.post_delete(src, 'newname', dst))

        return messages

    def process_event(self, event, src, dst):
        """
          return a list of messages.
        """
        #logger.debug("process_event %s %s %s " % (event,src,dst) )

        done = True
        later = False

        # delete

        if event == 'delete':
            if event in self.o.events:
                return self.post1file(src, None)
            return []

        # move

        if event == 'move':
            if self.o.create_modify:
                return self.post1move(src, dst)

        # create or modify

        # directory : skipped, its content is watched

        if os.path.isdir(src):
            dirs = list(map(lambda x: x[1][1], self.inl.items()))
            #logger.debug("skipping directory %s list: %s" % (src, dirs))
            return []

        # link ( os.path.exists = false, lstat = None )

        if os.path.islink(src):
            if 'link' in self.o.events:
                return self.post1file(src, None)
            return []

        # file : must exists
        #       (may have been deleted since event caught)

        if not os.path.exists(src): return []

        # file : must be old enough

        lstat = os.stat(src)
        if self.path_inflight(src, lstat): return []

        # post it

        if self.o.create_modify:
            return self.post1file(src, lstat)
        return []

    def set_blocksize(self, bssetting, fsiz):

        tfactor = 50 * 1024 * 1024

        if bssetting == 0:  ## default blocksize
            return tfactor

        elif bssetting == 1:  ## send file as one piece.
            return fsiz

        else:  ## partstr=i
            return bssetting

    def wakeup(self):
        #logger.debug("wakeup")

        # FIXME: Tiny potential for events to be dropped during copy.
        #     these lists might need to be replaced with watchdog event queues.
        #     left for later work. PS-20170105
        #     more details: https://github.com/gorakhargosh/watchdog/issues/392

        # pile up left events to process

        self.left_events.update(self.new_events)
        self.new_events = OrderedDict()

        # work with a copy events and keep done events (to delete them)

        self.cur_events = OrderedDict()
        self.cur_events.update(self.left_events)

        # loop on all events

        messages = []
        for key in self.cur_events:
            event, src, dst = self.cur_events[key]
            done = False
            try:
                messages.extend(self.process_event(event, src, dst))
            except OSError as err:
                logger.error("could not process event({}): {}".format(
                    event, err))
                logger.debug("Exception details:", exc_info=True)
                self.left_events.pop(key)
            if done:
                self.left_events.pop(key)
        return messages

    def walk(self, src):
        """
          walk directory tree returning 1 message for each file in it.
        """
        logger.debug("walk %s" % src)

        # how to proceed with symlink

        if os.path.islink(src) and self.o.realpath_post:
            src = os.path.realpath(src)
            if sys.platform == 'win32':
                src = src.replace('\\', '/')

        # walk src directory, this walk is depth first... there could be a lot of time
        # between *listdir* run, and when a file is visited, if there are subdirectories before you get there.
        # hence the existence check after listdir (crashed in flow_tests of > 20,000)

        messages = []
        for x in os.listdir(src):
            path = src + '/' + x
            if os.path.isdir(path):
                messages.extend(self.walk(path))
                continue

            # add path created
            if os.path.exists(path):
                messages.extend(self.post1file(path, os.stat(path)))
        return messages

    def walk_priming(self, p):
        """
         Find all the subdirectories of the given path, start watches on them. 
         deal with symbolically linked directories correctly
        """
        if os.path.islink(p):
            realp = os.path.realpath(p)
            if sys.platform == 'win32':
                realp = realp.replace('\\', '/')

            logger.info("sr_watch %s is a link to directory %s" % (p, realp))
            if self.o.realpath_post:
                d = realp
            else:
                d = p + '/' + '.'
        else:
            d = p

        try:
            fs = os.stat(d)
            dir_dev_id = '%s,%s' % (fs.st_dev, fs.st_ino)
            if dir_dev_id in self.inl:
                return True
        except OSError as err:
            logger.warning("could not stat file ({}): {}".format(d, err))
            logger.debug("Exception details:", exc_info=True)

        if os.access(d, os.R_OK | os.X_OK):
            try:
                ow = self.observer.schedule(self.watch_handler,
                                            d,
                                            recursive=True)
                self.obs_watched.append(ow)
                self.inl[dir_dev_id] = (ow, d)
                logger.info(
                    "sr_watch priming watch (instance=%d) scheduled for: %s " %
                    (len(self.obs_watched), d))
            except:
                logger.warning("sr_watch priming watch: %s failed, deferred." %
                               d)
                logger.debug('Exception details:', exc_info=True)

                # add path created
                self.on_add('create', p, None)
                return True

        else:
            logger.warning(
                "sr_watch could not schedule priming watch of: %s (EPERM) deferred."
                % d)
            logger.debug('Exception details:', exc_info=True)

            # add path created
            self.on_add('create', p, None)
            return True

        return True

    def watch_dir(self, sld):
        logger.debug("watch_dir %s" % sld)

        if self.o.force_polling:
            logger.info(
                "sr_watch polling observer overriding default (slower but more reliable.)"
            )
            self.observer = PollingObserver()
        else:
            logger.info(
                "sr_watch optimal observer for platform selected (best when it works)."
            )
            self.observer = Observer()

        self.obs_watched = []

        self.watch_handler = SimpleEventHandler(self)
        self.walk_priming(sld)

        logger.info(
            "sr_watch priming walk done, but not yet active. Starting...")
        self.observer.start()
        logger.info("sr_watch now active on %s posting to exchange: %s" %
                    (sld, self.o.post_exchange))

        if self.o.post_on_start:
            return self.walk(sld)
        else:
            return []

    def on_start(self):
        self.queued_messages = []
        self.primed = False

    def gather(self):
        """
           from sr_post.py/run 

           FIXME: really bad performance with large trees. it does scans an entire tree
           before emitting any messages.  need to re-factor with iterator style so produce
           result in batch sized chunks incrementally.
        """
        #logger.debug("%s run partflg=%s, sum=%s, suppress_duplicates=%s basis=%s pbd=%s" % \
        #      ( self.o.program_name, self.o.partflg, self.o.sumflg, self.o.suppress_duplicates,
        #        self.o.suppress_duplicates_basis, self.o.post_baseDir ))
        #logger.debug("%s realpath_post=%s follow_links=%s force_polling=%s batch=%s"  % \
        #      ( self.o.program_name, self.o.realpath_post, self.o.follow_symlinks, \
        #        self.o.force_polling, self.o.batch ) )
        #logger.info("%s len(self.queued_messages)=%d" % \
        #     ( self.o.program_name, len(self.queued_messages) ) )

        pbd = self.o.post_baseDir

        if len(self.queued_messages) > self.o.batch:
            messages = self.queued_messages[0:self.o.batch]
            self.queued_messages = self.queued_messages[self.o.batch:]
            return messages

        elif len(self.queued_messages) > 0:
            messages = self.queued_messages
            self.queued_messages = []

            if self.o.sleep < 0:
                return messages
        else:
            messages = []

        if self.primed:
            return self.wakeup()

        cwd = os.getcwd()

        for d in self.o.postpath:

            # convert relative path to absolute.
            if d[0] != os.sep: d = cwd + os.sep + d

            logger.debug("postpath = %s" % d)

            if self.o.sleep > 0:
                messages.extend(self.watch_dir(d))
                continue

            if os.path.isdir(d):
                logger.debug("postpath = %s" % d)
                messages.extend(self.walk(d))
            elif os.path.islink(d):
                messages.extend(self.post1file(d, None))
            elif os.path.isfile(d):
                messages.extend(self.post1file(d, os.stat(d)))
            else:
                logger.error("could not post %s (exists %s)" %
                             (d, os.path.exists(d)))

        if len(messages) > self.o.batch:
            self.queued_messages = messages[self.o.batch:]
            logger.info("len(queued_messages)=%d" % len(self.queued_messages))
            messages = messages[0:self.o.batch]

        self.primed = True
        return messages
