import copy
import glob
import importlib
import logging
import os
import re

# v3 plugin architecture...
import sarracenia.flowcb
import sarracenia.identity
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

from sarracenia.featuredetection import features

if features['reassembly']['present']:
    import sarracenia.blockmanifest

from sarracenia import nowflt

logger = logging.getLogger(__name__)

allFileEvents = set(['create', 'delete', 'link', 'mkdir', 'modify','rmdir'])

default_options = {
    'accelThreshold': 0,
    'acceptUnmatched': True,
    'byteRateMax': None,
    'discard': False,
    'download': False,
    'fileEvents': allFileEvents,
    'housekeeping': 300,
    'logReject': False,
    'logLevel': 'info',
    'mirror': True,
    'permCopy': True,
    'timeCopy': True,
    'messageCountMax': 0,
    'messageRateMax': 0,
    'messageRateMin': 0,
    'sleep': 0.1,
    'topicPrefix': ['v03'],
    'topicCopy': False,
    'vip': []
}

if features['filetypes']['present']:
    import magic

if features['vip']['present']:
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
            if self.o.nodupe_driver.lower() == "redis":
                self.plugins['load'].append('sarracenia.flowcb.nodupe.redis.Redis')
            else:
                self.plugins['load'].append('sarracenia.flowcb.nodupe.disk.Disk')
            

        if (( hasattr(self.o, 'delete_source') and self.o.delete_source ) or \
            ( hasattr(self.o, 'delete_destination') and self.o.delete_destination )) and \
            ('sarracenia.flowcb.work.delete.Delete' not in self.o.plugins_late):
            self.o.plugins_late.append('sarracenia.flowcb.work.delete.Delete')

        # transport stuff.. for download, get, put, etc...
        self.scheme = None
        self.cdir = None
        self.proto = {}

        # initialize plugins.
        if hasattr(self.o, 'v2plugins') and len(self.o.v2plugins) > 0:
            self.plugins['load'].append(
                'sarracenia.flowcb.v2wrapper.V2Wrapper')

        self.plugins['load'].extend(self.o.plugins_late)

        self.plugins['load'].extend(self.o.destfn_scripts)

        self.block_reassembly_active = 'block_reassembly' in self.plugins['load'] or \
                 'sarracenia.flowcb.block_reassembly' in self.plugins['load']

        # metrics - dictionary with names of plugins as the keys
        self.metrics_lastWrite=0
        self.metricsFlowReset()

        self.had_vip = not os.path.exists( self.o.novipFilename )

    def metricsFlowReset(self) -> None:

        self.new_metrics = { 'flow': { 'stop_requested': False, 'last_housekeeping': 0,  
              'transferConnected': False, 'transferConnectStart': 0, 'transferConnectTime':0, 
              'transferRxBytes': 0, 'transferTxBytes': 0, 'transferRxFiles': 0, 'transferTxFiles': 0,
              'last_housekeeping_cpuTime': 0, 'cpuTime' : 0, } }

        # carry over some metrics... that don't reset.
        if hasattr(self,'metrics'):
            if 'transferRxLast' in self.metrics:
                self.new_metrics['transferRxLast'] = self.metrics['transferRxLast']

            if 'transferTxLast' in self.metrics:
                self.new_metrics['transferTxLast'] = self.metrics['transferTxLast']

        self.metrics=self.new_metrics

        # removing old metrics files
        #logger.debug( f"looking for old metrics for {self.o.metricsFilename}" )
        old_metrics=sorted(glob.glob(self.o.metricsFilename+'.*'))[0:-self.o.logRotateCount]
        for o in old_metrics:
            logger.info( f"removing old metrics file: {o} " )
            os.unlink(o)

    def loadCallbacks(self, plugins_to_load=None):

        if not plugins_to_load:
            plugins_to_load=self.plugins['load']

        for m in self.o.imports:
            try:
                importlib.import_module(m)
            except Exception as ex:
                logger.critical( f"python module import {m} load failed: {ex}" )
                logger.debug( "details:", exc_info=True )
                return False

        logger.debug( f'flowCallback plugins to load: {plugins_to_load}' )
        for c in plugins_to_load:
            try:
                plugin = sarracenia.flowcb.load_library(c, self.o)
            except Exception as ex:
                logger.critical( f"flowCallback plugin {c} did not load: {ex}" )
                logger.debug( "details:", exc_info=True )
                return False

            #logger.debug( f'flowCallback plugin loading: {c} an instance of: {plugin}' )
            for entry_point in sarracenia.flowcb.entry_points:
                if hasattr(plugin, entry_point):
                    fn = getattr(plugin, entry_point)
                    if callable(fn):
                        #logger.debug( f'registering {c}/{entry_point}' )
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

        if hasattr(self, entry_point):
            if self.o.logLevel.lower() == 'debug' :
                eval( f"self.{entry_point}(self.worklist)")
            else:
                try:
                    eval( f"self.{entry_point}(self.worklist)")
                except Exception as ex:
                    logger.error( f'flow {entry_point} crashed: {ex}' )
                    logger.debug( "details:", exc_info=True )

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

    def runCallbacksTime(self, entry_point):

        if hasattr(self, entry_point):
            if self.o.logLevel.lower() == 'debug' :
                eval( f"self.{entry_point}()")
            else:
                try:
                    eval( f"self.{entry_point}()")
                except Exception as ex:
                    logger.error( f'flow {entry_point} crashed: {ex}' )
                    logger.debug( "details:", exc_info=True )

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
        """Collect metrics from plugins with a ``metricsReport`` entry point.

        Expects the plugin to return a dictionary containing metrics, which is saved to ``self.metrics[plugin_name]``.
        """
        
        if hasattr(self, "metricsReport"):
            if self.o.logLevel.lower() == 'debug' :
                self.metricsReport()
            else:
                try:
                    self.metricsReport()
                except Exception as ex:
                    logger.error( f'flow metricsReport() crashed: {ex}' )
                    logger.debug( "details:", exc_info=True )

        if 'transferConnected' in self.metrics['flow'] and self.metrics['flow']['transferConnected']: 
            now=nowflt()
            self.metrics['flow']['transferConnectTime'] += now - self.metrics['flow']['transferConnectStart']
            self.metrics['flow']['transferConnectStart']=now

        modules=self.plugins["metricsReport"]

        if hasattr(self,'proto'): # gets re-spawned every batch, so not a permanent thing...
            for scheme in self.proto:
                if hasattr(self.proto[scheme], 'metricsReport'):
                    fn = getattr(self.proto[scheme], 'metricsReport')
                    if callable(fn):
                       modules.append( fn )

        for p in modules:
            if self.o.logLevel.lower() == 'debug' :
                module_name = str(p.__module__).replace('sarracenia.flowcb.', '' )
                self.metrics[module_name] = p()
            else:
                try:
                    module_name = str(p.__module__).replace('sarracenia.flowcb.', '' )
                    self.metrics[module_name] = p()
                except Exception as ex:
                    logger.error( f'flowCallback plugin {p}/metricsReport crashed: {ex}' )
                    logger.debug( "details:", exc_info=True )
        ost = os.times()
        self.metrics['flow']['cpuTime'] = ost.user+ost.system-self.metrics['flow']['last_housekeeping_cpuTime']

    def _runCallbackPoll(self):
        if hasattr(self, "Poll"):
            if self.o.logLevel.lower() == 'debug' :
                self.Poll()
            else:
                try:
                    self.Poll()
                except Exception as ex:
                    logger.error( f'flow Poll crashed: {ex}' )
                    logger.debug( "details:", exc_info=True )

        for plugin in self.plugins['poll']:
            if self.o.logLevel.lower() == 'debug' :
                new_incoming = plugin()
                if len(new_incoming) > 0:
                    self.worklist.incoming.extend(new_incoming)
            else:
                try:
                    new_incoming = plugin()
                    if len(new_incoming) > 0:
                        self.worklist.incoming.extend(new_incoming)
                except Exception as ex:
                    try:
                        logger.error(f'flowCallback plugin {plugin.__module__}.{plugin.__qualname__} crashed: {ex}' )
                    except:
                        # just in case
                        logger.error(f'flowCallback plugin {plugin} crashed: {ex}' )
                    logger.debug("details:", exc_info=True )

    def _runHousekeeping(self, now) -> float:
        """ Run housekeeping callbacks
            Return the time when housekeeping should be run next
        """
        logger.info(f'on_housekeeping pid: {os.getpid()} {self.o.component}/{self.o.config} instance: {self.o.no}')
        if hasattr(self, "on_housekeeping"):
            if self.o.logLevel.lower() == 'debug' :
                self.on_housekeeping()
            else:
                try:
                    self.on_housekeeping()
                except Exception as ex:
                    logger.error( f'flow on_housekeeping crashed: {ex}' )
                    logger.debug( "details:", exc_info=True )

        self.runCallbacksTime('on_housekeeping')
        self.metricsFlowReset()
        self.metrics['flow']['last_housekeeping'] = now
        ost = os.times()
        self.metrics['flow']['last_housekeeping_cpuTime'] = ost.user+ost.system
        self.metrics['flow']['cpuTime'] = ost.user+ost.system

        next_housekeeping = now + self.o.housekeeping
        self.metrics['flow']['next_housekeeping'] = next_housekeeping
        return next_housekeeping

    def has_vip(self) -> list:
        """
            return list of vips which are active on the current machine, or an empty list.
        """

        if not features['vip']['present']: return True

        # no vip given... standalone always has vip.
        if self.o.vip == []:
            return [ 'AnyAddressIsFine' ]

        try:
            for i in netifaces.interfaces():
                for a in netifaces.ifaddresses(i):
                    j = 0
                    while (j < len(netifaces.ifaddresses(i)[a])):
                        k=netifaces.ifaddresses(i)[a][j].get('addr')
                        if k in self.o.vip:
                            return k
                        j += 1
        except Exception as ex:
            logger.error(
                f'error while looking for interfaces to compare with vip {self.o.vip}: {ex}' )
            logger.debug('Exception details: ', exc_info=True)

        return []

    def reject(self, m, code, reason) -> None:
        """
            reject a message.
        """
        self.worklist.rejected.append(m)
        m.setReport(code, reason)

    def stop_request(self) -> None:
        """ called by the signal handler to tell self and FlowCB classes to stop. Without this,
            calling runCallbacksTime('please_stop') from inside self.please_stop causes an infinite loop.
            Note: if this is called from outside of a signal handler, the interruptible_sleep function
                  won't work.
        """
        logger.info(f'telling {len(self.plugins["please_stop"])} callbacks to please_stop.')
        # this will call the please_stop method below, and other classes' please_stop methods
        self.runCallbacksTime('please_stop')

    def please_stop(self) -> None:
        logger.info(f'asked to stop')
        self._stop_requested = True
        self.metrics["flow"]['stop_requested'] = True
    
    def close(self) -> None:

        self.runCallbacksTime('on_stop')
        if os.path.exists( self.o.novipFilename ):
            os.unlink( self.o.novipFilename )
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

    def _run_vip_update(self) -> bool:

        self.have_vip = self.has_vip()
        if (self.o.component == 'poll') and not self.have_vip:
            if self.had_vip:
                logger.info("now passive on vips %s" % self.o.vip )
                with open( self.o.novipFilename, 'w' ) as f:
                    f.write(str(nowflt()) + '\n' )
                self.had_vip=False
        else:
            if not self.had_vip:
                logger.info("now active on vip %s" % self.have_vip )
                self.had_vip=True
                if os.path.exists( self.o.novipFilename ):
                    os.unlink( self.o.novipFilename )

    def run(self):
        """
          This is the core routine of the algorithm, with most important data driven
          loop in it. This implements the General Algorithm (as described in the Concepts Explanation Guide) 
          check if stop_requested once in a while, but never return otherwise.
        """


        if hasattr(self.o, 'metricsFilename' ):
            mdir=os.path.dirname(self.o.metricsFilename)
            if not os.path.isdir(mdir):
                os.makedirs(mdir, self.o.permDirDefault, True)

        pidfilename = sarracenia.config.get_pid_filename(
                self.o.hostdir if self.o.statehost else None,
                self.o.component, self.o.config, self.o.no)
        pdir=os.path.dirname(pidfilename)
        if not os.path.isdir(pdir):
            os.makedirs(mdir, self.o.permDirDefault, True)


        if not self.loadCallbacks(self.plugins['load']):
           return

        logger.debug( f"working directory: {os.getpid()}" )

        next_housekeeping = nowflt() + self.o.housekeeping

        current_rate = 0
        total_messages = 1
        start_time = nowflt()
        now=start_time
        current_sleep = self.o.sleep
        last_time = start_time
        self.metrics['flow']['last_housekeeping'] = start_time
        ost=os.times()
        self.metrics['flow']['last_housekeeping_cpuTime'] =  ost.user+ost.system

        if self.o.logLevel == 'debug':
            logger.debug("options:")
            self.o.dump()

        logger.debug("callbacks loaded: %s" % self.plugins['load'])
        logger.debug(
            f'pid: {os.getpid()} {self.o.component}/{self.o.config} instance: {self.o.no}'
        )

        spamming = True
        last_gather_len = 0
        stopping = False

        while True:

            if self._stop_requested:
                if stopping:
                    logger.debug('clean stop from run loop')
                    self.close()
                    break
                else:
                    logger.debug('starting last pass (without gather) through loop for cleanup.')
                    stopping = True

            self._run_vip_update()

            if now > next_housekeeping or stopping:
                next_housekeeping = self._runHousekeeping(now)
            elif now == start_time:
                self.runCallbacksTime(f'on_start')

            self.worklist.incoming = []

            if (self.o.component == 'poll') or self.have_vip:

                if ( self.o.messageRateMax > 0 ) and (current_rate > 0.8*self.o.messageRateMax ):
                    logger.debug("current_rate (%.2f) vs. messageRateMax(%.2f)) " % (current_rate, self.o.messageRateMax))

                if not stopping:
                    self.gather()

                last_gather_len = len(self.worklist.incoming)
                if (last_gather_len == 0):
                    spamming = True
                else:
                    current_sleep = self.o.sleep
                    spamming = False

                self.filter()

                # this for duplicate cache synchronization.
                if self.worklist.poll_catching_up:
                    self.ack(self.worklist.incoming)
                    self.worklist.incoming = []

                else: # normal processing, when you are active.
                    self.work()
                    self.post(now)

            now = nowflt()
            run_time = now - start_time
            total_messages += last_gather_len

            # trigger shutdown when messageCountMax is reached
            if (self.o.messageCountMax > 0) and (total_messages > self.o.messageCountMax):
                logger.info(f'{total_messages} messages processed > messageCountMax {self.o.messageCountMax}')
                self.runCallbacksTime('please_stop')

            current_rate = total_messages / run_time
            elapsed = now - last_time

            self.metrics['flow']['msgRate'] = current_rate
            self.metrics['flow']['msgRateCpu'] = total_messages / (self.metrics['flow']['cpuTime']+self.metrics['flow']['last_housekeeping_cpuTime'] )

            # trigger shutdown once gather is finished, where sleep < 0 (e.g. a post)
            if (last_gather_len == 0) and (self.o.sleep < 0):
                if (self.o.retryEmptyBeforeExit and "retry" in self.metrics
                    and self.metrics['retry']['msgs_in_post_retry'] > 0):
                    logger.info( f"retryEmptyBeforeExit=True and there are still "
                        f"{self.metrics['retry']['msgs_in_post_retry']} messages in the post retry queue.")
                    # Sleep for a while. Messages can't be retried before housekeeping has run...
                    # how long to sleep is unclear... if there are a lot of retries, and a low batch... could take a long time.
                    current_sleep = self.o.batch if self.o.batch < self.o.housekeeping else self.o.housekeeping // 2
                else:
                    self.runCallbacksTime('please_stop')

            if spamming and (current_sleep < 5):
                current_sleep *= 2

            self.metrics['flow']['current_sleep'] = current_sleep

            # Run housekeeping based on time, and before stopping to ensure it's run at least once
            if now > next_housekeeping or stopping:
                next_housekeeping = self._runHousekeeping(now)

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
                # dividing into small sleeps so exit processing happens faster
                # bug #595, still relatively low cpu usage in increment sized chunks.
                if 5 < stime:
                    increment=5
                else:
                    increment=stime
                while (stime > 0):
                    logger.debug( f"sleeping for {increment:.2f}" )
                    time.sleep(increment)
                    if self._stop_requested:
                        break
                    else:
                        stime -= 5 
                    # Run housekeeping during long sleeps
                    now_for_hk = nowflt()
                    if now_for_hk > next_housekeeping:
                        next_housekeeping = self._runHousekeeping(now_for_hk)

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
        if currentFileOption is None or currentFileOption == 'None': return filename

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
                    classname =  dfm.__qualname__.split('.')[0]
                    if (scriptclass == classname) or (scriptclass.capitalize() == classname): 
                        try:
                            destFileName = dfm(msg)
                        except Exception as ex:
                            logger.error( f'DESTFNSCRIPT plugin {dfm} crashed: {ex}' )
                            logger.debug( "details:", exc_info=True )

                        if destFileName == None or type(destFileName) != str:
                             logger.error( f"DESTFNSCRIPT {dfm} return value must be the new file name as a string. This one returned {destFileName}, ignoring")
                             return None

            elif spec == 'TIME':
                timeSuffix = ':' + time.strftime("%Y%m%d%H%M%S", time.gmtime())
                if 'pubTime' in msg:
                    timeSuffix = ":" + msg['pubTime'].split('.')[0]
                if 'pubTime' in msg:
                    timeSuffix = ":" + msg['pubTime'].split('.')[0]
                    timeSuffix = timeSuffix.replace('T', '')
                # check for PX or PDS behavior ...
                # if file already had a time extension keep his...
                if len(parts[-1]) == 14 and parts[-1][0] == '2':
                    timeSuffix = ':' + parts[-1]

            else:
                logger.error( f"invalid DESTFN parameter: {spec}" )
                return None
        return destFileName + satnet + timeSuffix


    # ==============================================
    # how will the download file land on this server
    # with all options, this is really tricky
    # ==============================================
    """
        to test changes to updateFieldsAccepted, run:  make test_shim in the SarraC package...
        because it tickles a lot of these settings, in addition to the flow_tests before
        trying to PR changes here.

    """
    def updateFieldsAccepted(self, msg, urlstr, pattern, maskDir,
                             maskFileOption, mirror, path_strip_count, pstrip, flatten) -> None:
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

        relPath = '%s' % msg['relPath']

        if self.o.baseUrl_relPath:
            u = sarracenia.baseUrlParse(msg['baseUrl'])
            relPath = u.path[1:] + '/' + relPath

        if self.o.download and 'rename' in msg: 
            # FIXME... why the % ? why not just assign it to copy the value?
            relPath = '%s' % msg['rename']

            # after download we dont propagate renaming... once used, get rid of it
            del msg['rename']
            # FIXME: worry about publishing after a rename.
            # the relpath should be replaced by rename value for downstream
            # because the file was written to rename.
            # not sure if this happens or not.


        token = relPath.split('/')
        filename = token[-1]

        # resolve a current base directory to which the relative path will eventually be added.
        #  update fileOp fields to replace baseDir.
        #if self.o.currentDir : new_dir = self.o.currentDir

        new_dir=''
        if maskDir:
            new_dir = self.o.variableExpansion(maskDir, msg)
        else:
            if self.o.post_baseDir:
                new_dir = self.o.variableExpansion(self.o.post_baseDir, msg)
        d=None
        if self.o.baseDir:
            if new_dir:
                d = new_dir
            elif self.o.post_baseDir:
                d = self.o.variableExpansion(self.o.post_baseDir, msg)

        # to get locally resolvable links and renames, need to mangle the pathnames.
        # to get something to restore for downstream consumers, need to put the original
        # names back.

        if 'fileOp' in msg:
            msg['post_fileOp'] = copy.deepcopy(msg['fileOp'])
            msg['_deleteOnPost'] |= set( [ 'post_fileOp' ] )

        # if provided, strip (integer) ... strip N heading directories
        #         or  pstrip (pattern str) strip regexp pattern from relPath
        # cannot have both (see setting of option strip in sr_config)

        if path_strip_count > 0:

            logger.warning( f"path_strip_count:{path_strip_count}   ")
            strip=path_strip_count 
            if strip < len(token):
                token = token[strip:]

            if 'fileOp' in msg:
                """
                   files are written with cwd being the directory containing the file written.
                   when stripping the root of the tree off, the path must be rendered relative to the
                   directory containing the file: the values are modified to create relative paths.
                """
                for f in ['link', 'hlink', 'rename']:
                    if f in msg['fileOp']:
                        fopv = msg['fileOp'][f].split('/') 
                        # an absolute path file posted is relative to '/' (in relPath) but the values in
                        # the link and rename fields may be absolute, requiring and adjustmeent when stripping
                        if fopv[0] == '':
                            strip += 1
                        elif len(fopv) == 1:
                            toclimb=len(token)-1
                            msg['fileOp'][f] = '../'*(toclimb) + fopv[0]
                        if len(fopv) > strip:
                            rest=fopv[strip:]
                            toclimb=len(token)-rest.count('..')-1
                            msg['fileOp'][f] = '../'*(toclimb)+'/'.join(rest)
                            
        # strip using a pattern
        elif pstrip:

            #MG FIXME Peter's wish to have replacement in pstrip (ex.:${SOURCE}...)

            relstrip = re.sub(pstrip, '', relPath, 1)

            if not filename in relstrip: relstrip = filename
            token = relstrip.split('/')

            if 'fileOp' in msg:
                for f in ['link', 'hlink', 'rename']:
                    if f in msg['fileOp']:
                        msg['fileOp'][f] = re.sub(pstrip, '', msg['fileOp'][f] )
                            
        # if flatten... we flatten relative path
        # strip taken into account

        if flatten != '/':
            filename = flatten.join(token)
            token[-1] = filename

            if 'fileOp' in msg:
                for f in ['link', 'hlink', 'rename']:
                    if f in msg['fileOp']:
                        msg['fileOp'][f] = flatten.join(msg['fileOp'][f].split('/'))
                            
        if self.o.baseDir:
            # remove baseDir from relPath if present.
            token_baseDir = self.o.baseDir.split('/')[1:]
            remcnt=0
            if len(token) > len(token_baseDir):
                for i in range(0,len(token_baseDir)):
                    if token_baseDir[i] == token[i]:
                        remcnt+=1
                    else:
                        break
                if remcnt == len(token_baseDir):
                    token=token[remcnt:] 

            if d:
                if 'fileOp' in msg and len(self.o.baseDir) > 1:
                    for f in ['link', 'hlink', 'rename']:
                        if (f in msg['fileOp']) :
                            if msg['fileOp'][f].startswith(self.o.baseDir):
                                msg['fileOp'][f] = msg['fileOp'][f].replace(self.o.baseDir, d, 1)
                            elif os.sep not in msg['fileOp'][f]:
                                toclimb=len(token)-1
                                msg['fileOp'][f] = '../'*(toclimb) + msg['fileOp'][f]

        elif 'fileOp' in msg and new_dir:
            u = sarracenia.baseUrlParse(msg['baseUrl'])
            for f in ['link', 'hlink', 'rename']:
                if (f in msg['fileOp']):
                    if (len(u.path) > 1):
                        if msg['fileOp'][f].startswith(u.path):
                            msg['fileOp'][f] = msg['fileOp'][f].replace(u.path, new_dir, 1)
                        elif '/' not in msg['fileOp'][f]:
                            toclimb=len(token)-1
                            msg['fileOp'][f] = '../'*(toclimb) + msg['fileOp'][f]
                            
        if self.o.mirror and len(token) > 1:
            new_dir = new_dir + '/' + '/'.join(token[:-1])

        new_dir = self.o.variableExpansion(new_dir, msg)
        # resolution of sundew's dirPattern

        tfname = filename
        # when sr_sender did not derived from sr_subscribe it was always called
        new_dir = self.o.sundew_dirPattern(pattern, urlstr, tfname, new_dir)
        msg.updatePaths(self.o, new_dir, filename)

        if maskFileOption:
            msg['new_file'] = self.sundew_getDestInfos(msg, maskFileOption, filename)
            msg['new_relPath'] = '/'.join(  msg['new_relPath'].split('/')[0:-1] + [ msg['new_file'] ]  )


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
                    f"message too old (high lag): {lag:g} sec. skipping: {m.getIDStr()}, " )
                continue

            if 'mtime' in m:
                age =  now-sarracenia.timestr2flt(m['mtime'])
                if self.o.fileAgeMax > 0 and age > self.o.fileAgeMax:
                    self.reject( m, 410, f"file too old: {age:g} sec. skipping: {m.getIDStr()}, ")
                    continue

                if self.o.fileAgeMin > 0 and age < self.o.fileAgeMin:
                    logger.warning( f"file too young: queueing for retry.")
                    self.worklist.failed.append(m)
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
                    if (pattern == '.*'):
                        oldname_matched = accepting
                        break
                    matches = mask_regexp.match(urlToMatch)
                    if matches:
                            m[ '_matches'] = matches
                            m['_deleteOnPost'] |= set(['_matches'])
                            oldname_matched = accepting
                    break

            url = self.o.variableExpansion(m['baseUrl'], m)
            if (m['baseUrl'][-1] == '/') or (len(m['relPath']) > 0 and (m['relPath'][0] == '/')):
                if (m['baseUrl'][-1] == '/') and (len(m['relPath'])>0) and (m['relPath'][0] == '/'):
                    url += m['relPath'][1:]
                else:
                    url += m['relPath']
            else:
                url += '/' + m['relPath']

            if 'sundew_extension' in m and url.count(":") < 1:
                urlToMatch = url + ':' + m['sundew_extension']
            else:
                urlToMatch = url

            logger.debug( f" urlToMatch: {urlToMatch} " )
            # apply masks for accept/reject options.
            matched = False
            for mask in self.o.masks:
                pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask
                if (pattern != '.*') :
                    matches = mask_regexp.match(urlToMatch)
                    if matches:
                        m[ '_matches'] = matches
                        m['_deleteOnPost'] |= set(['_matches'])

                if (pattern == '.*') or matches:
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

        logger.debug( 'end len(incoming)=%d, rejected=%d' % (len(self.worklist.incoming), len(self.worklist.rejected)))

        self._runCallbacksWorklist('after_accept')

        logger.debug( 'B filtered incoming: %d, ok: %d (directories: %d), rejected: %d, failed: %d stop_requested: %s have_vip: %s'
            % (len(self.worklist.incoming), len(self.worklist.ok), len(self.worklist.directories_ok),
               len(self.worklist.rejected), len(self.worklist.failed), self._stop_requested, self.have_vip))

        self.ack(self.worklist.ok)
        self.worklist.ok = []
        self.ack(self.worklist.rejected)
        self.worklist.rejected = []
        self.ack(self.worklist.failed)


    def gather(self) -> None:
        so_far=0
        keep_going=True
        for p in self.plugins["gather"]:
            try:
                retval = p(self.o.batch-so_far)

                # To avoid having to modify all existing gathers, support old API.
                if type(retval) == tuple:
                    keep_going, new_incoming = retval
                elif type(retval) == list:
                    new_incoming = retval
                else:
                    logger.error( f"flowCallback plugin gather routine {p} returned unexpected type: {type(retval)}. Expected tuple of boolean and list of new messages" )
            except Exception as ex:
                logger.error( f'flowCallback plugin {p} crashed: {ex}' )
                logger.debug( "details:", exc_info=True )
                continue

            if len(new_incoming) > 0:
                self.worklist.incoming.extend(new_incoming)
                so_far += len(new_incoming) 

            # if we gathered enough with a subset of plugins then return.
            if not keep_going or (so_far >= self.o.batch):
                if (self.o.component == 'poll' ):
                    self.worklist.poll_catching_up=True

                return

        # gather is an extended version of poll.
        if self.o.component != 'poll':
            return

        if len(self.worklist.incoming) > 0:
            logger.debug('ingesting %d postings into duplicate suppression cache' % len(self.worklist.incoming) )
            self.worklist.poll_catching_up = True
            return
        else:
            self.worklist.poll_catching_up = False

        if self.have_vip:
            self._runCallbackPoll()

    def do(self) -> None:

        if self.o.download:
            self.do_download()
        else:
            # mark all remaining messages as done.
            self.worklist.ok = self.worklist.incoming
            self.worklist.incoming = []

        logger.debug('processing %d messages worked!' % len(self.worklist.ok))

    def work(self) -> None:

        self.do()

        # need to acknowledge here, because posting will delete message-id
        self.ack(self.worklist.ok)
        self.ack(self.worklist.rejected)
        self.ack(self.worklist.failed)

        # adjust message after action is done, but before 'after_work' so adjustment is possible.
        for m in self.worklist.ok:
            if ('new_baseUrl' in m) and (m['baseUrl'] !=
                                         m['new_baseUrl']):
                m['old_baseUrl'] = m['baseUrl']
                m['_deleteOnPost'] |= set(['old_baseUrl'])
                m['baseUrl'] = m['new_baseUrl']
            if ('new_retrievePath' in m) :
                m['old_retrievePath'] = m['retrievePath']
                m['retrievePath'] = m['new_retrievePath']
                m['_deleteOnPost'] |= set(['old_retrievePath'])

            # if new_file does not match relPath, then adjust relPath so it does.
            if 'relPath' in m and m['new_file'] != m['relPath'].split('/')[-1]:
                if not 'new_relPath' in m:
                    if len(m['relPath']) > 1:
                        m['new_relPath'] = '/'.join( m['relPath'].split('/')[0:-1] + [ m['new_file'] ])
                    else:
                        m['new_relPath'] = m['new_file']
                else:
                    if len(m['new_relPath']) > 1:
                        m['new_relPath'] = '/'.join( m['new_relPath'].split('/')[0:-1] + [ m['new_file'] ] )
                    else:
                        m['new_relPath'] = m['new_file']

            if ('new_relPath' in m) and (m['relPath'] != m['new_relPath']):
                m['old_relPath'] = m['relPath']
                m['_deleteOnPost'] |= set(['old_relPath'])
                m['relPath'] = m['new_relPath']
                m['old_subtopic'] = m['subtopic']
                m['_deleteOnPost'] |= set(['old_subtopic','subtopic'])
                m['subtopic'] = m['new_subtopic']

            if '_format' in m:
                m['old_format'] = m['_format']
                m['_deleteOnPost'] |= set(['old_format'])

            if 'post_format' in m:
                m['_format'] = m['post_format']

            # restore adjustment to fileOp
            if 'post_fileOp' in m:
                m['fileOp'] = m['post_fileOp']

            if self.o.download and 'retrievePath' in m:
                # retrieve paths do not propagate after download.
                del m['retrievePath'] 

        self._runCallbacksWorklist('after_work')

        self.ack(self.worklist.rejected)
        self.worklist.rejected = []
        self.ack(self.worklist.failed)



    def post(self,now) -> None:

        if hasattr(self.o,'post_broker') and self.o.post_broker:

            if len(self.plugins["post"]) > 0:

                # work-around for python3.5 not being able to copy re.match issue: 
                # https://github.com/MetPX/sarracenia/issues/857 
                if sys.version_info.major == 3 and sys.version_info.minor <= 6:
                    for m in self.worklist.ok:
                        if '_matches' in m:
                            del m['_matches']

                for p in self.plugins["post"]:
                    try:
                        p(self.worklist)
                    except Exception as ex:
                        logger.error( f'flowCallback plugin {p} crashed: {ex}' )
                        logger.debug( "details:", exc_info=True )

            self._runCallbacksWorklist('after_post')

        self._runCallbacksWorklist('report')
        self._runCallbackMetrics()

        if hasattr(self.o, 'metricsFilename' ) \
                and now > self.metrics_lastWrite+self.o.metrics_writeInterval:

            # assume dir always exist... should check on startup, not here.
            # if os.path.isdir(os.path.dirname(self.o.metricsFilename)):
            metrics=json.dumps(self.metrics)
            with open(self.o.metricsFilename, 'w') as mfn:
                 mfn.write(metrics+"\n")
            self.metrics_lastWrite=now

            if self.o.logMetrics:
                if self.o.logRotateInterval >= 24*60*60:
                    tslen=8
                elif self.o.logRotateInterval > 60:
                    tslen=14
                else:
                    tslen=16
                timestamp=time.strftime("%Y%m%d-%H%M%S", time.gmtime())
                with open(self.o.metricsFilename + '.' + timestamp[0:tslen], 'a') as mfn:
                    mfn.write( f'\"{timestamp}\" : {metrics},\n')

            # removing old metrics files
            #logger.debug( f"looking for old metrics for {self.o.metricsFilename}" )
            old_metrics=sorted(glob.glob(self.o.metricsFilename+'.*'))[0:-self.o.logRotateCount]
            for o in old_metrics:
                logger.info( f"removing old metrics file: {o} " )
                os.unlink(o)

        self.worklist.ok = []
        self.worklist.directories_ok = []
        self.worklist.failed = []

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
            data = msg['content']['value'].encode(msg['content']['encoding'])

        if self.o.identity_method.startswith('cod,'):
            algo_method = self.o.identity_method[4:]
        elif msg['identity']['method'] == 'cod':
            algo_method = msg['identity']['value']
        else:
            algo_method = msg['identity']['method']

        onfly_algo = sarracenia.identity.Identity.factory(algo_method)
        data_algo = sarracenia.identity.Identity.factory(algo_method)
        onfly_algo.set_path(path)
        data_algo.set_path(path)

        if algo_method == 'arbitrary':
            onfly_algo.value = msg['identity']['value']
            data_algo.value = msg['identity']['value']

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
                s = x.get('identity')

                if s:
                    metadata_cached_mtime = x.get('mtime')
                    if ((metadata_cached_mtime >= msg['mtime'])):
                        # file has not been modified since checksum value was stored.

                        if (( 'identity' in msg ) and ( 'method' in msg['identity']  ) and \
                            ( msg['identity']['method'] == s['method'] )) or  \
                            ( s['method'] ==  self.o.identity_method ) :
                            # file
                            # cache good.
                            msg['local_identity'] = s
                            msg['_deleteOnPost'] |= set(['local_identity'])
                            b = x.get('blocks')
                            msg['local_blocks'] = b
                            msg['_deleteOnPost'] |= set(['local_blocks'])
                            return
            except:
                pass

        local_identity = sarracenia.identity.Identity.factory(
            msg['identity']['method'])

        if msg['identity']['method'] == 'arbitrary':
            local_identity.value = msg['identity']['value']

        local_identity.update_file(msg['new_path'])
        msg['local_identity'] = {
            'method': msg['identity']['method'],
            'value': local_identity.value
        }
        msg['_deleteOnPost'] |= set(['local_identity'])

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
        # if using a true binary checksum, the size check is enough.
        if 'identity' in msg and 'method' in msg['identity']:
            method=msg['identity']['method']
        else:
            method='unknown'
        
        # if no method given, then assume binary comparison is good.
        if method in sarracenia.identity.binary_methods: 
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

        elif method in ['random', 'cod']:
            logger.debug("content_match %s sum random/zero/cod never matches" %
                         (msg['new_path']))
            return True

        if not 'identity' in msg: 
            # FIXME... should there be a setting to assume them the same? use cases may vary.
            logger.debug( "size different and no checksum available, assuming different" )
            return True

        try:
            self.compute_local_checksum(msg)
        except:
            logger.debug(
                "something went wrong when computing local checksum... considered different"
            )
            return True

        logger.debug( f"checksum in message: {msg['identity']} vs. local: {msg['local_identity']}" )

        if msg['local_identity'] == msg['identity']:
            self.reject(msg, 304, f"same checksum {msg['new_path']}" )
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
            logger.debug("removed %s" % path)
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
        if not os.path.exists(old):
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

    def mkdir(self, msg) -> bool:
        """
            perform an mkdir.
        """

        ok=False
        path = msg['new_dir'] + '/' + msg['new_file']
        logger.debug( f"message is to mkdir {path}" )

        if not os.path.isdir(msg['new_dir']):
            try:
                os.makedirs(msg['new_dir'], self.o.permDirDefault, True)
            except Exception as ex:
                logger.warning("making %s: %s" % (msg['new_dir'], ex))
                logger.debug('Exception details:', exc_info=True)

        if os.path.isdir(path):
            logger.debug( f"no need to mkdir {path} as it exists" )
            return True

        if 'mode' in msg:
            mode=msg['mode']
        else:
            mode=self.o.permDirDefault

        if type(mode) is not int:
            mode=int(mode,base=8)

        try:
            os.mkdir(path,mode=mode)
            ok=True
        except Exception as ex:
            logger.error( f"mkdir {path} failed." )
            logger.debug('Exception details:', exc_info=True)
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
                os.makedirs(msg['new_dir'], self.o.permDirDefault, True)
            except Exception as ex:
                logger.warning("making %s: %s" % (msg['new_dir'], ex))
                logger.debug('Exception details:', exc_info=True)

        ok = True
        try:
            path = msg['new_dir'] + '/' + msg['new_file']

            if os.path.isfile(path): os.unlink(path)
            if os.path.islink(path): os.unlink(path)
            #if os.path.isdir(path): os.rmdir(path)

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

            if not 'new_dir' in msg or not msg['new_dir']:
                self.reject(msg, 422, f"new_dir message field missing, do not know which directory to put file in. skipping." )
                continue

            if not 'new_file' in msg or not msg['new_file']:
                self.reject(msg, 422, f"new_file message field missing, do not know name of file to write. skipping." )
                continue

            new_path = msg['new_dir'] + os.path.sep + msg['new_file']
            new_file = msg['new_file']

            if not os.path.isdir(msg['new_dir']):
                try:
                    logger.debug( f"missing destination directories, makedirs: {msg['new_dir']} " )
                    self.worklist.directories_ok.append(msg['new_dir'])
                    os.makedirs(msg['new_dir'], 0o775, True)
                except Exception as ex:
                    logger.warning("making %s: %s" % (msg['new_dir'], ex))
                    logger.debug('Exception details:', exc_info=True)
        
            os.chdir(msg['new_dir'])
            logger.debug( f"chdir {msg['new_dir']}")

            if 'fileOp' in msg :
                if 'rename' in msg['fileOp']:

                    if 'renameUnlink' in msg:
                        self.removeOneFile(msg['fileOp']['rename'])
                        msg.setReport(201, 'old unlinked %s' % msg['fileOp']['rename'])
                        self.worklist.ok.append(msg)
                        self.metrics['flow']['transferRxFiles'] += 1
                        self.metrics['flow']['transferRxLast'] = msg['report']['timeCompleted']

                    else:
                        # actual rename...
                        ok = self.renameOneItem(msg['fileOp']['rename'], new_path)
                        # if rename succeeds, fall through to download object to find if the file renamed
                        # actually matches the one advertised, and potentially download it.
                        # if rename fails, recover by falling through to download the data anyways.
                        if ok:
                            self.worklist.ok.append(msg)
                            self.metrics['flow']['transferRxFiles'] += 1
                            msg.setReport(201, 'renamed')
                            self.metrics['flow']['transferRxLast'] = msg['report']['timeCompleted']
                            continue

                elif ('directory' in msg['fileOp']) and ('remove' in msg['fileOp'] ): 
                    if  'rmdir' not in self.o.fileEvents:
                        self.reject(msg, 202, "skipping rmdir %s" % new_path)
                        continue

                    if self.removeOneFile(new_path):
                        msg.setReport(201, 'rmdired')
                        self.worklist.ok.append(msg)
                        self.metrics['flow']['transferRxFiles'] += 1
                        self.metrics['flow']['transferRxLast'] = msg['report']['timeCompleted']
                    else:
                        #FIXME: should this really be queued for retry? or just permanently failed?
                        # in rejected to avoid retry, but wondering if failed and deferred
                        # should be separate lists in worklist...
                        self.reject(msg, 500, "rmdir %s failed" % new_path)
                    continue

                elif ('remove' in msg['fileOp']):
                    if 'delete' not in self.o.fileEvents:
                        self.reject(msg, 202, "skipping delete %s" % new_path)
                        continue

                    if self.removeOneFile(new_path):
                        msg.setReport(201, 'removed')
                        self.worklist.ok.append(msg)
                        self.metrics['flow']['transferRxFiles'] += 1
                        self.metrics['flow']['transferRxLast'] = msg['report']['timeCompleted']
                    else:
                        #FIXME: should this really be queued for retry? or just permanently failed?
                        # in rejected to avoid retry, but wondering if failed and deferred
                        # should be separate lists in worklist...
                        self.reject(msg, 500, "remove %s failed" % new_path)
                    continue

                # no elif because if rename fails and operation is an mkdir or a symlink..
                # need to retry as ordinary creation, similar to normal file copy case.
                if 'directory' in msg['fileOp']:
                    if 'mkdir' not in self.o.fileEvents:
                        self.reject(msg, 202, "skipping mkdir %s" % new_path)
                        continue

                    if self.mkdir(msg):
                        msg.setReport(201, 'made directory')
                        self.worklist.ok.append(msg)
                        self.metrics['flow']['transferRxFiles'] += 1
                        self.metrics['flow']['transferRxLast'] = msg['report']['timeCompleted']
                    else:
                        # as above...
                        self.reject(msg, 500, "mkdir %s failed" % msg['new_file'])
                    continue

                elif 'link' in msg['fileOp'] or 'hlink' in msg['fileOp']:
                    if 'link' not in self.o.fileEvents:
                        self.reject(msg, 202, "skipping link %s" % new_path)
                        continue

                    if self.link1file(msg):
                        msg.setReport(201, 'linked')
                        self.worklist.ok.append(msg)
                        self.metrics['flow']['transferRxFiles'] += 1
                        self.metrics['flow']['transferRxLast'] = msg['report']['timeCompleted']
                    else:
                        # as above...
                        self.reject(msg, 500, "link %s failed" % msg['fileOp'])
                    continue

            # all non-files taken care of above... rest of routine is normal file download.

            if self.o.fileSizeMax > 0 and msg['size'] > self.o.fileSizeMax:
                self.reject(msg, 413, f"Payload Too Large {msg.getIDStr()}")
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
                logger.error('interval inflight setting: %s, not appropriate for downloads.' %
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
                    how_old = time.time() - os.path.getmtime(msg['new_inflight_path'])
                    #FIXME: if mtime > 5 minutes, perhaps rm it, and continue? what if transfer crashed?
                    #       Added this with fixed value, should it be a setting?
                    if how_old > 300:
                        os.unlink( msg['new_inflight_path'] )
                        logger.info(
                            f"inflight file is {how_old}s old. Removed previous attempt {msg['new_path']}" )
                    else:
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
                    self.metrics['flow']['transferRxLast'] = msg['report']['timeCompleted']
                    continue
                logger.warning(
                    "failed to write inline content %s, falling through to download"
                    % new_path)

            parsed_url = sarracenia.baseUrlParse(msg['baseUrl'])
            self.scheme = parsed_url.scheme

            i = 1
            while i <= self.o.attempts:

                if i > 1:
                    logger.warning("downloading again, attempt %d" % i)

                ok = self.download(msg, self.o)
                if ok == 1:
                    logger.debug("downloaded ok: %s" % new_path)
                    msg.setReport(201, "Download successful" )
                    # if content is present, but downloaded anyways, then it is no good, and should not be forwarded.
                    if 'content' in msg:
                        del msg['content']
                    self.worklist.ok.append(msg)
                    self.metrics['flow']['transferRxLast'] = msg['report']['timeCompleted']
                    break
                elif ok == -1:
                    logger.debug("download failed permanently, discarding transfer: %s" % new_path)
                    msg.setReport(410, "message received for content that is no longer available" )
                    self.worklist.rejected.append(msg)
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
    def download(self, msg, options) -> int:
        """
           download/transfer one file based on message, return True if successful, otherwise False.

           return 0 -- failed, retry later.
           return 1 -- OK download successful.
           return -1 -- download failed permanently, retry not useful.
        """

        self.o = options

        if 'retrievePath' in msg:
            logger.debug("%s_transport download override retrievePath=%s" % (self.scheme, msg['retrievePath']))
            remote_file = msg['retrievePath']
            cdir = None
            if msg['relPath'][0] == '/' or msg['baseUrl'][-1] == '/':
                urlstr = msg['baseUrl'] + msg['relPath']
            else:
                urlstr = msg['baseUrl'] + '/' + msg['relPath']
        else:
            logger.debug("%s_transport download relPath=%s" % (self.scheme, msg['relPath']))

            # split the path to the file and the file
            # if relPath is just the file remote_path will return empty
            remote_path, remote_file = os.path.split(msg['relPath'])

            u = sarracenia.baseUrlParse(msg['baseUrl']) 
            logger.debug( f"baseUrl.path= {u.path} ")
            if remote_path:
                if u.path: 
                    if ( u.path[-1] != '/' ) and ( remote_path[0] != '/' ) :
                        remote_path = u.path + '/' + remote_path
                    else:
                        remote_path = u.path + remote_path

                cdir = remote_path
            else:
                if u.path:
                    cdir=u.path
                else:
                    cdir=None

            if msg['relPath'][0] == '/' or msg['baseUrl'][-1] == '/':
                urlstr = msg['baseUrl'] + msg['relPath']
            else:
                urlstr = msg['baseUrl'] + '/' + msg['relPath']


        istr =msg['identity']  if ('identity' in msg) else "None"
        fostr = msg['fileOp'] if ('fileOp' in msg ) else "None"

        logger.debug( 'identity: %s, fileOp: %s' % ( istr, fostr ) ) 
        new_inflight_path = ''

        new_dir = msg['new_dir']
        new_file = msg['new_file']
        new_inflight_path = None

        if 'blocks' in msg: 
            if msg['blocks']['method'] in [ 'inplace' ]: # download only a specific block from a file, not the whole thing.
                logger.debug( f"splitting 1 file into {len(msg['blocks']['manifest'])} block messages." )
                blkno = msg['blocks']['number']
                blksz_l = sarracenia.naturalSize(msg['blocks']['size']).split()
                blksz = blksz_l[0]+blksz_l[1][0].lower()
                if not '§block_' in new_file:
                    new_file += f"§block_{blkno:04d},{blksz}_§"
                msg['new_file'] = new_file

        if options.inflight == None:
            new_inflight_path = new_file
        elif type(options.inflight) == str:
            if options.inflight == '.':
                new_inflight_path = '.' + new_file
            elif ( options.inflight[-1] == '/' ) or (options.inflight[0] == '/'):
                new_inflight_path = options.inflight + new_file
            elif options.inflight[0] == '.':
                new_inflight_path = new_file + options.inflight
        else:
            logger.error('inflight setting: %s, not for downloads.' %
                         options.inflight)
        if new_inflight_path:
            msg['new_inflight_path'] = new_inflight_path
            msg['_deleteOnPost'] |= set(['new_inflight_path'])

        if 'download' in self.plugins and len(self.plugins['download']) > 0:
            ok = False
            for plugin in self.plugins['download']:
                try:
                    ok = plugin(msg)
                    if type(ok) is not bool:
                        logger.error( f"{plugin} returned {type(ok)}. Should return boolean" )
                except Exception as ex:
                    logger.error( f'flowCallback plugin {plugin} crashed: {ex}' )
                    logger.debug( "details:", exc_info=True )

                if not ok: return 0
            return 1

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
                logger.debug( f"local cd to {new_dir}") 
            except Exception as ex:
                logger.warning("making %s: %s" % (new_dir, ex))
                logger.debug('Exception details:', exc_info=True)
                return 0

        try:
            options.sendTo = msg['baseUrl']

            if (not (self.scheme in self.proto)) or (self.proto[self.scheme] is None):
                self.proto[self.scheme] = sarracenia.transfer.Transfer.factory(self.scheme, self.o)
                self.metrics['flow']['transferConnected'] = True
                self.metrics['flow']['transferConnectStart'] = time.time() 

            if (not self.o.dry_run) and not self.proto[self.scheme].check_is_connected():

                    if self.metrics['flow']['transferConnected']: 
                         now=nowflt()
                         self.metrics['flow']['transferConnectTime'] += now - self.metrics['flow']['transferConnectStart']
                         self.metrics['flow']['transferConnectStart'] = 0
                         self.metrics['flow']['transferConnected'] = False

                    logger.debug("%s_transport download connects" % self.scheme)
                    ok = self.proto[self.scheme].connect()
                    if not ok:
                        self.proto[self.scheme] = None
                        return 0

                    self.metrics['flow']['transferConnected'] = True
                    self.metrics['flow']['transferConnectStart'] = time.time() 
                    logger.debug('connected')

            #=================================
            # if parts, check that the protol supports it
            #=================================

            #if not hasattr(proto,'seek') and ('blocks' in msg) and ( msg['blocks']['method'] == 'inplace' ):
            #   logger.error("%s, inplace part file not supported" % self.scheme)
            #   return 0

            cwd = None
         
            if (not self.o.dry_run) and hasattr(self.proto[self.scheme], 'getcwd'):
                cwd = self.proto[self.scheme].getcwd()
                logger.debug( f" from proto getcwd: {cwd} ")

            if cdir and cwd != cdir:
                logger.debug("%s_transport remote cd to %s" % (self.scheme, cdir))
                if self.o.dry_run:
                    cwd = cdir
                else:
                    try:
                         self.proto[self.scheme].cd(cdir)
                    except Exception as ex:
                         logger.error("chdir %s: %s" % (cdir, ex))
                         return 0

            remote_offset = 0
            exactLength=False
            if ('blocks' in msg) and (msg['blocks']['method'] == 'inplace'):
                blkno=msg['blocks']['number']
                remote_offset=0
                exactLength=True
                while blkno > 0:
                    blkno -= 1
                    remote_offset += msg['blocks']['manifest'][blkno]['size']

                block_length=msg['blocks']['manifest'][msg['blocks']['number']]['size']
                logger.debug( f"offset calculation:  start={remote_offset} count={block_length}" )

            elif 'size' in msg:
                block_length = msg['size']
            else:
                block_length = 0

            #download file

            logger.debug(
                'Beginning fetch of %s %d-%d into %s %d-%d' %
                (urlstr, remote_offset, block_length-1, new_inflight_path, msg['local_offset'],
                 msg['local_offset'] + block_length - 1))

            # FIXME  locking for i parts in temporary file ... should stay lock
            # and file_reassemble... take into account the locking

            if self.o.identity_method.startswith('cod,'):
                download_algo = self.o.identity_method[4:]
            elif 'identity' in msg:
                if msg['identity']['method'] == 'cod':
                    download_algo = msg['identity']['value']
                else:
                    download_algo = msg['identity']['method']
            else:
                download_algo = None

            if download_algo:
                self.proto[self.scheme].set_sumalgo(download_algo)

            if download_algo == 'arbitrary':
                self.proto[self.scheme].set_sumArbitrary(
                    msg['identity']['value'])

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
                try:
                    if accelerated:
                        len_written = self.proto[self.scheme].getAccelerated(
                            msg, remote_file, new_inflight_path, block_length, remote_offset, exactLength)
                        #FIXME: no onfly_checksum calculation during download.
                    else:
                        self.proto[self.scheme].set_path(new_inflight_path)
                        len_written = self.proto[self.scheme].get(
                            msg, remote_file, new_inflight_path, remote_offset,
                            msg['local_offset'], block_length, exactLength)
                except Exception as ex:
                    logger.error( f"could not get {remote_file}: {ex}" )
                    return 0

            else:
                len_written = block_length

            if ('blocks' in msg) and (msg['blocks']['method'] == 'inplace'):
                msg['blocks']['method'] = 'separate'

            if (len_written == block_length):
                if not self.o.dry_run:
                    if accelerated:
                        self.proto[self.scheme].update_file(new_inflight_path)
            elif len_written < 0:
                logger.error("failed to download %s" % new_file)
                if (self.o.inflight != None) and os.path.isfile(new_inflight_path):
                    os.remove(new_inflight_path)
                return 0
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
                        logger.info(
                            'AcceptSizeWrong download size mismatch, received %d of expected %d bytes for %s'
                            % (len_written, block_length, new_inflight_path))
                    else:
                        retval=0
                        if hasattr( self.proto[self.scheme],'stat'):
                            current_stat = self.proto[self.scheme].stat( remote_file, msg )
                            if 'mtime' in msg:
                                mtime = sarracenia.timestr2flt(msg['mtime'])
                            else:
                                mtime = sarracenia.timestr2flt(msg['pubTime'])

                            if current_stat and current_stat.st_mtime and current_stat.st_mtime > mtime:
                                logger.info( f'upstream resource is newer, so message {msg.getIDStr()} is obsolete. Discarding.' )
                                retval=-1
                            elif current_stat and current_stat.st_size and current_stat.st_size == len_written:
                                logger.info( f'matches upstream source, {msg.getIDStr()} but not announcement. Discarding.' )
                                retval=-1 
                            else:
                                logger.error( f"unexplained size discrepancy in {msg.getIDStr()}, will retry later" )
                        elif len_written > block_length:
                            logger.error( f'download more {len_written} than expected {block_length} bytes for {new_inflight_path}' )
                        else:
                            logger.error( f'incomplete download only {len_written} of expected {block_length} bytes for {new_inflight_path}' )

                        if (self.o.inflight != None) and os.path.isfile(new_inflight_path):
                            os.remove(new_inflight_path)
                        return retval 
                # when len_written is different than block_length
                msg['size'] = len_written

            # if we haven't returned False by this point, assuming download was successful
            if (new_inflight_path != new_file):
                if os.path.isfile(new_file):
                    os.remove(new_file)
                os.rename(new_inflight_path, new_file)
            
            # older versions don't include the contentType, so patch it here.
            if features['filetypes']['present'] and 'contentType' not in msg:
                msg['contentType'] = magic.from_file(new_file,mime=True)

            self.metrics['flow']['transferRxBytes'] += len_written
            self.metrics['flow']['transferRxFiles'] += 1

            if download_algo and not self.o.dry_run:
                msg['onfly_checksum'] = self.proto[self.scheme].get_sumstr()
                msg['data_checksum'] = self.proto[self.scheme].data_checksum

                if self.o.identity_method.startswith('cod,') and not accelerated:
                    msg['identity'] = msg['onfly_checksum']

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
                except Exception as ex:
                    logger.error( f'unable to delete remote file {remote_file}: {ex}' )
                    logger.debug('Exception details: ', exc_info=True)

            if (self.o.acceptSizeWrong or (block_length == 0)) and (len_written > 0):
                return 1

            if (len_written != block_length):
                return 0

        except Exception as ex:
            logger.debug('Exception details: ', exc_info=True)
            logger.warning("failed to write %s: %s" % (new_inflight_path, ex))

            #closing on problem
            if not self.o.dry_run:
                try:
                    self.proto[self.scheme].close()
                except:
                    logger.debug('closing exception details: ', exc_info=True)
            self.metrics['flow']["transferConnected"] = False
            if 'transferConnectLast' in self.metrics['flow']:
                self.metrics['flow']['transferConnectedTime'] = time.time() - self.metrics['flow']['transferConnectLast']
            else:
                self.metrics['flow']['transferConnectedTime'] = 0
            self.cdir = None
            self.proto[self.scheme] = None
        
            if (not self.o.dry_run) and os.path.isfile(new_inflight_path):
                os.remove(new_inflight_path)
            return 0
        return 1

    # generalized send...
    def send(self, msg, options):
        self.o = options
        sendTo=self.o.sendTo 
        logger.debug( f"{self.scheme}_transport sendTo: {sendTo}" )
        logger.debug("%s_transport send %s %s" %
                     (self.scheme, msg['new_dir'], msg['new_file']))

        if len(self.plugins['send']) > 0:
            ok = False
            for plugin in self.plugins['send']:
                try:
                    ok = plugin(msg)
                    if type(ok) is not bool:
                        logger.error( f"{plugin} returned {type(ok)}. Should return boolean" )
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

        # older versions don't include the contentType, so patch it here.
        if features['filetypes']['present'] and \
           ('contentType' not in msg) and (not 'fileOp' in msg):
            msg['contentType'] = magic.from_file(local_path,mime=True)

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
    
                    if self.metrics['flow']['transferConnected']: 
                         now = nowflt()
                         self.metrics['flow']['transferConnectTime'] += now - self.metrics['flow']['transferConnectStart']
                         self.metrics['flow']['transferConnectStart'] = 0
                         self.metrics['flow']['transferConnected'] = False

                    self.proto[self.scheme] = sarracenia.transfer.Transfer.factory( self.scheme, options)
    
                    ok = self.proto[self.scheme].connect()
                    if not ok: return False
                    self.cdir = None
                    self.metrics['flow']['transferConnected'] = True
                    self.metrics['flow']['transferConnectStart'] = time.time() 

            elif not (self.scheme in self.proto) or self.proto[self.scheme] is None:
                logger.debug("dry_run %s_transport send connects" % self.scheme)
                self.proto[self.scheme] = sarracenia.transfer.Transfer.factory( self.scheme, options)
                self.cdir = None
                self.metrics['flow']['transferConnected'] = True
                self.metrics['flow']['transferConnectStart'] = time.time() 

            #=================================
            # if parts, check that the protocol supports it
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
                    try:
                        cwd = self.proto[self.scheme].getcwd()
                    except Exception as ex:
                        logger.error( f"could not getcwd on {sendTo} : {ex}" )
                        return False

            if cwd != new_dir:
                logger.debug("%s_transport send cd to %s" %
                             (self.scheme, new_dir))
                if not self.o.dry_run:
                    try:
                        self.proto[self.scheme].cd_forced(new_dir)
                    except Exception as ex:
                        logger.error( f"could not chdir to {sendTo} {new_dir}: {ex}" )
                        return False

            #=================================
            # delete event
            #=================================

            if 'fileOp' in msg:
                if 'remove' in msg['fileOp'] :
                    if hasattr(self.proto[self.scheme], 'delete'):
                        logger.debug("message is to remove %s" % new_file)
                        if not self.o.dry_run:
                            if 'directory' in msg['fileOp']: 
                                try:
                                    self.proto[self.scheme].rmdir(new_file)
                                except Exception as ex:
                                    logger.error( f"could not rmdir {sendTo} {msg['new_dir']}/{new_file}: {ex}" )
                                    return False
                            else:
                                try:
                                    self.proto[self.scheme].delete(new_file)
                                except Exception as ex:
                                    logger.error( f"could not delete {sendTo} {msg['new_dir']}/{new_file}: {ex}" )
                                    return False

                        msg.setReport(201, f'file or directory removed')
                        self.metrics['flow']['transferTxFiles'] += 1
                        self.metrics['flow']['transferTxLast'] = msg['report']['timeCompleted']
                        return True
                    logger.error("%s, delete not supported" % self.scheme)
                    return False

                if 'rename' in msg['fileOp'] :
                    if hasattr(self.proto[self.scheme], 'delete'):
                        logger.debug( f"message is to rename {msg['fileOp']['rename']} to {new_file}" )
                        if not self.o.dry_run:
                            try:
                                self.proto[self.scheme].rename(msg['fileOp']['rename'], new_file)
                            except Exception as ex:
                                logger.error( f"could not rename {sendTo} (in {msg['new_dir']} {msg['fileOp']['rename']} to {new_file}: {ex}" )
                                return False

                        msg.setReport(201, f'file renamed')
                        self.metrics['flow']['transferTxFiles'] += 1
                        self.metrics['flow']['transferTxLast'] = msg['report']['timeCompleted']
                        return True
                    logger.error("%s, delete not supported" % self.scheme)
                    return False

                if 'directory' in msg['fileOp'] :
                    if 'contentType' not in msg:
                        msg['contentType'] = 'text/directory'
                    if hasattr(self.proto[self.scheme], 'mkdir'):
                        logger.debug( f"message is to mkdir {new_file}")
                        if not self.o.dry_run:
                            try:
                                self.proto[self.scheme].mkdir(new_file)
                            except Exception as ex:
                                logger.error( f"could not mkdir {sendTo} {msg['new_dir']}/{new_file}: {ex}" )
                                return False
                        msg.setReport(201, f'directory created')
                        self.metrics['flow']['transferTxFiles'] += 1
                        self.metrics['flow']['transferTxLast'] = msg['report']['timeCompleted']
                        return True
                    logger.error("%s, mkdir not supported" % self.scheme)
                    return False


                #=================================
                # link event
                #=================================

                if 'hlink' in msg['fileOp']:
                    if 'contentType' not in msg:
                        msg['contentType'] = 'text/link'
                    if hasattr(self.proto[self.scheme], 'link'):
                        logger.debug("message is to link %s to: %s" % (new_file, msg['fileOp']['hlink']))
                        if not self.o.dry_run:
                            try:
                                self.proto[self.scheme].link(msg['fileOp']['hlink'], new_file)
                            except Exception as ex:
                                logger.error( f"could not link {sendTo} in {msg['new_dir']}{os.sep}{msg['fileOp']['hlink']} to {new_file}: {ex}" )
                                return False
                        return True
                    logger.error("%s, hardlinks not supported" % self.scheme)
                    return False
                elif 'link' in msg['fileOp']:
                    if 'contentType' not in msg:
                        msg['contentType'] = 'text/link'
                    if hasattr(self.proto[self.scheme], 'symlink'):
                        logger.debug("message is to link %s to: %s" % (new_file, msg['fileOp']['link']))
                        if not self.o.dry_run:
                            try:
                                self.proto[self.scheme].symlink(msg['fileOp']['link'], new_file)
                            except Exception as ex:
                                logger.error( f"could not symlink {sendTo} in {msg['new_dir']} {msg['fileOp']['link']} to {new_file}: {ex}" )
                                return False
                        msg.setReport(201, f'file linked')
                        self.metrics['flow']['transferTxFiles'] += 1
                        self.metrics['flow']['transferTxLast'] = msg['report']['timeCompleted']
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
            elif 'size' not in msg:
                msg['size'] = os.path.getsize(local_file)

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
                try:
                    if not self.o.dry_run:
                        if accelerated:
                            len_written = self.proto[self.scheme].putAccelerated( msg, local_file, new_file)
                        else:
                            len_written = self.proto[self.scheme].put( msg, local_file, new_file)
                except Exception as ex:
                    logger.error( f"could not send {local_dir}{os.sep}{local_file} to inflight=None {sendTo} {msg['new_dir']}/{new_file}: {ex}" )
                    return False
                
            elif (('blocks' in msg)
                  and (msg['blocks']['method'] == 'inplace')):
                if not self.o.dry_run:
                    try:
                        self.proto[self.scheme].put(msg, local_file, new_file, offset,
                                            new_offset, msg['size'])
                    except Exception as ex:
                        logger.error( f"could not send {local_dir}{os.sep}{local_file} inplace {sendTo} {msg['new_dir']}/{new_file}: {ex}" )
                        return False

            elif inflight == '.':
                new_inflight_path = '.' + new_file
                if not self.o.dry_run:
                    try:
                        if accelerated:
                            len_written = self.proto[self.scheme].putAccelerated(
                                msg, local_file, new_inflight_path)
                        else:
                            len_written = self.proto[self.scheme].put(
                                msg, local_file, new_inflight_path)
                    except Exception as ex:
                        logger.error( f"could not send {local_dir}{os.sep}{local_file} inflight={inflight} {sendTo} {msg['new_dir']}/{new_file}: {ex}" )
                        return False
                    try:
                        self.proto[self.scheme].rename(new_inflight_path, new_file)
                    except Exception as ex:
                        logger.error( f"could not rename inflight={inflight} {sendTo} {msg['new_dir']}/{new_file}: {ex}" )
                        return False
                else:
                    len_written = msg['size']

            elif inflight[0] == '.':
                new_inflight_path = new_file + inflight
                if not self.o.dry_run:
                    try:
                        if accelerated:
                            len_written = self.proto[self.scheme].putAccelerated(
                                msg, local_file, new_inflight_path)
                        else:
                            len_written = self.proto[self.scheme].put(msg, local_file, new_inflight_path)
                    except Exception as ex:
                        logger.error( f"could not send {local_dir}{os.sep}{local_file} inflight={inflight} {sendTo} {msg['new_dir']}/{new_file}: {ex}" )
                        return False
                    try:
                        self.proto[self.scheme].rename(new_inflight_path, new_file)
                    except Exception as ex:
                        logger.error( f"could not rename inflight={inflight} {sendTo} {msg['new_dir']}/{new_file}: {ex}" )
                        return False
            elif options.inflight[-1] == '/':
                if not self.o.dry_run:
                    try:
                        self.proto[self.scheme].cd_forced(
                            new_dir + '/' + options.inflight)
                        self.proto[self.scheme].cd_forced(new_dir)
                    except:
                        pass
                new_inflight_path = options.inflight + new_file
                if not self.o.dry_run:
                    try:
                        if accelerated:
                            len_written = self.proto[self.scheme].putAccelerated(
                                msg, local_file, new_inflight_path)
                        else:
                            len_written = self.proto[self.scheme].put(
                                msg, local_file, new_inflight_path)
                    except Exception as ex:
                        logger.error( f"could not send {local_dir}{os.sep}{local_file} inflight={inflight} {sendTo} {msg['new_dir']}/{new_file}: {ex}" )
                        return False
                    try:
                        self.proto[self.scheme].rename(new_inflight_path, new_file)
                    except Exception as ex:
                        logger.error( f"could not rename inflight={inflight} {sendTo} {msg['new_dir']}/{new_file}: {ex}" )
                        return False
                else:
                    len_written = msg['size']
            elif inflight == 'umask':
                if not self.o.dry_run:
                    self.proto[self.scheme].umask()
                    try:
                        if accelerated:
                            len_written = self.proto[self.scheme].putAccelerated(
                                msg, local_file, new_file)
                        else:
                            len_written = self.proto[self.scheme].put(
                                msg, local_file, new_file)
                    except Exception as ex:
                        logger.error( f"could not send {local_dir}{os.sep}{local_file} inflight={inflight} {sendTo} {msg['new_dir']}/{new_file}: {ex}" )
                        return False
                    try:
                        self.proto[self.scheme].put(msg, local_file, new_file)
                    except Exception as ex:
                        logger.error( f"could not rename inflight={inflight} {sendTo} {msg['new_dir']}/{new_file}: {ex}" )
                        return False
                else:
                    len_written = msg['size']

            msg.setReport(201, 'file sent')
            self.metrics['flow']['transferTxBytes'] += len_written
            self.metrics['flow']['transferTxFiles'] += 1
            self.metrics['flow']['transferTxLast'] = msg['report']['timeCompleted']

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

            now = nowflt()
            self.metrics['flow']['transferConnectTime'] += now - self.metrics['flow']['transferConnectStart']
            self.metrics['flow']['transferConnectStart']=0
            self.metrics['flow']['transferConnected']=False
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
        logger.debug("%s" % local_file)

        # if the file is not partitioned, the the onfly_checksum is for the whole file.
        # cache it here, along with the mtime, unless block_reassembly plugin is active...
        
        if ('blocks' in msg) and sarracenia.features['reassembly']['present'] and not self.block_reassembly_active:
            with sarracenia.blockmanifest.BlockManifest(local_file) as bm:
                bm.set( msg['blocks'] )

        x = sarracenia.filemetadata.FileMetadata(local_file)
        # FIXME ... what to do when checksums don't match?
        if 'onfly_checksum' in msg: 
            x.set( 'identity', msg['onfly_checksum'] )
        elif 'identity' in msg:
            x.set('identity', msg['identity'] )

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

        if hasattr(proto, 'utime'):
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

            if not 'new_dir' in msg or not msg['new_dir']:
                self.reject(msg, 422, f"new_dir message field missing, do not know which directory to put file in. skipping." )
                continue

            if not 'new_file' in msg or not msg['new_file']:
                self.reject(msg, 422, f"new_file message field missing, do not know name of file to write. skipping." )
                continue

            # weed out non-file transfer operations that are configured to not be done.
            if 'fileOp' in msg:
                if ('directory' in msg['fileOp']) and ('remove' in msg['fileOp']) and ( 'rmdir' not in self.o.fileEvents ):
                    self.reject(msg, 202, "skipping rmdir here." )
                    continue

                elif ('remove' in msg['fileOp']) and ( 'delete' not in self.o.fileEvents ):
                    self.reject(msg, 202, "skipping delete here." )
                    continue

                if ('directory' in msg['fileOp']) and ( 'mkdir' not in self.o.fileEvents ):
                    self.reject(msg, 202, "skipping mkdir here." )
                    continue

                if ('hlink' in msg['fileOp']) and ( 'link' not in self.o.fileEvents ):
                    self.reject(msg, 202, "skipping hlink here." )
                    continue

                if ('link' in msg['fileOp']) and ( 'link' not in self.o.fileEvents ):
                    self.reject(msg, 202, "skipping link here." )
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
