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
# sr_util.py : python3 utility mostly for checksum and file part
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Feb  4 09:09:03 EST 2016
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

import os,stat,time,sys,datetime,calendar
import urllib
import urllib.parse
from hashlib import md5
from hashlib import sha512

"""

A single checksum class is chosen by the source of data being injected into the network.
The following checksum classes are alternatives that are built-in.  Sources may define 
new algorithms that need to be added to networks.

checksums are used by:
    sr_post to generate the initial post.
    sr_post to compare against cached values to see if a given block is the same as what was already posted.
    sr_sarra to ensure that the post received is accurate before echoing further.
    sr_subscribe to compare the post with the file which is already on disk.
    sr_winnow to determine if a given post has been seen before.


The API of a checksum class (in calling sequence order):
   __init__   -- initialize the value of a checksum for a part.
   set_path   -- identify the checksumming algorithm to be used by update.
   update     -- given this chunk of the file, update the checksum for the part
   get_value  -- return the current calculated checksum value.

The API allows for checksums to be calculated while transfer is in progress 
rather than after the fact as a second pass through the data.  

"""

# ===================================
# checksum_0 class
# ===================================

class checksum_0(object):
      """
      Trivial minimalist checksumming algorithm, returns 0 for any file.
      """
      def __init__(self):
          self.value = '0'

      def get_value(self):
          return self.value

      def update(self,chunk):
          pass

      def set_path(self,path):
          pass

# ===================================
# checksum_d class
# ===================================

class checksum_d(object):
      """
      The default algorithm is to do a checksum of the entire contents of the file, which is called 'd'.
      """
      def __init__(self):
          self.value = '0'

      def get_value(self):
          self.value = self.filehash.hexdigest()
          return self.value

      def update(self,chunk):
          self.filehash.update(chunk)

      def set_path(self,path):
          self.filehash = md5()

# ===================================
# checksum_s class
# ===================================

class checksum_s(object):
      """
      The SHA512 algorithm to checksum the entire file, which is called 's'.
      """
      def __init__(self):
          self.value = '0'

      def get_value(self):
          self.value = self.filehash.hexdigest()
          return self.value

      def update(self,chunk):
          self.filehash.update(chunk)

      def set_path(self,path):
          self.filehash = sha512()

# ===================================
# checksum_n class
# ===================================

class checksum_n(object):
      """
      when there is more than one processing chain producing products, it can happen that files are equivalent
      without being identical, for example if each server tags a product with ''generated on server 16', then
      the generation tags will differ.   The simplest option for checksumming then is to use the name of the
      product, which is generally the same from all the processing chains.  
      """
      def __init__(self):
          self.value = '0'

      def get_value(self):
          return self.value

      def update(self,chunk):
          pass

      def set_path(self,path):
          filename   = os.path.basename(path)
          self.value = md5(bytes(filename,'utf-8')).hexdigest()

# ===================================
# startup args parsing
# ===================================

