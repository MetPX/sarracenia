#!/usr/bin/env python3

#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Shared Services Canada, 2019
#

"""
   parallel version of sr. Generates a global state, then performs an action.
   previous version would, recursion style, launch individual components.

"""
import os
import os.path
import psutil
import appdirs
import pathlib
import getpass
import time
import signal
import sys

def ageoffile(lf):
    """ return number of seconds since a file was modified as a floating point number of seconds.
        FIXME: mocked here for now. 
    """
    return(0);

def _parse_cfg(cfg):
    """ return configuration file as a dictionary.
        FIXME: this is extremely rudimentary, doesn't do variable substitution, etc...
               only want to use this to get 'instances' for now which should be ok 99% of the time.
    """
    cfgbody={}
    for l in open(cfg,"r").readlines():
       line = l.split()
       if (len(line) < 1 ) or (  line[0] == '#' ):
          continue
       cfgbody[line[0]] = line[1:] 
    return cfgbody


class sr_GlobalState:

    """
       build a global state of all sarra processes running on the system for this user.
       makes three data structures:  procs, configs, and states, indexed by component
       and configuration name.

       self.(procs|configs|states)[ component ][ config ]  something...

       naming: routines that start with *read* don't modify anything on disk.
               routines that start with clean do...
          
    """
    def _read_procs(self):
        # read process table.
        self.procs={}
        me=getpass.getuser()
        for proc in psutil.process_iter():
            p = proc.as_dict()
            if p['name'].startswith( 'sr_' ) and ( me == p['username'] ):
                self.procs[proc.pid] = p
                self.procs[proc.pid]['claimed'] = False
             

    def _read_configs(self):
        # read in configurations.
        self.configs={}
        os.chdir(self.user_config_dir)
       
        for c in self.components:
            if os.path.isdir(c):
               os.chdir(c)
               self.configs[c] = {}
               for cfg in os.listdir() :
                   
                   if cfg[-4:] == '.stopped'  :
                       cbase = cfg[0:-4]
                       state = 'disabled'
                   elif cfg[-5:] == '.conf':
                       cbase = cfg[0:-5]
                       state = 'stopped'
                   else:
                       cbase = cfg
                       state = 'unknown'

                   if state != 'unknown':
                       self.configs[c][cbase] = {}
                       self.configs[c][cbase]['state'] = state 
                       cfgbody = _parse_cfg( cfg )
                       if 'instances' in cfgbody:                        
                           self.configs[c][cbase]['instances'] = cfgbody['instances'] 

               os.chdir('..')
   
    
    def _read_states(self):
        # read in state files
        os.chdir(self.user_cache_dir)
        self.states  = {}

        for c in self.components:
            if os.path.isdir(c):
                os.chdir(c)
                self.states[c] = {}
                for cfg in os.listdir():
                   if os.path.isdir(cfg):
                       os.chdir(cfg)
                       self.states[c][cfg]={}
                       self.states[c][cfg]['instance_pids']={}
                       self.states[c][cfg]['queue_name']=None
                       self.states[c][cfg]['instances_expected']=0
                       self.states[c][cfg]['has_state']=False

                       #print( 'state %s/%s' % ( c, cfg ) )
                       for f in os.listdir():
                            t = pathlib.Path(f).read_text().strip()
                           
                            #print( 'read f:%s len: %d contents:%s' % ( f, len(t), t[0:10] ) )
                            if len(t) == 0:
                                continue

                            #print( 'read f[-4:] = +%s+ ' % ( f[-4:] ) )
                            if f[-4:] == '.pid':
                                i = int(f[-6:-4])
                                if t.isdigit():
                                    #print( "%s/%s instance: %s, pid: %s" % 
                                    #     ( c, cfg, i, t ) )
                                    self.states[c][cfg]['instance_pids'][i]= int( t )
                            elif f[-6:] == '.qname' :
                                self.states[c][cfg]['queue_name'] = t
                            elif f[-6:] == '.state' and ( f[-12:-6] != '.retry' ):
                                if t.isdigit():
                                    self.states[c][cfg]['instances_expected'] = int ( t )
                       os.chdir('..')
                os.chdir('..')

    def _clean_missing_proc_state(self): 
        """ remove state pid files for process which are no longer running
        """
        os.chdir(self.user_cache_dir)
        for c in self.components:
            if os.path.isdir(c):
                os.chdir(c)
                for cfg in os.listdir():
                   if os.path.isdir(cfg):
                       os.chdir(cfg)
                       for f in os.listdir():
                            if f[-4:] == '.pid':
                               t = pathlib.Path(f).read_text()
                               if t.isdigit():
                                   pid = int( t )
                                   if pid not in self.procs:
                                       os.unlink(f)
                               else:
                                   os.unlink(f)

                       os.chdir('..')
                os.chdir('..')
               

    def _read_logs(self):

        os.chdir(self.user_cache_dir)
        if os.path.isdir('log'):
           self.logs={}
           for c in self.components:
              self.logs[c]={}
              
           os.chdir('log')

           for lf in os.listdir():
              lff = lf.split('_')

              if len(lff) > 3 :
                  c = lff[1]
                  cfg = '_'.join(lff[2:-1])
                  suffix = lff[-1].split('.')

                  if suffix[1] == 'log':
                      inum = int(suffix[0])
                      age = ageoffile(lf)
                      if not cfg in self.logs[c]:
                         self.logs[c][cfg]={}
                      self.logs[c][cfg][inum]=age


    def _resolve(self):
        """
           compare configs, states, & logs and fill things in.

           things that could be identified: differences in state, running & configured instances.
        """

        # comparing states and configs to find missing instances, and correct state.
        for c in self.components:
            if (c not in self.states) or (c not in self.configs):
                  continue

            for cfg in self.configs[c]:
               if not cfg in self.states[c]:
                  print('missing state for sr_%s/%s' % (c,cfg) )
                  continue
               if len(self.states[c][cfg]['instance_pids']) > 0:
                  self.states[c][cfg]['missing_instances'] = []
                  observed_instances=0
                  for i in self.states[c][cfg]['instance_pids']:
                      if self.states[c][cfg]['instance_pids'][i] not in self.procs:
                         self.states[c][cfg]['missing_instances'].append(i) 
                      else:
                         observed_instances+=1
                         self.procs[ self.states[c][cfg]['instance_pids'][i] ]['claimed'] = True

                  if observed_instances < self.states[c][cfg]['instances_expected']:
                      print( "%s/%s observed_instances: %s expected: %s" % \
                         ( c, cfg, observed_instances, self.states[c][cfg]['instances_expected'] ) )
                      self.configs[c][cfg]['state'] = 'partial'
                  else:
                      self.configs[c][cfg]['state'] = 'running'

         

    def __init__(self):
        """
           side effect: changes current working directory FIXME?
        """

        self.appname   = 'sarra'
        self.appauthor = 'science.gc.ca'
        self.user_config_dir = appdirs.user_config_dir( self.appname, self.appauthor )
        self.user_cache_dir  = appdirs.user_cache_dir (self.appname,self.appauthor)
        self.components = [ 'audit', 'cpost', 'cpump', 'poll', 'post', 'report', 'sarra', 'sender', 'shovel', 'subscribe', 'watch', 'winnow' ]

        self._read_procs()
        self._read_configs() 
        self._read_states() 
        self._read_logs() 
        self._resolve()

    def stop(self):

        self._clean_missing_proc_state()

        for c in self.components:
            if (c not in self.configs):
               continue
            for cfg in self.configs[c]:
               if self.configs[c][cfg]['state'] in [ 'running', 'partial' ]:
                  for i in self.states[c][cfg]['instance_pids']:
                      #print( "for %s/%s - %s os.kill( %s, SIGTERM )" % \
                      #    ( c, cfg, i, self.states[c][cfg]['instance_pids'][i] ) )
                      if self.states[c][cfg]['instance_pids'][i] in self.procs:
                          os.kill( self.states[c][cfg]['instance_pids'][i], signal.SIGTERM )

        for pid in self.procs:
            if not self.procs[pid]['claimed']:
                print( "pid: %s-%s does not match any configured instance, sending TERM" %  (pid, self.procs[pid]['cmdline']) )
                os.kill( pid, signal.SIGTERM )
                
        print( 'Waiting to check if they stopped' )
        time.sleep(5)
        # update to reflect killed processes.
        self._read_procs()
        self._clean_missing_proc_state()
        self._read_states()
        self._resolve()
        
        for c in self.components:
            if (c not in self.configs):
               continue
            for cfg in self.configs[c]:
               if self.configs[c][cfg]['state'] in [ 'running', 'partial' ]:
                   for i in self.states[c][cfg]['instance_pids']:
                       if self.states[c][cfg]['instance_pids'][i] in self.procs:
                           print( "os.kill( %s, SIGKILL )" % self.states[c][cfg]['instance_pids'][i] )
                           os.kill( self.states[c][cfg]['instance_pids'][i], signal.SIGKILL )

        for pid in self.procs:
            if not self.procs[pid]['claimed']:
                print( "pid: %s-%s does not match any configured instance, would kill" %  (pid, self.procs[pid]['cmdline']) )
                os.kill( pid, signal.SIGKILL )

        time.sleep(2)
        self._read_procs()
        self._clean_missing_proc_state()
        self._read_states()
        self._resolve()

        for c in self.components:
            if (c not in self.configs):
               continue
            for cfg in self.configs[c]:
               if self.configs[c][cfg]['state'] in [ 'running', 'partial' ]:
                   for i in self.states[c][cfg]['instance_pids']:
                       print( "failed to kill: %s/%s instance: %s, pid: %s )" % (c, cfg, i, self.states[c][cfg]['instance_pids'][i] ) )



    def dump(self):

        print( '\n\nRunning Processes\n\n' )
        for pid in self.procs:
            print( '\t%s: %s' % (pid, self.procs[pid]['cmdline']) )

        print( '\n\nConfigs\n\n' )
        for c in self.configs:
           print( '\t%s ' %c )
           for cfg in self.configs[c]:
               print( '\t\t%s : %s' % (cfg, self.configs[c][cfg] ) )

        print( '\n\nStates\n\n' )
        for c in self.states:
           print( '\t%s ' %c )
           for cfg in self.states[c]:
               print( '\t\t%s : %s' % (cfg, self.states[c][cfg] ) )


    def status(self):

        for c in self.configs:
            status_values = [ 'stopped', 'partial', 'running' ]
            status={}
            for sv in status_values:
                status[ sv ] =[]

            for cfg in self.configs[c]:
                status[ self.configs[c][cfg]['state'] ].append( cfg )
                   
            if (len(status['partial'])+len(status['running'])) < 1:
                   print( 'sr_%s: all stopped' % c ) 
            elif ( len(status['running']) == len(self.configs[c]) ):
                   print( 'sr_%s: all running' % c ) 
            else:
                print( 'sr_%s: mixed status' % c )
                for sv in status_values:
                    if len(status[sv]) > 0:
                       print( '%10s: %s ' % ( sv, ', '.join(status[ sv ]) ) )

        for pid in self.procs:
            if not self.procs[pid]['claimed']:
                print( "pid: %s-%s is not a configured instance" %  (pid, self.procs[pid]['cmdline']) )
            


def main():

   actions_supported = [ 'status' ]

   gs = sr_GlobalState()   

   if len(sys.argv) < 2:
       action='status'
   else:
       action=sys.argv[1]


   if action == 'status' :
       print('status...')
       gs.status()

   elif action == 'stop' :
      print('stopping...')
      gs.stop()

   elif action == 'dump' :
      print('dumping...')
      gs.dump()



if __name__ == "__main__":
   main()

