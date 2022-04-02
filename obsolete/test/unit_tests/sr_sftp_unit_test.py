#!/usr/bin/env python3

import shutil

try:
    from sr_config import *
    from sr_message import *
    from sr_sftp import *
    from sr_util import *
except:
    from sarra.sr_config import *
    from sarra.sr_message import *
    from sarra.sr_sftp import *
    from sarra.sr_util import *

# ===================================
# self_test
# ===================================


def self_test():

    failed = False

    # configuration

    cfg = sr_config()
    cfg.configure()
    cfg.set_sumalgo('d')
    cfg.option(['ll', 'None'])
    print("sr_sftp: BEGIN TEST\n")

    msg = sr_message(cfg)
    msg.filesize = None
    msg.lastchunk = True
    msg.onfly_checksum = False

    # 1 bytes par 5 secs
    #cfg.kbytes_ps = 0.0001

    cfg.timeout = 5.0
    cfg.kbytes_ps = 0.01
    cfg.chmod_dir = 0o775
    cfg.msg = msg

    opt1 = "destination sftp://${SFTPUSER}@localhost"
    cfg.option(opt1.split())

    # make sure test directory is removed before test startup

    sftp_url = cfg.destination
    sftpuser = sftp_url.split('/')[2].split('@')[0]
    testdir = os.path.expanduser('~' + sftpuser) + '/tztz'
    try:
        shutil.rmtree(testdir)
    except:
        pass

    print("TEST 01: instantiation and connection")

    sftp = sr_sftp(cfg)
    sftp.connect()

    if sftp.check_is_connected():
        print("TEST 01: OK")
    else:
        print("TEST 01: failed ... not connected")
        failed = True

    print("TEST 02: mkdir,rmdir,chmod,cd")

    sftp.mkdir("txtx")
    ls = sftp.ls()
    if "txtx" in ls:
        sftp.chmod(0o775, "txtx")
        sftp.delete("txtx")

    ls = sftp.ls()
    if "txtx" in ls:
        print("TEST 02: failed1")
        failed = True
    else:
        print("TEST 02: OK1")

    sftp.mkdir("tztz")
    ls = sftp.ls()
    if "tztz" in ls:
        sftp.chmod(0o775, "tztz")
        sftp.cd("tztz")
        print("TEST 02: OK2")
    else:
        print("TEST 02: failed2")
        failed = True

    print("TEST 03: put local aaa to remote bbb, chmod bbb, rename bbb ccc")

    f = open("aaa", "wb")
    f.write(b"1\n")
    f.write(b"2\n")
    f.write(b"3\n")
    f.close()

    sftp.put("aaa", "bbb")
    ls = sftp.ls()
    if "bbb" in ls:
        sftp.chmod(0o775, "bbb")
        sftp.rename("bbb", "ccc")

    ls = sftp.ls()
    if "ccc" in ls:
        print("TEST 03: OK")
    else:
        print("TEST 03: failed")
        failed = True

    print("TEST 04: get part of remote ccc into bbb")

    sftp.get("ccc", "bbb", 1, 0, 4)
    f = open("bbb", "rb")
    data = f.read()
    f.close()

    if data == b"\n2\n3":
        print("TEST 04: OK")
    else:
        print("TEST 04: failed")
        failed = True

    # build a message
    msg.pubtime = "20190109084420.788106"
    msg.start_timer()
    msg.topic = "v02.post.test"
    msg.notice = "notice"
    msg.baseurl = sftp_url
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

    print("TEST 05: transport download with exact name and onfly_checksum")

    try:
        os.unlink("bbb")
    except:
        pass

    msg.onfly_checksum = None

    tr = sftp_transport()
    tr.download(cfg)

    if os.path.exists("bbb") and cfg.msg.onfly_checksum:
        os.unlink("./bbb")
        print("TEST 05: OK")
    else:
        print("TEST 05: failed")
        failed = True

    print("TEST 06: download file lock is .filename")
    cfg.inflight = '.'
    tr.download(cfg)
    try:
        os.unlink("./bbb")
        print("TEST 06: OK")
    except:
        print("TEST 06: FAILED, file not found")
        failed = True

    print("TEST 07: download file lock is filename.tmp")
    cfg.inflight = '.tmp'
    tr.download(cfg)
    try:
        os.unlink("./bbb")
        print("TEST 07: OK")
    except:
        print("TEST 07: FAILED, file not found")
        failed = True

    # download the file... it is sent below
    tr.download(cfg)

    # closing way too much
    tr.close()
    tr.close()
    tr.close()

    # configure sending
    tr = sftp_transport()
    cfg.local_file = "bbb"
    msg.relpath = "./bbb"
    msg.new_dir = "tztz"
    msg.new_file = "ddd"
    cfg.remote_file = "ddd"
    cfg.remote_path = "tztz/ddd"
    cfg.remote_urlstr = sftp_url + "/tztz/ddd"
    cfg.remote_dir = "tztz"
    cfg.chmod = 0o775

    print("TEST 08: send file with exact name")
    cfg.inflight = None
    tr.send(cfg)
    if os.path.exists(os.path.expanduser("~/tztz/ddd")):
        print("TEST 08: OK")
    else:
        print("TEST 08: FAILED, file not found")
        failed = True

    print("TEST 09: delete remote file")

    sftp = tr.proto
    sftp.delete("ddd")
    if not os.path.exists("~/tztz/ddd"):
        print("TEST 09: OK")
    else:
        print("TEST 09: FAILED, file not found")
        failed = True

    # deleting a non existing file
    print("TEST 10: delete not existing file")
    try:
        sftp.delete("zzz_unexistant")
        print("TEST 10: OK")
    except:
        print("TEST 10: FAILED")
        failed = True

    # testing several sending options

    print("TEST 11: sending file lock = .filename")
    cfg.inflight = '.'
    tr.send(cfg)
    try:
        sftp.delete("ddd")
        print("TEST 11: OK")
    except:
        print("TEST 11: FAILED")
        failed = True

    print("TEST 12: sending file lock = filename.tmp")
    cfg.inflight = '.tmp'
    tr.send(cfg)
    try:
        sftp.delete("ddd")
        print("TEST 12: OK")
    except:
        print("TEST 12: FAILED")
        failed = True

    # testing a number of sends
    print("TEST 13: numerous send for the same file")
    tr.send(cfg)
    tr.send(cfg)
    tr.send(cfg)
    tr.close()
    print("TEST 13: OK")

    # do cleanup from previous tests
    sftp = sr_sftp(cfg)
    sftp.connect()
    sftp.cd("tztz")
    sftp.ls()
    sftp.delete("ccc")
    sftp.delete("ddd")
    print("%s" % sftp.originalDir)
    sftp.cd("")
    print("%s" % sftp.getcwd())
    sftp.rmdir("tztz")
    sftp.close()

    pwd = os.getcwd()

    # as sftp do part stuff back and fore
    print("TEST 14: testing parts get/put")
    sftp = sr_sftp(cfg)
    sftp.connect()
    sftp.cd(pwd)

    sftp.set_sumalgo(cfg.sumalgo)
    sftp.put("aaa", "bbb", 0, 0, 2)
    sftp.get("aaa", "bbb", 2, 2, 2)
    sftp.put("aaa", "bbb", 4, 4, 2)

    f = open("bbb", "rb")
    data = f.read()
    f.close()

    if data == b"1\n2\n3\n":
        print("TEST 14: OK")
    else:
        print("TEST 14: FAILED")
        failed = True

    sftp.delete("bbb")
    sftp.delete("aaa")

    sftp.close()

    if not failed:
        print("sr_sftp: TEST PASSED")
    else:
        print("sr_sftp: TEST FAILED")
        sys.exit(1)


# ===================================
# MAIN
# ===================================


def main():
    try:
        self_test()
    except:
        print("sr_sftp: TEST FAILED")
        raise


# =========================================
# direct invocation : self testing
# =========================================

if __name__ == "__main__":
    main()
