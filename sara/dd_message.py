#!/usr/bin/python3

import socket,time,urllib,urllib.parse

try :
         from dd_util         import *
except :
         from sara.dd_util    import *

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
        self.sumflg        = None

        self.part_ext      = 'Part'

        self.chkclass      = Checksum()

    def change_partflg(self, partflg ):
        self.partflg       =  partflg 
        self.partstr       = '%s,%d,%d,%d,%d' %\
                             (partflg,self.chunksize,self.block_count,self.remainder,self.current_block)

    def from_amqplib(self, msg ):

        self.start_timer()

        self.exchange  = msg.delivery_info['exchange']
        self.topic     = msg.delivery_info['routing_key']
        self.headers   = msg.properties['application_headers']
        self.notice    = msg.body

        #if type(self.notice) == bytes :
        #   self.notice = self.notice.decode("utf-8")
  
        self.event     = None
        self.flow      = None
        self.message   = None
        self.partstr   = None
        self.rename    = None
        self.source    = None
        self.sumstr    = None

        token        = self.topic.split('.')
        self.version = token[0]

        if self.version == 'v00' :
           self.parse_v00_post()

        if self.version == 'v02' :
           self.parse_v02_post()

    def get_elapse(self):
        return time.time()-self.tbegin

    def log(self, code, message ):
        self.log_exchange           = 'xlog'
        self.log_topic              = self.topic.replace('.post.','.log.')
        self.log_notice             = "%s %d %s %s %f" % (self.notice,code,socket.gethostname(),self.headers['source'],self.get_elapse())
        self.log_headers            = self.headers
        self.log_headers['message'] = message

    def parse_v00_post(self):
        token         = self.topic.split('.')
        # v00         = token[0]
        # dd          = token[1]
        # notify      = token[2]
        self.version  = 'v02'
        self.mtype    = 'post'
        self.subtopic = '.'.join(token[3:])

        token         = self.notice.split(' ')
        self.filename = self.headers['filename']
        self.filesize = int(token[0])
        self.checksum = token[1]
        self.url      = urllib.parse.urlparse(token[2:])
        self.path     = token[3]
        
        self.sumflg   = 'd'
        self.sumstr   = 'd,%s' % self.checksum

        self.chkclass.from_list(self.sumflg)
        self.compute_chksum = self.chkclass.checksum

        self.chunksize     = self.filesize
        self.block_count   = 1
        self.remainder     = 0
        self.current_block = 0
        self.partflg       = '1'
        self.partstr       = '1,%d' % self.filesize
        self.offset        = 0
        self.length        = self.filesize
        self.suffix        = ''

    def parse_v02_post(self):

        token         = self.topic.split('.')
        self.version  = token[0]
        self.mtype    = token[1]
        self.topic_prefix = '.'.join(token[:2])
        self.subtopic     = '.'.join(token[3:])

        token        = self.notice.split(' ')
        self.time    = token[0]
        self.url     = urllib.parse.urlparse(token[1]+token[2])
        self.path    = token[2]

        self.hdrstr  = ''

        self.source  = None
        if 'source'  in self.headers :
           self.source   = self.headers['source']
           self.hdrstr  += '%s=%s ' % ('source',self.source)

        self.partstr = None
        if 'parts'   in self.headers :
           self.partstr  = self.headers['parts']
           self.hdrstr  += '%s=%s ' % ('parts',self.partstr)

        self.sumstr  = None
        if 'sum'     in self.headers :
           self.sumstr   = self.headers['sum']
           self.hdrstr  += '%s=%s ' % ('sum',self.sumstr)

        self.event   = None
        if 'event'   in self.headers :
           self.event    = self.headers['event']
           self.hdrstr  += '%s=%s ' % ('event',self.event)

        self.flow    = None
        if 'flow'    in self.headers :
           self.flow     = self.headers['flow']
           self.hdrstr  += '%s=%s ' % ('flow',self.flow)

        self.rename  = None
        if 'rename'  in self.headers :
           self.rename   = self.headers['rename']
           self.hdrstr  += '%s=%s ' % ('rename',self.rename)

        self.message = None
        if 'message' in self.headers :
           self.message  = self.headers['message']
           self.hdrstr  += '%s=%s ' % ('message',self.message)

        self.suffix = ''

        self.set_parts_str(self.partstr)
        self.set_sum_str(self.sumstr)
        self.set_suffix()

    def part_suffix(self):
        return ".%d.%d.%d.%s.%s" % (self.filesize,self.chunksize,self.current_block,self.sumflg,self.part_ext)

    def set_exchange(self,name):
        self.exchange = name

    def set_event(self,event=None):
        self.event = event

    def set_flow(self,flow=None):
        self.flow   = flow

    def set_headers(self):
        self.headers = {}
        self.hdrstr  = ''

        if self.source  != None :
           self.headers['source']  = self.source
           self.hdrstr  += '%s=%s ' % ('source',self.source)

        if self.partstr != None :
           self.headers['parts']   = self.partstr
           self.hdrstr  += '%s=%s ' % ('parts',self.partstr)

        if self.sumstr  != None :
           self.headers['sum']     = self.sumstr
           self.hdrstr  += '%s=%s ' % ('sum',self.sumstr)

        if self.event   != None :
           self.headers['event']   = self.event
           self.hdrstr  += '%s=%s ' % ('event',self.event)

        if self.flow    != None :
           self.headers['flow']    = self.flow
           self.hdrstr  += '%s=%s ' % ('flow',self.flow)

        if self.rename  != None :
           self.headers['rename']  = self.rename
           self.hdrstr  += '%s=%s ' % ('rename',self.rename)

        if self.message != None :
           self.headers['message'] = self.message
           self.hdrstr  += '%s=%s ' % ('message',self.message)

    def set_notice(self,url,time=None):
        self.time = time
        if time  == None : self.set_time()
        self.url    = url
        path        = url.path
        urlstr      = url.geturl()
        static_part = urlstr.replace(path,'')
        self.notice = '%s %s %s' % (self.time,static_part,path)

    def set_parts(self,partflg='1',chunksize=0, block_count=1, remainder=0, current_block=0):
        self.partflg       =  partflg 
        self.chunksize     =  chunksize
        self.block_count   =  block_count
        self.remainder     =  remainder
        self.current_block =  current_block
        self.partstr       =  None
        if partflg         == None : return
        self.partstr       = '%s,%d,%d,%d,%d' %\
                             (partflg,chunksize,block_count,remainder,current_block)
        self.lastchunk     = current_block == block_count-1

    def set_parts_str(self,partstr):

        self.partflg = None
        self.partstr = partstr

        if self.partstr == None : return

        token        = self.partstr.split(',')
        self.partflg = token[0]

        self.chunksize     = int(token[1])
        self.block_count   = 1
        self.remainder     = 0
        self.current_block = 0
        self.lastchunk     = True

        self.offset        = 0
        self.length        = self.chunksize

        self.filesize      = self.chunksize

        if self.partflg == '1' : return

        self.block_count   = int(token[2])
        self.remainder     = int(token[3])
        self.current_block = int(token[4])
        self.lastchunk     = self.current_block == self.block_count-1

        self.offset        = self.current_block * self.chunksize

        self.filesize      = self.block_count * self.chunksize

        if self.remainder  > 0 :
           self.filesize  += self.remainder   - self.chunksize
           if self.lastchunk : self.length    = self.remainder

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

    def set_sum_str(self,sumstr):
        self.sumflg  = None
        self.sumstr  = sumstr
        if sumstr == None : return

        token        = self.sumstr.split(',')
        self.sumflg  = token[0]
        self.chksum  = token[1]

        self.chkclass.from_list(self.sumflg)
        self.compute_chksum = self.chkclass.checksum

    def set_suffix(self):
        self.suffix = self.part_suffix()

    def set_time(self):
        msec = '.%d' % (int(round(time.time() * 1000)) %1000)
        now  = time.strftime("%Y%m%d%H%M%S",time.gmtime()) + msec
        self.time = now

    def set_topic_url(self,topic_prefix,url):
        self.topic_prefix = topic_prefix
        self.url          = url
        path              = url.path.strip('/')
        self.subtopic     = path.replace('/','.')
        self.topic        = '%s.%s' % (topic_prefix,self.subtopic)
        self.topic        = self.topic.replace('..','.')

    def set_topic_usr(self,topic_prefix,subtopic):
        self.topic_prefix = topic_prefix
        self.subtopic     = subtopic
        self.topic        = '%s.%s' % (topic_prefix,self.subtopic)
        self.topic        = self.topic.replace('..','.')

    def start_timer(self):
        self.tbegin = time.time()
