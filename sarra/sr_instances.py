#!/usr/bin/python3
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

    def __init__(self,config=None,args=None):
        signal.signal(signal.SIGTERM, self.stop_signal)
        signal.signal(signal.SIGINT, self.stop_signal)
        if _platform != 'win32':
            signal.signal(signal.SIGHUP, self.reload_signal)

        sr_config.__init__(self,config,args)
        self.cwd = os.getcwd()
        self.build_parent()
        self.configure()

    def build_parent(self):
        self.logger.debug("sr_instances build_parent")

        self.logpath    = None

        self.basic_name = self.program_name
        if self.config_name : self.basic_name += '_' + self.config_name 
        self.statefile  = self.user_cache_dir + os.sep + self.basic_name + '.state'

        self.last_nbr_instances = self.file_get_int(self.statefile)
        if self.last_nbr_instances == None : self.last_nbr_instances = 0

    def build_instance(self,i):
        self.logger.debug("sr_instances build_instance %d" % i)
        self.instance      = i
        self.instance_name = self.basic_name + '_%.4d'%i
        self.instance_str  = 'sr_' + self.instance_name[3:].replace('_',' ')

        self.pidfile       = self.user_cache_dir + os.sep + self.instance_name + '.pid'
        self.logpath       = self.user_log_dir   + os.sep + self.instance_name + '.log'

        self.isrunning     = False
        self.pid           = self.file_get_int(self.pidfile)
    
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
        self.configure()
        self.logger.debug("sr_instances foreground_parent")
        self.nbr_instances = 0
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
        if self.user_config != None : cmd.append(self.user_config)
        cmd.append("start")
     
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
           self.logger.info("%s stopped" % self.instance_str)
           return

        try    : 
                 p = psutil.Process(self.pid)
                 status = p.status()
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

