#!/usr/bin/python3

import logging,os,random,sys

try :
         from dd_amqp        import *
         from dd_config      import *
         from dd_util        import *
except :
         from sara.dd_amqp   import *
         from sara.dd_config import *
         from sara.dd_util   import *

class dd_post(dd_config):

    def __init__(self,config=None,args=None):
        dd_config.__init__(self,config,args)
        self.configure()

    def check(self):

        if self.program_name == 'dd_post' :
           if self.logpath != None : self.logpath = None

        self.setlog()

        self.source.set(self.source.get())
        if not self.source.protocol in [ 'file', 'ftp', 'http','sftp'] : self.source.error = True
        if self.source.protocol in ['ftp','sftp'] and \
           self.source.user     == None   :                              self.source.error = True
        if self.source.error :
           self.logger.error("source_url %s " % self.source.get())

        self.post_broker.set(self.post_broker.get())
        if not self.post_broker.protocol in ['amqp','amqps'] or \
           self.post_broker.user     == None   or \
           self.post_broker.password == None   or \
           self.post_broker.error :
           self.logger.error("post_broker error %s " % self.post_broker.error)
           self.logger.error("post_broker url %s "   % self.post_broker.get())

        self.default_exchange  = 'sx_' + self.post_broker.user
        self.exchange_name     = self.default_exchange
        if self.post_exchange != None :
           self.exchange_name = self.post_exchange

    def close(self):
        self.hc_post.close()

    def configure(self):

        # defaults general and proper to dd_post

        self.defaults()
        self.source    = URL()
        self.reconnect = False

        # arguments from command line

        self.args(self.user_args)

        # config from file

        self.config(self.user_config)

        # verify all settings

        self.check()


    def connect(self):

        self.hc_post      = HostConnect( logger = self.logger )
        self.hc_post.set_url( self.post_broker )

        # dd_post : no loop to reconnect to broker

        if self.program_name == 'dd_post' :
           self.hc_post.loop = False
                                   
        self.hc_post.connect()

        self.pub    = Publisher(self.hc_post)
        self.pub.build()

        ex = Exchange(self.hc_post,self.exchange_name)
        ex.build()

    def help(self):
        self.logger.info("Usage: %s -s <source-url> -pb <broker-url> ... [OPTIONS]\n" % self.program_name )
        self.logger.info("OPTIONS:")
        self.logger.info("-c  <config_file>")
        self.logger.info("-dr <document_root>")
        self.logger.info("-dp <destination_path>")
        self.logger.info("-bz <blocksize>")
        self.logger.info("-f  <flags>")
        if self.program_name == 'dd_watch': self.logger.info("-l  <logpath>")
        self.logger.info("-pe <exchange>")
        self.logger.info("-pk <topic key>")
        self.logger.info("-t  <tag>\n")
        self.logger.info("DEBUG:")
        self.logger.info("-debug")
        self.logger.info("-r  : randomize chunk posting")
        self.logger.info("-rr : reconnect between chunks")

    def posting(self):

        filepath = self.source.path

        # check abspath for filename

        if self.document_root != None :
           if not self.document_root in filepath :
              filepath = self.document_root + os.sep + filepath

        # verify that file exists

        if not os.path.isfile(filepath):
           self.logger.error("File not found %s " % filepath )
           return False

        # fix destination path if needed

        notice_path = self.destination_path
        notice_url  = self.source.get()

        # no destination given

        if self.destination_path == None :
           notice_path = self.source.path
           notice_url  = notice_url.replace(notice_path,'')

        # destination path given with no filename

        elif self.destination_path[-1] == os.sep :
             notice_path += os.path.basename(self.source.path)

        # build product exchange key

        post_key = Key()
        post_key.set(self.post_broker.user, notice_path )
        str_key  = post_key.get()

        if self.post_topic_key != None :
           str_key = self.post_topic_key

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

        self.logger.debug("vhost %s  exchange_name %s" % (self.post_broker.vhost,self.exchange_name) )

        i  = 0
        while i < N:

            c = chunk.get( rparts[i] )
            blocksize, block_count, remainder, current_block, sum_data = c

            notice.set_chunk(blocksize, block_count, remainder, current_block, self.flags_str, sum_data)
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
               self.hc_post.reconnect()

            i = i + 1

    def watching(self, fpath ):

        if self.document_root != None :
           bd = self.document_root
           if self.document_root[-1] != '/' : bd = bd + '/'
           fpath = fpath.replace(bd,'')

        spath = self.source.path
        self.source.path = fpath

        self.posting()

        self.source.path = spath

    def watchpath(self ):

       watch_path = self.source.path
       if watch_path == None : watch_path = ''

       if self.document_root != None :
          if not self.document_root in watch_path :
             watch_path = self.document_root + os.sep + watch_path

       if not os.path.exists(watch_path):
          self.logger.error("Not found %s " % watch_path )
          sys.exit(1)

       if os.path.isfile(watch_path):
          self.logger.info("Watching file %s " % watch_path )

       if os.path.isdir(watch_path):
          self.logger.info("Watching directory %s " % watch_path )

       return watch_path


# ===================================
# MAIN
# ===================================

def main():

    post = dd_post(config=None,args=sys.argv[1:])

    try :
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

