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

import appdirs
import copy
import errno
import getpass
import logging
import os
import os.path
import pathlib
import platform
import psutil
import re
import shutil
import signal
import subprocess
import sys
import time

try:
    from sr_cfg2 import *

except:
    from sarra.sr_cfg2 import *



def ageoffile(lf):
    """ return number of seconds since a file was modified as a floating point number of seconds.
        FIXME: mocked here for now. 
    """
    return 0

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
        if c[0] != 'c':  # python components
            s = self.bin_dir + os.sep + 'sr_' + c
            if not os.path.exists(s):
                s += '.py'
            if not os.path.exists(s):
                print("don't know where the script files are for: %s" % c)
                return ''
            return s
        else:  # C components
            return 'sr_' + c

    def _launch_instance(self, component_path, c, cfg: str, i):
        """
          start up a instance process (always daemonish/background fire & forget type process.)
        """
        if cfg is None:
            lfn = self.user_cache_dir + os.sep + 'log' + os.sep + 'sr_' + c + "_%02d" % i + '.log'
        else:
            s = self.configs[c][cfg]['options'].statehost.lower()
            if (s == 'true') or (s == 'yes') or (s == 'on') or (s == '1'): 
                lfn = self.user_cache_dir + os.sep + self.hostname
            else:
                lfn = self.user_cache_dir

            lfn += os.sep + 'log' + os.sep + 'sr_' + c + '_' + cfg + "_%02d" % i + '.log'

        dir_not_there = not os.path.exists( os.path.dirname(lfn) )

        while dir_not_there:
            try:
                os.makedirs(os.path.dirname(lfn), exist_ok=True)
                dir_not_there=False
            except Exception as Ex:
                print( 'makedirs %s failed: %s' % ( os.path.dirname(lfn), ex ) )
                if ex.errno == errno.EEXIST: 
                     dir_not_there=False
       

        if c[0] != 'c':  # python components
            if cfg is None:
                cmd = [sys.executable, component_path, '--no', "%d" % i, 'start']
            else:
                cmd = [sys.executable, component_path, '--no', "%d" % i, 'start', cfg]
        else:  # C components
            cmd = [component_path, 'start', cfg]

        #print( "launching +%s+  re-directed to: %s" % ( cmd, lfn ), flush=True )

        try:
            with open(lfn, "a") as lf:
                subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=lf, stderr=subprocess.STDOUT)
        except Exception as ex:
            print( "failed to launch: %s >%s >2&1 (reason: %s) " % ( ' '.join(cmd), lfn, ex ) )

    def save_procs(self,File="procs.json"):
        """
           dump image of process table to a file, one process per line, JSON UTF-8 encoded.
        """
        print( 'save_procs to: %s' % File )
        with open(File,'a') as f:
            f.seek(0,0)
            f.truncate()
            f.write( getpass.getuser() + '\n' )
            for proc in psutil.process_iter( ):
                p = proc.as_dict( ['pid','cmdline','name', 'username', 'create_time' ] )
                pj = json.dumps(p,ensure_ascii=False)
                f.write(pj +'\n')
            
    def _filter_sr_proc(self,p):
        
        if self.me != p['username'] :
            return

        # process name 'python3' is not helpful, so overwrite...
        if 'python' in p['name']:
            if len(p['cmdline']) < 2:
                return
            n = os.path.basename(p['cmdline'][1])
            p['name'] = n

        if p['name'][0:2] != 'sr':
            return

        if ( sys.platform == 'win32') and ( p['name'][-4:].lower() == '.exe' ):
            # on windows, it seems to fork .exe and then there is a -script.py which is the right pid
            # .e.g sr_subscribe.exe -> sr_subscribe-script.py ... If you kill the -script, the .exe goes away.
            return

        #print( 'pname=%s, self.me=%s, pid=%s, cmdline=%s ' % \
        #      ( p['name'], p['username'], p['pid'], p['cmdline'] ) )
        if p['name'].startswith('sr_'): 
            self.procs[p['pid']] = p

            if p['name'][3:8] == 'audit':
                self.procs[p['pid']]['claimed'] = True
                self.auditors += 1
            else:
                self.procs[p['pid']]['claimed'] = (p['name'][-4:] == 'post') or \
                    any(item in ['declare', 'foreground', 'edit', 'sanity', 'setup', 'status'] for item in p['cmdline'])

    def read_proc_file(self,File="procs.json"):
        """
           read process table from a save file, for reproducible testing.
        """
        self.procs = {}
        self.auditors = 0
        print( 'getting procs from %s: ' % File, end='', flush=True )
        pcount = 0
        with open(File,'r') as f:
           self.me = f.readline().rstrip()
           for pj in f.readlines():
               p = json.loads(pj)
               self._filter_sr_proc(p)
               pcount += 1 
               if pcount % 100 == 0 : print( '.', end='', flush=True )
        print(' Done! Read %d procs' % ( pcount ) , flush=True )
      
    def _read_procs(self):
        # read process table from the system
        self.procs = {}
        self.me = getpass.getuser()
        if sys.platform == 'win32':
            self.me = os.environ['userdomain'] + '\\' + self.me
        self.auditors = 0
        for proc in psutil.process_iter( ):
            self._filter_sr_proc(proc.as_dict( ['pid','cmdline','name', 'username', 'create_time' ] ))

    def _read_configs(self):
        # read in configurations.
        self.configs = {}
        if not os.path.isdir(self.user_config_dir):
           return
        os.chdir(self.user_config_dir)
        self.default_cfg = sr_cfg2(self.logger,self.user_config_dir)
        if os.path.exists( "default.conf" ):
            self.default_cfg.parse_file("default.conf")
        if os.path.exists( "admin.conf" ):
            self.default_cfg.parse_file("admin.conf")

        self.admin_cfg = copy.deepcopy( self.default_cfg )
        if os.path.exists( "admin.conf" ):
            self.admin_cfg.parse_file("admin.conf")

        for c in self.components:
            if os.path.isdir(c):
                os.chdir(c)
                self.configs[c] = {}
                for cfg in os.listdir():

                    numi = 0
                    if cfg[-4:] == '.off':
                        cbase = cfg[0:-4]
                        state = 'disabled'
                    elif cfg[-5:] == '.conf':
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
                        cfgbody = copy.deepcopy( self.default_cfg )
                        cfgbody.override( { 'program_name' : c, 'config': cbase,  'directory':'${PWD}' } )
                        cfgbody.parse_file( cfg )
                        self.configs[c][cbase]['options'] = cfgbody
                        # ensure there is a known value of instances to run.
                        if c in ['post', 'cpost']:
                            if hasattr(cfgbody,'sleep') and cfgbody.sleep not in ['-', '0']:
                                numi = 1
                        elif hasattr(cfgbody, 'instances' ):
                            numi = int(cfgbody.instances)
                        else:
                            numi = 1

                    self.configs[c][cbase]['instances'] = numi

                os.chdir('..')

    def _cleanse_credentials(self, savename ):
        """
           copy credentials to a savename file, replacing actual passwords with a place holder.

        """
       
        sno=0

        with open( savename, 'w' ) as save_config_file: 
            with open( self.user_config_dir + os.sep + 'credentials.conf', 'r' ) as config_file:
                 for cfl in config_file.readlines():
                    lout = re.compile(':[^/][^/].*?@').sub(':secret%02d@' % sno, cfl, 1 )
                    save_config_file.write( lout )
                    sno += 1

    def save_configs(self,savename):
        """ DEVELOPER only... copy configuration to an alternate tree 
        """
        os.chdir(self.user_config_dir)
        other_config_dir = appdirs.user_config_dir(savename, self.appauthor)

        if not os.path.exists(other_config_dir):
            os.mkdir(other_config_dir)

        for f in [ 'default.conf', 'admin.conf' ]:
            to = other_config_dir + os.sep + f
            print( 'save_configs copying: %s %s' % ( f , to ) )
            shutil.copyfile( f, to )                

        self._cleanse_credentials(other_config_dir + os.sep + 'credentials.conf')

        for c in self.components:
            if os.path.isdir(c):
                os.chdir(c)
                other_c_dir= other_config_dir + os.sep + c
                if not os.path.exists(other_c_dir):
                    os.mkdir(other_c_dir)
                self.states[c] = {}
                for cfg in os.listdir():
                    to=other_c_dir + os.sep + cfg
                    print( 'save_configs copying: %s %s' % ( cfg , to ) )
                    shutil.copyfile( cfg, to )                
                os.chdir('..')

    def save_states_dir(self,savename,dir):
        """ DEVELOPER ONLY.. copy state files to an alternate tree.
            FIXME: statehost honoured kludgily.
        """

        if not os.path.isdir(dir):
           return
        os.chdir(dir)
        other_cache_dir = appdirs.user_cache_dir(savename, self.appauthor)
        if os.path.basename(dir) == self.hostdir:
           other_cache_dir += os.sep + self.hostdir

        if not os.path.exists(other_cache_dir):
            os.mkdir(other_cache_dir)
        for c in self.components:
            if os.path.isdir(c):
                os.chdir(c)
                other_c_dir= other_cache_dir + os.sep + c
                if not os.path.exists(other_c_dir):
                    os.mkdir(other_c_dir)
                self.states[c] = {}
                for cfg in os.listdir():
                    os.chdir(cfg)
                    other_cfg_dir= other_c_dir + os.sep + cfg
                    if not os.path.exists(other_cfg_dir):
                        os.mkdir(other_cfg_dir)
                    for f in os.listdir():
                        to=other_cfg_dir + os.sep + f
                        print( 'save_states copying: %s %s' % ( f , to ) )
                        shutil.copyfile( f, to )                
                    os.chdir('..')
                os.chdir('..')
        os.chdir('..')

    def save_states(self,savename):
        self.states = {}
        self.save_states_dir(savename,self.user_cache_dir)
        self.save_states_dir(savename,self.user_cache_dir + os.sep + self.hostdir )



    def _read_state_dir(self,dir):
        # read in state files
        if not os.path.isdir(dir):
           return

        os.chdir(dir)

        for c in self.components:
            if os.path.isdir(c):
                os.chdir(c)
                self.states[c] = {}
                for cfg in os.listdir():
                    if os.path.isdir(cfg):
                        os.chdir(cfg)
                        self.states[c][cfg] = {}
                        self.states[c][cfg]['instance_pids'] = {}
                        self.states[c][cfg]['queue_name'] = None
                        if c == 'audit' :
                            self.states[c][cfg]['instances_expected'] = 1
                        elif c in self.configs: 
                            if cfg not in self.configs[c] :
                                self.states[c][cfg]['status'] = 'removed'
                                self.states[c][cfg]['instances_expected'] = 0
                            elif self.configs[c][cfg]['instances'] == 0:
                                self.states[c][cfg]['instances_expected'] = 0
                        if c[0] == 'c':
                            self.states[c][cfg]['instances_expected'] = 1
                        else:
                            self.states[c][cfg]['instances_expected'] = 0
                        self.states[c][cfg]['has_state'] = False
                        self.states[c][cfg]['retry_queue'] = 0

                        for pathname in os.listdir():
                            p = pathlib.Path(pathname)
                            if p.suffix in ['.pid', '.qname', '.state']:
                                if sys.version_info[0] > 3 or sys.version_info[1] > 4:
                                    t = p.read_text().strip()
                                else:
                                    with p.open() as f:
                                        t = f.read().strip()
                                # print( 'read f:%s len: %d contents:%s' % ( f, len(t), t[0:10] ) )
                                if len(t) == 0:
                                    continue

                                # print( 'read f[-4:] = +%s+ ' % ( f[-4:] ) )
                                if pathname[-4:] == '.pid':
                                    i = int(pathname[-6:-4])
                                    if t.isdigit():
                                        # print( "%s/%s instance: %s, pid: %s" %
                                        #     ( c, cfg, i, t ) )
                                        self.states[c][cfg]['instance_pids'][i] = int(t)
                                elif pathname[-6:] == '.qname':
                                    self.states[c][cfg]['queue_name'] = t
                                elif pathname[-6:] == '.state' and (pathname[-12:-6] != '.retry'):
                                    if t.isdigit():
                                        self.states[c][cfg]['instances_expected'] = int(t)
                                elif pathname[-12:] == '.retry.state':
                                     buffer=2**16
                                     try:
                                         with open(p) as f:
                                             self.states[c][cfg]['retry_queue'] += sum(x.count('\n') for x in iter(partial(f.read,buffer), ''))
                                     except Exception as ex:
                                             #print( 'info reading statefile %p gone before it was read: %s' % (p, ex) )
                                             pass

                        os.chdir('..')
                os.chdir('..')

    def _read_states(self):
        self.states = {}
        self._read_state_dir(self.user_cache_dir)
        self._read_state_dir(self.user_cache_dir + os.sep + self.hostdir )
        


    def _find_missing_instances_dir(self,dir):
        """ find processes which are no longer running, based on pidfiles in state, and procs.
        """
        if not os.path.isdir(dir):
           return
        os.chdir(dir)
        missing = []
        for c in self.components:
            if os.path.isdir(c):
                os.chdir(c)
                for cfg in os.listdir():
                    if os.path.isdir(cfg):
                        os.chdir(cfg)
                        for filename in os.listdir():
                            if filename[-4:] == '.pid':
                                i = int(filename[-6:-4])
                                p = pathlib.Path(filename)
                                if sys.version_info[0] > 3 or sys.version_info[1] > 4:
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

                        os.chdir('..')
                os.chdir('..')

        self.missing.extend( missing )

    def _find_missing_instances(self):
        self.missing = []
        self._find_missing_instances_dir(self.user_cache_dir)
        self._find_missing_instances_dir(self.user_cache_dir + os.sep + self.hostdir )


    def _clean_missing_proc_state_dir(self,dir):
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
                                if sys.version_info[0] > 3 or sys.version_info[1] > 4:
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
        self._clean_missing_proc_state_dir(self.user_cache_dir + os.sep + self.hostdir )



    def _read_logs_dir(self,dir):

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
                lff = lf.split('_')
                if len(lff) > 3:
                    c = lff[1]
                    cfg = '_'.join(lff[2:-1])
                    
                    suffix = lff[-1].split('.')

                    if len(suffix) > 1:
                        if suffix[1] == 'log':
                            try:
                                inum = int(suffix[0])
                            except:
                                inum=0
                            age = ageoffile(lf)
                            if cfg not in self.logs[c]:
                                self.logs[c][cfg] = {}
                            self.logs[c][cfg][inum] = age

    def _read_logs(self):
        self._read_logs_dir(self.user_cache_dir)
        self._read_logs_dir(self.user_cache_dir + os.sep + self.hostdir )



    def _init_broker_host(self, bhost ):
        if '@' in bhost:
            host=bhost.split('@')[1]
        else:
            host=bhost

        if not host in self.brokers:
                 
            self.brokers[host] = {}
            self.brokers[host]['post_exchanges'] = {}
            self.brokers[host]['exchanges'] = {}
            self.brokers[host]['queues'] = {}
            if hasattr(self.admin_cfg,'admin') and host in self.admin_cfg.admin:
                self.brokers[host]['admin'] = self.admin_cfg.admin 

        return host


    def _resolve_brokers(self):
        """ make a map of dependencies

            on a given broker, 
                 exchanges exist, 
                      with publishers: [ 'c/cfg', 'c/cfg' ... ]
                      with queues: [ 'qname', 'qname', ... ]
                      for each queue: [ 'c/cfg', 'c/cfg', ... ]
        """
        self.brokers={}
        for c in self.components:
            if (c not in self.states) or (c not in self.configs):
                continue
            
            for cfg in self.configs[c]:

                if not 'options' in self.configs[c][cfg] :
                    continue

                o = self.configs[c][cfg]['options']
                name = c + os.sep + cfg
                
                if hasattr(o,'broker') and o.broker is not None:
                    host = self._init_broker_host( o.broker.netloc )

                    if hasattr(o,'exchange'):

                        if hasattr(o,'queue'):
                           q = o.queue
                        else:
                           try:
                              q = self.states[c][cfg]['queue_name']
                           except:
                              q = 'unknown'

                        if o.exchange in self.brokers[host]['exchanges']:
                            self.brokers[host]['exchanges'][o.exchange].append( q )
                        else:
                            self.brokers[host]['exchanges'][o.exchange] = [ q ]
                        if q in self.brokers[host]['queues']:
                            self.brokers[host]['queues'][q].append( name )
                        else:
                            self.brokers[host]['queues'][q] = [ name ]

                if hasattr(o,'post_broker') and o.post_broker is not None:
                    host = self._init_broker_host( o.post_broker.netloc )

                    if hasattr(o,'post_exchange'):
                        if o.post_exchange in self.brokers[host]['post_exchanges']:
                            self.brokers[host]['post_exchanges'][o.post_exchange].append( name )
                        else:
                            self.brokers[host]['post_exchanges'][o.post_exchange]= [ name ]
                                      
        self.exchange_summary= {}
        for h in self.brokers:
           self.exchange_summary[h] = {}
           allx=[]
           if 'exchanges' in self.brokers[h]:
               allx += self.brokers[h]['exchanges'].keys() 

           if 'post_exchanges' in self.brokers[h]:
               allx += self.brokers[h]['post_exchanges'].keys()

           for x in allx:
               a=0
               if x in self.brokers[h]['exchanges']:
                   a += len(self.brokers[h]['exchanges'][x])
               if x in self.brokers[h]['post_exchanges']:
                  a += len(self.brokers[h]['post_exchanges'][x])
               self.exchange_summary[h][x]=a
               
                           

    def _resolve(self):
        """
           compare configs, states, & logs and fill things in.

           things that could be identified: differences in state, running & configured instances.
        """

        self._resolve_brokers()

        # comparing states and configs to find missing instances, and correct state.
        for c in self.components:
            if (c not in self.states) or (c not in self.configs):
                continue

            for cfg in self.configs[c]:
                if cfg not in self.states[c]:
                    # print('missing state for sr_%s/%s' % (c,cfg) )
                    continue
                if (self.configs[c][cfg]['instances'] == 0):
                        self.states[c][cfg]['instances_expected'] = 0
                if len(self.states[c][cfg]['instance_pids']) > 0:
                    self.states[c][cfg]['missing_instances'] = []
                    observed_instances = 0
                    for i in self.states[c][cfg]['instance_pids']:
                        if self.states[c][cfg]['instance_pids'][i] not in self.procs:
                            self.states[c][cfg]['missing_instances'].append(i)
                        else:
                            observed_instances += 1
                            self.procs[self.states[c][cfg]['instance_pids'][i]]['claimed'] = True

                    if observed_instances < self.states[c][cfg]['instances_expected']:
                        # print( "%s/%s observed_instances: %s expected: %s" % \
                        #   ( c, cfg, observed_instances, self.states[c][cfg]['instances_expected'] ) )
                        self.configs[c][cfg]['status'] = 'partial'
                    elif observed_instances == 0:
                        self.configs[c][cfg]['status'] = 'stopped'
                    else:
                        self.configs[c][cfg]['status'] = 'running'

        # FIXME: missing check for too many instances.

    @property
    def appname(self):
        return self.__appname 

    @appname.setter
    def appname(self,n):
        self.__appname = n
        self.user_config_dir = appdirs.user_config_dir(self.appname, self.appauthor)
        self.user_cache_dir = appdirs.user_cache_dir(self.appname, self.appauthor)

            
        
    def __init__(self,logger):
        """
           side effect: changes current working directory FIXME?
        """

        self.logger = logger

        self.bin_dir = os.path.dirname(os.path.realpath(__file__))
        self.appauthor = 'science.gc.ca'
        self.appname = os.getenv( 'SR_DEV_APPNAME' )
        self.hostname = socket.getfqdn()
        self.hostdir = self.hostname.split('.')[0]


        if self.appname == None:
            self.appname = 'sarra'
        else:
            print( 'DEVELOPMENT using alternate application name: %s, bindir=%s' % (self.appname, self.bin_dir ))

        if not os.path.isdir( self.user_config_dir ):
            print( 'WARNING: No %s configuration found.' % self.appname )

        if not os.path.isdir( self.user_cache_dir ):
            print( 'WARNING: No %s configuration state or log files found.' % self.appname )

        self.components = ['audit', 'cpost', 'cpump', 'poll', 'post', 'report', 'sarra', 'sender', 'shovel',
                           'subscribe', 'watch', 'winnow']
        self.status_values = ['disabled', 'include', 'stopped', 'partial', 'running', 'unknown' ]

 
        self.bin_dir = os.path.dirname(os.path.realpath(__file__))

        #print('gathering global state: ', flush=True)

        pf=self.user_cache_dir + os.sep + "procs.json"
        if os.path.exists( pf ) :
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

    def _start_missing(self):
        for instance in self.missing:
            (c, cfg, i) = instance
            component_path = self._find_component_path(c)
            if component_path == '':
                continue
            self._launch_instance(component_path, c, cfg, i)

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
                print('.', end='')
                if c[0] != 'c':  # python components
                    cmd = [sys.executable, component_path, action, cfg]
                else:
                    cmd = [component_path, action, cfg]

                plist.append(subprocess.Popen( cmd,
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                ))
        print('Done')
        for p in plist:
            (outs, errs) = p.communicate()
            print(outs.decode('utf8'))

    def sanity(self):
        """ Run sanity by finding and starting missing instances

        :return:
        """
        self._find_missing_instances()
        print('missing: %s' % self.missing)
        print('starting them up...')
        self._start_missing()

        print('killing strays...')
        now=time.time()
        for pid in self.procs:
            if (not self.procs[pid]['claimed']) and ( (now-self.procs[pid]['create_time']) > 50 ):
                print("pid: %s-%s (name: %s) does not match any configured instance, sending it TERM" % (
                        pid, self.procs[pid]['cmdline'][0:5], self.procs[pid]['name']))
                os.kill(pid, signal.SIGTERM)


    def start(self):
        """ Starting all components

        :return:
        """

        pcount=0
        for c in self.components:
            if c not in self.configs:
                continue
            component_path = self._find_component_path(c)
            if component_path == '':
                continue
            for cfg in self.configs[c]:
                if self.configs[c][cfg]['status'] in ['stopped']:
                    numi = self.configs[c][cfg]['instances']
                    for i in range(1, numi + 1):
                        if pcount % 10 == 0 : print('.', end='', flush=True)
                        pcount += 1
                        self._launch_instance(component_path, c, cfg, i)

        c = 'audit'
        component_path = self._find_component_path(c)
        if self.auditors == 0:
            self._launch_instance(component_path, c, None, 1)

        print('( %d ) Done' % pcount )

    def stop(self):
        """
           stop all of this users sr_ processes. 
           return 0 on success, non-zero on failure.
        """
        self._clean_missing_proc_state()

        if len(self.procs) == 0:
            print('...already stopped')
            return

        print( 'sending SIGTERM ', end='', flush=True )
        pcount=0
        # kill sr_audit first, so it does not restart while others shutting down.
        # https://github.com/MetPX/sarracenia/issues/210
        if self.auditors > 0:
            for p in self.procs:
                if 'audit' in self.procs[p]['name']:
                    os.kill(p, signal.SIGTERM)
                    print('.', end='', flush=True)
                    pcount += 1

        for c in self.components:
            if c not in self.configs:
                continue
            for cfg in self.configs[c]:
                if self.configs[c][cfg]['status'] in ['running', 'partial']:
                    for i in self.states[c][cfg]['instance_pids']:
                        # print( "for %s/%s - %s os.kill( %s, SIGTERM )" % \
                        #    ( c, cfg, i, self.states[c][cfg]['instance_pids'][i] ) )
                        if self.states[c][cfg]['instance_pids'][i] in self.procs:
                            os.kill(self.states[c][cfg]['instance_pids'][i], signal.SIGTERM)
                            print('.', end='', flush=True)
                            pcount += 1

        print(' ( %d ) Done' % pcount, flush=True )

        attempts = 0
        attempts_max = 5
        while attempts < attempts_max:
            for pid in self.procs:
                if not self.procs[pid]['claimed']:
                    print("pid: %s-%s does not match any configured instance, sending it TERM" % (
                        pid, self.procs[pid]['cmdline'][0:5]))
                    os.kill(pid, signal.SIGTERM)

            ttw = 1 << attempts
            print('Waiting %d sec. to check if %d processes stopped (try: %d)' % (ttw, len(self.procs), attempts))
            time.sleep(ttw)
            # update to reflect killed processes.
            self._read_procs()
            self._find_missing_instances()
            self._clean_missing_proc_state()
            self._read_states()
            self._resolve()

            if len(self.procs) == 0:
                print('All stopped after try %d' % attempts)
                return 0
            attempts += 1

        print('doing SIGKILL this time')

        if self.auditors > 0:
            for p in self.procs:
                if 'audit' in p['name']:
                    os.kill(p, signal.SIGKILL)

        for c in self.components:
            if c not in self.configs:
                continue
            for cfg in self.configs[c]:
                if self.configs[c][cfg]['status'] in ['running', 'partial']:
                    for i in self.states[c][cfg]['instance_pids']:
                        if self.states[c][cfg]['instance_pids'][i] in self.procs:
                            print("os.kill( %s, SIGKILL )" % self.states[c][cfg]['instance_pids'][i])
                            os.kill(self.states[c][cfg]['instance_pids'][i], signal.SIGKILL)
                            print('.', end='')

        for pid in self.procs:
            if not self.procs[pid]['claimed']:
                print(
                    "pid: %s-%s does not match any configured instance, would kill" % (pid, self.procs[pid]['cmdline']))
                os.kill(pid, signal.SIGKILL)

        print('Done')
        print('Waiting again...')
        time.sleep(10)
        self._read_procs()
        self._find_missing_instances()
        self._clean_missing_proc_state()
        self._read_states()
        self._resolve()

        for c in self.components:
            if c not in self.configs:
                continue
            for cfg in self.configs[c]:
                if self.configs[c][cfg]['status'] in ['running', 'partial']:
                    for i in self.states[c][cfg]['instance_pids']:
                        print("failed to kill: %s/%s instance: %s, pid: %s )" % (
                            c, cfg, i, self.states[c][cfg]['instance_pids'][i]))
        if len(self.procs) == 0:
            print('All stopped after KILL')
            return 0
        else:
            print('not responding to SIGKILL:')
            for p in self.procs:
                print('\t%s: %s' % (p, self.procs[p]['cmdline'][0:5]))
            return 1

    def dump(self):
        """ Printing all running processes, configs, states

        :return:
        """
        print('\n\nRunning Processes\n\n')
        for pid in self.procs:
            print('\t%s: name:%s cmdline:%s' % (pid, self.procs[pid]['name'], self.procs[pid]['cmdline']))

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
            print( "\nhost: %s" % h )
            print( "\npost_exchanges: " )
            for x in self.brokers[h]['post_exchanges']:
                print( "\t%s: %s" % ( x, self.brokers[h]['post_exchanges'][x] ) )
            print( "\nexchanges: " )
            for x in self.brokers[h]['exchanges']:
                print( "\t%s: %s" % ( x, self.brokers[h]['exchanges'][x] ) )
            print( "\nqueues: " ) 
            for q in self.brokers[h]['queues']:
                print( "\t%s: %s" % ( q, self.brokers[h]['queues'][q] ) )
            
        print('\n\nbroker summaries:\n\n')
        for h in self.brokers:
            if 'admin' in self.brokers[h]:
                a='admin: %s' % self.brokers[h]['admin']
            else:
                a=''
            print('\nbroker: %s  %s' % (h,a) )
            print('\nexchanges: ', end='' )
            for x in self.exchange_summary[h]:
                print( "%s-%d, " % ( x, self.exchange_summary[h][x] ), end='' )
            print('') 
            print('\nqueues: ', end='' )
            for q in self.brokers[h]['queues']:
                print( "%s-%d, " % ( q, len(self.brokers[h]['queues'][q]) ), end='' )
            print('') 


        print('\n\nMissing instances\n\n')
        for instance in self.missing:
            (c, cfg, i) = instance
            print('\t\t%s : %s %d' % (c, cfg, i))

    def status(self):
        """ Printing statuses for each component/configs found

        :return:
        """
        bad = 0

        print('%-10s %-10s %-6s %3s %s' % ( 'Component', 'State', 'Good?', 'Qty', 'Configurations-i(r/e)-r(Retry)' ) )
        print('%-10s %-10s %-6s %3s %s' % ( '---------', '-----', '-----', '---', '------------------------------' ) )
        if self.auditors == 1:
            audst = "OK"
        elif self.auditors > 1:
            audst = "excess"
        else:
            audst = "absent"

        print("%-10s %-10s %-6s %3d" % ('audit', 'running', audst, self.auditors ))
        configs_running = 0
        missing_state_files=0
        for c in self.configs:

            status = {}
            for sv in self.status_values:
                status[sv] = []

            for cfg in self.configs[c]:

                sfx=''
                if self.configs[c][cfg]['status'] == 'include' :
                    continue

                if not ( c in self.states and cfg in self.states[c] ):
                    continue

                if self.configs[c][cfg]['status'] != 'stopped' :
                    m = sum( map( lambda x: c in x and cfg in x, self.missing ) ) #perhaps expensive, but I am lazy FIXME
                    sfx += '-i%d/%d' % ( \
                        len(self.states[c][cfg]['instance_pids']) - m, \
                        self.states[c][cfg]['instances_expected'])
                    if len(self.states[c][cfg]['instance_pids']) < self.states[c][cfg]['instances_expected'] :
                        missing_state_files += (  self.states[c][cfg]['instances_expected'] - len(self.states[c][cfg]['instance_pids']) )
                if self.states[c][cfg]['retry_queue'] > 0 :
                    sfx += '-r%d' % self.states[c][cfg]['retry_queue']
                status[self.configs[c][cfg]['status']].append( cfg+sfx )

                #'-i(%d/%d)-r(%d)' % (len(self.states[c][cfg]['instance_pids']), self.states[c][cfg]['instances_expected'], self.states[c][cfg]['retry_queue'] ) )


            if (len(status['partial']) + len(status['running'])) < 1:
                print('%-10s %-10s %-6s %3d %s' % (c, 'stopped', 'OK', len(status['stopped']), ', '.join(status['stopped'])) )
            elif len(status['running']) == len(self.configs[c]):
                print('%-10s %-10s %-6s %3d %s' % (c, 'running', 'OK', len(self.configs[c]), ', '.join(status['running'] )) )
            elif len(status['running']) == (len(self.configs[c]) - len(status['disabled'])):
                print('%-10s %-10s %-6s %-3d %s' % (c, 'most', 'OKd', \
                    (len(self.configs[c]) - len(status['disabled']),  ', '.join(status['running'] ))) )
            else:
                print('%-10s %-10s %-6s %3d' % (c, 'mixed', 'mult', len(self.configs[c])))
                bad = 1
                for sv in self.status_values:
                    if len(status[sv]) > 0:
                        print('    %3d %s: %s ' % (len(status[sv]), sv, ', '.join(status[sv])))

            configs_running += len(status['running'])

        stray=0
        for pid in self.procs:
            if not self.procs[pid]['claimed']:
                stray += 1
                bad = 1
                print("pid: %s-%s is not a configured instance" % (pid, self.procs[pid]['cmdline']))

        print('      total running configs: %3d ( processes: %d missing: %d stray: %d )' % \
            (configs_running, len(self.procs), len(self.missing)+missing_state_files, stray))

        # FIXME: does not seem to find any stray exchange (with no bindings...) hmm...
        for h in self.brokers:
            for x in self.exchange_summary[h]:
                if self.exchange_summary[h][x] == 0:
                    print( "exchange with no bindings: %s-%s " % ( h, x ), end='' )
        
        return bad

