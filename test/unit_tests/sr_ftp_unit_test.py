#!/usr/bin/env python3

import os,shutil

try    :
         from sr_config         import *
         from sr_message        import *
         from sr_ftp            import *
         from sr_util           import *
except :
         from sarra.sr_config   import *
         from sarra.sr_message  import *
         from sarra.sr_ftp      import *
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
    logger.info("sr_ftp : BEGIN TEST\n")

    # configuration

    cfg = sr_config()
    cfg.logger = logger
    cfg.configure()
    cfg.set_sumalgo('d')

    msg = sr_message(cfg)
    msg.filesize = None
    msg.onfly_checksum = False

    # 1 bytes par 5 secs
    #cfg.kbytes_ps = 0.0001

    cfg.timeout   = 5.0
    cfg.kbytes_ps = 0.01
    cfg.chmod_dir = 0o775
    cfg.msg       = msg

    opt1 = "destination ftp://aspymjg@localhost"
    cfg.option( opt1.split()  )
    
    # make sure test directory is removed before test startup

    ftp_url = cfg.destination
    ftpuser = ftp_url.split('/')[2].split('@')[0]
    testdir  = os.path.expanduser('~'+ftpuser) + '/tztz'
    try   :shutil.rmtree(testdir)
    except: pass

    logger.info("TEST 01: instantiation and connection")

    ftp = sr_ftp(cfg)
    ftp.connect()

    if ftp.check_is_connected():
          logger.info("TEST 01: OK")
    else:
          logger.info("TEST 01: failed ... not connected")
          failed = True

    logger.info("TEST 02: mkdir,chmod,cd")

    ftp.mkdir("tztz")
    ls = ftp.ls()
    if "tztz" in ls :
          ftp.chmod(0o775,"tztz")
          ftp.cd("tztz")
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

    ftp.put("aaa", "bbb")
    ls = ftp.ls()
    if "bbb" in ls :
       ftp.chmod(0o775,"bbb")
       ftp.rename("bbb", "ccc")

    ls = ftp.ls()
    if "ccc" in ls :
          logger.info("TEST 03: OK")
    else:
          logger.info("TEST 03: failed")
          failed = True

    # build a message
    msg.start_timer()
    msg.topic   = "v02.post.test"
    msg.notice  = "notice"
    msg.baseurl = ftp_url
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

    logger.info("TEST 04: transport download with exact name and onfly_checksum")

    try:   os.unlink("bbb")
    except:pass

    msg.onfly_checksum = None

    tr = ftp_transport()
    tr.download(cfg)

    if os.path.exists("bbb") and cfg.msg.onfly_checksum :
          os.unlink("./bbb")
          logger.info("TEST 04: OK")
    else:
          logger.info("TEST 04: failed")
          failed = True


    logger.info("TEST 05: download file lock is .filename")
    cfg.inflight = '.'
    tr.download(cfg)
    try :
            os.unlink("./bbb")
            logger.info("TEST 05: OK")
    except:
            logger.info("TEST 05: FAILED, file not found")
            failed = True

    logger.info("TEST 06: download file lock is filename.tmp")
    cfg.inflight = '.tmp'
    tr.download(cfg)
    try :
            os.unlink("./bbb")
            logger.info("TEST 06: OK")
    except:
            logger.info("TEST 06: FAILED, file not found")
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
    cfg.local_file    = "bbb"
    cfg.local_path    = "./bbb"
    msg.new_dir       = "tztz"
    msg.new_file      = "ddd"
    cfg.remote_file   = "ddd"
    cfg.remote_path   = "tztz/ddd"
    cfg.remote_urlstr = ftp_url + "/tztz/ddd"
    cfg.remote_dir    = "tztz"
    cfg.chmod         = 0o775

    logger.info("TEST 07: send file with exact name")
    cfg.inflight      = None
    tr.send(cfg)

    if os.path.exists(testdir + os.sep + 'ddd') :
            logger.info("TEST 07: OK")
    else:
            logger.info("TEST 07: FAILED, file not found")
            failed = True
    logger.debug  = logger.silence

    logger.info("TEST 08: delete remote file")

    ftp = tr.proto
    ftp.delete("ddd")
    if not os.path.exists("~/tztz/ddd") :
            logger.info("TEST 08: OK")
    else:
            logger.info("TEST 08: FAILED, file not found")
            failed = True

    # deleting a non existing file
    logger.info("TEST 09: delete not existing file")
    try :
            ftp.delete("zzz_unexistant")
            logger.info("TEST 09: OK")
    except:
            logger.info("TEST 09: FAILED")
            failed = True


    # testing several sending options

    logger.info("TEST 10: sending file lock = .filename")
    cfg.inflight        = '.'
    tr.send(cfg)
    try :
            ftp.delete("ddd")
            logger.info("TEST 10: OK")
    except:
            logger.info("TEST 10: FAILED")
            failed = True

    logger.info("TEST 11: sending file lock = filename.tmp")
    cfg.inflight        = '.tmp'
    tr.send(cfg)
    try :
            ftp.delete("ddd")
            logger.info("TEST 11: OK")
    except:
            logger.info("TEST 11: FAILED")
            failed = True

    # testing a number of sends
    logger.info("TEST 12: numerous send for the same file")
    tr.send(cfg)
    tr.send(cfg)
    tr.send(cfg)
    tr.close()
    logger.info("TEST 12: OK")

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

    logger.info("")
    if not failed :
                    logger.info("sr_ftp: TEST PASSED")
    else :          
                    logger.info("sr_ftp: TEST FAILED")
                    sys.exit(1)


# ===================================
# MAIN
# ===================================

def main():

    try:    self_test()
    except: 
            (stype, svalue, tb) = sys.exc_info()
            print("%s, Value: %s" % (stype, svalue))
            print("sr_ftp: TEST FAILED")
            sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()

