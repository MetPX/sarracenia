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
# sr_post.py : python3 program allowing users to post an available product
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Nov  8 22:10:16 UTC 2017
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

#============================================================
# usage example
#
# sr_post [options] [config] [foreground|add|remove|edit|cleanup|setup]
#
#============================================================

import json,os,random,sys,time

from sys import platform as _platform

from base64 import b64decode, b64encode
from mimetypes import guess_type


try:
    import xattr
    supports_extended_attributes=True

except:
    supports_extended_attributes=False
    
from collections import *

from watchdog.observers         import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events            import PatternMatchingEventHandler

try :    
         from sr_amqp            import *
         from sr_cache           import *
         from sr_instances       import *
         from sr_message         import *
         from sr_rabbit          import *
         from sr_util            import *
except : 
         from sarra.sr_amqp      import *
         from sarra.sr_cache     import *
         from sarra.sr_instances import *
         from sarra.sr_message   import *
         from sarra.sr_rabbit    import *
         from sarra.sr_util      import *

#============================================================

class SimpleEventHandler(PatternMatchingEventHandler):

   def __init__(self,parent):
       self.on_created  = parent.on_created
       self.on_deleted  = parent.on_deleted
       self.on_modified = parent.on_modified
       self.on_moved    = parent.on_moved
       super().__init__()

#============================================================

