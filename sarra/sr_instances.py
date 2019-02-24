#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
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
#  the Free Software Foundation; version 2 of the License.
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
from pathlib import PureWindowsPath

if sys.hexversion > 0x03030000 :
   from shutil import copyfile,get_terminal_size
   py2old=False
else: 
   py2old=True 

try :
         from sr_config      import *
         from sr_util        import *
except :
         from sarra.sr_config import *
         from sarra.sr_util   import *

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
        self.instance_name = self.basic_name + '_%.2d' % i

        self.instance_str  = self.program_name
        if self.config_name: self.instance_str += ' ' + self.config_name + ' %.2d' % i

        self.pidfile       = self.user_cache_dir + os.sep + self.instance_name + '.pid'
        self.logpath       = self.user_log_dir   + os.sep + self.instance_name + '.log'
        self.retry_path    = self.user_cache_dir + os.sep + self.instance_name + '.retry'
        self.save_path     = self.user_cache_dir + os.sep + self.instance_name + '.save'

        # ===
        # MG conversion from 4 to 2 digits instance name
        # get rid of these 3 lines in 2019 :-)
        self.build_path(i)
        self.old_path      = False
        self.build_old_path(i)
        # ===

        self.isrunning     = False
        self.pid           = self.file_get_int(self.pidfile)

    # ===
    # MG conversion from 4 to 2 digits instance name
    # get rid of this module in 2019 :-)
    def build_path(self,i):
        self.logger.debug( "sr_instances build_path instance %d" % i)
        self.instance      = i
        self.instance_name = self.basic_name + '_%.2d' % i

        self.instance_str  = self.program_name
        if self.config_name: self.instance_str += ' ' + self.config_name + ' %.2d' % i

        self.pidfile       = self.user_cache_dir + os.sep + self.instance_name + '.pid'
        self.logpath       = self.user_log_dir   + os.sep + self.instance_name + '.log'
        self.retry_path    = self.user_cache_dir + os.sep + self.instance_name + '.retry'
        self.save_path     = self.user_cache_dir + os.sep + self.instance_name + '.save'

    # ===
    # MG conversion from 4 to 2 digits instance name
    # get rid of this module in 2019 :-)
    def build_old_path(self,i):
        self.logger.debug( "sr_instances build_old_path instance %d" % i)
        self.old_instance_name = self.basic_name + '_%.4d' % i

        self.old_instance_str  = self.program_name
        if self.config_name: self.old_instance_str += ' ' + self.config_name + ' %.4d' % i

        self.old_pidfile       = self.user_cache_dir + os.sep + self.old_instance_name + '.pid'
        self.old_logpath       = self.user_log_dir   + os.sep + self.old_instance_name + '.log'
        self.old_retry_path    = self.user_cache_dir + os.sep + self.old_instance_name + '.retry'
        self.old_save_path     = self.user_cache_dir + os.sep + self.old_instance_name + '.save'

        # running the old style
        if os.path.exists(self.old_logpath):
           self.logger.debug( "sr_instances build_old_path running old style %d" % i)
           self.old_path      = True
           self.instance_name = self.old_instance_name
           self.instance_str  = self.old_instance_str
           self.pidfile       = self.old_pidfile
           self.logpath       = self.old_logpath
           self.retry_path    = self.old_retry_path
           self.save_path     = self.old_save_path

    # ===
    # MG conversion from 4 to 2 digits instance name
    # get rid of this module in 2019 :-)
    def build_path_migration(self,i):
        self.logger.debug( "sr_instances build_path_migration %d" % i)

        # already converted
        if not self.old_path : return

        # set new path
        self.build_path(i)

        # migrate each file...

        # should never happened for pidfile since we migrate on start

        if not os.path.exists(self.pidfile) :
           if os.path.exists(self.old_pidfile) :
              os.rename(self.old_pidfile,self.pidfile)

        # we dont check existance of new log because the startup already wrote in it.
        if os.path.exists(self.old_logpath) :
           os.rename(self.old_logpath,self.logpath)

        if not os.path.exists(self.save_path) :
           if os.path.exists(self.old_save_path) :
              os.rename(self.old_save_path,self.save_path)

        if not os.path.exists(self.retry_path) :
           if os.path.exists(self.old_retry_path) :
              os.rename(self.old_retry_path,self.retry_path)

        if not os.path.exists(self.retry_path+'.heart') :
           if os.path.exists(self.old_retry_path+'.heart') :
              os.rename(self.old_retry_path+'.heart',self.retry_path+'.heart')

        if not os.path.exists(self.retry_path+'.new') :
           if os.path.exists(self.old_retry_path+'.new') :
              os.rename(self.old_retry_path+'.new',self.retry_path+'.new')

        if not os.path.exists(self.retry_path+'.state') :
           if os.path.exists(self.old_retry_path+'.state') :
              os.rename(self.old_retry_path+'.state',self.retry_path+'.state')

        if not os.path.exists(self.retry_path+'.work') :
           if os.path.exists(self.old_retry_path+'.work') :
              os.rename(self.old_retry_path+'.work',self.retry_path+'.work')

        self.logger.info("instance string converted")


    def cleanup_parent(self,log_cleanup=False):
        # make sure all instances are stopped

        no=1
        stopped = True
        while no <= self.nbr_instances :
              self.build_instance(no)
              if self.pid != None :
                 try    : 
                          p = psutil.Process(self.pid)
                          self.logger.info("%s running (pid=%d)" % (self.instance_str,self.pid) )
                          stopped = False
                 except : pass
              no = no + 1

        if not stopped :
           self.logger.error("instances must be stopped for cleanup")
           return False

        # run cleanup

        self.cleanup()

        # get rid of this instance's cache file

        dpath = self.user_cache_dir
        if not os.path.isdir(dpath): return True

        for x in os.listdir(dpath):
            fpath = dpath + os.sep + x
            try   : os.unlink(fpath)
            except: self.logger.debug("could not delete %f on cleanup" % fpath)

        try   : os.rmdir(dpath)
        except: self.logger.debug("could not delete %d on cleanup" % dpath)

        # log_cleanup 

        #if log_cleanup :
        #   no=1
        #   while no <= self.nbr_instances :
        #         self.build_instance(no)
        #         try   : os.unlink(self.logpath)
        #         except: self.logger.debug("could not delete %s logpath" % self.logpath)
        #         no = no + 1

        return True

    def exec_action(self,action,old=False):
        self.logger.debug("config = %s" % self.user_config)

        self.action = action

        if action == 'help':
           self.help()
           return

        if old :
           self.logger.warning("Should invoke 3: %s [args] action config" % sys.argv[0])

        # sr_post special case : may not have config_name

        if self.program_name == 'sr_post' :
           if action == 'status' :
               return
           if action == 'foreground' :
               self.foreground_parent()
               return
           elif action == 'sanity' :
               self.foreground_parent()
               return
           elif (action == 'start' or action == 'restart' ) and (self.sleep <= 0):
               self.logger.info("start|restart do nothing if sleep <= 0. exiting." )
               return

        # No config provided

        if self.config_name == None:
           if   action == 'list'     : self.exec_action_on_all(action)
           elif action == 'restart'  : self.exec_action_on_all(action)
           elif action == 'reload'   : self.exec_action_on_all(action)
           elif action == 'start'    : self.exec_action_on_all(action)
           elif action == 'stop'     : self.exec_action_on_all(action)
           elif action == 'status'   : self.exec_action_on_all(action)
           elif action == 'sanity'   : self.exec_action_on_all(action)
           else :
                self.logger.warning("Should invoke 4: %s [args] action config" % sys.argv[0])
           os._exit(0)

        # Config provided was not a config (i.e. ".conf' file in usr_config_dir)

        if not self.config_found :
           if   action == 'add'      : self.exec_action_on_config(action)
           elif action == 'disable'  : self.exec_action_on_config(action)
           elif action == 'edit'     : self.exec_action_on_config(action)
           elif action == 'enable'   : self.exec_action_on_config(action)
           elif action == 'list'     : self.exec_action_on_config(action)
           elif action == 'remove'   : self.exec_action_on_config(action)
           elif action == 'rename'   : self.exec_action_on_config(action)
           else :
                self.logger.warning("Should invoke 5: %s [args] action config" % sys.argv[0])
           os._exit(0)

        # config file is correct

        if   action == 'foreground' : self.foreground_parent()
        elif action == 'reload'     : self.reload_parent()
        elif action == 'restart'    : self.restart_parent()
        elif action == 'start'      : self.start_parent()
        elif action == 'stop'       : self.stop_parent()
        elif action == 'status'     : self.status_parent()
        elif action == 'sanity'     : 
                                      self.status_parent(sanity=True)
                                      self.log_age_parent()

        elif action == 'cleanup'    : self.cleanup_parent()

        elif action == 'declare'    : self.declare()
        elif action == 'setup'      : self.setup()

        elif action == 'add'        : self.exec_action_on_config(action)
        elif action == 'disable'    : self.exec_action_on_config(action)
        elif action == 'edit'       : self.exec_action_on_config(action)
        elif action == 'enable'     : self.exec_action_on_config(action)
        elif action == 'list'       : self.exec_action_on_config(action)
        elif action == 'log'        : self.exec_action_on_config(action)
        elif action == 'remove'     : self.exec_action_on_config(action)
        elif action == 'rename'     : self.exec_action_on_config(action)

        else :
           self.logger.error("action unknown %s" % action)
           self.help()
           os._exit(1)

    def exec_action_on_all(self,action):

        configdir = self.user_config_dir + os.sep + self.program_dir

        if action == 'list':
            self.print_configdir("configuration examples", os.path.normpath( self.package_dir +os.sep+ 'examples' +os.sep+ self.program_dir) )
            self.print_configdir("general",                os.path.normpath( self.user_config_dir ))
            self.print_configdir("user configurations",    os.path.normpath(configdir))
            print( "logs are in: %s\n" % os.path.normpath( self.user_log_dir ))
            return

        for confname in sorted( os.listdir(configdir) ):
            try: 
                    if confname[-5:] == '.conf' : subprocess.check_output([self.program_name, action, confname] )
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
        self.logger.debug("exec_action_on_config %s, config_dir=%s, user_config=%s" % (action,self.config_dir,self.user_config) )

        usr_cfg  = self.user_config
        plugin   = usr_cfg.endswith('.py') or usr_cfg.endswith('.py.off')

        if plugin: sub_dir = 'plugins'
        else     : sub_dir = self.program_dir

        def_fil = self.user_config_dir + os.sep + sub_dir + os.sep + PureWindowsPath(usr_cfg).name

        if self.config_found : def_fil = self.user_config

        def_dir  = os.path.dirname(def_fil)

        usr_fil  = None
        if    self.config_found      : usr_fil = usr_cfg
        elif  os.path.isfile(usr_cfg): usr_fil = usr_cfg

        # add

        if   action == 'add' and not py2old:
             if not os.path.isdir(def_dir):
                try    : os.makedirs(def_dir, 0o775,True)
                except : pass

             if not usr_fil:
                f  = self.find_conf_file(os.sep + sub_dir + os.sep + usr_cfg)
                if f and 'examples' in f : usr_fil = f

             if not usr_fil or not os.path.isfile(usr_fil):
                self.logger.error("could not add %s to %s" % (self.user_config, def_dir))
             elif usr_fil == def_fil :
                self.logger.warning("file already installed %s" % def_fil)
             else:
                self.logger.info("copying %s to %s" % (usr_fil,def_fil))
                try   : os.unlink(def_fil)
                except: pass
                if _platform != 'win32' :
                    copyfile(usr_fil,def_fil)
                else: # on windows convert text files...
                    excf = open(usr_fil,'r')
                    exfl = excf.readlines()
                    excf.close()
                    dsfl = list(map( lambda x: x.replace( '\n', '\r\n' ), exfl ))
                    dscf = open( def_fil, 'w' )
                    dscf.write(''.join(dsfl))
                    dscf.close() 
                    

        # disable

        elif action == 'disable' :
             src   = def_fil.replace('.off','')
             dst   = src + '.off'
             if  os.path.isfile( dst ):
                 self.logger.info('%s already disabled' % self.user_config )
                 return
             try   : os.rename(src,dst)
             except: self.logger.error("cound not disable %s" % src )

        # edit

        elif action == 'edit'    :
             if not usr_fil:
                f  = self.find_conf_file(usr_cfg)
                if not f:
                    self.logger.error('could not identify file to edit: %s' % usr_cfg  )
                    return

                if self.user_config_dir in f : usr_fil = f
             else:
                usr_fil = self.user_config

             edit_fil = usr_fil

             editor=os.environ.get('EDITOR')
             
             if not editor:
                 if _platform == 'win32' :
                    editor='notepad'
                 else:
                    editor='vi'
                 self.logger.info('using %s. Set EDITOR variable pick another one.' % editor )

             self.run_command([ editor, edit_fil] )

        # enable

        elif action == 'enable'  :
             dst   = def_fil.replace('.off','')
             src   = dst + '.off'
             if  os.path.isfile( dst ):
                 self.logger.info('%s already enabled' % self.user_config )
                 return
             try   : os.rename(src,dst)
             except: self.logger.error("cound not enable %s " % src )

        # list

        elif action == 'list'    :
             if usr_cfg ==  'plugins':
                 self.print_configdir("packaged plugins", os.path.normpath( self.package_dir     +os.sep+ 'plugins'))
                 self.print_configdir("user plugins",     os.path.normpath( self.user_config_dir +os.sep+ 'plugins'))

             else:
                if not usr_fil:
                   usr_fil  = self.find_conf_file(usr_cfg)
                self.list_file(usr_fil)

        # log

        elif action == 'log' and self.config_found :


             if self.nbr_instances == 1 :
                self.build_instance(1)
                if _platform == 'win32' :
                    self.run_command([ 'sr_tailf', self.logpath])
                else:
                    print("\ntail -f %s\n" % self.logpath)
                    self.run_command([ 'tail', '-f', self.logpath])
                return

             if self.no > 0 :
                self.build_instance(self.no)
                if _platform == 'win32' :
                    self.run_command([ 'sr_tailf', self.logpath])
                else:
                    print("\ntail -f %s\n" % self.logpath)
                    self.run_command([ 'tail', '-f', self.logpath] )
                return

             no=1
             while no <= self.nbr_instances :
                   self.build_instance(no)
                   print("\ntail -f %s\n" % self.logpath)
                   if not os.path.isfile(self.logpath) : continue
                   self.run_command( [ 'tail', '-n10', self.logpath] )
                   no = no + 1

        # remove

        elif action == 'remove'  :
             if self.config_found :
                ok = self.cleanup_parent(log_cleanup=True)
                if not ok : return
             if not def_fil                 : return
             if not os.path.isfile(def_fil) : return
             try   : os.unlink(def_fil)
             except: self.logger.error("could not remove %s" % self.def_fil)

        # rename

        elif action == 'rename' :
            old_fil = self.user_config_dir + os.sep + sub_dir + os.sep + self.user_args[-1]
            if not os.path.isfile(old_fil) : return
            if not def_fil                 : return

            copyfile(old_fil,def_fil)
            self.logger.info("renaming %s to %s" % (old_fil,def_fil))
            try    : os.unlink(old_fil)
            except : pass

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
                 return True
        except : pass
        return False

    def foreground_parent(self):
        self.logger.debug("sr_instances foreground_parent")
        self.nbr_instances = 0
        self.build_instance(0)
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

    def log_age_parent(self):

        # instance 0 is the parent... child starts at 1

        i=1
        while i <= self.nbr_instances :
              self.build_instance(i)
              self.log_age_instance()
              i = i + 1

        # the number of instances has decreased... stop excedent
        if i <= self.last_nbr_instances:
           self.stop_instances(i,self.last_nbr_instances)

        # write nbr_instances
        self.file_set_int(self.statefile,self.nbr_instances)
    
    def log_age_instance(self):

        # program is stopped ...  or no sanity_log_dead set

        if self.pid           == None : return
        if self.sanity_log_dead  <= 0 : return

        # in case it is from a plugin
        if self.action == 'foreground': return

        # check log age 

        if os.path.exists(self.logpath):
           log_age  = os.stat(self.logpath)[stat.ST_MTIME]
        else:
           log_age = 0

        now      = time.time()
        elapse   = now - log_age

        if elapse <= self.sanity_log_dead : return

        self.logger.warning("logfile older than %d; restarting %s" % (self.sanity_log_dead, self.instance_str))
        self.restart_instance()

    def reload_parent(self):

        # instance 0 is the parent... child starts at 1

        i=1
        while i <= self.nbr_instances :
              self.build_instance(i)
              self.reload_instance()
              i = i + 1

        # the number of instances has decreased... stop excedent
        if i <= self.last_nbr_instances:
           self.stop_instances(i,self.last_nbr_instances)

        # write nbr_instances
        self.file_set_int(self.statefile,self.nbr_instances)
    
    def reload_signal(self,signum,stack):
        sig_str = None
        if signum == signal.SIGHUP  : sig_str = 'SIGHUP'
        self.logger.info("signal reload (%s)" % sig_str)
        if hasattr(self,'reload') :
           self.reload()

    def restart_instance(self):
        self.stop_instance()
        if self.pid != None :
           self.logger.error("%s could not stop... not restarted " % self.instance_str)
           return
        self.start_instance()

    def restart_parent(self):

        # as parent
        if   self.no == -1 :

             # instance 0 is the parent... child starts at 1

             i=1
             while i <= self.nbr_instances :
                   self.build_instance(i)
                   self.restart_instance()
                   i = i + 1

             # the number of instances has decreased... stop excedent
             if i <= self.last_nbr_instances:
                self.stop_instances(i,self.last_nbr_instances)

             # write nbr_instances
             self.file_set_int(self.statefile,self.nbr_instances)

        # as instance
        else:
             self.logger.debug("restart instance %d \n" % self.no)
             self.build_instance(self.no)
             self.restart_instance()

    def start_instance(self):

        if self.pid != None :
           try    : 
                    p = psutil.Process(self.pid)
                    self.logger.info("%s already started" % self.instance_str)
                    return
           except : 
                    self.logger.info("%s strange state... " % self.instance_str)
                    self.stop_instance()
                    if self.pid != None :
                       self.logger.error("%s could not stop... not started " % self.instance_str)
                       return

        cmd = [ sys.argv[0] ]
        if _platform == 'win32': 
            #! does not work on windows, and subcomponents are actual scripts, not entry points.
            #  need to invoke interpreter manually.
            #  FIXME: pythonw preferred because it continues living after cmd window is closed.
            #
            self.logger.debug("sys.argv[0]=%s windows_run=%s" % (sys.argv[0], self.windows_run) )
            for p in os.getenv("PATH").split(";") :

                if self.windows_run == 'exe':
                    q= p + '\\'+ os.path.basename(sys.argv[0]).replace('.py','') + '.exe' 
                    if os.path.exists( q ):
                        cmd = [ q ]
                        break
                elif self.windows_run == 'pyw':
                    q= p + '\pythonw.exe' 
                    if os.path.exists( q ):
                        cmd = [ q ]
                        break
                elif self.windows_run == 'py':
                    q= p + '\python.exe' 
                    if os.path.exists( q ):
                        cmd = [ q ]
                        break

            if not os.path.exists( cmd[0] ):
                self.logger.warning( "check windows_run setting (%s), perhaps try another (pyw, py, exe)?" % self.windows_run )

            if self.windows_run != 'exe':
                if os.path.exists( sys.argv[0] ):
                     cmd.append( sys.argv[0] )
                else:
                     cmd.append(  sys.argv[0] + '-script.py' )

        if not self.user_args or not "--no" in self.user_args :
           cmd.append("--no")
           cmd.append("%d" % self.instance)
        if self.user_args   != None : cmd.extend(self.user_args)
        cmd.append("start")
        if self.user_config != None : cmd.append(self.user_config)
     
        self.logger.info("%s starting" % self.instance_str)

        # ===
        # MG conversion from 4 to 2 digits instance name
        # get rid of these 3 lines in 2019 :-)
        if os.path.exists(self.old_logpath):
           self.old_path      = True
           self.build_path_migration(self.instance)
        # ===

        self.logger.debug("cmd = %s" % cmd)

        # FIXME: at around 3.4, https://docs.python.org/3/library/os.html#fd-inheritance 
        #   inheritance of file descriptors changed.  I think earlier versions require PIPE
        #   later versions None is better.
        #   use of Pipe causes issue: https://github.com/MetPX/sarracenia/issues/63

        if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 4) :
            pid = subprocess.Popen(cmd,shell=False,\
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        else:  
            pid = subprocess.Popen(cmd,shell=False,close_fds=False)


    def start_parent(self):
        self.logger.debug(" pid %d instances %d no %d \n" % (os.getpid(),self.nbr_instances,self.no))

        # as parent
        if   self.no == -1 :

             # instance 0 is the parent... child starts at 1

             i=1
             while i <= self.nbr_instances :
                   self.build_instance(i)
                   self.setlog()
                   self.start_instance()
                   i = i + 1

             # the number of instances has decreased... stop excedent
             if i <= self.last_nbr_instances:
                self.stop_instances(i,self.last_nbr_instances)

             # write nbr_instances
             self.file_set_int(self.statefile,self.nbr_instances)

        # as instance
        else:
             self.build_instance(self.no)
             self.pid = os.getpid()
             ok = self.file_set_int(self.pidfile,self.pid)
             self.setlog()
             if self.no > 0:
                os.close(0)
                #lfd=os.open( self.logpath, os.O_CREAT|os.O_WRONLY|os.O_APPEND )
                #os.dup2(lfd,1)
                #os.dup2(lfd,2)
  
             self.logger.debug("start instance %d (pid=%d)\n" % (self.no, self.pid) )

             if not ok :
                self.logger.error("could not write pid for instance %s" % self.instance_str)
                self.logger.error("instance not started")
                sys.exit(1)
               
             self.start()
        sys.exit(0)

    def status_instance(self,sanity=False):
        if self.pid == None :
           if not sanity : self.logger.info("%s is stopped" % self.instance_str)
           return

        if psutil.pid_exists(self.pid):
             p = psutil.Process(self.pid)
             status = p.status
             if not isinstance(p.status,str): status = p.status()
             status = status.lower()
             status = status.replace('sleeping','running')
             if not sanity : self.logger.info("%s is %s (pid=%d)" % (self.instance_str,status,self.pid))
             return
        else:
             self.logger.info("%s instance missing (pid=%d)" % (self.instance_str, self.pid) )

        if sanity :
           self.logger.info("%s restart" % self.instance_str)
           self.restart_instance()

    def status_parent(self, sanity=False):

        # instance 0 is the parent... child starts at 1

        i=1
        while i <= self.nbr_instances :
              self.build_instance(i)
              self.status_instance(sanity)
              i = i + 1

        # the number of instances has decreased... stop excedent
        if i <= self.last_nbr_instances:
           self.stop_instances(i,self.last_nbr_instances)

        # write nbr_instances
        self.file_set_int(self.statefile,self.nbr_instances)


    def stop_instance(self):
        if self.pid == None :
           self.logger.info("%s already stopped" % self.instance_str)
           return

        self.logger.info("%s stopping (pid=%d)" % (self.instance_str, self.pid) )

        sleep_max = 7.0
        sleep_now = 0.5

        # try sigterm and let the program finish

        stillAlive = True

        while stillAlive :

              # check if program is still alive

              try    : 
                       p=psutil.Process(self.pid)
                       self.logger.debug("stillAlive %s (pid=%d)" % (self.instance_str,self.pid))
                       stillAlive = True
              except :
                       stillAlive = False
                       break

              # SIGTERM

              try    : os.kill(self.pid, signal.SIGTERM)
              except : self.logger.debug("SIGTERM %s pid = %d did not work" % (self.instance_str,self.pid))

              # sleep

              if sleep_now > sleep_max : break
              time.sleep(sleep_now)
              sleep_now = sleep_now * 2

        # check if program is still alive

        try    : 
                 p=psutil.Process(self.pid)
                 stillAlive = True
        except : stillAlive = False

        # if program is still alive, kill it

        if stillAlive:
           time.sleep(2)
           try   : os.kill(self.pid, signal.SIGKILL)
           except: self.logger.debug("SIGKILL %s pid = %d, will check if still alive" % (self.instance_str,self.pid))
        else:
           # if program is running... we could not stop it
           try: 
                 p=psutil.Process(self.pid)
                 self.logger.error("unable to stop instance = %s (pid=%d)" % (self.instance_str,self.pid))
                 return
           except : pass

        # not running anymore...

        try    : os.unlink(self.pidfile)
        except : pass

        self.logger.info("%s stopped" % self.instance_str)
        self.pid = None

    def stop_instances(self, begin, end):

        pdict = {}

        # get instance info

        i=begin
        while i <= end :
              self.build_instance(i)
              pdict[i] = [self.pid, self.pidfile, self.pid == None, self.instance_str ]
              i = i + 1

        # loop on instance and send SIGTERM

        i=begin
        while i <= end :
              self.pid, self.pidfile, stopped, self.instance_str = pdict[i]
              if not stopped:
                 try   : os.kill(self.pid, signal.SIGTERM)
                 except: self.logger.debug("SIGTERM %s pid = %d, will check if still alive" % (self.instance_str,self.pid))
              i = i + 1

        time.sleep(0.01)

        # loop on instance clean stopped, keep alive in pdict

        i=begin
        while i <= end :
              self.pid, self.pidfile, stopped, self.instance_str = pdict[i]

              if not stopped :
                 try   : 
                         p=psutil.Process(self.pid)
                         i = i+1
                         continue
                 except: pass

              try   : os.unlink(self.pidfile)
              except: pass

              pdict[i] = [None, self.pidfile, True, self.instance_str]
              i = i + 1


        # enforced kill if necessary (sleep 2 sec before first SIGKILL)

        hasSlept = False

        i=begin
        while i <= end :
              self.pid, self.pidfile, stopped, self.instance_str = pdict[i]
              i = i + 1

              if not stopped :

                 if not hasSlept: time.sleep(2)
                 hasSlept = True

                 try   : os.kill(self.pid, signal.SIGKILL)
                 except: self.logger.debug("SIGKILL %s pid = %d, will check if still alive" % (self.instance_str,self.pid))

        # we did not sleep... they are all stopped

        if not hasSlept : return

        # log the one still alive, clean the one stopped

        time.sleep(0.01)

        i=begin
        while i <= end :
              self.pid, self.pidfile, stopped, self.instance_str = pdict[i]
              i = i + 1

              if not stopped : 

                 try   : 
                         p=psutil.Process(self.pid)
                         self.logger.error("unable to stop instance = %s (pid=%d)" % (self.instance_str,self.pid))
                         continue
                 except: pass

              self.logger.info("%s stopped" % self.instance_str)
              try   : os.unlink(self.pidfile)
              except: pass


    def stop_parent(self):

        # as parent
        if   self.no == -1 :

             # instance 0 is the parent... child starts at 1

             i=1
             n = self.nbr_instances
             if n < self.last_nbr_instances :
                n = self.last_nbr_instances

             if i <= n:
                self.stop_instances(i,n)

             # write nbr_instances
             self.file_set_int(self.statefile,self.nbr_instances)

        # as instance
        else:
             self.logger.debug("stop instance %d \n" % self.no)
             self.build_instance(self.no)
             self.stop_instance()
        sys.exit(0)
    
    def stop_signal(self, signum, stack):
        sig_str = None
        if signum == signal.SIGTERM : sig_str = 'SIGTERM'
        if signum == signal.SIGINT  : sig_str = 'SIGINT'
        self.logger.info("signal stop (%s)" % sig_str)

        if hasattr(self,'stop') :
           self.stop()
        os._exit(0)
