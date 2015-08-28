#!/usr/bin/python3

import socket,time,urllib,urllib.parse

class dd_message():

    def __init__(self,logger):
        self.logger        = logger
        self.exchange_name = None
        self.routing_key   = None
        self.notice        = None
        self.headers       = {}

        self.partstr       = None
        self.sumstr        = None
        self.flow          = None
        self.rename        = None
        self.event         = None

    def from_amqplib(self, msg ):

        self.start_timer()

        self.exchange_name      = msg.delivery_info['exchange']
        self.exchange_topic_key = msg.delivery_info['routing_key']
        self.notice             = msg.body
        self.headers            = msg.properties['application_headers']

        if type(msg.body) == bytes :
           self.notice = msg.body.decode("utf-8")

        token        = self.exchange_topic_key.split('.')
        self.version = token[0]

        if self.version == 'v00' :
           self.parse_v00_post()

        if self.version == 'v02' :
           if self.mtype == 'post' : self.parse_v02_post()

    def get_elapse(self):
        return time.time()-self.tbegin

    def log(self, code, message ):
        self.log_exchange_name      = 'log'
        self.log_routing_key        = self.routing_key.replace('.post.','.log.')
        self.log_notice             = "%s %d %s %s %f" % (self.notice,code,socket.gethostname(),self.user,self.get_elapse())
        self.log_headers            = self.headers
        self.log_headers['message'] = message

    def parse_v00_post(self):
        token       = self.exchange_topic_key.split('.')
        self.version = token[0]
        self.mtype   = 'post'
        self.user    = None
        self.kpath   = '.'.join(token[3:])

        token         = self.notice.split(' ')
        self.filename = self.headers['filename']
        self.filesize = int(token[0])
        self.checksum = token[1]
        self.url      = urllib.parse.urlparse(token[2:])
        self.path     = token[3]
        
        self.sumflg   = 'd'
        self.sumstr   = 'd,%s' % self.checksum

        self.chunksize     = self.filesize
        self.block_count   = 1
        self.remainder     = 0
        self.current_block = 0
        self.partflg       = '1'
        self.partstr       = '1,%d' % self.filesize

        self.flow          = None
        self.rename        = None

    def parse_v02_post(self):

        token       = self.exchange_topic_key.split('.')
        self.version = token[0]
        self.mtype   = token[1]
        self.user    = token[2]
        self.kpath   = '.'.join(token[3:])

        token        = self.notice.slit(' ')
        self.time    = token[0]
        self.url     = urllib.parse.urlparse(token[1:])
        self.path    = token[2]
  
        self.flow    = None
        self.rename  = None
        self.partstr = None
        self.sumstr  = None

        if 'parts'  in self.headers : self.partstr = self.headers['parts']
        if 'sum'    in self.headers : self.sumstr  = self.headers['sum']
        if 'flow'   in self.headers : self.flow    = self.headers['flow']
        if 'rename' in self.headers : self.rename  = self.headers['rename']
        if 'event'  in self.headers : self.event   = self.headers['event']

        if self.sumstr != None :
           token        = self.sumstr(',')
           self.sumflg  = token[0]
           self.chksum  = token[1]

        if self.partstr != None :
           token        = self.partstr(',')
           self.partflg = token[0]

           self.chunksize     = int(token[1])
           self.block_count   = 1
           self.remainder     = 0
           self.current_block = 0
           self.filesize      = self.chunksize

           if self.partflg != '1' :
              self.block_count   = int(token[2])
              self.remainder     = int(token[3])
              self.current_block = int(token[4])
              self.filesize      = self.block_count * self.chunksize
              if self.remainder  > 0 :
                 self.filesize  += self.remainder   - self.chunksize

    def print_message(self):
        self.logger.debug("exchange_name      = %s" % self.exchange_name)
        self.logger.debug("exchange_topic_key = %s" % self.exchange_topic_key)
        self.logger.debug("notice             = %s" % self.notice)
        self.logger.debug("parts              = %s" % self.partstr)
        self.logger.debug("sum                = %s" % self.sumstr)
        self.logger.debug("flow               = %s" % self.flow)
        self.logger.debug("rename             = %s" % self.rename)

    def set_post_headers(self):
        self.headers = {}

        if self.partstr != None : self.headers['parts']  = self.partstr
        if self.sumstr  != None : self.headers['sum']    = self.sumstr
        if self.event   != None : self.headers['event']  = self.event
        if self.flow    != None : self.headers['flow']   = self.flow
        if self.rename  != None : self.headers['rename'] = self.rename

    def set_exchange_name(self,name):
        self.exchange_name = name

    def set_post_exchange_topic_key(self,user,url,post_topic=None):
        self.user       = user
        self.url        = url
        path            = url.path.strip('/')
        self.kpath      = path.replace('/','.')
        self.post_topic = 'v02.post'
        if post_topic != None : self.post_topic = post_topic
        self.exchange_topic_key = '%s.%s.%s' % (self.post_topic,self.user,self.kpath)
        self.exchange_topic_key = self.exchange_topic_key.replace('..','.')

    def set_post_options(self,flow=None,rename=None,event=None):
        self.flow   = flow
        self.rename = rename
        self.event  = event

    def set_post_parts(self,partflg='1',blocksize=0, block_count=1, remainder=0, current_block=0):
        self.partflg       = partflg 
        self.blocksize     = blocksize
        self.block_count   = block_count
        self.remainder     = remainder
        self.current_block = current_block

        if partflg == None : 
           self.partstr = None
           return

        self.partstr = '1,%d' % blocksize
        if partflg  != '1' :
           self.partstr = '%c,%d,%d,%d,%d' % (partflg,blocksize,block_count,remainder,current_block)

    def set_post_sum(self,sumflg='d',checksum=0):
        self.sumflg   = sumflg
        self.checksum = checksum
        self.sumstr   = None

        if self.sumflg != None : self.sumstr   = '%s,%s' % (sumflg,checksum)

    def set_post_notice(self,url):
        self.set_time()
        self.url = url

        path = url.path[1:]
        ustr = url.geturl()
        part = ustr.replace(path,'')
        self.notice = '%s %s %s' % (self.time,part,path)

    def set_post_topic(self,post_topic):
        self.post_topic = post_topic

    def set_time(self):
        msec = '.%d' % (int(round(time.time() * 1000)) %1000)
        now  = time.strftime("%Y%m%d%H%M%S",time.gmtime()) + msec
        self.time = now

    def start_timer(self):
        self.tbegin = time.time()
