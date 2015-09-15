#!/usr/bin/python3

import os,sys,time

try :    
         from dd_amqp           import *
         from dd_http           import *
         from dd_instances      import *
         from dd_message        import *
         from dd_sftp           import *
         from dd_util           import *
except : 
         from sara.dd_amqp      import *
         from sara.dd_http      import *
         from sara.dd_instances import *
         from sara.dd_message   import *
         from sara.dd_sftp      import *
         from sara.dd_util      import *

class dd_sara(dd_instances):

    def __init__(self,config=None,args=None):
        dd_instances.__init__(self,config,args)
        self.defaults()
        self.exchange = 'xpublic'
        self.configure()

    def check(self):

        # dont want to recreate these if they exists

        if not hasattr(self,'imsg') :
           self.imsg = dd_message(self.logger)

        # umask change for directory creation and chmod

        try    : os.umask(0)
        except : pass

    def close(self):
        self.hc_src.close()
        self.hc_pst.close()

    def connect(self):

        # =============
        # consumer
        # =============

        # consumer host

        self.hc_src = HostConnect( logger = self.logger )
        self.hc_src.set_url( self.source_broker )
        self.hc_src.connect()

        # consumer  add_prefetch(1) allows queue sharing between instances

        self.consumer  = Consumer(self.hc_src)
        self.consumer.add_prefetch(1)
        self.consumer.build()

        # consumer exchange : make sure it exists
        ex = Exchange(self.hc_src,self.source_exchange)
        ex.build()

        # consumer queue

        # OPTION ON QUEUE NAME ?
        name  = 'cmc.' + self.program_name + '.' + self.config_name
        if self.queue_name != None :
           name = self.queue_name

        self.queue = Queue(self.hc_src,name)
        self.queue.add_binding(self.source_exchange,self.source_topic)
        self.queue.build()

        # log publisher

        self.log    = Publisher(self.hc_src)
        self.log.build()

        # log exchange : make sure it exists

        xlog = Exchange(self.hc_src,'xlog')
        xlog.build()

        # =============
        # publisher
        # =============

        # publisher host

        self.hc_pst = HostConnect( logger = self.logger )
        self.hc_pst.set_url( self.broker )
        self.hc_pst.connect()

        # publisher

        self.pub    = Publisher(self.hc_pst)
        self.pub.build()

        # publisher exchange : make sure it exists

        xpub = Exchange(self.hc_pst,self.exchange)
        xpub.build()

    def configure(self):

        # arguments from command line

        self.args(self.user_args)

        # config from file

        self.config(self.user_config)

        # verify all settings

        self.check()

        self.setlog()

    def delete_event(self):
        ok      = False
        code    = 503
        message = "Service unavailable : %s " % delete
        self.dual_log(ok,code,message)

    def help(self):
        self.logger.info("Usage: %s [OPTIONS] configfile [start|stop|restart|reload|status]\n" % self.program_name )
        self.logger.info("OPTIONS:")
        self.logger.info("-i   <nbr_of_instances>      default 1")
        self.logger.info("-b   <broker>                default amqp://guest:guest@localhost/")
        self.logger.info("-dr  <document_root>")
        self.logger.info("-ex  <exchange>              default amq.topic")
        self.logger.info("-u   <url>")
        self.logger.info("-sb  <source_broker>         default amqp://guest:guest@localhost/")
        self.logger.info("-se  <source_exchange>       default amq.topic")
        self.logger.info("-st  <source_topic>          default v02.post.#")
        self.logger.info("-qn  <queue_name>            default dd_sara.config_name")
        self.logger.info("-ms  <message_validation_script>")
        self.logger.info("-fs  <file_validation_script>")
        self.logger.info("-sk  <ssh_keyfile>")
        self.logger.info("-strip <strip count (directory)>")
        self.logger.info("-in  <put parts inplace>      default True")
        self.logger.info("-o   <overwrite no sum check> default True")
        self.logger.info("-rc  <recompute sun>          default False")
        self.logger.info("DEBUG:")
        self.logger.info("-debug")

    def dual_log(self,ok,code,message):
        print_severity = self.logger.info
        if not ok : print_severity = self.logger.error

        self.imsg.log(code,message)
        print_severity('(%d,%s): %s %s %s',code,message,self.imsg.topic,self.imsg.notice,self.imsg.hdrstr)
        self.log.publish(self.imsg.log_exchange,self.imsg.log_topic,self.imsg.log_notice,self.imsg.log_headers)

    def insert_file(self,part_file):
        try :
                 bufsize = 10 * 1024 * 1024
                 fp = open(part_file,'rb')
                 ft = open(self.imsg.target_file,'r+b')
                 ft.seek(self.imsg.offset,0)

                 i  = 0
                 while i<self.imsg.length :
                       buf = fp.read(bufsize)
                       ft.write(buf)
                       i  += len(buf)

                 ft.close()
                 fp.close()

                 os.unlink(part_file)

                 return True,201,'Created (Inserted)'

        except :
                 (stype, svalue, tb) = sys.exc_info()
                 return False,499,svalue

        return False,499,'Unknown'

    def insert_from_parts(self):

        if not os.path.isfile(self.imsg.target_file) : return
        lstat   = os.stat(self.imsg.target_file)
        fsiz    = lstat[stat.ST_SIZE] 
        i       = int(fsiz /self.imsg.chunksize)


        while i < self.imsg.block_count:
              self.imsg.current_block = i
              partstr = '%s,%d,%d,%d,%d' %\
                        ('i',self.imsg.chunksize,self.imsg.block_count,self.imsg.remainder,self.imsg.current_block)
              self.imsg.set_parts_str(partstr)
              self.imsg.set_suffix()

              part_file = self.imsg.target_file + self.imsg.suffix
              if not os.path.isfile(part_file) : return

              lstat   = os.stat(self.imsg.target_file)
              fsiz    = lstat[stat.ST_SIZE] 
              if self.imsg.offset > fsiz : return
 
              # special locking insert... try avoid race condition
              part_file_lck = part_file + '.lck_ins'
              if os.path.isfile(part_file_lck) : return
              try :    os.link(part_file,part_file_lck)
              except : return
              try :    os.unlink(part_file)
              except : pass

              ok,code,message = self.insert_file(part_file_lck)
              self.dual_log(ok,code,message)
              if not ok : return

              self.imsg.set_exchange(self.exchange)
              self.imsg.set_topic_url('v02.post',self.imsg.target_url)
              self.imsg.set_notice(self.imsg.target_url,self.imsg.time)
              self.imsg.rename  = None
              self.imsg.message = None
              self.imsg.set_headers()
              self.pub.publish(self.imsg.exchange,self.imsg.topic,self.imsg.notice,self.imsg.headers)
              self.dual_log(True,201,'Created (Published)')

              i = i + 1

        self.lastchunk()

    def lastchunk(self):
        if self.imsg.partflg == '1': return
        if not self.inplace        : return
        if not self.lastchunk      : return

        try :
                 lstat   = os.stat(self.imsg.target_file)
                 fsiz    = lstat[stat.ST_SIZE] 

                 if fsiz > self.imsg.filesize :
                    fp = open(self.imsg.target_file,'r+b')
                    fp.truncate(self.imsg.filesize)
                    fp.close()
                    self.dual_log(True,205,'Reset Content %s' % 'truncated')
                 elif fsiz < self.imsg.filesize :
                    self.dual_log(False,411,'Length Requiered %s' % 'file too small')

        except : pass

    def set_local(self):

        # relative path

        yyyymmdd = time.strftime("%Y%m%d",time.gmtime())
        self.rel_path = '%s/%s/%s' % (yyyymmdd,self.imsg.source,self.imsg.path)
        if self.imsg.rename != None :
           self.rel_path = '%s/%s/%s' % (yyyymmdd,self.imsg.source,self.imsg.rename)
           self.rel_path = self.rel_path.replace('//','/')

        token = self.rel_path.split('/')
        self.filename = token[-1]

        if self.strip > 0 :
           if self.strip > len(token) : token = [token[-1]]
           else :                       token = token[self.strip:]
           self.rel_path = '/'.join(token)

        self.local_dir  = ''
        if self.document_root != None :
           self.local_dir = self.document_root 
        if len(token) > 1 :
           self.local_dir = self.local_dir + '/' + '/'.join(token[:-1])

        # Local directory (directory created if needed)

        self.local_dir  = self.local_dir.replace('//','/')
        self.local_file = self.local_dir   + '/' + self.filename
        self.local_url  = urllib.parse.urlparse(self.url.geturl() + '/' + self.rel_path)

    def validate_file(self,target_file, offset, length):

        if self.file_script == None : return True

        ok, code, message = self.file_script(target_file, offset, length)

        if not ok : self.dual_log(ok,code,message)

        return ok

    def validate_message(self):

        if self.msg_script == None : return True

        ok, code, message = self.msg_script(self.imsg)

        if not ok : self.dual_log(ok,code,message)

        return ok


    def run(self):

        self.logger.info("dd_sara run")

        self.connect()

        self.imsg.logger = self.logger

        #
        # loop on all message
        #
        while True :

          try  :
                 msg = self.consumer.consume(self.queue.qname)
                 if msg == None : continue

                 # make use it as a dd_message

                 self.imsg.from_amqplib(msg)
                 self.logger.info("Received %s '%s' %s" % (self.imsg.topic,self.imsg.notice,self.imsg.hdrstr))

                 # testing purpose
                 if self.sleep > 0 :
                    self.logger.info("Sleeping %d" % self.sleep)
                    time.sleep(self.sleep)

                 # message validation

                 ok = self.validate_message()
                 if not ok :
                    self.consumer.ack(msg)
                    continue

                 # set local file :  dr + imsg.path (renamed path)

                 self.set_local()

                 self.imsg.set_local(self.inplace,self.local_file,self.local_url)

                 # asked to delete ?

                 if self.imsg.event == 'IN_DELETE' :
                    self.delete_event()
                    self.consumer.ack(msg)
                    continue

                 # make sure local directory exists
                 # FIXME : logging errors...
                 try    : os.makedirs(self.local_dir,0o775,True)
                 except : pass

                 # if overwrite is not enforced (False)
                 # verify if msg checksum and local_file checksum match
                 # FIXME : should we republish / repost ???

                 if not self.overwrite :
                    if  self.imsg.checksum_match() :
                        self.dual_log(True,304,'not modified')
                        self.lastchunk()
                        self.consumer.ack(msg)
                        continue

                 # another race condition : lock writing so the part is not inserted when unfinished

                 if self.inplace and self.imsg.in_partfile :
                    self.imsg.local_lock('.lck_wrt')

                 # proceed to download
                 i = 0
                 ok,code,message = False,503,"unable to download"
                 while  i < 3 : 

                      try :
                           if   self.imsg.url.scheme == 'http' :
                                ok,code,message = http_download(self.imsg, self.user, self.password )
                                break
                           elif self.imsg.url.scheme == 'sftp' :
                                ok,code,message = sftp_download(self.imsg, self.user, self.password, self.ssh_keyfile )
                                break
                           elif self.imsg.url.scheme == 'file' :
                                fp = open(self.imsg.url.path,'rb')
                                if self.imsg.partflg == 'i' : fp.seek(self.imsg.offset,0)
                                write_to_file(self,fp, self.imsg.local_file, self.imsg.local_offset, self.imsg.length )
                                fp.close()
                                ok,code,message = True,201,'Created (copied)'
                                break
                           else :
                                ok,code,message = False,503,"Service unavailable %s" % self.imsg.url.scheme
                                break
                      except :
                           (stype, svalue, tb) = sys.exc_info()
                           self.logger.error("Download  Type: %s, Value: %s,  ..." % (stype, svalue))

                      i = i + 1

                   
                 self.dual_log(ok,code,message)
                 if not ok :
                    self.consumer.ack(msg)
                    continue

                 # validate file/data
                 ok = self.validate_file(self.imsg.local_file, self.imsg.local_offset, self.imsg.length)
                 if not ok :
                    self.consumer.ack(msg)
                    continue

                 # force recompute checksum

                 if self.recompute_chksum :
                    self.imsg.compute_local_checksum()
                    if not self.imsg.local_checksum == self.imsg.checksum :
                       self.imsg.set_sum(self.imsg.sumflg,self.imsg.local_checksum)
                       self.imsg.checksum = self.imsg.local_checksum
                       self.dual_log(True,205,'Reset Content : checksum')


                 # if mode is inplace and we downloaded in part file...
                 # unlock + log temporary redirection + attempt to insert

                 if self.inplace and self.imsg.in_partfile :
                    lock = self.imsg.local_file
                    self.imsg.local_unlock()
                    orig = self.imsg.local_file
                    try    : os.unlink(orig)
                    except : pass
                    try    : os.link(lock,orig)
                    except : return
                    try    : os.unlink(lock)
                    except : pass
                    self.dual_log(True,307,'Temporary Redirect')

                    # try inserting it... conditions may have changed since writing

                    self.insert_from_parts()

                    self.consumer.ack(msg)
                    continue

                 # announcing the download

                 if self.imsg.partflg != 1 :
                    if self.inplace : self.imsg.change_partflg('i')
                    else            : self.imsg.change_partflg('p')

                 self.imsg.set_exchange(self.exchange)
                 self.imsg.set_topic_url('v02.post',self.imsg.local_url)
                 self.imsg.set_notice(self.imsg.local_url,self.imsg.time)
                 self.imsg.rename  = None
                 self.imsg.message = None
                 self.imsg.set_headers()
                 self.pub.publish(self.imsg.exchange,self.imsg.topic,self.imsg.notice,self.imsg.headers)
                 self.dual_log(True,201,'Created (Published)')

                 # if we inserted a part in file ... perhaps others are ready

                 if self.inplace :
                    self.insert_from_parts()

                 self.consumer.ack(msg)

          except :
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
                 self.consumer.ack(msg)

    def reload(self):
        self.logger.info("dd_sara reload")
        self.close()
        self.configure()
        self.run()

    def start(self):
        self.configure()
        self.logger.info("dd_sara start")
        self.run()

    def stop(self):
        self.logger.info("dd_sara stop")
        self.close()
        os._exit(0)


# ===================================
# MAIN
# ===================================

def main():

    action = None
    args   = None
    config = None

    if len(sys.argv) >= 3 :
       action = sys.argv[-1]
       config = sys.argv[-2]
       if len(sys.argv) > 3: args = sys.argv[1:-2]

    sara = dd_sara(config,args)

    if   action == 'reload' : sara.reload_parent()
    elif action == 'restart': sara.restart_parent()
    elif action == 'start'  : sara.start_parent()
    elif action == 'stop'   : sara.stop_parent()
    elif action == 'status' : sara.status_parent()
    else :
           sara.logger.error("action unknown %s" % action)
           sys.exit(1)

    sys.exit(0)



# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
