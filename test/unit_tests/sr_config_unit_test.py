#!/usr/bin/env python3
try :
         from sr_config       import *
except : 
         from sarra.sr_config import *

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

    # test include
    f = open("./bbb.inc","w")
    f.write("randomize True\n")
    f.close()
    f = open("./aaa.conf","w")
    f.write("include bbb.inc\n")
    f.close()

    # instantiation, test include and overwrite logs
    logger = test_logger()
    cfg    = sr_config(config="aaa")
    cfg.logger = logger
    cfg.configure()

    if not cfg.randomize :
       cfg.logger.error("test 01 : problem with include")
       failed = True

    # back to defaults + check isTrue
    cfg.defaults()
    if not cfg.isTrue('true') or cfg.isTrue('false') :
       cfg.logger.error("test 02: problem with module isTrue")
       failed = True

    # pluggin script checking
    f = open("./scrpt.py","w")
    f.write("class Transformer(object): \n")
    f.write("      def __init__(self):\n")
    f.write("          pass\n")
    f.write("\n")
    f.write("      def perform(self,parent):\n")
    f.write("          if parent.this_value != 0 : return False\n")
    f.write("          parent.this_value = 1\n")
    f.write("          return True\n")
    f.write("\n")
    f.write("transformer = Transformer()\n")
    f.write("self.on_message = transformer.perform\n")
    f.close()

    # able to find the script
    ok, path = cfg.config_path("plugins","scrpt.py",mandatory=True,ctype='py')
    if not ok :
       cfg.logger.error("test 03: problem with config_path script not found")
       failed = True
 
    # able to load the script
    cfg.execfile("on_message",path)
    if cfg.on_message == None :
       cfg.logger.error("test 04: problem with module execfile script not loaded")
       failed = True

    # able to run the script
    cfg.this_value = 0
    cfg.on_message(cfg)
    if cfg.this_value != 1 :
       cfg.logger.error("test 05: problem to run the script ")
       failed = True
    os.unlink("./scrpt.py")

    # general ... 

    cfg.general()
    cfg.logger.info(cfg.user_cache_dir)
    cfg.logger.info(cfg.user_log_dir)    
    cfg.logger.info(cfg.user_config_dir)

    # args ... 

    cfg.randomize = False
    cfg.assemble  = False
    cfg.logrotate = 5
    cfg.expire      = 0
    expire_value    = 1000*60*60*3
    message_value   = 1000*60*60*24*7*3
    cfg.message_ttl = 0
    cfg.args(['-expire','3h','-message_ttl','3W','--randomize', '--assemble', 'True',  '-logrotate', '10'])
    if not cfg.randomize :
       cfg.logger.error("test 06: args problem randomize")
       failed = True
    if not cfg.inplace  :
       cfg.logger.error("test 07: args problem assemble")
       failed = True
    if cfg.logrotate !=10 :
       cfg.logger.error("test 08: args problem logrotate %s" % cfg.logrotate)
       failed = True
    if cfg.expire != expire_value :
       cfg.logger.error("test 09: args problem expire %s" % cfg.expire)
       failed = True
    if cfg.message_ttl != message_value :
       cfg.logger.error("test 10: args problem message_ttl %s" % cfg.message_ttl)
       failed = True


    # has_vip... 
    cfg.args(['-vip', '127.0.0.1' ])
    if not cfg.has_vip():
       cfg.logger.error("test 11: has_vip failed")
       failed = True


    opt1 = "hostname toto"
    opt2 = "broker amqp://a:b@${HOSTNAME}"
    cfg.option(opt1.split())
    cfg.option(opt2.split())
    if cfg.broker.geturl() != "amqp://a:b@toto" :
       cfg.logger.error("test 12: varsub problem with replacing HOSTNAME")
       failed = True

    opt1 = "parts i,128"
    cfg.option(opt1.split())
    if cfg.partflg != 'i' or cfg.blocksize != 128:
       cfg.logger.error("test 13: option parts or module validate_parts")
       failed = True

    opt1 = "sum z,d"
    cfg.option(opt1.split())
    if cfg.sumflg != 'z,d' :
       cfg.logger.error("test 14: option sum or module validate_sum")
       failed = True

    opt1 = "sum R,0"
    cfg.option(opt1.split())
    if cfg.sumflg != 'R,0' :
       cfg.logger.error("test 15: option sum or module validate_sum")
       failed = True

    opt1 = "sum d"
    cfg.option(opt1.split())
    if cfg.sumflg != 'd' or type(cfg.sumalgo) != checksum_d :
       cfg.logger.error("test 16: option sum or module validate_sum")
       failed = True

    opt1 = "sum 0"
    cfg.option(opt1.split())
    if cfg.sumflg != '0' or type(cfg.sumalgo) != checksum_0 :
       cfg.logger.error("test 17: option sum or module validate_sum")
       failed = True

    opt1 = "sum n"
    cfg.option(opt1.split())
    if cfg.sumflg != 'n' or type(cfg.sumalgo) != checksum_n :
       cfg.logger.error("test 18: option sum or module validate_sum")
       failed = True

    opt1 = "sum s"
    cfg.option(opt1.split())
    if cfg.sumflg != 's' or type(cfg.sumalgo) != checksum_s :
       cfg.logger.error("test 19: option sum or module validate_sum")
       failed = True

    opt1 = "move toto titi"
    cfg.option(opt1.split())
    if cfg.movepath[0] != 'toto' or cfg.movepath[1] != 'titi' :
       cfg.logger.error("test 20: option move for sr_post does not work")
       failed = True

    opt1 = "path .. ."
    cfg.option(opt1.split())
    if cfg.postpath[0] != os.path.abspath('..') or cfg.postpath[1] != os.path.abspath('.') :
       cfg.logger.error("test 21: option path for sr_post does not work")
       failed = True

    opt1 = "inflight ."
    cfg.option(opt1.split())
    if cfg.inflight != '.' :
       cfg.logger.error("test 22: option inflight . does not work")
       failed = True

    opt1 = "inflight .tmp"
    cfg.option(opt1.split())
    if cfg.inflight != '.tmp' :
       cfg.logger.error("test 23: option inflight .tmp does not work")
       failed = True

    opt1 = "inflight 1.5"
    cfg.option(opt1.split())
    if cfg.inflight != 1.5 :
       cfg.logger.error("test 24: option inflight 1.5  does not work")
       failed = True

    opt1 = "prefetch 10"
    cfg.option(opt1.split())
    if cfg.prefetch != 10 :
       cfg.logger.error("test 25: prefetch option did not work")
       failed = True

    # reexecuting the config aaa.conf

    cfg.logger.debug("test 25b: reparsing aaa.conf that includes bbb.inc")
    cfg.config(cfg.user_config)
    os.unlink('aaa.conf')
    os.unlink('bbb.inc')
    cfg.logger.debug("test 25b: worked")

    opt1 = "header toto1=titi1"
    cfg.option(opt1.split())
    opt2 = "header toto2=titi2"
    cfg.option(opt2.split())
    opt3 = "header tutu1=None"
    cfg.option(opt3.split())
    opt4 = "header tutu2=None"
    cfg.option(opt4.split())

    if not 'toto1' in cfg.headers_to_add      or \
       not 'toto2' in cfg.headers_to_add      or \
       cfg.headers_to_add['toto1'] != 'titi1' or \
       cfg.headers_to_add['toto2'] != 'titi2' or \
       len(cfg.headers_to_add)     != 2 :
       cfg.logger.error("test 26: option header adding entries did not work")
       failed = True

    if not 'tutu1' in cfg.headers_to_del      or \
       not 'tutu2' in cfg.headers_to_del      or \
       len(cfg.headers_to_del)     != 2 :
       cfg.logger.error("test 27: option header deleting entries did not work")
       failed = True

    # expire in ms
    opt4 = "expire 10m"
    cfg.option(opt4.split())
    if cfg.expire != 600000 :
       cfg.logger.error("test 28: option expire or module duration_from_str did not work")
       failed = True

    # message_ttl in ms
    opt4 = "message_ttl 20m"
    cfg.option(opt4.split())
    if cfg.message_ttl != 1200000 :
       cfg.logger.error("test 29: option message_ttl or module duration_from_str did not work")
       failed = True

    opt4="directory ${MAIL}/${USER}/${SHELL}/blabla"
    cfg.option(opt4.split())
    if '$' in cfg.currentDir:
       cfg.logger.error("test 30: env variable substitution failed %s" % cfg.currentDir)
       failed = True

    opt4='strip 4'
    cfg.option(opt4.split())
    if cfg.strip != 4 :
       cfg.logger.error("test 31: option strip with integer failed")
       failed = True

    opt4='strip .*aaa'
    cfg.option(opt4.split())
    if cfg.pstrip != '.*aaa' :
       cfg.logger.error("test 32: option strip with pattern failed")
       failed = True

    pika = cfg.use_pika

    opt4='use_pika True'
    cfg.option(opt4.split())
    if not cfg.use_pika :
       cfg.logger.error("test 33: option use_pika boolean set to true failed")
       failed = True

    opt4='use_pika False'
    cfg.option(opt4.split())
    if cfg.use_pika :
       cfg.logger.error("test 34: option use_pika boolean set to false failed")
       failed = True

    opt4='use_pika'
    cfg.option(opt4.split())
    if not cfg.use_pika :
       cfg.logger.error("test 35: option use_pika boolean set to true without value failed")
       failed = True

    opt4='statehost False'
    cfg.option(opt4.split())
    if cfg.statehost :
       cfg.logger.error("test 35: option statehost boolean set to false failed")
       failed = True

    opt4='statehost True'
    cfg.option(opt4.split())
    if not cfg.statehost or cfg.hostform != 'short' :
       cfg.logger.error("test 36: option statehost boolean set to true, hostform short, failed")
       failed = True

    opt4='statehost SHORT'
    cfg.option(opt4.split())
    if not cfg.statehost or cfg.hostform != 'short' :
       cfg.logger.error("test 37: option statehost set to SHORT, hostform short, failed")
       failed = True

    opt4='statehost fqdn'
    cfg.option(opt4.split())
    if not cfg.statehost or cfg.hostform != 'fqdn' :
       cfg.logger.error("test 38: option statehost set to fqdn, hostform fqdn, failed")
       failed = True

    opt4='statehost TOTO'
    cfg.option(opt4.split())
    if cfg.statehost and cfg.hostform != None:
       cfg.logger.error("test 39: option statehost set badly ... did not react correctly, failed")
       failed = True

    # extended options 

    opt4='extended TOTO'
    cfg.option(opt4.split())

    cfg.declare_option('extended')
    if not cfg.check_extended():
       cfg.logger.error("test 40: extend with new option, option was declared, but check_extended complained(False)")
       failed = True

    opt4='extended_bad TITI'
    cfg.option(opt4.split())
    if cfg.check_extended():
       cfg.logger.error("test 41: extend with new option, option not declared, but check_extended said ok (True)")
       failed = True

    opt1 = "surplus_opt surplus_value"
    cfg.option(opt1.split())
    if cfg.surplus_opt != [ "surplus_value" ] :
       cfg.logger.error("test 42: extend option did not work")
       failed = True

    opt1 = "surplus_opt surplus_value2"
    cfg.option(opt1.split())
    if cfg.surplus_opt[0] != "surplus_value" or cfg.surplus_opt[1] != "surplus_value2":
       cfg.logger.error("test 43: extend option list did not work")
       failed = True

    # more options testing

    opt1 = "base_dir /home/aspymjg/dev/metpx-sarracenia/sarra"
    cfg.option(opt1.split())
    if cfg.base_dir != '/home/aspymjg/dev/metpx-sarracenia/sarra':
       cfg.logger.error("test 44: string option base_dir did not work")
       failed = True

    opt1 = "post_base_dir /totot/toto"
    cfg.option(opt1.split())
    if cfg.post_base_dir != '/totot/toto':
       cfg.logger.error("test 45: string option post_base_dir did not work")
       failed = True

    opt1 = "post_base_url file://toto"
    cfg.option(opt1.split())
    if cfg.post_base_url != 'file://toto':
       cfg.logger.error("test 46: url option post_base_url did not work")
       failed = True

    if cfg.outlet != 'post' :
       cfg.logger.error("test 47: default error outlet = %s" % self.outlet)
       failed = True

    opt1 = "outlet json"
    cfg.option(opt1.split())
    if cfg.outlet != 'json' :
       cfg.logger.error("test 48: option outlet value json did not work")
       failed = True

    opt1 = "outlet url"
    cfg.option(opt1.split())
    if cfg.outlet != 'url' :
       cfg.logger.error("test 49: option outlet value url did not work")
       failed = True

    opt1 = "outlet post"
    cfg.option(opt1.split())
    if cfg.outlet != 'post' :
       cfg.logger.error("test 50: option outlet value post did not work")
       failed = True

    opt1 = "outlet toto"
    cfg.option(opt1.split())
    if cfg.outlet != 'post' :
       cfg.logger.error("test 51: option outlet with bad value did not work")
       failed = True

    if not cfg.retry_mode :
       cfg.logger.error("test 52: retry_mode should be the default")
       failed = True

    opt1 = "retry_mode false"
    cfg.option(opt1.split())
    if cfg.retry_mode :
       cfg.logger.error("test 53: retry_mode should be false")
       failed = True

    # retry_ttl in mins 
    opt1 = "retry_ttl 1D"
    cfg.option(opt1.split())
    if cfg.retry_ttl != 86400 :
       cfg.logger.error("test 54: option retry_ttl or module duration_from_str did not work")
       failed = True

    # exchange_suffix
    opt1 = "exchange_suffix suffix1"
    cfg.option(opt1.split())
    opt1 = "post_exchange_suffix suffix2"
    cfg.option(opt1.split())
    if cfg.exchange_suffix != 'suffix1' or cfg.post_exchange_suffix != 'suffix2' :
       cfg.logger.error("test 55: option exchange_suffix or post_exchange_suffix did not work")
       failed = True

    # internal variables substitution

    opt1 = "broker amqp://michel:passwd@testbroker.toto"
    cfg.option(opt1.split())
    opt1 = "post_base_dir /${broker.hostname}/${broker.username}"
    cfg.option(opt1.split())
    if cfg.post_base_dir != '/testbroker.toto/michel':
       cfg.logger.error("test 56: replacing internal ${broker.hostname} ${broker.username} did not work")
       failed = True

    cfg.toto = ['tutu1','tutu2']
    opt1 = "post_base_dir /${toto[1]}/${broker.username}/aaa"
    cfg.option(opt1.split())
    if cfg.post_base_dir != '/tutu2/michel/aaa':
       cfg.logger.error("test 57: replacing internal ${toto[1]} did not work")
       failed = True

    cfg.toto = ['tutu1','tutu2']
    opt1 = "post_base_dir /${toto}/${broker.username}/aaa"
    cfg.option(opt1.split())
    if cfg.post_base_dir != '/tutu1/michel/aaa':
       cfg.logger.error("test 58: replacing internal ${toto} did not work")
       failed = True

    # more config test to perform for full coverage... 
    #def isMatchingPattern(self, str, accept_unmatch = False): 
    #def sundew_dirPattern(self,basename,destDir,destName) :
    #def sundew_getDestInfos(self, filename):
    #def validate_urlstr(self,urlstr):


    if not failed :
                    print("%s TEST PASSED" % sys.argv[0])
    else :          
                    print("%s TEST FAILED" % sys.argv[0])
                    sys.exit(1)


# ===================================
# MAIN
# ===================================

def main():

    try:    self_test()
    except: 
            (stype, svalue, tb) = sys.exc_info()
            print("%s, Value: %s" % (stype, svalue))
            print("%s TEST FAILED" % sys.argv[0])
            sys.exit(1)

    sys.exit(0)

# =========================================
# direct invocation : self testing
# =========================================

if __name__=="__main__":
   main()
