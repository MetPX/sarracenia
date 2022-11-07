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
import psutil
import random
import re
import shutil
import signal
import socket
import subprocess
import sys
import time

from sarracenia import user_config_dir, user_cache_dir
from sarracenia.config import *
import sarracenia.moth
import sarracenia.rabbitmq_admin

import urllib.parse

logger = logging.getLogger(__name__)


def ageoffile(lf):
    """ return number of seconds since a file was modified as a floating point number of seconds.
        FIXME: mocked here for now. 
    """
    return 0

def signal_pid( pid, sig ):
    """
        wrap os.kill in a try/except for cleaner error messages and avoid control jumping somewhere
        unexpected.
    """
    try:
       os.kill(pid, sig)
    except Exception as ex:
       logger.warning('sending kill signal to pid:%s failed: %s' % ( pid, ex))

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
                    lfn = self.user_cache_dir + os.sep + self.hostname
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
                        os.sleep(1)
                
        if c in [ 'flow',
                'poll', 'post', 'report', 'sarra', 'sender', 'shovel',
                'subscribe', 'watch', 'winnow'
        ]:
            component_path = os.path.dirname(
                component_path) + os.sep + 'instance.py'
            cmd = [sys.executable, component_path, '--no', "%d" % i]

            # would like to forward things like --debug...
            for arg in sys.argv[1:-1]:
                if arg in ['start', 'restart']:
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

        try:
            if self.configs[c][cfg]['options'].logStdout:
                subprocess.Popen(cmd)
            else:
                with open(lfn, "a") as lf:
                    subprocess.Popen(cmd,
                                 stdin=subprocess.DEVNULL,
                                 stdout=lf,
                                 stderr=subprocess.STDOUT)
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
            for proc in psutil.process_iter():
                f.write(
                    json.dumps(proc.as_dict(
                        ['pid', 'cmdline', 'name', 'username', 'create_time']),
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

        #print( 'sr? name=%s, pid=%s, cmdline=%s' % ( p['name'], p['pid'], p['cmdline'] ) )
        if ( sys.platform == 'win32') and ( p['name'][-4:].lower() == '.exe' ):
            # on windows, it seems to fork .exe and then there is a -script.py which is the right pid
            # .e.g sr_subscribe.exe -> sr_subscribe-script.py ... If you kill the -script, the .exe goes away.
            return

        if p['name'].startswith('sr3_'):
            self.procs[p['pid']] = p
            if p['name'][3:8] == 'audit':
                self.procs[p['pid']]['claimed'] = True
                self.auditors += 1
            else:
                self.procs[p['pid']]['claimed'] =   (p['name'][-4:] == 'post') or \
                    any( item in [ 'declare', 'edit', 'foreground', 'sanity', 'setup', 'status' ] for item in  p['cmdline'] )

    def read_proc_file(self, File="procs.json"):
        """
           read process table from a save file, for reproducible testing.
        """
        self.procs = {}
        self.auditors = 0
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
        self.auditors = 0
        for proc in psutil.process_iter():
            try:
                self._filter_sr_proc(
                    proc.as_dict(
                        ['pid', 'cmdline', 'name', 'username', 'create_time']))
            except:
                pass # the process went away while iterating. avoid spurious message.

    def _read_configs(self):
        # read in configurations.
        self.configs = {}
        if not os.path.isdir(self.user_config_dir):
            return

        self.default_cfg = sarracenia.config.default_config()

        #self.default_cfg = sarracenia.config.Config()
        #if os.path.exists( "default.conf" ):
        #    self.default_cfg.parse_file("default.conf")
        #if os.path.exists( "admin.conf" ):
        #    self.default_cfg.parse_file("admin.conf")

        #self.admin_cfg = copy.deepcopy( self.default_cfg )
        #if os.path.exists( "admin.conf" ):
        #    self.admin_cfg.parse_file("admin.conf")
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
                        cbase = cfg
                        state = 'unknown'

                    self.configs[c][cbase] = {}
                    self.configs[c][cbase]['status'] = state
                    if state != 'unknown':
                        cfgbody = copy.deepcopy(self.default_cfg)
                        cfgbody.override({
                            'component': c,
                            'config': cbase,
                            'directory': '${PWD}'
                        })
                        cfgbody.applyComponentDefaults( c )
                        cfgbody.parse_file(cfg,c)
                        cfgbody.fill_missing_options(c, cfg)
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
            os.mkdir(other_config_dir)

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

    def _read_state_dir(self, dir1):

        # read in state files
        if not os.path.isdir(dir1):
            return
        os.chdir(dir1)

        for c in self.components:
            if os.path.isdir(c):
                os.chdir(c)
                for cfg in os.listdir():
                    if os.path.isdir(cfg):
                        os.chdir(cfg)
                        self.states[c][cfg] = {}
                        self.states[c][cfg]['instance_pids'] = {}
                        self.states[c][cfg]['queueName'] = None
                        if c in self.configs:
                            if cfg not in self.configs[c]:
                                self.states[c][cfg]['status'] = 'removed'

                        self.states[c][cfg]['has_state'] = False
                        self.states[c][cfg]['retry_queue'] = 0

                        for pathname in os.listdir():
                            p = pathlib.Path(pathname)
                            if p.suffix in ['.pid', '.qname', '.state']:
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
                                    i = int(pathname[-6:-4])
                                    if t.isdigit():
                                        #print( "%s/%s instance: %s, pid: %s" % ( c, cfg, i, t ) )
                                        self.states[c][cfg]['instance_pids'][
                                            i] = int(t)
                                elif pathname[-6:] == '.qname':
                                    self.states[c][cfg]['queueName'] = t
                                elif pathname[-12:] == '.retry.state':
                                    buffer = 2**16
                                    try:
                                        with open(p) as f:
                                            self.states[c][cfg][
                                                'retry_queue'] += sum(
                                                    x.count('\n')
                                                    for x in iter(
                                                        partial(
                                                            f.read, buffer),
                                                        ''))
                                    except Exception as ex:
                                        #print( 'info reading statefile %p gone before it was read: %s' % (p, ex) )
                                        pass

                        os.chdir('..')
                os.chdir('..')

    def _read_states(self):
        self.states = {}
        for c in self.components:
            self.states[c] = {}

        self._read_state_dir(self.user_cache_dir)
        self._read_state_dir(self.user_cache_dir + os.sep + self.hostdir)

    def _find_missing_instances_dir(self, dir):
        """ find processes which are no longer running, based on pidfiles in state, and procs.
        """
        missing = []
        if not os.path.isdir(dir):
            return
        os.chdir(dir)
        for c in self.components:
            if os.path.isdir(c):
                os.chdir(c)
                for cfg in os.listdir():
                    if cfg[0] == '.': continue
                    
                    if cfg not in self.configs[c]: continue

                    if os.path.isdir(cfg):
                        os.chdir(cfg)
                        for filename in os.listdir():
                            # look at pid files, find ones where process is missing.
                            if filename[-4:] == '.pid':
                                i = int(filename[-6:-4])
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
                        if ( len(self.states[c][cfg]['instance_pids']) > 0 ) or ( len(missing) > 0 ) :
                            # look for instances that should be running, but no pid file exists.
                            for i in range(1, int(self.configs[c][cfg]['instances'])+1 ):
                                if not i in self.states[c][cfg]['instance_pids']:
                                    if i not in self.procs:
                                        if i != 0:
                                            missing.append([c,cfg,i])
                        os.chdir('..')
                os.chdir('..')

        self.missing.extend(missing)

    def _find_missing_instances(self):
        self.missing = []
        self._find_missing_instances_dir(self.user_cache_dir)
        self._find_missing_instances_dir(self.user_cache_dir + os.sep +
                                         self.hostdir)

    def _clean_missing_proc_state_dir(self, dir):
        """ remove state pid files for process which are not running
        """

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
        if os.path.isdir('log'):
            self.logs = {}
            for c in self.components:
                self.logs[c] = {}

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
                        if suffix[1] == 'log':
                            try:
                                inum = int(suffix[0])
                            except:
                                inum = 0
                            age = ageoffile(lf)
                            if cfg not in self.logs[c]:
                                self.logs[c][cfg] = {}
                            self.logs[c][cfg][inum] = age

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

                if hasattr(o, 'broker') and o.broker is not None and o.broker.url is not None:
                    host = self._init_broker_host(o.broker.url.netloc)

                    xl = self.__resolved_exchanges(c, cfg, o)

                    q = self.__guess_queueName(c, cfg, o)

                    self.configs[c][cfg]['options'].resolved_qname = q

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

                    #o.broker = o.post_broker
                    if hasattr(o, 'post_exchange'):
                        o.exchange = o.post_exchange
                    if hasattr(o, 'post_exchangeSplit'):
                        o.exchangeSplit = o.post_exchangeSplit
                    if hasattr(o, 'post_exchangeSuffix'):
                        o.exchangeSuffix = o.post_exchangeSuffix

                    xl = self.__resolved_exchanges(c, cfg, o)

                    self.configs[c][cfg]['options'].resolved_exchanges = xl

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

        if not os.path.exists( self.user_cache_dir ):
            os.makedirs(self.user_cache_dir)

        # comparing states and configs to find missing instances, and correct state.
        for c in self.components:
            if not os.path.exists( self.user_cache_dir + os.sep + c ):
                os.mkdir(self.user_cache_dir + os.sep + c )
            if (c not in self.states) or (c not in self.configs):
                continue

            for cfg in self.configs[c]:
                if cfg not in self.states[c]:
                    print('missing state for %s/%s' % (c,cfg))
                    os.mkdir(self.user_cache_dir + os.sep + c + os.sep + cfg)
                    # add config as state in .cache under right directory.
                    self.states[c][cfg] = {}
                    self.states[c][cfg]['instance_pids'] = {}
                    self.states[c][cfg]['queueName'] = None
                    self.states[c][cfg]['status'] = 'stopped'
                    self.states[c][cfg]['has_state'] = False
                    self.states[c][cfg]['retry_queue'] = 0
                    continue
                if os.path.exists(self.user_cache_dir + os.sep + c + os.sep + cfg + os.sep + 'disabled'):
                    self.configs[c][cfg]['status'] = 'disabled'
                if len(self.states[c][cfg]['instance_pids']) >= 0:
                    self.states[c][cfg]['missing_instances'] = []
                    observed_instances = 0
                    for i in self.states[c][cfg]['instance_pids']:
                        if self.states[c][cfg]['instance_pids'][
                                i] not in self.procs:
                            self.states[c][cfg]['missing_instances'].append(i)
                        else:
                            observed_instances += 1
                            self.procs[self.states[c][cfg]['instance_pids']
                                       [i]]['claimed'] = True

                    if observed_instances < int(self.configs[c][cfg]['instances']):
                        if (c == 'post') and (('sleep' not in self.states[c][cfg]) or self.states[c][cfg]['sleep'] <= 0):
                            if self.configs[c][cfg]['status'] != 'disabled':
                                self.configs[c][cfg]['status'] = 'stopped'
                        else:
                            if observed_instances > 0:
                                self.configs[c][cfg]['status'] = 'partial'
                                for i in range(1, int(self.configs[c][cfg]['instances'])+1 ):
                                    if not i in self.states[c][cfg]['instance_pids']:
                                         self.states[c][cfg]['missing_instances'].append(i)
                            else:
                                if self.configs[c][cfg]['status'] != 'disabled':
                                    self.configs[c][cfg]['status'] = 'stopped'
                    elif observed_instances == 0:
                        self.configs[c][cfg]['status'] = 'stopped'
                    else:
                        self.configs[c][cfg]['status'] = 'running'

        # FIXME: missing check for too many instances.

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

        candidates = ['audit']
        for c in self.components:
            if (c not in self.configs):
                continue
            for cfg in self.configs[c]:
                fcc = c + os.sep + cfg
                candidates.append(fcc)

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
                        if c == 'audit': continue
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
        self.package_lib_dir = os.path.dirname(
            inspect.getfile(sarracenia.config.Config))
        self.appauthor = 'MetPX'
        self.options = opt
        self.appname = os.getenv('SR_DEV_APPNAME')
        self.hostname = socket.getfqdn()
        self.hostdir = self.hostname.split('.')[0]
        self.users = opt.users
        self.declared_users = opt.declared_users

        signal.signal(signal.SIGTERM, self._stop_signal)
        signal.signal(signal.SIGINT, self._stop_signal)

        if self.appname is None:
            self.appname = 'sr3'
        else:
            print(
                'DEVELOPMENT using alternate application name: %s, bindir=%s' %
                (self.appname, self.bin_dir))

        if not os.path.isdir(self.user_config_dir):
            print('WARNING: No %s configuration found.' % self.appname)

        if not os.path.isdir(self.user_cache_dir):
            print('WARNING: No %s configuration state or log files found.' %
                  self.appname)

        self.components = [
            'cpost', 'cpump', 'flow', 'poll', 'post', 'report', 'sarra',
            'sender', 'shovel', 'subscribe', 'watch', 'winnow'
        ]
        self.status_values = [
            'disabled', 'include', 'stopped', 'partial', 'running', 'unknown'
        ]

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
        # Signal is also sent to subprocesses. Once they exit, subprocess.run returns and sr.py should terminate.

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

            iedir = os.path.dirname(inspect.getfile(
                sarracenia.config.Config)) + os.sep + 'examples'

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

        if self.users:
            for h in self.brokers:
                if 'admin' in self.brokers[h]:
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
                            if u_url.username in self.default_cfg.declared_users:
                                #print( 'u_url : user:%s, pw:%s, role: %s' % \
                                #    (u_url.username, u_url.password, self.default_cfg.declared_users[u_url.username]))
                                sarracenia.rabbitmq_admin.add_user( \
                                    self.brokers[h]['admin'].url, \
                                    self.default_cfg.declared_users[u_url.username],
                                    u_url.username, u_url.password, self.options.dry_run )

        # declare exchanges first.
        for f in self.filtered_configurations:
            if f == 'audit': continue
            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue
            logging.info('looking at %s/%s ' % (c, cfg))
            o = self.configs[c][cfg]['options']
            if hasattr(
                    o,
                    'resolved_exchanges') and o.resolved_exchanges is not None:
                xdc = sarracenia.moth.Moth.pubFactory(
                    o.post_broker, {
                        'broker': o.post_broker,
                        'exchange': o.resolved_exchanges,
                        'message_strategy': { 'stubborn':True }
                    })
                xdc.close()

        # then declare and bind queues....
        for f in self.filtered_configurations:
            if f == 'audit': continue

            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue
            logging.info('looking at %s/%s ' % (c, cfg))
            o = self.configs[c][cfg]['options']
            od = o.dictify()
            if hasattr(o, 'resolved_qname'):
                od['queueName'] = o.resolved_qname
                qdc = sarracenia.moth.Moth.subFactory(o.broker, od)
                qdc.close()

    def disable(self):
        if len(self.filtered_configurations) == 0:
            logging.error('%s configuration not found', self.leftovers)
            return

        for f in self.filtered_configurations:
            if f == 'audit': continue
            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue

            if len(self.states[c][cfg]['instance_pids']) > 0:
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
            if f == 'audit': continue
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
        if len(self.filtered_configurations) == 0:
            logging.error('%s configuration not found', self.leftovers)
            return
        # declare exchanges first.
        for f in self.filtered_configurations:
            if f == 'audit': continue
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

    def foreground(self):

        for f in self.filtered_configurations:
            if f == 'audit': continue
            (c, cfg) = f.split(os.sep)

            component_path = self._find_component_path(c)
            pcount = 0

            if component_path == '':
                continue

            if self.configs[c][cfg]['status'] in ['stopped']:
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
                    if sys.argv[0].find('python') >= 0:
                        cmd.extend(sys.argv[2:])
                    else:
                        cmd.extend(sys.argv[1:])

                elif c[0] != 'c':  # python components
                    if cfg is None:
                        cmd = [sys.executable, component_path, 'foreground']
                    else:
                        cmd = [sys.executable, component_path, 'foreground', cfg]
                else:  # C components
                    cmd = [component_path, 'foreground', cfg]

                self.run_command(cmd)
            else:
                print('foreground: stop other instances of this process first')

    def cleanup(self):

        if len(self.filtered_configurations
               ) > 1 and not self.options.dangerWillRobinson:
            logging.error(
                "specify --dangerWillRobinson to cleanup > 1 config at a time")
            return

        queues_to_delete = []
        for f in self.filtered_configurations:
            if f == 'audit': continue
            (c, cfg) = f.split(os.sep)

            o = self.configs[c][cfg]['options']

            if hasattr(o, 'resolved_qname'):
                #print('deleting: %s is: %s @ %s' % (f, o.resolved_qname, o.broker.url.hostname ))
                qdc = sarracenia.moth.Moth.subFactory(
                    o.broker, {
                        'echangeDeclare': False,
                        'queueDeclare': False,
                        'queueBind': False,
                        'broker': o.broker,
                        'queueName': o.resolved_qname,
                        'message_strategy': { 'stubborn':True }
                    })
                qdc.getCleanUp()
                qdc.close()
                queues_to_delete.append((o.broker, o.resolved_qname))

        for h in self.brokers:
            for qd in queues_to_delete:
                if qd[0].url.hostname != h: continue
                for x in self.brokers[h]['exchanges']:
                    xx = self.brokers[h]['exchanges'][x]
                    if qd[1] in xx:
                        if 'admin' not in self.brokers[h]:
                            continue
                        print(' remove %s from %s subscribers: %s ' %
                              (qd[1], x, xx))
                        xx.remove(qd[1])
                        if len(xx) < 1:
                            print("no more queues, removing exchange %s" % x)
                            qdc = sarracenia.moth.Moth.pubFactory(
                                o.post_broker, {
                                    'declare': False,
                                    'exchange': x,
                                    'broker': self.brokers[h]['admin'],
                                    'message_strategy': { 'stubborn':True }
                                })
                            if qdc:
                                qdc.putCleanUp()
                                qdc.close()

        self.user_cache_dir
        for f in self.filtered_configurations:
            cache_dir = self.user_cache_dir + os.sep + f.replace('/', os.sep)
            for state_file in os.listdir(cache_dir):
                if state_file[0] == '.':
                    continue

                asf = cache_dir + os.sep + state_file
                print('removing state file: %s' % asf)
                os.unlink(asf)

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
            if f == 'audit': continue
            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue

            o = self.configs[c][cfg]['options']
            print('\nConfig of %s/%s: ' % (c, cfg))
            o.dump()

    def remove(self):

        if len(self.filtered_configurations) == 0:
            logging.error("No configuration matched")
            return

        if len(self.filtered_configurations
               ) > 1 and not self.options.dangerWillRobinson:
            logging.error(
                "specify --dangerWillRobinson to remove > 1 config at a time")
            return

        for f in self.filtered_configurations:

            if f == 'audit': continue
            (c, cfg) = f.split(os.sep)

            if not 'options' in self.configs[c][cfg]:
                continue

            if not cfg in self.states[c]:
                continue

            if ('instance_pids' in self.states[c][cfg]) and len(
                    self.states[c][cfg]['instance_pids']) > 0:
                logging.error("cannot remove %s/%s while it is running! " % ( c, cfg ) )
                continue

            cfgfile = self.user_config_dir + os.sep + c + os.sep + cfg + '.conf'
            statefile = self.user_cache_dir + os.sep + c + os.sep + cfg

            logging.info('removing %s/%s ' % ( c, cfg ))
            os.unlink(cfgfile)
            shutil.rmtree(statefile)

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
        pcount = 0
        for f in self.filtered_configurations:
            (c, cfg) = f.split(os.sep)
            component_path = self._find_component_path(c)
            if component_path == '':
                continue
            if self.configs[c][cfg]['status'] in ['stopped']:
                numi = self.configs[c][cfg]['instances']
                for i in range(1, numi + 1):
                    if pcount % 10 == 0: print('.', end='', flush=True)
                    pcount += 1
        if pcount != 0:
            self._find_missing_instances()
            filtered_missing = []
            for m in self.missing:
                if m[0] + os.sep + m[1] in self.filtered_configurations:
                    filtered_missing.append(m)

            print('missing: %s' % filtered_missing)
            print('starting them up...')
            self._start_missing()

            print('killing strays...')
            for pid in self.procs:
                if not self.procs[pid]['claimed']:
                    print(
                        "pid: %s-%s does not match any configured instance, sending it TERM"
                        % (pid, self.procs[pid]['cmdline'][0:5]))
                    signal_pid(pid, signal.SIGTERM)
        else:
            print('no missing processes found')
        for l in sarracenia.extras.keys():
            if not sarracenia.extras[l]['present']:
                print( f"notice: python module {l} is missing: {sarracenia.extras[l]['lament']}" )

    def start(self):
        """ Starting all components

        :return:
        """

        pcount = 0
        for f in self.filtered_configurations:

            if f == 'audit':
                if self.auditors == 0:
                    component_path = self._find_component_path(f)
                    self._launch_instance(component_path, f, None, 1)
                    continue

            (c, cfg) = f.split(os.sep)

            # skip posts that cannot run as daemons
            if c in ['post', 'cpost'] and not self._post_can_be_daemon(c, cfg): continue

            component_path = self._find_component_path(c)
            if component_path == '':
                continue

            if self.configs[c][cfg]['status'] in ['stopped']:
                numi = self.configs[c][cfg]['instances']
                for i in range(1, numi + 1):
                    if pcount % 10 == 0: print('.', end='', flush=True)
                    pcount += 1
                    self._launch_instance(component_path, c, cfg, i)

        print('( %d ) Done' % pcount)

    def stop(self):
        """
           stop all of this users sr_ processes. 
           return 0 on success, non-zero on failure.
        """
        self._clean_missing_proc_state()

        if len(self.procs) == 0:
            print('...already stopped')
            return

        print('sending SIGTERM ', end='', flush=True)
        pcount = 0
        fg_instances = set()
        # kill sr_audit first, so it does not restart while others shutting down.
        # https://github.com/MetPX/sarracenia/issues/210

        if ('audit' in self.filtered_configurations) and self.auditors > 0:
            for p in self.procs:
                if 'audit' in self.procs[p]['name']:
                    signal_pid(p, signal.SIGTERM)
                    print('.', end='', flush=True)
                    pcount += 1

        for f in self.filtered_configurations:
            if f == 'audit': continue

            (c, cfg) = f.split(os.sep)

            # exclude foreground instances unless --dangerWillRobinson specified
            if (not self.options.dangerWillRobinson) and self._cfg_running_foreground(c, cfg):
                fg_instances.add(f"{c}/{cfg}")
                continue

            if self.configs[c][cfg]['status'] in ['running', 'partial']:
                for i in self.states[c][cfg]['instance_pids']:
                    # print( "for %s/%s - %s signal_pid( %s, SIGTERM )" % \
                    #    ( c, cfg, i, self.states[c][cfg]['instance_pids'][i] ) )
                    if self.states[c][cfg]['instance_pids'][i] in self.procs:
                        signal_pid(self.states[c][cfg]['instance_pids'][i],
                                signal.SIGTERM)
                        print('.', end='', flush=True)
                        pcount += 1

        print(' ( %d ) Done' % pcount, flush=True)

        attempts = 0
        attempts_max = 5
        now = time.time()

        while attempts < attempts_max:
            for pid in self.procs:
                if (not self.procs[pid]['claimed']) and (
                    (now - self.procs[pid]['create_time']) > 50):
                    print(
                        "pid: %s-%s does not match any configured instance, sending it TERM"
                        % (pid, self.procs[pid]['cmdline'][0:5]))
                    signal_pid(pid, signal.SIGTERM)

            ttw = 1 << attempts
            print(
                'Waiting %d sec. to check if %d processes stopped (try: %d)' %
                (ttw, len(self.procs), attempts))
            time.sleep(ttw)
            # update to reflect killed processes.
            self._read_procs()
            self._find_missing_instances()
            self._clean_missing_proc_state()
            self._read_states()
            self._resolve()

            running_pids = 0
            for f in self.filtered_configurations:
                if f == 'audit': continue
                (c, cfg) = f.split(os.sep)
                # exclude foreground instances unless --dangerWillRobinson specified
                if (not self.options.dangerWillRobinson) and self._cfg_running_foreground(c, cfg):
                    fg_instances.add(f"{c}/{cfg}")
                    continue
                running_pids += len(self.states[c][cfg]['instance_pids'])

            if running_pids == 0:
                print('All stopped after try %d' % attempts)
                if len(fg_instances) > 0:
                    print(f"Foreground instances {fg_instances} are running and were not stopped.")
                    print("Use --dangerWillRobinson to force stop foreground instances with sr3 stop.")
                return 0
            attempts += 1

        print('doing SIGKILL this time')

        if ('audit' in self.filtered_configurations) and self.auditors > 0:
            for p in self.procs:
                if 'audit' in p['name']:
                    signal_pid(p, signal.SIGKILL)

        for f in self.filtered_configurations:
            if f == 'audit': continue
            (c, cfg) = f.split(os.sep)
            # exclude foreground instances unless --dangerWillRobinson specified
            if (not self.options.dangerWillRobinson) and self._cfg_running_foreground(c, cfg):
                fg_instances.add(f"{c}/{cfg}")
                continue
            if self.configs[c][cfg]['status'] in ['running', 'partial']:
                for i in self.states[c][cfg]['instance_pids']:
                    if self.states[c][cfg]['instance_pids'][i] in self.procs:
                        print("signal_pid( %s, SIGKILL )" %
                              self.states[c][cfg]['instance_pids'][i])
                        signal_pid(self.states[c][cfg]['instance_pids'][i],
                                signal.SIGKILL)
                        print('.', end='')

        for pid in self.procs:
            if not self.procs[pid]['claimed']:
                print(
                    "pid: %s-%s does not match any configured instance, would kill"
                    % (pid, self.procs[pid]['cmdline']))
                signal_pid(pid, signal.SIGKILL)

        print('Done')
        print('Waiting again...')
        time.sleep(10)
        self._read_procs()
        self._find_missing_instances()
        self._clean_missing_proc_state()
        self._read_states()
        self._resolve()

        for f in self.filtered_configurations:
            if f == 'audit': continue
            (c, cfg) = f.split(os.sep)
            # exclude foreground instances unless --dangerWillRobinson specified
            if (not self.options.dangerWillRobinson) and self._cfg_running_foreground(c, cfg):
                fg_instances.add(f"{c}/{cfg}")
                continue
            if self.configs[c][cfg]['status'] in ['running', 'partial']:
                for i in self.states[c][cfg]['instance_pids']:
                    print("failed to kill: %s/%s instance: %s, pid: %s )" %
                          (c, cfg, i, self.states[c][cfg]['instance_pids'][i]))

        if len(self.procs) == 0:
            print('All stopped after KILL')
            if len(fg_instances) > 0:
                print(f"Foreground instances {fg_instances} are running and were not stopped.")
                print("Use --dangerWillRobinson to force stop foreground instances with sr3 stop.")
            return 0
        else:
            print('not responding to SIGKILL:')
            for p in self.procs:
                # exclude foreground instances from printing unless --dangerWillRobinson specified
                if not ((not self.options.dangerWillRobinson) and self._pid_running_foreground(p)):
                    print('\t%s: %s' % (p, self.procs[p]['cmdline'][0:5]))
            return 1

    def dump(self):
        """ Printing all running processes, configs, states

        :return:
        """
        print('\n\nRunning Processes\n\n')
        for pid in self.procs:
            print('\t%s: name:%s cmdline:%s' %
                  (pid, self.procs[pid]['name'], self.procs[pid]['cmdline']))

        print('\n\nConfigs\n\n')
        for c in self.configs:
            print('\t%s ' % c)
            for cfg in self.configs[c]:
                print('\t\t%s : %s' % (cfg, self.configs[c][cfg]))

        print('\n\nStates\n\n')
        for c in self.states:
            print('\t%s ' % c)
            for cfg in self.states[c]:
                print('\t\t%s : %s' % (cfg, self.states[c][cfg]))

        print('\n\nBroker Bindings\n\n')
        for h in self.brokers:
            print("\nhost: %s" % h)
            print("\nexchanges: ")
            for x in self.brokers[h]['exchanges']:
                print("\t%s: %s" % (x, self.brokers[h]['exchanges'][x]))
            print("\nqueues: ")
            for q in self.brokers[h]['queues']:
                print("\t%s: %s" % (q, self.brokers[h]['queues'][q]))

        print('\n\nbroker summaries:\n\n')
        for h in self.brokers:
            if 'admin' in self.brokers[h]:
                admin_url = self.brokers[h]['admin'].url
                admin_urlstr = "%s://%s@%s" % ( admin_url.scheme, \
                   admin_url.username, admin_url.hostname)
                if admin_url.port:
                    admin_urlstr += ":" + str(admin_url.port)
                a = 'admin: %s' % admin_urlstr
            else:
                a = 'admin: none'
            print('\nbroker: %s  %s' % (h, a))
            print('\nexchanges: ', end='')
            for x in self.exchange_summary[h]:
                print("%s-%d, " % (x, self.exchange_summary[h][x]), end='')
            print('')
            print('\nqueues: ', end='')
            for q in self.brokers[h]['queues']:
                print("%s-%d, " % (q, len(self.brokers[h]['queues'][q])),
                      end='')
            print('')

        print('\n\nMissing instances\n\n')
        for instance in self.missing:
            (c, cfg, i) = instance
            print('\t\t%s : %s %d' % (c, cfg, i))

    def status(self):
        """ v3 Printing prettier statuses for each component/configs found
        """
        print("%-40s %-15s %5s %5s %5s %5s" %
              ("Component/Config", "State", "Run", "Miss", "Exp", "Retry"))
        print("%-40s %-15s %5s %5s %5s %5s" %
              ("----------------", "-----", "---", "----", "---", "-----"))
        configs_running = 0

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
                m = sum(map(lambda x: c in x and cfg in x, self.missing))
                if self.configs[c][cfg]['status'] != 'stopped':
                    expected = self.configs[c][cfg]['instances']
                    running = expected - m
                    if running > 0:
                        configs_running += 1
                else:
                    running = 0
                    expected = 0
                    m = 0

                retry = self.states[c][cfg]['retry_queue']

                cfg_status = self.configs[c][cfg]['status']
                if cfg_status == "running" and self._cfg_running_foreground(c, cfg):
                    cfg_status = "foreground"

                print("%-40s %-15s %5d %5d %5d %5d" %
                      (f, cfg_status, running, m, expected, retry))
        stray = 0
        for pid in self.procs:
            if not self.procs[pid]['claimed']:
                stray += 1
                bad = 1
                print("pid: %s-%s is not a configured instance" %
                      (pid, self.procs[pid]['cmdline']))

        print('      total running configs: %3d ( processes: %d missing: %d stray: %d )' % \
            (configs_running, len(self.procs), len(self.missing), stray))

        # FIXME: does not seem to find any stray exchange (with no bindings...) hmm...
        for h in self.brokers:
            for x in self.exchange_summary[h]:
                if self.exchange_summary[h][x] == 0:
                    print("exchange with no bindings: %s-%s " % (h, x), end='')

    def convert(self):
        cfg = self.v2_config[0]
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

        synonyms = sarracenia.config.Config.synonyms
        with open(v3_config_path, 'w') as v3_cfg:
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
                    elif k == 'destination':
                        if component == 'poll':
                            k = 'pollUrl'
                        else:
                            k = 'remoteUrl'

                    if k in convert_to_v3:
                        if len(line) > 1:
                            v = line[1].replace('.py', '', 1)
                            if v in convert_to_v3[k]:
                                line = convert_to_v3[k][v]
                                if 'continue' in line:
                                    logger.info("obsolete v2: " + v)
                                    continue
                        else:
                            line = convert_to_v3[k]
                            k = line[0]
                            v = line[1]
                    else:
                       line[0] = k

                    if k == 'continue':
                        continue
                    v3_cfg.write(' '.join(line)+'\n')
        logging.info('converting %s from v2 to v3 ' % cfg)


    def overview(self):
        """ v2 Printing statuses for each component/configs found

        :return:
        """
        bad = 0

        print('%-10s %-10s %-6s %3s %s' %
              ('Component', 'State', 'Good?', 'Qty',
               'Configurations-i(r/e)-r(Retry)'))
        print('%-10s %-10s %-6s %3s %s' %
              ('---------', '-----', '-----', '---',
               '------------------------------'))
        if self.auditors == 1:
            audst = "OK"
        elif self.auditors > 1:
            audst = "excess"
        else:
            audst = "absent"

        print("%-10s %-10s %-6s %3d" %
              ('audit', 'running', audst, self.auditors))
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
                if self.states[c][cfg]['retry_queue'] > 0:
                    sfx += '-r%d' % self.states[c][cfg]['retry_queue']
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
                    (len(self.configs[c]) - len(status['disabled']),  ', '.join(status['running'] ))) )
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
                print("pid: %s-%s is not a configured instance" %
                      (pid, self.procs[pid]['cmdline']))

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
        'convert', 'declare', 'devsnap', 'dump', 'edit', 'log', 'restart', 'sanity',
        'setup', 'show', 'status', 'overview', 'stop'
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
    #cfg.fill_missing_options()

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
        print('dumping: ', end='', flush=True)
        gs.dump()

    if action == 'edit':
        gs.edit()

    if action == 'enable':
        gs.enable()

    if action == 'foreground':
        gs.foreground()

    if action == 'list':
        gs.config_list()

    if action == 'log':
        gs.log()

    if action == 'convert':
        gs.convert()

    if action == 'remove':
        gs.remove()

    elif action == 'restart':
        print('restarting: ', end='', flush=True)
        gs.stop()
        gs.start()

    elif action == 'sanity':
        print('sanity: ', end='', flush=True)
        gs.sanity()

    if action == 'show':
        gs.config_show()

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
