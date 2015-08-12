#!/usr/bin/python3

import os,sys,time

try :    
         from dd_amqp           import *
         from dd_config         import *
         from dd_transfert      import *
         from dd_util           import *
except : 
         from sara.dd_amqp      import *
         from sara.dd_config    import *
         from sara.dd_transfert import *
         from sara.dd_util      import *

class dd_sara(dd_config):

    def __init__(self,logger,config=None,args=None):

        self.logger = logger
        self.conf   = config

        self.defaults()
        self.config(config)
        self.args(args)

        self.check()

    def check(self):

        self.destination.set(self.destination.get())
        if not self.destination.protocol in ['amqp','amqps'] or \
           self.destination.user     == None   or \
           self.destination.password == None   or \
           self.destination.error :
           self.logger.error("destination url %s " % self.destination.get())

        self.source.set(self.source.get())
        if not self.source.protocol in ['amqp','amqps'] or \
           self.source.user     == None   or \
           self.source.password == None   or \
           self.source.error :
           self.logger.error("source url %s " % self.source.get())

        self.download.set_clustered(self.clustered)
        self.download.set_recompute(self.recompute_chksum)

    def defaults(self):

        self.str_flags   = 'd'
        self.blocksize   = 0
        self.tag         = 'default'
        self.instances   = 0
        self.randomize   = False
        self.strip       = 0
        self.basedir     = ''
        self.source      = URL()
        self.destination = URL()
        self.post        = URL()

        self.source.protocol = 'amqp'
        self.source.host     = 'localhost'
        self.source.user     = 'guest'
        self.source.password = 'guest'
        self.src_exchange    = 'sx_guest'

        self.destination.protocol = 'amqp'
        self.destination.host     = 'localhost'
        self.destination.user     = 'guest'
        self.destination.password = 'guest'
        self.dest_exchange        = 'xpublic'
        self.dest_path            = None

        self.exchange_type = 'topic'
        self.exchange_key  = []

        self.flags       = Flags()
        self.flags.from_str(self.str_flags)

        self.recompute_chksum = False
        self.clustered        = False

        # download class

        self.download = dd_download(self.logger)


    def close(self):
        self.hc_src.close()
        self.hc_dst.close()

    def connect(self):

        # =============
        # consumer
        # =============

        # consumer host

        self.hc_src = HostConnect( self.source.host, self.source.port, \
                                   self.source.user,self.source.password, \
                                   ssl= self.source.protocol == 'amqps', logger = self.logger, loop=True)
        self.hc_src.connect()

        # consumer 

        self.consumer  = Consumer(self.hc_src)
        self.consumer.add_prefetch(1)
        self.consumer.build()

        # consumer exchange : make sure it exists
        ex = Exchange(self.hc_src,self.src_exchange)
        ex.build()

        # consumer queue

        key   = self.exchange_key[0]
        if key[-2:] == '.#' : key = key[:-2]
        name  = 'cmc.dd_sara' + '.' + self.conf + '.' + self.src_exchange + '.' + key
        self.queue = Queue(self.hc_src,name)
        self.queue.add_binding(self.src_exchange,self.exchange_key[0])
        self.queue.build()

        # log publisher

        self.log    = Publisher(self.hc_src)
        self.log.build()

        # log exchange : make sure it exists

        xlog = Exchange(self.hc_src,'log')
        xlog.build()

        # =============
        # publisher
        # =============

        # publisher host

        self.hc_dst = HostConnect( self.destination.host, self.destination.port, \
                                   self.destination.user, self.destination.password, \
                                   ssl= self.destination.protocol == 'amqps', logger = self.logger, loop=True)
        self.hc_dst.connect()

        # publisher

        self.pub    = Publisher(self.hc_dst)
        self.pub.build()

        # publisher exchange : make sure it exists

        xpub = Exchange(self.hc_dst,self.dest_exchange)
        xpub.build()

    def run(self):

        #
        # loop on all message
        #
        while True :

          try  :
                 msg = self.consumer.consume(self.queue.qname)
                 if msg == None : continue

                 # restoring all info from amqp message

                 body     = msg.body
                 exchange = msg.delivery_info['exchange']
                 str_key  = msg.delivery_info['routing_key']
                 hdr      = msg.properties['application_headers']
                 filename = hdr['filename']

                 if type(body) == bytes : body = body.decode("utf-8")

                 self.logger.info('Receiving: %s',str_key)
                 self.logger.info('Receiving: %s',body)

                 # instanciate key and notice

                 dkey    = Key()
                 notice  = Notice()
                 new_key = str_key

                 if str_key[:3] == 'v01':
                    dkey.from_key(str_key) 
                    notice.from_notice(body)
                 else :
                    dkey.from_v00_key(str_key,self.source.user) 
                    notice.from_v00_notice(body)
                    new_key = dkey.get()
                    body    = notice.get()


                 # message validation

                 #ok = validator.vscript( body, logger )
                 ok = True

                 if notice.url[:4] != 'http' and notice.url[:4] != 'sftp' : ok = False

                 if not ok :
                    log_key = new_key.replace('.post.','.log.')
                    self.logger.error('Not valid: %s',body)
                    body   += ' 404 ' + socket.gethostname() + ' ' + self.source.user + ' 0.0'
                    self.log.publish('log',log_key,body,filename)
                    self.consumer.ack(msg)
                    continue

                 # Target file and directory (directory created if needed)

                 target_file = self.basedir + '/' + notice.dpath
                 if exchange[:3] == 'sx_' or str_key[:4] == 'v00.' :
                    today = time.strftime("%Y%m%d",time.gmtime())
                    target_file = self.basedir + \
                                   '/' + today + \
                                   '/' + self.source.user + \
                                   '/' + notice.dpath

                 target_file = target_file.replace('//','/')
                 target_dir  = target_file.replace(notice.dfile,'')
                 try    : os.umask(0)
                 except : pass
                 try    : os.makedirs(target_dir,0o775,True)
                 except : pass

                 # download setup

                 #dkey.lpath = notice.dpath

                 dnotice = Notice()
                 dnotice.from_notice(body)
                 dnotice.source = self.post.get()
                 dnotice.lpath  = target_file.replace(self.basedir + '/','')

                 self.download.set_key(dkey)
                 self.download.set_notice(dnotice)
                 self.download.set_publish(self.pub,self.log)

                 self.download.set_url(notice.url)
                 self.download.set_local_file(target_file)
                 self.download.get(notice.chunksize, notice.block_count, notice.remainder, notice.current_block, notice.str_flags,notice.data_sum)
                 self.consumer.ack(msg)

          except :
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))