def startup_args(sys_argv):

    actions = ['foreground', 'start', 'stop', 'status', 'restart', 'reload', 'cleanup', 'declare', 'setup' ]
    actions.extend( ['add','disable', 'edit', 'enable', 'list',    'log',    'remove' ] )

    args    = None
    action  = None
    config  = None
    old     = False

    largv   = len(sys_argv)

    # work with a copy

    argv = []
    argv.extend(sys_argv)

    # program

    if largv < 2 : return (args,action,config,old)

    # program action

    if largv < 3 :
       if argv[-1] in actions : action = argv[-1]
       if argv[-1].lower().strip('-') in ['h','help'] : args = [ argv[-1] ]
       return (args,action,config,old)

    # check for action and config flags

    flagA   = False
    flagC   = False

    # program [... -[a|action] action...]

    idx = -1
    try    : idx = argv.index('-a')
    except :
             try    : idx    = argv.index('-action')
             except : pass
    if idx > -1 and idx < largv-2 :
       flagA  = True
       action = argv[idx+1]
       # strip action from args
       cmd    = ' '.join(argv)
       cmd    = cmd.replace(argv[idx] + ' ' + action, '')
       argv   = cmd.split()
       largv  = len(argv)

    # program [... -[c|config] config...]

    idx = -1
    try    : idx = argv.index('-c')
    except :
             try    : idx = argv.index('-config')
             except : pass
    if idx > -1 and idx < largv-2 :
       config = argv[idx+1]
       flagC  = True
       # strip config from args
       cmd    = ' '.join(argv)
       cmd    = cmd.replace(argv[idx] + ' ' + config, '')
       argv   = cmd.split()
       largv  = len(argv)

    # got both flags
    # program [... -[a|action] action... -[c|config] config...]
 
    if flagA and flagC :
       args = argv[1:]
       return (args,action,config,old)

    # action found... but not config
    # program [... -[a|action] action...] config

    if flagA :
       args   = argv[1:-1]
       config = argv[-1]
       return (args,action,config,old)

    # config found... but not action
    # program [... -[c|config] config...] action

    if flagC :
       args   = argv[1:-1]
       action = argv[-1]
       return (args,action,config,old)

    # positional arguments 

    # tolerate old : program [args] config action

    if argv[-1] in actions :
       action = argv[-1]
       config = argv[-2]
       args   = argv[1:-2]
       old    = True
       return (args,action,config,old)

    # program [args] action config

    action = argv[-2]
    config = argv[-1]
    args   = argv[1:-2]

    return (args,action,config,old)

"""

  Time conversion routines.  
   - os.stat, and time.now() return floating point 
   - The floating point representation is a count of seconds since the beginning of the epoch.
   - beginning of epoch is platform dependent, and conversion to actual date is fraught (leap seconds, etc...)
   - Entire SR_* formats are text, no floats are sent over the protocol (avoids byte order issues, null byte / encoding issues, 
     and enhances readability.) 
   - str format: YYYYMMDDHHMMSS.msec goal of this representation is that a naive conversion to floats yields comparable numbers.
   - but the number that results is not useful for anything else, so need these special routines to get a proper epochal time.
   - also OK for year 2032 or whatever (rollover of time_t on 32 bits.)
   - string representation is forced to UTC timezone to avoid having to communicate timezone.

   timeflt2str - accepts a float and returns a string.
   timestr2flt - accepts a string and returns a float.


  caveat:
   - FIXME: this encoding will break in the year 10000 (assumes four digit year) and requires leading zeroes prior to 1000.
     one will have to add detection of the decimal point, and change the offsets at that point.
    
"""

def timeflt2str( f ):
    msec = '.%d' % ((f%1)*1000)
    s  = time.strftime("%Y%m%d%H%M%S",time.gmtime(f)) + msec
    return(s) 
    

def timestr2flt( s ):
    t=datetime.datetime(  int(s[0:4]), int(s[4:6]), int(s[6:8]), int(s[8:10]), int(s[10:12]), int(s[12:14]), 0, datetime.timezone.utc )
    f=calendar.timegm(  t.timetuple())+float('0'+s[14:])
    return(f)

# ===================================
# self_test
# ===================================

