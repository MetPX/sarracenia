#!/usr/bin/env python3

import time, sys

try:
    from sr_config import *
except:
    from sarra.sr_config import *

# ===================================
# self_test
# ===================================


def self_test():
    failed = False

    cfg = sr_config()

    # ===================================
    # TESTING
    # ===================================

    # Testing for 2 weeks - today in YYYYMMDD format
    print('Testing todays date - 2 weeks')
    test = cfg.set_dir_pattern('${YYYYMMDD-2w}')

    answer = time.mktime(time.gmtime()) - 2 * 7 * 24 * 60 * 60
    answer = time.strftime("%Y%m%d", time.localtime(answer))
    print('test: ' + test + '  answer: ' + answer)

    if (not test) or (str(test) != str(answer)):
        failed = True
    else:
        print("Pass\n")

    # Testing for 12 days - today in JJJ format
    print('Testing todays date - 12 days')
    test = cfg.set_dir_pattern('${JJJ-12D}')

    answer = time.mktime(time.gmtime()) - 12 * 24 * 60 * 60
    answer = time.strftime("%j", time.localtime(answer))
    print('test: ' + test + '  answer: ' + answer)

    if (not test) or (str(test) != str(answer)):
        failed = True
    else:
        print("Pass\n")

    # Testing for 60 hours - today in MM format
    print('Testing todays date - 1400 hours')
    test = cfg.set_dir_pattern('${MM-1400h}')

    answer = time.mktime(time.gmtime()) - 1400 * 60 * 60
    answer = time.strftime("%m", time.localtime(answer))
    print('test: ' + test + '  answer: ' + answer)

    if (not test) or (str(test) != str(answer)):
        failed = True
    else:
        print("Pass\n")

    if not failed:
        print("sr_pattern_test.py TEST PASSED")
    else:
        print("sr_pattern_test.py TEST FAILED")
        sys.exit(1)


# ===================================
# MAIN
# ===================================


def main():
    try:
        self_test()
    except:
        print("sr_pattern_test.py TEST FAILED")
        raise


# =========================================
# direct invocation : self testing
# =========================================

if __name__ == "__main__":
    main()
