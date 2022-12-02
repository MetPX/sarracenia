import copy
import importlib
import logging
import os
import re

# v3 plugin architecture...
import sarracenia.flowcb
import sarracenia.integrity
import sarracenia.transfer

import stat
import time
import types
import urllib.parse

import sarracenia

import sarracenia.filemetadata

# for v2 subscriber routines...
import json, os, sys, time

from sys import platform as _platform

from base64 import b64decode, b64encode
from mimetypes import guess_type
# end v2 subscriber

from sarracenia import nowflt

logger = logging.getLogger(__name__)

allFileEvents = set(['create', 'delete', 'link', 'modify'])

default_options = {
    'accelThreshold': 0,
    'acceptUnmatched': False,
    'attempts': 3,
    'batch': 100,
    'byteRateMax': None,
    'discard': False,
    'download': False,
    'fileEvents': allFileEvents,
    'housekeeping': 300,
    'logReject': False,
    'logFormat':
    '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s',
    'logLevel': 'info',
    'mirror': True,
    'permCopy': True,
    'timeCopy': True,
    'messageCountMax': 0,
    'messageRateMax': 0,
    'messageRateMin': 0,
    'sleep': 0.1,
    'topicPrefix': ['v03'],
    'vip': None
}

if sarracenia.extras['vip']['present']:
    import netifaces


