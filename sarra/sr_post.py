#!/usr/bin/env python3
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

#============================================================
# DECLARE TRICK for false self.poster

from collections import *

#============================================================

try :
         from sr_amqp          import *
         from sr_cache         import *
         from sr_config        import *
         from sr_instances     import *
         from sr_message       import *
         from sr_util          import *
except :
         from sarra.sr_amqp      import *
         from sarra.sr_cache     import *
         from sarra.sr_config    import *
         from sarra.sr_instances import *
         from sarra.sr_message   import *
         from sarra.sr_util     import *

class sr_post(sr_instances):

    def __init__(self,config=None,args=None,action=None):
        self.instances = 1
        sr_instances.__init__(self,config,args,action)
        self.configure()
        self.in_error  = False
        self.recursive = True

    def check(self):
        self.logger.debug("sr_post check")

        # enforcing post_broker

        if self.post_broker == None :
           if self.broker   != None :
              self.post_broker = self.broker
              self.logger.warning("use post_broker to set broker")

        # enforcing post_exchange

        if self.post_exchange == None :
           if self.exchange   != None :
              self.post_exchange = self.exchange
              self.logger.warning("use post_exchange to set exchange")

        if self.post_exchange  == None :
           self.post_exchange   = 'xs_%s' % self.post_broker.username

        # verify post_base_dir

        if self.post_base_dir == None :
           if self.post_document_root != None :
              self.post_base_dir = self.post_document_root
              self.logger.warning("use post_base_dir instead of post_document_root")
           elif self.document_root != None :
              self.post_base_dir = self.document_root
              self.logger.warning("use post_base_dir instead of document_root")


        # verify post_base_url

        self.in_error = False
        if self.post_base_url == None :
           self.logger.error("post_base_url required")
           self.in_error = True
           self.help()
           return

        # set a default to_clusters if none given

        if self.to_clusters == None:
            self.to_clusters = self.post_broker.hostname

        # masks != [] accept only what matches given accept/reject options
        # masks == [] accept everything (because there is no match to do)

        self.accept_unmatch = self.masks == []

        # resetting logs if needed

        if self.program_name != 'sr_watch' : self.setlog()

        # check for caching
      
        if self.caching == True : self.caching = 300
        if self.caching :
           self.cache = sr_cache(self)
           self.cache.open()
           self.execfile("on_heartbeat",'heartbeat_cache')
           self.on_heartbeat_list.append(self.on_heartbeat)

        # ========================================
        # BEGIN TRICK for false self.poster

        addmodule = namedtuple('AddModule', ['post'])
        self.poster = addmodule(self.post_url)

        if self.poster.post == self.post_url :
           self.logger.debug("MY POSTER TRICK DID WORK !!!")

    def post_url(self,post_exchange,url,to_clusters,\
                      partstr=None,sumstr=None,rename=None,filename=None,mtime=None,atime=None,mode=None,link=None):
        self.logger.warning("instead of using self.poster.post(post_exchange,url... use self.post(post_exchange,post_base_url,post_relpath...")

        urlstr        = url.geturl()
        post_relpath  = url.path
        post_base_url = urlstr.replace(post_relpath,'')

        return self.post(post_exchange,post_base_url,post_relpath,to_clusters,partstr,sumstr,rename,mtime,atime,mode,link)

    # ENDOF TRICK for false self.poster
    # ========================================

    def close(self):
        self.logger.debug("sr_post close")

        if self.post_hc :
           self.post_hc.close()
        
        if self.cache :
           self.cache.save()
           self.cache.close()

        self.connected = False


    def connect(self):
        self.logger.debug("sr_post connect")

        # sr_post : no loop to reconnect to broker

        self.loop = True
        if self.program_name == 'sr_post' :
           self.loop = False

        # message

        self.msg = sr_message( self )

        # =============
        # posting
        # =============

        self.post_hc      = HostConnect( self.logger )
        self.post_hc.set_pika(self.use_pika)
        self.post_hc.set_url(self.post_broker)
        self.post_hc.loop = self.loop
        self.post_hc.connect()

        self.publisher = Publisher(self.post_hc)
        self.publisher.build()

        self.logger.info("Output AMQP broker(%s) user(%s) vhost(%s)" % \
                        (self.post_broker.hostname,self.post_broker.username,self.post_broker.path) )

        # =============
        # setup message publish
        # =============

        self.msg.user                 = self.post_broker.username
        self.msg.publisher            = self.publisher
        self.msg.pub_exchange         = self.post_exchange
        self.msg.post_exchange_split  = self.post_exchange_split

        self.logger.info("Output AMQP exchange(%s)" % self.msg.pub_exchange )

        self.connected        = True

        # =============
        # amqp resources
        # =============

        self.declare_exchanges()

    def help(self):
        print("\nUsage: %s -u <url> -pb <post_broker> ... [OPTIONS]\n" % self.program_name )
        print("version: %s \n" % sarra.__version__ )
        print("OPTIONS:")
        print("-pb|post_broker   <broker>          default:amqp://guest:guest@localhost/")
        print("-c|config   <config_file>")
        print("-pbd <post_base_dir>   default:None")
        print("-e   <events>          default:create|delete|follow|link|modify\n")
        print("-pe  <post_exchange>        default:xs_\"broker.username\"")
        print("-h|--help\n")
        print("-parts [0|1|sz]        0-computed blocksize (default), 1-whole files (no partitioning), sz-fixed blocksize")
        print("-to  <name1,name2,...> defines target clusters, default: ALL")
        print("-tp  <topic_prefix>    default:v02.post")
        print("-sub <subtopic>        default:'path.of.file'")
        print("-rn  <rename>          default:None")
        print("-sum <sum>             default:d")
        print("-caching               default:enable caching")
        print("-reset                 default:enable reset")
        print("-path <path1... pathN> default:required")
        print("-on_post <script>      default:None")
        print("DEBUG:")
        print("-debug")
        print("-r  : randomize chunk posting")
        print("-rr : reconnect between chunks\n")

    def move(self,src,dst):
        self.logger.warning("file moved support not implemented. Event ignored.")

    # =============
    # __on_post__ internal posting of message
    # =============

    def __on_post__(self):
        self.logger.debug("sr_post __on_post__")

        # *** special retransmit setting...
        # if a queue_name is provided

        if self.queue_name != None :
           self.msg.headers['exchange'] = self.msg.exchange
           self.msg.exchange = ''
           self.msg.topic    =  self.queue_name

        # should always be ok
        ok = True
        if self.event in self.events:
           for plugin in self.on_post_list:
               if not plugin(self): return False

           ok = self.msg.publish()

        return ok

    def overwrite_defaults(self):
        self.logger.debug("sr_post overwrite_defaults")

        self.post_broker   = None 
        self.post_exchange = None 
        self.post_base_url = None 

        self.post_hc = None
        self.cache   = None

        self.key     = None
        self.value   = None

        self.logger.debug("sr_post overwrite_defaults Done")


    def post(self,post_exchange,post_base_url,post_relpath,to_clusters, \
             partstr=None,sumstr=None,rename=None,mtime=None,atime=None,mode=None,link=None):

        urlstr = post_base_url + '/' + post_relpath

        self.logger.debug("sr_post post %s caching(%s) post_exchange(%s)" % (urlstr,self.caching,post_exchange) )

        # apply accept/reject
        if not self.isMatchingPattern(urlstr,self.accept_unmatch) :
           self.logger.debug("post of %s Rejected by accept/reject options" % urlstr )
           return True  # need to return true because this isn´t a failure.

        # if caching is enabled make sure it was not already posted

        if self.caching :

           new_post = self.cache.check(str(sumstr),post_relpath,partstr)

           if new_post :

              # delete
              if sumstr.startswith('R,'):
                 self.cache.delete_path(post_relpath)

              # link - never store them, message contains whole payload.
              elif sumstr.startswith('L,'):
                 self.cache.delete_path(post_relpath)

              else:
                 self.logger.info("caching %s"% post_relpath )

           # modified, or repost
           else:
                self.logger.debug("skipped already posted %s %s %s" % (post_relpath,partstr,sumstr))
                return True
                 
        # set message exchange
        self.msg.exchange = post_exchange
        
        # set message topic
        self.msg.set_topic(self.topic_prefix,post_relpath)
        if self.subtopic != None :
           self.msg.set_topic_usr(self.topic_prefix,self.subtopic)

        # set message notice
        self.msg.set_notice(post_base_url,post_relpath)

        # set message headers
        self.msg.headers = {}

        self.msg.headers['to_clusters'] = to_clusters

        if partstr  != None : self.msg.headers['parts']        = partstr
        if sumstr   != None : self.msg.headers['sum']          = sumstr
        if rename   != None : self.msg.headers['rename']       = rename
        if mtime    != None : self.msg.headers['mtime']        = mtime
        if atime    != None : self.msg.headers['atime']        = atime
        if mode     != None : self.msg.headers['mode']         = "%o" % ( mode & 0o7777 )
        if link     != None : self.msg.headers['link']         = link

        if self.cluster != None : self.msg.headers['from_cluster']    = self.cluster
        if self.source  != None : self.msg.headers['source']          = self.source

        if self.key     != None : self.msg.headers[self.key]          = self.value

        self.msg.trim_headers()

        ok = self.__on_post__()

        self.key   = None
        self.value = None

        return ok

    def post_local_file(self,path,post_exchange,post_base_url,post_relpath,to_clusters,sumflg='d',rename=None):
        self.logger.debug("sr_post post_local_file %s post_exchange(%s) " % (path,post_exchange) )
    
        # set partstr

        lstat   = os.stat(path)
        fsiz    = lstat[stat.ST_SIZE]

        mtime = timeflt2str(lstat.st_mtime)
        atime = timeflt2str(lstat.st_atime)
        mode  = lstat[stat.ST_MODE]

        partstr = '1,%d,1,0,0' % fsiz

        # set sumstr

        self.set_sumalgo(sumflg)
        sumalgo = self.sumalgo

        # bad flag provided
        if self.lastflg != sumflg : sumflg = self.lastflg

        if   sumflg == '0' :
             sumstr = '0,%d' % random.randint(0,100)

        elif sumflg == 'R' :
             sumstr = 'R,%d' % random.randint(0,100)

        elif len(sumflg) > 2 and sumflg[:2] == 'z,' :
             sumstr = sumflg

        # compute checksum
        else:
              sumalgo.set_path(path)

              fp = open(path,'rb')
              i  = 0
              while i<fsiz :
                    buf = fp.read(self.bufsize)
                    if not buf: break
                    sumalgo.update(buf)
                    i  += len(buf)
              fp.close()

              checksum = sumalgo.get_value()
              sumstr   = '%s,%s' % (sumflg,checksum)

        # post

        ok = self.post(post_exchange,post_base_url,post_relpath,to_clusters,partstr,sumstr,rename,mtime,atime,mode)

        self.logger.debug("sr_post post_local_file %s post_exchange(%s)" % (path,post_exchange ))

        return ok

    def post_local_inplace(self,path,post_exchange,post_base_url,post_relpath,to_clusters,chunksize=0,sumflg='d',rename=None):
        self.logger.debug("sr_post post_local_inplace")

        ok       = False
        lstat    = os.stat(path)
        fsiz     = lstat[stat.ST_SIZE]

        mtime = timeflt2str(lstat.st_mtime)
        atime = timeflt2str(lstat.st_atime)
        mode  = lstat[stat.ST_MODE]

        # file too small for chunksize

        if chunksize <= 0 or chunksize >= fsiz : 
           ok = self.post_local_file(path,post_exchange,post_base_url,post_relpath,to_clusters,sumflg,rename)
           return ok

        # count blocks and remainder

        block_count = int(fsiz/chunksize)
        remainder   =     fsiz%chunksize
        if remainder > 0 : block_count = block_count + 1

        # info setup

        self.set_sumalgo(sumflg)
        sumalgo  = self.sumalgo

        # bad flag provided
        if self.lastflg != sumflg : sumflg = self.lastflg

        blocks   = list(range(0,block_count))

        # randomize chunks

        if self.randomize :
           i = 0
           while i < block_count/2+1 :
               j         = random.randint(0,block_count-1)
               tmp       = blocks[j]
               blocks[j] = blocks[i]
               blocks[i] = tmp
               i = i + 1


        # loop on chunks

        i = 0
        while i < block_count :
              current_block = blocks[i]

              offset = current_block * chunksize
              length = chunksize

              last   = current_block == block_count-1
              if last and remainder > 0 :
                 length = remainder

              # set partstr

              partstr = 'i,%d,%d,%d,%d' %\
                        (chunksize,block_count,remainder,current_block)

              # compute checksum if needed

              if len(sumflg) > 2 and sumflg[:2] == 'z,' :
                 sumstr = sumflg
              else:
                 bufsize = self.bufsize
                 if length < bufsize : bufsize = length

                 sumalgo.set_path(path)

                 fp = open(path,'rb')
                 if offset != 0 : fp.seek(offset,0)
                 t  = 0
                 while t<length :
                       buf = fp.read(bufsize)
                       if not buf: break
                       sumalgo.update(buf)
                       t  += len(buf)
                 fp.close()

                 checksum = sumalgo.get_value()
                 sumstr   = '%s,%s' % (sumflg,checksum)

              # post

              ok = self.post(post_exchange,post_base_url,post_relpath,to_clusters,partstr,sumstr,rename,mtime,atime,mode)
              if not ok : return ok

              # reconnect ?

              if self.reconnect:
                 self.logger.info("Reconnect")
                 self.post_hc.reconnect()

              self.logger.debug("sr_post posted part %i of %i" % (i, block_count-1) )
              i = i + 1

        return ok


    def post_local_part(self,path,post_exchange,post_base_url,post_relpath,to_clusters,rename=None):
        self.logger.debug("sr_post post_local_part")

        # verify part suffix is ok

        ok,message,suffix,partstr,sumstr = self.msg.verify_part_suffix(path)

        if not ok:
           self.logger.error("partflg set to p but %s for file  %s " % (message,path))
           return ok

        # make sure suffix is also in rename

        if rename != None and not suffix in rename : rename += suffix

        lstat   = os.stat(path)

        mtime = timeflt2str(lstat.st_mtime)
        atime = timeflt2str(lstat.st_atime)
        mode  = lstat[stat.ST_MODE]

        ok = self.post(post_exchange,post_base_url,post_relpath,to_clusters,partstr,sumstr,rename,mtime,atime,mode)

        return ok

    def posting(self):
        self.logger.debug("sr_post posting %s" % ( self.fpath ) )

        filepath = self.fpath

        # verify that file exists

        if not os.path.islink(filepath) and ( not os.path.exists(filepath) and self.event != 'delete' ):
           self.logger.error("File not found %s " % filepath )
           return False

        # rename path given with no filename

        rename = self.rename
        if self.rename != None and self.rename[-1] == os.sep :
           rename += os.path.basename(self.fpath)

        # strip option when no rename option
        # strip 'N' heading directories from post_relpath

        if self.strip != 0:
           if rename != None :
              self.logger.error("option strip used with option rename conflicts")
              sys.exit(1)
           strip  = self.strip
           token  = self.post_relpath.split(os.sep)
           if self.post_relpath[0] == os.sep  : strip += 1
           if len(token) <= self.strip : strip = len(token)-1
           rename = os.sep+os.sep.join(token[strip:])
              
        # ==============
        # delete event...
        # ==============

        if self.event == 'delete' :
           hash = sha512()
           hash.update(bytes(os.path.basename(filepath), encoding='utf-8'))
           ok = self.post(self.post_exchange,self.post_base_url,self.post_relpath,self.to_clusters,None, \
                    'R,%s' % hash.hexdigest(), rename)

           if not ok : sys.exit(1)
           return

        
        # ==============
        # link event...
        # ==============

        """
        table:          behaviour
        Link  Follow 
        False False     ignore the symlink
        False True      file is posted using the link name, rathter than the value of the link.
        True  False     Link is posted.
        True  True      Link is posted, and the link followed and that is posted also.
        """

        if os.path.islink(filepath):
           if 'link' in self.events: 
               linkdest = os.readlink(filepath)
               hash = sha512()
               hash.update( bytes( linkdest, encoding='utf-8' ) )
               ok = self.post( self.post_exchange,self.post_base_url,self.post_relpath,self.to_clusters,None, \
                    'L,%s' % hash.hexdigest(), rename, link=linkdest )

               if not ok : sys.exit(1)

               filepath = os.path.realpath(filepath)

               if self.follow_symlinks : self.watching(filepath,self.event)

               return True

          # Note: if (not link) and follow -> path is unchanged, so file is created through linked name.

        # ==============
        # p partflg special case
        # ==============

        if self.partflg == 'p' :
           ok = self.post_local_part(filepath,self.post_exchange,self.post_base_url,self.post_relpath,self.to_clusters,rename)
           if not ok : sys.exit(1)
           return

        # ==============
        # 0 partflg : compute blocksize if necessary (huge file) for the file Peter's algo
        # ==============

        elif self.partflg.startswith('0') and (( len(self.partflg) == 1 ) or ( self.partflg[1] == ',' )):
           lstat   = os.stat(filepath)
           fsiz    = lstat[stat.ST_SIZE]

           # compute blocksize from Peter's algo

           # tfactor of 50Mb
           if len(self.partflg) > 1:
               tfactor = self.blocksize
           else:
               tfactor = 50 * 1024 * 1024

           # file > 5Gb  block of 500Mb
           if   fsiz > 100 * tfactor :
                self.blocksize = 10 * tfactor

           # file [ 500Mb, 5Gb]  = 1/10 of fsiz
           elif fsiz > 10 * tfactor :
                self.blocksize = int((fsiz+9)/10)
           # file [ 50Mb, 500Mb[  = 1/3 of fsiz
           elif fsiz > tfactor :
                self.blocksize = int((fsiz+2)/ 3)

        # ==============
        # 1 force whole files to be sent.
        # ==============

        elif self.partflg == '1':
           self.blocksize = 0

        # ==============
        # partflg 'i' left : fixed blocksize specified.
        # ==============

        else:
           if self.blocksize == 0 :
              self.logger.error("parts %s without blocksize" % self.parts)
              sys.exit(1)

        # ===================
        # post file in blocks (inplace)
        # ===================

        if self.blocksize > 0 :
           ok = self.post_local_inplace(filepath,self.post_exchange,self.post_base_url,self.post_relpath, \
                                                  self.to_clusters,self.blocksize,self.sumflg,rename)
           if not ok : sys.exit(1)
           return

        # ==============
        # whole file
        # ==============

        ok = self.post_local_file(filepath,self.post_exchange,self.post_base_url,self.post_relpath,self.to_clusters,self.sumflg,rename)
        if not ok: sys.exit(1)
        return


    def scandir_and_post(self,path,recursive):
        self.logger.debug("sr_post scandir_and_post %s " % path)

        if not os.path.isdir(path):
            self.logger.error("sr_post scandir_and_post not a directory %s " % path)
            return False

        try :
            entries = os.listdir(path)
            for e in entries:
                   newpath = path + os.sep + e

                   if os.path.isfile(newpath) and os.access(newpath,os.R_OK):
                      self.watching(newpath,'modify')
                      continue

                   if os.path.isdir(newpath) and recursive :
                      self.scandir_and_post(newpath,recursive)
                      continue

                   self.logger.warning("skipped : %s " % newpath)
        except: 
            self.logger.error("sr_post scandir_and_post not accessible  %s " % path)
            return False

        return True

    def watching(self, fpath, event, key=None, value=None ):
        self.logger.debug("sr_post watching %s, ev=%s (%s,%s)" % ( fpath, event, key, value ) )

        if sys.platform == 'win32' : # put the slashes in the right direction on windows
           fpath = fpath.replace('\\','/')

        self.event = event
        self.fpath = fpath

        self.post_relpath = fpath

        if self.post_base_dir != None :
           pbd = self.post_base_dir
           if pbd in fpath :
              self.post_relpath = fpath.replace(pbd,'',1)
           elif fpath[0] != os.sep :
              self.fpath = pbd + os.sep + fpath
           else :
              self.logger.error("post_base_dir %s not present in %s" % (pbd,fpath))
              self.logger.error("no posting")
              return False

           if value != None and pbd in value :
              value = value.replace(dr,'',1)

        self.logger.debug("sr_post watching %s, ev=%s, url=%s" % ( fpath, event, self.post_base_url+self.post_relpath ) )
        self.key     = key
        self.value   = value

        self.posting()

        self.key     = None
        self.value   = None


        return True

    def watchpath(self ):
        self.logger.debug("sr_post watchpath")

        watch_path = ''
        l = len(self.postpath)
        if l != 0 :
           watch_path = self.postpath[0]
           if l > 1 and self.program_name == 'sr_watch' :
             self.logger.error("only one path should be given for sr_watch")
             sys.exit(1)
 
        if self.post_base_dir != None :
           if not self.post_base_dir in watch_path :
              watch_path = self.post_base_dir + os.sep + watch_path
 
        if not os.path.exists(watch_path):
           self.logger.error("Not found %s " % watch_path )
           sys.exit(1)

        watch_path = os.path.abspath (watch_path)
        if self.realpath:
            watch_path = os.path.realpath(watch_path)
 
        if os.path.isfile(watch_path):
           self.logger.debug("file %s " % watch_path )
 
        if os.path.isdir(watch_path):
           self.logger.debug("directory %s " % watch_path )
           if self.rename != None and self.rename[-1] != '/' and 'modify' in self.events:
              self.logger.warning("renaming all modified files to %s " % self.rename )

        self.watch_path = watch_path
 
        return watch_path

    # ===================== 
    # sarra program actions 
    # ===================== 

    def cleanup(self):
        self.logger.info("%s %s cleanup" % (self.program_name,self.config_name))

        # if caching
        if self.caching : self.cache.close(unlink=True)

        # on posting host

        self.post_hc  = HostConnect( self.logger )
        self.post_hc.set_pika(self.use_pika)
        self.post_hc.set_url(self.post_broker)

        self.post_hc.connect()
        self.declare_exchanges(cleanup=True)

        self.close()

    def declare(self):
        self.logger.info("%s %s declare" % (self.program_name,self.config_name))

        # on posting host

        self.post_hc  = HostConnect( self.logger )
        self.post_hc.set_pika(self.use_pika)
        self.post_hc.set_url(self.post_broker)
        self.post_hc.connect()

        # declare posting exchange(s)
       
        self.declare_exchanges()

        self.close()

    def declare_exchanges(self, cleanup=False):

        # define post exchange (splitted ?)

        exchanges = []

        if self.post_exchange_split != 0 :
           for n in list(range(self.post_exchange_split)) :
               exchanges.append(self.post_exchange + "%02d" % n )
        else :
               exchanges.append(self.post_exchange)

        # do exchange setup
              
        for x in exchanges :
            if cleanup: self.post_hc.exchange_delete(x)
            else      : self.post_hc.exchange_declare(x)


    # setup: declare posting exchanges

    def setup(self):
        self.logger.info("%s %s setup" % (self.program_name,self.config_name))

        # on posting host

        self.post_hc  = HostConnect( self.logger )
        self.post_hc.set_pika(self.use_pika)
        self.post_hc.set_url(self.post_broker)
        self.post_hc.connect()
        self.declare_exchanges()

        self.close()

