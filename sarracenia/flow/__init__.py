import copy
import importlib
import logging
import netifaces
import os

# v3 plugin architecture...
import sarracenia.flowcb
import sarracenia.integrity

import stat
import time
import types
import urllib.parse

from sarracenia import timestr2flt, timeflt2str, msg_set_report

import sarracenia.filemetadata

# for v2 subscriber routines...
import json, os, sys, time

from sys import platform as _platform

from base64 import b64decode, b64encode
from mimetypes import guess_type
# end v2 subscriber

from sarracenia import nowflt

logger = logging.getLogger(__name__)

default_options = {
    'accel_threshold': 0,
    'accept_unmatched': False,
    'attempts': 3,
    'batch': 100,
    'bytes_per_second': None,
    'download': False,
    'events': 'create|delete|link|modify',
    'housekeeping': 30,
    'log_reject': False,
    'logFormat':
    '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s',
    'logLevel': 'info',
    'mirror': True,
    'preserve_mode': True,
    'preserve_time': True,
    'message_count_max': 0,
    'message_rate_max': 0,
    'message_rate_min': 0,
    'sleep': 0.1,
    'topic_prefix': [ 'v03' ],
    'vip': None
}


class Flow:
    """
    Implement the General Algorithm from the Concepts Guide.

    The constructor/factory accept a configuration (sarracenia.config.Config class) with all the 
    settings in it.

    This class takes care of starting up, running with callbacks, and clean shutdown.

      need to know whether to sleep between passes  
      o.sleep - an interval (floating point number of seconds)
      o.housekeeping - 

      A flow processes worklists of messages

      worklist given to callbacks...

          worklist.incoming --> new messages to continue processing
          worklist.ok       --> successfully processed
          worklist.rejected --> messages to not be further processed.
          worklist.failed   --> messages for which processing failed.

      Initially all messages are placed in incoming.
      if a callback decides:
      
      - a message is not relevant, it is moved to rejected.
      - all processing has been done, it moves it to ok.
      - an operation failed and it should be retried later, move to retry

    callbacks must not remove messages from all worklists, re-classify them.
    it is necessary to put rejected messages in the appropriate worklist
    so they can be acknowledged as received.

    plugins  -- dict of modular functionality metadata.
         "load" - list of (v3) flow_callbacks to load.
         time    - one of the invocation times of callbacks. examples:
                   "on_start", "after_accept", etc...
                 contains routines to run at each *time*
     
    """
    @staticmethod
    def factory(cfg):
        for sc in Flow.__subclasses__():
            if cfg.program_name == sc.__name__.lower():
                return sc(cfg)

        if cfg.program_name == 'flow':
            return Flow(cfg)
        return None

    def __init__(self, cfg=None):
        """
       The cfg is should be an sarra/config object.
       """

        self._stop_requested = False

        me = 'flow'
        logging.basicConfig(
            format=
            '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s',
            level=logging.DEBUG)

        self.o = cfg

        if 'sarracenia.flow.Flow.logLevel' in self.o.settings:
            logger.setLevel( getattr(logging, self.o.settings['sarracenia.flow.Flow.logLevel'].upper() ) )
        else:
            logger.setLevel( getattr(logging, self.o.logLevel.upper() ))

        if not hasattr(self.o, 'post_topic_prefix'):
            self.o.post_topic_prefix = self.o.topic_prefix

        logging.basicConfig(format=self.o.logFormat,
                            level=getattr(logging, self.o.logLevel.upper()))


        self.plugins = {}
        for entry_point in sarracenia.flowcb.entry_points:
            self.plugins[entry_point] = []

        # FIXME: open new worklist
        self.worklist = types.SimpleNamespace()
        self.worklist.ok = []
        self.worklist.incoming = []
        self.worklist.rejected = []
        self.worklist.failed = []

        self.plugins['load'] = ['sarracenia.flowcb.retry.Retry']

        # open cache, get masks.
        if self.o.suppress_duplicates > 0:
            # prepend...
            self.plugins['load'].append('sarracenia.flowcb.nodupe.NoDupe')

        # FIXME: open retry

        # transport stuff.. for download, get, put, etc...
        self.scheme = None
        self.cdir = None
        self.proto = {}

        if hasattr(self.o, 'plugins'):
            self.plugins['load'].extend(self.o.plugins)

        # initialize plugins.
        if hasattr(self.o, 'v2plugins'):
            self.plugins['load'].append(
                'sarracenia.flowcb.v2wrapper.V2Wrapper')

    def loadCallbacks(self, plugins_to_load):

        logger.info('imports to load: %s' % (self.o.imports))
        for m in self.o.imports:
            importlib.import_module(m)

        #logger.info( 'plugins to load: %s' % ( plugins_to_load ) )
        for c in plugins_to_load:

            plugin = sarracenia.flowcb.load_library(c, self.o)

            #logger.info( 'plugin loading: %s an instance of: %s' % ( c, plugin ) )
            for entry_point in sarracenia.flowcb.entry_points:
                if hasattr(plugin, entry_point):
                    fn = getattr(plugin, entry_point)
                    if callable(fn):
                        #logger.info( 'registering %s/%s' % (c, entry_point))
                        if entry_point in self.plugins:
                            self.plugins[entry_point].append(fn)
                        else:
                            self.plugins[entry_point] = [fn]

            if not (hasattr(plugin, 'registered_as')
                    and callable(getattr(plugin, 'registered_as'))):
                continue

            schemes = plugin.registered_as()
            for schemed_entry_point in sarracenia.flowcb.schemed_entry_points:
                if not hasattr(plugin, schemed_entry_point):
                    continue

                fn = getattr(plugin, schemed_entry_point)
                if not callable(fn):
                    continue

                if not schemed_entry_point in self.plugins:
                    self.plugins[schemed_entry_point] = {}

                for s in schemes:
                    self.plugins[schemed_entry_point][s] = fn

        #logger.info( 'plugins initialized')
        self.o.check_undeclared_options()

    def _runCallbacksWorklist(self, entry_point):

        if hasattr(self, 'plugins') and (entry_point in self.plugins):
            for p in self.plugins[entry_point]:
                p(self.worklist)

    def _runCallbacksTime(self, entry_point):
        for p in self.plugins[entry_point]:
            p()

    def has_vip(self):
        # no vip given... standalone always has vip.
        if self.o.vip == None:
            return True

        for i in netifaces.interfaces():
            for a in netifaces.ifaddresses(i):
                j = 0
                while (j < len(netifaces.ifaddresses(i)[a])):
                    if self.o.vip in netifaces.ifaddresses(i)[a][j].get(
                            'addr'):
                        return True
                    j += 1
        return False

    def please_stop(self):
        self._stop_requested = True

    def close(self):

        self._runCallbacksTime('on_stop')
        logger.info('flow/close completed cleanly')

    def ack(self, mlist):
        if "ack" in self.plugins:
            for p in self.plugins["ack"]:
                p(mlist)

    def ackOKandRejected(self, desc):
        logger.debug('%s incoming: %d, ok: %d, rejected: %d, failed: %d' %
                     (desc, len(self.worklist.incoming), len(self.worklist.ok),
                      len(self.worklist.rejected), len(self.worklist.failed)))

        self.ack(self.worklist.ok)
        self.worklist.ok = []
        self.ack(self.worklist.rejected)
        self.worklist.rejected = []

    def run(self):
        """
          check if stop_requested once in a while, but never return otherwise.
        """

        self.loadCallbacks(self.plugins['load'])

        logger.debug("working directory: %s" % os.getcwd())

        next_housekeeping = nowflt() + self.o.housekeeping

        current_rate = 0
        total_messages = 0
        start_time = nowflt()

        current_sleep = self.o.sleep
        last_time = start_time

        logger.info("options:")
        self.o.dump()
        logger.info("callbacks loaded: %s" % self.plugins['load'])
        #for t in self.plugins:
        #    logger.info("%s : %s" % ( t, self.plugins[t] ) )

        self._runCallbacksTime('on_start')
        spamming = True

        while True:

            if self._stop_requested:
                self.close()
                break

            if self.has_vip():

                #logger.info("current_rate (%g) vs. message_rate_max(%g)) " %
                #            (current_rate, self.o.message_rate_max))
                self.gather()

                self.ackOKandRejected('A gathered')

                last_gather_len = len(self.worklist.incoming)
                if (last_gather_len == 0):
                    spamming = True
                else:
                    current_sleep = self.o.sleep
                    spamming = False

                self.filter()

                self.ackOKandRejected('B filtered')

                self.do()

                # need to acknowledge here, because posting will delete message-id
                self.ack(self.worklist.ok)

                self.ack(self.worklist.rejected)
                self.worklist.rejected = []
                self.ack(self.worklist.failed)
                self._runCallbacksWorklist('after_work')

                self.post()

                self.report()

                self.worklist.ok = []
                self.worklist.failed = []

            now = nowflt()
            run_time = now - start_time
            total_messages += last_gather_len

            if (self.o.message_count_max > 0) and (total_messages >= self.o.message_count_max):
                self.close()
                break

            current_rate = total_messages / run_time
            elapsed = now - last_time

            if (last_gather_len == 0) and (self.o.sleep < 0):
                self.close()
                break

            if spamming and (current_sleep < 5):
                current_sleep *= 2

            if now > next_housekeeping:
                logger.info('on_housekeeping')
                self._runCallbacksTime('on_housekeeping')
                next_housekeeping = now + self.o.housekeeping

            if (self.o.message_rate_min > 0) and (current_rate <
                                                  self.o.message_rate_min):
                logger.warning("receiving below minimum message rate")

            if (self.o.message_rate_max > 0) and (current_rate >=
                                                  self.o.message_rate_max):
                stime = 1 + 2 * ((current_rate - self.o.message_rate_max) /
                                 self.o.message_rate_max)
                logger.info(
                    "current_rate/2 (%g) above message_rate_max(%g): throttling"
                    % (current_rate, self.o.message_rate_max))
            else:
                stime = 0

            if (current_sleep > 0):
                if elapsed < current_sleep:
                    stime += current_sleep - elapsed
                    if stime > 60:  # if sleeping for a long time, debug output is good...
                        logger.debug(
                            "sleeping for more than 60 seconds: %g seconds. Elapsed since wakeup: %g Sleep setting: %g "
                            % (stime, elapsed, self.o.sleep))
                else:
                    logger.debug('worked too long to sleep!')
                    last_time = now
                    continue

            if (stime > 0):
                try:
                    logger.debug('sleeping for stime: %g seconds' % stime)
                    time.sleep(stime)
                except:
                    logger.info("flow woken abnormally from sleep")

                last_time = now

    def filter(self):

        #logger.debug('start')
        filtered_worklist = []
        for m in self.worklist.incoming:
            #logger.warning('message: %s ' % m)

            if 'oldname' in m:
                url = self.o.set_dir_pattern(m['baseUrl']) + os.sep + m['oldname']
                oldname_matched = False
                for mask in self.o.masks:
                    pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask
                    if mask_regexp.match(url):
                        oldname_matched = accepting
                        break

            url = self.o.set_dir_pattern(m['baseUrl']) + os.sep + m['relPath']

            # apply masks for accept/reject options.
            matched = False
            for mask in self.o.masks:
                #logger.info('filter - checking: %s' % str(mask) )
                pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask

                if mask_regexp.match(url):
                    matched = True
                    if not accepting:
                        if ('oldname' in m) and oldname_matched:
                            # deletion rename case... need to accept with an extra field...
                            if not 'renameUnlink' in m:
                                m['renameUnlink'] = True
                                m['_deleteOnPost'] |= set(['renameUnlink'])
                            logger.debug("rename deletion 1 %s" %
                                         (m['oldname']))
                        elif self.o.log_reject:
                            logger.info("reject: mask=%s strip=%s url=%s" %
                                        (str(mask), strip, url))
                        self.worklist.rejected.append(m)
                        break

                    # FIXME... missing dir mapping with mirror, strip, etc...
                    self.o.set_newMessageFields(m, url, pattern, maskDir,
                                                maskFileOption, mirror, strip,
                                                pstrip, flatten)

                    filtered_worklist.append(m)
                    #logger.debug( "accepted mask=%s strip=%s" % (str(mask), strip) )
                    break

            if not matched:
                if ('oldname' in m) and oldname_matched:
                    if not 'renameUnlink' in m:
                        m['renameUnlink'] = True
                        m['_deleteOnPost'] |= set(['renameUnlink'])
                    logger.debug("rename deletion 2 %s" % (m['oldname']))
                    filtered_worklist.append(m)
                    self.o.set_newMessageFields(m, url, None, None,
                                                self.o.filename, self.o.mirror,
                                                self.o.strip, self.o.pstrip,
                                                self.o.flatten)
                    continue

                if self.o.accept_unmatched:
                    logger.debug("accept: unmatched pattern=%s" % (url))
                    # FIXME... missing dir mapping with mirror, strip, etc...
                    self.o.set_newMessageFields(m, url, None,
                                                self.o.currentDir,
                                                self.o.filename, self.o.mirror,
                                                self.o.strip, self.o.pstrip,
                                                self.o.flatten)
                    filtered_worklist.append(m)
                else:
                    if self.o.log_reject:
                        logger.info("reject: unmatched pattern=%s" % (url))
                    msg_set_report(m, 304, "not modified (filter)")
                    self.worklist.rejected.append(m)

        self.worklist.incoming = filtered_worklist
        # apply after_accept plugins.
        self._runCallbacksWorklist('after_accept')

        #logger.debug('done')

    def gather(self):
        self.worklist.incoming = []
        for p in self.plugins["gather"]:
            new_incoming = p()
            if len(new_incoming) > 0:
                self.worklist.incoming.extend(new_incoming)

    def do(self):

        # mark all remaining messages as done.
        self.worklist.ok = self.worklist.incoming
        self.worklist.incoming = []
        logger.debug('processing %d messages worked!' % len(self.worklist.ok))

    def post(self):

        #logger.info('on_post starting for %d messages' % len(self.worklist.ok))
        #logger.info('post_baseDir=%s' % self.o.post_baseDir)
        for m in self.worklist.ok:

            if 'new_baseUrl' in m:
                m['baseUrl'] = m['new_baseUrl']

            if 'new_relPath' in m:
                m['relPath'] = m['new_relPath']

            if self.o.post_baseDir:
                m['relPath'].replace(self.o.post_baseDir, '', 1)

        #self._runCallbacksWorklist('on_posts')
        for p in self.plugins["post"]:
            p(self.worklist)

    def report(self):
        # post reports
        # apply on_report plugins
        #logger.info('unimplemented')
        pass

    def write_inline_file(self, msg):
        """
           write local file based on a message with inlined content.

        """
        # make sure directory exists, create it if not
        if not os.path.isdir(msg['new_dir']):
            try:
                os.makedirs(msg['new_dir'], 0o775, True)
            except Exception as ex:
                logger.warning("making %s: %s" % (newdir, ex))

        logger.info("data inlined with message, no need to download")
        path = msg['new_dir'] + os.path.sep + msg['new_file']
        #path = msg['new_relPath']

        try:
            f = os.fdopen(os.open(path, os.O_RDWR | os.O_CREAT), 'rb+')
        except Exception as ex:
            logger.warning("could not open %s to write: %s" % (path, ex))
            return False

        if msg['content']['encoding'] == 'base64':
            data = b64decode(msg['content']['value'])
        else:
            data = msg['content']['value'].encode('utf-8')

        if msg['integrity']['method'] == 'cod':
            algo_method = msg['integrity']['value']
        else:
            algo_method = msg['integrity']['method']

        onfly_algo = sarracenia.integrity.Integrity.factory(algo_method)
        data_algo = sarracenia.integrity.Integrity.factory(algo_method)
        onfly_algo.set_path(path)
        data_algo.set_path(path)

        onfly_algo.update(data)
        #msg.onfly_checksum = "{},{}".format(onfly_algo.registered_as(), onfly_algo.get_value())

        msg['onfly_checksum'] = {
            'method': algo_method,
            'value': onfly_algo.get_value()
        }

        if len(data) != msg['size']:
            logger.error(
                "decoded data size (%d bytes) does not have expected size: (%d bytes)"
                % (len(data), msg['size']))
            return False

        try:
            for p in self.plugins['on_data']:
                data = p(data)

        except Exception as ex:
            logger.warning("plugin failed: %s" % (p, ex))
            return False

        data_algo.update(data)

        #FIXME: If data is changed by plugins, need to update content header.
        #       current code will reproduce the upstream message without mofification.
        #       need to think about whether that is OK or not.

        msg['data_checksum'] = {
            'method': algo_method,
            'value': data_algo.get_value()
        }

        msg['_deleteOnPost'] |= set(['onfly_checksum'])

        msg['_deleteOnPost'] |= set(['data_checksum'])

        try:
            f.write(data)
            f.truncate()
            f.close()
            self.set_local_file_attributes(path, msg)

        except Exception as ex:
            logger.warning("failed writing and finalizing: %s" % (path, ex))
            return False

        return True

    def compute_local_checksum(self, msg):

        if sarracenia.filemetadata.supports_extended_attributes:
            try:
                x = sarracenia.filemetadata.FileMetadata(msg['new_path'])
                s = x.get('integrity')

                if s:
                    msg['local_integrity'] = x.get('integrity')
                    msg['_deleteOnPost'] |= set(['local_integrity'])
                    return

            except:
                pass

        local_integrity = sarracenia.integrity.Integrity.factory(
            msg['integrity']['method'])
        local_integrity.update_file(msg['new_path'])
        msg['local_integrity'] = {
            'method': msg['integrity']['method'],
            'value': local_integrity.get_value()
        }
        msg['_deleteOnPost'] |= set(['local_integrity'])

    def file_should_be_downloaded(self, msg):
        """
          determine whether a comparison of local_file and message metadata indicates that it is new enough
          that writing the file locally is warranted.

          return True to say downloading is warranted.

             False if the file in the message represents the same or an older version that what is corrently on disk.

          origin: refactor & translation of v2: content_should_not_be downloaded

          Assumptions:
                 new_path exists... there is a file to compare against.
        """
        # assert

        lstat = os.stat(msg['new_path'])
        fsiz = lstat[stat.ST_SIZE]

        # FIXME... local_offset... offset within the local file... partitioned... who knows?
        #   part of partitioning deferral.
        #end   = self.local_offset + self.length
        end = msg['size']

        # compare sizes... if (sr_subscribe is downloading partitions into taget file) and (target_file isn't fully done)
        # This check prevents random halting of subscriber (inplace on) if the messages come in non-sequential order
        # target_file is the same as new_file unless the file is partitioned.
        # FIXME If the file is partitioned, then it is the new_file with a partition suffix.
        #if ('self.target_file == msg['new_file'] ) and ( fsiz != msg['size'] ):

        if (fsiz != msg['size']):
            logger.debug("%s file size different, so cannot be the same" %
                         (msg['new_path']))
            return True

    # compare dates...

        if 'mtime' in msg:
            new_mtime = timestr2flt(msg['mtime'])
            old_mtime = 0.0

            if self.o.preserve_time:
                old_mtime = lstat.st_mtime
            elif sarracenia.filemetadata.supports_extended_attributes:
                try:
                    x = sarracenia.filemetadata.FileMetadata(msg['new_path'])
                    old_mtime = timestr2flt(x.get('mtime'))
                except:
                    pass

            if new_mtime <= old_mtime:
                if self.o.log_reject:
                    logger.info("rejected: mtime not newer %s " %
                                (msg['new_path']))
                return False
            else:
                logger.debug(
                    "{} new version is {} newer (new: {} vs old: {} )".format(
                        msg['new_path'], new_mtime - old_mtime, new_mtime,
                        old_mtime))

        if msg['integrity']['method'] in ['random', 'md5name', 'cod']:
            logger.debug("content_match %s sum 0/n/z never matches" %
                         (msg['new_path']))
            return True

        if end > fsiz:
            logger.debug(
                "content_match file not big enough... considered different")
            return True

        try:
            self.compute_local_checksum(msg)
        except:
            logger.debug(
                "something went wrong when computing local checksum... considered different"
            )
            return True

        logger.debug("checksum in message: %s vs. local: %s" %
                     (msg['integrity'], msg['local_integrity']))

        if msg['local_integrity'] == msg['integrity']:
            if self.o.log_reject:
                logger.info("rejected: same checksum %s " % (msg['new_path']))
            return False
        else:
            return True

    def removeOneFile(self, path):
        """
          process an unlink event, returning boolean success.
        """

        logger.debug("path to remove: %s" % path)

        ok = True
        try:
            if os.path.isfile(path): os.unlink(path)
            if os.path.islink(path): os.unlink(path)
            if os.path.isdir(path): os.rmdir(path)
            logger.info("removed %s" % path)
        except:
            logger.error("could not remove %s." % path)
            logger.debug('Exception details: ', exc_info=True)
            ok = False

        return ok

    def renameOneItem(self, old, path):
        """
            for messages with an oldname, it is to rename a file.
        """
        ok = True
        if not os.path.isfile(old): 
            logger.info( "old file %s not found, if destination (%s) missing, then fall back to copy" % (old,path) )
            # if the destination file exists, assume rename already happenned, 
            # otherwis return false so that caller falls back to downloading/sending the file.
            return os.path.isfile(path)

        try:
   
            if os.path.isfile(path): os.unlink(path)
            if os.path.islink(path): os.unlink(path)
            if os.path.isdir(path): os.rmdir(path)
            os.rename(old, path)
            logger.info("renamed %s -> %s" % (old, path))
        except:
            logger.error(
                "sr_subscribe/doit_download: could not rename %s to %s " %
                (old, path))
            logger.debug('Exception details: ', exc_info=True)
            ok = False
        return ok

    def link1file(self, msg):
        """        
          perform a symbolic link of a single file, based on a message, returning boolean success

          imported from v2/subscribe/doit_download "link event, try to link the local product given by message"
        """
        logger.debug("message is to link %s to %s" %
                     (msg['new_file'], msg['link']))

        # redundant, check is done in caller.
        #if not 'link' in self.o.events:
        #    logger.info("message to link %s to %s ignored (events setting)" %  \
        #                                    ( msg['new_file'], msg[ 'link' ] ) )
        #    return False

        if not os.path.isdir(msg['new_dir']):
            try:
                os.makedirs(msg['new_dir'], 0o775, True)
            except Exception as ex:
                logger.warning("making %s: %s" % (msg['new_dir'], ex))
                logger.debug('Exception details:', exc_info=True)

        ok = True
        try:
            path = msg['new_dir'] + '/' + msg['new_file']

            if os.path.isfile(path): os.unlink(path)
            if os.path.islink(path): os.unlink(path)
            if os.path.isdir(path): os.rmdir(path)
            os.symlink(msg['link'], path)
            logger.info("%s symlinked to %s " % (msg['new_file'], msg['link']))
        except:
            ok = False
            logger.error("symlink of %s %s failed." %
                         (msg['new_file'], msg['link']))
            logger.debug('Exception details:', exc_info=True)

        return ok

    def do_download(self):
        """
           do download work for self.worklist.incoming, placing files:
                successfully downloaded in worklist.ok
                temporary failures in worklist.failed
                permanent failures (or files not to be downloaded) in worklist.rejected

        """

        if self.o.notify_only:
            self.worklist.ok = self.worklist.incoming
            self.worklist.incoming = []
            return

        for msg in self.worklist.incoming:

            if 'newname' in msg:
                """
                  revamped rename algorithm requires only 1 message, ignore newname.
                """
                self.worklist.ok.append(msg)
                continue

            new_path = msg['new_dir'] + os.path.sep + msg['new_file']

            if 'oldname' in msg:
                if 'renameUnlink' in msg:
                    self.removeOneFile(msg['oldname'])
                    self.worklist.ok.append(msg)
                else:
                    # actual rename...
                    ok = self.renameOneItem(msg['oldname'], new_path)
                    # if rename succeeds, fall through to download object to find if the file renamed
                    # actually matches the one advertised, and potentially download it.
                    # if rename fails, recover by falling through to download the data anyways.
                    if ok:
                         self.worklist.ok.append(msg)
                         msg_set_report(msg, 201, 'renamed')
                         continue
                        
            elif (msg['integrity']['method'] == 'remove') and ('delete' in self.o.events):
                if self.removeOneFile(new_path):
                    msg_set_report(msg, 201, 'removed')
                    self.worklist.ok.append(msg)
                else:
                    #FIXME: should this really be queued for retry? or just permanently failed?
                    # in rejected to avoid retry, but wondering if failed and deferred
                    # should be separate lists in worklist...
                    msg_set_report(msg, 500, "remove failed")
                    self.worklist.rejected.append(msg)
                continue

            if 'link' in msg.keys() and ( 'link' in self.o.events ):
                if self.link1file(msg):
                    msg_set_report(msg, 201, 'linked')
                    self.worklist.ok.append(msg)
                else:
                    # as above...
                    msg_set_report(msg, 500, "symlink failed")
                    self.worklist.rejected.append(msg)
                continue

            # establish new_inflight_path which is the file to download into initially.
            if self.o.inflight == None or (
                ('blocks' in msg) and (msg['blocks']['method'] == 'inplace')):
                new_inflight_path = msg['new_file']
            elif type(self.o.inflight) == str:
                if self.o.inflight == '.':
                    new_inflight_path = '.' + new_file
                elif self.o.inflight[-1] == '/':
                    if not os.path.isdir(self.o.inflight):
                        try:
                            os.mkdir(self.o.inflight)
                            os.chmod(self.o.inflight, self.o.chmod_dir)
                        except:
                            pass
                    new_inflight_path = self.o.inflight + new_file
                elif self.o.inflight[0] == '.':
                    new_inflight_path = new_file + self.o.inflight
            else:
                #inflight is interval: minimum the age of the source file, as per message.
                logger.error('interval inflight setting: %s, not for remote.' %
                             self.o.inflight)
                # FIXME... what to do?
                msg_set_report(msg, 503, "invalid reception settings.")
                self.worklist.rejected.append(msg)
                continue

            msg['new_inflight_path'] = new_inflight_path
            msg['new_path'] = new_path

            msg['_deleteOnPost'] |= set(['new_path'])
            msg['_deleteOnPost'] |= set(['new_inflight_path'])

            # assert new_inflight_path is set.

            if os.path.exists(msg['new_inflight_path']):
                if self.o.inflight:
                    #FIXME: if mtime > 5 minutes, perhaps rm it, and continue? what if transfer crashed?
                    logger.warning(
                        'inflight file already exists. race condition, deferring transfer of %s'
                        % msg['new_path'])
                    self.worklist.failed.append(msg)
                    continue
                # overwriting existing file.

            # FIXME: decision of whether to download, goes here.
            if os.path.isfile(new_path):
                if not self.o.overwrite:
                    msg_set_report(msg, 204, "not overwriting existing files.")
                    self.worklist.rejected.append(msg)
                    continue

                if not self.file_should_be_downloaded(msg):
                    msg_set_report(
                        msg, 304, "Not modified 3 - (compared to local file)")
                    self.worklist.rejected.append(msg)
                    continue

            # download content
            if 'content' in msg.keys():
                if self.write_inline_file(msg):
                    msg_set_report(msg, 201,
                                   "Download successful (inline content)")
                    self.worklist.ok.append(msg)
                else:
                    msg_set_report(msg, 503, "failed to write inline content")
                    self.worklist.rejected.append(msg)
            else:
                parsed_url = urllib.parse.urlparse(msg['baseUrl'])
                self.scheme = parsed_url.scheme

                i = 1
                while i <= self.o.attempts:

                    if i > 1:
                        logger.warning("downloading again, attempt %d" % i)

                    ok = self.download(msg, self.o)
                    if ok:
                        logger.info("downloaded ok: %s" % new_path)
                        msg_set_report(msg, 201, "Download successful")
                        self.worklist.ok.append(msg)
                        break
                    else:
                        logger.info("warning downloaded attempt %d failed: %s" % ( i, new_path) )
                    i = i + 1

                if not ok:
                    logger.error("gave up downloading for now")
                    self.worklist.failed.append(msg)
                # FIXME: file reassembly missing?
                #if self.inplace : file_reassemble(self)

        self.worklist.incoming = []

    # v2 sr_util.py ... generic sr_transport imported here...

    # generalized download...
    def download(self, msg, options):

        self.o = options

        logger.debug("%s_transport download" % self.scheme)

        token = msg['relPath'].split('/')
        cdir = '/' + '/'.join(token[:-1])
        remote_file = token[-1]
        urlstr = msg['baseUrl'] + '/' + msg['relPath']
        new_inflight_path = ''

        new_dir = msg['new_dir']
        new_file = msg['new_file']

        try:
            curdir = os.getcwd()
        except:
            curdir = None

        if curdir != new_dir:
            # make sure directory exists, create it if not
            if not os.path.isdir(new_dir):
                try:
                    os.makedirs(new_dir, 0o775, True)
                except Exception as ex:
                    logger.warning("making %s: %s" % (new_dir, ex))
                    logger.debug('Exception details:', exc_info=True)
            os.chdir(new_dir)

        try:
            options.destination = msg['baseUrl']

            if (not (self.scheme in self.proto)) or \
               (self.proto[self.scheme] is None) or not self.proto[self.scheme].check_is_connected():

                logger.debug("%s_transport download connects" % self.scheme)
                self.proto[self.scheme] = sarracenia.transfer.Transfer.factory(
                    self.scheme, self.o)
                logger.debug("HOHO proto %s " % type(self.proto))
                ok = self.proto[self.scheme].connect()
                if not ok:
                    self.proto[self.scheme] = None
                    return False
                logger.debug('connected')

            #=================================
            # if parts, check that the protol supports it
            #=================================

            #if not hasattr(proto,'seek') and ('blocks' in msg) and ( msg['blocks']['method'] == 'inplace' ):
            #   logger.error("%s, inplace part file not supported" % self.scheme)
            #   return False

            cwd = None
            if hasattr(self.proto[self.scheme], 'getcwd'):
                cwd = self.proto[self.scheme].getcwd()

            logger.debug(" proto %s " % type(self.proto[self.scheme]))
            if cwd != cdir:
                logger.debug("%s_transport download cd to %s" %
                             (self.scheme, cdir))
                self.proto[self.scheme].cd(cdir)

            remote_offset = 0
            if ('blocks' in msg) and (msg['blocks']['method'] == 'inplace'):
                remote_offset = msg['offset']

            if 'size' in msg:
                block_length = msg['size']
                str_range = ''
                if ('blocks' in msg) and (
                        msg['blocks']['method'] == 'inplace'):
                    block_length = msg['blocks']['size']
                    str_range = 'bytes=%d-%d' % (remote_offset, remote_offset +
                                                 block_length - 1)

            #download file

            logger.debug('Beginning fetch of %s %s into %s %d-%d' %
                         (urlstr, str_range, new_file, msg['local_offset'],
                          msg['local_offset'] + block_length - 1))

            # FIXME  locking for i parts in temporary file ... should stay lock
            # and file_reassemble... take into account the locking

            self.proto[self.scheme].set_sumalgo(msg['integrity']['method'])

            if options.inflight == None or (
                ('blocks' in msg) and (msg['blocks']['method'] == 'inplace')):
                new_inflight_path = new_file
            elif type(options.inflight) == str:
                if options.inflight == '.':
                    new_inflight_path = '.' + new_file
                elif options.inflight[-1] == '/':
                    try:
                        os.mkdir(options.inflight)
                        os.chmod(options.inflight, options.chmod_dir)
                    except:
                        pass
                    new_inflight_path = options.inflight + new_file
                elif options.inflight[0] == '.':
                    new_inflight_path = new_file + options.inflight
            else:
                logger.error('inflight setting: %s, not for remote.' %
                             options.inflight)

            logger.debug( "hasattr=%s, thresh=%d, len=%d, remote_off=%d, local_off=%d " % \
                ( hasattr( self.proto[self.scheme], 'getAccelerated'),  \
                self.o.accel_threshold, block_length, remote_offset,  msg['local_offset'] ) )

            accelerated = hasattr( self.proto[self.scheme], 'getAccelerated') and \
                (self.o.accel_threshold > 0 ) and (block_length > self.o.accel_threshold) and \
                (remote_offset == 0) and ( msg['local_offset'] == 0)

            if accelerated:
                len_written = self.proto[self.scheme].getAccelerated(
                    msg, remote_file, new_inflight_path, block_length)
            else:
                self.proto[self.scheme].set_path(new_inflight_path)
                len_written = self.proto[self.scheme].get(
                    msg, remote_file, new_inflight_path, remote_offset,
                    msg['local_offset'], block_length)

            if (len_written == block_length):
                if accelerated:
                    self.proto[self.scheme].update_file(new_inflight_path)
                if (new_inflight_path != new_file):
                    if os.path.isfile(new_file):
                        os.remove(new_file)
                    os.rename(new_inflight_path, new_file)
            else:
                logger.error(
                    'incomplete download only %d of expected %d bytes for %s' %
                    (len_written, block_length, new_inflight_path))
                msg['size'] = len_written

            msg['onfly_checksum'] = self.proto[self.scheme].get_sumstr()
            msg['data_checksum'] = self.proto[self.scheme].data_checksum

            msg['_deleteOnPost'] |= set(['onfly_checksum'])

            msg['_deleteOnPost'] |= set(['data_checksum'])

            # fix message if no partflg (means file size unknown until now)
            #if not 'blocks' in msg:
            #    #msg['size'] = self.proto[self.scheme].fpos ... fpos not set when accelerated.

            # fix permission
            self.set_local_file_attributes(new_file, msg)

            if options.delete and hasattr(self.proto[self.scheme], 'delete'):
                try:
                    self.proto[self.scheme].delete(remote_file)
                    logger.debug('file deleted on remote site %s' %
                                 remote_file)
                except:
                    logger.error('unable to delete remote file %s' %
                                 remote_file)
                    logger.debug('Exception details: ', exc_info=True)

            if (len_written != block_length):
                return False

        except:
            #closing on problem
            try:
                self.proto[self.scheme].close()
                self.cdir = None
                self.proto[self.scheme] = None
            except:
                pass

            logger.debug('Exception details: ', exc_info=True)
            if os.path.isfile(new_inflight_path):
                os.remove(new_inflight_path)
            return False
        return True

    # generalized send...
    def send(self, msg, options):
        self.o = options
        logger.debug("%s_transport destination: %s " %
                     (self.scheme, self.o.destination))
        logger.debug("%s_transport send %s %s" %
                     (self.scheme, msg['new_dir'], msg['new_file']))

        if self.o.baseDir:
            local_path = self.o.baseDir + '/' + msg['relPath']
        else:
            local_path = '/' + msg['relPath']

        local_dir = os.path.dirname(local_path).replace('\\', '/')
        local_file = os.path.basename(local_path).replace('\\', '/')
        new_dir = msg['new_dir'].replace('\\', '/')
        new_file = msg['new_file'].replace('\\', '/')
        new_inflight_path = None

        try:
            curdir = os.getcwd()
        except:
            curdir = None

        if curdir != local_dir:
            os.chdir(local_dir)

        try:

            if (not (self.scheme in self.proto)) or \
               (self.proto[self.scheme] is None) or not self.proto[self.scheme].check_is_connected():
                logger.debug("%s_transport send connects" % self.scheme)
                self.proto[self.scheme] = sarracenia.transfer.Transfer.factory(
                    self.scheme, options)
                ok = self.proto[self.scheme].connect()
                if not ok: return False
                self.cdir = None

            #=================================
            # if parts, check that the protol supports it
            #=================================

            if not hasattr(self.proto[self.scheme],
                           'seek') and ('blocks' in msg) and (
                               msg['blocks']['method'] == 'inplace'):
                logger.error("%s, inplace part file not supported" %
                             self.scheme)
                return False

            #=================================
            # if umask, check that the protocol supports it ...
            #=================================

            inflight = options.inflight
            if not hasattr(self.proto[self.scheme],
                           'umask') and options.inflight == 'umask':
                logger.warning("%s, umask not supported" % self.scheme)
                inflight = None

            #=================================
            # if renaming used, check that the protocol supports it ...
            #=================================

            if not hasattr(self.proto[self.scheme],
                           'rename') and options.inflight.startswith('.'):
                logger.warning("%s, rename not supported" % self.scheme)
                inflight = None

            #=================================
            # remote set to new_dir
            #=================================

            cwd = None
            if hasattr(self.proto[self.scheme], 'getcwd'):
                cwd = self.proto[self.scheme].getcwd()

            if cwd != new_dir:
                logger.debug("%s_transport send cd to %s" %
                             (self.scheme, new_dir))
                self.proto[self.scheme].cd_forced(775, new_dir)

            #=================================
            # delete event
            #=================================

            if msg['integrity']['method'] == 'remove':
                if hasattr(self.proto[self.scheme], 'delete'):
                    logger.debug("message is to remove %s" % new_file)
                    self.proto[self.scheme].delete(new_file)
                    return True
                logger.error("%s, delete not supported" % self.scheme)
                return False

            #=================================
            # link event
            #=================================

            if 'link' in msg:
                if hasattr(self.proto[self.scheme], 'symlink'):
                    logger.debug("message is to link %s to: %s" %
                                 (new_file, msg['link']))
                    self.proto[self.scheme].symlink(msg['link'], new_file)
                    return True
                logger.error("%s, symlink not supported" % self.scheme)
                return False

            #=================================
            # send event
            #=================================

            # the file does not exist... warn, sleep and return false for the next attempt
            if not os.path.exists(local_file):
                logger.warning(
                    "product collision or base_dir not set, file %s does not exist"
                    % local_file)
                time.sleep(0.01)
                return False

            offset = 0
            if ('blocks' in msg) and (msg['blocks']['method'] == 'inplace'):
                offset = msg['offset']

            new_offset = msg['local_offset']

            if 'size' in msg:
                block_length = msg['size']
                str_range = ''
                if ('blocks' in msg) and (
                        msg['blocks']['method'] == 'inplace'):
                    block_length = msg['blocks']['size']
                    str_range = 'bytes=%d-%d' % (remote_offset, remote_offset +
                                                 block_length - 1)

            str_range = ''
            if ('blocks' in msg) and (msg['blocks']['method'] == 'inplace'):
                str_range = 'bytes=%d-%d' % (offset, offset + msg['size'] - 1)

            #upload file

            logger.debug( "hasattr=%s, thresh=%d, len=%d, remote_off=%d, local_off=%d " % \
                ( hasattr( self.proto[self.scheme], 'putAccelerated'),  \
                self.o.accel_threshold, block_length, new_offset,  msg['local_offset'] ) )

            accelerated = hasattr( self.proto[self.scheme], 'putAccelerated') and \
                (self.o.accel_threshold > 0 ) and (block_length > self.o.accel_threshold) and \
                (new_offset == 0) and ( msg['local_offset'] == 0)


            if inflight == None or (('blocks' in msg) and (msg['blocks']['method'] != 'inplace')):
                if accelerated:
                    len_written = self.proto[self.scheme].putAccelerated( msg, local_file, new_file)
                else:
                    len_written = self.proto[self.scheme].put(msg, local_file, new_file)
            elif (('blocks' in msg) and (msg['blocks']['method'] == 'inplace')):
                self.proto[self.scheme].put(msg, local_file, new_file, offset,
                                            new_offset, msg['size'])
            elif inflight == '.':
                new_inflight_path = '.' + new_file
                if accelerated:
                    len_written = self.proto[self.scheme].putAccelerated( msg, local_file, new_inflight_path)
                else:
                    len_written = self.proto[self.scheme].put(msg, local_file, new_inflight_path)
                self.proto[self.scheme].rename(new_inflight_path, new_file)
            elif inflight[0] == '.':
                new_inflight_path = new_file + inflight
                if accelerated:
                    len_written = self.proto[self.scheme].putAccelerated( msg, local_file, new_inflight_path)
                else:
                    len_written = self.proto[self.scheme].put(msg, local_file, new_inflight_path)
                proto.rename(new_inflight_path, new_file)
            elif options.inflight[-1] == '/':
                try:
                    self.proto[self.scheme].cd_forced(
                        775, new_dir + '/' + options.inflight)
                    self.proto[self.scheme].cd_forced(775, new_dir)
                except:
                    pass
                new_inflight_path = options.inflight + new_file
                if accelerated:
                    len_written = self.proto[self.scheme].putAccelerated( msg, local_file, new_inflight_path)
                else:
                    len_written = self.proto[self.scheme].put(msg, local_file, new_inflight_path)
                self.proto[self.scheme].rename(new_inflight_path, new_file)
            elif inflight == 'umask':
                self.proto[self.scheme].umask()
                if accelerated:
                    len_written = self.proto[self.scheme].putAccelerated( msg, local_file, new_file)
                else:
                    len_written = self.proto[self.scheme].put(msg, local_file, new_file)
                self.proto[self.scheme].put(msg, local_file, new_file)

            # fix permission

            self.set_remote_file_attributes(self.proto[self.scheme], new_file,
                                            msg)

            logger.info('Sent: %s %s into %s/%s %d-%d' %
                        (local_path, str_range, new_dir, new_file, offset,
                         offset + msg['size'] - 1))

            return True

        except Exception as err:

            #removing lock if left over
            if new_inflight_path != None and hasattr(self.proto[self.scheme],
                                                     'delete'):
                try:
                    self.proto[self.scheme].delete(new_inflight_path)
                except:
                    pass

            #closing on problem
            try:
                self.proto[self.scheme].close()
                self.cdir = None
                self.proto[self.scheme] = None

            except:
                pass

            logger.error("Delivery failed %s" % msg['new_dir'] + '/' +
                         msg['new_file'])
            logger.debug('Exception details: ', exc_info=True)

            return False

    # set_local_file_attributes
    def set_local_file_attributes(self, local_file, msg):
        """
           after a file has been written, restore permissions and ownership if necessary.
        """
        #logger.debug("sr_transport set_local_file_attributes %s" % local_file)

        # if the file is not partitioned, the the onfly_checksum is for the whole file.
        # cache it here, along with the mtime.
        if (not 'blocks' in msg):
            if 'onfly_checksum' in msg:
                sumstr = msg['onfly_checksum']
            else:
                sumstr = msg['integrity']

            x = sarracenia.filemetadata.FileMetadata(local_file)
            x.set('integrity', sumstr)

            if self.o.preserve_time and 'mtime' in msg and msg['mtime']:
                x.set('mtime', msg['mtime'])
            else:
                st = os.stat(local_file)
                mtime = timeflt2str(st.st_mtime)
                x.set('mtime', mtime)
            x.persist()

        mode = 0
        if self.o.preserve_mode and 'mode' in msg:
            try:
                mode = int(msg['mode'], base=8)
            except:
                mode = 0
            if mode > 0:
                os.chmod(local_file, mode)

        if mode == 0 and self.o.chmod != 0:
            os.chmod(local_file, self.o.chmod)

        if self.o.preserve_time and 'mtime' in msg and msg['mtime']:
            mtime = timestr2flt(msg['mtime'])
            atime = mtime
            if 'atime' in msg and msg['atime']:
                atime = timestr2flt(msg['atime'])
            os.utime(local_file, (atime, mtime))

    # set_remote_file_attributes
    def set_remote_file_attributes(self, proto, remote_file, msg):
        #logger.debug("sr_transport set_remote_file_attributes %s" % remote_file)

        if hasattr(proto, 'chmod'):
            mode = 0
            if self.o.preserve_mode and 'mode' in msg:
                try:
                    mode = int(msg['mode'], base=8)
                except:
                    mode = 0
                if mode > 0:
                    try:
                        proto.chmod(mode, remote_file)
                    except:
                        pass

            if mode == 0 and self.o.chmod != 0:
                try:
                    proto.chmod(self.o.chmod, remote_file)
                except:
                    pass

        if hasattr(proto, 'chmod'):
            if self.o.preserve_time and 'mtime' in msg and msg['mtime']:
                mtime = timestr2flt(msg['mtime'])
                atime = mtime
                if 'atime' in msg and msg['atime']:
                    atime = timestr2flt(msg['atime'])
                try:
                    proto.utime(remote_file, (atime, mtime))
                except:
                    pass

    # v2 sr_util sr_transport stuff. end.

    # imported from v2: sr_sender/doit_send

    def do_send(self):
        """
        """
        if self.o.notify_only:
            self.worklist.ok = self.worklist.incoming
            self.worklist.incoming = []
            return

        for msg in self.worklist.incoming:

            #=================================
            # check message for local file
            #=================================

            if msg['baseUrl'] != 'file:/':
                logger.error("protocol should be 'file:' message ignored")
                self.worklist.rejected.append(msg)
                continue

            #=================================
            # proceed to send :  has to work
            #=================================

            # N attempts to send

            i = 1
            while i <= self.o.attempts:
                if i != 1:
                    logger.warning("sending again, attempt %d" % i)

                ok = self.send(msg, self.o)
                logger.info("ok: %s" % ok)
                if ok:
                    self.worklist.ok.append(msg)
                    break

                i = i + 1
            if not ok:
                self.worklist.failed.append(msg)
        self.worklist.incoming= []

import sarracenia.flow.poll
import sarracenia.flow.post
import sarracenia.flow.report
import sarracenia.flow.sarra
import sarracenia.flow.sender
import sarracenia.flow.shovel
import sarracenia.flow.subscribe
import sarracenia.flow.watch
import sarracenia.flow.winnow