def main():
    """ Main thread for sr dealing with parsing and action switch

    :return:
    """
    logger = logging.getLogger()
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG)
    logger.setLevel( logging.ERROR )



    actions = ['declare', 'devsnap', 'dump', 'restart', 'sanity', 'setup', 'status', 'stop']

    if len(sys.argv) < 2:
        print('USAGE: %s (%s)' % (sys.argv[0], '|'.join(actions)))
        return
    else:
        action = sys.argv[1]


    gs = sr_GlobalState(logger)
    # testing proc file i/o
    #gs.read_proc_file()
    #return

    if action in ['declare', 'setup']:
        print('%s: ' % action, end='', flush=True)
        gs.maint(action)

    if action == 'dump':
        print('dumping: ', end='', flush=True)
        gs.dump()

    elif action == 'restart':
        print('restarting: ', end='', flush=True)
        gs.stop()
        gs.start()

    elif action == 'sanity':
        print('sanity: ', end='', flush=True)
        gs.sanity()

    elif action == 'start':
        print('starting:', end='', flush=True)
        gs.start()

    elif action == 'status':
        print('status: ')
        sys.exit(gs.status())

    elif action == 'devsnap':
        if len(sys.argv) < 3:
           print( 'devsnap requires alternate app name as argument' )
           sys.exit(1)

        gs.save_states(sys.argv[2])
        gs.save_configs(sys.argv[2])
        gs.appname = sys.argv[2]
        gs.save_procs( gs.user_cache_dir + os.sep + "procs.json" )

    elif action == 'stop':
        print('Stopping: ', end='', flush=True)
        gs.stop()


if __name__ == "__main__":
    main()
