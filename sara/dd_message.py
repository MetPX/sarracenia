#!/usr/bin/python3

import socket,time,urllib,urllib.parse

class dd_message():

    def __init__(self,logger):
        self.logger        = logger
        self.exchange      = None
        self.topic         = None
        self.notice        = None
        self.headers       = {}

        self.flow          = None
        self.event         = None
        self.message       = None
        self.partstr       = None
        self.rename        = None
        self.source        = None
        self.sumstr        = None

    def from_amqplib(self, msg ):

        self.start_timer()

        self.exchange  = msg.delivery_info['exchange']
        self.topic     = msg.delivery_info['routing_key']
        self.notice    = msg.body
        self.headers   = msg.properties['application_headers']

        if type(msg.body) == bytes :
           self.notice = msg.body.decode("utf-8")

        token        = self.topic.split('.')
        self.version = token[0]

        if self.version == 'v00' :
           self.parse_v00_post()

        if self.version == 'v02' :
           if self.mtype == 'post' : self.parse_v02_post()

    def get_elapse(self):
        return time.time()-self.tbegin

    def log(self, code, message ):
        self.log_exchange           = 'log'
        self.log_routing_key        = self.routing_key.replace('.post.','.log.')
        self.log_notice             = "%s %d %s %s %f" % (self.notice,code,socket.gethostname(),self.user,self.get_elapse())
        self.log_headers            = self.headers
        self.log_headers['message'] = message

    def parse_v00_post(self):
        token       = self.topic.split('.')
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

        token       = self.topic.split('.')
        self.version = token[0]
        self.mtype   = token[1]
        self.user    = token[2]
        self.kpath   = '.'.join(token[3:])

        token        = self.notice.slit(' ')
        self.time    = token[0]
        self.url     = urllib.parse.urlparse(token[1:])
        self.path    = token[2]
  
        self.event   = None
        self.flow    = None
        self.message = None
        self.partstr = None
        self.rename  = None
        self.source  = None
        self.sumstr  = None

        if 'event'   in self.headers : self.event   = self.headers['event']
        if 'flow'    in self.headers : self.flow    = self.headers['flow']
        if 'message' in self.headers : self.message = self.headers['message']
        if 'parts'   in self.headers : self.partstr = self.headers['parts']
        if 'rename'  in self.headers : self.rename  = self.headers['rename']
        if 'source'  in self.headers : self.source  = self.headers['source']
        if 'sum'     in self.headers : self.sumstr  = self.headers['sum']

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

    def set_exchange(self,name):
        self.exchange = name

    def set_event(self,event=None):
        self.event = event

    def set_flow(self,flow=None):
        self.flow   = flow

    def set_headers(self):
        self.headers = {}

        if self.source  != None : self.headers['source']  = self.source
        if self.partstr != None : self.headers['parts']   = self.partstr
        if self.sumstr  != None : self.headers['sum']     = self.sumstr
        if self.event   != None : self.headers['event']   = self.event
        if self.flow    != None : self.headers['flow']    = self.flow
        if self.rename  != None : self.headers['rename']  = self.rename
        if self.message != None : self.headers['message'] = self.message

    def set_notice(self,url):
        self.set_time()
        self.url    = url
        path        = url.path[1:]
        urlstr      = url.geturl()
        static_part = urlstr.replace(path,'')
        self.notice = '%s %s %s' % (self.time,static_part,path)

    def set_parts(self,partflg='1',blocksize=0, block_count=1, remainder=0, current_block=0):
        self.partflg       =  partflg 
        self.blocksize     =  blocksize
        self.block_count   =  block_count
        self.remainder     =  remainder
        self.current_block =  current_block
        self.partstr       =  None
        if partflg         == None : return
        self.partstr       = '%s,%d,%d,%d,%d' %\
                             (partflg,blocksize,block_count,remainder,current_block)

    def set_rename(self,rename):
        self.rename = rename

    def set_source(self,source):
        self.source = source

    def set_sum(self,sumflg='d',checksum=0):
        self.sumflg    =  sumflg
        self.checksum  =  checksum
        self.sumstr    =  None
        if self.sumflg == None : return
        self.sumstr    = '%s,%s' % (sumflg,checksum)

    def set_time(self):
        msec = '.%d' % (int(round(time.time() * 1000)) %1000)
        now  = time.strftime("%Y%m%d%H%M%S",time.gmtime()) + msec
        self.time = now

    def set_topic(self,topic_prefix,url):
        self.topic_prefix = topic_prefix
        self.url          = url
        path              = url.path.strip('/')
        self.kpath        = path.replace('/','.')
        self.topic        = '%s.%s' % (topic_prefix,self.kpath)
        self.topic        = self.topic.replace('..','.')

    def start_timer(self):
        self.tbegin = time.time()