class Flow:
    """
      Implement the General Algorithm from the Concepts Guide.

      All of the component types (e.g. poll, subscribe, sarra, winnow, shovel ) are implemented 
      as sub-classes of Flow. The constructor/factory accept a configuration 
      (sarracenia.config.Config class) with all the settings in it.

      This class takes care of starting up, running with callbacks, and clean shutdown.

      need to know whether to sleep between passes  
      o.sleep - an interval (floating point number of seconds)
      o.housekeeping - 

      A flow processes worklists of messages

      worklist given to callbacks...

      * worklist.incoming --> new messages to continue processing
      * worklist.ok       --> successfully processed
      * worklist.rejected --> messages to not be further processed.
      * worklist.failed   --> messages for which processing failed.
      * worklist.dirrectories_ok --> directories created.

      Initially all messages are placed in incoming.
      if a callback decides:
      
      - a message is not relevant, it is moved to rejected.
      - all processing has been done, it moves it to ok.
      - an operation failed and it should be retried later, move to retry

      callbacks must not remove messages from all worklists, re-classify them.
      it is necessary to put rejected messages in the appropriate worklist
      so they can be acknowledged as received.

      interesting data structure:
      self.plugins  -- dict of modular functionality metadata. 

      * self.plugins[ "load" ] contains a list of (v3) flow_callbacks to load.

      * self.plugins[ entry_point ]  - one for each invocation times of callbacks. examples:
        "on_start", "after_accept", etc...  contains routines to run at each *entry_point*
     
    """
    @staticmethod
    def factory(cfg):

        if cfg.flowMain:
              flowMain=cfg.flowMain
        else:
              flowMain=cfg.component

        for sc in Flow.__subclasses__():
            if flowMain == sc.__name__.lower():
                return sc(cfg)

        if cfg.component == 'flow':
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

        if 'sarracenia.flow.Flow' in self.o.settings and 'logLevel' in self.o.settings['sarracenia.flow.Flow']:
            logger.setLevel(
                getattr(
                    logging,
                    self.o.settings['sarracenia.flow.Flow']['logLevel'].upper()))
            logger.warning('FIXME! class specific logLevel Override')
        else:
            logger.setLevel(getattr(logging, self.o.logLevel.upper()))

        if not hasattr(self.o, 'post_topicPrefix'):
            self.o.post_topicPrefix = self.o.topicPrefix

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
        self.worklist.directories_ok = []

        # for poll only, mark if we are catching up on posted messages
        #
        self.worklist.poll_catching_up = False

        # Witness the creation of this list
        self.plugins['load'] = self.o.plugins_early + [
            'sarracenia.flowcb.retry.Retry',
            'sarracenia.flowcb.housekeeping.resources.Resources'
        ]

        # open cache, get masks.
        if self.o.nodupe_ttl > 0:
            # prepend...
            self.plugins['load'].append('sarracenia.flowcb.nodupe.NoDupe')

        # FIXME: open retry

        # transport stuff.. for download, get, put, etc...
        self.scheme = None
        self.cdir = None
        self.proto = {}

        # initialize plugins.
        if hasattr(self.o, 'v2plugins') and len(self.o.v2plugins) > 0:
            self.plugins['load'].append(
                'sarracenia.flowcb.v2wrapper.V2Wrapper')

        self.plugins['load'].extend(self.o.plugins_late)

        # metrics - dictionary with names of plugins as the keys
        self.metrics = {}

    def loadCallbacks(self, plugins_to_load):

        for m in self.o.imports:
            try:
                importlib.import_module(m)
            except Exception as ex:
                logger.critical( f"python module import {m} load failed: {ex}" )
                logger.debug( "details:", exc_info=True )
                return False

        logger.info('flowCallback plugins to load: %s' % (plugins_to_load))
        for c in plugins_to_load:
            try:
                plugin = sarracenia.flowcb.load_library(c, self.o)
            except Exception as ex:
                logger.critical( f"flowCallback plugin {c} did not load: {ex}" )
                logger.debug( "details:", exc_info=True )
                return False

            logger.debug('flowCallback plugin loading: %s an instance of: %s' % (c, plugin))
            for entry_point in sarracenia.flowcb.entry_points:
                if hasattr(plugin, entry_point):
                    fn = getattr(plugin, entry_point)
                    if callable(fn):
                        logger.debug('registering %s/%s' % (c, entry_point))
                        if entry_point in self.plugins:
                            self.plugins[entry_point].append(fn)
                        else:
                            self.plugins[entry_point] = [fn]

            if not (hasattr(plugin, 'registered_as')
                    and callable(getattr(plugin, 'registered_as'))):
                continue

        logger.debug('complete')
        self.o.check_undeclared_options()
        return True

    def _runCallbacksWorklist(self, entry_point):

        if hasattr(self, 'plugins') and (entry_point in self.plugins):
            for p in self.plugins[entry_point]:
                if self.o.logLevel.lower() == 'debug' :
                    p(self.worklist)
                else:
                    try:
                        p(self.worklist)
                    except Exception as ex:
                        logger.error( f'flowCallback plugin {p}/{entry_point} crashed: {ex}' )
                        logger.debug( "details:", exc_info=True )

    def _runCallbacksTime(self, entry_point):
        for p in self.plugins[entry_point]:
            if self.o.logLevel.lower() == 'debug' :
                p()
            else:
                try:
                    p()
                except Exception as ex:
                    logger.error( f'flowCallback plugin {p}/{entry_point} crashed: {ex}' )
                    logger.debug( "details:", exc_info=True )

    def _runCallbackMetrics(self):
        """Collect metrics from plugins with a ``metrics_report`` entry point.

        Expects the plugin to return a dictionary containing metrics, which is saved to ``self.metrics[plugin_name]``.
        """
        for p in self.plugins["metrics_report"]:
            if self.o.logLevel.lower() == 'debug' :
                plugin_name = p.__qualname__.replace('.metrics_report', '')
                self.metrics[plugin_name] = p()
            else:
                try:
                    plugin_name = p.__qualname__.replace('.metrics_report', '')
                    self.metrics[plugin_name] = p()
                except Exception as ex:
                    logger.error( f'flowCallback plugin {p}/metrics_report crashed: {ex}' )
                    logger.debug( "details:", exc_info=True )

    def has_vip(self):

        if not sarracenia.extras['vip']['present']: return True

        # no vip given... standalone always has vip.
        if self.o.vip == None:
            return True

        try:
            for i in netifaces.interfaces():
                for a in netifaces.ifaddresses(i):
                    j = 0
                    while (j < len(netifaces.ifaddresses(i)[a])):
                        if self.o.vip in netifaces.ifaddresses(i)[a][j].get(
                                'addr'):
                            return True
                        j += 1
        except Exception as ex:
            logger.error(
                'error while looking for interfaces to compare with vip (%s): '
                % (self.o.vip, ex))
            logger.debug('Exception details: ', exc_info=True)

        return False

    def reject(self, m, code, reason) -> None:
        """
            reject a message.
        """
        self.worklist.rejected.append(m)
        m.setReport(code, reason)

    def please_stop(self) -> None:
        logger.info(
            f'ok, telling {len(self.plugins["please_stop"])} callbacks about it.'
        )
        self._runCallbacksTime('please_stop')

        if self.o.please_stop_immediately:
            sys.exit(0)

        self._stop_requested = True


    def close(self) -> None:

        self._runCallbacksTime('on_stop')
        logger.info(
            f'flow/close completed cleanly pid: {os.getpid()} {self.o.component}/{self.o.config} instance: {self.o.no}'
        )

    def ack(self, mlist) -> None:
        if "ack" in self.plugins:
            for p in self.plugins["ack"]:
                if self.o.logLevel.lower() == 'debug' :
                    p(mlist)
                else:
                    try:
                        p(mlist)
                    except Exception as ex:
                        logger.error( f'flowCallback plugin {p}/ack crashed: {ex}' )
                        logger.debug( "details:", exc_info=True )

    def run(self):
        """
          This is the core routine of the algorithm, with most important data driven
          loop in it. This implements the General Algorithm (as described in the Concepts Explanation Guide) 
          check if stop_requested once in a while, but never return otherwise.
        """

        if not self.loadCallbacks(self.plugins['load']+self.o.destfn_scripts):
           return

        logger.debug("working directory: %s" % os.getcwd())

        next_housekeeping = nowflt() + self.o.housekeeping

        current_rate = 0
        total_messages = 1
        start_time = nowflt()
        had_vip = False
        current_sleep = self.o.sleep
        last_time = start_time

        if self.o.logLevel == 'debug':
            logger.debug("options:")
            self.o.dump()

        logger.info("callbacks loaded: %s" % self.plugins['load'])
        logger.info(
            f'pid: {os.getpid()} {self.o.component}/{self.o.config} instance: {self.o.no}'
        )
        self._runCallbacksTime(f'on_start')

        spamming = True
        last_gather_len = 0
        stopping = False

        while True:

            if self._stop_requested:
                if stopping:
                    logger.info('clean stop from run loop')
                    self.close()
                    break
                else:
                    logger.info(
                        'starting last pass (without gather) through loop for cleanup.'
                    )
                    stopping = True

            self.have_vip = self.has_vip()
            if (self.o.component == 'poll') or self.have_vip:

                if ( self.o.messageRateMax > 0 ) and (current_rate > 0.8*self.o.messageRateMax ):
                    logger.info("current_rate (%.2f) vs. messageRateMax(%.2f)) " % (current_rate, self.o.messageRateMax))

                self.worklist.incoming = []

                if not stopping:
                    self.gather()
                else:
                    self.worklist.incoming = []

                last_gather_len = len(self.worklist.incoming)
                if (last_gather_len == 0):
                    spamming = True
                else:
                    current_sleep = self.o.sleep
                    spamming = False

                self.filter()

                self._runCallbacksWorklist('after_accept')

                logger.debug(
                    'B filtered incoming: %d, ok: %d (directories: %d), rejected: %d, failed: %d stop_requested: %s'
                    % (len(self.worklist.incoming), len(
                        self.worklist.ok), len(self.worklist.directories_ok),
                       len(self.worklist.rejected), len(
                           self.worklist.failed), self._stop_requested))

                self.ack(self.worklist.ok)
                self.worklist.ok = []
                self.ack(self.worklist.rejected)
                self.worklist.rejected = []
                self.ack(self.worklist.failed)

                # this for duplicate cache synchronization.
                if self.worklist.poll_catching_up:
                    self.ack(self.worklist.incoming)
                    self.worklist.incoming = []
                    continue

                if (self.o.component == 'poll') and not self.have_vip:
                    if had_vip:
                        logger.info("now passive on vip %s" % self.o.vip )
                        had_vip=False
                else:
                    if not had_vip:
                        logger.info("now active on vip %s" % self.o.vip )
                        had_vip=True

                    # normal processing, when you are active.
                    self.do()

                    # need to acknowledge here, because posting will delete message-id
                    self.ack(self.worklist.ok)
                    self.ack(self.worklist.rejected)
                    self.ack(self.worklist.failed)

                    # adjust message after action is done, but before 'after_work' so adjustment is possible.
                    for m in self.worklist.ok:
                        if ('new_baseUrl' in m) and (m['baseUrl'] !=
                                                     m['new_baseUrl']):
                            m['baseUrl'] = m['new_baseUrl']
                        if ('new_retPath' in m) :
                            m['retPath'] = m['new_retPath']
                        if ('new_relPath' in m) and (m['relPath'] !=
                                                     m['new_relPath']):
                            m['relPath'] = m['new_relPath']
                            m['subtopic'] = m['new_subtopic']
                        if ('version' in m) and ( m['version'] != 
                                                  m['post_version']):
                            m['version'] = m['post_version']

                    self._runCallbacksWorklist('after_work')

                    self.ack(self.worklist.rejected)
                    self.worklist.rejected = []
                    self.ack(self.worklist.failed)

                    if len(self.plugins["post"]) > 0:
                        self.post()
                        self._runCallbacksWorklist('after_post')

                    self.report()

                    self._runCallbackMetrics()

                    self.worklist.ok = []
                    self.worklist.directories_ok = []
                    self.worklist.failed = []

            now = nowflt()
            run_time = now - start_time
            total_messages += last_gather_len

            if (self.o.messageCountMax > 0) and (total_messages >=
                                                 self.o.messageCountMax):
                self.please_stop()

            current_rate = total_messages / run_time
            elapsed = now - last_time

            if (last_gather_len == 0) and (self.o.sleep < 0):
                if (self.o.retryEmptyBeforeExit and "Retry" in self.metrics
                    and self.metrics['Retry']['msgs_in_post_retry'] > 0):
                    logger.info("Not exiting because there are still messages in the post retry queue.")
                    # Sleep for a while. Messages can't be retried before housekeeping has run...
                    current_sleep = 60
                else:
                    self.please_stop()

            if spamming and (current_sleep < 5):
                current_sleep *= 2

            # Run housekeeping based on time, and before stopping to ensure it's run at least once
            if now > next_housekeeping or stopping:
                logger.info(
                    f'on_housekeeping pid: {os.getpid()} {self.o.component}/{self.o.config} instance: {self.o.no}'
                )
                self._runCallbacksTime('on_housekeeping')
                next_housekeeping = now + self.o.housekeeping

            if (self.o.messageRateMin > 0) and (current_rate <
                                                self.o.messageRateMin):
                logger.warning("receiving below minimum message rate")

            if (self.o.messageRateMax > 0) and (current_rate >=
                                                self.o.messageRateMax):
                stime = 1 + 2 * ((current_rate - self.o.messageRateMax) /
                                 self.o.messageRateMax)
                logger.info(
                    "current_rate/2 (%.2f) above messageRateMax(%.2f): throttling"
                    % (current_rate, self.o.messageRateMax))
            else:
                logger.debug( f" not throttling: limit: {self.o.messageRateMax} " )
                stime = 0

            if (current_sleep > 0):
                if elapsed < current_sleep:
                    stime += current_sleep - elapsed
                    if stime > 60:  # if sleeping for a long time, debug output is good...
                        logger.debug(
                            "sleeping for more than 60 seconds: %.2f seconds. Elapsed since wakeup: %.2f Sleep setting: %.2f "
                            % (stime, elapsed, self.o.sleep))
                else:
                    logger.debug('worked too long to sleep!')
                    last_time = now
                    continue

            if not self._stop_requested and (stime > 0):
                try:
                    logger.debug('sleeping for stime: %.2f seconds' % stime)
                    time.sleep(stime)
                except:
                    logger.info("flow woken abnormally from sleep")
                    self.please_stop()

                last_time = now


    def sundew_getDestInfos(self, msg, currentFileOption, filename):
        """
        modified from sundew client

        WHATFN         -- First part (':') of filename 
        HEADFN         -- Use first 2 fields of filename
        NONE           -- Use the entire filename
        TIME or TIME:  -- TIME stamp appended
        DESTFN=fname   -- Change the filename to fname

        ex: mask[2] = 'NONE:TIME'
        """
        if currentFileOption == None: return filename

        timeSuffix = ''
        satnet = ''
        parts = filename.split(':')
        firstPart = parts[0]

        if 'sundew_extension' in msg.keys():
            parts = [parts[0]] + msg['sundew_extension'].split(':')
            filename = ':'.join(parts)

        destFileName = filename

        for spec in currentFileOption.split(':'):
            if spec == 'WHATFN':
                destFileName = firstPart
            elif spec == 'HEADFN':
                headParts = firstPart.split('_')
                if len(headParts) >= 2:
                    destFileName = headParts[0] + '_' + headParts[1]
                else:
                    destFileName = headParts[0]
            elif spec == 'SENDER' and 'SENDER=' in filename:
                i = filename.find('SENDER=')
                if i >= 0: destFileName = filename[i + 7:].split(':')[0]
                if destFileName[-1] == ':': destFileName = destFileName[:-1]
            elif spec == 'NONE':
                if 'SENDER=' in filename:
                    i = filename.find('SENDER=')
                    destFileName = filename[:i]
                else:
                    if len(parts) >= 6:
                        # PX default behavior : keep 6 first fields
                        destFileName = ':'.join(parts[:6])
                        #  PDS default behavior  keep 5 first fields
                        if len(parts[4]) != 1:
                            destFileName = ':'.join(parts[:5])
                # extra trailing : removed if present
                if destFileName[-1] == ':': destFileName = destFileName[:-1]
            elif spec == 'NONESENDER':
                if 'SENDER=' in filename:
                    i = filename.find('SENDER=')
                    j = filename.find(':', i)
                    destFileName = filename[:i + j]
                else:
                    if len(parts) >= 6:
                        # PX default behavior : keep 6 first fields
                        destFileName = ':'.join(parts[:6])
                        #  PDS default behavior  keep 5 first fields
                        if len(parts[4]) != 1:
                            destFileName = ':'.join(parts[:5])
                # extra trailing : removed if present
                if destFileName[-1] == ':': destFileName = destFileName[:-1]
            elif re.compile('SATNET=.*').match(spec):
                satnet = ':' + spec
            elif re.compile('DESTFN=.*').match(spec):
                destFileName = spec[7:]
            elif re.compile('DESTFNSCRIPT=.*').match(spec):
                scriptclass = spec[13:].split('.')[-1]
                for dfm in self.plugins['destfn']:
                    if scriptclass == dfm.__qualname__.split('.')[0] :
                         destFileName = dfm(msg)
            elif spec == 'TIME':
                timeSuffix = ':' + time.strftime("%Y%m%d%H%M%S", time.gmtime())
                if 'pubTime' in msg:
                    timeSuffix = ":" + msg['pubTime'].split('.')[0]
                if 'pubTime' in msg:
                    timeSuffix = ":" + msg['pubtime'].split('.')[0]
                    timeSuffix = timeSuffix.replace('T', '')
                # check for PX or PDS behavior ...
                # if file already had a time extension keep his...
                if len(parts[-1]) == 14 and parts[-1][0] == '2':
                    timeSuffix = ':' + parts[-1]

            else:
                logger.error("Don't understand this DESTFN parameter: %s" %
                             spec)
                return (None, None)
        return destFileName + satnet + timeSuffix


    # ==============================================
    # how will the download file land on this server
    # with all options, this is really tricky
    # ==============================================

    def updateFieldsAccepted(self, msg, urlstr, pattern, maskDir,
                             maskFileOption, mirror, strip, pstrip, flatten) -> None:
        """
           Set new message fields according to values when the message is accepted.
           
           * urlstr: the urlstr being matched (baseUrl+relPath+sundew_extension)
           * pattern: the regex that was matched.
           * maskDir: the current directory to base the relPath from.
           * maskFileOption: filename option value (sundew compatibility options.)
           * strip: number of path entries to strip from the left side of the path.
           * pstrip: pattern strip regexp to apply instead of a count.
           * flatten: a character to replace path separators with toe change a multi-directory 
             deep file name into a single long file name
        """

        # relative path by default mirror
        if type(maskDir) is str:
            # trying to subtract maskDir if present in relPath...
            # occurs in polls a lot.
            if maskDir in msg['relPath']:
                relPath = '%s' % msg['relPath'].replace(maskDir, '', 1)

            # sometimes the same, just the leading / is missing.
            elif maskDir[1:] in msg['relPath']:
                relPath = '%s' % msg['relPath'].replace(maskDir[1:], '', 1)
            else:
                relPath = '%s' % msg['relPath']
        else:
            relPath = '%s' % msg['relPath']

        if self.o.baseUrl_relPath:
            u = urllib.parse.urlparse(msg['baseUrl'])
            relPath = u.path[1:] + '/' + relPath

        # FIXME... why the % ? why not just assign it to copy the value?
        if 'rename' in msg: relPath = '%s' % msg['rename']

        token = relPath.split('/')
        filename = token[-1]

        # if provided, strip (integer) ... strip N heading directories
        #         or  pstrip (pattern str) strip regexp pattern from relPath
        # cannot have both (see setting of option strip in sr_config)

        if strip > 0:

            if strip < len(token):
                token = token[strip:]

            # strip too much... keep the filename
            else:
                token = [filename]

            logger.info(' 015 token=%s fname=%s' %(token, filename) )
        # strip using a pattern

        elif pstrip:

            #MG FIXME Peter's wish to have replacement in pstrip (ex.:${SOURCE}...)

            relstrip = re.sub(pstrip, '', relPath, 1)

            if not filename in relstrip: relstrip = filename
            token = relstrip.split('/')

        # if flatten... we flatten relative path
        # strip taken into account

        if flatten != '/':
            filename = flatten.join(token)
            token[-1] = [filename]

        if maskFileOption is not None:
            filename = self.sundew_getDestInfos(msg, maskFileOption,
                                                       filename)
            token[-1] = [filename]

        # not mirroring

        if not mirror:
            token = [filename]

        # uses current dir

        #if self.o.currentDir : new_dir = self.o.currentDir
        if maskDir:
            new_dir = self.o.variableExpansion(maskDir, msg)
        else:
            new_dir = ''

        if self.o.baseDir:
            if new_dir:
                d = new_dir
            elif self.o.post_baseDir:
                d = self.o.variableExpansion(self.o.post_baseDir, msg)
            else:
                d = None

            if d:
                if 'fileOp' in msg:
                    for f in ['link', 'hlink', 'rename']:
                        if f in msg['fileOp']:
                             msg['fileOp'][f] = msg['fileOp'][f].replace(self.o.baseDir, d, 1)

        # add relPath

        if len(token) > 1:
            new_dir = new_dir + '/' + '/'.join(token[:-1])

        new_dir = self.o.variableExpansion(new_dir, msg)
        # resolution of sundew's dirPattern

        tfname = filename
        # when sr_sender did not derived from sr_subscribe it was always called
        new_dir = self.o.sundew_dirPattern(pattern, urlstr, tfname, new_dir)

        msg.updatePaths(self.o, new_dir, filename)



    def filter(self) -> None:

        logger.debug(
            'start len(incoming)=%d, rejected=%d' %
            (len(self.worklist.incoming), len(self.worklist.rejected)))
        filtered_worklist = []

        if hasattr(self.o, 'directory'):
            default_accept_directory = self.o.directory
        elif hasattr(self.o, 'post_baseDir'):
            default_accept_directory = self.o.post_baseDir
        elif hasattr(self.o, 'baseDir'):
            default_accept_directory = self.o.baseDir

        now = nowflt()
        for m in self.worklist.incoming:
            then = sarracenia.timestr2flt(m['pubTime'])
            lag = now - then
            if self.o.messageAgeMax != 0 and lag > self.o.messageAgeMax:
                self.reject(
                    m, 504,
                    "Excessive lag: %g sec. Skipping download of: %s, " %
                    (lag, m['new_file']))
                continue

            if 'fileOp' in m and 'rename' in m['fileOp']:
                url = self.o.variableExpansion(m['baseUrl'],
                                             m) + os.sep + m['fileOp']['rename']
                if 'sundew_extension' in m and url.count(":") < 1:
                    urlToMatch = url + ':' + m['sundew_extension']
                else:
                    urlToMatch = url
                oldname_matched = False
                for mask in self.o.masks:
                    pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask
                    if mask_regexp.match(urlToMatch):
                        oldname_matched = accepting
                        break

            url = self.o.variableExpansion(m['baseUrl'],
                                         m) + os.sep + m['relPath']
            if 'sundew_extension' in m and url.count(":") < 1:
                urlToMatch = url + ':' + m['sundew_extension']
            else:
                urlToMatch = url

            # apply masks for accept/reject options.
            matched = False
            for mask in self.o.masks:
                pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask

                if mask_regexp.match(urlToMatch):
                    matched = True
                    if not accepting:
                        if 'fileOp' in m and 'rename' in m['fileOp'] and oldname_matched:
                            # deletion rename case... need to accept with an extra field...
                            if not 'renameUnlink' in m:
                                m['renameUnlink'] = True
                                m['_deleteOnPost'] |= set(['renameUnlink'])
                            logger.debug("rename deletion 1 %s" %
                                         (m['fileOp']['rename']))
                        else:
                            self.reject(
                                m, 304, "mask=%s strip=%s url=%s" %
                                (str(mask), strip, urlToMatch))
                        break

                    self.updateFieldsAccepted(m, url, pattern, maskDir,
                                           maskFileOption, mirror, strip,
                                           pstrip, flatten)

                    filtered_worklist.append(m)
                    break

            if not matched:
                if 'fileOp' in m and ('rename' in m['fileOp']) and oldname_matched:
                    if not 'renameUnlink' in m:
                        m['renameUnlink'] = True
                        m['_deleteOnPost'] |= set(['renameUnlink'])
                    logger.debug("rename deletion 2 %s" % (m['fileOp']['rename']))
                    filtered_worklist.append(m)
                    self.updateFieldsAccepted(m, url, None,
                                           default_accept_directory,
                                           self.o.filename, self.o.mirror,
                                           self.o.strip, self.o.pstrip,
                                           self.o.flatten)
                    continue

                if self.o.acceptUnmatched:
                    logger.debug("accept: unmatched pattern=%s" % (url))
                    # FIXME... missing dir mapping with mirror, strip, etc...
                    self.updateFieldsAccepted(m, url, None,
                                           default_accept_directory,
                                           self.o.filename, self.o.mirror,
                                           self.o.strip, self.o.pstrip,
                                           self.o.flatten)
                    filtered_worklist.append(m)
                else:
                    self.reject(m, 304, "unmatched pattern %s" % url)

        self.worklist.incoming = filtered_worklist
        logger.debug(
            'end len(incoming)=%d, rejected=%d' %
            (len(self.worklist.incoming), len(self.worklist.rejected)))

    def gather(self) -> None:
        for p in self.plugins["gather"]:
            try:
                new_incoming = p()
            except Exception as ex:
                logger.error( f'flowCallback plugin {p} crashed: {ex}' )
                logger.debug( "details:", exc_info=True )
                continue

            if len(new_incoming) > 0:
                self.worklist.incoming.extend(new_incoming)

    def do(self) -> None:
        """
            stub to do the work: does nothing, marking everything done.
            to be replaced in child classes that do transforms or transfers.
        """

        # mark all remaining messages as done.
        self.worklist.ok = self.worklist.incoming
        self.worklist.incoming = []
        logger.debug('processing %d messages worked! (stop requested: %s)' %
                     (len(self.worklist.ok), self._stop_requested))

    def post(self) -> None:
        for p in self.plugins["post"]:
            try:
                p(self.worklist)
            except Exception as ex:
                logger.error( f'flowCallback plugin {p} crashed: {ex}' )
                logger.debug( "details:", exc_info=True )

    def report(self) -> None:
        # post reports
        # apply on_report plugins
        pass

    def write_inline_file(self, msg) -> bool:
        """
           write local file based on a message with inlined content.

        """
        # make sure directory exists, create it if not
        if not os.path.isdir(msg['new_dir']):
            try:
                self.worklist.directories_ok.append(msg['new_dir'])
                os.makedirs(msg['new_dir'], 0o775, True)
            except Exception as ex:
                logger.error("failed to make directory %s: %s" %
                             (msg['new_dir'], ex))
                return False

        logger.debug("data inlined with message, no need to download")
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

        if self.o.integrity_method.startswith('cod,'):
            algo_method = self.o.integrity_method[4:]
        elif msg['integrity']['method'] == 'cod':
            algo_method = msg['integrity']['value']
        else:
            algo_method = msg['integrity']['method']

        onfly_algo = sarracenia.integrity.Integrity.factory(algo_method)
        data_algo = sarracenia.integrity.Integrity.factory(algo_method)
        onfly_algo.set_path(path)
        data_algo.set_path(path)

        if algo_method == 'arbitrary':
            onfly_algo.value = msg['integrity']['value']
            data_algo.value = msg['integrity']['value']

        onfly_algo.update(data)

        msg['onfly_checksum'] = {
            'method': algo_method,
            'value': onfly_algo.value
        }

        if ((msg['size'] > 0) and len(data) != msg['size']):
            if self.o.acceptSizeWrong:
                logger.warning(
                    "acceptSizeWrong data size is (%d bytes) vs. expected: (%d bytes)"
                    % (len(data), msg['size']))
            else:
                logger.warning(
                    "decoded data size (%d bytes) does not have expected size: (%d bytes)"
                    % (len(data), msg['size']))
                return False

        #try:
        #    for p in self.plugins['on_data']:
        #        data = p(data)

        #except Exception as ex:
        #    logger.warning("plugin failed: %s" % (p, ex))
        #    return False

        data_algo.update(data)

        #FIXME: If data is changed by plugins, need to update content header.
        #       current code will reproduce the upstream message without mofification.
        #       need to think about whether that is OK or not.

        msg['data_checksum'] = {
            'method': algo_method,
            'value': data_algo.value
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

    def compute_local_checksum(self, msg) -> None:

        if sarracenia.filemetadata.supports_extended_attributes:
            try:
                x = sarracenia.filemetadata.FileMetadata(msg['new_path'])
                s = x.get('integrity')

                if s:
                    metadata_cached_mtime = x.get('mtime')
                    if ((metadata_cached_mtime >= msg['mtime'])):
                        # file has not been modified since checksum value was stored.

                        if (( 'integrity' in msg ) and ( 'method' in msg['integrity']  ) and \
                            ( msg['integrity']['method'] == s['method'] )) or  \
                            ( s['method'] ==  self.o.integrity_method ) :
                            # file
                            # cache good.
                            msg['local_integrity'] = s
                            msg['_deleteOnPost'] |= set(['local_integrity'])
                            return
            except:
                pass

        local_integrity = sarracenia.integrity.Integrity.factory(
            msg['integrity']['method'])

        if msg['integrity']['method'] == 'arbitrary':
            local_integrity.value = msg['integrity']['value']

        local_integrity.update_file(msg['new_path'])
        msg['local_integrity'] = {
            'method': msg['integrity']['method'],
            'value': local_integrity.value
        }
        msg['_deleteOnPost'] |= set(['local_integrity'])

    def file_should_be_downloaded(self, msg) -> bool:
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

        lstat = sarracenia.stat(msg['new_path'])
        fsiz = lstat.st_size

        # FIXME... local_offset... offset within the local file... partitioned... who knows?
        #   part of partitioning deferral.
        #end   = self.local_offset + self.length
        if 'size' in msg:
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
        else:
            end = 0

        # compare dates...

        if 'mtime' in msg:
            new_mtime = sarracenia.timestr2flt(msg['mtime'])
            old_mtime = 0.0

            if self.o.timeCopy:
                old_mtime = lstat.st_mtime
            elif sarracenia.filemetadata.supports_extended_attributes:
                try:
                    x = sarracenia.filemetadata.FileMetadata(msg['new_path'])
                    old_mtime = sarracenia.timestr2flt(x.get('mtime'))
                except:
                    pass

            if new_mtime <= old_mtime:
                self.reject(msg, 304,
                            "mtime not newer %s " % (msg['new_path']))
                return False
            else:
                logger.debug(
                    "{} new version is {} newer (new: {} vs old: {} )".format(
                        msg['new_path'], new_mtime - old_mtime, new_mtime,
                        old_mtime))

        if 'integrity' in msg and msg['integrity']['method'] in ['random', 'cod']:
            logger.debug("content_match %s sum 0/z never matches" %
                         (msg['new_path']))
            return True

        if end > fsiz:
            logger.debug(
                "new file not big enough... considered different")
            return True

        if not 'integrity' in msg: 
            # FIXME... should there be a setting to assume them the same? use cases may vary.
            logger.debug( "no checksum available, assuming different" )
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
            self.reject(msg, 304, "same checksum %s " % (msg['new_path']))
            return False
        else:
            return True

    def removeOneFile(self, path) -> bool:
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

    def renameOneItem(self, old, path) -> bool:
        """
            for messages with an rename file operation, it is to rename a file.
        """
        ok = True
        if not os.path.isfile(old):
            logger.info(
                "old file %s not found, if destination (%s) missing, then fall back to copy"
                % (old, path))
            # if the destination file exists, assume rename already happenned,
            # otherwis return false so that caller falls back to downloading/sending the file.
            # return os.path.isfile(path) 
            # PAS 2022/12/01 ... only 1 message to interpret, will never be a previous rename.
            return False

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

    def link1file(self, msg, symbolic=True) -> bool:
        """        
          perform a link of a single file, based on a message, returning boolean success
          if it's Symbolic, then do that. else do a hard link.

          imported from v2/subscribe/doit_download "link event, try to link the local product given by message"
        """
        logger.debug("message is to link %s to %s" %
                     (msg['new_file'], msg['fileOp']['link']))

        # redundant, check is done in caller.
        #if not 'link' in self.o.fileEvents:
        #    logger.info("message to link %s to %s ignored (events setting)" %  \
        #                                    ( msg['new_file'], msg['fileOp'][ 'link' ] ) )
        #    return False

        if not os.path.isdir(msg['new_dir']):
            try:
                self.worklist.directories_ok.append(msg['new_dir'])
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

            if 'hlink' in msg['fileOp'] :
                os.link(msg['fileOp']['hlink'], path)
                logger.info("%s hard-linked to %s " % (msg['new_file'], msg['fileOp']['hlink']))
            else:
                os.symlink(msg['fileOp']['link'], path)
                logger.info("%s sym-linked to %s " % (msg['new_file'], msg['fileOp']['link']))

        except:
            ok = False
            logger.error("link of %s %s failed." %
                         (msg['new_file'], msg['fileOp']))
            logger.debug('Exception details:', exc_info=True)

        return ok

    def do_download(self) -> None:
        """
           do download work for self.worklist.incoming, placing files:
                successfully downloaded in worklist.ok
                temporary failures in worklist.failed
                permanent failures (or files not to be downloaded) in worklist.rejected

        """

        if not self.o.download:
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
            new_file = msg['new_file']

            if 'fileOp' in msg :
                if 'rename' in msg['fileOp']:
                    if 'renameUnlink' in msg:
                        self.removeOneFile(msg['fileOp']['rename'])
                        msg.setReport(201, 'old unlinked %s' % msg['fileOp']['rename'])
                        self.worklist.ok.append(msg)
                    else:
                        # actual rename...
                        ok = self.renameOneItem(msg['fileOp']['rename'], new_path)
                        # if rename succeeds, fall through to download object to find if the file renamed
                        # actually matches the one advertised, and potentially download it.
                        # if rename fails, recover by falling through to download the data anyways.
                        if ok:
                            self.worklist.ok.append(msg)
                            msg.setReport(201, 'renamed')
                            continue

                if ('remove' in msg['fileOp']) and ('delete' in self.o.fileEvents):
                    if self.removeOneFile(new_path):
                        msg.setReport(201, 'removed')
                        self.worklist.ok.append(msg)
                    else:
                        #FIXME: should this really be queued for retry? or just permanently failed?
                        # in rejected to avoid retry, but wondering if failed and deferred
                        # should be separate lists in worklist...
                        self.reject(msg, 500, "remove %s failed" % new_path)
                    continue

                if 'link' in msg['fileOp'] or 'hlink' in msg['fileOp'] and ('link' in self.o.fileEvents):
                    if self.link1file(msg):
                        msg.setReport(201, 'linked')
                        self.worklist.ok.append(msg)
                    else:
                        # as above...
                        self.reject(msg, 500, "link %s failed" % msg['fileOp'])
                    continue

            # establish new_inflight_path which is the file to download into initially.
            if self.o.inflight == None or (
                ('blocks' in msg) and (msg['blocks']['method'] == 'inplace')):
                new_inflight_path = msg['new_file']
            elif type(self.o.inflight) == str:
                if self.o.inflight == '.':
                    new_inflight_path = '.' + new_file
                elif (self.o.inflight[-1] == '/') or (self.o.inflight[0] == '/'):
                    if not self.o.dry_run and not os.path.isdir(self.o.inflight):
                        try:
                            os.mkdir(self.o.inflight)
                            os.chmod(self.o.inflight, self.o.permDirDefault)
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
                self.reject(
                    msg, 503, "invalid inflight %s settings %s" %
                    (self.o.inflight, new_path))
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
                    self.reject(msg, 204,
                                "not overwriting existing file %s" % new_path)
                    continue

                if not self.file_should_be_downloaded(msg):
                    continue

            # download content
            if 'content' in msg.keys():
                if self.write_inline_file(msg):
                    msg.setReport(201, "Download successful (inline content)")
                    self.worklist.ok.append(msg)
                    continue
                logger.warning(
                    "failed to write inline content %s, falling through to download"
                    % new_path)

            parsed_url = urllib.parse.urlparse(msg['baseUrl'])
            self.scheme = parsed_url.scheme

            i = 1
            while i <= self.o.attempts:

                if i > 1:
                    logger.warning("downloading again, attempt %d" % i)

                ok = self.download(msg, self.o)
                if ok:
                    logger.debug("downloaded ok: %s" % new_path)
                    msg.setReport(201, "Download successful %s" % new_path)
                    # if content is present, but downloaded anyways, then it is no good, and should not be forwarded.
                    if 'content' in msg:
                        del msg['content']
                    self.worklist.ok.append(msg)
                    break
                else:
                    logger.info("attempt %d failed to download %s/%s to %s" \
                        % ( i, msg['baseUrl'], msg['relPath'], new_path) )
                i = i + 1

            if not ok:
                logger.error(
                    "gave up downloading for now, appending to retry queue")
                self.worklist.failed.append(msg)
            # FIXME: file reassembly missing?
            #if self.inplace : file_reassemble(self)

        self.worklist.incoming = []

    # v2 sr_util.py ... generic sr_transport imported here...

    # generalized download...
    def download(self, msg, options) -> bool:
        """
           download/transfer one file based on message, return True if successful, otherwise False.
        """

        self.o = options

        if 'retPath' in msg:
            logger.debug("%s_transport download override retPath=%s" %
                         (self.scheme, msg['retPath']))
            remote_file = msg['retPath']
            cdir = '/'
            urlstr = msg['baseUrl'] + '/' + msg['retPath']
        else:
            logger.debug("%s_transport download relPath=%s" %
                         (self.scheme, msg['relPath']))

            token = msg['relPath'].split('/')
            cdir = '/' + '/'.join(token[:-1])
            remote_file = token[-1]
            urlstr = msg['baseUrl'] + '/' + msg['relPath']

        istr =msg['integrity']  if ('integrity' in msg) else "None"
        fostr = msg['fileOp'] if ('fileOp' in msg ) else "None"

        logger.debug( 'integrity: %s, fileOp: %s' % ( istr, fostr ) ) 
        new_inflight_path = ''

        new_dir = msg['new_dir']
        new_file = msg['new_file']
        new_inflight_path = None

        if options.inflight == None or (
            ('blocks' in msg) and (msg['blocks']['method'] == 'inplace')):
            new_inflight_path = new_file
        elif type(options.inflight) == str:
            if options.inflight == '.':
                new_inflight_path = '.' + new_file
            elif ( options.inflight[-1] == '/' ) or (options.inflight[0] == '/'):
                new_inflight_path = options.inflight + new_file
            elif options.inflight[0] == '.':
                new_inflight_path = new_file + options.inflight
        else:
            logger.error('inflight setting: %s, not for remote.' %
                         options.inflight)
        if new_inflight_path:
            msg['new_inflight_path'] = new_inflight_path
            msg['_deleteOnPost'] |= set(['new_inflight_path'])

        if 'download' in self.plugins and len(self.plugins['download']) > 0:
            for plugin in self.plugins['download']:
                try:
                    ok = plugin(msg)
                except Exception as ex:
                    logger.error( f'flowCallback plugin {plugin} crashed: {ex}' )
                    logger.debug( "details:", exc_info=True )

                if not ok: return False
            return True

        if self.o.dry_run:
            curdir = new_dir
        else:
            try:
                curdir = os.getcwd()
            except:
                curdir = None

        if curdir != new_dir:
            # make sure directory exists, create it if not
            try:
                if not os.path.isdir(new_dir):
                    self.worklist.directories_ok.append(new_dir)
                    os.makedirs(new_dir, 0o775, True)
                os.chdir(new_dir)
            except Exception as ex:
                logger.warning("making %s: %s" % (new_dir, ex))
                logger.debug('Exception details:', exc_info=True)
                return False

        try:
            options.remoteUrl = msg['baseUrl']

            if (not (self.scheme in self.proto)) or (self.proto[self.scheme] is None):
                    self.proto[self.scheme] = sarracenia.transfer.Transfer.factory(self.scheme, self.o)

            if (not self.o.dry_run) and not self.proto[self.scheme].check_is_connected():
                    logger.debug("%s_transport download connects" % self.scheme)
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

         
            if (not self.o.dry_run) and hasattr(self.proto[self.scheme], 'getcwd'):
                cwd = self.proto[self.scheme].getcwd()

            if cwd != cdir:
                logger.debug("%s_transport download cd to %s" % (self.scheme, cdir))
                if self.o.dry_run:
                    cwd = cdir
                else:
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
            else:
                block_length = 0
                str_range = ''

            #download file

            logger.debug(
                'Beginning fetch of %s %s into %s %d-%d' %
                (urlstr, str_range, new_inflight_path, msg['local_offset'],
                 msg['local_offset'] + block_length - 1))

            # FIXME  locking for i parts in temporary file ... should stay lock
            # and file_reassemble... take into account the locking

            if self.o.integrity_method.startswith('cod,'):
                download_algo = self.o.integrity_method[4:]
            elif 'integrity' in msg:
                download_algo = msg['integrity']['method']
            else:
                download_algo = None

            if download_algo:
                self.proto[self.scheme].set_sumalgo(download_algo)

            if download_algo == 'arbitrary':
                self.proto[self.scheme].set_sumArbitrary(
                    msg['integrity']['value'])

            if (type(options.inflight) == str) \
                and (options.inflight[0] == '/' or options.inflight[-1] == '/') \
                and not os.path.exists(options.inflight):

                try:
                    if not self.o.dry_run:
                        os.mkdir(options.inflight)
                        os.chmod(options.inflight, options.permDirDefault)
                except:
                    logger.error('unable to make inflight directory %s/%s' %
                                 (msg['new_dir'], options.inflight))
                    logger.debug('Exception details: ', exc_info=True)

            logger.debug( "hasAccel=%s, thresh=%d, len=%d, remote_off=%d, local_off=%d inflight=%s" % \
                ( hasattr( self.proto[self.scheme], 'getAccelerated' ),  \
                self.o.accelThreshold, block_length, remote_offset,  msg['local_offset'], new_inflight_path ) )

            accelerated = hasattr( self.proto[self.scheme], 'getAccelerated') and \
                (self.o.accelThreshold > 0 ) and (block_length > self.o.accelThreshold) and \
                (remote_offset == 0) and ( msg['local_offset'] == 0)

            if not self.o.dry_run:
                if accelerated:
                    len_written = self.proto[self.scheme].getAccelerated(
                        msg, remote_file, new_inflight_path, block_length)
                    #FIXME: no onfly_checksum calculation during download.
                else:
                    self.proto[self.scheme].set_path(new_inflight_path)
                    len_written = self.proto[self.scheme].get(
                        msg, remote_file, new_inflight_path, remote_offset,
                        msg['local_offset'], block_length)
            else:
                len_written = block_length

            if (len_written == block_length):
                if not self.o.dry_run:
                    if accelerated:
                        self.proto[self.scheme].update_file(new_inflight_path)
                    if (new_inflight_path != new_file):
                        if os.path.isfile(new_file):
                            os.remove(new_file)
                        os.rename(new_inflight_path, new_file)
            elif len_written < 0:
                logger.error("failed to download %s" % new_file)
                return False
            else:
                if block_length == 0:
                    if self.o.acceptSizeWrong:
                        logger.debug(
                            'AcceptSizeWrong %d of with no length given for %s assuming ok'
                            % (len_written, new_inflight_path))
                    else:
                        logger.warning(
                            'downloaded %d of with no length given for %s assuming ok'
                            % (len_written, new_inflight_path))
                else:
                    if self.o.acceptSizeWrong:
                        logger.debug(
                            'AcceptSizeWrong download size mismatch, received %d of expected %d bytes for %s'
                            % (len_written, block_length, new_inflight_path))
                    else:
                        logger.error(
                            'incomplete download only %d of expected %d bytes for %s'
                            % (len_written, block_length, new_inflight_path))
                        return False

                    msg['size'] = len_written

            if download_algo and not self.o.dry_run:
                msg['onfly_checksum'] = self.proto[self.scheme].get_sumstr()
                msg['data_checksum'] = self.proto[self.scheme].data_checksum

                if self.o.integrity_method.startswith('cod,') and not accelerated:
                    msg['integrity'] = msg['onfly_checksum']

                msg['_deleteOnPost'] |= set(['onfly_checksum'])
                msg['_deleteOnPost'] |= set(['data_checksum'])

            # fix message if no partflg (means file size unknown until now)
            #if not 'blocks' in msg:
            #    #msg['size'] = self.proto[self.scheme].fpos ... fpos not set when accelerated.

            # fix permission
            if not self.o.dry_run:
                self.set_local_file_attributes(new_file, msg)

            if options.delete and hasattr(self.proto[self.scheme], 'delete'):
                try:
                    if not self.o.dry_run:
                        self.proto[self.scheme].delete(remote_file)
                    logger.debug('file deleted on remote site %s' %
                                 remote_file)
                except:
                    logger.error('unable to delete remote file %s' %
                                 remote_file)
                    logger.debug('Exception details: ', exc_info=True)

            if (block_length == 0) and (len_written > 0):
                return True

            if (len_written != block_length):
                return False

        except Exception as ex:
            logger.debug('Exception details: ', exc_info=True)
            logger.warning("failed to write %s: %s" % (new_inflight_path, ex))

            #closing on problem
            if not self.o.dry_run:
                try:
                    self.proto[self.scheme].close()
                except:
                    logger.debug('closing exception details: ', exc_info=True)
            self.cdir = None
            self.proto[self.scheme] = None
        
            if (not self.o.dry_run) and os.path.isfile(new_inflight_path):
                os.remove(new_inflight_path)
            return False
        return True

    # generalized send...
    def send(self, msg, options):
        self.o = options
        logger.debug("%s_transport remoteUrl: %s " %
                     (self.scheme, self.o.remoteUrl))
        logger.debug("%s_transport send %s %s" %
                     (self.scheme, msg['new_dir'], msg['new_file']))

        if len(self.plugins['send']) > 0:
            for plugin in self.plugins['send']:
                try:
                    ok = plugin(msg)
                except Exception as ex:
                    logger.error( f'flowCallback plugin {plugin} crashed: {ex}' )
                    logger.debug( "details:", exc_info=True )

                if not ok: return False
            return True

        if self.o.baseDir:
            local_path = self.o.variableExpansion(self.o.baseDir,
                                                msg) + '/' + msg['relPath']
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

        if (curdir != local_dir) and not self.o.dry_run:
            try:
                os.chdir(local_dir)
            except Exception as ex:
                logger.error("could not chdir to %s to write: %s" % (local_dir, ex))
                return False

        try:

            if not self.o.dry_run:
                if (not (self.scheme in self.proto)) or \
                   (self.proto[self.scheme] is None) or not self.proto[self.scheme].check_is_connected():
                    logger.debug("%s_transport send connects" % self.scheme)
    
                    self.proto[self.scheme] = sarracenia.transfer.Transfer.factory( self.scheme, options)
    
                    ok = self.proto[self.scheme].connect()
                    if not ok: return False
                    self.cdir = None

            elif not (self.scheme in self.proto) or self.proto[self.scheme] is None:
                logger.debug("dry_run %s_transport send connects" % self.scheme)
                self.proto[self.scheme] = sarracenia.transfer.Transfer.factory( self.scheme, options)
                self.cdir = None

            #=================================
            # if parts, check that the protol supports it
            #=================================

            if not self.o.dry_run and not hasattr(self.proto[self.scheme],
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
                if not self.o.dry_run:
                    cwd = self.proto[self.scheme].getcwd()

            if cwd != new_dir:
                logger.debug("%s_transport send cd to %s" %
                             (self.scheme, new_dir))
                if not self.o.dry_run:
                    self.proto[self.scheme].cd_forced(775, new_dir)

            #=================================
            # delete event
            #=================================

            if 'fileOp' in msg:
                if 'remove' in msg['fileOp'] :
                    if hasattr(self.proto[self.scheme], 'delete'):
                        logger.debug("message is to remove %s" % new_file)
                        if not self.o.dry_run:
                            self.proto[self.scheme].delete(new_file)
                        return True
                    logger.error("%s, delete not supported" % self.scheme)
                    return False

                #=================================
                # link event
                #=================================

                if 'hlink' in msg['fileOp']:
                    if hasattr(self.proto[self.scheme], 'link'):
                        logger.debug("message is to link %s to: %s" % (new_file, msg['fileOp']['hlink']))
                        if not self.o.dry_run:
                            self.proto[self.scheme].link(msg['fileOp']['hlink'], new_file)
                        return True
                    logger.error("%s, hardlinks not supported" % self.scheme)
                    return False
                elif 'link' in msg['fileOp']:
                    if hasattr(self.proto[self.scheme], 'symlink'):
                        logger.debug("message is to link %s to: %s" % (new_file, msg['fileOp']['link']))
                        if not self.o.dry_run:
                             self.proto[self.scheme].symlink(msg['fileOp']['link'], new_file)
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
                    str_range = 'bytes=%d-%d' % (new_offset, new_offset +
                                                 block_length - 1)

            str_range = ''
            if ('blocks' in msg) and (msg['blocks']['method'] == 'inplace'):
                str_range = 'bytes=%d-%d' % (offset, offset + msg['size'] - 1)

            #upload file

            logger.debug( "hasattr=%s, thresh=%d, len=%d, remote_off=%d, local_off=%d " % \
                ( hasattr( self.proto[self.scheme], 'putAccelerated'),  \
                self.o.accelThreshold, block_length, new_offset,  msg['local_offset'] ) )

            accelerated = hasattr( self.proto[self.scheme], 'putAccelerated') and \
                (self.o.accelThreshold > 0 ) and (block_length > self.o.accelThreshold) and \
                (new_offset == 0) and ( msg['local_offset'] == 0)

            if inflight == None or (('blocks' in msg) and
                                    (msg['blocks']['method'] != 'inplace')):
                logger.critical('none!')
                if not self.o.dry_run:
                    if accelerated:
                        len_written = self.proto[self.scheme].putAccelerated( msg, local_file, new_file)
                    else:
                        len_written = self.proto[self.scheme].put( msg, local_file, new_file)
                logger.critical('none! len_written=%d, block_length=%d ' % ( len_written, block_length) )
            elif (('blocks' in msg)
                  and (msg['blocks']['method'] == 'inplace')):
                if not self.o.dry_run:
                    self.proto[self.scheme].put(msg, local_file, new_file, offset,
                                            new_offset, msg['size'])
            elif inflight == '.':
                new_inflight_path = '.' + new_file
                if not self.o.dry_run:
                    if accelerated:
                        len_written = self.proto[self.scheme].putAccelerated(
                            msg, local_file, new_inflight_path)
                    else:
                        len_written = self.proto[self.scheme].put(
                            msg, local_file, new_inflight_path)
                    self.proto[self.scheme].rename(new_inflight_path, new_file)
                else:
                    len_written = msg['size']

            elif inflight[0] == '.':
                new_inflight_path = new_file + inflight
                if not self.o.dry_run:
                    if accelerated:
                        len_written = self.proto[self.scheme].putAccelerated(
                            msg, local_file, new_inflight_path)
                    else:
                        len_written = self.proto[self.scheme].put(msg, local_file, new_inflight_path)
                    self.proto[self.scheme].rename(new_inflight_path, new_file)
            elif options.inflight[-1] == '/':
                if not self.o.dry_run:
                    try:
                        self.proto[self.scheme].cd_forced(
                            775, new_dir + '/' + options.inflight)
                        self.proto[self.scheme].cd_forced(775, new_dir)
                    except:
                        pass
                new_inflight_path = options.inflight + new_file
                if not self.o.dry_run:
                    if accelerated:
                        len_written = self.proto[self.scheme].putAccelerated(
                            msg, local_file, new_inflight_path)
                    else:
                        len_written = self.proto[self.scheme].put(
                            msg, local_file, new_inflight_path)
                    self.proto[self.scheme].rename(new_inflight_path, new_file)
                else:
                    len_written = msg['size']
            elif inflight == 'umask':
                if not self.o.dry_run:
                    self.proto[self.scheme].umask()
                    if accelerated:
                        len_written = self.proto[self.scheme].putAccelerated(
                            msg, local_file, new_file)
                    else:
                        len_written = self.proto[self.scheme].put(
                            msg, local_file, new_file)
                    self.proto[self.scheme].put(msg, local_file, new_file)
                else:
                    len_written = msg['size']

            # fix permission

            if not self.o.dry_run:
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
                if not self.o.dry_run:
                    try:
                        self.proto[self.scheme].delete(new_inflight_path)
                    except:
                        pass

            #closing on problem
            if not self.o.dry_run:
                try:
                    self.proto[self.scheme].close()
                except:
                    pass
            self.cdir = None
            self.proto[self.scheme] = None

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
            x = sarracenia.filemetadata.FileMetadata(local_file)

            # FIXME ... what to do when checksums don't match?
            if 'onfly_checksum' in msg: 
                x.set( 'integrity', msg['onfly_checksum'] )
            elif 'integrity' in msg:
                x.set('integrity', msg['integrity'] )

            if self.o.timeCopy and 'mtime' in msg and msg['mtime']:
                x.set('mtime', msg['mtime'])
            else:
                x.set('mtime', sarracenia.timeflt2str(os.path.getmtime(local_file)))
            x.persist()

        mode = 0
        if self.o.permCopy and 'mode' in msg:
            try:
                mode = int(msg['mode'], base=8)
            except:
                mode = 0
            if mode > 0:
                os.chmod(local_file, mode)

        if mode == 0 and self.o.permDefault != 0:
            os.chmod(local_file, self.o.permDefault)

        if self.o.timeCopy and 'mtime' in msg and msg['mtime']:
            mtime = sarracenia.timestr2flt(msg['mtime'])
            atime = mtime
            if 'atime' in msg and msg['atime']:
                atime = sarracenia.timestr2flt(msg['atime'])
            os.utime(local_file, (atime, mtime))

    # set_remote_file_attributes
    def set_remote_file_attributes(self, proto, remote_file, msg):
        #logger.debug("sr_transport set_remote_file_attributes %s" % remote_file)

        if hasattr(proto, 'chmod'):
            mode = 0
            if self.o.permCopy and 'mode' in msg:
                try:
                    mode = int(msg['mode'], base=8)
                except:
                    mode = 0
                if mode > 0:
                    try:
                        proto.chmod(mode, remote_file)
                    except:
                        pass

            if mode == 0 and self.o.permDefault != 0:
                try:
                    proto.chmod(self.o.permDefault, remote_file)
                except:
                    pass

        if hasattr(proto, 'chmod'):
            if self.o.timeCopy and 'mtime' in msg and msg['mtime']:
                mtime = sarracenia.timestr2flt(msg['mtime'])
                atime = mtime
                if 'atime' in msg and msg['atime']:
                    atime = sarracenia.timestr2flt(msg['atime'])
                try:
                    proto.utime(remote_file, (atime, mtime))
                except:
                    pass

    # v2 sr_util sr_transport stuff. end.

    # imported from v2: sr_sender/doit_send

    def do_send(self):
        """
        """
        if not self.o.download:
            self.worklist.ok = self.worklist.incoming
            self.worklist.incoming = []
            return

        for msg in self.worklist.incoming:

            #=================================
            # proceed to send :  has to work
            #=================================

            # N attempts to send

            i = 1
            while i <= self.o.attempts:
                if i != 1:
                    logger.warning("sending again, attempt %d" % i)

                ok = self.send(msg, self.o)
                if ok:
                    self.worklist.ok.append(msg)
                    break

                i = i + 1
            if not ok:
                self.worklist.failed.append(msg)
        self.worklist.incoming = []


import sarracenia.flow.poll
import sarracenia.flow.post
import sarracenia.flow.report
import sarracenia.flow.sarra
import sarracenia.flow.sender
import sarracenia.flow.shovel
import sarracenia.flow.subscribe
import sarracenia.flow.watch
import sarracenia.flow.winnow
