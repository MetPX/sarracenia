#!/usr/bin/env python3

try    :
         from sr_config         import *
         from sr_consumer       import *
         from sr_http           import *
         from sr_message        import *
         from sr_util           import *
except :
         from sarra.sr_config   import *
         from sarra.sr_consumer import *
         from sarra.sr_http     import *
         from sarra.sr_message  import *
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
          self.info    = self.silence

def self_test():

    failed = False
    logger = test_logger()

    opt1   = 'accept .*'

    #setup consumer to catch first post
    cfg = sr_config()
    cfg.configure()
    cfg.logger         = logger
    cfg.use_pika       = False
    cfg.broker         = urllib.parse.urlparse("amqp://anonymous:anonymous@dd.weather.gc.ca/")
    cfg.prefetch       = 10
    cfg.bindings       = [ ( 'xpublic', 'v02.post.#') ]
    cfg.durable        = False
    cfg.expire         = 60 * 1000 # 60 secs
    cfg.message_ttl    = 10 * 1000 # 10 secs
    cfg.user_cache_dir = os.getcwd()
    cfg.config_name    = "test"
    cfg.queue_name     = None
    cfg.retry_path     = '/tmp/retry'
    cfg.option( opt1.split()  )

    consumer = sr_consumer(cfg)

    i = 0
    while True :
          ok, msg = consumer.consume()
          if ok: break

    cfg.set_sumalgo('d')
    cfg.msg = msg
    msg.sumalgo = cfg.sumalgo
    cfg.new_dir  = "."
    cfg.new_file = "toto"

    cfg.msg.local_offset = 0

    tr   = http_transport()

    cfg.inflight = None
    tr.download(cfg)

    cfg.inflight = '.'
    tr.download(cfg)

    cfg.inflight = '.tmp'
    tr.download(cfg)

    cfg.msg.sumalgo = cfg.sumalgo
    tr.download(cfg)

    cfg.timeout = 12
    cfg.inflight = None
    tr.download(cfg)

    http = tr.http

    fp = open("titi","wb")
    fp.write(b"01234567890")
    fp.close()

    fp = open("toto","rb")
    data = fp.read()
    fp.close()

    cfg.msg.partflg = 'i'
    cfg.msg.offset = 3
    cfg.msg.length = 5
    cfg.msg.local_offset = 1
    cfg.new_file   = "titi"

    tr.download(cfg)

    fp = open("titi","rb")
    data2 = fp.read()
    fp.close()

    b  = cfg.msg.offset
    e  = cfg.msg.offset+cfg.msg.length-1
    b2 = cfg.msg.local_offset
    e2 = cfg.msg.local_offset+cfg.msg.length-1
             
    if data[b:e] != data2[b2:e2] :
       logger.error("sr_http TEST FAILED")
       sys.exit(1)

    os.unlink("titi")
    os.unlink("toto")

    os.unlink(consumer.queuepath)
    consumer.cleanup()
    consumer.close()


    if not failed :
                    print("sr_http.py TEST PASSED")
    else :          
                    print("sr_http.py TEST FAILED")
                    sys.exit(1)


# ===================================
# MAIN
# ===================================

def main():

    try:    self_test()
    except: 
            (stype, svalue, tb) = sys.exc_info()
            print("%s, Value: %s" % (stype, svalue))
            print("sr_http.py TEST FAILED")
            sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()

