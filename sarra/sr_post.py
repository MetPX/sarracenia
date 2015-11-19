#!/usr/bin/python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SarraDocumentation
#
# sr_post.py : python3 program allowing users to post an available product
#
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Jun Hu         - Shared Services Canada
#  Last Changed   : Sep 22 10:41:32 EDT 2015
#  Last Revision  : Sep 22 10:41:32 EDT 2015
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
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

import os,random,sys

try :
         from sr_amqp         import *
         from sr_config       import *
         from sr_message      import *
         from sr_util         import *
except :
         from sarra.sr_amqp    import *
         from sarra.sr_config  import *
         from sarra.sr_message import *
         from sarra.sr_util    import *

class sr_post(sr_config):

    def __init__(self,config=None,args=None):
        sr_config.__init__(self,config,args)
        self.configure()

    def check(self):

        if self.url == None :
           self.logger.error("url required")
           sys.exit(1)

        self.chkclass = Checksum()
        self.chkclass.from_list(self.sumflg)
        self.chksum = self.chkclass.checksum

        # sarra exchange default value is xs_username
        # username being the broker's

        if self.exchange == None :
           self.exchange = 'xs_%s' % self.broker.username

        self.msg = sr_message(self.logger)
        self.msg.set_exchange(self.exchange)
        self.msg.set_flow(self.flow)
        self.msg.set_flow(self.flow)
        self.msg.set_to_clusters(self.to_clusters)
        if self.to_clusters == None :
           self.logger.error("-to option is mandatory\n")
           self.help()
           sys.exit(1)

    def close(self):
        self.hc_post.close()

    def configure(self):

        # defaults general and proper to sr_post

        self.defaults()

        # installation general configurations and settings

        self.general()

        # arguments from command line

        self.args(self.user_args)

        # config from file

        self.config(self.user_config)

        # verify all settings

        self.check()


    def connect(self):

        self.hc_post      = HostConnect( logger = self.logger )
        self.hc_post.set_url( self.broker )

        # sr_post : no loop to reconnect to broker

        if self.program_name == 'sr_post' :
           self.hc_post.loop = False
                                   
        self.hc_post.connect()

        self.pub    = Publisher(self.hc_post)
        self.pub.build()

    def help(self):
        self.logger.info("Usage: %s -u <url> -b <broker> ... [OPTIONS]\n" % self.program_name )
        self.logger.info("OPTIONS:")
        self.logger.info("-b   <broker>          default:amqp://guest:guest@localhost/")
        self.logger.info("-c   <config_file>")
        self.logger.info("-dr  <document_root>   default:None")
        if self.program_name == 'sr_watch' : self.logger.info("-e   <events>          default:IN_CLOSE_WRITE\n")
        self.logger.info("-ex  <exchange>        default:xs_\"broker.username\"")
        self.logger.info("-f   <flow>            default:None\n")
        self.logger.info("-h|--help\n")
        self.logger.info("-l   <logpath>         default:stdout")
        self.logger.info("-p   <parts>           default:1")
        self.logger.info("-to  <name1,name2,...> defines target clusters, mandatory")
        self.logger.info("-tp  <topic_prefix>    default:v02.post")
        self.logger.info("-sub <subtopic>        default:'path.of.file'")
        self.logger.info("-rn  <rename>          default:None")
        self.logger.info("-sum <sum>             default:d")
        self.logger.info("DEBUG:")
        self.logger.info("-debug")
        self.logger.info("-r  : randomize chunk posting")
        self.logger.info("-rr : reconnect between chunks")

    def instantiate(self,i=0):
        self.instance = i
        self.setlog()

    def posting(self):

        filepath = '/' + self.url.path.strip('/')

        # urllib keeps useless repetitive '/' so rebuild url smartly
        if filepath != self.url.path :
           if self.document_root == None and self.url.scheme[-3:] == 'ftp' :
              filepath = '/' + filepath
           urlstr   = self.url.scheme + '://' + self.url.netloc + filepath
           self.url = urllib.parse.urlparse(urlstr)

        # check abspath for filename

        filepath = self.url.path
        if self.document_root != None :
           if str.find(filepath,self.document_root) != 0 :
              filepath = self.document_root + os.sep + filepath
              filepath = filepath.replace('//','/')

        # verify that file exists

        if not os.path.isfile(filepath) and self.event != 'IN_DELETE' :
           self.logger.error("File not found %s " % filepath )
           return False

        # verify part file... if it is ok

        if self.partflg == 'p' :
           ok,message = self.verify_p_file(filepath)
           if not ok:
              self.logger.error("partflg set to p but %s for file  %s " % (message,filepath))
              return False

        # rename path given with no filename

        rename = self.rename
        if self.rename != None and self.rename[-1] == os.sep :
           rename += os.path.basename(self.url.path)

        # make sure a part file has a part name
        if self.rename != None and self.partflg == 'p' :
           if not self.msg.suffix in rename :
              rename += self.msg.suffix

        self.msg.set_rename(rename)

        #

        self.logger.info("broker(%s) user(%s) vhost(%s)  exchange(%s)" % \
        (self.broker.hostname,self.broker.username,self.broker.path,self.exchange) )

        # ==============
        # delete event...
        # ==============

        if self.event == 'IN_DELETE' :
           self.msg.set_parts(None)
           self.msg.set_sum(sumflg='R')
           self.publish()
           return

        # ==============
        # p partflg special case
        # ==============

        if self.partflg == 'p' :
           blocksize, block_count, remainder, current_block, sum_data = self.p_chunk
           self.msg.set_parts('p', blocksize, block_count, remainder, current_block)
           self.msg.set_sum(self.sumflg,sum_data)
           self.publish()
           return

        # ==============
        # Chunk set up
        # ==============

        chunk  = Chunk(self.blocksize,self.chksum,filepath)
        N      = chunk.get_Nblock()

        # ==============
        # Randomize
        # ==============

        rparts = list(range(0,N))

        # randomize chunks
        if self.randomize and N>1 :
           i = 0
           while i < N/2+1 :
               j         = random.randint(0,N-1)
               tmp       = rparts[j]
               rparts[j] = rparts[i]
               rparts[i] = tmp
               i = i + 1

        # ==============
        # loop on chunk
        # ==============

        i  = 0
        while i < N:

            # build message
 
            c = chunk.get( rparts[i] )
            blocksize, block_count, remainder, current_block, sum_data = c

            self.msg.set_parts(self.partflg, blocksize, block_count, remainder, current_block)
            self.msg.set_sum(self.sumflg,sum_data)

            self.publish()

            i = i + 1

            # reconnect ?
            if self.reconnect and i<N :
               self.logger.info("Reconnect")
               self.hc_post.reconnect()

    def publish(self):
        if self.subtopic == None :
           self.msg.set_topic_url(self.topic_prefix,self.url)
        else :
           self.msg.set_topic_usr(self.topic_prefix,self.subtopic)

        self.msg.set_notice(self.url)
        self.msg.set_hdrstr()
        self.logger.info("%s '%s' %s" % (self.msg.topic,self.msg.notice,self.msg.hdrstr))
        ok = self.pub.publish( self.msg.exchange, self.msg.topic, self.msg.notice, self.msg.headers )
        if not ok : sys.exit(1)
        self.logger.info("published")

    def verify_p_file(self,filepath):
        ok,message = self.msg.verify_part_suffix(filepath)

        if ok :
           self.p_chunk = (self.msg.chunksize, self.msg.block_count, self.msg.remainder, self.msg.current_block, self.msg.checksum)

        return ok,message

    def watching(self, fpath, event ):

        self.event = event

        if self.document_root != None :
           fpath = fpath.replace(self.document_root,'')
           if fpath[0] == '/' : fpath = fpath[1:]

        url = self.url
        self.url = urllib.parse.urlparse('%s://%s/%s'%(url.scheme,url.netloc,fpath))
        self.posting()
        self.url = url

    def watchpath(self ):

       watch_path = self.url.path
       if watch_path == None : watch_path = ''

       if self.document_root != None :
          if not self.document_root in watch_path :
             watch_path = self.document_root + os.sep + watch_path

       watch_path = watch_path.replace('//','/')

       if not os.path.exists(watch_path):
          self.logger.error("Not found %s " % watch_path )
          sys.exit(1)

       if os.path.isfile(watch_path):
          self.logger.info("Watching file %s " % watch_path )

       if os.path.isdir(watch_path):
          self.logger.info("Watching directory %s " % watch_path )
          if self.rename != None and self.rename[-1] != '/' and 'IN_CLOSE_WRITE' in self.events:
             self.logger.warning("renaming all modified files to %s " % self.rename )

       return watch_path


# ===================================
# MAIN
# ===================================

def main():

    post = sr_post(config=None,args=sys.argv[1:])

    try :
             post.instantiate()
             post.connect()
             post.posting()
             post.close()
    except :
             (stype, value, tb) = sys.exc_info()
             post.logger.error("Type: %s, Value:%s\n" % (stype, value))
             sys.exit(1)


    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()

