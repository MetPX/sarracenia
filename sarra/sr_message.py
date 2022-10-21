#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#
# sr_message.py : python3 utility tools for sarracenia amqp message processing
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Sep 22 10:41:32 EDT 2015
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 2 of the License.
#
#  This program is distributed in the hope that it will be useful, 
#  but WITHOUT ANY WARRANTY; without even the implied warranty of 
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#
#

import calendar,os,socket,sys,time,urllib,urllib.parse

from sys import platform as _platform

from codecs import decode,encode

from hashlib import md5

import json

# AMQP limits headers to 'short string', or 255 characters, so truncate and warn.
amqp_ss_maxlen = 253

from base64 import b64decode, b64encode
from mimetypes import guess_type


try :
         from sr_util         import *
         from sr_xattr        import *
except :
         from sarra.sr_util    import *
         from sarra.sr_xattr   import *

class sr_message():

    def __init__(self,parent):
        self.parent        = parent
        self.logger        = parent.logger

        self.bufsize       = parent.bufsize

        self.message_ttl   = 0
        self.exchange      = None
        self.report_exchange  = parent.report_exchange
        self.topic_prefix  = parent.topic_prefix
        self.version  = parent.version
        self.log_reject  = parent.log_reject
        self.post_topic_prefix  = parent.post_topic_prefix
        self.post_version  = parent.post_version
        self.report_publisher = None
        self.publisher     = None
        self.pub_exchange  = None
        self.topic         = None
        self.notice        = None
        self.headers       = {}

        self.partstr       = None
        self.sumstr        = None
        self.sumflg        = None

        # Default value for parts attributes
        self.partflg = None
        self.chunksize = None
        self.length = None
        self.block_count = None
        self.remainder = None
        self.current_block = None
        self.lastchunk = None
        self.offset = None
        self.filesize = None

        # Setting default length
        self.length = 0

        self.inline = parent.inline
        self.inline_max = parent.inline_max
        self.post_base_dir = parent.post_base_dir
        self.inline_encoding = parent.inline_encoding

        self.part_ext      = 'Part'

        self.sumalgo       = parent.sumalgo

        self.inplace       = True

        self.user          = None

        self.host          = socket.getfqdn()

        self.add_headers   = self.parent.headers_to_add
        self.del_headers   = self.parent.headers_to_del

        self.isPulse       = False
        self.isRetry       = False

        # important working attributes set to None at startup
        
        self.baseurl       = None
        self.relpath       = None
        self.new_dir       = None
        self.new_file      = None
        self.new_baseurl   = None
        self.new_relpath   = None
        self.to_clusters = []
        self.tbegin = nowflt()
        self.pubtime = None

    def __print_json( self ):

        if not self.topic.split('.')[1] in [ 'post', 'report' ]:
            return

        if self.post_version == 'v03':
            json_line = json.dumps( ( self.pubtime, self.baseurl, self.relpath, self.headers ), sort_keys=True )
        else:
            json_line = json.dumps( ( self.topic, self.headers, self.notice ), sort_keys=True )

        print("%s" % json_line, flush=True )

    def change_partflg(self, partflg ):
        self.partflg       =  partflg
        self.partstr       = '%s,%d,%d,%d,%d' %\
                             (partflg,self.chunksize,self.block_count,self.remainder,self.current_block)
        self.headers['parts'] = self.partstr

    def content_should_not_be_downloaded(self):
        """
        if the file advertised is newer than the local one, and it has a different checksum, return False.

        """
        fname = "%s%s%s" %  (self.new_dir, '/', self.new_file )
        self.logger.debug("sr_csnbd start %s" % (fname ) )
        
        self.local_checksum = None

        if not os.path.isfile(fname) : 
           self.logger.debug("sr_csnbd content_match %s, file does not currently exist." % (fname ) )
           return False

        # insert : file big enough to compute part checksum ?

        lstat = os.stat(fname)
        fsiz  = lstat[stat.ST_SIZE] 
        end   = self.local_offset + self.length

        # compare sizes... if (sr_subscribe is downloading partitions into taget file) and (target_file isn't fully done)
        # This check prevents random halting of subscriber (inplace on) if the messages come in non-sequential order
        if (self.target_file == self.new_file) and (fsiz != self.filesize):
          self.logger.debug("sr_csnbd %s file size different, so cannot be the same" % (fname ) )
          return False

        # compare dates...

        if 'mtime' in self.headers:
            new_mtime = timestr2flt(self.headers[ 'mtime' ])
            old_mtime=0.0

            if self.parent.preserve_time :
               old_mtime = lstat.st_mtime
            elif supports_extended_attributes:
               try:
                   x = sr_xattr( os.path.join(self.new_dir, self.new_file) )
                   old_mtime = timestr2flt(x.get( 'mtime' ))
               except:
                   pass

            if new_mtime <= old_mtime:
               self.logger.debug("sr_csnbd %s new version not newer" % ( fname ) )
               if self.log_reject:
                   self.logger.info("rejected: mtime not newer %s " % (fname ) )
               return True
            else:
               self.logger.debug("sr_csnbd {} new version is {} newer (new: {} vs old: {} )".format(fname, new_mtime-old_mtime, new_mtime, old_mtime ))

        if self.sumflg in [ '0', 'n', 'z'] : 
            self.logger.debug("sr_csnbd content_match %s sum 0/n/z never matches" % (fname ) )
            return False
 
        if end > fsiz :
           self.logger.debug("sr_csnbd content_match file not big enough... considered different")
           return False

        try   : self.compute_local_checksum()
        except: 
                self.logger.debug("sr_csnbd something went wrong when computing local checksum... considered different")
                return False

        self.logger.debug( "sr_csnbd checksum in message: %s vs. local: %s" % ( self.local_checksum, self.checksum ) ) 

        if self.local_checksum == self.checksum:
            if self.log_reject:
                 self.logger.info( "rejected: same checksum %s " % (fname ) )
            return True
        else:
            return False
        #return self.local_checksum == self.checksum

    def compute_local_checksum(self):
        self.logger.debug("sr_message compute_local_checksum new_dir=%s, new_file=%s" % ( self.new_dir, self.new_file ) )

        if supports_extended_attributes:
            try:
                x = sr_xattr( os.path.join(self.new_dir, self.new_file) )
                s = x.get( 'sum' )

                if s:
                   self.local_checksum = s.split(',')[-1]
                   return

            except:
                pass

        self.logger.debug("checksum extracted by reading file/calculating")

        bufsize = self.bufsize
        if self.length < bufsize : bufsize = self.length

        self.sumalgo.set_path(os.path.basename(self.new_file))

        fp = open( self.new_dir + '/' + self.new_file,'rb')
        if self.local_offset != 0 : fp.seek(self.local_offset,0)
        i  = 0
        while i<self.length :
              buf = fp.read(bufsize)
              if not buf: break
              self.sumalgo.update(buf)
              i  += len(buf)
        fp.close()

        if i != self.length :
           self.logger.warning("sr_message compute_local_checksum incomplete reading %d %d" % (i,self.length))
           self.local_checksum = '0'
           return

        self.local_checksum = self.sumalgo.get_value()

    def convert_partsv2tov3(self):
        self.headers['size'] = self.length
        if self.partflg not in ['0', '1']:
            self.headers['blocks'] = {}
            self.headers['blocks']['method'] = {'i': 'inplace', 'p': 'partitioned'}[self.partflg]
            self.headers['blocks']['size'] = str(self.chunksize)
            self.headers['blocks']['count'] = str(self.block_count)
            self.headers['blocks']['remainder'] = str(self.remainder)
            self.headers['blocks']['number'] = str(self.current_block)

    def from_amqplib(self, msg=None ):
        """
            This routine does a minimal decode of raw messages from amqplib
            raw messages are also decoded by sr_retry/msgToJSON, so must match the two. 
        """

        self.start_timer()

        self.logger.debug("from_amqplib " )
        if msg :
           self.exchange  = msg.delivery_info['exchange']
           self.topic     = msg.delivery_info['routing_key']
           self.topic     = self.topic.replace('%20',' ')
           self.topic     = self.topic.replace('%23','#')
           sum_algo_v3tov2 = { "arbitrary":"a", "md5":"d", "sha512":"s", "md5name":"n", "random":"0", "link":"L", "remove":"R", "cod":"z" }
           if msg.body[0] == '[' :
               self.logger.debug("from_amqplib transitional v03" )
               self.pubtime, self.baseurl, self.relpath, self.headers = json.loads(msg.body)
               self.notice = "%s %s %s" % ( self.pubtime, self.baseurl, self.relpath )
           elif msg.body[0] == '{' :
               self.logger.debug("from_amqplib v03 body: %s" % msg.body)
               self.headers = json.loads(msg.body)
               self.logger.debug("from_amqplib v03 headers: %s" % self.headers )
               self.pubtime = self.headers[ "pubTime" ]
               self.baseurl = self.headers[ "baseUrl" ]
               self.relpath = self.headers[ "relPath" ]
               self.notice = "%s %s %s" % ( self.pubtime, self.baseurl, self.relpath )
               if "integrity" in self.headers.keys():
                   if type( self.headers[ "integrity" ] ) is str:
                       self.headers[ "integrity" ] = json.loads( self.headers[ "integrity" ] )
                   sa = sum_algo_v3tov2[ self.headers[ "integrity" ][ "method" ] ]

                   # transform sum value
                   if sa in [ '0' ]:
                       sv = self.headers[ "integrity" ][ "value" ]
                   elif sa in [ 'z' ]:
                       sv = sum_algo_v3tov2[ self.headers[ "integrity" ][ "value" ] ]
                   else:
                       sv = encode( decode( self.headers[ "integrity" ][ "value" ].encode('utf-8'), "base64" ), 'hex' ).decode('utf-8')
                   # set event.
                   if sa == 'L' :
                       self.event = 'link'
                   elif sa == 'l':
                       self.event = 'link'
                   elif sa == 'R':
                       self.event = 'delete'
                   else:
                       self.event = 'modify'

                   self.headers[ "sum" ] = sa + ',' + sv
                   self.sumstr = self.headers['sum']
               else:
                   sa='n'
                   sv = md5(bytes(self.relpath,'utf-8')).hexdigest()
                   self.headers[ "sum" ] = sa + ',' + sv
                   self.sumstr = self.headers['sum']
                   
               if 'fileOp'in self.headers.keys():
                   sv = md5(bytes(self.headers['relPath'],'utf-8')).hexdigest()
                   
                   if 'hlink' in self.headers['fileOp']:
                       self.headers['link'] = self.headers['fileOp']['link']
                       self.event = 'link'
                       sa='l'
                   elif 'link' in self.headers['fileOp']:
                       self.headers['link'] = self.headers['fileOp']['link']
                       self.event = 'link'
                       sa='L'
                   elif 'remove' in self.headers['fileOp']:
                       self.event = 'delete'
                       sa='R'
                   elif 'rename' in self.headers['fileOp']:
                       self.headers['oldname'] = self.headers['fileOp']['rename']
                       self.event = 'modify'
                   else:
                       self.event = 'modify'
                   del self.headers['fileOp']

                   self.headers[ "sum" ] = sa + ',' + sv
                   self.sumstr = self.headers['sum']
                   
               if "integrity" in self.headers.keys():
                   del self.headers['integrity']
                
               if 'blocks' in self.headers.keys():
                   parts_map = {'inplace': 'i', 'partitioned': 'p'}
                   self.set_parts(parts_map[self.headers['blocks']['method']], int(self.headers['blocks']['size']),
                                      int(self.headers['blocks']['count']), int(self.headers['blocks']['remainder']),
                                      int(self.headers['blocks']['number']))
                   del self.headers['blocks']
               elif 'size' in self.headers.keys():
                   self.set_parts('1', int(self.headers['size']))
                   del self.headers['size']
               else:
                   self.set_parts('1',0)


           else:
               self.logger.debug("from_amqplib v02" )
               if 'application_headers' in msg.properties.keys():
                   self.headers = msg.properties['application_headers']

               if type(msg.body) == bytes: 
                    self.notice = msg.body.decode("utf-8")
               else:
                    self.notice = msg.body

               self.pubtime, self.baseurl, self.relpath = self.notice.split(' ')[0:3]
           self.isRetry   = msg.isRetry

        # retransmission case :
        # topic is name of the queue...
        # set exchange to xpublic
        # rebuild topic from notice : v02.post....

        if self.exchange == '' and self.topic[:2] == 'q_':
           self.logger.debug(" retransmit topic = %s" % self.topic)
           token = self.notice.split(' ')
           self.exchange = 'xpublic'
           if hasattr(self.headers,'exchange') :
              self.exchange = self.headers['exchange']
              del self.headers['exchange']

           path = token[2].strip('/')
           words = path.split('/')
           self.topic = self.post_topic_prefix + '.'.join(words[:-1])
           self.logger.debug(" modified for topic = %s" % self.topic)

        # adjust headers from -headers option

        self.trim_headers()

        token = self.topic.split('.')
        self.version = token[0]

        if self.version == 'v00':
           self.parse_v00_post()
        else:
           self.parse_v02_post()

    def get_elapse_pubtime(self):
        """ Time calculated between now and the time of the first publication in seconds

        :return: the result of now - pubtime
        """
        return nowflt() - timestr2flt(self.pubtime)

    def get_elapse(self):
        """ Time calculated between now and the time of the msg decoded

        :return: the result of now - tbegin
        """
        return nowflt() - self.tbegin

    def report_publish(self,code,message):
        self.code               = code
        self.headers['message'] = message
        self.report_topic          = self.topic.replace('.post.','.report.')
     
        # reports should not contain the inlined data.
        if 'content' in self.headers:
           del self.headers[ 'content' ]

        e = self.get_elapse()

        if self.topic_prefix.startswith('v03'):
           self.headers['report'] = { "elapsedTime": e, "resultCode":self.code, \
               "host":self.host, "user":self.user }

        # v02 filler... remove 2020.
        self.report_notice         = "%s %s %s %d %s %s %f" % \
                (self.pubtime, self.baseurl, self.relpath, self.code, \
                     self.host, self.user, e )
        self.set_hdrstr()

        # AMQP limits topic to 255 characters, so truncate and warn.
        if len(self.topic.encode("utf8")) >= amqp_ss_maxlen :
           mxlen=amqp_ss_maxlen 
           # see truncation explanation from above.
           while( self.report_topic.encode("utf8")[mxlen-1] & 0xc0 == 0xc0 ):
               mxlen -= 1

           self.report_topic = self.report_topic.encode("utf8")[0:mxlen].decode("utf8")
           self.logger.warning( "reporting topic too long. truncated to fit 255 byte AMQP limit: %s " % \
                        ( self.report_topic ) )

        # if  there is a publisher
        if self.report_publisher != None :

           # run on_report plugins
           ok=True
           for plugin in self.parent.on_report_list :
               if not plugin(self.parent): 
                   ok=False
                   break

           # publish
           if ok:
               self.report_publisher.publish(self.report_exchange,self.report_topic,self.report_notice,self.headers)

        self.logger.debug("%d %s : %s %s %s" % (code,message,self.report_topic,self.report_notice,self.hdrstr))

        # make sure not published again
        for i in [ 'message', 'report' ]:
            if i in self.headers:
                del self.headers[i]

    def parse_v00_post(self):
        token             = self.topic.split('.')
        self.version      = 'v02'
        self.mtype        = 'post'
        self.topic_prefix = 'v02.post'
        self.subtopic     = '.'.join(token[3:])
        self.topic        = self.topic_prefix + '.' + self.subtopic

        token        = self.notice.split(' ')
        self.baseurl = token[2]
        self.relpath = token[3].replace(    '%20',' ')
        self.relpath = self.relpath.replace('%23','#')

        self.set_notice(token[2],token[3])

        url          = urllib.parse.urlparse(token[2]+token[3])
        
        self.checksum = token[0]
        self.filesize = int(token[1])

        self.headers['source'] = 'metpx'

        self.partstr = '1,%d,1,0,0' % self.filesize
        self.headers['parts'] = self.partstr

        self.sumstr  = 'd,%s' % self.checksum
        self.headers['sum'] = self.sumstr

        self.headers['to_clusters'] = None

        self.suffix  = ''
        
        self.set_parts_from_str(self.partstr)
        self.set_sum_str(self.sumstr)
        self.set_suffix()
        self.set_hdrstr()

    def parse_v02_post(self):

        token         = self.topic.split('.')
        self.version  = token[0]
        self.mtype    = token[1]
        self.topic_prefix = '.'.join(token[:2])
        self.subtopic     = '.'.join(token[3:])

        token        = self.notice.split(' ')
        self.pubtime = token[0]
        self.baseurl = token[1]
        self.relpath = token[2].replace(    '%20',' ')
        self.relpath = self.relpath.replace('%23','#')
        self.urlstr  = token[1]+token[2]
        self.url     = urllib.parse.urlparse(self.urlstr)

        if self.mtype == 'report' or self.mtype == 'log': # log included for compatibility... prior to rename..

           if self.version == 'v02':
               self.report_code   = int(token[3])
               self.report_host   = token[4]
               self.report_user   = token[5]
               self.report_elapse = float(token[6])
           else:
               ( self.report_elapse, self.report_code, self.report_host, self.report_user ) = self.headers['report'].split()

        if 'parts' in self.headers:
           self.partstr = self.headers['parts']

        if 'sum' in self.headers:
           self.sumstr = self.headers['sum']
           if self.sumstr[0] == 'R':
              self.event = 'delete'
           elif self.sumstr[0] == 'L':
              self.event = 'link'
           else:
              self.event = 'modify'

        if 'to_clusters' in self.headers:
           self.to_clusters = self.headers['to_clusters'].split(',')

        self.suffix = ''

        if self.partstr is not None:
            self.set_parts_from_str(self.partstr)
        self.set_sum_str(self.sumstr)
        self.set_suffix()
        self.set_hdrstr()

    def part_suffix(self):
        return '.%d.%d.%d.%d.%s.%s' %\
               (self.chunksize,self.block_count,self.remainder,self.current_block,self.sumflg,self.part_ext)

    def post(self,parent):
        ok = False

        if self.pub_exchange != None : self.exchange = self.pub_exchange

        if not ( self.post_version == 'v03' ): 
           # truncated content is useless, so drop it.
           if 'content' in self.headers :
               del self.headers['content']

        elif ( self.headers[ 'sum' ][0] in [ 'l', 'L', 'R' ] ) :
            # avoid inlining if it is a link or a remove.
            pass
        elif ( self.post_version == 'v03' ) and ( 'post' in self.post_topic_prefix ) \
            and self.inline and not ( 'content' in self.headers ) :
  
            self.logger.debug("FIXME inlining possible headers: %s" % self.headers )

            if 'size' in self.headers :
                sz = int(self.headers[ 'size' ])
            else:
                sz = int( self.headers[ 'parts' ].split(',')[1] ) 

            if ( sz < self.inline_max ) :
    
                fn = self.post_base_dir
    
                if fn[-1] != '/':
                    fn = fn + os.path.sep
    
                if self.relpath[0] == '/':
                    fn = fn +  self.relpath[1:]
                else:
                    fn = fn + self.relpath
    
                if os.path.isfile(fn):
                    if self.inline_encoding == 'guess':
                       e = guess_type(fn)[0]
                       binary = not e or not ('text' in e )
                    else:
                       binary = (self.inline_encoding == 'text' )
    
                    f = open(fn,'rb')
                    d = f.read()
                    f.close()
        
                    if binary:
                        self.headers[ "content" ] = { "encoding": "base64", "value": b64encode(d).decode('utf-8') }
                    else:
                        try:
                            self.headers[ "content" ] = { "encoding": "utf-8", "value": d.decode('utf-8') }
                        except:
                            self.headers[ "content" ] = { "encoding": "base64", "value": b64encode(d).decode('utf-8') }
    
        # AMQP limits topic to 255 characters, space and # replaced, if greater than limit : truncate and warn.
        self.topic = self.topic.replace(' ','%20')
        self.topic = self.topic.replace('#','%23')

        if self.post_topic_prefix != self.topic_prefix:
            self.topic = self.topic.replace(self.topic_prefix,self.post_topic_prefix,1)

        if len(self.topic.encode("utf8")) >= amqp_ss_maxlen :
           mxlen=amqp_ss_maxlen 
           # see truncation explanation from above.
           while( self.topic.encode("utf8")[mxlen-1] & 0xc0 == 0xc0 ):
               mxlen -= 1

           self.topic = self.topic.encode("utf8")[0:mxlen].decode("utf8")
           self.logger.warning( "too long topic.  Truncated to fit 255 byte AMQP limit: %s " % \
                        ( self.topic ) )

        # in order to split winnowing into multiple instances, directs items with same checksum
        # to same shard. do that by keying on a specific character in the checksum.
        # TODO investigate as this would throw a TypeError if post_exchange_split is None
        if self.post_exchange_split > 0 :
           if 'integrity' in self.headers : 
               if self.headers['integrity']['method'] in ['cod','random']:
                   suffix= "%02d" % ( sum( bytearray(self.headers['integrity']['value'], 'ascii')) % self.post_exchange_split )
                   self.logger.debug( "post_exchange_split set, keying on %s , suffix is %s" % \
                        ( self.headers['sum']['value'], suffix) )
               else: 
                   suffix= "%02d" % ( sum( bytearray(self.headers['integrity']['value'],'ascii')) % self.post_exchange_split )
                   self.logger.debug( "post_exchange_split set, keying on %s , suffix is %s" % \
                        ( self.headers['sum']['value'], suffix) )
           else:
               suffix= "%02d" % ( sum( bytearray(self.headers['sum'], 'ascii')) % self.post_exchange_split )
               self.logger.debug( "post_exchange_split set, keying on %s , suffix is %s" % ( self.headers['sum'], suffix) )
        else:
           suffix=""

        if self.publisher != None :
           if self.post_version == 'v03':
               self.headers[ "pubTime" ] = timev2tov3str( self.pubtime )
               if "mtime" in self.headers.keys():
                   self.headers[ "mtime" ] = timev2tov3str( self.headers[ "mtime" ] )
               if "atime" in self.headers.keys():
                   self.headers[ "atime" ] = timev2tov3str( self.headers[ "atime" ] )
               self.headers[ "baseUrl" ] = self.baseurl
               self.headers[ "relPath" ] = self.relpath
               
               sum_algo_map = { "a":"arbitrary", "d":"md5", "s":"sha512", "n":"md5name", "0":"random", "L":"link", "R":"remove", "z":"cod" }
               if 'sum' in self.headers:
                   sa = self.headers["sum"][0] 
                   sm = sum_algo_map[ sa ]
                   if sm in [ 'random' ] :
                       sv = self.headers["sum"][2:]
                       self.headers[ "integrity" ] = { "method": sm, "value": sv }
                   elif sm in [ 'cod' ] :
                       sv = sum_algo_map[ self.headers["sum"][2:] ]
                       self.headers[ "integrity" ] = { "method": sm, "value": sv }
                   elif sm in [ 'link', 'remove' ] :
                       if sa == 'l' :
                           self.headers['fileOp'] = { 'hlink': self.headers['link'] } 
                           del self.headers['link']
                       elif sa ==  'L':
                           self.headers['fileOp'] = { 'link': self.headers['link'] } 
                           del self.headers['link']
                       elif sm in [ 'remove' ]:
                           self.headers['fileOp'] = { 'remove': True } 
                   else:
                       sv = encode( decode( self.headers["sum"][2:], 'hex'), 'base64' ).decode('utf-8').strip()
                       self.headers[ "integrity" ] = { "method": sm, "value": sv }

               if 'oldname' in self.headers.keys():
                   self.headers['fileOp'] = { 'rename' : self.headers['oldname'] }
                   del self.headers['oldname']

               if 'parts' in self.headers.keys():
                   self.set_parts_from_str(self.headers['parts'])
                   self.convert_partsv2tov3()

               body = json.dumps({k: self.headers[k] for k in self.headers if k not in ['sum', 'parts']})

               for plugin in parent.on_post_list:
                    if not plugin(parent):
                       return False
             
               if parent.outlet == 'json':
                    self.__print_json()
                    ok= True
               elif parent.outlet == 'url' :
                    print( "%s/%s" % ( self.base_url, self.relpath ) )
                    ok= True
               else:
                    ok = self.publisher.publish(self.exchange+suffix, self.topic, body, None, self.message_ttl)
           else:
               #in v02, sum is the correct header. FIXME: roundtripping not quite right yet.
               if 'integrity' in self.headers.keys(): 
                  del self.headers[ 'integrity' ]
               if 'size' in self.headers.keys():
                  del self.headers['size']
               if 'blocks' in self.headers.keys():
                  del self.headers['blocks']

               for plugin in parent.on_post_list:
                    if not plugin(parent):
                       return False

               for h in self.headers:
                   # v02 wants simple strings, cannot have dicts like in v03.
                   if type(self.headers[h]) is dict:
                       self.logger.debug( "dict header flattening to a string: header[ %s ] = %s " % ( h, self.headers[h] ) )
                       self.headers[h] = json.dumps( self.headers[h] )

                   if (type(self.headers[h]) is str) and (len(self.headers[h].encode("utf8")) >= amqp_ss_maxlen):

                       # strings in utf, and if names have special characters, the length
                       # of the encoded string wll be longer than what is returned by len(. so actually need to look
                       # at the encoded length ...  len ( self.headers[h].encode("utf-8") ) < 255
                       # but then how to truncate properly. need to avoid invalid encodings.
                       mxlen=amqp_ss_maxlen
                       while( self.headers[h].encode("utf8")[mxlen-1] & 0xc0 == 0xc0 ):
                             mxlen -= 1

                       self.headers[h] = self.headers[h].encode("utf8")[0:mxlen].decode("utf8")
                       self.logger.error( "too long %s header at %d characters (to fit 255 byte AMQP limit) to: %s " % \
                               ( h, len(self.headers[h]) , self.headers[h]) )
                       return False

               if parent.outlet == 'json':
                    self.__print_json( )
                    ok=True
               elif parent.outlet == 'url' :
                    print( "%s/%s" % ( self.base_url, self.relpath ) )
                    ok=True
               else:
                    ok = self.publisher.publish(self.exchange+suffix,self.topic,self.notice,self.headers,self.message_ttl)

        self.set_hdrstr()

        if ok :
                self.logger.debug("Published1: %s %s" % (self.exchange,self.topic))
                self.logger.debug("Published2: '%s %s %s' %s" % (self.pubtime, self.baseurl, self.relpath, self.hdrstr))
        else  :
                self.printlog = self.logger.error
                self.printlog("Could not publish message :")

                self.printlog("exchange %s topic %s " % (self.exchange,self.topic) )
                self.printlog("notice   %s %s %s"     % (self.pubtime, self.baseurl, self.relpath) )
                self.printlog("headers  %s"           % self.hdrstr )

        return ok

    def set_exchange(self,name):
        self.exchange = name

    def set_file(self, new_file, sumstr):
        """ 
            set_file: modify a message to reflect a new file.
                      make a file URL of the new_file.
            sumstr should be the properly formatted checksum field for a message
              '<algorithm>,<value>', e.g.  'd,cbe9047d1b979561bed9a334111878c6'
            to be used by filter plugins when changing the output url.
        """
        fstat = os.stat(new_file)

        # Modify message for posting.

        self.baseurl = 'file:'
        self.relpath = new_file

        self.urlstr = 'file:/' + new_file
        self.url = urllib.parse.urlparse(self.urlstr)

        path  = new_file.strip('/')
        words = path.split('/')
        self.topic = self.post_topic_prefix + '.'.join(words[:-1])

        self.headers[ 'sum' ] = sumstr
        self.headers[ 'parts' ] = '1,%d,0,0' % fstat.st_size
        self.headers[ 'mtime' ] = timeflt2str(fstat.st_mtime)

        self.set_notice(self.baseurl,self.relpath)

    def set_hdrstr(self):
        self.hdrstr  = ''

        for h in sorted(self.headers):
           self.hdrstr += '%s=%s ' % (h, self.headers[h])

        # added for v00 compatibility (old version of dd_subscribe)
        # can be taken off when v02 will be fully deployed and end user uses sr_subscribe
        #self.headers['filename'] = os.path.basename(self.relpath).split(':')[0][0:200]


    # Once we know the local file we want to use
    # we can have a few flavor of it

    def set_new(self):

        self.local_offset  = 0
        self.in_partfile   = False
        self.local_checksum= None
       
        self.inplace       = self.parent.inplace
        self.target_file   = None

        # file to file

        if self.partflg == '1' : return
        if self.partflg == None : return
        if (self.partflg != 'i') and ( self.partflg != 'p' ):
            self.logger.error("sr_message/set_new message received with invalid partflg=%s" % (self.partflg) )
            return
            
     
        # part file never inserted

        if not self.inplace :

           self.in_partfile = True

           # part file to part file

           if self.partflg == 'p' : return

           # file inserts to part file

           if self.partflg == 'i' :
              self.new_file    += self.suffix
              self.new_relpath += self.suffix
              return

        
        # part file inserted

        if self.inplace :

           # part file inserts to file (maybe in file, maybe in part file)

           if self.partflg == 'p' :
              self.target_file    = self.new_file.replace(self.suffix,'')
              self.target_relpath = self.new_relpath.replace(self.suffix,'')
              part_file    = self.new_file
              part_relpath = self.new_relpath
        
           # file insert inserts into file (maybe in file, maybe in part file)

           elif self.partflg == 'i' :
              self.target_file    = self.new_file
              self.target_relpath = self.new_relpath
              part_file           = self.new_file + self.suffix
              part_relpath        = self.new_relpath + self.suffix


           # sparse file is tolerated in sr_sender
           # so part inplace whatever the condition of the target_file

           if self.parent.program_name == 'sr_sender' :  
              self.new_file     = self.target_file
              self.new_relpath  = self.target_relpath
              self.local_offset = self.offset
              self.in_partfile  = False
              return

           # default setting : redirect to temporary part file

           self.new_file    = part_file
           self.new_relpath = part_relpath
           self.in_partfile = True
        
           # try to make this message a file insert

           # file exists
           self.target_path = self.new_dir + '/' + self.target_file
           if os.path.isfile(self.target_path) :
              self.logger.debug("new_file exists")
              lstat   = os.stat(self.target_path)
              fsiz    = lstat[stat.ST_SIZE] 

              self.logger.debug("offset vs fsiz %d %d" % (self.offset,fsiz ))
              # part/insert can be inserted 
              if self.offset <= fsiz :
                 self.logger.debug("insert")
                 self.new_file     = self.target_file
                 self.new_relpath  = self.target_relpath
                 self.local_offset = self.offset
                 self.in_partfile  = False
                 return

              # in temporary part file
              self.logger.debug("exist but no insert")
              return


           # file does not exists but first part/insert ... write directly to new_file
           elif self.current_block == 0 :
              self.logger.debug("not exist but first block")
              self.new_file    = self.target_file
              self.new_relpath = self.target_relpath
              self.in_partfile = False
              return

           # file does not exists any other part/insert ... put in temporary part_file
           else :
              self.logger.debug("not exist and not first block")
              self.in_partfile = True
              return
                 
        # unknow conditions

        self.logger.error("bad unknown conditions")
        return

    def set_notice_url(self, url, time=None):
        self.url = url
        self.set_pubtime(time)

        path = url.path.strip('/')
        notice_path = path.replace(' ', '%20')
        notice_path = notice_path.replace('#', '%23')

        if url.scheme == 'file':
           self.notice = '%s %s %s' % (self.pubtime, 'file:', '/'+notice_path)
           self.baseurl = 'file:'
           self.relpath = '/'+notice_path
           return

        urlstr = url.geturl()
        static_part = urlstr.replace(url.path, '') + '/'

        if url.scheme == 'http':
           self.notice = '%s %s %s' % (self.pubtime, static_part, notice_path)
           self.baseurl = static_part
           self.relpath = notice_path
           return

        if url.scheme[-3:] == 'ftp':
           if url.path[:2] == '//':
               notice_path = '/' + notice_path

        self.notice = '%s %s %s' % (self.pubtime, static_part, notice_path)
        self.baseurl = static_part
        self.relpath = notice_path

    def set_notice(self, baseurl, relpath, time=None):
        self.baseurl = baseurl
        self.relpath = relpath
        self.set_pubtime(time)

        notice_relpath = relpath.replace(' ', '%20')
        notice_relpath = notice_relpath.replace('#', '%23')

        self.notice = '%s %s %s' % (self.pubtime, baseurl, notice_relpath)
        self.baseurl = baseurl
        self.relpath = notice_relpath

        #========================================
        # COMPATIBILITY TRICK  for the moment

        self.urlstr = baseurl+notice_relpath
        self.url = urllib.parse.urlparse(self.urlstr)
        #========================================

    def set_parts(self, partflg='1', chunksize=0, block_count=1, remainder=0, current_block=0):
        # Setting parts for v02
        self.partstr = '%s,%d,%d,%d,%d' % (partflg, chunksize, block_count, remainder, current_block)
        self.headers['parts'] = self.partstr

        # Setting other common attributes from parts
        self.partflg = partflg
        self.chunksize = chunksize
        self.block_count = block_count
        self.remainder = remainder
        self.current_block = current_block

        # Setting calculated attributes from parts
        is_chunk = current_block != block_count - 1 or block_count == 1
        self.length = chunksize if is_chunk else remainder
        self.lastchunk = current_block == block_count-1
        self.offset = current_block * chunksize
        self.filesize = block_count * chunksize + remainder

    def set_parts_from_str(self, partstr):
        tokens = partstr.split(',')
        if 0 < len(tokens) < 6:
            parts_rest = [int(tok) for tok in tokens[1:]]
            self.set_parts(tokens[0], *parts_rest)
        else:
            raise ValueError('malformed parts string %s' % partstr)

    def set_rename(self,rename=None):
        if rename != None :
           self.headers['rename'] = rename
        elif 'rename' in self.headers :
           del self.headers['rename']

    def set_source(self,source=None):
        if source != None :
           self.headers['source'] = source
        elif 'source' in self.headers :
           del self.headers['source']

    def set_sum(self,sumflg='d',checksum=0):
        self.sumflg   =  sumflg
        self.checksum =  checksum
        self.sumstr   = '%s,%s' % (sumflg,checksum)
        self.headers['sum'] = self.sumstr

    def set_sum_str(self,sumstr):
        self.sumflg  = None
        self.sumalgo = None
        self.sumstr  = sumstr
        if sumstr == None : return

        token        = self.sumstr.split(',')
        self.sumflg  = token[0]
        self.checksum= token[1]

        # file to be removed
        if self.sumflg == 'R' : return

        # keep complete z description in sumflg
        if self.sumflg == 'z':
           self.sumflg  = sumstr

        self.parent.set_sumalgo(self.sumflg)
        self.sumalgo = self.parent.sumalgo

    def set_suffix(self):
        if self.partstr == None : return
        if self.sumstr  == None or self.sumflg == 'R' : return
        self.suffix = self.part_suffix()

    def set_pubtime(self, time=None):
        if not time:
            self.pubtime = nowstr()
        else:
            self.pubtime = time

    def set_to_clusters(self,to_clusters=None):
        if to_clusters != None :
           self.headers['to_clusters'] = to_clusters
           self.to_clusters = to_clusters.split(',')
        elif 'to_clusters' in self.headers :
           del self.headers['to_clusters']
           self.to_clusters = []

    def set_topic(self,topic_prefix,relpath):
        self.topic_prefix = topic_prefix
        self.topic        = topic_prefix
        self.subtopic     = ''

        strpath           = relpath.strip('/')
        words             = strpath.split('/')
        if len(words) > 1 :
           self.subtopic = '.'.join(words[:-1])
           self.topic   += '.' + self.subtopic

        self.topic       = self.topic.replace('..','.')

    def set_topic_url(self,topic_prefix,url):
        self.topic_prefix = topic_prefix
        self.topic        = topic_prefix
        self.subtopic     = ''
        relpath           = url.path

        # MG compat ?
        self.url          = url

        strpath           = relpath.strip('/')
        words             = strpath.split('/')
        if len(words) > 1 :
           self.subtopic = '.'.join(words[:-1])
           self.topic   += '.' + self.subtopic

        self.topic        = self.topic.replace('..','.')
        self.logger.debug("set_topic_url topic %s" % self.topic )

    def set_topic_usr(self,topic_prefix,subtopic):
        self.topic_prefix = topic_prefix
        self.subtopic     = subtopic
        self.topic        = topic_prefix + '.' + self.subtopic
        self.topic        = self.topic.replace('..','.')

    def start_timer(self):
        """ Set a timestamp at the creation of a new msg and/or at the decoding of a new raw_msg

        :return:
        """
        self.tbegin = nowflt()

    # adjust headers from -headers option

    def trim_headers(self):
        self.logger.debug("trim_headers")

        for k in self.del_headers:
            if k in self.headers : del self.headers[k]

        for k in self.add_headers:
            if k in self.headers : continue
            self.headers[k] = self.add_headers[k]

    def verify_part_suffix(self,filepath):
        filename = os.path.basename(filepath)
        token    = filename.split('.')

        try :  
                 self.suffix = '.' + '.'.join(token[-6:])
                 if token[-1] != self.part_ext :
                    return False,'not right extension',None,None,None

                 self.chunksize     = int(token[-6])
                 self.block_count   = int(token[-5])
                 self.remainder     = int(token[-4])
                 self.current_block = int(token[-3])
                 self.sumflg        = token[-2]

                 if self.current_block >= self.block_count :
                    return False,'current block wrong',None,None,None
                 if self.remainder     >= self.chunksize   :
                    return False,'remainder too big',None,None,None

                 self.length    = self.chunksize
                 self.lastchunk = self.current_block == self.block_count-1
                 self.filesize  = self.block_count * self.chunksize
                 if self.remainder  > 0 :
                    self.filesize  += self.remainder - self.chunksize
                    if self.lastchunk : self.length  = self.remainder

                 lstat     = os.stat(filepath)
                 fsiz      = lstat[stat.ST_SIZE] 

                 if fsiz  != self.length :
                    return False,'wrong file size',None,None,None

                 # compute chksum
                 self.parent.set_sumalgo(self.sumflg)
                 self.sumalgo = self.parent.sumalgo

                 self.sumalgo.set_path(filepath)
                 fp = open(filepath,'rb')
                 i  = 0
                 while i<fsiz :
                       buf = fp.read(self.bufsize)
                       if not buf : break
                       self.sumalgo.update(buf)
                       i  += len(buf)
                 fp.close()

                 if i != fsiz :
                    self.logger.warning("sr_message verify_part_suffix incomplete reading %d %d" % (i,fsiz))
                    return False,'missing data from file', None,None,None

                 # set chksum
                 self.checksum  = self.sumalgo.get_value()


                 # set partstr
                 self.partstr = 'p,%d,%d,%d,%d' %\
                   (self.chunksize,self.block_count,self.remainder,self.current_block)

                 # set sumstr
                 self.sumstr  = '%s,%s' % (self.sumflg,self.checksum)

        except :
                 self.logger.error("sr_message/verify_part_suffix: incorrect extension")
                 self.logger.debug('Exception details: ', exc_info=True)
                 return False,'incorrect extension',None,None,None

        return True,'ok',self.suffix,self.partstr,self.sumstr
