#!/usr/bin/env python3

#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Shared Services Canada, 2019
#
"""
   parallel version of sr. Generates a global state, then performs an action.
   previous version would, recursion style, launch individual components.

   TODO:
       - when number of instances changes, currently have to stop/start individual component.
         would be nice if srp, would notice and fix in sr sanity.

       - perhaps accept subsets of configuration as globs?
         just reduces the set of configs already read that are operated on.

"""

from functools import partial

import copy
import fnmatch
import getpass
import inspect
import json
import logging
import os
import os.path
import pathlib
import platform
import random
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import traceback

from sarracenia.flowcb.v2wrapper import sum_algo_v2tov3

from sarracenia import user_config_dir, user_cache_dir, naturalSize, nowstr, timestr2flt, timeflt2str, durationToString
from sarracenia.config import *
import sarracenia.moth
import sarracenia.rabbitmq_admin

if sarracenia.features['process']['present']:
   import psutil

import urllib.parse

logger = logging.getLogger(__name__)

empty_metrics={ "byteRate":0, "cpuTime":0, "rejectCount":0, "last_housekeeping":0, "messagesQueued": 0, 
        "lagMean": 0, "latestTransfer": 0, "rejectPercent":0, "transferRxByteRate":0, "transferTxByteRate": 0,
        "rxByteCount":0, "rxGoodCount":0, "rxBadCount":0, "txByteCount":0, "txGoodCount":0, "txBadCount":0, 
        "lagMax":0, "lagTotal":0, "lagMessageCount":0, "disconnectTime":0, "transferConnectTime":0, 
        "transferRxLast": 0, "transferTxLast": 0, "rxLast":0, "txLast":0, 
        "transferRxBytes":0, "transferRxFiles":0, "transferTxBytes": 0, "transferTxFiles": 0, 
        "msgs_in_post_retry": 0, "msgs_in_download_retry":0, "brokerQueuedMessageCount": 0, 
        'time_base': 0, 'byteTotal': 0, 'byteRate': 0, 'msgRate': 0, 'msgRateCpu': 0, 'retry': 0, 
        'messageLast': 0, 'transferLast': 0, 'connectPercent': 0, 'byteConnectPercent': 0
        }

sr3_tools_entry_points = [ "sr3_action_convert", "sr3_action_remove", "sr3_commit", "sr3_pull", "sr3_push", "sr3_remove", "sr3_scp", "sr3_ssh", "sr3_utils", "sr3d", "sr3l", "sr3r" ]

def ageOfFile(lf) -> int:
    """ return number of seconds since a file was modified as a floating point number of seconds.
        FIXME: mocked here for now. 
    """
    st=os.stat(lf)
    return st.st_mtime

def signal_pid( pid, sig ) -> int:
    """
        wrap os.kill in a try/except for cleaner error messages and avoid control jumping somewhere
        unexpected.
    """
    try:
       os.kill(pid, sig)
       return 0
    except ProcessLookupError:
        return -2

    except Exception as ex:
       logger.warning('sending kill signal to pid:%s failed: %s' % ( pid, ex))
       return -1

