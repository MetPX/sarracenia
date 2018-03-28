#!/usr/bin/env python3

import shutil

try    :
         from sr_config         import *
         from sr_message        import *
         from sr_sftp           import *
         from sr_util           import *
except :
         from sarra.sr_config   import *
         from sarra.sr_message  import *
         from sarra.sr_sftp     import *
         from sarra.sr_util     import *

# ===================================
# self_test
# ===================================

class test_logger:
      def silence(self,str):
          pass
      def __init__(self):
          self.debug   = print
          self.error   = print
          self.info    = print
          self.warning = print
          self.debug   = self.silence

def self_test():

    failed = False
    logger = test_logger()
    logger.info("sr_sftp: BEGIN TEST\n")

    # configuration

    cfg = sr_config()
    cfg.logger = logger
    cfg.configure()
    cfg.set_sumalgo('d')

    msg = sr_message(cfg)
    msg.filesize = None
    msg.lastchunk = True
    msg.onfly_checksum = False

    # 1 bytes par 5 secs
    #cfg.kbytes_ps = 0.0001

    cfg.timeout   = 5.0
    cfg.kbytes_ps = 0.01
    cfg.chmod_dir = 0o775
    cfg.msg       = msg

    opt1 = "destination sftp://${SFTPUSER}@localhost"
    cfg.option( opt1.split()  )
    
    # make sure test directory is removed before test startup

    sftp_url = cfg.destination
    sftpuser = sftp_url.split('/')[2].split('@')[0]
    testdir  = os.path.expanduser('~'+sftpuser) + '/tztz'
    try   :shutil.rmtree(testdir)
    except: pass

    logger.info("TEST 01: instantiation and connection")

    sftp = sr_sftp(cfg)
    sftp.connect()

    if sftp.check_is_connected():
          logger.info("TEST 01: OK")
    else:
          logger.info("TEST 01: failed ... not connected")
          failed = True

    logger.info("TEST 02: mkdir,chmod,cd")

    sftp.mkdir("tztz")
    ls = sftp.ls()
    if "tztz" in ls :
          sftp.chmod(0o775,"tztz")
          sftp.cd("tztz")
          logger.info("TEST 02: OK")
    else:
          logger.info("TEST 02: failed")
          failed = True

    logger.info("TEST 03: put local aaa to remote bbb, chmod bbb, rename bbb ccc")

    f = open("aaa","wb")
    f.write(b"1\n")
    f.write(b"2\n")
    f.write(b"3\n")
    f.close()

    sftp.put("aaa", "bbb")
    ls = sftp.ls()
    if "bbb" in ls :
       sftp.chmod(0o775,"bbb")
       sftp.rename("bbb", "ccc")

    ls = sftp.ls()
    if "ccc" in ls :
          logger.info("TEST 03: OK")
    else:
          logger.info("TEST 03: failed")
          failed = True

    logger.info("TEST 04: get part of remote ccc into bbb")

    sftp.get("ccc", "bbb",1,0,4)
    f = open("bbb","rb")
    data = f.read()
    f.close()

    if data == b"\n2\n3" :
          logger.info("TEST 04: OK")
    else:
          logger.info("TEST 04: failed")
          failed = True

    # build a message
    msg.start_timer()
    msg.topic   = "v02.post.test"
    msg.notice  = "notice"
    msg.baseurl = sftp_url
    msg.relpath = "tztz/ccc"
    msg.partflg = '1'
    msg.offset  = 0
    msg.length  = 6

    msg.local_file   = "bbb"
    msg.local_offset = 0
    cfg.set_sumalgo('d')
    msg.sumalgo      = cfg.sumalgo
    msg.logger       = logger

    msg.new_file     = "bbb"
    msg.new_dir      = "."

    cfg.msg     = msg
    cfg.batch   = 5
    cfg.inflight    = None

    logger.info("TEST 05: transport download with exact name and onfly_checksum")

    try:   os.unlink("bbb")
    except:pass

    msg.onfly_checksum = None

    tr = sftp_transport()
    tr.download(cfg)

    if os.path.exists("bbb") and cfg.msg.onfly_checksum :
          os.unlink("./bbb")
          logger.info("TEST 05: OK")
    else:
          logger.info("TEST 05: failed")
          failed = True


    logger.info("TEST 06: download file lock is .filename")
    cfg.inflight = '.'
    tr.download(cfg)
    try :
            os.unlink("./bbb")
            logger.info("TEST 06: OK")
    except:
            logger.info("TEST 06: FAILED, file not found")
            failed = True

    logger.info("TEST 07: download file lock is filename.tmp")
    cfg.inflight = '.tmp'
    tr.download(cfg)
    try :
            os.unlink("./bbb")
            logger.info("TEST 07: OK")
    except:
            logger.info("TEST 07: FAILED, file not found")
            failed = True

    # download the file... it is sent below
    tr.download(cfg)

    # closing way too much
    tr.close()
    tr.close()
    tr.close()

    # configure sending
    tr = sftp_transport()
    cfg.local_file    = "bbb"
    msg.relpath       = "./bbb"
    msg.new_dir       = "tztz"
    msg.new_file      = "ddd"
    cfg.remote_file   = "ddd"
    cfg.remote_path   = "tztz/ddd"
    cfg.remote_urlstr = sftp_url + "/tztz/ddd"
    cfg.remote_dir    = "tztz"
    cfg.chmod         = 0o775

    logger.info("TEST 08: send file with exact name")
    cfg.inflight      = None
    tr.send(cfg)
    if os.path.exists(os.path.expanduser("~/tztz/ddd")) :
            logger.info("TEST 08: OK")
    else:
            logger.info("TEST 08: FAILED, file not found")
            failed = True

    logger.info("TEST 09: delete remote file")

    sftp = tr.proto
    sftp.delete("ddd")
    if not os.path.exists("~/tztz/ddd") :
            logger.info("TEST 09: OK")
    else:
            logger.info("TEST 09: FAILED, file not found")
            failed = True

    # deleting a non existing file
    logger.info("TEST 10: delete not existing file")
    try :
            sftp.delete("zzz_unexistant")
            logger.info("TEST 10: OK")
    except:
            logger.info("TEST 10: FAILED")
            failed = True


    # testing several sending options

    logger.info("TEST 11: sending file lock = .filename")
    cfg.inflight        = '.'
    tr.send(cfg)
    try :
            sftp.delete("ddd")
            logger.info("TEST 11: OK")
    except:
            logger.info("TEST 11: FAILED")
            failed = True

    logger.info("TEST 12: sending file lock = filename.tmp")
    cfg.inflight        = '.tmp'
    tr.send(cfg)
    try :
            sftp.delete("ddd")
            logger.info("TEST 12: OK")
    except:
            logger.info("TEST 12: FAILED")
            failed = True

    # testing a number of sends
    logger.info("TEST 13: numerous send for the same file")
    tr.send(cfg)
    tr.send(cfg)
    tr.send(cfg)
    tr.close()
    logger.info("TEST 13: OK")


    # do cleanup from previous tests
    sftp = sr_sftp(cfg)
    sftp.connect()
    sftp.cd("tztz")
    sftp.ls()
    sftp.delete("ccc")
    sftp.delete("ddd")
    logger.info("%s" % sftp.originalDir)
    sftp.cd("")
    logger.info("%s" % sftp.getcwd())
    sftp.rmdir("tztz")
    sftp.close()

    pwd = os.getcwd()

    # as sftp do part stuff back and fore
    logger.info("TEST 14: testing parts get/put")
    sftp = sr_sftp(cfg)
    sftp.connect()
    sftp.cd(pwd)

    sftp.set_sumalgo(cfg.sumalgo)
    sftp.put("aaa","bbb",0,0,2)
    sftp.get("aaa","bbb",2,2,2)
    sftp.put("aaa","bbb",4,4,2)

    f = open("bbb","rb")
    data = f.read()
    f.close()

    if data == b"1\n2\n3\n" :
            logger.info("TEST 14: OK")
    else:
            logger.info("TEST 14: FAILED")
            failed = True

    sftp.delete("bbb")
    sftp.delete("aaa")

    sftp.close()

    logger.info("")
    if not failed :
                    logger.info("sr_sftp: TEST PASSED")
    else :          
                    logger.info("sr_sftp: TEST FAILED")
                    sys.exit(1)


# ===================================
# MAIN
# ===================================

def main():

    try:    self_test()
    except: 
            (stype, svalue, tb) = sys.exc_info()
            print("%s, Value: %s" % (stype, svalue))
            print("sr_sftp: TEST FAILED")
            sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()

