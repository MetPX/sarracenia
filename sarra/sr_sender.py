#!/usr/bin/python3

import os,sys,time
import paramiko
from   paramiko import *

try :    
         from sr_amqp           import *
         from sr_config         import *
         from sr_transfert      import *
         from sr_util           import *
except : 
         from sarra.sr_amqp      import *
         from sarra.sr_config    import *
         from sarra.sr_transfert import *
         from sarra.sr_util      import *

class sr_sender(sr_config):

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

    def defaults(self):

        self.str_flags   = 'd'
        self.blocksize   = 0
        self.tag         = 'default'
        self.randomize   = False
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

        self.transmission  = URL()
        self.trx_basedir   = ''
        self.user          = None
        self.password      = None
        self.ssh_keyfile   = None
        self.lock          = None

        self.exchange_type = 'topic'
        self.exchange_key  = []

        self.flags       = Flags()
        self.flags.from_str(self.str_flags)

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
        name  = 'cmc.sr_sender' + '.' + self.conf + '.' + self.src_exchange + '.' + key
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

    def get_elapse(self):
        return time.time()-self.tbegin

    def run(self):

        #
        # loop on all message
        #
        while True :

          try  :
                 msg = self.consumer.consume(self.queue.qname)
                 if msg == None : continue
                 self.start_timer()

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


                 # local file
                 local_file = self.basedir + '/' + notice.dpath
                 if not os.path.isfile(local_file) :
                    self.logger.error("file notified but not present %s" % local_file)
                    self.consumer.ack(msg)
                    continue
                    

                 # Target file

                 target_file = self.trx_basedir + '/' + notice.dpath
                 if exchange[:3] == 'sx_' or str_key[:4] == 'v00.' :
                    today = time.strftime("%Y%m%d",time.gmtime())
                    target_file = self.trx_basedir + \
                                   '/' + today + \
                                   '/' + self.source.user + \
                                   '/' + notice.dpath

                 target_file = target_file.replace('//','/')
                 target_dir  = target_file.replace(notice.dfile,'')

                 # send product

                 self.send(local_file,target_dir,notice.dfile)

                 # create new notice

                 notice.source = self.post.get()
                 if self.trx_basedir != '' :
                    notice.lpath  = target_file.replace(self.trx_basedir + '/','')

                 # publish and log


                 str_key = dkey.get()
                 body    = notice.get()

                 self.pub.publish(self.dest_exchange,str_key,body,notice.dfile)
                 self.logger.info("Publishes: %s   key      = %s" % ('xpublic',str_key))
                 self.logger.info("Publishes: %s   body     = %s" % ('xpublic',body) )

                 log_key  = str_key.replace('.post.','.log.')
                 body    += ' %d %s %s %f' % (202,socket.gethostname(),self.destination.user,self.get_elapse())
                 self.log.publish('log',log_key,body,'log')

                 self.consumer.ack(msg)

          except :
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))

    def send(self,lfile,tdir,tfile):
        host        = self.transmission.host
        port        = self.transmission.port
        user        = self.transmission.user
        passwd      = self.transmission.password

        ssh_keyfile = self.ssh_keyfile
        if self.user     != None : user   = self.user
        if self.password != None : passwd = self.password

        try :
                self.t = None
                if port == None : 
                   self.t = paramiko.Transport(host)
                else:
                   t_args = (host,port)
                   self.t = paramiko.Transport(t_args)

                if ssh_keyfile != None :
                   key=DSSKey.from_private_key_file(ssh_keyfile,password=None)
                   self.t.connect(username=user,pkey=key)
                else:
                   self.t.connect(username=user,password=passwd)

                self.sftp = paramiko.SFTP.from_transport(self.t)

                # chdir/mkdir
                try    : self.sftp.chdir(tdir)
                except :
                         self.sftp.chdir('/')
                         cwd = ''
                         dirs = tdir.split('/')
                         for d in dirs :
                             cwd = cwd + '/' + d
                             try    : self.sftp.chdir(cwd)
                             except : 
                                      try :
                                               self.sftp.mkdir(cwd,0o755)
                                               self.sftp.chdir(cwd)
                                      except : 
                                               (stype, svalue, tb) = sys.exc_info()
                                               self.logger.error("Type=%s, Value=%s" % (stype, svalue))
                                               self.logger.error("file not delivered %s" % tfile)
                                               return False
                # sending
                lockf = tfile
                if self.lock != None :
                   if self.lock == '.' : lockf = '.' + tfile
                   else                : lockf = tfile + self.lock

                self.sftp.put(lfile,lockf)
                if self.lock != None :  self.sftp.rename(lockf,tfile)

                # close connection
                try    : self.sftp.close()
                except : pass
                try    : self.t.close()
                except : pass

                return True
                
        except:
                (stype, value, tb) = sys.exc_info()
                self.logger.error("Sending failed %s. Type: %s, Value: %s" % (self.transmission.get_nocredential(), stype ,value))

        return False

    def start_timer(self):
        self.tbegin = time.time()
  
    def truncate(self,lfile,l_fsiz,r_fsiz):
        fp = open(lfile,'r+b')
        fp.truncate(r_fsiz)
        fp.close()
        self.logger.info("Truncated: %s (%d to %d)" % (lfile,l_fsiz,r_fsiz) )

    def update(self, lfile, offset, length, fsiz, str_flags, data_sum ):
        lfsiz  = 0

        if not os.path.isfile(lfile) : return True,lfsiz

        lstat  = os.stat(lfile)
        lfsiz  = lstat[stat.ST_SIZE]

        echunk = offset + length - 1
        if echunk >= lfsiz : return True,lfsiz

        ldata_sum = self.checksum(lfile,offset,length)
        if ldata_sum != data_sum : return True,lfsiz
   
        return False,lfsiz
                
    def write_to_file(self,req,lfile,loffset,length) :
        # file should exists
        if not os.path.isfile(lfile) :
           fp = open(lfile,'w')
           fp.close()

        # file open read/modify binary
        fp = open(lfile,'r+b')
        if loffset != 0 : fp.seek(loffset,0)

        nc = int(length/self.bufsize)
        r  = length % self.bufsize

        # loop on bufsize if needed
        i  = 0
        while i < nc :
              chunk = req.read(self.bufsize)
              if len(chunk) != self.bufsize :
                 self.logger.debug('length %d and bufsize = %d' % (len(chunk),self.bufsize))
                 self.logger.error('source data differ from notification... abort')
                 if i > 0 : self.logger.error('product corrupted')
                 return False
              fp.write(chunk)
              i = i + 1

        # remaining
        if r > 0 :
           chunk = req.read(r)
           if len(chunk) != r :
              self.logger.debug('length %d and remainder = %d' % (len(chunk),r))
              self.logger.error('source data differ from notification... abort')
              return False
           fp.write(chunk)

        fp.close()

        return True

    def start_timer(self):
        self.tbegin = time.time()

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

logdir = '/tmp'

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
       fn     = 'sr_sender'
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


    sender = sr_sender(logger,config=sys.argv[1],args=sys.argv)

    sender.connect()

    sender.run()

    sender.close()

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
