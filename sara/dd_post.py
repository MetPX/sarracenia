#!/usr/bin/python3

import getopt,hashlib,os,random,re,socket,stat,sys,time,ssl

from hashlib import md5

try :
         from dd_amqp        import *
         from dd_config      import *
         from dd_util        import *
except :
         from sara.dd_amqp   import *
         from sara.dd_config import *
         from sara.dd_util   import *

class dd_post(dd_config):

    def __init__(self,logger,config=None,args=None):

        self.logger = logger

        self.defaults()
        self.config(config)
        self.args(args)

        self.check()

    def check(self):

        self.source.set(self.source.get())
        if not self.source.protocol in [ 'file', 'http','sftp'] : self.source.error = True
        if self.source.protocol == 'sftp' and \
           self.source.user     == None   :               self.source.error = True
        if self.source.error :
           self.logger.error("source url %s " % self.source.get())

        self.destination.set(self.destination.get())
        if not self.destination.protocol in ['amqp','amqps'] or \
           self.destination.user     == None   or \
           self.destination.password == None   or \
           self.destination.error :
           self.logger.error("destination url %s " % self.destination.get())

    def close(self):
        self.hc_dst.close()

    def connect(self):

        self.hc_dst = HostConnect( self.destination.host, self.destination.port, \
                                   self.destination.user, self.destination.password, \
                                   ssl= self.destination.protocol == 'amqps', logger = self.logger, loop=False)
        self.hc_dst.connect()

        self.pub    = Publisher(self.hc_dst)
        self.pub.build()

        self.exchange_name = 'sx_' + self.destination.user
        ex = Exchange(self.hc_dst,self.exchange_name)
        ex.build()

    def defaults(self):

        self.str_flags   = 'd'
        self.blocksize   = 0
        self.tag         = 'default'
        self.randomize   = False
        self.basedir     = None
        self.source      = URL()
        self.destination = URL()
        self.dest_path   = None

        self.watch_dir   = None

        self.destination.protocol = 'amqp'
        self.destination.host     = 'localhost'
        self.destination.user     = 'guest'
        self.destination.password = 'guest'

        self.flags       = Flags()
        self.flags.from_str(self.str_flags)

        self.reconnect   = False

    def posting(self):

        filepath = self.source.path

        # check abspath for filename

        if self.basedir != None :
           if not self.basedir in filepath :
              filepath = self.basedir + os.sep + filepath

        # verify that file exists

        if not os.path.isfile(filepath):
           self.logger.error("File not found %s " % filepath )
           return False

        # fix destination path if needed

        notice_path = self.dest_path
        notice_url  = self.source.get()

        # no destination given

        if self.dest_path == None :
           notice_path = self.source.path
           notice_url  = notice_url.replace(notice_path,'')

        # destination path given with no filename

        elif self.dest_path[-1] == os.sep :
             notice_path += os.path.basename(self.source.path)

        # build product exchange key

        post_key = Key()
        post_key.set(self.destination.user, notice_path )
        str_key  = post_key.get()

        # build notice class

        notice = Notice()
        notice.set_source(notice_url,notice_path)
        notice.set_tag(self.tag)


        # ==============
        # Chunk set up
        # ==============

        chunk  = Chunk(self.blocksize,self.flags.checksum,filepath)
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

            c = chunk.get( rparts[i] )
            blocksize, block_count, remainder, current_block, sum_data = c

            notice.set_chunk(blocksize, block_count, remainder, current_block, self.str_flags, sum_data)
            str_notice = notice.get()

            self.logger.info("Key %s" % str_key )
            self.logger.info("Notice %s" % str_notice )

            # publish
            ok = self.pub.publish( self.exchange_name, str_key, str_notice, os.path.basename(notice_path) )
            if not ok :
               sys.exit(1)

            # reconnect ?
            if self.reconnect :
               self.logger.info("Reconnect")
               self.hc_dst.reconnect()

            i = i + 1


    def watching(self, fpath ):

        if self.basedir != None :
           bd = self.basedir
           if self.basedir[-1] != '/' : bd = bd + '/'
           fpath = fpath.replace(bd,'')

        spath = self.source.path
        self.source.path = fpath

        self.posting()

        self.source.path = spath


# ===================================
# MAIN
# ===================================

import logging

def help(logger):
    logger.info("Usage: dd_post [-c configfile] [-r] [-bz blocksize] [-t tag] [-f flags] [-bd basedir] -s <source-url> -b <broker-url> -d destination")
    logger.info("default blocksize 0")
    logger.info("default tag ''")

def main():

    LOG_FORMAT = ('%(asctime)s [%(levelname)s] %(message)s')
    logger     = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    try :
             post = dd_post(logger,config=None,args=sys.argv)
             post.connect()
             post.posting()
             post.close()
    except :
             help(logger)


    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()