class sr_post(sr_instances):

    # =============
    # check 
    # =============

    def check(self):
        self.logger.debug("%s check" % self.program_name)

        if self.config_name == None and self.action != 'foreground' : return

        # singleton

        if self.nbr_instances != 1 :
           self.logger.error("number of instance must be one")

        # ===============
        # FIXME remove 2018 :  temporary checks and fake subclass
        self.temporary_stuff()
        # ===============

        if self.post_broker   == None :
           self.logger.error("post_broker required")

        if self.post_exchange == None :
           self.post_exchange = 'xs_%s' % self.post_broker.username
           if self.post_exchange_suffix : self.post_exchange += '_' + self.post_exchange_suffix

        if   self.post_base_url == None :
             self.logger.error("post_base_url required")
        elif self.post_base_url.startswith('file:') :
             self.post_base_url = 'file:'

        # if accept_unmatch was not set, accept whatever not rejected

        if self.accept_unmatch == None : self.accept_unmatch = True

        # permanent message headers fields

        if self.to_clusters == None:
           self.to_clusters = self.post_broker.hostname

        # inflight 

        try   : self.inflight = int(self.inflight)
        except: pass

        # merge these 2 events

        self.create_modify = 'create' in self.events  or  'modify' in self.events

    # =============
    # close 
    # =============

    def close(self):
        self.logger.debug("%s close" % self.program_name)

        for plugin in self.on_stop_list:
           if not plugin(self): break

        if self.post_hc :
           self.post_hc.close()
           self.post_hc = None

        if hasattr(self,'cache') and self.cache :
           self.cache.save()
           self.cache.close()

        if self.sleep > 0 and len(self.obs_watched):
           for ow in self.obs_watched:
               self.observer.unschedule(ow)
           self.observer.stop()

        if self.restore_queue != None :
           self.publisher.restore_clear()

    # =============
    # connect 
    # =============

    def connect(self):
        self.logger.debug("%s connect" % self.program_name)

        # =============
        # create message if needed
        # =============

        self.msg = sr_message(self)

        # =============
        # posting 
        # =============

        loop = True
        if self.sleep <= 0 : loop = False

        self.post_hc = HostConnect( logger = self.logger )
        self.post_hc.choose_amqp_alternative(self.use_amqplib, self.use_pika)
        self.post_hc.set_url( self.post_broker )
        self.post_hc.loop = loop

        if not self.post_hc.connect():
           return

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

        # =============
        # amqp resources
        # =============

        self.declare_exchanges()

        # =============
        # retransmit/restore_queue
        # =============

        if self.restore_queue != None :
           self.publisher.restore_set(self)
           self.msg.pub_exchange        = self.publisher.restore_exchange
           self.msg.post_exchange_split = 0

    # =============
    # help
    # =============

    def help(self):
        print("\nUsage: %s -u <url> -pb <post_broker> ... [OPTIONS]\n" % self.program_name )
        print("version: %s \n" % sarra.__version__ )
        print("OPTIONS:")
        print("-a|action   <action>    default:foreground")
        print("                        keyword: add|cleanup|declare|disable|edit|enable|foreground|list|remove|setup")
        print("-pb|post_broker   <broker>          default:amqp://guest:guest@localhost/")
        print("-c|config   <config_file>")
        print("-pbd <post_base_dir>   default:None")
        print("-e   <events>          default:create|delete|follow|link|modify\n")
        print("-pe  <post_exchange>        default:xs_\"broker.username\"")
        print("-h|--help\n")
        print("-parts [0|1|sz]        0-computed blocksize (default), 1-whole files (no partitioning), sz-fixed blocksize")
        print("-to  <name1,name2,...> defines target clusters, default: ALL")
        print("-ptp <post_topic_prefix> default:v02.post")
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

    # =============
    # on_add     (for SimpleEventHandler module)
    # =============

    def on_add(self, event, src, dst):
        #self.logger.debug("%s %s %s" % ( event, src, dst ) )
        self.new_events['%s %s'%(src,dst)] = ( event, src, dst )

    # =============
    # on_created (for SimpleEventHandler)
    # =============

    def on_created(self, event):
        self.on_add( 'create', event.src_path, None )

    # =============
    # on_deleted (for SimpleEventHandler)
    # =============

    def on_deleted(self, event):
        self.on_add( 'delete', event.src_path, None )

    # =============
    # on_modified (for SimpleEventHandler)
    # =============

    def on_modified(self, event):
        self.on_add( 'modify', event.src_path, None )

    # =============
    # on_moved (for SimpleEventHandler)
    # =============

    def on_moved(self, event):
        self.on_add( 'move', event.src_path, event.dest_path )

    # =============
    # __on_post__ posting of message
    # =============

    def __on_post__(self):
        #self.logger.debug("%s __on_post__" % self.program_name)

        # invoke on_post when provided

        for plugin in self.on_post_list:
           if not plugin(self): return False

        ok = True

        if   self.outlet == 'json' :
             json_line = json.dumps( [ self.msg.topic, self.msg.headers, "%s %s %s" % ( self.msg.pubtime, self.msg.baseurl, self.msg.relpath ) ], sort_keys=True ) + '\n'
             print("%s" % json_line )

        elif self.outlet == 'url'  :
             print( "%s%s%s" % ( self.baseurl, os.sep, self.relpath ) )

        else:
             ok = self.msg.publish( )

        # publish counter

        self.publish_count += 1

        return ok

    # =============
    # __on_watch__
    # =============

    def __on_watch__(self):

        # invoke user defined on_message when provided

        for plugin in self.on_watch_list:
           if not plugin(self): return False

        return True

    # =============
    # __on_part__
    # =============

    def __on_part__(self):

        # invoke user defined on_part when provided

        for plugin in self.on_part_list:
           if not plugin(self): return False

        return True

    # =============
    # overwride defaults
    # =============

    def overwrite_defaults(self):
        self.logger.debug("%s overwrite_defaults" % self.program_name)

        self.post_hc       = None

        self.obs_watched   = []
        self.watch_handler = None
        self.post_topic_prefix = "v02.post"

        self.inl           = []
        self.new_events    = OrderedDict()
        self.left_events   = OrderedDict()

        self.blocksize     = 200 * 1024 * 1024

    # =============
    # path inflight
    # =============

    def path_inflight(self,path,lstat):
        #self.logger.debug("path_inflight %s" % path )

        if not isinstance(self.inflight,int):
           #self.logger.debug("ok inflight unused")
           return False

        if lstat == None :
           #self.logger.debug("ok lstat None")
           return False

        age = time.time() - lstat[stat.ST_MTIME]
        if age < self.inflight :
           self.logger.debug("%d vs (inflight setting) %d seconds. Too New!" % (age,self.inflight) )
           return True

        return False

    # =============
    # path renamed
    # =============

    def path_renamed(self,path):

        newname = path

        # rename path given with no filename

        if self.rename :
           newname = self.rename
           if self.rename[-1] == '/' :
              newname += os.path.basename(path)

        # strip 'N' heading directories

        if self.strip > 0:
           strip = self.strip
           if path[0] == '/' : strip = strip + 1
           # if we strip too much... keep the filename
           token = path.split('/')
           try :   token   = token[strip:]
           except: token   = [os.path.basename(path)]
           newname = '/'+'/'.join(token)

        if newname == path : return None

        return newname

    # =============
    # path rejected
    # =============

    def path_rejected(self,path):
        #self.logger.debug("path_rejected %s" % path )

        if not self.post_base_url:
            self.post_base_url = 'file:/'
        
        if self.masks == [] : return False

        self.post_relpath = path
        if self.post_base_dir : self.post_relpath = path.replace(self.post_base_dir, '')

        urlstr = self.post_base_url + '/' + self.post_relpath

        if self.realpath_filter and not self.realpath_post :
           if os.path.exists(path) :
              fltr_post_relpath = os.path.realpath(path)
              if sys.platform == 'win32':
                  fltr_post_relpath = fltr_post_relpath.replace('\\','/')

              if self.post_base_dir : fltr_post_relpath = fltr_post_relpath.replace(self.post_base_dir, '')
              urlstr = self.post_base_url + '/' + fltr_post_relpath
        
        if not self.isMatchingPattern(urlstr,self.accept_unmatch) :
           self.logger.debug("%s Rejected by accept/reject options" % urlstr )
           return True

        self.logger.debug( "%s not rejected" % urlstr )
        return False

    # =============
    # post_delete
    # =============

    def post_delete(self, path, key=None, value=None):
        #self.logger.debug("post_delete %s (%s,%s)" % (path,key,value) )

        # accept this file

        if self.path_rejected (path): return False

        # post_init (message)
        self.post_init(path,None)

        # sumstr
        hash   = sha512()
        hash.update(bytes(os.path.basename(path), encoding='utf-8'))
        sumstr = 'R,%s' % hash.hexdigest()

        # partstr
        partstr = None

        # caching
        if self.caching :
           new_post = self.cache.check(str(sumstr),path,partstr)
           self.cache.delete_path(path)  # dont keep delete in cache
           if not new_post :
              self.logger.debug("already posted as deleted %s %s"%(path,sumstr))
              return False

        # completing headers

        self.msg.headers['sum'] = sumstr

        # used when moving a file

        if key != None :
           self.msg.headers[key] = value
           if key == 'newname' and self.post_base_dir :
              self.msg.new_dir  = os.path.dirname( value)
              self.msg.new_file = os.path.basename(value)
              self.msg.headers[key] = value.replace(self.post_base_dir, '')

        # post message

        ok = self.__on_post__()

        return ok

    # =============
    # post_file
    # =============

    def post_file(self, path, lstat, key=None, value=None):
        #self.logger.debug("post_file %s" % path )

        # accept this file

        if self.path_rejected(path): return False

        # check if it is a part file

        if path.endswith('.'+self.msg.part_ext):
           return self.post_file_part(path,lstat)
        
        # This variable means that part_file_assemble plugin is loaded and will handle posting the original file (being assembled)

        elif hasattr(self, 'suppress_posting_partial_assembled_file'):
            return False

        # check the value of blocksize

        fsiz  = lstat[stat.ST_SIZE]
        blksz = self.set_blocksize(self.blocksize,fsiz)

        # if we should send the file in parts

        if blksz > 0 and blksz < fsiz :
           return self.post_file_in_parts(path,lstat)

        # post_init (message)
        self.post_init(path,lstat)

        # partstr

        partstr = '1,%d,1,0,0' % fsiz

        sumstr = self.compute_sumstr(path, fsiz)
 
        # caching

        if self.caching :
           new_post = self.cache.check(str(sumstr),self.post_relpath,partstr)
           if new_post : self.logger.info("caching %s"% path)
           else        : 
                         self.logger.debug("already posted %s"% path)
                         return False

        # complete message        
        if self.post_topic_prefix.startswith('v03') and self.inline and fsiz < self.inline_max :        
 
           if self.inline_encoding == 'guess':
              e = guess_type(path)[0]
              binary = not e or not ('text' in e )
           else:
              binary = (self.inline_encoding == 'text' )

           f = open(path,'rb')
           d = f.read()
           f.close()

           if binary:
               self.msg.headers[ "content" ] = { "encoding": "base64", "value": b64encode(d).decode('utf-8') }
           else:
               try:
                   self.msg.headers[ "content" ] = { "encoding": "utf-8", "value": d.decode('utf-8') }
               except:
                   self.msg.headers[ "content" ] = { "encoding": "base64", "value": b64encode(d).decode('utf-8') }

        self.msg.headers['parts'] = partstr
        self.msg.headers['sum']   = sumstr

        # used when moving a file

        if key != None : 
           self.msg.headers[key] = value
           if key == 'oldname' and self.post_base_dir :
              self.msg.headers[key] = value.replace(self.post_base_dir, '')

        # post message

        ok = self.__on_post__()

        return ok

    def compute_sumstr(self, path, fsiz):

        sumstr = '' 

        if supports_extended_attributes:
           try:
               attr = xattr.xattr(path)
               if 'user.sr_sum' in attr:
                  if 'user.sr_mtime' in attr:
                     if attr['user.sr_mtime'].decode("utf-8") >= self.msg.headers['mtime']:
                        self.logger.debug("sum set by xattr")
                        sumstr = attr['user.sr_sum'].decode("utf-8")
                        return sumstr
                  else:
                     xattr.setxattr(path, 'user.sr_mtime', bytes(self.msg.headers['mtime'], "utf-8"))
                     self.logger.debug("sum set by xattr")
                     sumstr = attr['user.sr_sum'].decode("utf-8")
                     return sumstr

           except:
               pass

        self.logger.debug("sum set by compute_sumstr")

        sumflg = self.sumflg

        if sumflg[:2] == 'z,' and len(sumflg) > 2 :
            sumstr = sumflg

        else:

            if not sumflg[0] in ['0','d','n','s','z' ]: sumflg = 'd'

            self.set_sumalgo(sumflg)
            sumalgo = self.sumalgo
            sumalgo.set_path(path)

            # compute checksum

            if sumflg in ['d','s'] :

                fp = open(path,'rb')
                i  = 0
                while i<fsiz :
                    buf = fp.read(self.bufsize)
                    if not buf: break
                    sumalgo.update(buf)
                    i  += len(buf)
                fp.close()

            # setting sumstr

            checksum = sumalgo.get_value()
            sumstr   = '%s,%s' % (sumflg,checksum)

        return sumstr

    # =============
    # post_file_in_parts
    # =============

    def post_file_in_parts(self, path, lstat):
        #self.logger.debug("post_file_in_parts %s" % path )

        # post_init (message)
        self.post_init(path,lstat)

        # check the value of blocksize

        fsiz      = lstat[stat.ST_SIZE]
        chunksize = self.set_blocksize(self.blocksize,fsiz)

        # count blocks and remainder

        block_count = int(fsiz/chunksize)
        remainder   =     fsiz%chunksize
        if remainder > 0 : block_count = block_count + 1

        # default sumstr

        sumstr = self.sumflg

        # loop on chunks

        blocks = list(range(0,block_count))
        if self.randomize:
            random.shuffle(blocks)
            #blocks = [8, 3, 1, 2, 9, 6, 0, 7, 4, 5] # Testing
            self.logger.info('Sending partitions in the following order: '+str(blocks))

        for i in blocks: 

              # setting sumalgo for that part

              sumflg = self.sumflg

              if sumflg[:2] == 'z,' and len(sumflg) > 2 :
                 sumstr = sumflg

              else:
                 sumflg = self.sumflg
                 if not self.sumflg[0] in ['0','d','n','s','z' ]: sumflg = 'd'
                 self.set_sumalgo(sumflg)
                 sumalgo = self.sumalgo
                 sumalgo.set_path(path)

              # compute block stuff

              current_block = i

              offset = current_block * chunksize
              length = chunksize

              last   = current_block == block_count-1
              if last and remainder > 0 :
                 length = remainder

              # set partstr

              partstr = 'i,%d,%d,%d,%d' %\
                        (chunksize,block_count,remainder,current_block)

              # compute checksum if needed

              if not self.sumflg in ['0','n','z'] :
                 bufsize = self.bufsize
                 if length < bufsize : bufsize = length

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

              # caching

              if self.caching :
                 new_post = self.cache.check(str(sumstr),self.post_relpath,partstr)
                 if new_post : self.logger.info("caching %s (%s)"% (path,partstr) )
                 else        :
                               self.logger.debug("already posted %s (%s)"%(path,partstr) )
                               continue

              # complete  message

              self.msg.headers['parts'] = partstr
              self.msg.headers['sum']   = sumstr

              # post message

              ok = self.__on_post__()
              if not ok:
                self.logger.error('Something went wrong while posting: %s' %self.msg.relpath)


        return True

    # =============
    # post_file_part
    # =============

    def post_file_part(self, path, lstat):

        # post_init (message)
        self.post_init(path,lstat)

        # verify suffix

        ok,log_msg,suffix,partstr,sumstr = self.msg.verify_part_suffix(path)

        # something went wrong

        if not ok:
           self.logger.debug("file part extension but %s for file %s" % (log_msg,path))
           return False

        # check rename see if it has the right part suffix (if present)
        if 'rename' in self.msg.headers and not suffix in self.msg.headers['rename']:
           self.msg.headers['rename'] += suffix

        # caching

        if self.caching :
           new_post = self.cache.check(str(sumstr),path,partstr)
           if new_post : self.logger.info("caching %s"% path)
           else        : 
                         self.logger.debug("already posted %s"% path)
                         return False

        # complete  message

        self.msg.headers['parts'] = partstr
        self.msg.headers['sum']   = sumstr

        # post message and trigger part plugins
        ok = self.__on_part__()

        if ok: ok = self.__on_post__()

        return ok

    # =============
    # post_init
    # =============

    def post_init(self, path, lstat=None, key=None, value=None):

        self.msg.new_dir  = os.path.dirname( path)
        self.msg.new_file = os.path.basename(path)

        # relpath
        self.post_relpath = path
        if self.post_base_dir :
           self.post_relpath = path.replace(self.post_base_dir, '')

        # exchange
        self.msg.exchange = self.post_exchange

        # topic
        self.msg.set_topic(self.post_topic_prefix,self.post_relpath)
        if self.subtopic: self.msg.set_topic_usr(self.post_topic_prefix,self.subtopic)

        # notice
        self.msg.set_notice(self.post_base_url,self.post_relpath)

        # rename
        rename = self.path_renamed(self.post_relpath)

        # headers

        self.msg.headers = {}

        self.msg.trim_headers()

        if self.to_clusters != None : self.msg.headers['to_clusters']  = self.to_clusters
        if self.cluster     != None : self.msg.headers['from_cluster'] = self.cluster
        if self.source      != None : self.msg.headers['source']       = self.source
        if rename           != None : self.msg.headers['rename']       = rename
        if key              != None : self.msg.headers[key]            = value

        if lstat == None : return

        if self.preserve_time:
            self.msg.headers['mtime'] = timeflt2str(lstat.st_mtime)
            self.msg.headers['atime'] = timeflt2str(lstat.st_atime)

        if self.preserve_mode:
            self.msg.headers['mode']  = "%o" % ( lstat[stat.ST_MODE] & 0o7777 )

    # =============
    # post_link
    # =============

    def post_link(self, path, key=None, value=None ):
        #self.logger.debug("post_link %s" % path )

        # accept this file

        if self.path_rejected (path): return False

        # post_init (message)
        self.post_init(path,None)

        # resolve link

        link = os.readlink(path)

        # partstr

        partstr = None

        # sumstr

        hash = sha512()
        hash.update( bytes( link, encoding='utf-8' ) )
        sumstr = 'L,%s' % hash.hexdigest()

        # caching

        if self.caching :
           new_post = self.cache.check(str(sumstr),self.post_relpath,partstr)
           if new_post : self.logger.info("caching %s"% path)
           else        : 
                         self.logger.debug("already posted %s"% path)
                         return False

        # complete headers

        self.msg.headers['link'] = link
        self.msg.headers['sum']  = sumstr

        # used when moving a file

        if key != None : self.msg.headers[key] = value

        # post message

        ok = self.__on_post__()

        return ok

    # =============
    # post_move
    # =============

    def post_move(self, src, dst ):
        #self.logger.debug("post_move %s %s" % (src,dst) )

        # watchdog funny ./ added at end of directory path ... removed

        src = src.replace('/./', '/' )
        dst = dst.replace('/./', '/' )

        if os.path.islink(dst) and self.realpath_post:
           dst = os.path.realpath(dst)
           if sys.platform == 'win32':
                  dst = dst.replace('\\','/')

        # file

        if os.path.isfile(dst) :
           ok = self.post_delete(src,               'newname', dst)
           ok = self.post_file  (dst, os.stat(dst), 'oldname', src)
           return True

        # link

        if os.path.islink(dst) :
           ok = self.post_delete(src, 'newname', dst)
           ok = self.post_link  (dst, 'oldname', src)
           return True

        # directory
        if os.path.isdir(dst) :
            for x in os.listdir(dst):

                dst_x = dst + '/' + x
                src_x = src + '/' + x

                ok = self.post_move(src_x,dst_x)

            # directory list to delete at end
            self.move_dir_lst.append( (src,dst) )

        return True

    # =============
    # post1file
    # =============

    def post1file(self,path,lstat):

        done = True

        # watchdog funny ./ added at end of directory path ... removed

        path = path.replace( '/./', '/' )

        # always use / as separator for paths being posted.
        if os.sep != '/' :  # windows
            path = path.replace( os.sep, '/' )

        # path is a link

        if os.path.islink(path):
           ok = self.post_link(path)

           if self.follow_symlinks :
              link  = os.readlink(path)
              try   : 
                   rpath = os.path.realpath(link)
                   if sys.platform == 'win32':
                       rpath = rpath.replace('\\','/')

              except: return done

              lstat = None
              if os.path.exists(rpath) : lstat = os.stat(rpath)

              ok = self.post1file(rpath,lstat)

           return done

        # path deleted

        if lstat == None :
           ok = self.post_delete(path)
           return done

        # path is a file

        if os.path.isfile(path):
           ok = self.post_file(path,lstat)
           return done

        # at this point it is a create,modify directory

        return done

    # =============
    # post1move
    # =============

    def post1move(self, src, dst ):
        #self.logger.debug("post1move %s %s" % (src,dst) )

        self.move_dir_lst = []

        ok = self.post_move(src,dst)

        for tup in self.move_dir_lst :
            src, dst = tup
            #self.logger.debug("deleting moved directory %s" % src )
            ok = self.post_delete(src, 'newname', dst)

        return True

    # =============
    # process event
    # =============

    def process_event(self, event, src, dst ):
        #self.logger.debug("process_event %s %s %s " % (event,src,dst) )

        done  = True
        later = False

        # delete

        if event == 'delete' :
           if event in self.events:
              ok = self.post1file(src,None)
           return done

        # move

        if event == 'move':
           if self.create_modify:
              ok = self.post1move(src,dst)
           return done

        # create or modify

        # directory : skipped, its content is watched

        if os.path.isdir(src): return done

        # link ( os.path.exists = false, lstat = None )

        if os.path.islink(src) :
           if 'link' in self.events :
              ok = self.post1file(src,None)
           return done

        # file : must exists
        #       (may have been deleted since event caught)

        if not os.path.exists(src) : return done

        # file : must be old enough

        lstat = os.stat(src)
        if self.path_inflight(src,lstat): return later

        # post it

        if self.create_modify :
           ok = self.post1file(src,lstat)

        return done

    def post_pulse(self):
        self.logger.info("post_pulse message")

        self.connect()

        # build message

        self.msg.topic    = 'v02.pulse'

        self.msg.set_time()
        self.msg.notice  = '%s' % self.msg.pubtime

        if self.pulse_message : 
           self.msg.topic  += '.message'
           self.msg.notice += ' ' + self.pulse_message
        else:
           self.msg.topic  += '.tick'
        
        self.msg.headers = {}
        self.msg.trim_headers()

        # pulse on all exchanges
        # because of its topic, it should not impact any process
        # that does not consider topic v02.pulse

        lst_dict = run_rabbitmqadmin(self.post_broker,"list exchanges name",self.logger)

        ex = []
        for edict in lst_dict :
            exchange = edict['name']
            if exchange == ''        : continue
            if exchange[0] != 'x'    : continue
            if exchange == 'xreport' : continue
            # deprecated exchanges
            if exchange == 'xlog'    : continue
            if exchange[0:3] == 'xl_': continue
            if exchange[0:3] == 'xr_': continue
            ex.append(exchange)
            self.msg.pub_exchange = exchange
            self.msg.message_ttl  = self.message_ttl
            self.msg.publish()

        self.close()

    # =============
    # set_blocksize ... directly from c code
    # =============

    def set_blocksize(self,bssetting,fsiz):

      tfactor =  50 * 1024 * 1024
      
      if bssetting == 0 : ## autocompute
            if   fsiz > 100*tfactor: return 10 * tfactor
            elif fsiz > 10*tfactor : return int((fsiz+9)/10)
            elif fsiz > tfactor :    return int((fsiz+2)/ 3)
            else:                    return fsiz 
             
      elif  bssetting == 1 : ## send file as one piece.
            return fsiz
             
      else: ## partstr=i
            return bssetting


    # =============
    # wakeup
    # =============

    def wakeup(self):
        #self.logger.debug("wakeup")

        # FIXME: Tiny potential for events to be dropped during copy.
        #     these lists might need to be replaced with watchdog event queues.
        #     left for later work. PS-20170105
        #     more details: https://github.com/gorakhargosh/watchdog/issues/392

        # on_watch 

        ok = self.__on_watch__()
        if not ok : return

        # pile up left events to process

        self.left_events.update(self.new_events)
        self.new_events = OrderedDict()

        # work with a copy events and keep done events (to delete them)

        self.done_events = []
        self.cur_events  = OrderedDict()
        self.cur_events.update(self.left_events)

        # nothing to do

        if len(self.cur_events) <= 0: return

        # loop on all events

        for key in self.cur_events:
            event, src, dst = self.cur_events[key]
            done = self.process_event( event, src, dst )
            if done : self.left_events.pop(key) 

        # heartbeat
        self.heartbeat_check()



    # =============
    # walk
    # =============

    def walk(self, src ):
        self.logger.debug("walk %s" % src )

        # how to proceed with symlink

        if os.path.islink(src) and self.realpath_post :
           src = os.path.realpath(src)
           if sys.platform == 'win32':
               src = src.replace('\\','/')

        # walk src directory, this walk is depth first... there could be a lot of time
        # between *listdir* run, and when a file is visited, if there are subdirectories before you get there.
        # hence the existence check after listdir (crashed in flow_tests of > 20,000)
        for x in os.listdir(src):
            path = src + '/' + x
            if os.path.isdir(path):
               self.walk(path)
               continue

            # add path created
            if os.path.exists(path):
                self.post1file(path,os.stat(path))

    # =============
    # original walk_priming
    # =============

    def walk_priming(self,p):
        """
         Find all the subdirectories of the given path, start watches on them. 
         deal with symbolically linked directories correctly
        """
        if os.path.islink(p):
            realp = os.path.realpath(p)
            if sys.platform == 'win32':
               realp = realp.replace('\\','/')

            self.logger.info("sr_watch %s is a link to directory %s" % ( p, realp) )
            if self.realpath_post:
                d=realp
            else:
                d=p + '/' + '.'
        else:
            d=p

        try :
                 fs = os.stat(d)
                 dir_dev_id = '%s,%s' % ( fs.st_dev, fs.st_ino )
                 if dir_dev_id in self.inl: return True
        except:  self.logger.warning("could not stat %s" % d)

        if os.access( d , os.R_OK|os.X_OK ): 
           try:
               ow = self.observer.schedule(self.watch_handler, d, recursive=True )
               self.obs_watched.append(ow)
               self.inl[dir_dev_id] = (ow,d)
               self.logger.info("sr_watch priming watch (instance=%d) scheduled for: %s " % (len(self.obs_watched), d))
           except:
               self.logger.warning("sr_watch priming watch: %s failed, deferred." % d)
               self.logger.debug('Exception details:', exc_info=True)

               # add path created
               self.on_add( 'create', p, None )
               return True

        else:
            self.logger.warning("sr_watch could not schedule priming watch of: %s (EPERM) deferred." % d)
            self.logger.debug('Exception details:', exc_info=True)

            # add path created
            self.on_add( 'create', p, None )
            return True

        return True

    # =============
    # watch_dir
    # =============

    def watch_dir(self, sld ):
        self.logger.debug("watch_dir %s" % sld )

        if self.force_polling :
           self.logger.info("sr_watch polling observer overriding default (slower but more reliable.)")
           self.observer = PollingObserver()
        else:
           self.logger.info("sr_watch optimal observer for platform selected (best when it works).")
           self.observer = Observer()

        self.obs_watched = []

        self.watch_handler  = SimpleEventHandler(self)
        self.walk_priming(sld)

        self.logger.info("sr_watch priming walk done, but not yet active. Starting...")
        self.observer.start()
        self.logger.info("sr_watch now active on %s posting to exchange: %s"%(sld,self.post_exchange))

        if self.post_on_start:
            self.walk(sld)


    # =============
    # watch_loop
    # =============

    def watch_loop(self ):
        self.logger.debug("watch_loop")

        last_time = time.time()
        while True:
            self.wakeup()
            now = time.time()
            elapse = now - last_time
            if elapse < self.sleep:
                time.sleep(self.sleep-elapse)
            last_time = now

        # FIXME This is unreachable code, need to figure out what to do with that
        # self.observer.join()

    # ==================================================
    # FIXME in 2018?  get rid of code from HERE TOP

    def temporary_stuff(self):

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

        # verify post_base_dir

        if self.post_base_dir == None :
           if self.post_document_root != None :
              self.post_base_dir = self.post_document_root
              self.logger.warning("use post_base_dir instead of post_document_root")
           elif self.document_root != None :
              self.post_base_dir = self.document_root
              self.logger.warning("use post_base_dir instead of document_root")

        # faking having a subclass poster from which post is called

        addmodule = namedtuple('AddModule', ['post'])
        self.poster = addmodule(self.post_url)

    def post_url(self,post_exchange,url,to_clusters,\
                      partstr=None,sumstr=None,rename=None,filename=None, \
                      mtime=None,atime=None,mode=None,link=None):

        self.logger.warning("deprecated use of self.poster.post(post_exchange,url...")
        self.logger.warning("should be using self.post1file or self.post_file...")

        post_relpath  = url.path
        urlstr        = url.geturl()
        post_base_url = urlstr.replace(post_relpath,'')

        # apply accept/reject

        if self.realpath_filter and not self.realpath_post :
           path = post_relpath
           if self.post_base_dir : path = self.post_base_dir + '/' + path
           if os.path.exist(path) :
              fltr_post_relpath = os.path.realpath(path)
              if sys.platform == 'win32':
                  fltr_post_relpath = fltr_post_relpath.replace('\\','/')

              if self.post_base_dir : fltr_post_relpath = fltr_post_relpath.replace(self.post_base_dir, '')
              urlstr = self.post_base_url + '/' + fltr_post_relpath

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
        self.msg.set_topic(self.post_topic_prefix,post_relpath)
        if self.subtopic != None :
           self.msg.set_topic_usr(self.post_topic_prefix,self.subtopic)

        # set message notice
        self.msg.set_notice(post_base_url,post_relpath)

        # set message headers
        self.msg.headers = {}

        self.msg.headers['to_clusters'] = to_clusters

        if partstr  != None : self.msg.headers['parts']        = partstr
        if sumstr   != None : self.msg.headers['sum']          = sumstr
        if rename   != None : self.msg.headers['rename']       = rename

        if self.preserve_time:
            if mtime    != None : self.msg.headers['mtime']        = mtime
            if atime    != None : self.msg.headers['atime']        = atime

        if self.preserve_mode:
            if mode     != None : self.msg.headers['mode']         = "%o" % ( mode & 0o7777 )

        if link     != None : self.msg.headers['link']         = link

        if self.cluster != None : self.msg.headers['from_cluster']    = self.cluster
        if self.source  != None : self.msg.headers['source']          = self.source

        self.msg.trim_headers()

        ok = self.__on_post__()

        return ok

    # FIXME in 2018?  get rid of code to HERE BOTTOM
    # ==================================================


    # =============
    # run
    # =============
      
    def run(self):
        self.logger.info("%s run partflg=%s, sum=%s, caching=%s basis=%s" % \
              ( self.program_name, self.partflg, self.sumflg, self.caching, self.cache_basis ))
        self.logger.info("%s realpath_post=%s follow_links=%s force_polling=%s"  % \
              ( self.program_name, self.realpath_post, self.follow_symlinks, self.force_polling ) )

        self.connect()

        # caching
        if self.caching :
           self.cache      = sr_cache(self)
           self.cache_stat = True
           if self.reset:
              self.cache.close(unlink=True)
           self.cache.open()
           if not hasattr(self,'heartbeat_cache_installed') or not self.heartbeat_cache_installed :
              self.execfile("on_heartbeat",'hb_cache')
              self.on_heartbeat_list.append(self.on_heartbeat)
              self.heartbeat_cache_installed = True

        pbd = self.post_base_dir

        for plugin in self.on_start_list:
           if not plugin(self): break

        for d in self.postpath :
            self.logger.debug("postpath = %s" % d)
            if pbd and not d.startswith(pbd) : d = pbd + '/' + d

            if self.sleep > 0 : 
               self.watch_dir(d)
               continue

            if   os.path.isdir(d) :
                 self.walk(d)
            elif os.path.islink(d):
                 self.post1file(d,None)
            elif os.path.isfile(d):
                 self.post1file(d,os.stat(d))
            else: 
                 self.logger.error("could not post %s (exists %s)" % (d,os.path.exists(d)) )

        if self.sleep > 0: self.watch_loop()

        self.close()

    def reload(self):
        self.logger.info( "%s reload" % self.program_name )
        self.close()
        self.configure()
        self.run()

    def start(self):
        self.logger.info( "%s %s startup" % (self.program_name,self.config_name) )
        self.log_settings()
        self.run()

    def stop(self):
        self.logger.info( "%s stop" % self.program_name)
        self.close()
        os._exit(0)

    def cleanup(self):
        self.logger.info( "%s %s cleanup" % (self.program_name,self.config_name))

        if self.post_broker :
           self.post_hc = HostConnect( logger = self.logger )
           self.post_hc.choose_amqp_alternative(self.use_amqplib, self.use_pika)
           self.post_hc.set_url( self.post_broker )
           self.post_hc.loop=False
           if self.post_hc.connect():
               self.declare_exchanges(cleanup=True)

        # caching

        if hasattr(self,'cache') and self.cache :
           self.cache.close(unlink=True)
           self.cache = None

        self.close()

    def declare(self):
        self.logger.info("%s %s declare" % (self.program_name,self.config_name))

        # on posting host
        if self.post_broker :
           self.post_hc = HostConnect( logger = self.logger )
           self.post_hc.choose_amqp_alternative(self.use_amqplib, self.use_pika)
           self.post_hc.set_url( self.post_broker )
           self.post_hc.loop=False;
           if self.post_hc.connect():
               self.declare_exchanges()

        self.close()

    def declare_exchanges(self, cleanup=False):

        # restore_queue mode has no post_exchange 

        if not self.post_exchange : return

        # define post exchange (splitted ?)

        exchanges = []

        if self.post_exchange_split != 0 :
           for n in list(range(self.post_exchange_split)) :
               exchanges.append(self.post_exchange + "%02d" % n )
        else :
               exchanges.append(self.post_exchange)

        # do exchanges
              
        for x in exchanges :
            if cleanup: self.post_hc.exchange_delete(x)
            else      : self.post_hc.exchange_declare(x)


    def setup(self):
        self.logger.info("%s %s setup" % (self.program_name,self.config_name))

        self.declare()

                 
