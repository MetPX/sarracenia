#!/usr/bin/env python3

import tempfile

try :
         from sr_util         import *
except :
         from sarra.sr_util   import *

# ===================================
# self_test
# ===================================

def self_test():


    failed = False

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

    v = int(chk0.get_value())
    if v < 0 or v > 9999 :
       print("test 01: checksum_0 did not work")
       failed = True
      

    # checksum_d

    chkd = checksum_d()
    chkd.set_path(tmppath)
    f = open(tmppath,'rb')
    for i in 0,1,2,3 :
        chunk = f.read(10)
        chkd.update(chunk)
    f.close()

    if chkd.get_value() != '7efaff9e615737b379a45646c755c492' :
       print("test 02: checksum_d did not work")
       failed = True
      

    # checksum_n

    chkn = checksum_n()
    chkn.set_path(tmpfilname)
    f = open(tmppath,'rb')
    for i in 0,1,2,3 :
        chunk = f.read(10)
        chkn.update(chunk)
    f.close()

    v=chkn.get_value()

    if chkn.get_value() != 'fd6b0296fe95e19fcef6f21f77efdfed' :
       print("test 03: checksum_N did not work")
       failed = True

    # checksum_N

    chkN = checksum_N()
    chkN.set_path(tmpfilname,'i,1,256,1,0,0')
    v = chkN.get_value()
  
    # this should do nothing
    chunk = 'aaa'
    chkN.update(chunk)

    if chkN.get_value() != 'a0847ab809f83cb573b76671bb500a430372d2e3d5bce4c4cd663c4ea1b5c40f5eda439c09c7776ff19e3cc30459acc2a387cf10d056296b9dc03a6556da291f' :
       print("test 04: checksum_N did not work")
       failed = True

    # checksum_s

    chks = checksum_s()
    chks.set_path(tmppath)
    f = open(tmppath,'rb')
    for i in 0,1,2,3 :
        chunk = f.read(10)
        chks.update(chunk)
    f.close()

    if chks.get_value() != 'e0103da78bbff9a741116e04f8bea2a5b291605c00731dcf7d26c0848bccf76dd2caa6771cb4b909d5213d876ab85094654f36d15e265d322b68fea4b78efb33':
       print("test 05: checksum_s did not work")
       failed = True
      
    os.unlink(tmppath)
    os.rmdir(tmpdirname)

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
       print("test 06: startup_args with %s : Failed" % testing_args[1])
       failed = True

    args,action,config,old = startup_args(testing_args[2])
    if args or action != taction or config or old :
       print("test 07: startup_args with %s : Failed" % testing_args[2])
       failed = True

    args,action,config,old = startup_args(testing_args[3])
    if args != [] or action != taction or config != tconfig or old :
       print("test 08: startup_args with %s : Failed" % testing_args[2])
       failed = True

    i = 4
    while i<11 :
          args,action,config,old = startup_args(testing_args[i])
          if args != targs  or action != taction or config != tconfig or old != told :
             print("test %.2d: startup_args %s : Failed" % (5+i,testing_args[i]))
             failed = True

          i = i + 1
          if i == 10 : told = True

    args,action,config,old = startup_args(testing_args[11])
    if args != [] or action != taction or config != tconfig or old != told :
       print("test 16: startup_args with %s : Failed" % testing_args[11])
       failed = True

    # ===================================
    # TESTING timeflt2str and timestr2flt
    # ===================================

    dflt = 1500897051.125
    dstr = '20170724115051.125'

    tstr = timeflt2str(dflt)
    tflt = timestr2flt(dstr)

    if dflt != tflt or dstr != tstr :
       print("test 17: timeflt2str timestr2flt : Failed")
       print("expected: %g, got: %g" % ( tflt, dflt ) )
       print("expected: %s, got: %s" % ( tstr, dstr ) )
       failed = True

    # ===================================
    # TESTING alarm
    # ===================================

    try: 
            status = 4
            alarm_set(1)
            time.sleep(2)
    except: status = 0

    if status == 4 : print("test 18: alarm_set 1 NOT OK")

    try: 
            status = 0
            alarm_set(2)
            time.sleep(1)
            alarm_cancel()
            time.sleep(1)
    except: status = 4

    if status == 4 : print("test 19: alarm_cancel 2 NOT OK")


###### missing coverage ######
# class raw_message
# class sr_proto()
# class sr_transport()


    if not failed :
                    print("sr_util.py TEST PASSED")
    else :          
                    print("sr_util.py TEST FAILED")
                    sys.exit(1)


# ===================================
# MAIN
# ===================================

def main():

    try:    self_test()
    except: 
            (stype, svalue, tb) = sys.exc_info()
            print("%s, Value: %s" % (stype, svalue))
            print("sr_util.py TEST FAILED")
            sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()

