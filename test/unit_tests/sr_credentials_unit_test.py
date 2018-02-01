#!/usr/bin/env python3

try :
         from sr_credentials       import *
except : 
         from sarra.sr_credentials import *

# ===================================
# self_test
# ===================================

class test_logger:
      def silence(self,str):
          pass

      def __init__(self):
          self.debug   = self.silence
          self.error   = print
          self.info    = self.silence
          self.warning = print

def self_test():

    failed      = False
    logger      = test_logger()
    credentials = sr_credentials(logger)

    # covers : parse, credential_details obj, isTrue, add
    line = "ftp://guest:toto@localhost active , binary"
    credentials.parse(line)

    # covers get with match
    urlstr = "ftp://guest:toto@localhost"
    ok, details = credentials.get(urlstr)
    if not ok :
       print("test 01: parsed %s and could not get %s " % (line,urlstr))
       failed = True

    # check details
    if not details.passive == False or \
       not details.binary  == True   :
       print("test 02: parsed %s and passive = %s, binary = " % (line,details.passive,details.binary))
       failed = True

    # covers get with resolve 1
    urlstr = "ftp://localhost"
    ok, details = credentials.get(urlstr)
    if not ok :
       print("test 03: parsed %s and could not get %s " % (line,urlstr))
       failed = True

    # covers get with resolve 2
    urlstr = "ftp://guest@localhost"
    ok, details = credentials.get(urlstr)
    if not ok :
       print("test 04: parsed %s and could not get %s " % (line,urlstr))
       failed = True

    # covers unresolve get
    urlstr = "http://localhost"
    ok, details = credentials.get(urlstr)
    if ok :
       print("test 05: parsed %s and could get %s " % (line,urlstr))
       failed = True

    # covers read
    urlstr = "sftp://ruser@remote"
    line   = urlstr + " ssh_keyfile=/tmp/mytoto2\n"
    f = open('/tmp/mytoto2','w')
    f.write(line)
    f.close()

    credentials.read('/tmp/mytoto2')
    ok, details = credentials.get(urlstr)
    if not ok or details.ssh_keyfile != '/tmp/mytoto2' :
       print("test 06: read %s and could not get %s (ssh_keyfile = %s) " % (line,urlstr,details.ssh_keyfile))
       failed = True

    os.unlink('/tmp/mytoto2')

    # covers isValid
    bad_urls = ["ftp://host","file://aaa/","ftp://user@host","ftp://user:@host","ftp://:pass@host"]
    for urlstr in bad_urls :
        if credentials.isValid(urllib.parse.urlparse(urlstr)) :
           print("test 07: isValid %s returned True" % urlstr)
           failed = True

    # covers Valid sftp
    ok_urls = ["sftp://host","sftp://aaa/","sftp://user@host","sftp://user:@host","sftp://:pass@host"]
    for urlstr in ok_urls :
        if not credentials.isValid(urllib.parse.urlparse(urlstr)) :
           print("test 08: not isValid %s returned True" % urlstr)
           failed = True


    if not failed :
                    print("sr_credentials.py TEST PASSED")
    else :          
                    print("sr_credentials.py TEST FAILED")
                    sys.exit(1)


# ===================================
# MAIN
# ===================================

def main():

    try:    self_test()
    except: 
            (stype, svalue, tb) = sys.exc_info()
            print("%s, Value: %s" % (stype, svalue))
            print("sr_credentials.py TEST FAILED")
            sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()

