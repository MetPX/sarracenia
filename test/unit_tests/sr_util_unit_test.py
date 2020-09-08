#!/usr/bin/env python3

import tempfile

try:
    from sr_util import *
except:
    from sarra.sr_util import *

# ===================================
# self_test
# ===================================


def self_test():
    failed = False

    # ===================================
    # TESTING startup_args
    # ===================================

    targs = ['-randomize', 'True']
    taction = 'cleanup'
    tconfig = 'toto'
    told = False

    # Tests

    testing_args = {}

    testing_args[1] = ['program']
    testing_args[2] = ['program', taction]

    testing_args[3] = ['program', taction, tconfig]
    testing_args[4] = ['program', '-randomize', 'True', taction, tconfig]

    testing_args[5] = ['program', '-a', taction, '-randomize', 'True', tconfig]
    testing_args[6] = ['program', '-c', tconfig, '-randomize', 'True', taction]

    testing_args[7] = [
        'program', '-action', taction, '-randomize', 'True', tconfig
    ]
    testing_args[8] = [
        'program', '-config', tconfig, '-randomize', 'True', taction
    ]

    testing_args[9] = [
        'program', '-config', tconfig, '-a', taction, '-randomize', 'True'
    ]

    # old style
    testing_args[10] = ['program', '-randomize', 'True', tconfig, taction]
    testing_args[11] = ['program', tconfig, taction]

    # testing...

    print("testing sr_util startup_args")
    args, action, config, old = startup_args(testing_args[1])
    if args or action or config or old:
        print("test 01: startup_args with %s : Failed" % testing_args[1])
        failed = True

    args, action, config, old = startup_args(testing_args[2])
    if args or action != taction or config or old:
        print("test 02: startup_args with %s : Failed" % testing_args[2])
        failed = True

    args, action, config, old = startup_args(testing_args[3])
    if args != [] or action != taction or config != tconfig or old:
        print("test 03: startup_args with %s : Failed" % testing_args[2])
        failed = True

    i = 4
    while i < 11:
        args, action, config, old = startup_args(testing_args[i])
        if args != targs or action != taction or config != tconfig or old != told:
            print("test %.2d: startup_args %s : Failed" %
                  (5 + i, testing_args[i]))
            failed = True

        i = i + 1
        if i == 10: told = True

    args, action, config, old = startup_args(testing_args[11])
    if args != [] or action != taction or config != tconfig or old != told:
        print("test 11: startup_args with %s : Failed" % testing_args[11])
        failed = True

    # ===================================
    # TESTING timeflt2str and timestr2flt
    # ===================================

    print("testing sr_util timeflt2str/timestr2flt ")

    dflt = 1500897051.125
    dstr = '20170724115051.125'

    tflt = timestr2flt(dstr)
    tstr = timeflt2str(dflt)

    if dflt != tflt:
        print("test 12.1: timestr2flt : Failed")
        print("expected: %g, got: %g" % (dflt, tflt))
        failed = True
    if dstr != tstr:
        print("test 12.2: timeflt2str : Failed")
        print("expected: %s, got: %s" % (dstr, tstr))
        failed = True

    # ===================================
    # TESTING alarm
    # ===================================

    print("testing sr_util alarm ")
    try:
        status = 4
        alarm_set(1)
        time.sleep(2)
    except:
        status = 0

    if status == 4: print("test 13: alarm_set 1 NOT OK")

    try:
        status = 0
        alarm_set(2)
        time.sleep(1)
        alarm_cancel()
        time.sleep(1)
    except:
        status = 4

    if status == 4: print("test 14: alarm_cancel 2 NOT OK")

    ###### missing coverage ######
    # class raw_message
    # class sr_proto()
    # class sr_transport()

    if not failed:
        print("sr_util.py TEST PASSED")
    else:
        print("sr_util.py TEST FAILED")
        sys.exit(1)


# ===================================
# MAIN
# ===================================


def main():
    try:
        self_test()
    except:
        print("sr_util.py TEST FAILED")
        raise


# =========================================
# direct invocation : self testing
# =========================================

if __name__ == "__main__":
    main()