# ===================================
# default validation: notification always ok
# ===================================

import logging

def validate_ok( body, logger ):
    valid = True

    logger.debug("validate_ok")

    return valid

class Validator():
      def __init__(self):
          pass

validator         = Validator()
validator.vscript = validate_ok

logdir = None

# ===================================
# MAIN
# ===================================

def main():

    LOG_FORMAT = ('%(asctime)s [%(levelname)s] %(message)s')

    if logdir == None :
       logger = logging.getLogger(__name__)
       logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    # user wants to logging in a directory/file
    else :
       fn     = 'dd_sara'
       lfn    = fn + '_' + sys.argv[1] + "_%s" % os.getpid() + ".log"
       lfile  = logdir + os.sep + lfn

       # Standard error is redirected in the log
       sys.stderr = open(lfile, 'a')

       # python logging
       logger = None
       fmt    = logging.Formatter( LOG_FORMAT )
       hdlr   = logging.handlers.TimedRotatingFileHandler(lfile, when='midnight', interval=1, backupCount=5)
       hdlr.setFormatter(fmt)
       logger = logging.getLogger(lfn)
       logger.setLevel(logging.INFO)
       logger.addHandler(hdlr)


    try :
              sara = dd_sara(logger,config=sys.argv[1],args=sys.argv)

              if sara.instances <= 1 :
                 sara.connect()
                 sara.run()
                 sara.close()

    except :  logger.error("Config file incorrect")

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()

