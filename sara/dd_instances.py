#!/usr/bin/python3

import logging,os,psutil,signal,sys

try :
         from dd_config      import *
except :
         from sara.dd_config import *

class dd_instances(dd_config):

    def __init__(self,config=None,args=None):
        signal.signal(signal.SIGTERM, self.stop_signal)
        signal.signal(signal.SIGINT, self.stop_signal)
        signal.signal(signal.SIGHUP, self.reload_signal)
        dd_config.__init__(self,config,args)
        self.cwd = os.getcwd()
        #self.configure()
        self.build_parent()
        self.setlog()

    def build_parent(self):
        self.logpath    = None
        self.basic_name = self.program_name + '_' + self.config_name 
        self.statefile  = self.exedir + os.sep + '.' + self.basic_name + '.state'
        self.last_nbr_instances = self.file_get_int(self.statefile)
        if self.last_nbr_instances == None : self.last_nbr_instances = 0

    def build_instance(self,i):
        self.instance      = i
        self.instance_name = self.basic_name + '_%.4d'%i
        self.instance_str  = self.program_name + ' ' + self.config_name + ' (%.4d)'%i
        self.pidfile       = self.exedir + os.sep + '.' + self.instance_name + '.pid'
        self.logpath       = self.logdir + os.sep +       self.instance_name + '.log'

        self.isrunning     = False
        self.pid           = self.file_get_int(self.pidfile)
    
    # from daniel lemay's metpx version
    def daemonize(self):
        try:
           pid = os.fork()
        except OSError as e:
           raise Exception("fork #1 failed: %s [%d]" % (e.strerror, e.errno))
     
        if (pid == 0):
           os.setsid()
           try:
              pid = os.fork() 
           except OSError as e:
              raise Exception("fork #2 failed: %s [%d]" % (e.strerror, e.errno))
    
           if (pid == 0):   
              os.chdir(self.cwd)
              os.umask(0)
           else:
              os._exit(0) 
        else:
           os._exit(0)  
     
        os.close(sys.stdin.fileno())
        os.close(sys.stdout.fileno())
        #os.close(sys.stderr.fileno())
     
        os.open('/dev/null', os.O_RDWR)  # stdin
        os.dup2(0, 1)                    # stdout
     
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
        self.logger.info("reload")
        if hasattr(self,'reload') :
           self.reload()

    def restart_instance(self):
        self.stop_instance()
        time.sleep(1)
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

        # fork : make sure the parent is not killed
        # wait for child to start
        pid = os.fork()
        if pid > 0 :
           os.wait()
           self.logger.info("%s started" % self.instance_str)
           return

        self.daemonize()

        self.pid = os.getpid()
        self.file_set_int(self.pidfile,self.pid)

        self.setlog()

        self.start()

    def start_parent(self):

        self.logger.info("instances %d \n" % self.nbr_instances)

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
                 time.sleep(1)
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
        self.logger.info("stop")
        if hasattr(self,'stop') :
           self.stop()
        os._exit(0)

# ===================================
# MAIN
# ===================================

class test_instances(dd_instances):
     
      def __init__(self,config=None,args=None):
         dd_instances.__init__(self,config,args)

      def reload(self):
          self.logger.info("reloaded")
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

    f = open('./test_instances.conf','wb')
    f.close()

    this_test = test_instances('./test_instances.conf',sys.argv[1:])

    action = sys.argv[-1]
    if action == 'reload' : this_test.reload_parent()
    if action == 'restart': this_test.restart_parent()
    if action == 'start'  : this_test.start_parent()
    if action == 'stop'   : this_test.stop_parent()
    if action == 'status' : this_test.status_parent()
    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()

