#!/usr/bin/python3

import os,random,sys

try :
         from dd_amqp         import *
         from dd_config       import *
         from dd_message      import *
         from dd_util         import *
except :
         from sara.dd_amqp    import *
         from sara.dd_config  import *
         from sara.dd_message import *
         from sara.dd_util    import *

class dd_post(dd_config):

    def __init__(self,config=None,args=None):
        dd_config.__init__(self,config,args)
        self.configure()

    def check(self):

        if self.url == None :
           self.logger.error("url required")
           sys.exit(1)

        self.chkclass = Checksum()
        self.chkclass.from_list(self.sumflg)
        self.chksum = self.chkclass.checksum

        self.msg = dd_message(self.logger)
        self.msg.set_exchange(self.exchange)
        self.msg.set_flow(self.flow)
        self.msg.set_source(self.broker.username)

    def close(self):
        self.hc_post.close()

    def connect(self):

        self.hc_post      = HostConnect( logger = self.logger )
        self.hc_post.set_url( self.broker )

        # dd_post : no loop to reconnect to broker

        if self.program_name == 'dd_post' :
           self.hc_post.loop = False
                                   
        self.hc_post.connect()

        self.pub    = Publisher(self.hc_post)
        self.pub.build()

        ex = Exchange(self.hc_post,self.exchange)
        ex.build()

    def help(self):
        self.logger.info("Usage: %s -u <url> -b <broker> ... [OPTIONS]\n" % self.program_name )
        self.logger.info("OPTIONS:")
        self.logger.info("-c   <config_file>")
        self.logger.info("-dr  <document_root>")
        if self.program_name == 'dd_watch' : self.logger.info("-e   <events>\n")
        self.logger.info("-ex  <exchange>")
        self.logger.info("-f   <flow>\n")
        self.logger.info("-h|--help\n")
        self.logger.info("-l   <logpath>")
        self.logger.info("-p   <parts>")
        self.logger.info("-tp  <topic_prefix>")
        self.logger.info("-t   <topic>")
        self.logger.info("-rn  <rename>")
        self.logger.info("-sum <sum>")
        self.logger.info("DEBUG:")
        self.logger.info("-debug")
        self.logger.info("-r  : randomize chunk posting")
        self.logger.info("-rr : reconnect between chunks")

    def instantiate(self,i=0):
        self.instance = i
        self.setlog()

    def posting(self):

        filepath = self.url.path[1:]

        # check abspath for filename

        if self.document_root != None :
           if not self.document_root in filepath :
              filepath = self.document_root + os.sep + filepath

        # verify that file exists

        if not os.path.isfile(filepath) and self.event != 'IN_DELETE' :
           self.logger.error("File not found %s " % filepath )
           return False

        # rename path given with no filename

        rename = self.rename
        if self.rename != None and self.rename[-1] == os.sep :
           rename += os.path.basename(self.url.path)
        self.msg.set_rename(rename)

        #

        self.logger.debug("vhost %s  exchange %s" % (self.broker.path,self.exchange) )


        # ==============
        # delete event...
        # ==============

        if self.event == 'IN_DELETE' :
           self.msg.set_parts(None)
           self.msg.set_sum(None)
           self.publish()


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

            # reconnect ?
            if self.reconnect :
               self.logger.info("Reconnect")
               self.hc_post.reconnect()

            i = i + 1

    def publish(self):
        self.msg.set_topic(self.topic_prefix,self.url)
        self.msg.set_notice(self.url)
        self.msg.set_event(self.event)
        self.msg.set_headers()
        self.logger.info("Key %s" % self.msg.topic )
        self.logger.info("Notice %s" % self.msg.notice)
        self.logger.info("Headers %s" % self.msg.headers)
        ok = self.pub.publish( self.msg.exchange, self.msg.topic, self.msg.notice, self.msg.headers )
        if not ok : sys.exit(1)
        self.logger.info("published")

    def watching(self, fpath, event ):

        self.event = event

        if self.document_root != None :
           bd = self.document_root
           if self.document_root[-1] != '/' : bd = bd + '/'
           fpath = fpath.replace(bd,'')

        url = self.url
        self.url = urllib.parse.urlparse('%s://%s%s'%(url.scheme,url.netloc,fpath))
        self.posting()
        self.url = url

    def watchpath(self ):

       watch_path = self.url.path
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
          if self.rename != None and self.rename[-1] != '/' and 'IN_CLOSE_WRITE' in self.events:
             self.logger.warning("renaming all modified files to %s " % self.rename )

       return watch_path


# ===================================
# MAIN
# ===================================

def main():

    post = dd_post(config=None,args=sys.argv[1:])

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