# noinspection PyArgumentList
class sr_GlobalState:
    """
       build a global state of all sarra processes running on the system for this user.
       makes three data structures:  procs, configs, and states, indexed by component
       and configuration name.

       self.(procs|configs|states)[ component ][ config ]  something...

       naming: routines that start with *read* don't modify anything on disk.
               routines that start with clean do...
          
    """
    def _find_component_path(self, c):
        """
            return the string to be used to run a component in Popen.
        """
        if c in [ 'flow',
                'poll', 'report', 'sarra', 'sender', 'shovel', 'subscribe',
                'watch', 'winnow'
        ]:
            c = 'flow'
        if c[0] != 'c':  # python components
            s = self.bin_dir + os.sep + 'sr_' + c
            if not os.path.exists(s):
                s += '.py'
            if not os.path.exists(s):
                print("don't know where the script files are for: %s" % c)
                return ''
            return s
        else:  # C components
            return 'sr3_' + c

    def _launch_instance(self, component_path, c, cfg, i):
        """
          start up a instance process (always daemonish/background fire & forget type process.)
        """

        if cfg is None:
            lfn = self.log_dir + os.sep + c + "_%02d" % i + '.log'
        else:
            if not self.configs[c][cfg]['options'].logStdout:
                # FIXME: honouring statehost missing.
                if self.configs[c][cfg]['options'].statehost:
                    lfn = self.user_cache_dir + os.sep + self.hostdir
                else:
                    lfn = self.user_cache_dir

                lfn += os.sep + 'log' + os.sep + c + '_' + cfg + "_%02d" % i + '.log'

                dir_not_there = not os.path.exists( os.path.dirname(lfn) )

                while dir_not_there:
                    try:
                        os.makedirs(os.path.dirname(lfn), exist_ok=True)
                        dir_not_there = False 
                    except FileExistsError:
                        dir_not_there = False 
                    except Exception as ex:
                        logging.error( "makedirs {} failed err={}".format(os.path.dirname(lfn),ex))
                        logging.debug("Exception details:", exc_info=True)
                        time.sleep(0.1)
                
        if c in [ 'flow',
                'poll', 'post', 'report', 'sarra', 'sender', 'shovel',
                'subscribe', 'watch', 'winnow'
        ]:
            component_path = os.path.dirname(
                component_path) + os.sep + 'instance.py'
            cmd = [sys.executable, component_path, '--no', "%d" % i]

            # would like to forward things like --debug...
            for arg in sys.argv[1:-1]:
                if arg in ['start', 'restart', 'run']:
                    break
                cmd.append(arg)

            cmd.extend(['start', c + os.sep + cfg])
        else:
            if c[0] != 'c':  # python components
                if cfg is None:
                    cmd = [
                        sys.executable, component_path, '--no',
                        "%d" % i, 'start'
                    ]
                else:
                    cmd = [
                        sys.executable, component_path, '--no',
                        "%d" % i, 'start', cfg
                    ]
            else:  # C components
                cmd = [component_path, 'start', cfg]

        #print("launching +%s+  re-directed to: %s" % (cmd, lfn), flush=True)
        if self.options.dry_run:
            print( f"dry_run would launch: {cmd} >{lfn} 2>&1")
            return

        try:
            if self.configs[c][cfg]['options'].logStdout:
                subprocess.Popen(cmd)
            else:
                with open(lfn, "a") as lf:
                    subprocess.Popen(cmd,
                                 stdin=subprocess.DEVNULL,
                                 stdout=lf,
                                 stderr=subprocess.STDOUT)
            #print( f"launched: {cmd}" )
        except Exception as ex:
            print("failed to launch: %s >%s >2&1 (reason: %s) " %
                  (' '.join(cmd), lfn, ex))

    def save_procs(self, File="procs.json"):
        """
           dump image of process table to a file, one process per line, JSON UTF-8 encoded.
        """
        print('save_procs to: %s' % File)
        with open(File, 'a') as f:
            f.seek(0, 0)
            f.truncate()
            f.write(getpass.getuser() + '\n')

            if not features['process']['present']:
                return

            for proc in psutil.process_iter():
                f.write(
                    json.dumps(proc.as_dict(
                        ['pid', 'cmdline', 'name', 'username', 'create_time', 'memory_info', 'cpu_times']),
                               ensure_ascii=False) + '\n')

    def _filter_sr_proc(self, p):

        #print( 'sr0? name=%s, pid=%s, cmdline=%s' % ( p['name'], p['pid'], p['cmdline'] ) )
        if self.me != p['username'] :
            return

        # process name 'python3' is not helpful, so overwrite...
        if 'python' in p['name']:
            if len(p['cmdline']) < 2:
                return
            n = os.path.basename(p['cmdline'][1])
            if n == 'instance.py':
                n = 'sr3_' + p['cmdline'][-1].split(os.sep)[0] + '.py'
            p['name'] = n
        
        if p['name'][0:2] != 'sr' :
            return

        if list(filter(p['name'].startswith, sr3_tools_entry_points)) != []:
            print( f"skipping sr3_tools process: {p['name']}" )
            return

        #print( 'sr? name=%s, pid=%s, cmdline=%s' % ( p['name'], p['pid'], p['cmdline'] ) )
        if ( sys.platform == 'win32') and ( p['name'][-4:].lower() == '.exe' ):
            # on windows, it seems to fork .exe and then there is a -script.py which is the right pid
            # .e.g sr_subscribe.exe -> sr_subscribe-script.py ... If you kill the -script, the .exe goes away.
            return

        if p['name'].startswith('sr3_'):
            #print( f"starts with sr3_ cmdline={p['cmdline']}" )
            p['memory'] = p['memory_full_info']._asdict()
            p['cpu'] = p['cpu_times']._asdict()
            del p['memory_full_info'] 
            del p['cpu_times']
            self.procs[p['pid']] = p
            self.procs[p['pid']]['claimed'] =   (p['name'][-4:] == 'post') or \
                    any( item in [ 'declare', 'edit', 'foreground', 'sanity', 'setup', 'status' ] for item in  p['cmdline'] )

    def read_proc_file(self, File="procs.json"):
        """
           read process table from a save file, for reproducible testing.
        """
        self.procs = {}
        print('getting procs from %s: ' % File, end='', flush=True)
        pcount = 0
        with open(File, 'r') as f:
            self.me = f.readline().rstrip()
            for pj in f.readlines():
                p = json.loads(pj)
                self._filter_sr_proc(p)
                pcount += 1
                if pcount % 100 == 0: print('.', end='', flush=True)
        print(' Done! Read %d procs' % (pcount), flush=True)

    def _read_procs(self):
        # read process table from the system
        self.procs = {}
        self.me = getpass.getuser()
        if sys.platform == 'win32':
            self.me = os.environ['userdomain'] + '\\' + self.me
        if not features['process']['present']:
            return
        for proc in psutil.process_iter():
            try:
                self._filter_sr_proc(
                    proc.as_dict(
                        ['pid', 'cmdline', 'name', 'username', 'create_time', 'memory_full_info', 'cpu_times']))
            except:
                pass # the process went away while iterating. avoid spurious message.

    def _read_configs(self):
        # read in configurations.
        self.configs = {}
        if not os.path.isdir(self.user_config_dir):
            return

        self.default_cfg = sarracenia.config.default_config()

        os.chdir(self.user_config_dir)

        for c in self.components:
            if os.path.isdir(c):
                os.chdir(c)
                self.configs[c] = {}
                for cfg in os.listdir():
                    if cfg[0] == '.':
                        continue
                    numi = 0
                    if cfg[-5:] == '.conf':
                        cbase = cfg[0:-5]
                        state = 'stopped'
                    elif cfg[-4:] == '.inc':
                        cbase = cfg[0:-5]
                        state = 'include'
                        continue
                    else:
                        continue

                    self.configs[c][cbase] = {}
                    self.configs[c][cbase]['status'] = state
                    if state != 'unknown':
                        cfgbody = copy.deepcopy(self.default_cfg)
                        cfgbody.override({
                            'component': c,
                            'config': cbase,
                            'action': self.options.action,
                            'directory': '${PWD}'
                        })
                        cfgbody.applyComponentDefaults( c )
                        cfgbody.parse_file(cfg,c)
                        cfgbody.finalize(c, cfg)
                        self.configs[c][cbase]['options'] = cfgbody

                        # ensure there is a known value of instances to run.
                        if c in ['poll', 'post', 'cpost']:
                            if hasattr(cfgbody,
                                       'sleep') and cfgbody.sleep not in [
                                           '-', '0'
                                       ]:
                                numi = 1
                        elif hasattr(cfgbody, 'instances'):
                            numi = int(cfgbody.instances)
                        else:
                            numi = 1
                        if ( numi > 1 ) and \
                           hasattr(cfgbody,'exchangeSplit'):
                            print( 'exchange: %s split: %d' % \
                               (cfgbody.exchange, numi) )
                            l = []
                            for i in range(0, numi):
                                l.append(cfgbody.exchange + '%02d' % i)
                            cfgbody.exchange = l

                    self.configs[c][cbase]['instances'] = numi

                os.chdir('..')

    def _cleanse_credentials(self, savename):
        """
           copy credentials to a savename file, replacing actual passwords with a place holder.

        """

        sno = 0

        with open(savename, 'w') as save_config_file:
            with open(self.user_config_dir + os.sep + 'credentials.conf',
                      'r') as config_file:
                for cfl in config_file.readlines():
                    lout = re.compile(':[^/][^/].*?@').sub(
                        ':secret%02d@' % sno, cfl, 1)
                    save_config_file.write(lout)
                    sno += 1

    def save_configs(self, savename):
        """ DEVELOPER only... copy configuration to an alternate tree 
        """
        os.chdir(self.user_config_dir)
        other_config_dir = sarracenia.user_config_dir(savename, self.appauthor)

        if not os.path.exists(other_config_dir):
            pathlib.Path(other_config_dir).mkdir(parents=True, exist_ok=True)

        for f in ['default.conf', 'admin.conf']:
            to = other_config_dir + os.sep + f
            print('save_configs copying: %s %s' % (f, to))
            shutil.copyfile(f, to)

        self._cleanse_credentials(other_config_dir + os.sep +
                                  'credentials.conf')

        for c in self.components:
            if os.path.isdir(c):
                os.chdir(c)
                other_c_dir = other_config_dir + os.sep + c
                if not os.path.exists(other_c_dir):
                    os.mkdir(other_c_dir)
                for cfg in os.listdir():
                    if cfg[0] == '.': continue
                    to = other_c_dir + os.sep + cfg
                    print('save_configs copying: %s %s' % (cfg, to))
                    shutil.copyfile(cfg, to)
                os.chdir('..')

    def _save_state_dir(self, savename, dir):
        """ DEVELOPER ONLY.. copy state files to an alternate tree.
        """

        if not os.path.isdir(dir):
            return
        os.chdir(dir)
        other_cache_dir = sarracenia.user_cache_dir(savename, self.appauthor)
        if os.path.basename(dir) == self.hostdir:
            other_cache_dir += os.sep + self.hostdir

        if not os.path.exists(other_cache_dir):
            os.mkdir(other_cache_dir)
        for c in self.components:
            if os.path.isdir(c):
                os.chdir(c)
                other_c_dir = other_cache_dir + os.sep + c
                if not os.path.exists(other_c_dir):
                    os.mkdir(other_c_dir)
                for cfg in os.listdir():
                    if cfg[0] == '.': continue
                    os.chdir(cfg)
                    other_cfg_dir = other_c_dir + os.sep + cfg
                    if not os.path.exists(other_cfg_dir):
                        os.mkdir(other_cfg_dir)
                    for f in os.listdir():
                        if f[0] == '.': continue
                        to = other_cfg_dir + os.sep + f
                        print('save_states copying: %s %s' % (f, to))
                        shutil.copyfile(f, to)
                    os.chdir('..')
                os.chdir('..')
        os.chdir('..')

    def save_states(self, savename):
        self.states = {}
        self._save_state_dir(savename, self.user_cache_dir)
        self._save_state_dir(savename,
                             self.user_cache_dir + os.sep + self.hostdir)

    def _read_state_dir(self):

        # read in state files
        dir1 = self.user_cache_dir
        if not os.path.isdir(dir1):
            return
        os.chdir(dir1)

        for c in self.components:
            if c not in self.configs:
                continue
            for cfg in self.configs[c]:
                    #print( f" {self.configs[c][cfg]['statehost']=} " )
                    if 'options' in self.configs[c][cfg] and self.configs[c][cfg]['options'].statehost:
                        state_dir=self.user_cache_dir + os.sep + self.hostdir + os.sep + c + os.sep + cfg
                    else:
                        state_dir=self.user_cache_dir + os.sep + c + os.sep + cfg

                    if os.path.isdir(state_dir):
                        os.chdir(state_dir)
                        self.states[c][cfg] = {}
                        self.states[c][cfg]['instance_pids'] = {}
                        self.states[c][cfg]['queueName'] = None
                        if c in self.configs:
                            if cfg not in self.configs[c]:
                                self.states[c][cfg]['status'] = 'removed'

                        self.states[c][cfg]['has_state'] = False
                        self.states[c][cfg]['noVip'] = None
                        

                        for pathname in os.listdir():
                            p = pathlib.Path(pathname)
                            if p.suffix in ['.pid', '.qname', '.state', '.noVip']:
                                if sys.version_info[0] > 3 or sys.version_info[
                                        1] > 4:
                                    t = p.read_text().strip()
                                else:
                                    with p.open() as f:
                                        t = f.read().strip()
                                #print( 'read pathname:%s len: %d contents:%s' % ( pathname, len(t), t[0:10] ) )
                                if len(t) == 0:
                                    continue

                                if pathname[-4:] == '.pid':
                                    i = self._instance_num_from_pidfile(pathname, c, cfg)
                                    if i < 0:
                                        continue
                                    if t.isdigit():
                                        #print( "pid assignment: {c}/{cfg} instance: {i}, pid: {t}" )
                                        self.states[c][cfg]['instance_pids'][i] = int(t)
                                elif pathname[-6:] == '.qname':
                                    self.states[c][cfg]['queueName'] = t
                                elif pathname[-6:] == '.noVip':
                                    self.states[c][cfg]['noVip'] = t
                                elif pathname[-8:] == '.metrics':
                                    i = int(pathname[-10:-8])
                                    if not 'instance_metrics' in self.states[c][cfg]:
                                        self.states[c][cfg]['instance_metrics'] = {}
                                    try:
                                        self.states[c][cfg]['instance_metrics'][i] = json.loads(t)
                                        self.states[c][cfg]['instance_metrics'][i]['status'] = { 'mtime':os.stat(p).st_mtime }
                                    except:
                                        logger.error( f"corrupt metrics file {pathname}: {t}" )


    def _read_metrics_dir(self,metrics_parent_dir):
        # read in metrics files

        dir1 = metrics_parent_dir + os.sep + 'metrics'

        if not os.path.isdir(dir1):
            return
        os.chdir(dir1)

        for l in os.listdir(dir1):

            if not l.endswith('.json'):
                continue

            ll = os.path.basename(l.replace('.json','')).split('_')
            if len(ll) < 3:
                continue

            c= ll[0]
            cfg = '_'.join(ll[1:-1])
            i = int(ll[-1].replace('i',''))

            if (not c in self.components) or (not cfg in self.states[c]):
                continue

            if not 'instance_metrics' in self.states[c][cfg]:
                self.states[c][cfg]['instance_metrics'] = {}

            try:
                p = pathlib.Path(l)
                with p.open() as f:
                    t = f.read().strip()

                self.states[c][cfg]['instance_metrics'][i] = json.loads(t)
                self.states[c][cfg]['instance_metrics'][i]['status'] = { 'mtime':os.stat(p).st_mtime }
            except:
                logger.error( f"corrupt metrics file {dir1+os.sep+l}: {t}" )


    def _read_states(self):
        self.states = {}
        for c in self.components:
            self.states[c] = {}

        self._read_state_dir()
        #self._read_state_dir(self.user_cache_dir + os.sep + self.hostdir)
        self._read_metrics_dir(self.user_cache_dir)
        self._read_metrics_dir(self.user_cache_dir + os.sep + self.hostdir)

    def _find_missing_instances_dir(self, dir):
        """ find processes which are no longer running, based on pidfiles in state, and procs.
        """
        missing = []
        if not os.path.isdir(dir):
            return
        os.chdir(dir)
        for c in self.components:
            c_dir = os.path.join(dir, c)
            if os.path.isdir(c_dir):
                if c not in self.configs: continue
                os.chdir(c_dir)
                for cfg in os.listdir():
                    if cfg[0] == '.': continue
                    
                    if cfg not in self.configs[c]: continue
                    
                    cfg_dir = os.path.join(c_dir, cfg)
                    if os.path.isdir(cfg_dir):
                        os.chdir(cfg_dir)

                        if os.path.exists("disabled"): # double check, if disabled should ignore state.
                            continue

                        for filename in os.listdir():
                            # look at pid files, find ones where process is missing.
                            if filename[-4:] == '.pid':
                                i = self._instance_num_from_pidfile(filename, c, cfg)
                                if i < 0:
                                    continue
                                if i != 0:
                                    p = pathlib.Path(filename)
                                    if sys.version_info[0] > 3 or sys.version_info[
                                            1] > 4:
                                        t = p.read_text().strip()
                                    else:
                                        with p.open() as f:
                                            t = f.read().strip()
                                    if t.isdigit():
                                        pid = int(t)
                                        if pid not in self.procs:
                                            missing.append([c, cfg, i])
                                    else:
                                        missing.append([c, cfg, i])
                    os.chdir(c_dir) # back to component dir containing configs
                os.chdir(dir) # back to dir containing components

        self.missing.extend(missing)

    def _find_missing_instances(self):
        self.missing = []
        self._find_missing_instances_dir(self.user_cache_dir)
        self._find_missing_instances_dir(self.user_cache_dir + os.sep +
                                         self.hostdir)

    def _clean_missing_proc_state_dir(self, dir):
        """ remove state pid files for process which are not running
        """

        if self.options.dry_run:
            return

        if not os.path.isdir(dir):
            return
        os.chdir(dir)
        for instance in self.missing:
            (c, cfg, i) = instance
            if os.path.isdir(c):
                os.chdir(c)
                for cfg in os.listdir():
                    if os.path.isdir(cfg):
                        os.chdir(cfg)
                        for filename in os.listdir():
                            if filename[-4:] == '.pid':
                                p = pathlib.Path(filename)
                                if sys.version_info[0] > 3 or sys.version_info[
                                        1] > 4:
                                    t = p.read_text().strip()
                                else:
                                    with p.open() as f:
                                        t = f.read().strip()
                                if t.isdigit():
                                    pid = int(t)
                                    if pid not in self.procs:
                                        os.unlink(filename)
                                else:
                                    os.unlink(filename)

                        os.chdir('..')
                os.chdir('..')

    def _clean_missing_proc_state(self):

        self._clean_missing_proc_state_dir(self.user_cache_dir)
        self._clean_missing_proc_state_dir(self.user_cache_dir + os.sep +
                                           self.hostdir)

    def _read_logs_dir(self, dir):

        if not os.path.isdir(dir):
            return
        os.chdir(dir)
        now = time.time()
        if os.path.isdir('log'):
            os.chdir('log')

            # FIXME: known issue... specify a log rotation interval < 1 d, it puts an _ between date and TIME.
            # ISO says this should be a T, but whatever... sr_shovel_t_dd1_f00_03.log.2019-12-27_12-43-01
            # the additional _ breaks this logic, can't be bothered to fix it yet... to unusual a case to worry about.
            # just patched to not crash for now.
            for lf in os.listdir():
                if lf[0] == '.': continue  # hidden, ignore.
                lff = lf.split('_')
                if len(lff) > 2:
                    c = lff[0]
                    if ( c == 'sr' ) or ( c not in self.components): 
                        continue  # old or inapplicable log, ignore.
                    cfg = '_'.join(lff[1:-1])

                    suffix = lff[-1].split('.')

                    if len(suffix) > 1:
                        if (suffix[1] == 'log') and len(suffix) < 3:
                            try:
                                inum = int(suffix[0])
                            except:
                                inum = 0
                            age = ageOfFile(lf)
                            if cfg not in self.states[c]:
                                self.states[c][cfg] = {}
                            if 'logAge' not in self.states[c][cfg]:
                                self.states[c][cfg]['logAge'] = {}
                            self.states[c][cfg]['logAge'][inum] = now-age

    def _read_logs(self):
        self._read_logs_dir(self.user_cache_dir)
        self._read_logs_dir(self.user_cache_dir + os.sep + self.hostdir)

    def _init_broker_host(self, bhost):
        if '@' in bhost:
            host = bhost.split('@')[1]
        else:
            host = bhost

        if not host in self.brokers:

            self.brokers[host] = {}
            self.brokers[host]['exchanges'] = {}
            self.brokers[host]['queues'] = {}
            if hasattr(self, 'admin') and host in self.admin:
                self.brokers[host]['admin'] = self.admin

        return host

    def __resolved_exchanges(self, c, cfg, o):
        """
          Guess the name of an exchange. looking at either a direct setting,
          or an existing queue state file, or lastly just guess based on conventions.
        """
        exl = []
        #if hasattr(o,'declared_exchanges'):
        #    exl.extend(o.declared_exchanges)

        if hasattr(o, 'exchange'):
            if type(o.exchange) == list:
                exl.extend(o.exchange)
            else:
                exl.append(o.exchange)
            return exl

        x = 'xs_%s' % o.broker.url.username

        if hasattr(o, 'exchangeSuffix'):
            x += '_%s' % o.exchangeSuffix

        if hasattr(o, 'exchangeSplit'):
            l = []
            for i in range(0, o.instances):
                y = x + '%02d' % i
                l.append(y)
            return l
        else:
            exl.append(x)
            return exl

    def __resolved_post_exchanges(self, c, cfg, o):
        """
          Guess the name of an exchange. looking at either a direct setting,
          or an existing queue state file, or lastly just guess based on conventions.
        """
        exl = []
        #if hasattr(o,'declared_exchanges'):
        #    exl.extend(o.declared_exchanges)

        if hasattr(o, 'post_exchange'):
            if type(o.post_exchange) == list:
                exl.extend(o.post_exchange)
            else:
                exl.append(o.post_exchange)
            return exl

        x = 'xs_%s' % o.post_broker.url.username

        if hasattr(o, 'post_exchangeSuffix'):
            x += '_%s' % o.post_exchangeSuffix

        if hasattr(o, 'post_exchangeSplit'):
            l = []
            for i in range(0, o.instances):
                y = x + '%02d' % i
                l.append(y)
            return l
        else:
            exl.append(x)
            return exl

    def __guess_queueName(self, c, cfg, o):
        """
          Guess the name of a queue. looking at either a direct setting,
          or an existing queue state file, or lastly just guess based on conventions.
        """
        if hasattr(o, 'queueName'):
            return o.queueName

        if cfg in self.states[c]:
            if self.states[c][cfg]['queueName']:
                return self.states[c][cfg]['queueName']

        n = 'q_' + o.broker.url.username + '.sr3_' + c + '.' + cfg
        n += '.' + str(random.randint(0, 100000000)).zfill(8)
        n += '.' + str(random.randint(0, 100000000)).zfill(8)

        return n

    def _resolve_brokers(self):
        """ make a map of dependencies

            on a given broker, 
                 exchanges exist, 
                      with publishers: [ 'c/cfg', 'c/cfg' ... ]
                      with queues: [ 'qname', 'qname', ... ]
                      for each queue: [ 'c/cfg', 'c/cfg', ... ]
        """
        self.brokers = {}

        o=self.default_cfg
        if hasattr(o, 'admin') and (o.admin is not None):
            # FIXME: sometimes o.admin is a string... no idea why.. upstream cause should be addressed.
            if o.admin.url is not None and type(o.admin.url) == str:
                o.admin.url = urllib.parse(o.admin.url)
            host = self._init_broker_host(o.admin.url.netloc)
            self.brokers[host]['admin'] = o.admin
            if hasattr(o, 'declared_exchanges'):
                for x in o.declared_exchanges:
                    if not x in self.brokers[host]['exchanges']:
                        self.brokers[host]['exchanges'][x] = [
                            'declared'
                        ]
                    else:
                        if not 'declared' in self.brokers[host][
                                'exchanges'][x]:
                            self.brokers[host]['exchanges'][x].append(
                                'declared')

        # find exchanges and queues
        for c in self.components:
            if (c not in self.states) or (c not in self.configs):
                continue

            for cfg in self.configs[c]:

                if not 'options' in self.configs[c][cfg]:
                    continue

                o = self.configs[c][cfg]['options']
                if not hasattr(o, 'instances'):
                    o.instances = 1
                name = c + os.sep + cfg

                if hasattr(o, 'broker') and o.broker is not None and o.broker.url is not None:
                    host = self._init_broker_host(o.broker.url.netloc)
                    xl = self.__resolved_exchanges(c, cfg, o)
                    q = self.__guess_queueName(c, cfg, o)

                    self.configs[c][cfg]['options'].queueName_resolved = q

                    for exch in xl:
                        if exch in self.brokers[host]['exchanges']:
                            self.brokers[host]['exchanges'][exch].append(q)
                        else:
                            self.brokers[host]['exchanges'][exch] = [q]

                    if q in self.brokers[host]['queues']:
                        self.brokers[host]['queues'][q].append(name)
                    else:
                        self.brokers[host]['queues'][q] = [name]

                if hasattr(o, 'post_broker') and o.post_broker is not None and o.post_broker.url is not None:
                    host = self._init_broker_host(o.post_broker.url.netloc)

                    self.configs[c][cfg]['options'].resolved_exchanges = \
                            self.__resolved_post_exchanges(c, cfg, o)

                    if hasattr(o, 'post_exchange'):
                        self.brokers[host]['exchange'] = o.post_exchange

        self.exchange_summary = {}
        for h in self.brokers:
            self.exchange_summary[h] = {}
            allx = []
            if 'exchanges' in self.brokers[h]:
                allx += self.brokers[h]['exchanges'].keys()

            if 'post_exchanges' in self.brokers[h]:
                allx += self.brokers[h]['post_exchanges'].keys()

            for x in allx:
                a = 0
                if x in self.brokers[h]['exchanges']:
                    a += len(self.brokers[h]['exchanges'][x])
                self.exchange_summary[h][x] = a

    def _resolve(self):
        """
           compare configs, states, & logs and fill things in.

           things that could be identified: differences in state, running & configured instances.
        """

        self._resolve_brokers()
        now = time.time()

        # comparing states and configs to find missing instances, and correct state.
        self.resources={ 'uss': 0, 'rss': 0, 'vms':0, 'user_cpu': 0, 'system_cpu':0 }
        self.cumulative_stats={ 
                'flowNameWidth': 20, 'latestTransferWidth': 4, 
                'rxLagTime':0, 'rxLagCount':0, 
                'rxMessageQueued':0, 'rxMessageRetry':0, 
                'txMessageQueued':0, 'txMessageRetry':0, 
                'rxMessageRate':0, 'rxMessageRateCpu':0, 'rxDataRate':0, 'rxFileRate':0, 'rxMessageByteRate':0, 
                'txMessageRate':0, 'txDataRate':0, 'txFileRate':0, 'txMessageByteRate':0
                }
        for c in self.components:
            if (c not in self.states) or (c not in self.configs):
                continue

            for cfg in self.configs[c]:
                if len( f"{c}/{cfg}" ) > self.cumulative_stats['flowNameWidth']:
                    self.cumulative_stats['flowNameWidth'] = len( f"{c}/{cfg}" ) 

                if cfg not in self.states[c]:
                    logger.debug('no existing state files for %s/%s' % (c,cfg))
                    self.states[c][cfg] = {}
                    self.states[c][cfg]['instance_pids'] = {}
                    self.states[c][cfg]['queueName'] = None
                    self.states[c][cfg]['status'] = 'stopped'
                    self.states[c][cfg]['has_state'] = False
                    continue
                if os.path.exists(self.user_cache_dir + os.sep + c + os.sep + cfg + os.sep + 'disabled'):
                    self.configs[c][cfg]['status'] = 'disabled'
                if 'instance_metrics' in self.states[c][cfg]:
                    if 'housekeeping' in self.configs[c][cfg]:
                        expiry = now - self.configs[c][cfg]['housekeeping']*1.5
                    else:
                        expiry = now - 300

                    # cumulate per instance metrics into overall ones for the configuration.

                    metrics=copy.deepcopy(empty_metrics)
                    for i in self.states[c][cfg]['instance_metrics']:
                        if self.states[c][cfg]['instance_metrics'][i]['status']['mtime'] < expiry:
                            logger.debug( f"metrics for {c}/{cfg}/ instance {i} too old ignoring." )
                            continue

                        #print( f"states of {c}/{cfg}: {self.states[c][cfg]} " )
                        #print( f"instance metrics states of {c}/{cfg}: {self.states[c][cfg]['instance_metrics']} " )
                        for j in self.states[c][cfg]['instance_metrics'][i]:
                            #print( f"i={i}, j={j}, c={c}, cfg={cfg}" )
                            for k in self.states[c][cfg]['instance_metrics'][i][j]:
                                #print( f"k={k}" )
                                if k in metrics:
                                    newval = self.states[c][cfg]['instance_metrics'][i][j][k]
                                    #print( f"k={k}, newval={newval}" )
                                    if k in [ "lagMax" ]:
                                        if newval > metrics[k]:
                                            metrics[k] = newval
                                    elif k in [ "last_housekeeping" ]:
                                        if metrics[k] == 0 or newval < metrics[k] :
                                            metrics[k] = newval
                                    elif k in [ "transferRxLast", "transferTxLast"  ]:
                                        newval = sarracenia.timestr2flt(newval)
                                        if 'transferLast' not in metrics or (newval > metrics['transferLast']):
                                            metrics['transferLast'] = newval
                                    elif k in [ "rxLast", "txLast"  ]:
                                        newval = sarracenia.timestr2flt(newval)
                                        if k == 'rxLast' and 'rxLast' not in metrics or (newval > metrics['rxLast']):
                                            metrics['rxLast'] = newval
                                        if k == 'txLast' and 'txLast' not in metrics or (newval > metrics['txLast']):
                                            metrics['txLast'] = newval
                                        if 'messageLast' not in metrics or (newval > metrics['messageLast']):
                                            metrics['messageLast'] = newval
                                    elif k in [ "cpuTime" ]:
                                        metrics['cpuTime'] += newval
                                    else:
                                        metrics[k] += newval
                                #else:
                                #    print( f'skipping {k}')

                        if 'transferConnectTime' in metrics:
                            metrics['transferConnectTime'] = metrics['transferConnectTime'] / len(self.states[c][cfg]['instance_metrics']) 

                        if 'disconnectTime' in metrics:
                            metrics['disconnectTime'] = metrics['disconnectTime'] / len(self.states[c][cfg]['instance_metrics']) 

                        m = metrics
                        m['messagesQueued'] = -1
                        if m[ "lagMessageCount" ] > 0:
                            m['lagMean'] = m[ "lagTotal" ] / m[ "lagMessageCount" ]
                            self.cumulative_stats['rxLagTime'] += m[ "lagTotal" ]
                            self.cumulative_stats['rxLagCount'] +=  m[ "lagMessageCount" ]
                        else:
                            m['lagMean'] = 0
                    
                        m['retry'] = m[ "msgs_in_download_retry" ] + m["msgs_in_post_retry" ]
                        self.cumulative_stats['rxMessageRetry'] += m['retry']
    
                        if 'brokerQueuedMessageCount' in m:
                            m['messagesQueued'] = m['brokerQueuedMessageCount']
                            self.cumulative_stats['rxMessageQueued'] += m['messagesQueued']
    
                        m['latestTransfer'] = "n/a"
                        if "transferLast" in m and m['transferLast'] > 0:
                            m['latestTransfer'] = durationToString(now - m['transferLast'])
                        elif "messageLast" in m and m['messageLast'] > 0:
                            m['latestTransfer'] = durationToString(now - m['messageLast'])
                        
                        if len(m['latestTransfer']) > self.cumulative_stats['latestTransferWidth']:
                            self.cumulative_stats['latestTransferWidth'] = len(m['latestTransfer'])
    
                        if "last_housekeeping" in m and m["last_housekeeping"] > 0:
                            m['time_base'] = now - m[ "last_housekeeping" ] 
                            time_base = m['time_base']
                            byteTotal = 0
                            if 'rxByteCount' in m:
                                byteTotal += m["rxByteCount"]
            
                            if 'txByteCount' in m:
                                byteTotal += m["txByteCount"]
                                self.cumulative_stats['txMessageByteRate'] +=  m["txByteCount"]/time_base
            
                            m['byteRate'] = byteTotal/time_base
                            m['msgRate']  = (m["rxGoodCount"]+m["rxBadCount"])/time_base
                            if m['cpuTime'] > 0:
                                m['msgRateCpu'] = (m["rxGoodCount"]+m["rxBadCount"])/m['cpuTime']
                            else:
                                m['msgRateCpu'] = 0

                            self.cumulative_stats['rxMessageByteRate'] += m['byteRate']
                            self.cumulative_stats['rxMessageRate'] +=  m['msgRate']
                            self.cumulative_stats['rxMessageRateCpu'] +=  m['msgRateCpu']
    
                            m['transferRxByteRate'] = m['transferRxBytes']/time_base
                            m['transferRxFileRate'] = m['transferRxFiles']/time_base
                            m['transferTxByteRate'] = m['transferTxBytes']/time_base
                            m['transferTxFileRate'] = m['transferTxFiles']/time_base
    
                            self.cumulative_stats['rxFileRate'] += m['transferRxFileRate']
                            self.cumulative_stats['rxDataRate'] += m['transferRxByteRate']
                            self.cumulative_stats['txFileRate'] += m['transferTxFileRate']
                            self.cumulative_stats['txDataRate'] += m['transferTxByteRate']
                            
    
    
                            if 'transferConnectTime' in m:
                                m['byteConnectPercent'] = int(100*(m['transferConnectTime'])/time_base)
                            else:
                                m['byteConnectPercent'] = 0
    
                            if 'disconnectTime' in m:
                                m['connectPercent'] = int(100*(time_base-m['disconnectTime'])/time_base)
                            else:
                                m['connectPercent']= 0
    
                            self.cumulative_stats['txMessageRate'] +=  (m["txGoodCount"]+m["txBadCount"])/time_base
                        if m["rxGoodCount"] > 0:
                            m['rejectPercent'] = ((m['rejectCount']+m['rxBadCount'])/(m['rxGoodCount']+m['rxBadCount']))*100
                            if m['rejectPercent'] > 100:
                                m['rejectPercent']=100
                        else:
                            m['rejectPercent'] = 0

                    self.states[c][cfg]['metrics'] = metrics
                else:
                    self.states[c][cfg]['metrics'] = empty_metrics
                    
                if ('instance_pids' in self.states[c][cfg]) and (len(self.states[c][cfg]['instance_pids']) >= 0):
                    self.states[c][cfg]['missing_instances'] = []
                    self.states[c][cfg]['hung_instances'] = []
                    observed_instances = 0
                    hung_instances=0
                    resource_usage={ 'uss': 0, 'rss': 0, 'vms':0, 'user_cpu': 0.0, 'system_cpu':0.0 }
                    nvip=False
                    for i in self.states[c][cfg]['instance_pids']:
                        if self.states[c][cfg]['instance_pids'][i] not in self.procs:
                            self.states[c][cfg]['missing_instances'].append(i)
                        else:
                            observed_instances += 1
                            pid = self.states[c][cfg]['instance_pids'][i]
                            self.procs[ pid ]['claimed'] = True
                            resource_usage[ 'uss' ] += self.procs[pid]['memory']['uss'] 
                            self.resources[ 'uss' ] += self.procs[pid]['memory']['uss'] 
                            resource_usage[ 'rss' ] += self.procs[pid]['memory']['rss'] 
                            self.resources[ 'rss' ] += self.procs[pid]['memory']['rss'] 
                            resource_usage[ 'vms' ] += self.procs[pid]['memory']['vms'] 
                            self.resources[ 'vms' ] += self.procs[pid]['memory']['vms'] 
                            resource_usage[ 'user_cpu' ] += self.procs[pid]['cpu']['user'] 
                            self.resources[ 'user_cpu' ] += self.procs[pid]['cpu']['user'] 
                            resource_usage[ 'system_cpu' ] += self.procs[pid]['cpu']['system'] 
                            self.resources[ 'system_cpu' ] += self.procs[pid]['cpu']['system'] 

                            if ('logAge' in self.states[c][cfg]) and (i in self.states[c][cfg]['logAge'] ) and \
                                    ( self.states[c][cfg]['logAge'][i] > self.configs[c][cfg]['options'].runStateThreshold_hung ):
                                hung_instances += 1
                                self.states[c][cfg]['hung_instances'].append(i)

                    flow_status = 'unknown' if self.configs[c][cfg]['status'] != 'disabled' else 'disabled'
                    if hung_instances > 0 and (observed_instances > 0):
                         flow_status = 'hung'
                    elif observed_instances < int(self.configs[c][cfg]['instances']):
                        if (c == 'post') and (('sleep' not in self.states[c][cfg]) or self.states[c][cfg]['sleep'] <= 0):
                            if self.configs[c][cfg]['status'] != 'disabled':
                                flow_status = 'stopped'
                        else:
                            if observed_instances > 0:
                                flow_status = 'partial'
                                for i in range(1, int(self.configs[c][cfg]['instances'])+1 ):
                                    if not i in self.states[c][cfg]['instance_pids']:
                                         self.states[c][cfg]['missing_instances'].append(i)
                            else:
                                if self.configs[c][cfg]['status'] != 'disabled':
                                    if len(self.states[c][cfg]['instance_pids']) == 0 :
                                        flow_status = 'stopped' 
                                    else:
                                        flow_status = 'missing' 
                                        if not i in self.states[c][cfg]['instance_pids']:
                                             self.states[c][cfg]['missing_instances'].append(i)
                    elif observed_instances == 0:
                        flow_status = "stopped" if len(self.states[c][cfg]['instance_pids']) == 0 else "missing"
                    elif self.states[c][cfg]['noVip']:
                        flow_status = 'waitVip'
                    elif self.states[c][cfg]['metrics']['byteRate'] < self.configs[c][cfg]['options'].runStateThreshold_slow:
                        flow_status = 'slow'
                    elif self.states[c][cfg]['metrics']['retry'] > self.configs[c][cfg]['options'].runStateThreshold_retry:
                        flow_status = 'retry'
                    elif self.states[c][cfg]['metrics']['lagMean'] > self.configs[c][cfg]['options'].runStateThreshold_lag:
                        flow_status = 'lagging'
                    elif self.states[c][cfg]['metrics']['rejectPercent'] > self.configs[c][cfg]['options'].runStateThreshold_reject:
                        flow_status = 'reject'
                    elif hasattr(self.configs[c][cfg]['options'],'post_broker') and self.configs[c][cfg]['options'].post_broker \
                            and (now-self.states[c][cfg]['metrics']['txLast']) > self.configs[c][cfg]['options'].runStateThreshold_idle:
                        flow_status = 'idle'
                    elif  hasattr(self.configs[c][cfg]['options'],'download') and self.configs[c][cfg]['options'].download \
                            and (now-self.states[c][cfg]['metrics']['transferLast']) > self.configs[c][cfg]['options'].runStateThreshold_idle:
                        flow_status = 'idle'
                    elif (now-self.states[c][cfg]['metrics']['rxLast']) > self.configs[c][cfg]['options'].runStateThreshold_idle:
                        flow_status = 'idle'
                    elif self.states[c][cfg]['metrics']['msgRate'] > 0 and \
                           self.states[c][cfg]['metrics']['msgRateCpu'] < self.configs[c][cfg]['options'].runStateThreshold_cpuSlow:
                        flow_status = 'cpuSlow'
                    else:
                        flow_status = 'running'

                    self.states[c][cfg]['resource_usage'] = copy.deepcopy(resource_usage)
                    self.configs[c][cfg]['status'] = flow_status


        # FIXME: missing check for too many instances.
        if self.cumulative_stats['rxLagCount']  > 0:
            self.cumulative_stats['lagMean'] = self.cumulative_stats['rxLagTime'] / self.cumulative_stats['rxLagCount'] 
        else:
            self.cumulative_stats['lagMean'] = 0

        self.strays = {}
        for pid in self.procs:
            if not self.procs[pid]['claimed']:
                self.strays[pid] = ' '.join(self.procs[pid]['cmdline'])

    def _match_patterns(self, patterns=None):
        """
          identify subset of configurations to operate on.
          fnmatch the patterns from the command line to the list of known configurations.
          put all the ones that do not match in leftovers.
        """

        logging.debug( 'starting match_patterns with: %s' % patterns )
        self.filtered_configurations = []
        self.leftovers = []
        leftover_matches = {}
        if (patterns is None) or (patterns == []):
            patterns = ['*' + os.sep + '*']

        if self.options.action == 'convert':
            self.v2_config = patterns
            return

        candidates=[]
        for c in self.components:
            if (c not in self.configs):
                continue
            for cfg in self.configs[c]:
                fcc = c + os.sep + cfg
                candidates.append(fcc)
    
        self.all_configs = candidates
        logger.debug( f"candidates: {candidates}" )
        new_patterns=[]
        for p in patterns:
            if p in [ 'examples','eg','ie', 'flow_callback','flowcb','fcb','v2plugins','v2p']:
                new_patterns.append(p)         
            elif os.sep not in p:
                p = 'flow/' + p
                new_patterns.append(p)         
            else:
                new_patterns.append(p)         
            leftover_matches[p] = 0
        patterns=new_patterns

        logger.debug( f"patterns: {patterns}" )
        for fcc in candidates:
            if (patterns is None) or (len(patterns) < 1):
                self.filtered_configurations.append(fcc)
            else:
                for p in patterns:
                    if p in [ 'examples','eg','ie','flow_callback','flowcb','fcb','v2plugins','v2p']:
                        continue
                    if fnmatch.fnmatch(fcc, p):
                        self.filtered_configurations.append(fcc)
                        leftover_matches[p] += 1

                    if fcc[-5:] == '.conf' and fcc[0:-5] == p :
                        self.filtered_configurations.append(fcc)
                        leftover_matches[p] += 1
 
                    if fcc[-4:] == '.inc' and fcc[0:-4] == p :
                        self.filtered_configurations.append(fcc)
                        leftover_matches[p] += 1
 
                    # 22/11/01... pas thinks this is wrong and backwards, but not sure..
                    if p[-5:] == '.conf' and fnmatch.fnmatch(fcc, p[0:-5]):
                        self.filtered_configurations.append(fcc)
                        leftover_matches[p] += 1

        for p in patterns:
            if leftover_matches[p] == 0:
                self.leftovers.append(p)

        if len(self.leftovers) > 0:
            if ('examples' == self.leftovers[0]) or (
                    'plugins' == self.leftovers[0]):
                candidates = []
                if len(patterns) == 1:
                    patterns = ['*' + os.sep + '*']
                else:
                    patterns = patterns[1:]
                if self.leftovers[0] == 'examples':
                    for c in self.components:
                        d = self.package_lib_dir + os.sep + 'examples' + os.sep + c
                        if not os.path.exists(d): continue
                        l = os.listdir(d)
                        candidates.extend(
                            list(
                                map(lambda x: c + os.sep + x[0:x.rfind('.')],
                                    l)))
                else:
                    d = self.package_lib_dir + os.sep + 'plugins'
                    if os.path.exists(d):
                        l = os.listdir(d)
                        l.remove('__init__.py')
                        candidates.extend(
                            list(
                                map(
                                    lambda x: 'plugins' + os.sep + x[0:x.rfind(
                                        '.')], l)))

                for fcc in candidates:
                    for p in patterns:
                        if fnmatch.fnmatch(fcc, p):
                            self.filtered_configurations.append(fcc)

        logging.debug( 'match_patterns result filtered_configurations: %s' % self.filtered_configurations )
        logging.debug( 'match_patterns result leftovers: %s' % self.leftovers )

    # FIXME: this should be in config.py
    @property
    def appname(self):
        return self.__appname

    @appname.setter
    def appname(self, n):
        self.__appname = n
        self.user_config_dir = sarracenia.user_config_dir(self.appname,
                                                       self.appauthor)
        self.user_cache_dir = sarracenia.user_cache_dir(self.appname,
                                                     self.appauthor)

    def __init__(self, opt, config_fnmatches=None):
        """
           side effect: changes current working directory FIXME?
        """

        self.invoking_directory = os.getcwd()
        self.bin_dir = os.path.dirname(os.path.realpath(__file__))
        self.package_lib_dir = os.path.dirname(inspect.getfile(sarracenia))
        self.appauthor = 'MetPX'
        self.options = opt
        self.appname = os.getenv('SR_DEV_APPNAME')
        self.hostname = socket.getfqdn()
        self.hostdir = self.hostname.split('.')[0]
        self.please_stop=False
        self.users = opt.users
        self.declared_users = opt.declared_users

        signal.signal(signal.SIGTERM, self._stop_signal)
        signal.signal(signal.SIGINT, self._stop_signal)

        if self.appname is None:
            self.appname = 'sr3'
        #else:
        #    print(
        #        'DEVELOPMENT using alternate application name: %s, bindir=%s' %
        #        (self.appname, self.bin_dir))


        if not os.path.isdir(self.user_config_dir):
            print( f'INFO: No {self.appname} configuration found. creating an empty one {self.user_config_dir}' )
            os.makedirs(self.user_config_dir)
     
        if not os.path.isdir(self.user_cache_dir):
            print( f'INFO: No {self.appname} state or log files found. Creating an empty one {self.user_cache_dir}' )
            os.makedirs(self.user_cache_dir)

        self.components = [
            'cpost', 'cpump', 'flow', 'poll', 'post', 'report', 'sarra',
            'sender', 'shovel', 'subscribe', 'watch', 'winnow'
        ]
        # active means >= 1 process exists on the node.
        self.status_active =  ['cpuSlow', 'hung', 'idle', 'lagging', 'partial', 'reject', 'retry', 'running', 'slow', 'waitVip' ]
        self.status_values = self.status_active + [ 'disabled', 'include', 'missing', 'stopped', 'unknown' ]

        self.bin_dir = os.path.dirname(os.path.realpath(__file__))

        #print('gathering global state: ', flush=True)

        self.log_dir = self.user_cache_dir + os.sep + 'log'
        pf = self.user_cache_dir + os.sep + "procs.json"
        if os.path.exists(pf):
            self.read_proc_file(pf)
        else:
            self._read_procs()

        #print('procs, ', end='', flush=True)
        self._read_configs()
        #print('got configs from %s' % self.user_config_dir, flush=True)
        self._read_states()
        #print('got state files from %s, ' % self.user_cache_dir , flush=True)
        self._read_logs()
        #print('logs, ', end='', flush=True)
        self._resolve()
        self._find_missing_instances()
        #print('analysis - Done. ', flush=True)
        # True if the user did ``sr3 action`` with no configs/components specified
        self._action_all_configs = (config_fnmatches is None or len(config_fnmatches) == 0)
        self._match_patterns(config_fnmatches)
        os.chdir(self.invoking_directory)

    def _start_missing(self):
        for instance in self.missing:
            if self.please_stop:
                break
            (c, cfg, i) = instance
            if not (c + os.sep + cfg in self.filtered_configurations):
                continue
            component_path = self._find_component_path(c)
            if component_path == '':
                continue
            self._launch_instance(component_path, c, cfg, i)

    def _stop_signal(self, signum, stack):
        logging.info('signal %d received' % signum)
        logging.info("Stopping config...")

        # stack trace dump from: https://stackoverflow.com/questions/132058/showing-the-stack-trace-from-a-running-python-application
        if self.options.debug:
            logger.debug("the following stack trace does not mean anything is wrong. When debug is enabled, we print a stack trace to help, even for normal termination")

            id2name = dict([(th.ident, th.name) for th in threading.enumerate()])
            code = []
            for threadId, stack in sys._current_frames().items():
                code.append("\n# Thread: %s(%d)" % (id2name.get(threadId,""), threadId))
                for filename, lineno, name, line in traceback.extract_stack(stack):
                    code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
                    if line:
                        code.append("  %s" % (line.strip()))
            logging.debug('\n'.join(code))
        self.please_stop=True
        # Signal is also sent to subprocesses. Once they exit, subprocess.run returns and sr.py should terminate.

    def _active_stop_signal(self, signum, stack):
        logging.info('signal %d received' % signum)
        logging.info( f"Stopping config... {self.filtered_configurations}")
        # Signal is also sent to subprocesses. Once they exit, subprocess.run returns and sr.py should terminate.
        self._read_procs()
        self._find_missing_instances()
        self._clean_missing_proc_state()
        self._read_states()
        self._resolve()
        self.stop()

    def run_command(self, cmd_list):
        sr_path = os.environ.get('SARRA_LIB')
        sc_path = os.environ.get('SARRAC_LIB')

        try:
            if sc_path and cmd_list[0].startswith("sr3_cp"):
                subprocess.run([sc_path + os.sep + cmd_list[0]] + cmd_list[1:],
                               check=True)
            elif sr_path and cmd_list[0].startswith("sr3"):
                subprocess.run([sr_path + os.sep + cmd_list[0] + '.py'] +
                               cmd_list[1:],
                               check=True)
            else:
                subprocess.run(cmd_list, check=True)
        except subprocess.CalledProcessError as err:
            logging.critical("subprocess.run failed err={}".format(err))
            logging.debug("Exception details:", exc_info=True)
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt...")
            logging.info("Stopping config...")

    def add(self):

        if not hasattr(self, 'leftovers') or (len(self.leftovers) == 0):
            if len(self.filtered_configurations) > 0:
               logging.info( f"matched existing {self.filtered_configurations}" )
            logging.error("nothing specified to add")

        for l in self.leftovers:
            if self.please_stop:
                break
            sp = l.split(os.sep)
            if (len(sp) == 1) or (
                (len(sp) > 1) and
                (sp[-2] not in sarracenia.config.Config.components +
                 ['plugins'])):
                component = 'flow'
                cfg = sp[-1]
            else:
                component = sp[-2]
                cfg = sp[-1]

            iedir = os.path.dirname(inspect.getfile(sarracenia)) + os.sep + 'examples'

            destdir = self.user_config_dir + os.sep + component

            suggestions = [l, os.path.join(iedir, component, cfg)]
            found = False
            for candidate in suggestions:
                if os.path.exists(candidate):
                    pathlib.Path(destdir).mkdir(parents=True, exist_ok=True)
                    logger.info("copying: %s to %s " %
                                (candidate, destdir + os.sep + cfg))
                    shutil.copyfile(candidate, destdir + os.sep + cfg)
                    found = True
                    break
            if not found:
                logger.info("did not find anything to copy for: %s. creating an empty one." % l)
                if cfg[-5:] not in [ '.inc', '.conf' ]:
                    cfg = cfg + '.conf'
                with open( destdir + os.sep + cfg, 'w' ) as f:
                    f.write('')

    def declare(self):
        '''
        creates users, exchanges, and queues in that order - each one is needed to create
        the subsequent one

        '''

        filtered_users = []

        if len(self.filtered_configurations) < len(self.all_configs):

            for config in self.filtered_configurations:

                (c, cfg) = config.split(os.sep)

                if not 'options' in self.configs[c][cfg]:
                    continue

                o = self.configs[c][cfg]['options']

                if hasattr(o, "broker") and o.broker:
                    filtered_users.append(f"{o.broker.url.username}@{o.broker.url.hostname}")
                if hasattr(o, "post_broker") and o.post_broker:
                    filtered_users.append(f"{o.post_broker.url.username}@{o.post_broker.url.hostname}")
                if hasattr(o, "report_broker") and o.report_broker:
                    filtered_users.append(f"{o.report_broker.url.username}@{o.report_broker.url.hostname}")

        # add users (?)
        if self.users: # check if users exist in the configuration (?)
            for h in self.brokers:
                if self.please_stop:
                    break
                if 'admin' in self.brokers[h]:
                    admin_url = self.brokers[h]['admin'].url
                    with open(
                            self.user_config_dir + os.sep + 'credentials.conf',
                            'r') as config_file:
                        for cfl in config_file.readlines():
                            if not cfl.strip(): continue
                            if cfl.lstrip()[0] == '#': continue
                            u_urlstr = cfl.split()[0]
                            try:
                                u_url = urllib.parse.urlparse(u_urlstr)
                            except:
                                continue
                            if not u_url.username:
                                continue
                            if u_url.scheme != admin_url.scheme:
                                continue
                            if u_url.hostname != h:
                                continue
                            if u_url.username in self.default_cfg.declared_users:
                                #print( 'u_url : user:%s, pw:%s, role: %s netloc: %s, host:%s' % \
                                #    (u_url.username, u_url.password, self.default_cfg.declared_users[u_url.username],
                                #     u_url.netloc, u_url.hostname ))
                                
                                user = f"{u_url.username}@{h}"

                                if filtered_users and user not in filtered_users:
                                    logger.debug(f"not adding {user}")
                                    continue

                                sarracenia.rabbitmq_admin.add_user( \
                                    self.brokers[h]['admin'].url, \
                                    self.default_cfg.declared_users[u_url.username],
                                    u_url.username, u_url.password, self.options.dry_run )

        # declare admin exchanges.
        if hasattr(self,'default_cfg') and self.default_cfg.admin:
            logger.info( f"Declaring exchanges for admin.conf using {self.default_cfg.admin} ")
            if hasattr(self.default_cfg, 'declared_exchanges'):
                xdc = sarracenia.moth.Moth.pubFactory(
                    {
                        'broker': self.default_cfg.admin,
                        'dry_run': self.options.dry_run,
                        'exchange': self.default_cfg.declared_exchanges,
                        'message_strategy': { 'stubborn':True }
                    })
                xdc.putSetup()
                xdc.close()
                
        # declare exchanges first.
        for f in self.filtered_configurations:
            if self.please_stop:
                break
            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue
            logging.info('looking at %s/%s ' % (c, cfg))
            o = self.configs[c][cfg]['options']
            if hasattr(
                    o,
                    'resolved_exchanges') and o.resolved_exchanges is not None:
                xdc = sarracenia.moth.Moth.pubFactory(
                    {
                        'broker': o.post_broker,
                        'dry_run': self.options.dry_run,
                        'exchange': o.resolved_exchanges,
                        'message_strategy': { 'stubborn':True }
                    })
                xdc.putSetup()
                xdc.close()

        # then declare and bind queues....
        for f in self.filtered_configurations:
            if self.please_stop:
                break

            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue
            logging.info('looking at %s/%s ' % (c, cfg))
            o = self.configs[c][cfg]['options']
            od = o.dictify()
            if hasattr(o, 'queueName_resolved'):
                od['broker'] = o.broker
                od['queueName'] = o.queueName_resolved
                od['dry_run'] = self.options.dry_run
                qdc = sarracenia.moth.Moth.subFactory(od)
                qdc.getSetup()
                qdc.close()

        # run on_declare plugins.
        for f in self.filtered_configurations:
            if self.please_stop:
                break

            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue

            o = self.configs[c][cfg]['options']
            o.no=0
            o.finalize()
            if c not in [ 'cpost', 'cpump' ]:
                flow = sarracenia.flow.Flow.factory(o)
                flow.loadCallbacks()
                flow.runCallbacksTime('on_declare')
                del flow
                flow=None

    def disable(self):
        if len(self.leftovers) > 0 and not self._action_all_configs:
            logging.error( f"{self.leftovers} configuration not found" )
            return

        for f in self.filtered_configurations:
            if self.please_stop:
                break
            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue

            if 'instance_pids' in self.states[c][cfg] and len(self.states[c][cfg]['instance_pids']) > 0:
                logging.error("cannot disable %s while it is running! " % f)
                continue

            state_file_cfg = self.user_cache_dir + os.sep + c + os.sep + cfg
            state_file_cfg_disabled = state_file_cfg + os.sep + 'disabled'
            if os.path.exists(state_file_cfg_disabled):
                logging.error("%s is already disabled! " % f)
                continue
            if os.path.exists(state_file_cfg):
                with open(state_file_cfg_disabled, 'w') as f:
                    f.write('')
                logging.info(c + '/' + cfg)


    def edit(self):

        for f in self.filtered_configurations:
            if self.please_stop:
                break
            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue

            cfgfile = self.user_config_dir + os.sep + c + os.sep + cfg + '.conf'
            editor = os.environ.get('EDITOR')

            if not editor:
                if sys.platform == 'win32':
                    editor = 'notepad'
                else:
                    editor = 'vi'
                logger.info(
                    'using %s. Set EDITOR variable pick another one.' % editor)

            self.run_command([editor, cfgfile])

    def log(self):

        for f in self.filtered_configurations:
            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue

            lfn = self.log_dir + os.sep + c + "_" + cfg + "_01" + '.log'

            if sys.platform == 'win32':
                self.run_command(['sr_tailf', lfn])
            else:
                self.run_command(['tail', '-f', lfn])

    def enable(self):
        if len(self.leftovers) > 0 and not self._action_all_configs:
            logging.error( f'{self.leftovers} configuration not found' )
            return
        # declare exchanges first.
        for f in self.filtered_configurations:
            if self.please_stop:
                break
            (c, cfg) = f.split(os.sep)

            state_file_cfg = self.user_cache_dir + os.sep + c + os.sep + cfg
            state_file_cfg_disabled = state_file_cfg + os.sep + 'disabled'
            if os.path.exists(state_file_cfg):
                if not os.path.exists(state_file_cfg_disabled):
                    logging.error('%s already enabled' % f)
                    continue
                else:
                    os.remove(state_file_cfg_disabled)
                    logging.info(c + '/' + cfg)

    def features(self):

        # run on_declare plugins.
        for f in self.filtered_configurations:
            if self.please_stop:
                break

            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue

            o = self.configs[c][cfg]['options']
            o.no=0
            o.finalize()
            if c not in [ 'cpost', 'cpump' ]:
                flow = sarracenia.flow.Flow.factory(o)
                flow.loadCallbacks()
                flow.runCallbacksTime('on_features')
                del flow
                flow=None

        features_present=[]
        print( f"\n{'Status:':10} {'feature:':10} {'python imports:':20} {'Description:'} ")
        features_absent=[]
        for x in sarracenia.features.keys():
            if x == 'all':
                continue
            if sarracenia.features[x]['present']:
                word1="Installed"
                desc=sarracenia.features[x]['rejoice']
            else:
                if 'Needed' in sarracenia.features[x]:
                     word1="MISSING"
                else:
                     word1="Absent"
                desc=sarracenia.features[x]['lament']

            print( f"{word1:10} {x:10} {','.join(sarracenia.features[x]['modules_needed']):20} {desc}" )

        if not (sarracenia.features['amqp']['present'] or sarracenia.features['mqtt']['present'] ):
            print( "ERROR: need at least one of: amqp or mqtt" )

        print( f"\n state dir: {self.user_cache_dir} " )
        print( f" config dir: {self.user_config_dir} " )


    def foreground(self):

        for f in self.filtered_configurations:
            if self.please_stop:
                break
            (c, cfg) = f.split(os.sep)

            component_path = self._find_component_path(c)
            pcount = 0

            if component_path == '':
                continue

            if self.configs[c][cfg]['status'] in ['stopped','missing']:
                numi = self.configs[c][cfg]['instances']
                for i in range(1, numi + 1):
                    if pcount % 10 == 0: print('.', end='', flush=True)
                    pcount += 1

            if pcount != 0:
                if not 'options' in self.configs[c][cfg]:
                    continue

                cfgfile = self.user_config_dir + os.sep + c + os.sep + cfg + '.conf'

                if c in [ 'flow',
                        'poll', 'post', 'report', 'sarra', 'sender', 'shovel', 
                        'subscribe', 'watch', 'winnow'
                ]:
                    component_path = os.path.dirname(
                        component_path) + os.sep + 'instance.py'
                    cmd = [sys.executable, component_path, '--no', "0"]
                    cmd.extend(sys.argv[1:])
                    """
                    FIXME... replace 'sub*/*amis*' on invocation with the resolved thing.
                         this feels hacky... but I can't think of a case that won't work.
                    """
                    if '--config' in cmd:
                        cmd[ cmd.index( '--config' )+1 ] = f
                    elif '-c' in cmd:
                        cmd[ cmd.index( '-c' )+1 ] = f
                    elif c not in [ 'post', 'watch' ]:
                        cmd[-1] = f

                elif c[0] != 'c':  # python components
                    if cfg is None:
                        cmd = [sys.executable, component_path, 'foreground']
                    else:
                        cmd = [sys.executable, component_path, 'foreground', cfg]
                else:  # C components
                    cmd = [component_path, '-a', 'foreground', '-c', cfg]

                self.run_command(cmd)
            else:
                print('foreground: stop other instances of this process first')

    def cleanup(self) -> bool:

        if len(self.leftovers) > 0 and not self._action_all_configs:
            logging.error( f'{self.leftovers} configuration not found' )
            return

        if len(self.filtered_configurations) > 1 :
            if len(self.filtered_configurations) != self.options.dangerWillRobinson:
                logging.error(
                        f"specify --dangerWillRobinson=<number> of configs to cleanup (actual: {len(self.filtered_configurations)}, given: {self.options.dangerWillRobinson} ) when cleaning more than one")
                return False

        all_stopped=True
        for f in self.filtered_configurations:
            (c, cfg) = f.split(os.sep)
            if self.configs[c][cfg]['status'] in self.status_active:
                logger.error( f"{c}/{cfg} is in {self.configs[c][cfg]['status']} state. Stop it first.")
                all_stopped=False
 
        if not all_stopped:
            return False

        queues_to_delete = []
        for f in self.filtered_configurations:
            if self.please_stop:
                break
            (c, cfg) = f.split(os.sep)

            o = self.configs[c][cfg]['options']

            if hasattr(o, 'queueName_resolved'):
                #print('deleting: %s is: %s @ %s' % (f, o.queueName_resolved, o.broker.url.hostname ))
                qdc = sarracenia.moth.Moth.subFactory(
                    {
                        'broker': o.broker,
                        'dry_run': self.options.dry_run,
                        'echangeDeclare': False,
                        'queueDeclare': False,
                        'queueBind': False,
                        'broker': o.broker,
                        'queueName': o.queueName_resolved,
                        'message_strategy': { 'stubborn':True }
                    })
                qdc.getSetup()
                qdc.getCleanUp()
                qdc.close()
                queues_to_delete.append((o.broker, o.queueName_resolved))

        for h in self.brokers:
            if self.please_stop:
                break
            for qd in queues_to_delete:
                if self.please_stop:
                    break
                if qd[0].url.hostname != h: continue
                for x in self.brokers[h]['exchanges']:
                    xx = self.brokers[h]['exchanges'][x]
                    if qd[1] in xx:
                        if 'admin' not in self.brokers[h]:
                            continue
                        print(' remove %s from %s subscribers: %s ' %
                              (qd[1], x, xx))
                        xx.remove(qd[1])
                        if o.post_broker and len(xx) < 1:
                            print("No local queues found for exchange %s, attemping to remove it..." % x)
                            qdc = sarracenia.moth.Moth.pubFactory(
                                {
                                    'broker': o.post_broker,
                                    'declare': False,
                                    'exchange': x,
                                    'dry_run': self.options.dry_run,
                                    'broker': self.brokers[h]['admin'],
                                    'message_strategy': { 'stubborn':True }
                                })
                            if qdc:
                                qdc.putSetup()
                                qdc.putCleanUp()
                                qdc.close()

        # run on_cleanup plugins.
        for f in self.filtered_configurations:
            if self.please_stop:
                break

            (c, cfg) = f.split(os.sep)

            if self.configs[c][cfg]['status'] in self.status_active:
                #logger.warning( f"cannot clean running configuration, skipping {c}/{cfg}")
                continue

            if not 'options' in self.configs[c][cfg]:
                continue

            o = self.configs[c][cfg]['options']
            o.no=0
            o.finalize()
            if c not in [ 'cpost', 'cpump' ]:
                flow = sarracenia.flow.Flow.factory(o)
                flow.loadCallbacks()
                flow.runCallbacksTime('on_cleanup')
                del flow
                flow=None
        
        # cleanup statefiles
        for f in self.filtered_configurations:
            if self.please_stop:
                break

            (c, cfg) = f.split(os.sep)

            if self.configs[c][cfg]['status'] in self.status_active:
                #logger.warning( f"cannot clean running configuration, skipping {c}/{cfg}")
                continue

            if self.configs[c][cfg]['options'].statehost:
                cache_dir = self.user_cache_dir + os.sep + self.hostdir + os.sep + f.replace('/', os.sep)
            else:
                cache_dir = self.user_cache_dir + os.sep + f.replace('/', os.sep)

            if os.path.isdir(cache_dir):
                for state_file in os.listdir(cache_dir):
                    if self.please_stop:
                        break
                    if state_file[0] == '.':
                        continue

                    if state_file in [ 'disabled' ]:
                        continue

                    asf = cache_dir + os.sep + state_file
                    if self.options.dry_run:
                        print('removing state file (dry run): %s' % asf)
                    else:
                        print('removing state file: %s' % asf)
                        if os.path.exists(asf):
                            os.unlink(asf)

        return True

    print_column = 0

    def walk_dir(f):
        l = []
        for root, dirs, filenames in os.walk(f):
            if os.path.basename(root) == '__pycache__':
                continue
            for f in filenames:
                if f in ['__init__.py']: continue
                l.append(os.path.join(root, f))

        return l

    def print_configdir2(self, prefix, configdir, component):
        """
           pretty print for v3 plugins.
        """
        if not os.path.isdir(configdir) or (len(os.listdir(configdir)) == 0):
            return

        #print("%s: ( %s )" % (prefix,configdir))
        term = shutil.get_terminal_size((80, 20))
        columns = term.columns
        count = 0
        for confname in sorted(sr_GlobalState.walk_dir(configdir)):
            confname = confname.replace(configdir + os.sep, '')
            if confname[0] == '.' or confname[
                    -1] == '~' or confname == '__init__.py':
                continue
            #if os.path.isdir(configdir + os.sep + confname): continue
            if (((sr_GlobalState.print_column + 1) * 33) >= columns):
                print('')
                sr_GlobalState.print_column = 0
            if (component != ''):
                f = component + os.sep + confname
            else:
                f = confname

            sr_GlobalState.print_column += 1
            count += 1
            print("%-32s " % f, end='')

    def print_configdir(self, prefix, configdir, component):
        """
          pretty print in columns a subdirectory of a configuration directory, respecting selections,
          except for the default ones to always include (admin, default, credentials)
        """

        if not os.path.isdir(configdir) or (len(os.listdir(configdir)) == 0):
            return

        #print("%s: ( %s )" % (prefix,configdir))
        term = shutil.get_terminal_size((80, 20))
        columns = term.columns
        count = 0

        for confname in sorted(os.listdir(configdir)):
            if confname[0] == '.' or confname[-1] == '~': continue
            if os.path.isdir(configdir + os.sep + confname): continue
            if (((sr_GlobalState.print_column + 1) * 33) >= columns):
                print('')
                sr_GlobalState.print_column = 0
            if (component != ''):
                f = component + os.sep + confname[0:confname.rfind('.')]
                if (f not in self.filtered_configurations):
                    continue
                f = component + os.sep + confname
            else:
                f = confname

            sr_GlobalState.print_column += 1
            count += 1
            print("%-32s " % f, end='')

    def config_list(self):
        """
        display all configurations possible for each component
        """

        if hasattr(self, 'leftovers') and (len(self.leftovers) > 0):
            if self.leftovers[0] in ['examples', 'eg', 'ie']:
                print('Sample Configurations: (from: %s )' %
                      (self.package_lib_dir + os.sep + 'examples'))
                for c in sarracenia.config.Config.components:
                    self.print_configdir2(
                        " of %s " % c,
                        os.path.normpath(self.package_lib_dir + os.sep +
                                         'examples' + os.sep + c), c)
            elif self.leftovers[0] in ['flow_callback', 'flowcb', 'fcb']:
                print('Provided callback classes: ( %s ) ' % self.package_lib_dir)
                self.print_configdir2(
                    " of callback classes: ",
                    os.path.normpath(self.package_lib_dir + os.sep + 'flowcb'),
                    'flowcb')
            elif self.leftovers[0] in ['v2plugins', 'v2p']:
                print('Provided v2 plugins: ( %s ) ' % self.package_lib_dir)
                self.print_configdir2(
                    " of plugins: ",
                    os.path.normpath(self.package_lib_dir + os.sep +
                                     'plugins'), 'plugins')
            else:
                print(
                    'Valid things to list: examples,eg,ie flow_callback,flowcb,fcb v2plugins,v2p'
                )
        else:
            print('User Configurations: (from: %s )' % self.user_config_dir)
            for c in sarracenia.config.Config.components:
                self.print_configdir(
                    "for %s" % c,
                    os.path.normpath(self.user_config_dir + os.sep + c), c)

            self.print_configdir("general",
                                 os.path.normpath(self.user_config_dir), '')
            print("\nlogs are in: %s\n" % os.path.normpath(self.log_dir))

    def config_show(self):
        """
        display the resulting settings for selected configurations.
        """
        for f in self.filtered_configurations:
            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue

            o = self.configs[c][cfg]['options']
            o.no=0
            o.finalize()
            if c not in [ 'cpost', 'cpump' ]:
                flow = sarracenia.flow.Flow.factory(o)
                flow.loadCallbacks()
                print('\nConfig of %s/%s: (with callbacks)' % (c, cfg))
                flow.o.dump()
                del flow
                flow=None
            else:
                print('\nConfig of %s/%s: ' % (c, cfg))
                o.dump()

    def remove(self):

        if len(self.leftovers) > 0 and not self._action_all_configs:
            logging.error( f"{self.leftovers} configuration not found" )
            return

        if len(self.filtered_configurations) > 1 :
            if len(self.filtered_configurations) != self.options.dangerWillRobinson:
                logging.error( f"specify --dangerWillRobinson=<n> of configs to remove "
                   f"when > 1 involved. (actual: {len(self.filtered_configurations)}, "
                   f"given: {self.options.dangerWillRobinson}")
                return

        for f in self.filtered_configurations:
            if self.please_stop:
                break

            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue

            if not cfg in self.states[c]:
                continue

            if ('instance_pids' in self.states[c][cfg]) and len(
                    self.states[c][cfg]['instance_pids']) > 0:
                running=0
                for p in self.states[c][cfg]['instance_pids'] :
                    if p in self.procs:
                        running +=1
                if running > 0:
                    logging.error("cannot remove %s/%s while it is running! " % ( c, cfg ) )
                    continue

            cfgfile = self.user_config_dir + os.sep + c + os.sep + cfg + '.conf'
            statefile = self.user_cache_dir + os.sep + c + os.sep + cfg

            if self.options.dry_run:
                logging.info('removing (dry run) %s/%s ' % ( c, cfg ))
            else:
                logging.info('removing %s/%s' % ( c, cfg ))
                os.unlink(cfgfile)
                try:
                    shutil.rmtree(statefile)
                except Exception as ex:
                    print( f" rmtree failed: {ex} " )


    def maint(self, action):
        """
           launch maintenance activity in parallel for all components.
           append outputs separately to stdout as they complete.
        """

        plist = []
        for c in self.components:
            if c not in self.configs:
                continue
            component_path = self._find_component_path(c)
            if component_path == '':
                continue
            for cfg in self.configs[c]:

                f = c + os.sep + cfg
                if f not in self.filtered_configurations:
                    continue

                if c[0] != 'c':  # python components
                    cmd = [sys.executable, component_path, action, cfg]
                else:
                    cmd = [component_path, action, cfg]

                plist.append(
                    subprocess.Popen(cmd,
                                     stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT))
        print('Done')
        for p in plist:
            (outs, errs) = p.communicate()
            print(outs.decode('utf8'))

 

    def sanity(self):
        """ Run sanity by finding and starting missing instances

        :return:
        """
        if len(self.leftovers) > 0 and not self._action_all_configs:
            logging.error( f"{self.leftovers} configuration not found" )
            return

        pcount = 0
        kill_hung=[]
        for f in self.filtered_configurations:
            (c, cfg) = f.split(os.sep)
            component_path = self._find_component_path(c)
            if component_path == '':
                continue
            if self.configs[c][cfg]['status'] in ['missing', 'partial']:
                numi = self.configs[c][cfg]['instances']
                for i in range(1, numi + 1):
                    if pcount % 10 == 0: print('.', end='', flush=True)
                    pcount += 1
            if 'hung_instances' in self.states[c][cfg] and len(self.states[c][cfg]['hung_instances']) > 0:
                for i in self.states[c][cfg]['hung_instances']:
                    kill_pid=self.states[c][cfg]['instance_pids'][i]
                    print( f'\nfound hung {c}/{cfg}/{i} pid: {kill_pid}' )
                    kill_hung.append(  kill_pid )
                    pcount += 1
        
        if (len(kill_hung) > 0) and not self.options.dry_run :
            print('killing hung processes... (no point in SIGTERM if it is hung)')
            for pid in kill_hung:
                signal_pid(pid, signal.SIGKILL)
            time.sleep(5)
            self._read_procs()
            # next step should identify the missing instances and start them up.

        if pcount != 0:
            self._find_missing_instances()
            self._clean_missing_proc_state()
            self._read_states()
            self._resolve()
            filtered_missing = []
            for m in self.missing:
                if m[0] + os.sep + m[1] in self.filtered_configurations:
                    filtered_missing.append(m)

            print('missing: %s' % filtered_missing)
            print('starting them up...')
            if not self.options.dry_run:
                self._start_missing()
        else:
            print('no missing processes found')

        if len(self.strays) > 0:
            print('killing strays...')
            for pid in self.strays:
                print( f"pid: {pid} \"{self.strays[pid]}\"  does not match any configured instance, sending it TERM" )
                if not self.options.dry_run:
                    signal_pid(pid, signal.SIGTERM)
        else:
            print('no stray processes found')

        #It is enough to have it *features* not needed in sanity.
        #for l in sarracenia.features.keys():
        #    if not sarracenia.features[l]['present']:
        #        print( f"notice: python module {l} is missing: {sarracenia.features[l]['lament']}" )

        # run on_sanity plugins.
        for f in self.filtered_configurations:
            if self.please_stop:
                break

            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue

            o = self.configs[c][cfg]['options']
            o.no=0
            o.finalize()
            if c not in [ 'cpost', 'cpump' ]:
                flow = sarracenia.flow.Flow.factory(o)
                flow.loadCallbacks()
                flow.runCallbacksTime('on_sanity')
                del flow
                flow=None
        
    def start(self):
        """ Starting all components

        :return:
        """

        if len(self.leftovers) > 0 and not self._action_all_configs:
            logging.error( f"{self.leftovers} configuration not found" )
            return

        pcount = 0
        for f in self.filtered_configurations:

            (c, cfg) = f.split(os.sep)

            # skip posts that cannot run as daemons
            if c in ['post', 'cpost'] and not self._post_can_be_daemon(c, cfg): continue

            component_path = self._find_component_path(c)
            if component_path == '':
                continue

            if self.configs[c][cfg]['status'] in [ 'missing', 'stopped']:
                numi = self.configs[c][cfg]['instances']
                for i in range(1, numi + 1):
                    if pcount % 10 == 0: print('.', end='', flush=True)
                    pcount += 1
                    self._launch_instance(component_path, c, cfg, i)

        print('( %d ) Done' % pcount)

    def run(self):
        """
            docker compatible run in foreground.
            works best with LogStdout on.
            after doing a start, wait in foreground for children to exit.
        """
        self.start()
        signal.signal(signal.SIGTERM, self._active_stop_signal)
        try:
            waitret = os.wait()
            while waitret is not None:
                print( f'pid {waitret[0]} just exited, waiting for others.')
                time.sleep(2)
                waitret = os.wait()
        except ChildProcessError:
            print( f'All done!')
        except Exception as ex:
            print( f" wait failed: {ex} " )
        
    def stop(self):
        """
           stop all of this users sr_ processes. 
           return 0 on success, non-zero on failure.
        """

        if len(self.leftovers) > 0 and not self._action_all_configs:
            logging.error( f"{self.leftovers} configuration not found" )
            return

        self._clean_missing_proc_state()

        if len(self.procs) == 0:
            print('no procs running...already stopped')
            return

        print('sending SIGTERM ', end='', flush=True)
        pcount = 0
        fg_instances = set()
        pids_signalled=set([])

        for pid in self.strays:
            print( f"pid: {pid} \"{self.strays[pid]}\" does not match any configured instance, killing" )
            signal_pid(pid, signal.SIGTERM)
            pids_signalled |= set([pid])

        for f in self.filtered_configurations:
            (c, cfg) = f.split(os.sep)

            # exclude foreground instances unless --dangerWillRobinson specified
            if (not self.options.dangerWillRobinson) and self._cfg_running_foreground(c, cfg):
                fg_instances.add(f"{c}/{cfg}")
                logger.warning( f"skipping foreground flow: {c}/{cfg}")
                continue

            if self.configs[c][cfg]['status'] in self.status_active:
                for i in self.states[c][cfg]['instance_pids']:
                    #print( "for %s/%s - %s signal_pid( %s, SIGTERM )" % \
                    #    ( c, cfg, i, self.states[c][cfg]['instance_pids'][i] ) )
                    p=self.states[c][cfg]['instance_pids'][i]
                    if p in self.procs:
                        if self.options.dry_run:
                            print( f"kill -TERM {p} # {c}/{cfg}[{i}] " )
                        else:
                            signal_pid( p, signal.SIGTERM )
                            pids_signalled |= set([p])
                            print('.', end='', flush=True)
                        pcount += 1

        print(' ( %d ) Done' % pcount, flush=True)
        if self.options.dry_run:
            print('dry_run assumes everything works the first time')
            return 0

        attempts = 0
        attempts_max = 5
        now = time.time()

        running_pids = len(pids_signalled)
        while attempts < attempts_max:
            for pid in self.procs:
                if (not self.procs[pid]['claimed']) and (
                    (now - self.procs[pid]['create_time']) > 50 and pid not in pids_signalled):
                    print( f"pid: {pid} \"{' '.join(self.procs[pid]['cmdline'])}\" does not match any configured instance, sending it TERM" )
                    signal_pid(pid, signal.SIGTERM)
                    pids_signalled |= set([pid])

            ttw = 1 << attempts
            print( f"Waiting {ttw} sec. to check if {running_pids} processes stopped (try: {attempts})" )
            time.sleep(ttw)
            # update to reflect killed processes.
            self._read_procs()
            self._find_missing_instances()
            self._clean_missing_proc_state()
            self._read_states()
            self._resolve()

            running_pids = 0
            for f in self.filtered_configurations:
                (c, cfg) = f.split(os.sep)
                # exclude foreground instances unless --dangerWillRobinson specified
                if (not self.options.dangerWillRobinson) and self._cfg_running_foreground(c, cfg):
                    fg_instances.add(f"{c}/{cfg}")
                    continue
                running_pids += len(self.states[c][cfg]['instance_pids'])

            if (running_pids == 0) and len(self.strays)==0:
                print('All stopped after try %d' % attempts)
                if len(fg_instances) > 0:
                    print(f"Foreground instances {fg_instances} are running and were not stopped.")
                    print("Use --dangerWillRobinson=1 to force stop foreground instances with sr3 stop.")
                return 0
            attempts += 1

        print('doing SIGKILL this time')
        
        for f in self.filtered_configurations:
            (c, cfg) = f.split(os.sep)
            # exclude foreground instances unless --dangerWillRobinson specified
            if (not self.options.dangerWillRobinson) and self._cfg_running_foreground(c, cfg):
                fg_instances.add(f"{c}/{cfg}")
                continue
            if self.configs[c][cfg]['status'] in self.status_active:
                for i in self.states[c][cfg]['instance_pids']:
                    if self.states[c][cfg]['instance_pids'][i] in self.procs:
                        p=self.states[c][cfg]['instance_pids'][i]
                        print( f"signal_pid( {p} \"{' '.join(self.procs[p]['cmdline'])}\", SIGKILL )")
                        signal_pid(p, signal.SIGKILL)
                        pids_signalled |= set([p])
                        print('.', end='')

        for pid in self.strays:
            print( f"pid: {pid} \"{self.strays[pid]}\" does not match any configured instance, killing" )
            signal_pid(pid, signal.SIGKILL)
            pids_signalled |= set([pid])

        print('Done')
        print('Waiting again...')
        time.sleep(10)
        self._read_procs()
        self._find_missing_instances()
        self._clean_missing_proc_state()
        self._read_states()
        self._resolve()

        for f in self.filtered_configurations:
            (c, cfg) = f.split(os.sep)
            # exclude foreground instances unless --dangerWillRobinson specified
            if (not self.options.dangerWillRobinson) and self._cfg_running_foreground(c, cfg):
                fg_instances.add(f"{c}/{cfg}")
                continue
            if self.configs[c][cfg]['status'] in self.status_active:
                for i in self.states[c][cfg]['instance_pids']:
                    print("failed to kill: %s/%s instance: %s, pid: %s )" %
                          (c, cfg, i, self.states[c][cfg]['instance_pids'][i]))

        if len(self.procs) == 0:
            print('All stopped after KILL')
            if len(fg_instances) > 0:
                print(f"Foreground instances {fg_instances} are running and were not stopped.")
                print("Use --dangerWillRobinson=1 to force stop foreground instances with sr3 stop.")
            return 0
        else:
            print('not responding to SIGKILL:')
            for p in self.procs:
                # exclude foreground instances from printing unless --dangerWillRobinson specified
                if p in pids_signalled:
                    if not self._pid_running_foreground(p): 
                         print( f"\t{p}: \"{' '.join(self.procs[p]['cmdline'])}\"" )
                    elif self.options.dangerWillRobinson: 
                         print( f"\tforeground {p}: \"{' '.join(self.procs[p]['cmdline'])}\"" )
                else:
                    logger.debug( f"\tdid not even try to kill: {p}: \"{' '.join(self.procs[p]['cmdline'])}\"" )
            return 1

    def dump(self): 
        """ Printing all running processes, configs, states
        :return:
        """
        print('{\n')
        print('\n\n"Processes" : { \n\n')

        #procs_length = len(self.procs)
        #for index,pid in enumerate(self.procs):
        #    print('\t\"%s\": %s' % (pid, json.dumps(self.procs[pid], sort_keys=True, indent=4)), end='')
        #    if procs_length-1 > index:
        #        print(',')

        print(','.join( map( lambda pid: f'"{pid}": {json.dumps(self.procs[pid], sort_keys=True, indent=1)}' , self.procs.keys() ) ))
        print('},') 

        print('\n\n"Configs\" : {\n\n')
        configLength = len(self.configs)
        for indexConfig,c in enumerate(self.configs):
            lengthSelfConfigC = len(self.configs[c])
            print('\t\"%s\": { ' % c)
            for indexC,cfg in enumerate(self.configs[c]):
                self.configs[c][cfg]['options']={ 'omitted': 'use show' }
                self.configs[c][cfg]['credentials']=[ 'omitted' ]
                print('\t\t\"%s\" : %s ' % (cfg, json.dumps(self.configs[c][cfg])),end="")
                if lengthSelfConfigC-1 > indexC:
                   print(',')
            print('}',end="")
            if configLength-1 > indexConfig or configLength == 0:
               print(',')

        print('},\n\n"States": { \n\n')
        lengthSelfStates = len(self.states)
        for indexSelfStates,c in enumerate(self.states):
            print('\t\"%s\": { ' % c)
            lengthC = len(self.states[c])
            for indexC,cfg in enumerate(self.states[c]):
                print('\t\t\"%s\" :  %s ' % (cfg, json.dumps(self.states[c][cfg])))
                if lengthC -1 > indexC:
                   print(',')
            print( "\t}", end="")
            if lengthSelfStates -1 > indexSelfStates:
                print(',')
        print('},')

        print('\n\n"Bindings": { \n\n')
        lengthSelfBrokers = len(self.brokers)
        print("\n\"host\":{\n\t", end="")
        for indexSelfBrokers,h in enumerate(self.brokers):
            print("\"%s\": { \n" % h)
            print("\n\t\t\"exchanges\": { ", end="")
            lengthExchange = len(self.brokers[h]['exchanges'])
            for indexExchange,x in enumerate(self.brokers[h]['exchanges']):
                print("\"%s\":  %s " % (x, json.dumps(self.brokers[h]['exchanges'][x])), end="")
                if lengthExchange -1 > indexExchange:
                   print(',')
            print("},\n\t\t\"queues\": {")
            lengthBrokersQueues = len(self.brokers[h]['queues'])
            for indexBrokerQueues,q in enumerate(self.brokers[h]['queues']):
                print("\t\"%s\":  \"%s\" " % (q, self.brokers[h]['queues'][q]), end="")
                if lengthBrokersQueues -1 > indexBrokerQueues:
                   print(',')
            print( " \n}\n}",end="")
            if lengthSelfBrokers - 1 > indexSelfBrokers:
               print(',') 

        print('}\n},\n"nbroker summaries": {\n\n')
        lengthSelfBroker = len(self.brokers)
        print('\n\"broker\": {')
        for indexSelfBroker,h in enumerate(self.brokers):
            if 'admin' in self.brokers[h]:
                admin_url = self.brokers[h]['admin'].url
                admin_urlstr = "%s://%s@%s" % ( admin_url.scheme, \
                   admin_url.username, admin_url.hostname)
                if admin_url.port:
                    admin_urlstr += ":" + str(admin_url.port)
                a = 'admin: %s' % admin_urlstr
            else:
                a = 'admin: none'
            print('\"%s\":{' % (h))
            
            print('\n\"URL\": \"%s\",\n\"exchanges\": [ ' %(a), end='')
            lengthExchangeSummary  = len(self.exchange_summary[h])
            for indexSummary,x in enumerate(self.exchange_summary[h]):
                print("\"%s-%d\" " % (x, self.exchange_summary[h][x]), end='')
                if lengthExchangeSummary -1 > indexSummary:
                   print(',')
            print('],"queues\": [', end="")
            lengthBrokersQueues = len(self.brokers[h]['queues'])
            for indexBrokersSummary,q in enumerate(self.brokers[h]['queues']):
                print("\"%s-%d\" " % (q, len(self.brokers[h]["queues"][q])),end="")
                if lengthBrokersQueues -1 > indexBrokersSummary:
                   print(',')
            print(']\n}', end="")
            if lengthSelfBroker -1 > indexSelfBroker:
               print(',')
        print('}\n},\n\n\"Missing instances\" : [\n\n')
        lengthMissing = len(self.missing)
        for indexMissing,instance in enumerate(self.missing):
            (c, cfg, i) = instance
            print('\t\t\"%s/%s_%d\"' % (c, cfg, i),end="")
            if lengthMissing - 1 > indexMissing:
               print(',')
        print('] }')

    def status(self):
        """ v3 Printing prettier statuses for each component/configs found
        """

        if len(self.leftovers) > 0 and not self._action_all_configs:
            logging.error( f"{self.leftovers} configuration not found" )
            return

        flowNameWidth=self.cumulative_stats['flowNameWidth']
        latestTransferWidth=self.cumulative_stats['latestTransferWidth']

        lfmt = f"%-{flowNameWidth}s %-11s %7s %10s %19s %14s %38s "
        line = lfmt % ("Component/Config", "Processes", "Connection", "Lag", "", "Rates", "" )

        if self.options.displayFull:
            line += "%10s %-40s %17s %33s %40s" % ("", "Counters (per housekeeping)", "", "Data Counters", "" )
            line += "%s %-21s " % (" ", "Memory" ) 

        if self.options.displayFull:
            line += "%10s %10s " % ( " ", "CPU Time" )

        try:
            print(line)

            lfmt      = f"%-{flowNameWidth}s %-5s %5s %5s %4s %4s %5s %8s %8s %{latestTransferWidth}s %5s %10s %10s %10s %10s " 
            line      =  lfmt % ("", "State", "Run", "Retry", "msg", "data", "Que", "LagMax", "LagAvg", "Last", "%rej", "pubsub", "messages", "RxData", "TxData" )
            underline =  lfmt % ("", "-----", "---", "-----", "---", "----", "---", "------", "------", "----", "----", "------", "--------", "------", "------" )

            if self.options.displayFull:
                line      += "%10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %8s " % \
                        ( "Msg/scpu", "subBytes", "Accepted", "Rejected", "Malformed", "pubBytes", "pubMsgs", "pubMal", "rxData", "rxFiles", "txData", "txFiles", "Since" )
                underline += "%10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %8s " % \
                        ( "-------", "--------", "--------", "---------", "-------", "------", "-----", "-----", "-------", "------", "-------", "-----", "---" )

                line      += "%10s %10s %10s " % ( "uss", "rss", "vms"  )
                underline += "%10s %10s %10s " % ( "---", "---", "---"  )

            if self.options.displayFull:
                line      += "%10s %10s " % ( "user", "system" )
                underline += "%10s %10s " % ( "----", "------" )

            print(line)
            print(underline)
        except:
            return

        configs_running = 0
        now = time.time()

                
        for c in sorted(self.configs):
            for cfg in sorted(self.configs[c]):
                f = c + os.sep + cfg
                if f not in self.filtered_configurations:
                    continue
                if self.configs[c][cfg]['status'] == 'include':
                    continue

                if not (c in self.states and cfg in self.states[c]):
                    continue

                #find missing instances for this config.
                missing_instances = sum(map(lambda x: c in x and cfg in x, self.missing))
                if self.configs[c][cfg]['status'] != 'stopped':
                    expected = self.configs[c][cfg]['instances']
                    running = expected - missing_instances
                    if running > 0:
                        configs_running += 1
                else:
                    running = 0
                    expected = 0
                    missing_instances = 0

                cfg_status = self.configs[c][cfg]['status'][0:4]
                if cfg_status == "runn" and self._cfg_running_foreground(c, cfg):
                    cfg_status = "fore"
                if cfg_status == "lagg" :
                    cfg_status = "lag"
                if cfg_status == "retr" :
                    cfg_status = "rtry"
                if cfg_status == "runn" :
                    cfg_status = "run"
                elif cfg_status == 'wait':
                    cfg_status = 'wVip'

                process_status = "%d/%d" % ( running, expected ) 
                lfmt      = f"%-{flowNameWidth}s %-5s %5s "
                line= lfmt % (f, cfg_status, process_status ) 

                if 'metrics' in self.states[c][cfg]:
                    m=self.states[c][cfg]['metrics']
                    lfmt = f"%5d %3d%% %3d%% %5d %8s %8s %{latestTransferWidth}s %4.1f%% %8s/s %8s/s %8s/s %8s/s "
                    line += lfmt % ( m['retry'], m['connectPercent'], m['byteConnectPercent'], \
                            m['messagesQueued'], durationToString(m['lagMax']), durationToString(m['lagMean']), m['latestTransfer'], m['rejectPercent'],\
                            naturalSize(m['byteRate']).replace("Bytes","B"), \
                            naturalSize(m['msgRate']).replace("B","m").replace("mytes","m"), \
                            naturalSize(m['transferRxByteRate']).replace("Bytes","B"), \
                            naturalSize(m['transferTxByteRate']).replace("Bytes","B") 
                            )

                    if self.options.displayFull :
                        line += "%10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %7.2fs " % ( \
                            naturalSize(m['msgRateCpu']).replace("B","m").replace("mytes","m/s"), \
                            naturalSize(m['rxByteCount']).replace("Bytes","B"), \
                            naturalSize(m['rxGoodCount']).replace("B","m").replace("mytes","m"), \
                            naturalSize(m["rejectCount"]).replace("B","m").replace("mytes","m"), \
                            naturalSize(m["rxBadCount"]).replace("B","m").replace("mytes","m"), \
                            naturalSize(m['txByteCount']).replace("Bytes","B"), 
                            naturalSize(m['txGoodCount']).replace("B","m").replace("mytes","m"), \
                            naturalSize(m["txBadCount"]).replace("B","m").replace("mytes","m"), \
                            naturalSize(m["transferRxBytes"]).replace("Bytes","B"), \
                            naturalSize(m["transferRxFiles"]).replace("B","F").replace("Fytes","f"), \
                            naturalSize(m["transferTxBytes"]).replace("Bytes","B"), \
                            naturalSize(m["transferTxFiles"]).replace("B","F").replace("Fytes","f"), \
                            m["time_base"] )
                else:
                    line += "%10s %10s %9s %5s %5s %10s %8s " % ( "-", "-", "-", "-", "-", "-", "-" )
                    if self.options.displayFull:
                        line += "%8s %7s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s" % \
                            ( "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-" )

                if ('instance_pids' in self.states[c][cfg]) and (len(self.states[c][cfg]['instance_pids']) >= 0) and ('resource_usage' in self.states[c][cfg]):
                    ru = self.states[c][cfg]['resource_usage'] 

                    
                    if self.options.displayFull:
                        line += "%10s %10s %10s " % (\
                             naturalSize( ru['uss'] ), naturalSize( ru['rss'] ), naturalSize( ru['vms'] )  \
                             )
                        line += "%10.2f %10.2f " % (\
                             ru['user_cpu'], ru['system_cpu'] \
                             )
                else:
                    line += "%10s %10s %10s" % ( "-", "-", "-" )
                    if self.options.displayFull:
                        line += "%10s %10s" % ( "-", "-" )
                try:
                     print(line)
                except:
                     return
        stray = 0
        try:
            for pid in self.strays:
                stray += 1
                bad = 1
                print( f"pid:{pid} \"{self.strays[pid]}\" is not a configured instance" )

            print('      Total Running Configs: %3d ( Processes: %d missing: %d stray: %d )' %
                (configs_running, len(self.procs), len(self.missing), stray ) )
            print('                     Memory: uss:%s rss:%s vms:%s ' % ( \
                  naturalSize( self.resources['uss'] ), \
                  naturalSize( self.resources['rss'] ), naturalSize( self.resources['vms'] )\
                  ))
            print('                   CPU Time: User:%.2fs System:%.2fs ' % ( \
                  self.resources['user_cpu'] , self.resources['system_cpu'] \
                  ))

            print( '\t   Pub/Sub Received: %s/s (%s/s), Sent:  %s/s (%s/s) Queued: %d Retry: %d, Mean lag: %02.2fs' % ( 
                    naturalSize(self.cumulative_stats['rxMessageRate']).replace("B","m").replace("mytes","m"), \
                    naturalSize(self.cumulative_stats['rxMessageByteRate']).replace("Bytes","B"),\
                    naturalSize(self.cumulative_stats['txMessageRate']).replace("B","m").replace("mytes","m"),\
                    naturalSize(self.cumulative_stats['txMessageByteRate']).replace("Bytes","B"),
                    self.cumulative_stats['rxMessageQueued'], self.cumulative_stats['rxMessageRetry'], self.cumulative_stats['lagMean']
                ))
            print( '\t      Data Received: %s/s (%s/s), Sent: %s/s (%s/s) ' % (
                   naturalSize(self.cumulative_stats['rxFileRate']).replace("B","F").replace("Fytes","f") ,
                   naturalSize(self.cumulative_stats['rxDataRate']).replace("Bytes","B"),
                   naturalSize( self.cumulative_stats['txFileRate']).replace("B","F").replace("Fytes","f"),
                   naturalSize(self.cumulative_stats['txDataRate']).replace("Bytes","B") ) )

            # FIXME: does not seem to find any stray exchange (with no bindings...) hmm...
            for h in self.brokers:
                for x in self.exchange_summary[h]:
                    if self.exchange_summary[h][x] == 0:
                        print("exchange with no bindings: %s-%s " % (h, x), end='')
        except:
            pass

    def convert(self):

        print( f"v2_config: {self.v2_config}")
        if len(self.v2_config) == 0:
            print("need to specify what to convert from v2")
            return

        conversion_targets = self.v2_config
        if self.options.wololo and len(conversion_targets) > 1:
            if len(conversion_targets) != self.options.dangerWillRobinson :
                print( f" will not overwrite multiple configurations unless really sure" )
                print( f" If you are really sure, use --dangerWillRobinson={len(conversion_targets)}" )
                return

        for c in conversion_targets:
            self.convert1(c)

    def convert1(self,cfg):
        """
          converts one config.
        """
        component = cfg.split('/')[0]
        base_v2 = self.user_config_dir.replace('sr3', 'sarra') + os.sep
        base_v3 = self.user_config_dir + os.sep
        if os.path.exists(base_v2 + cfg):
            v2_config_path = base_v2 + cfg
            v3_config_path = base_v3 + cfg
        else:
            v2_config_path_inc = base_v2 + cfg + '.inc'
            v2_config_path_conf = base_v2 + cfg + '.conf'
            if os.path.exists(v2_config_path_conf):
                v2_config_path = v2_config_path_conf
                v3_config_path = base_v3 + cfg + '.conf'
            elif os.path.exists(v2_config_path_inc):
                v2_config_path = v2_config_path_inc
                v3_config_path = base_v3 + cfg + '.inc'
            else:
                logging.error('Invalid config %s' % cfg)
                return

        if not os.path.isdir(base_v3 + component):
            os.makedirs(base_v3 + component)

        if self.options.wololo:
            logger.warning("Wololo!" )
        elif os.path.exists(v3_config_path): 
            logger.error( f"{component}/{cfg} already exists in v3. To overwrite, use --wololo" )
            return

        synonyms = sarracenia.config.Config.synonyms
        accept_all_seen=False
        acceptUnmatched_explicit=False
        pos_args_present=False
        with open(v3_config_path, 'w') as v3_cfg:
            v3_cfg.write( f'# created by: sr3 convert {cfg}\n')
            if component in [ 'shovel', 'winnow' ]:
                v3_cfg.write('# topicCopy on is only there for bug-for-bug compat with v2. turn it off if you can.\n')
                v3_cfg.write('#topicCopy on\n')

            if component in [ 'sarra', 'sender', 'subscribe' ]:
                v3_cfg.write('#v2 sftp handling is always absolute, sr3 is relative. might need this, remove when all sr3:\n')
                v3_cfg.write('#flowcb accept.sftp_absolute\n')

            queueName=None

            #1st prep pass (for cases when re-ordering needed.)
            with open(v2_config_path, 'r') as v2_cfg:
                for line in v2_cfg.readlines():
                    if len(line.strip()) < 1:
                        continue
                    if line[0].startswith('#'):
                        continue
                    line = line.strip().split()
                    k = line[0]
                    if k in synonyms:
                        k = synonyms[k]
                    if k in [ 'queueName' ]:
                        queueName=line[1]

            #2nd re-write pass.
            subtopicFound=False
            with open(v2_config_path, 'r') as v2_cfg:
                for line in v2_cfg.readlines():
                    if len(line.strip()) < 1:
                        v3_cfg.write('\n')
                        continue
                    if line[0].startswith('#'):
                        v3_cfg.write(line)
                        continue
                    line = line.strip().split()
                    k = line[0]
                    if k in synonyms:
                        k = synonyms[k]

                    if k == 'destination':
                        if component == 'poll':
                            k = 'pollUrl'
                            v3_cfg.write('permCopy off\n')
                        else:
                            k = 'sendTo'
                    elif (k == 'get' ) and (component == 'poll'):
                        k = 'accept'
                        if not line[1].startswith('.*'):
                            if line[1][0] == '^':
                                line[1] = '.*/'+line[1][1:]
                            else:
                                line[1] = '.*'+line[1]
                    elif (k == 'broker') and (component == 'poll'):
                        k = 'post_broker'
                    elif (k == 'directory' ) and (component == 'poll'):
                        k = 'path'
                    elif k in [ 'identity', 'integrity' ]:
                        if line[1][0] in sum_algo_v2tov3:
                           method=sum_algo_v2tov3[line[1][0]]
                           if method == 'cod':
                               if line[1][3] in sum_algo_v2tov3:
                                   value=sum_algo_v2tov3[line[1][3]]
                                   line[1]=f"{method},{value}"
                               else:
                                   logger.error( f"unknown checksum spec: {line}")
                                   continue
                        else:
                            logger.error( f"unknown checksum spec: {line}")
                            continue
                    elif k == 'queueName':
                        if subtopicFound or not queueName:
                            continue
                    elif k == 'subtopic':
                        if queueName:
                            v3_cfg.write(f'queueName {queueName}\n')
                            queueName=None
                    if (k == 'accept') :
                        if line[1] == '.*':
                            accept_all_seen=True
                            continue
                    elif ( k == 'acceptUnmatched' ):
                            acceptUnmatched_explicit=line[1]
                            continue
                    elif ( k == 'post_baseUrl' ) and line[1][-1] != '/':
                            line[1]+='/'
                            # see: https://github.com/MetPX/sarracenia/issues/841
                    elif (k == 'sleep' ) and (component == 'poll'):
                        k = 'scheduled_interval'
                    if k in convert_to_v3:
                        if convert_to_v3[k] == [ 'continue' ]:
                            logger.info( f"obsolete v2 keyword: {k}" )
                            continue

                        if len(line) > 1:
                            v = line[1].replace('.py', '', 1)
                            if v in convert_to_v3[k]:
                                line = convert_to_v3[k][v]
                                if 'continue' in line:
                                    logger.info("obsolete v2: " + k)
                                    continue
                            else:
                                logger.warning( f"unknown {k} {v}, manual conversion required.")
                                v3_cfg.write( f"# PROBLEM: unknown {k} {v}, manual conversion required.\n")
                        else:
                            line = convert_to_v3[k]
                            k = line[0]
                            v = line[1]
                    else:
                        line[0] = k

                    if k in [ 'logEvents', 'fileEvents' ]: # set option semantics changed as per https://github.com/MetPX/sarracenia/issues/608 
                        if 'none' in line[1].lower():
                            v=line[1]
                        else:
                            if line[1][0] not in ['+','-']:
                                line[1]= '+' + line[1]
                            v=line[1]

                    if k == 'continue':
                        continue

                    if len(line) > 1:
                        for p in convert_patterns_to_v3:
                            while p in line[1]:
                               line[1] = line[1].replace(p,convert_patterns_to_v3[p])

                    if not pos_args_present and re.search( r'\${[0-9]}', ' '.join(line[1:]) ):
                         pos_args_present=True
                         v3_cfg.write('sundew_compat_regex_first_match_is_zero True\n')
                    v3_cfg.write(' '.join(line)+'\n')
                if accept_all_seen:
                    pass
                    #v3_cfg.write('accept .*\n')
                elif acceptUnmatched_explicit:
                    v3_cfg.write( f"acceptUnmatched {acceptUnmatched_explicit}")
                elif component in [ 'subscribe', 'poll', 'sender' ]: # accomodate change of default from v2 to sr3
                    v3_cfg.write( f"acceptUnmatched False")

        logger.info( f'wrote conversion from v2 {cfg} to sr3' )


    def overview(self):
        """ v2 Printing statuses for each component/configs found

        :return:
        """

        if len(self.leftovers) > 0 and not self._action_all_configs:
            logging.error( f"{self.leftovers} configuration not found" )
            return

        bad = 0


        print('%-10s %-10s %-6s %3s %s' %
              ('Component', 'State', 'Good?', 'Qty',
               'Configurations-i(r/e)-r(Retry)'))
        print('%-10s %-10s %-6s %3s %s' %
              ('---------', '-----', '-----', '---',
               '------------------------------'))

        configs_running = 0
        for c in self.configs:

            status = {}
            for sv in self.status_values:
                status[sv] = []

            for cfg in self.configs[c]:

                f = c + os.sep + cfg
                if f not in self.filtered_configurations:
                    continue

                sfx = ''
                if self.configs[c][cfg]['status'] == 'include':
                    continue

                if not (c in self.states and cfg in self.states[c]):
                    continue

                if self.configs[c][cfg]['status'] != 'stopped':
                    m = sum(map(
                        lambda x: c in x and cfg in x,
                        self.missing))  #perhaps expensive, but I am lazy FIXME
                    sfx += '-i%d/%d' % ( \
                        len(self.states[c][cfg]['instance_pids']) - m, \
                        self.configs[c][cfg]['instances'])
                status[self.configs[c][cfg]['status']].append(cfg + sfx)

            if (len(status['partial']) + len(status['running'])) < 1:
                print('%-10s %-10s %-6s %3d %s' %
                      (c, 'stopped', 'OK', len(status['stopped']), ', '.join(
                          status['stopped'])))
            elif len(status['running']) == len(self.configs[c]):
                print('%-10s %-10s %-6s %3d %s' %
                      (c, 'running', 'OK', len(self.configs[c]), ', '.join(
                          status['running'])))
            elif len(status['running']) == (len(self.configs[c]) -
                                            len(status['disabled'])):
                print('%-10s %-10s %-6s %-3d %s' % (c, 'most', 'OKd', \
                    len(self.configs[c]) - len(status['disabled']),  ', '.join(status['running'] )))
            else:
                print('%-10s %-10s %-6s %3d' %
                      (c, 'mixed', 'mult', len(self.configs[c])))
                bad = 1
                for sv in self.status_values:
                    if len(status[sv]) > 0:
                        print('    %3d %s: %s ' %
                              (len(status[sv]), sv, ', '.join(status[sv])))

            configs_running += len(status['running'])

        stray = 0
        for pid in self.procs:
            if not self.procs[pid]['claimed']:
                stray += 1
                bad = 1
                print( f"pid: {pid}-\"{' '.join(self.procs[pid]['cmdline'])}\" is not a configured instance" )

        print('      total running configs: %3d ( processes: %d missing: %d stray: %d )' % \
            (configs_running, len(self.procs), len(self.missing), stray))

        # FIXME: does not seem to find any stray exchange (with no bindings...) hmm...
        for h in self.brokers:
            for x in self.exchange_summary[h]:
                if self.exchange_summary[h][x] == 0:
                    print("exchange with no bindings: %s-%s " % (h, x), end='')

        return bad

    def _pid_running_foreground(self, pid):
        """Returns True if the specified pid is running in the foreground.
        Possible cases:
          * anything with ``foreground`` in its cmd_line is always foreground.
          * anything with ``start`` in its cmd_line is always a daemon (not foreground).
          * posts and cposts without ``start`` in the cmd_line are always foreground.
          * other components without ``start`` or ``foreground`` will return False.

        Args:
            pid: the pid to check.

        Returns: True if foreground, False if not.
        """
        if not pid in self.procs:   # indicates a process that crashed.
            return False

        if 'foreground' in self.procs[pid]['cmdline']:
            return True
        elif 'start' in self.procs[pid]['cmdline']:
            return False
        # Default behavior for sr3_(c)post is to run in the foreground
        elif 'sr3_cpost' in self.procs[pid]['cmdline'] or 'sr3_post' in self.procs[pid]['cmdline']:
            return True
        else:
            return False

    def _cfg_running_foreground(self, component, config):
        """Returns True if the specified config is running in the foreground.

        Args:
            component: the config's component
            config: config to check

        Returns: True if foreground, False if not.
        """
        for pid_id, pid in self.states[component][config]['instance_pids'].items():
            return self._pid_running_foreground(pid)

    def _post_can_be_daemon(self, component, config):
        """Returns True if a post or cpost config can run as a daemon. Criteria is that a path and sleep value > 0 are
        defined in the config. Configs with no sleep value get set to the default in config.py (0.1).

        Args:
            component: the config's component
            config: config to check

        Returns: True if the config can run as a daemon, False if not.
        """
        return (component in ['post', 'cpost'] and self.configs[component][config]['options'].sleep > 0.1 and
                hasattr(self.configs[component][config]['options'], 'path'))

    def _instance_num_from_pidfile(self, pathname, component, cfg):
        if os.sep in pathname:
            pathname = pathname.split(os.sep)[-1]
        if '_' in pathname:
            i = int(pathname[0:-4].split('_')[-1])
        # sr3c components just use iXX.pid
        elif component[0] == 'c':
            i = int(pathname[0:-4].replace('i', ''))
        else:
            logger.error(f"Failed to determine instance # for {component}/{cfg} {pathname}")
            i = -1
        return i


