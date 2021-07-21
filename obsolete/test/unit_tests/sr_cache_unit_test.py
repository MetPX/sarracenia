#!/usr/bin/env python3

import tempfile

try:
    from sr_cache import *
    from sr_config import *
except:
    from sarra.sr_cache import *
    from sarra.sr_config import *

# ===================================
# self_test
# ===================================


def self_test():

    failed = False
    # creating a temporary cache directory/file

    tmpdirname = tempfile.TemporaryDirectory().name
    try:
        os.mkdir(tmpdirname)
    except:
        pass
    tmpfilname = 'cache_test_file'
    tmppath = tmpdirname + os.sep + 'cache_test_file'

    cfg = sr_config()
    cfg.config_name = "test"
    cfg.configure()
    # cfg.general()

    optH = "caching 1"
    cfg.option(optH.split())

    # check creation addition close
    cache = sr_cache(cfg)
    cache.open(tmppath)
    cache.check('key1', 'file1', 'part1')
    cache.check('key2', 'file2', 'part2')
    cache.check('key1', 'file1', 'part1')
    cache.close()

    cache = sr_cache(cfg)
    cache.open(tmppath)
    cache.load()

    # one collision when adding so 2 entries
    if len(cache.cache_dict) != 2:
        print("test 01: expecting 2 entries...")
        failed = True

    # expire previous and add 3
    time.sleep(1)
    cache.check('key3', 'file3', 'part3')
    cache.check_expire()
    cache.check('key4', 'file4', None)
    cache.check('key5', 'file5', 'part5')
    if len(cache.cache_dict) != 3:
        print("test 02: expecting 3 entries...")
        failed = True

    #checking cache internals ...
    #print("%s" % cache.cache_dict)

    cache.close()

    # expire previous
    time.sleep(1)
    cache = sr_cache(cfg)
    cache.open(tmppath)
    if len(cache.cache_dict) != 0:
        print("test 03: expecting 0 entry...")
        failed = True
    cache.close()

    #add 100 entries
    cache = sr_cache(cfg)
    cache.open(tmppath)
    cache.load()
    i = 0
    now = time.time()
    while i < 100:
        cache.check('key%d' % i, 'file%d' % i, 'part%d' % i)
        i = i + 1

    if len(cache.cache_dict) != 100:
        print("test 04: expecting 100 entries...")
        failed = True

    # free cache
    cache.free()

    if len(cache.cache_dict) != 0:
        print("test 05: expecting 0 entry...")
        failed = True

    cache.close()

    #add 10 entries
    cache = sr_cache(cfg)
    cache.open(tmppath)
    i = 0
    while i < 10:
        cache.check('key%d' % i, 'file%d' % i, 'part%d' % i)
        cache.check('key%d' % i, 'file%d' % i, 'part0%d' % i)
        cache.check('key%d' % i, 'file%d' % i, 'part1%d' % i)
        cache.check('key%d' % i, 'file%d' % i, 'part2%d' % i)
        i = i + 1

    # delete one
    cache.delete_path('file8')

    if len(cache.cache_dict) != 9:
        print("test 06: expecting 9 entries...got %d" % len(cache.cache_dict))
        failed = True

    # expire and clean
    time.sleep(1)
    cache.clean()
    if len(cache.cache_dict) != 0:
        print("test 07: expecting 0 entry...")
        failed = True

    # add one and save
    cache.check('key%d' % i, 'file%d' % i, 'part2%d' % i)
    cache.save()
    if len(cache.cache_dict) != 1:
        print("test 08: expecting 1 entry...")
        failed = True

    if not os.path.exists(tmppath):
        print("test 09: cache file should exists")
        failed = True

    # close and unlink
    cache.close(unlink=True)
    if os.path.exists(tmppath):
        print("test 10: cache file should have been deleted")
        failed = True

    if not failed:
        print("sr_cache.py TEST PASSED")
    else:
        print("sr_cache.py TEST FAILED")
        sys.exit(1)


# ===================================
# MAIN
# ===================================


def main():
    try:
        self_test()
    except:
        print("sr_cache.py TEST FAILED")
        raise


# =========================================
# direct invocation : self testing
# =========================================

if __name__ == "__main__":
    main()