# ===================================
# MAIN
# ===================================

class Silent_Logger:
      def silence(self,str):
          pass
      def __init__(self):
          self.debug   = self.silence
          self.error   = self.silence
          self.info    = self.silence
          self.warning = self.silence

def main():

    # try the normal sarra arguments parsing

    args,action,config,old = startup_args(sys.argv)
    #print("args,action,config,old = %s %s %s %s" % (args,action,config,old))

    # verification: config

    post        = sr_post(None,None,action)
    logger      = post.logger

    #post.logger = Silent_Logger()

    config_ok, user_config = post.config_path(post.program_dir,config)
    #print("config_ok,user_config = %s %s" % (config_ok, user_config))
    if action in ['add','edit','enable','remove']: config_ok = True

    # config and action are ok so try normal execution

    if config_ok and action :
       post = sr_post(user_config,args,action)
       post.exec_action(action,old)
       os._exit(0)

    # verification: action

    if action == None : action = 'foreground'

    # user_config is wrong

    if not config_ok :

       # if specifically set... exit
       cidx   = -99
       try    : cidx = sys.argv.index('-c')
       except :
                try    : cidx = sys.argv.index('-config')
                except : pass
       if cidx > 0 :
          logger.error("config file %s" % config)
          os._exit(1)

       # parsing incorrect, put it back in args
       if config : args.append(config)
       config = None
    
    # if the config is ok, we parse it

    if config_ok: post.config(user_config)

    # verification : args

    post.args(args)

    # are we posting a pulse message

    if post.pulse_message != None :
       post = sr_post(config,args,action)
       post.post_pulse()
       os._exit(0)

    # if we found something to post we are done

    if len(post.postpath) > 0 :
       post = sr_post(config,args,action)
       post.exec_action(action,old)
       os._exit(0)

    # still no posting path... should we have
       
    pidx   = -99
    try    : pidx = sys.argv.index('-p')
    except :
             try    : pidx = sys.argv.index('-path')
             except : pass
    if pidx > 0 :
       logger.error("problem posting path not found")
       os._exit(1)

    # loop from last arg to front and build postpath
 
    postpath = []
    pbd      = post.post_base_dir
    i        = len(sys.argv)-1

    while i > 0 :
        arg   = sys.argv[i]
        value = '%s' % arg
        i     = i - 1
        if pbd and not pbd in value : value = pbd + '/' + value
        if os.path.exists(value) or os.path.islink(value):
           postpath.append(value)
           try:    args.remove(arg)
           except: pass
           continue
        break

    # add what we found

    if len(postpath) > 0 :
       args.append('-p')
       args.extend(postpath)

    # try normal execution

    post = sr_post(config,args,action)

    post.exec_action(action,old)

    os._exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