def main():
    """ Main thread for sr dealing with parsing and action switch

    :return:
    """
    logger = logging.getLogger()
    logging.basicConfig(
        format='%(asctime)s %(process)d [%(levelname)s] %(name)s %(funcName)s %(message)s',
        level=logging.DEBUG)
    logger.setLevel(logging.INFO)

    if len(sys.argv) > 1:
        if sys.argv[1] == '--debug':
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

    actions = [
        'convert', 'declare', 'devsnap', 'dump', 'edit', 'features', 'log', 'overview', 'restart', 'run', 'sanity',
        'setup', 'show', 'status', 'start', 'stop'
    ]

    cfg = sarracenia.config.Config({
        'acceptUnmatched': True,
        'exchange': 'xpublic',
        'inline': False,
        'logStdout': False,
        'inlineEncoding': 'auto',
        'inlineByteMax': 4096,
        'subtopic': None
    })

    cfg.parse_args()

    #FIXME... hmm... so...
    #cfg.finalize()

    if not hasattr(cfg, 'action'):
        print('USAGE: %s [ -h ] (%s)' % (sys.argv[0], '|'.join(actions)))
        return

    action = cfg.action

    if cfg.logStdout:
       logging.basicConfig(
           format= '%(asctime)s [%(levelname)s] %(process)d %{processName}s %(name)s %(funcName)s %(message)s' )

    gs = sr_GlobalState(cfg, cfg.configurations)

    #print("filtered_config: %s" % gs.filtered_configurations )
    # testing proc file i/o
    #gs.read_proc_file()

    if action in ['add']:
        print('%s: ' % action, end='', flush=True)
        gs.add()

    if action in ['declare', 'setup']:
        print('%s: ' % action, end='', flush=True)
        gs.declare()

    if action == 'cleanup':
        print('cleanup: ', end='', flush=True)
        gs.cleanup()

    elif action == 'devsnap':
        if len(sys.argv) < 3:
            print('devsnap requires alternate app name as argument')
            sys.exit(1)

        gs.save_states(sys.argv[2])
        gs.save_configs(sys.argv[2])
        gs.appname = sys.argv[2]
        gs.save_procs(gs.user_cache_dir + os.sep + "procs.json")

    if action == 'disable':
        gs.disable()

    if action == 'dump':
        gs.dump()

    if action == 'edit':
        gs.edit()

    if action == 'enable':
        gs.enable()

    if action == 'features':
        gs.features()

    if action == 'foreground':
        gs.foreground()

    if action == 'list':
        gs.config_list()

    if action == 'log':
        gs.log()

    if action == 'convert':
        gs.convert()

    if action == 'remove':
        if gs.cleanup():
            gs.remove()

    elif action == 'restart':
        print('stopping: ', end='', flush=True)
        gs.stop()
        print('starting: ', end='', flush=True)
        gs.start()

    elif action == 'sanity':
        print('sanity: ', end='', flush=True)
        gs.sanity()

    if action == 'show':
        gs.config_show()

    elif action == 'run':
        print('running:', end='', flush=True)
        gs.run()

    elif action == 'start':
        print('starting:', end='', flush=True)
        gs.start()

    elif action == 'overview':
        print('status: ')
        sys.exit(gs.overview())

    elif action == 'status':
        print('status: ')
        sys.exit(gs.status())

    elif action == 'stop':
        print('Stopping: ', end='', flush=True)
        gs.stop()

    print('')


if __name__ == "__main__":
    main()