def self_test():

    import tempfile

    status = 0

    # ===================================
    # TESTING checksum
    # ===================================

    # creating a temporary directory with testfile test_chksum_file

    tmpdirname = tempfile.TemporaryDirectory().name
    try    : os.mkdir(tmpdirname)
    except : pass
    tmpfilname = 'test_chksum_file'
    tmppath    = tmpdirname + os.sep + 'test_chksum_file'

    f=open(tmppath,'wb')
    f.write(b"0123456789")
    f.write(b"abcdefghij")
    f.write(b"ABCDEFGHIJ")
    f.write(b"9876543210")
    f.close()

    # checksum_0

    chk0 = checksum_0()
    chk0.set_path(tmppath)
    f = open(tmppath,'rb')
    for i in 0,1,2,3 :
        chunk = f.read(10)
        chk0.update(chunk)
    f.close()

    if chk0.get_value() != '0' :
          print("test checksum_0 Failed")
          status = 1
      

    # checksum_d

    chkd = checksum_d()
    chkd.set_path(tmppath)
    f = open(tmppath,'rb')
    for i in 0,1,2,3 :
        chunk = f.read(10)
        chkd.update(chunk)
    f.close()

    if chkd.get_value() != '7efaff9e615737b379a45646c755c492' :
          print("test checksum_d Failed")
          status = 1
      

    # checksum_n

    chkn = checksum_n()
    chkn.set_path(tmpfilname)
    f = open(tmppath,'rb')
    for i in 0,1,2,3 :
        chunk = f.read(10)
        chkn.update(chunk)
    f.close()

    if chkn.get_value() != 'fd6b0296fe95e19fcef6f21f77efdfed' :
          print("test checksum_n Failed")
          status = 1

    # checksum_s

    chks = checksum_s()
    chks.set_path(tmppath)
    f = open(tmppath,'rb')
    for i in 0,1,2,3 :
        chunk = f.read(10)
        chks.update(chunk)
    f.close()

    if chks.get_value() != 'e0103da78bbff9a741116e04f8bea2a5b291605c00731dcf7d26c0848bccf76dd2caa6771cb4b909d5213d876ab85094654f36d15e265d322b68fea4b78efb33':
          print("test checksum_s Failed")
          status = 1
      
    os.unlink(tmppath)
    os.rmdir(tmpdirname)

    if status < 1 : print("test checksum_[0,d,n,s] OK")

    # ===================================
    # TESTING startup_args
    # ===================================

    targs   = [ '-randomize', 'True' ]
    taction = 'cleanup'
    tconfig = 'toto'
    told    = False

    # Tests

    testing_args     = {}

    testing_args[ 1] = ['program']
    testing_args[ 2] = ['program', taction ]

    testing_args[ 3] = ['program',                       taction, tconfig ]
    testing_args[ 4] = ['program', '-randomize', 'True', taction, tconfig ]

    testing_args[ 5] = ['program', '-a', taction,      '-randomize', 'True', tconfig ]
    testing_args[ 6] = ['program', '-c', tconfig,      '-randomize', 'True', taction ]

    testing_args[ 7] = ['program', '-action', taction, '-randomize', 'True', tconfig ]
    testing_args[ 8] = ['program', '-config', tconfig, '-randomize', 'True', taction ]

    testing_args[ 9] = ['program', '-config', tconfig, '-a', taction, '-randomize', 'True' ]

    # old style
    testing_args[10] = ['program', '-randomize', 'True', tconfig, taction ]
    testing_args[11] = ['program',                       tconfig, taction ]


    # testing...

    args,action,config,old = startup_args(testing_args[1])
    if args or action or config or old :
       print("test01 startup_args with %s : Failed" % testing_args[1])
       status = 2

    args,action,config,old = startup_args(testing_args[2])
    if args or action != taction or config or old :
       print("test02 startup_args with %s : Failed" % testing_args[2])
       status = 2

    args,action,config,old = startup_args(testing_args[3])
    if args != [] or action != taction or config != tconfig or old :
       print("test03 startup_args with %s : Failed" % testing_args[2])
       status = 2

    i = 4
    while i<11 :
          args,action,config,old = startup_args(testing_args[i])
          if args != targs  or action != taction or config != tconfig or old != told :
             print("test%.2d startup_args %s : Failed" % (i,testing_args[i]))
             status = 2
          i = i + 1
          if i == 10 : told = True

    args,action,config,old = startup_args(testing_args[11])
    if args != [] or action != taction or config != tconfig or old != told :
       print("test11 startup_args with %s : Failed" % testing_args[11])
       print(args,action,config,old)
       status = 2

    if status < 2 : print("test startup_args OK")

    # ===================================
    # TESTING timeflt2str and timestr2flt
    # ===================================

    dflt = 1500897051.125
    dstr = '20170724115051.125'

    tstr = timeflt2str(dflt)
    tflt = timestr2flt(dstr)

    if dflt != tflt or dstr != tstr :
          print("test timeflt2str timestr2flt : Failed")
          status = 3

    if status < 3 : print("test timeflt2str timestr2flt : OK")

    return status

# ===================================
# MAIN
# ===================================

def main():

    status = self_test()
    sys.exit(status)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()

