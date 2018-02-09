#!/usr/bin/env python3

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

    # config setup
    cfg = sr_config()

    logger.info("sftp testing start...")
    cfg.defaults()
    cfg.general()
    logger.info("sftp testing config read...")
    cfg.set_sumalgo('d')
    msg = sr_message(cfg)
    logger.info("sftp testing fake message built ...")
    msg.filesize = None
    msg.onfly_checksum = False
    cfg.msg = msg

    opt1 = "destination sftp://${SFTPUSER}@localhost"
    cfg.option( opt1.split()  )
    cfg.logger = logger
    sftp_url = cfg.destination
    cfg.timeout = 5.0
    # 1 bytes par 5 secs
    #cfg.kbytes_ps = 0.0001
    cfg.kbytes_ps = 0.01
    cfg.chmod_dir = 0o775

    sftp = sr_sftp(cfg)
    logger.info("sftp sr_ftp instantiated ...")
    sftp.connect()
    logger.info("sftp sr_ftp connected ...")
    sftp.mkdir("tztz")
    logger.info("sftp sr_ftp mkdir ...")
    ls = sftp.ls()
    if not "tztz" in ls :
       logger.error("test 01: directory creation failed")
       failed = True
    else:
       logger.info("test 01: directory creation succeeded")

    sftp.chmod(0o775,"tztz")
    sftp.cd("tztz")

    f = open("aaa","wb")
    f.write(b"1\n")
    f.write(b"2\n")
    f.write(b"3\n")
    f.close()

    sftp.put("aaa", "bbb")
    ls = sftp.ls()
    if not "bbb" in ls :
       logger.error("test 02: file upload failed")
       failed = True
    else:
       logger.info("test 02: file upload succeeded")

    sftp.chmod(0o775,"bbb")

    sftp.rename("bbb", "ccc")
    ls = sftp.ls()
    if "bbb" in ls or not "ccc" in ls :
       logger.error("test 03: file rename failed")
       failed = True
    else:
       logger.info("test 03: file rename succeeded")

    sftp.get("ccc", "bbb",1,0,4)
    f = open("bbb","rb")
    data = f.read()
    f.close()

    if data != b"\n2\n3" :
       logger.error("test 04: getting a part FAILED")
       failed = True
    else:
       logger.info("test 04: getting a part succeeded")

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
    msg.sumalgo      = checksum_d()
    msg.logger       = logger

    cfg.new_file     = "bbb"
    cfg.new_dir      = "."

    cfg.msg     = msg
    cfg.batch   = 5
    cfg.inflight    = None

    # test transport
    dldr = sftp_transport()

    # download

    try:   os.unlink("bbb")
    except:pass
    msg.onfly_checksum = None
    dldr.download(cfg)
    if not os.path.exists("bbb") :
       logger.error("test 05: download FAILED")
       failed = True
    else:
       logger.info("test 05: download succeeded")

    # onfly_checksum
    if not cfg.msg.onfly_checksum :
       logger.error("test 06: onfly_checksum FAILED")
       failed = True
    else:
       logger.info("test 06: onfly_checksum succeeded")

    # testing various download
    dldr.download(cfg)
    dldr.download(cfg)

    cfg.inflight    = '.'
    dldr.download(cfg)

    msg.sumalgo = None
    dldr.download(cfg)

    cfg.inflight    = '.tmp'
    dldr.download(cfg)
 
    # closing way too much
    dldr.close()
    dldr.close()
    dldr.close()


    # sending
    dldr = sftp_transport()
    cfg.local_file    = "bbb"
    cfg.local_path    = "./bbb"
    cfg.new_dir       = "tztz"
    cfg.new_file      = "ddd"
    cfg.remote_file   = "ddd"
    cfg.remote_path   = "tztz/ddd"
    cfg.remote_urlstr = sftp_url + "/tztz/ddd"
    cfg.remote_dir    = "tztz"
    cfg.chmod         = 0o775
    cfg.inflight      = None
    dldr.send(cfg)
    if not os.path.exists(os.path.expanduser("~/tztz/ddd")) :
       logger.error("test 07: download FAILED")
       failed = True
    else:
       logger.info("test 07: download succeeded")

    dldr.sftp.delete("ddd")
    if os.path.exists("~/tztz/ddd") :
       logger.error("test 08: delete FAILED")
       failed = True
    else:
       logger.info("test 08: delete succeeded")

    # deleting a non existing file
    dldr.sftp.delete("zzz_unexistant")

    # testing several sending options

    cfg.inflight        = '.'
    dldr.send(cfg)
    dldr.sftp.delete("ddd")

    cfg.inflight        = '.tmp'
    dldr.send(cfg)
    dldr.sftp.delete("ddd")

    # testing a number of sends
    dldr.send(cfg)
    dldr.send(cfg)
    dldr.send(cfg)

    dldr.close()


    # as sftp now... do cleanup
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

    if data != b"1\n2\n3\n" :
       logger.error("test 09: bad part FAILED")
       failed = True
    else:
       logger.info("test 09: bad part succeeded")

    sftp.delete("bbb")
    sftp.delete("aaa")

    sftp.close()



    if not failed :
                    print("sr_sftp.py TEST PASSED")
    else :          
                    print("sr_sftp.py TEST FAILED")
                    sys.exit(1)


# ===================================
# MAIN
# ===================================

def main():

    try:    self_test()
    except: 
            (stype, svalue, tb) = sys.exc_info()
            print("%s, Value: %s" % (stype, svalue))
            print("sr_sftp.py TEST FAILED")
            sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()

