# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#
import copy
from base64 import b64decode, b64encode
from collections import *
from hashlib import sha512
import json
import logging
from mimetypes import guess_type
import os
import os.path
import random
from random import choice

import sarracenia
from sarracenia import *

from sarracenia.featuredetection import features

if features['reassembly']['present']:
    import sarracenia.blockmanifest

from sarracenia.flowcb import FlowCB
import sarracenia.identity


import stat
from sys import platform as _platform
import sys
import time

if features['watch']['present']:
    from watchdog.observers import Observer
    from watchdog.observers.polling import PollingObserver
    from watchdog.events import PatternMatchingEventHandler

logger = logging.getLogger(__name__)


if features['watch']['present']:
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
    so it was incremental and had little overhead. This one is does the whole recursion
    in one gather.

    It will fail horribly for large trees. Need to re-formulate to replace recursion with interation.
    perhaps a good time to use python iterators.
  
    also should likely switch from listdir to scandir
    """
    def on_add(self, event, src, dst):
        logger.debug("on_add %s %s %s" % ( event, src, dst ) )
        self.new_events['%s %s' % (src, dst)] = (event, src, dst)

    def on_created(self, event):
        # on_created (for SimpleEventHandler)
        if event.is_directory:
            self.on_add('mkdir', event.src_path, None)
        else:
            self.on_add('create', event.src_path, None)

    def on_deleted(self, event):
        # on_deleted (for SimpleEventHandler)
        if event.is_directory:
            self.on_add('rmdir', event.src_path, None)
        else:
            self.on_add('delete', event.src_path, None)

    def on_modified(self, event):
        # on_modified (for SimpleEventHandler)
        if not event.is_directory:
            self.on_add('modify', event.src_path, None)

    def on_moved(self, event):
        # on_moved (for SimpleEventHandler)
        self.on_add('move', event.src_path, event.dest_path)

    def __init__(self, options):
        """ 
        """

        super().__init__(options,logger)

        if not features['watch']['present']:
            logger.critical("watchdog module must be installed to watch directories")
            
        logger.debug("%s used to be overwrite_defaults" % self.o.component)

        self.obs_watched = []
        self.watch_handler = None
        self.post_topicPrefix = ["v03"]

        self.inl = OrderedDict()
        self.new_events = OrderedDict()
        self.left_events = OrderedDict()

        #self.o.blockSize = 200 * 1024 * 1024
        self.o.create_modify = ('create' in self.o.fileEvents) or (
            'modify' in self.o.fileEvents)

    def post_delete(self, path, key=None, value=None,is_directory=False):
        #logger.debug("post_delete %s (%s,%s)" % (path, key, value))

        msg = sarracenia.Message.fromFileInfo(path, self.o, None)

        msg['fileOp'] = { 'remove':'' }

        if is_directory: 
            msg['fileOp']['directory'] = ''

        # partstr
        partstr = None

        # used when moving a file
        if key != None:
            msg[key] = value
            if key == 'newname' and self.o.post_baseDir:
                msg['new_dir'] = os.path.dirname(value)
                msg['new_file'] = os.path.basename(value)
                msg[key] = value.replace(self.o.post_baseDir, '')

        return [msg]

    def post_file(self, path, lstat, key=None, value=None):
        #logger.debug("start  %s" % path)

        # check the value of blockSize

        fsiz = lstat.st_size
        blksz = self.set_blockSize(self.o.blockSize, fsiz)

        # if we should send the file in parts

        if (blksz > 0 and blksz < fsiz) and os.path.isfile(path):
            return self.post_file_in_parts(path, lstat)

        msg = sarracenia.Message.fromFileData(path, self.o, lstat)

        # used when moving a file
        if key != None:
            if not 'fileOp' in msg:
                msg['fileOp'] = { key : value }
            else:
                msg['fileOp'][key] = value

        if os_stat.S_ISDIR(lstat.st_mode):
            return [msg]

        # complete message
        if (self.o.post_topicPrefix[0] == 'v03') and self.o.inline:
            if fsiz < self.o.inlineByteMax:

                if self.o.inlineEncoding == 'guess':
                    e = guess_type(path)[0]
                    binary = not e or not ('text' in e)
                else:
                    binary = (self.o.inlineEncoding == 'text')

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
            else:
                if self.o.inlineOnly:
                    logger.error('skipping file %s too large (%d bytes > %d bytes max)) for inlining' % \
                       ( path, fsiz, self.o.inlineByteMax )  )
                    return []

        return [msg]

    def post_file_in_parts(self, path, lstat):
        #logger.info("start %s" % path )

        msg = sarracenia.Message.fromFileInfo(path, self.o, lstat)

        logger.debug( f"initial msg:{msg}" )
        # check the value of blockSize

        fsiz = lstat.st_size
        chunksize = self.set_blockSize(self.o.blockSize, fsiz)

        # count blocks and remainder

        block_count = int(fsiz / chunksize)
        remainder = fsiz % chunksize
        if remainder > 0: block_count = block_count + 1

        #logger.debug( f" fiz:{fsiz}, chunksize:{chunksize}, block_count:{block_count}, remainder:{remainder}" )

        # loop on blocks

        blocks = list(range(0, block_count))
        if self.o.randomize:
            random.shuffle(blocks)
            #blocks = [8, 3, 1, 2, 9, 6, 0, 7, 4, 5] # Testing
            logger.info('Sending partitions in the following order: ' +
                        str(blocks))

        msg['blocks'] = {
            'method': 'inplace',
            'size': chunksize,
            'number': -1,
            'manifest': {}
        }
        logger.debug( f" blocks:{blocks} " )

        for current_block in blocks:

            # compute block stuff
            offset = current_block * chunksize
            length = chunksize

            last = current_block == block_count - 1

            if last and remainder > 0:
                length = remainder

            msg['size']=length

            # set partstr
            msg.computeIdentity(path, self.o, offset=offset )
            msg['blocks']['manifest'][current_block] = { 'size':length, 'identity': msg['identity']['value'] }

        
        if features['reassembly']['present'] and \
           (not hasattr(self.o, 'block_manifest_delete') or not self.o.block_manifest_delete):
            with sarracenia.blockmanifest.BlockManifest( path ) as bm:
                bm.set(msg['blocks'])

        messages = []
        for current_block in blocks:

            msg['blocks']['number'] = current_block
            msg['size'] = msg['blocks']['manifest'][current_block]['size']
            msg['identity']['value'] = msg['blocks']['manifest'][current_block]['identity']

            #logger.info( f" size: {msg['size']} blocks: {msg['blocks']}, offset: {offset} identity: {msg['identity']} " )

            messages.append(copy.deepcopy(msg))

        return messages

    def post_link(self, path, key='link', value=None):
        #logger.debug("post_link %s" % path )

        msg = sarracenia.Message.fromFileInfo(path, self.o, None)

        # resolve link

        if key == 'link':
            value = os.readlink(path)

        # used when moving a file
        if not 'fileOp' in msg:
           msg['fileOp'] = { key: value }
        else:
           msg['fileOp'][key] = value

        return [msg]

    def post_move(self, src, dst):
        #logger.debug("post_move %s %s" % (src,dst) )

        # watchdog funny ./ added at end of directory path ... removed

        messages = []
        src = src.replace('/./', '/')
        dst = dst.replace('/./', '/')

        if os.path.islink(dst) and self.o.realpathPost:
            dst = os.path.realpath(dst)
            if sys.platform == 'win32':
                dst = dst.replace('\\', '/')

        # file

        if os.path.isfile(dst):
            if hasattr(self.o,'v2compatRenameDoublePost') and self.o.v2compatRenameDoublePost:
                messages.extend(self.post_delete(src, 'newname', dst))
            messages.extend(self.post_file(dst, sarracenia.stat(dst), 'rename', src))
            return messages

        # link

        if os.path.islink(dst):
            if hasattr(self.o,'v2compatRenameDoublePost') and self.o.v2compatRenameDoublePost:
                messages.extend(self.post_delete(src, 'newname', dst))
            messages.extend(self.post_link(dst, 'rename', src))
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

    def post1file(self, path, lstat, is_directory=False) -> list:
        """
          create the notification message for a single file, based on the lstat metadata.

          when lstat is present it is used to decide whether the file is an ordinary file, a link
          or a directory, and the appropriate message is built and returned.

          if the lstat metadata is None, then that signifies a "remove" message to be created.
          In the remove case, without the lstat, one needs the is_directory flag to decide whether
          it is an ordinary file remove, or a directory remove.   is_directory is not used other
          than for the remove case.

          The return value is a list that usually contains a single message.  It is a list to allow
          for if options are combined such that a symbolic link and the realpath it posts to may
          involve multiple messages for a single file. Similarly in the multi-block transfer case.

        """

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
                if os.path.exists(rpath): 
                   lstat = sarracenia.stat(rpath)

                messages.extend(self.post1file(rpath, lstat))

        # path deleted

        elif lstat == None:
            messages.extend(self.post_delete(path,key=None,value=None,is_directory=is_directory))

        # path is a file

        elif os.path.isfile(path) or os.path.isdir(path):
            messages.extend(self.post_file(path, lstat))

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
          return a tuple: pop? + list of messages.
          

        """
        #logger.debug("process_event %s %s %s " % (event,src,dst) )

        # delete

        if event == 'delete' :
            if event in self.o.fileEvents:
                return (True, self.post1file(src, None))
            return (True, [])

        if event == 'rmdir' :
            if event in self.o.fileEvents:
                return (True, self.post1file(src, None, is_directory=True))
            return (True, [])

        # move

        if event == 'move':
            if self.o.create_modify:
                return (True, self.post1move(src, dst))

        # create or modify

        # directory : skipped, its content is watched
        #if self.o.recursive and os.path.isdir(src):
        #    dirs = list(map(lambda x: x[1][1], self.inl.items()))
        #    #logger.debug("skipping directory %s list: %s" % (src, dirs))

        # link ( os.path.exists = false, lstat = None )

        if os.path.islink(src):
            if 'link' in self.o.fileEvents:
                return (True, self.post1file(src, None))
            return (True, [])

        # file : must exists
        #       (may have been deleted since event caught)

        if not os.path.exists(src): return (True, [])

        # file : must be old enough

        lstat = sarracenia.stat(src)

        if lstat and hasattr(lstat,'st_mtime'):
            age = time.time() - lstat.st_mtime

            if age < self.o.fileAgeMin:
                logger.debug( "%d vs (inflight setting) %d seconds. Too New!" % (age,self.o.fileAgeMin) )
                return (False, [])

            if self.o.fileAgeMax > 0 and age > self.o.fileAgeMax:
                logger.debug("%d vs (fileAgeMax setting) %d seconds. Too Old!" % (age,self.o.fileAgeMax) )
                return (True, [])

        # post it

        if event == 'mkdir':
            if 'mkdir' in self.o.fileEvents:
                return (True, self.post1file(src, lstat, is_directory=True))
            return(True,[])
        elif self.o.create_modify: 
            return (True, self.post1file(src, lstat))
        return (True, [])

    def set_blockSize(self, bssetting, fsiz):

        tfactor = 50 * 1024 * 1024

        if bssetting == 0:  ## default blockSize
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
            event_done=False
            event, src, dst = self.cur_events[key]
            try:
                (event_done, new_messages) = self.process_event(event, src, dst)
                messages.extend(new_messages)
            except OSError as err:
                """
                  This message is reduced to debug priority because it often happens when files
                  are too transitory (they disappear before we have a chance to post them)
                  not sure if it should be an error message or not.
                  
                """
                logger.debug("skipping event that could not be processed: ({}): {}".format(
                    event, err))
                logger.debug("Exception details:", exc_info=True)
                event_done=True
            if event_done:
                self.left_events.pop(key)
        return messages

    def walk(self, src):
        """
          walk directory tree returning 1 message for each file in it.
        """
        logger.debug("walk %s" % src)

        # how to proceed with symlink

        if os.path.islink(src) and self.o.realpathPost:
            src = os.path.realpath(src)
            if sys.platform == 'win32':
                src = src.replace('\\', '/')

        messages = []

        # need to post root of tree first, so mode bits get propagated on creation.
        if src == self.o.post_baseDir :
            logger.debug("skip posting of post_baseDir {src}")
        else:
            messages.extend(self.post1file(src, sarracenia.stat(src), is_directory=True))

        # walk src directory, this walk is depth first... there could be a lot of time
        # between *listdir* run, and when a file is visited, if there are subdirectories before you get there.
        # hence the existence check after listdir (crashed in flow_tests of > 20,000)

        if self.o.recursive:
            for x in os.listdir(src):
                path = src + '/' + x
                # add path created
                if os.path.isdir(path):
                    messages.extend(self.walk(path))
                    continue

                if os.path.exists(path):
                    messages.extend(self.post1file(path, sarracenia.stat(path)))


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
            if self.o.realpathPost:
                d = realp
            else:
                d = p + '/' + '.'
        else:
            d = p

        try:
            fs = sarracenia.stat(d)
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

        if not features['watch']['present']:
            logger.critical("sr_watch needs the python watchdog library to be installed.")
            return []

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

    def gather(self, messageCountMax):
        """
           from sr_post.py/run 

           FIXME: really bad performance with large trees: It scans an entire tree
           before emitting any messages. Need to re-factor with iterator style so produce
           result in batch sized chunks incrementally.
        """
        #logger.debug("%s run partflg=%s, sum=%s, nodupe_ttl=%s basis=%s pbd=%s" % \
        #      ( self.o.component, self.o.partflg, self.o.sumflg, self.o.nodupe_ttl,
        #        self.o.nodupe_basis, self.o.post_baseDir ))
        #logger.debug("%s realpathPost=%s follow_links=%s force_polling=%s batch=%s"  % \
        #      ( self.o.component, self.o.realpathPost, self.o.follow_symlinks, \
        #        self.o.force_polling, self.o.batch ) )
        #logger.info("%s len(self.queued_messages)=%d" % \
        #     ( self.o.component, len(self.queued_messages) ) )

        pbd = self.o.post_baseDir

        if len(self.queued_messages) > self.o.batch:
            messages = self.queued_messages[0:self.o.batch]
            self.queued_messages = self.queued_messages[self.o.batch:]
            return (True, messages)

        elif len(self.queued_messages) > 0:
            messages = self.queued_messages
            self.queued_messages = []

            if self.o.sleep < 0:
                return (True, messages)
        else:
            messages = []

        if self.primed:
            return (True, self.wakeup())

        cwd = os.getcwd()

        for d in self.o.postpath:

            # convert relative path to absolute.
            if d[0] != os.sep: d = cwd + os.sep + d

            d=self.o.variableExpansion(d)
            logger.debug("postpath = %s" % d)

            if self.o.sleep > 0:
                if features['watch']['present']:
                    messages.extend(self.watch_dir(d))
                else:
                    logger.critical("python watchdog package missing! Cannot watch directory")
                continue

            if os.path.isdir(d):
                logger.debug("postpath = %s" % d)
                messages.extend(self.walk(d))
            elif os.path.islink(d):
                messages.extend(self.post1file(d, None))
            elif os.path.isfile(d):
                messages.extend(self.post1file(d, sarracenia.stat(d)))
            else:
                logger.error("could not post %s (exists %s)" %
                             (d, os.path.exists(d)))

        if len(messages) > self.o.batch:
            self.queued_messages = messages[self.o.batch:]
            logger.info("len(queued_messages)=%d" % len(self.queued_messages))
            messages = messages[0:self.o.batch]

        self.primed = True
        return (True, messages)
