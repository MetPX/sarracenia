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
# sr.py : python3 program starting an environment of sarra processes
#         found under ~/.config/sarra/*
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Sep 22 10:41:32 EDT 2015
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

import os, os.path, shutil, subprocess, sys, time

try :    
         from sr_config         import *
         from sr_post           import *
except : 
         from sarra.sr_config   import *
         from sarra.sr_post     import *

cfg    = sr_config()
action = sys.argv[-1]

# an sr_subscribe config will be under ~/.config/sarra/subscribe,
# will be  sr_subscribe ~/.config/sarra/subscribe/file.conf "action"

def invoke(dirconf,pgm,confname,action):

    program = 'sr_' + pgm
    config  = re.sub(r'(\.conf)','',confname)

    try :
             # anything but sr_post
             if program != 'sr_post' :
                subprocess.check_call([program,action,config])
                return

             # sr_post/sr_cpost cases  

             confpath = dirconf + os.sep + pgm + os.sep + confname
             post = sr_post(confpath)

             # if sleep... use sr_cpost
             if post.sleep > 0 :
                try :
                        sr_cpost = shutil.which('sr_cpost')
                        if sr_cpost == None : post.logger.error("sr_cpost not found but option sleep > 0")
                        if sr_cpost != None : program = sr_cpost
                except: pass

             subprocess.check_call([program,'-c',confpath,action])
             return

    except :
             (stype, svalue, tb) = sys.exc_info()
             print("Type: %s, Value: %s" % (stype, svalue))


# check number of config files

def nbr_config(dirconf):
    n = 0

    if not os.path.isdir(dirconf)       : return 0

    for confname in os.listdir(dirconf) :
        if not '.conf' in confname      : continue
        n += 1
 
    return n

# recursive scan of ~/.config/sarra/* , invoking process according to
# the process named from the parent directory

def scandir(dirconf,pgm,action):

    path = dirconf + os.sep + pgm

    if not os.path.isdir(path) : return

    for confname in os.listdir(path) :
        if len(confname) < 5                 : continue
        if not '.conf' in confname[-5:]      : continue
        invoke(dirconf,pgm,confname,action)


# ===================================
# MAIN
# ===================================

def main():
    # first check action

    if len(sys.argv) == 1 or sys.argv[1] not in ['start', 'stop', 'status', 'restart', 'reload', 'cleanup', 'declare', 'setup', 'force_setup' ]:
       print("USAGE: %s (start|stop|restart|reload|status|cleanup|declare|setup) (version: %s) " % (sys.argv[0], sarra.__version__) )
       sys.exit(1)

    force  = False
    action = sys.argv[-1]
    if action == 'force_setup' :
       force = True
       action = 'setup'

    # sarracenia program that may start without config file
    REPORT_PROGRAMS=['audit']
    for d in REPORT_PROGRAMS:
        pgm = d
        if nbr_config(cfg.user_config_dir+os.sep+d) != 0 :
           scandir(cfg.user_config_dir,pgm,action)
        else :
           cfg.logger.info("%s %s" % ('sr_'+ d,sys.argv[-1]))
           subprocess.check_call(['sr_'+pgm,action])

    # sarracenia program requiring configs
    
    SR_PROGRAMS =['post','watch','winnow','sarra','shovel','subscribe','sender','poll','report']

    if not force and action == 'setup' :
       subprocess.check_call(['sr','declare'])
       subprocess.check_call(['sr','force_setup'])
       sys.exit(0)

    for d in SR_PROGRAMS:
        pgm = d
        scandir(cfg.user_config_dir,pgm,action)

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
