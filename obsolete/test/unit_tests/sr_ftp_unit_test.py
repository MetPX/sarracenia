#!/usr/bin/env python3

import os, shutil

try:
    from sr_config import *
    from sr_message import *
    from sr_ftp import *
    from sr_util import *
except:
    from sarra.sr_config import *
    from sarra.sr_message import *
    from sarra.sr_ftp import *
    from sarra.sr_util import *

# ===================================
# self_test
# ===================================


def self_test():

    failed = False
    print("sr_ftp : BEGIN TEST\n")

    # configuration

    cfg = sr_config()
    cfg.configure()
    cfg.set_sumalgo('d')

    msg = sr_message(cfg)
    msg.filesize = None
    msg.onfly_checksum = False

    # 1 bytes par 5 secs
    #cfg.kbytes_ps = 0.0001

    cfg.timeout = 5.0
    cfg.kbytes_ps = 0.01
    cfg.chmod_dir = 0o775
    cfg.msg = msg

    opt1 = "destination ftp://aspymjg@localhost"
    cfg.option(opt1.split())

    # make sure test directory is removed before test startup

    ftp_url = cfg.destination
    ftpuser = ftp_url.split('/')[2].split('@')[0]
    testdir = os.path.expanduser('~' + ftpuser) + '/tztz'
    try:
        shutil.rmtree(testdir)
    except:
        pass

    print("TEST 01: instantiation and connection")

    ftp = sr_ftp(cfg)
    ftp.connect()

    if ftp.check_is_connected():
        print("TEST 01: OK")
    else:
        print("TEST 01: failed ... not connected")
        failed = True

    print("TEST 02: mkdir,chmod,cd")

    ftp.mkdir("tztz")
    ls = ftp.ls()
    if "tztz" in ls:
        ftp.chmod(0o775, "tztz")
        ftp.cd("tztz")
        print("TEST 02: OK")
    else:
        print("TEST 02: failed")
        failed = True

    print("TEST 03: put local aaa to remote bbb, chmod bbb, rename bbb ccc")

    f = open("aaa", "wb")
    f.write(b"1\n")
    f.write(b"2\n")
    f.write(b"3\n")
    f.close()

    ftp.put("aaa", "bbb")
    ls = ftp.ls()
    if "bbb" in ls:
        ftp.chmod(0o775, "bbb")
        ftp.rename("bbb", "ccc")

    ls = ftp.ls()
    if "ccc" in ls:
        print("TEST 03: OK")
    else:
        print("TEST 03: failed")
        failed = True

    # build a message
    msg.pubtime = "20190109084420.788106"
    msg.start_timer()
    msg.topic = "v02.post.test"
    msg.notice = "notice"
    msg.baseurl = ftp_url
    msg.relpath = "tztz/ccc"
    msg.partflg = '1'
    msg.offset = 0
    msg.length = 6

    msg.local_file = "bbb"
    msg.local_offset = 0
    cfg.set_sumalgo('d')
    msg.sumalgo = cfg.sumalgo

    msg.new_file = "bbb"
    msg.new_dir = "."

    cfg.msg = msg
    cfg.batch = 5
    cfg.inflight = None

    print("TEST 04: transport download with exact name and onfly_checksum")

    try:
        os.unlink("bbb")
    except:
        pass

    msg.onfly_checksum = None

    tr = ftp_transport()
    tr.download(cfg)

    if os.path.exists("bbb") and cfg.msg.onfly_checksum:
        os.unlink("./bbb")
        print("TEST 04: OK")
    else:
        print("TEST 04: failed")
        failed = True

    print("TEST 05: download file lock is .filename")
    cfg.inflight = '.'
    tr.download(cfg)
    try:
        os.unlink("./bbb")
        print("TEST 05: OK")
    except:
        print("TEST 05: FAILED, file not found")
        failed = True

    print("TEST 06: download file lock is filename.tmp")
    cfg.inflight = '.tmp'
    tr.download(cfg)
    try:
        os.unlink("./bbb")
        print("TEST 06: OK")
    except:
        print("TEST 06: FAILED, file not found")
        failed = True

    # download the file... it is sent below
    tr.download(cfg)

    # closing way too much
    tr.close()
    tr.close()
    tr.close()
    tr = None

    # configure sending
    tr = ftp_transport()
    cfg.local_file = "bbb"
    msg.relpath = "./bbb"
    msg.new_dir = "tztz"
    msg.new_file = "ddd"
    cfg.remote_file = "ddd"
    cfg.remote_path = "tztz/ddd"
    cfg.remote_urlstr = ftp_url + "/tztz/ddd"
    cfg.remote_dir = "tztz"
    cfg.chmod = 0o775

    print("TEST 07: send file with exact name")
    cfg.inflight = None
    tr.send(cfg)

    if os.path.exists(testdir + os.sep + 'ddd'):
        print("TEST 07: OK")
    else:
        print("TEST 07: FAILED, file not found")
        failed = True

    print("TEST 08: delete remote file")

    ftp = tr.proto
    ftp.delete("ddd")
    if not os.path.exists("~/tztz/ddd"):
        print("TEST 08: OK")
    else:
        print("TEST 08: FAILED, file not found")
        failed = True

    # deleting a non existing file
    print("TEST 09: delete not existing file")
    try:
        ftp.delete("zzz_unexistant")
        print("TEST 09: OK")
    except:
        print("TEST 09: FAILED")
        failed = True

    # testing several sending options

    print("TEST 10: sending file lock = .filename")
    cfg.inflight = '.'
    tr.send(cfg)
    try:
        ftp.delete("ddd")
        print("TEST 10: OK")
    except:
        print("TEST 10: FAILED")
        failed = True

    print("TEST 11: sending file lock = filename.tmp")
    cfg.inflight = '.tmp'
    tr.send(cfg)
    try:
        ftp.delete("ddd")
        print("TEST 11: OK")
    except:
        print("TEST 11: FAILED")
        failed = True

    # testing a number of sends
    print("TEST 12: numerous send for the same file")
    tr.send(cfg)
    tr.send(cfg)
    tr.send(cfg)
    tr.close()
    print("TEST 12: OK")

    # do cleanup from previous tests
    ftp = sr_ftp(cfg)
    ftp.connect()
    ftp.cd("tztz")
    ftp.ls()
    ftp.delete("ccc")
    ftp.delete("ddd")
    ftp.cd("")
    ftp.rmdir("tztz")
    ftp.close()

    if not failed:
        print("sr_ftp: TEST PASSED")
    else:
        print("sr_ftp: TEST FAILED")
        sys.exit(1)


# ===================================
# MAIN
# ===================================


def main():
    try:
        self_test()
    except:
        print("sr_ftp: TEST FAILED")
        raise


# =========================================
# direct invocation : self testing
# =========================================

if __name__ == "__main__":
    main()
