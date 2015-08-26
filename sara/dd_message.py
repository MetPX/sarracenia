#!/usr/bin/python3

import time,urllib,urllib.parse

class dd_message():

    def __init__(self,logger):
        self.logger        = logger
        self.exchange_name = None
        self.routing_key   = None
        self.notice        = None
        self.headers       = {}

    def from_amqplib(self, msg ):

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
  
        self.flow    = None
        self.rename  = None
        self.partstr = self.headers['parts']
        self.sumstr  = self.headers['sum']

        if 'flow'   in self.headers : self.flow   = self.headers['flow']
        if 'rename' in self.headers : self.rename = self.headers['rename']

        token        = self.sumstr(',')
        self.sumflg  = token[0]
        self.chksum  = token[1]

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

    def set_time(self):
        msec = '.%d' % (int(round(time.time() * 1000)) %1000)
        now  = time.strftime("%Y%m%d%H%M%S",time.gmtime()) + msec
        self.time = now

    def set_post_headers(self):
        self.headers = {}

        self.headers['parts']  = self.partstr
        self.headers['sum']    = self.sumstr

        if self.flow != None   : self.headers['flow']   = self.flow
        if self.rename != None : self.headers['rename'] = self.rename

    def set_exchange_name(self,name):
        self.exchange_name = name

    def set_post_exchange_topic_key(self,user,url):
        self.user    = user
        self.url     = url
        path         = url.path.strip('/')
        self.kpath   = path.replace('/','.')
        self.exchange_topic_key = 'v02.post.%s.%s' % (self.user,self.kpath)
        self.exchange_topic_key = self.exchange_topic_key.replace('..','.')

    def set_post_options(self,flow=None,rename=None):
        self.flow   = flow
        self.rename = rename

    def set_post_parts(self,partflg='1',blocksize=0, block_count=1, remainder=0, current_block=0):
        self.partflg       = partflg 
        self.blocksize     = blocksize
        self.block_count   = block_count
        self.remainder     = remainder
        self.current_block = current_block

        self.partstr = '1,%d' % blocksize
        if partflg  != '1' :
           self.partstr = '%c,%d,%d,%d,%d' % (partflg,blocksize,block_count,remainder,current_block)

    def set_post_sum(self,sumflg='d',checksum=0):
        self.sumflg   = sumflg
        self.checksum = checksum
        self.sumstr   = '%s,%s' % (sumflg,checksum)

    def set_post_notice(self,url):
        self.set_time()
        self.url = url

        path = url.path[1:]
        ustr = url.geturl()
        part = ustr.replace(path,'')
        self.notice = '%s %s %s' % (self.time,part,path)