# ===================================
# MAIN
# ===================================

def post1file(p, fn):
    p.logger.debug("post1file fn = %s " % fn)

    if fn[0] != os.path.sep :
        fn = os.getcwd() + os.path.sep + fn

    p.watch_path = fn

    if os.path.islink(fn) : 
        p.watching(fn,'link')
    elif os.path.isfile(fn) : 
        p.watching(fn,'modify')
    else :
        p.scandir_and_post(fn,p.recursive)


def main():

    args,action,config,old = startup_args(sys.argv)

    if config and config[0] == '-' : config = None

    # unsupported action in python (but supported in sr_cpost)
    if action in ['start', 'stop', 'status', 'restart', 'reload' ]:
         post = sr_post(config,args,action)
         cfg  = config
         if config : cfg = os.path.basename(config)
         post.logger.info("%s %s %s (unimplemented in python)" % (post.program_name,cfg,action))
         os._exit(0)

    # supported actions in both
    elif action in ['cleanup','declare','setup' ] :
         post = sr_post(config,args,action)

    # extended actions 
    elif action in ['add','disable', 'edit', 'enable', 'list',    'log',    'remove' ] :
         post = sr_post(config,args,action)
         post.exec_action(action,False)
         os._exit(0)

    # default case in python
    else:
         action    = None
         post      = sr_post(config=None,args=sys.argv[1:])
         post.loop = False

    if post.in_error : os._exit(1)

    try :


        if   action == 'cleanup'    :
             post.cleanup()
             os._exit(0)
        elif action == 'declare'    :
             post.declare()
             os._exit(0)
        elif action == 'setup'      :
             post.setup()
             os._exit(0)

        else:

              if post.reset :
                 post.logger.info("reset: cache cleaned")
                 if post.cache :
                    post.cache.close(unlink=True)
                    post.cache.open()
                 os._exit(0)

              if len(post.postpath) == 0 :
                  post.postpath = sys.argv[post.first_arg:]

              if len(post.postpath) == 0 :
                  post.logger.error("no path to post")
                  post.help()
                  os._exit(1)

              post.connect()

              for watchpath in post.postpath :
                  post1file(post, watchpath)

              if post.pipe:
                  for watchpath in sys.stdin:
                      post1file(post, watchpath.strip())

        post.close()

    except :
             (stype, value, tb) = sys.exc_info()
             post.logger.error("Type: %s, Value:%s\n" % (stype, value))
             os._exit(1)

    """
    Workaround closes stderr to suppress error messages from sys.exit(0).
    See bug #74 for details. 
    if post.debug:
        post.logger.debug("FIXME: if you connect to SSL broker, there is a tear down bug bug #74." )
        post.logger.debug("FIXME: Message is harmless, but should take the time to fix eventually." )
        post.logger.debug("FIXME: outside debug mode, the message is suppressed." )
    else:
        os.close(2)
    """

    os._exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()

