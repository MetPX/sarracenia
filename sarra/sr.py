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

import sys, os, os.path, time, subprocess

try :    
         from sr_config         import *
except : 
         from sarra.sr_config    import *

cfg = sr_config()

# an sr_subscribe config will be under ~/.config/sarra/subscribe,
# will be  sr_subscribe ~/.config/sarra/subscribe/file.conf "action"

def invoke(confpath):

    parts = confpath.split('/')

    program = 'sr_' + parts[-2]
    config  = re.sub(r'(\.conf)','',parts[-1])

    try :
             cfg.logger.info("%s %s %s" % (program,config,sys.argv[-1]))
             subprocess.check_call([program,config,sys.argv[-1]])
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

def scandir(dirconf):
    if not os.path.isdir(dirconf)       : return

    for confname in os.listdir(dirconf) :
        if len(confname) < 5                 : continue
        if not '.conf' in confname[-5:]      : continue
        confpat = dirconf + '/' + confname
 
        invoke(confpat)


# ===================================
# MAIN
# ===================================

def main():
    # first check action

    if len(sys.argv) == 1 or sys.argv[1] not in ['start', 'stop', 'status', 'restart', 'reload']:
       print("USAGE: %s (start|stop|restart|reload|status) " % sys.argv[0])
       sys.exit(1)

    # sarracenia program that may start without config file
    LOG_PROGRAMS=['audit','log2clusters','2xreport','log2source']
    for d in LOG_PROGRAMS:
        if nbr_config(cfg.user_config_dir+os.sep+d) != 0 :
           scandir(cfg.user_config_dir+os.sep+d)
        else :
           cfg.logger.info("%s %s" % ('sr_'+ d,sys.argv[-1]))
           subprocess.check_call(['sr_'+d,sys.argv[-1]])

    # sarracenia program requiring configs
    SR_PROGRAMS =['watch','winnow','sarra','shovel','subscribe','sender','poll','report']
    for d in SR_PROGRAMS:
        scandir(cfg.user_config_dir+os.sep+d)

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
