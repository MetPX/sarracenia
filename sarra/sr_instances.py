#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SarraDocumentation
#
# sr_instances.py : python3 utility tools to manage N instances of a program
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Jan  6 08:33:10 EST 2016
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, 
#  but WITHOUT ANY WARRANTY; without even the implied warranty of 
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#
#

import logging,os,psutil,signal,subprocess,sys
from sys import platform as _platform

try :
         from sr_config      import *
except :
         from sarra.sr_config import *

class sr_instances(sr_config):

    def __init__(self,config=None,args=None,action=None):
        signal.signal(signal.SIGTERM, self.stop_signal)
        signal.signal(signal.SIGINT, self.stop_signal)
        if _platform != 'win32':
            signal.signal(signal.SIGHUP, self.reload_signal)

        sr_config.__init__(self,config,args,action)
        self.cwd = os.getcwd()
        self.configure()
        self.build_parent()

    def build_parent(self):
        self.logger.debug("sr_instances build_parent")

        self.basic_name = self.program_name
        if self.config_name : self.basic_name += '_' + self.config_name 
        self.statefile  = self.user_cache_dir + os.sep + self.basic_name + '.state'

        self.last_nbr_instances = self.file_get_int(self.statefile)
        if self.last_nbr_instances == None : self.last_nbr_instances = 0

    def build_instance(self,i):
        self.logger.debug( "sr_instances build_instance %d" % i)
        self.instance      = i
        self.instance_name = self.basic_name + '_%.4d' % i

        self.instance_str  = self.program_name
        if self.config_name: self.instance_str += ' ' + self.config_name + ' %.4d' % i

        # setting of context files

        self.pidfile       = self.user_cache_dir + os.sep + self.instance_name + '.pid'
        self.logpath       = self.user_log_dir   + os.sep + self.instance_name + '.log'
        self.save_path     = self.user_cache_dir + os.sep + self.instance_name + '.save'

        self.isrunning     = False
        self.pid           = self.file_get_int(self.pidfile)

    def exec_action(self,action,old=False):

        if old :
           self.logger.warning("Should invoke : %s [args] action config" % sys.argv[0])

        # no config file given

        if self.config_name == None:
           if   action == 'list'     : self.exec_action_on_all(action)
           elif action == 'restart'  : self.exec_action_on_all(action)
           elif action == 'reload'   : self.exec_action_on_all(action)
           elif action == 'start'    : self.exec_action_on_all(action)
           elif action == 'stop'     : self.exec_action_on_all(action)
           elif action == 'status'   : self.exec_action_on_all(action)
           else :
                self.logger.warning("Should invoke : %s [args] action config" % sys.argv[0])
           os._exit(0)

        # a config file that does not exists

        if not os.path.isfile(self.user_config) :
           if   action == 'edit'    : self.exec_action_on_config(action)
           else :
                self.logger.warning("Should invoke : %s [args] action config" % sys.argv[0])
           os._exit(0)

        # a config file exists

        if   action == 'foreground' : self.foreground_parent()
        elif action == 'reload'     : self.reload_parent()
        elif action == 'restart'    : self.restart_parent()
        elif action == 'start'      : self.start_parent()
        elif action == 'stop'       : self.stop_parent()
        elif action == 'status'     : self.status_parent()

        elif action == 'cleanup'    : self.cleanup()
        elif action == 'declare'    : self.declare()
        elif action == 'setup'      : self.setup()

        elif action == 'add'        : self.exec_action_on_config(action)
        elif action == 'disable'    : self.exec_action_on_config(action)
        elif action == 'edit'       : self.exec_action_on_config(action)
        elif action == 'enable'     : self.exec_action_on_config(action)
        elif action == 'list'       : self.exec_action_on_config(action)
        elif action == 'log'        : self.exec_action_on_config(action)
        elif action == 'remove'     : self.exec_action_on_config(action)

        else :
           self.logger.error("action unknown %s" % action)
           self.help()
           os._exit(1)

    def exec_action_on_all(self,action):

        configdir = self.user_config_dir + os.sep + self.program_dir

        if not os.path.isdir(configdir)      : return

        if action == 'list':
           print("admin.conf")
           print("credentials.conf")
           print("default.conf\n")

        for confname in os.listdir(configdir):
            if action == 'list'     : print("%s" % confname)
            else:
                  try   :
                          if confname[-5:] == '.conf' : subprocess.check_call([self.program_name, action, confname] )
                  except: pass



    # MG FIXME first shot
    # a lot of things should be verified
    # instead we log when something wrong
    #
    # ex.: add     : config does not end with .conf
    #      disable : program is running
    #      edit    : EDITOR variable exists
    #      enable  : .off file exists
    #      list    : add include files at the end
    #      log     : probably need to configure -n for tail
    #      remove  : program is running

    def exec_action_on_config(self,action):
        self.logger.debug("exec_action_on_config %s" % action)
        
        usr_dir = self.config_dir
        usr_fil = self.user_config

        ext     = '.conf'
        if self.user_config[-4:] == '.inc' : ext = ''

        def_dir = self.user_config_dir + os.sep + self.program_dir
        def_fil = def_dir + os.sep + self.config_name + ext

        if   action == 'add'        :
             try   : os.rename(usr_fil,def_fil)
             except: self.logger.error("cound not add %s to %s" % (self.config_name + ext,def_dir))

        elif action == 'disable'    :
             src   = def_fil.replace('.off','')
             dst   = src + '.off'
             try   : os.rename(src,dst)
             except: self.logger.error("cound not disable %s" % src )

        elif action == 'edit'       :
             if self.config_name in ['admin','default','credentials'] :
                def_fil = def_dir + os.sep + '..' + os.sep + self.config_name + ext
             try   : subprocess.check_call([ os.environ.get('EDITOR'), def_fil] )
             except: self.logger.error("problem editor %s file %s" % (os.environ.get('EDITOR'), def_fil))

        elif action == 'enable'     :
             dst   = def_fil.replace('.off','')
             src   = dst + '.off'
             try   : os.rename(src,dst)
             except: self.logger.error("cound not enable %s " % src )

        elif action == 'list'       : 
             try   : subprocess.check_call([ 'cat', usr_fil ] )
             except: self.logger.error("could not cat %s" % usr_fil )

        elif action == 'log' and ext == '.conf' :


             if self.nbr_instances == 1 :
                self.build_instance(1)
                print("\ntail -f %s\n" % self.logpath)
                try   : subprocess.check_call([ 'tail', '-f', self.logpath] )
                except: self.logger.info("stop (or error?)")
                return

             if self.no > 0 :
                self.build_instance(self.no)
                print("\ntail -f %s\n" % self.logpath)
                try   : subprocess.check_call([ 'tail', '-f', self.logpath] )
                except: self.logger.info("stop (or error?)")
                return

             no=1
             while no <= self.nbr_instances :
                   self.build_instance(no)
                   print("\ntail -f %s\n" % self.logpath)
                   if not os.path.isfile(self.logpath) : continue
                   try   : subprocess.check_call( [ 'tail', '-n10', self.logpath] )
                   except: self.logger.error("could not tail -n 10 %s" % self.logpath)
                   no = no + 1

        elif action == 'remove'     : 
             try   : os.unlink(def_fil)
             except: self.logger.error("could not remove %s" % self.logpath)

    
    def file_get_int(self,path):
        i = None
        try :
                 f = open(path,'r')
                 data = f.read()
                 f.close()
        except : return i

        try :    i = int(data)
        except : return i

        return i

    def file_set_int(self,path,i):
        try    : os.unlink(path)
        except : pass
     
        try    :
                 f = open(path,'w')
                 f.write("%d"%i)
                 f.close()
        except : pass

    def foreground_parent(self):
        self.logger.debug("sr_instances foreground_parent")
        self.nbr_instances = 0
        self.save_path     = self.user_cache_dir + os.sep + self.basic_name + '_0000.save'
        self.logpath       = None
        self.setlog()
        self.start()

    def reload_instance(self):
        if self.pid == None :
           self.logger.warning("%s was not running" % self.instance_str)
           self.start_instance()
           return

        try :
                 os.kill(self.pid, signal.SIGHUP)
                 self.logger.info("%s reload" % self.instance_str)
        except :
                 self.logger.warning("%s no reload ... strange state; restarting" % self.instance_str)
                 self.restart_instance()
    
    def reload_parent(self):

        # instance 0 is the parent... child starts at 1

        i=1
        while i <= self.nbr_instances :
              self.build_instance(i)
              self.reload_instance()
              i = i + 1

        # the number of instances has decreased... stop excedent
        while i <= self.last_nbr_instances:
              self.build_instance(i)
              self.stop_instance()
              i = i + 1

        # write nbr_instances
        self.file_set_int(self.statefile,self.nbr_instances)
    
    def reload_signal(self,sig,stack):
        self.logger.info("signal reload")
        if hasattr(self,'reload') :
           self.reload()

    def restart_instance(self):
        self.stop_instance()
        time.sleep(0.01)
        self.start_instance()

    def restart_parent(self):

        # instance 0 is the parent... child starts at 1

        i=1
        while i <= self.nbr_instances :
              self.build_instance(i)
              self.restart_instance()
              i = i + 1

        # the number of instances has decreased... stop excedent
        while i <= self.last_nbr_instances:
              self.build_instance(i)
              self.stop_instance()
              i = i + 1

        # write nbr_instances
        self.file_set_int(self.statefile,self.nbr_instances)

    def start_instance(self):

        if self.pid != None :
           try    : 
                    p = psutil.Process(self.pid)
                    self.logger.info("%s already started" % self.instance_str)
                    return
           except : 
                    self.logger.info("%s strange state... " % self.instance_str)
                    self.stop_instance()

        cmd = []
        cmd.append(sys.argv[0])
        cmd.append("--no")
        cmd.append("%d" % self.instance)
        if self.user_args   != None : cmd.extend(self.user_args)
        cmd.append("start")
        if self.user_config != None : cmd.append(self.user_config)
     
        self.logger.info("%s starting" % self.instance_str)
        self.logger.debug(" cmd = %s" % cmd)
        if self.debug :
           pid = subprocess.Popen(cmd)
        else :
           pid = subprocess.Popen(cmd,shell=False,\
                 stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

    def start_parent(self):
        self.logger.debug(" pid %d instances %d no %d \n" % (os.getpid(),self.nbr_instances,self.no))

        # as parent
        if   self.no == -1 :

             # instance 0 is the parent... child starts at 1

             i=1
             while i <= self.nbr_instances :
                   self.build_instance(i)
                   self.start_instance()
                   i = i + 1

             # the number of instances has decreased... stop excedent
             while i <= self.last_nbr_instances:
                   self.build_instance(i)
                   self.stop_instance()
                   i = i+1

             # write nbr_instances
             self.file_set_int(self.statefile,self.nbr_instances)

        # as instance
        else:
             self.logger.debug("start instance %d \n" % self.no)
             self.build_instance(self.no)
             self.pid = os.getpid()
             self.file_set_int(self.pidfile,self.pid)
             self.setlog()
             self.start()
        sys.exit(0)

    def status_instance(self):
        if self.pid == None :
           self.logger.info("%s is stopped" % self.instance_str)
           return

        try    : 
                 p = psutil.Process(self.pid)
                 status = p.status().replace('sleeping','running')
                 self.logger.info("%s is %s" % (self.instance_str,status))
                 return
        except : pass

        self.logger.info("%s no status ... strange state" % self.instance_str)

    def status_parent(self):

        # instance 0 is the parent... child starts at 1

        i=1
        while i <= self.nbr_instances :
              self.build_instance(i)
              self.status_instance()
              i = i + 1

        # the number of instances has decreased... stop excedent
        while i <= self.last_nbr_instances:
              self.build_instance(i)
              self.stop_instance()
              i = i+1

        # write nbr_instances
        self.file_set_int(self.statefile,self.nbr_instances)


    def stop_instance(self):
        if self.pid == None :
           self.logger.info("%s already stopped" % self.instance_str)
           return

        try    : 
                 self.logger.info("%s stopping" % self.instance_str)
                 os.kill(self.pid, signal.SIGTERM)
                 time.sleep(0.01)
                 os.kill(self.pid, signal.SIGKILL)

        except : pass
        try    : os.unlink(self.pidfile)
        except : pass

        self.pid = None

    def stop_parent(self):

        # instance 0 is the parent... child starts at 1

        i=1
        n = self.nbr_instances
        if n < self.last_nbr_instances :
           n = self.last_nbr_instances

        while i <= n :
              self.build_instance(i)
              self.stop_instance()
              i = i + 1

        # write nbr_instances
        self.file_set_int(self.statefile,self.nbr_instances)
    
    def stop_signal(self, sig, stack):
        self.logger.info("signal stop")
        if hasattr(self,'stop') :
           self.stop()
        os._exit(0)

# ===================================
# MAIN
# ===================================

class test_instances(sr_instances):
     
      def __init__(self,config=None,args=None):
         sr_instances.__init__(self,config,args)

      def close(self):
          pass

      def reload(self):
          self.logger.info("reloaded")
          self.close()
          self.configure()
          self.run()

      def run(self):
          while True :
                time.sleep(100000)

      def start(self):
          self.logger.info("started")
          self.run()

      def stop(self):
          self.logger.info("stopped")
          pass

def main():


    action = sys.argv[-1]
    args   = sys.argv[1:-1]
    config = './test_instances.conf'

    f = open(config,'wb')
    f.close()


    this_test = test_instances(config,args)

    action = sys.argv[-1]

    if action == 'foreground' : this_test.foreground_parent()
    if action == 'reload'     : this_test.reload_parent()
    if action == 'restart'    : this_test.restart_parent()
    if action == 'start'      : this_test.start_parent()
    if action == 'status'     : this_test.status_parent()
    if action == 'stop'       :
                                this_test.stop_parent()
                                os.unlink('./test_instances.conf')
    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()

