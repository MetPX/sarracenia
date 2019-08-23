#!/usr/bin/env python3

#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Shared Services Canada, 2019
#

import os
import os.path
import psutil
import appdirs
import pathlib
import getpass
import time

def ageoffile(lf):
    """ return number of seconds since a file was modified as a floating point number of seconds.
        FIXME: mocked here for now. 
    """
    return(0);

class sr_GlobalState:

    """
       build a global state of all sarra processes running on the system for this user.
       makes three data structures:  procs, configs, and states, indexed by component
       and configuration name.

       self.(procs|configs|states)[ component ][ config ]  something...

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
                       #print(' state directory for %s/%s is: %s ' % (c,cfg,os.getcwd()) )
                       self.states[c][cfg]={}
                       self.states[c][cfg]['instance_pids']={}
                       self.states[c][cfg]['queue_name']=None
                       self.states[c][cfg]['instances_expected']=0
                       for f in os.listdir():
                            if f[-4:] == '.pid':
                                i = int(f[-6:-4])
                                #print('from f:%s, instance extraced as: %s' % (f,i) )
                                self.states[c][cfg]['instance_pids'][i]= int( pathlib.Path(f).read_text() )
                            elif f[-6:] == '.qname' :
                               self.states[c][cfg]['queue_name'] = pathlib.Path(f).read_text()
                            elif f[-6:] == '.state' :
                               self.states[c][cfg]['instances_expected'] = int ( pathlib.Path(f).read_text() )
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
              #print( 'lff= %s' % lff )

              if len(lff) > 3 :
                  c = lff[1]
                  #print( 'c=%s' % lff )
                  cfg = '_'.join(lff[2:-1])
                  #print( 'cfg=%s' % cfg )
                  suffix = lff[-1].split('.')

                  if suffix[1] == 'log':
                      inum = int(suffix[0])
                      #print( 'inum=%s' % inum )
                      age = ageoffile(lf)
                      if not cfg in self.logs[c]:
                         self.logs[c][cfg]={}
                      self.logs[c][cfg][inum]=age


    def _resolve(self):
        """
           compare configs, states, & logs and fill things in.
        """

        # comparing states and configs to find missing instances, and correct state.
        for c in self.components:
            if (c not in self.states) or (c not in self.configs):
                  continue

            for cfg in self.configs[c]:
               if not cfg in self.states[c]:
                  continue
               if len(self.states[c][cfg]['instance_pids']) > 0:
                  self.states[c][cfg]['missing_instances'] = []
                  expected_instances=0
                  for i in self.states[c][cfg]['instance_pids']:
                      if self.states[c][cfg]['instance_pids'][i] not in self.procs:
                         self.states[c][cfg]['missing_instances'].append(i) 
                      else:
                         expected_instances+=1
                         self.procs[ self.states[c][cfg]['instance_pids'][i]]['claimed'] = True
                  if expected_instances < self.states[c][cfg]['instances_expected']:
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
        self.components = [ 'cpost', 'cpump', 'poll', 'post', 'report', 'sarra', 'sender', 'shovel', 'subscribe', 'watch', 'winnow' ]

        self._read_procs()
        self._read_configs() 
        self._read_states() 
        self._read_logs() 
        self._resolve()


    def stop(self):

        for c in self.components:
            if (c not in self.configs):
               continue
            for cfg in self.configs[c]:
               if self.configs[c][cfg]['state'] in [ 'running', 'partial' ]:
                   for i in self.states[c][cfg]['instance_pids']:
                       print( "os.kill( %s, SIGTERM )" % self.states[c][cfg]['instance_pids'][i] )
                       #os.kill( self.states[c][cfg]['instance_pids'][i], signal.SIGTERM )

        for pid in self.procs:
            if not self.procs[pid]['claimed']:
                print( "pid: %s-%s does not match any configured instance, killing" %  (pid, self.procs[pid]['cmdline']) )
                #os.kill( pid, signal.SIGTERM )

        time.sleep(5)
        self._read_procs()
        self._read_states()
        self._resolve()
        
        for c in self.components:
            if (c not in self.configs):
               continue
            for cfg in self.configs[c]:
               if self.configs[c][cfg]['state'] in [ 'running', 'partial' ]:
                   for i in self.states[c][cfg]['instance_pids']:
                       print( "os.kill( %s, SIGKILL )" % self.states[c][cfg]['instance_pids'][i] )
                       #os.kill( self.states[c][cfg]['instance_pids'][i], signal.SIGKILL )

        for pid in self.procs:
            if not self.procs[pid]['claimed']:
                print( "pid: %s-%s does not match any configured instance, killing" %  (pid, self.procs[pid]['cmdline']) )
                #os.kill( pid, signal.SIGKILL )

        time.sleep(2)
        self._read_procs()
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

            


def main():

   actions_supported = [ 'status' ]

   gs = sr_GlobalState()   
   gs.dump()
   print('stopping...')
   gs.stop()

   print('status...')
   gs.status()



if __name__ == "__main__":
   main()

