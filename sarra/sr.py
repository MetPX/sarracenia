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
#  Jun Hu         - Shared Services Canada
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

import sys, os, os.path, time, pwd, subprocess

# just make it simple and stupid

# first check action

if sys.argv[1] not in ['start', 'stop', 'status', 'restart', 'reload']:
   print("USAGE: %s (start|stop|restart|reload|status) " % sys.argv[0])
   sys.exit(1)

# an sr_subscribe config will be under ~/.config/sarra/subscribe,
# will be  sr_subscribe ~/.config/sarra/subscribe/file.conf "action"

def invoke(confpath):

    parts = confpath.split('/')

    if not parts[-2] in ['sarra','subscribe','sender','poll'] : return

    program = 'sr_' + parts[-2]

    print("executing %s %s %s" % (program,confpath,sys.argv[-1]))

    pid = os.fork()
    if pid > 0 :
       os.wait()
       return

    try :
             subprocess.check_call([program,confpath,sys.argv[-1]])
    except :
             (stype, svalue, tb) = sys.exc_info()
             print("Type: %s, Value: %s" % (stype, svalue))



# recursive scan of ~/.config/sarra/* , invoking process according to
# the process named from the parent directory

def scandir(dirpath):
    for name in os.listdir(dirpath) :
        absname = dirpath+'/'+name

        if os.path.isdir(absname) : scandir(absname)
        if not '.conf' in name    : continue
 
        invoke(absname)


homedir = os.path.expanduser("~")
confdir = homedir + '/.config/sarra/'

scandir(confdir)
sys.exit(0)
