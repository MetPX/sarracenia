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

try :
         from sr_config        import *
         from sr_message       import *
         from sr_poster        import *
         from sr_util          import *
except :
         from sarra.sr_config  import *
         from sarra.sr_message import *
         from sarra.sr_poster  import *
         from sarra.sr_util    import *

class sr_post(sr_config):

    def __init__(self,config=None,args=None):
        sr_config.__init__(self,config,args)
        self.configure()
        self.in_error = False

    def check(self):
        self.logger.debug("sr_post check")

        self.in_error = False
        if self.url == None :
           self.logger.error("url required")
           self.in_error = True
           self.help()
           return

        # sarra exchange default value is xs_username
        # username being the broker's

        if self.exchange == None :
           self.exchange = 'xs_%s' % self.broker.username

        if self.to_clusters == None :
           self.logger.error("-to option is mandatory\n")
           self.in_error = True
           return

        # resetting logs if needed

        if self.program_name != 'sr_watch' and self.logpath != self.lpath : self.setlog()

    def close(self):
        self.logger.debug("sr_post close")
        self.poster.close()

    def connect(self):
        self.logger.debug("sr_post connect")

        # sr_post : no loop to reconnect to broker

        self.loop = True
        if self.program_name == 'sr_post' :
           self.loop = False

        # message

        self.msg = sr_message( self )

        # publisher

        self.post_broker   = self.broker
        self.poster        = sr_poster(self, self.loop)

        self.msg.publisher = self.poster.publisher
        self.msg.post_exchange_split = self.post_exchange_split

                                   
    def help(self):
        print("\nUsage: %s -u <url> -b <broker> ... [OPTIONS]\n" % self.program_name )
        print("version: %s \n" % sarra.__version__ )
        print("OPTIONS:")
        print("-b   <broker>          default:amqp://guest:guest@localhost/")
        print("-c   <config_file>")
        print("-dr  <document_root>   default:None")
        if self.program_name == 'sr_watch' : print("-e   <events>          default:create|delete|follow|link|modify\n")
        print("-ex  <exchange>        default:xs_\"broker.username\"")
        print("-f   <flow>            default:None\n")
        print("-h|--help\n")
        print("-l   <logpath>         default:stdout")
        print("-parts [0|1|sz]        0-computed blocksize (default), 1-whole files (no partitioning), sz-fixed blocksize")
        print("-to  <name1,name2,...> defines target clusters, default: ALL")
        print("-tp  <topic_prefix>    default:v02.post")
        print("-sub <subtopic>        default:'path.of.file'")
        print("-rn  <rename>          default:None")
        print("-sum <sum>             default:d")
        print("-recursive             default:enable recursive post")
        print("-caching               default:enable caching")
        print("-reset                 default:enable reset")
        print("-path <path1... pathN> default:required")
        print("-on_post <script>      default:None")
        print("DEBUG:")
        print("-debug")
        print("-r  : randomize chunk posting")
        print("-rr : reconnect between chunks\n")

    def lock_set(self):
        #self.logger.debug("sr_post lock_set")

        if self.reset   :
           self.poster.cache_reset()

        if self.caching :
           self.logger.debug("sr_post cache_load")
           self.poster.cache_load()

    def lock_unset(self):
        #self.logger.debug("sr_post lock_unset")
        if self.caching :
           self.logger.debug("sr_post cache_close")
           self.poster.cache_close()

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
        if self.to_clusters == None:
            self.to_clusters = self.broker.hostname
           
        self.logger.debug("sr_post overwrite_defaults Done")

    def posting(self):
        self.logger.debug("sr_post posting %s" % ( self.url.path ) )

        filepath = '/' + self.url.path.strip('/')

        # urllib keeps useless repetitive '/' so rebuild url smartly
        if filepath != self.url.path :
           if self.document_root == None and 'ftp' in self.url.scheme :
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

        if not os.path.islink(filepath) and ( not os.path.exists(filepath) and self.event != 'delete' ):
           self.logger.error("File not found %s " % filepath )
           return False

        # rename path given with no filename

        rename = self.rename
        if self.rename != None and self.rename[-1] == os.sep :
           rename += os.path.basename(self.url.path)

        # strip option when no rename option
        # strip 'N' heading directories from url.path

        if self.strip != 0:
           if rename != None :
              self.logger.error("option strip used with option rename conflicts")
              sys.exit(1)
           strip  = self.strip
           token  = self.url.path.split(os.sep)
           if self.url.path[0] == os.sep : strip += 1
           if len(token) <= self.strip   : strip = len(token)-1
           rename = os.sep+os.sep.join(token[strip:])
              
        filename = os.path.basename(filepath)

        # ==============
        # delete event...
        # ==============

        if self.event == 'delete' :
           ok = self.poster.post(self.exchange,self.url,self.to_clusters,None, \
                    'R,%d' % random.randint(0,100), rename, filename)

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
               ok = self.poster.post(self.exchange,self.url,self.to_clusters,None, \
                    'L,%d' % random.randint(0,100), rename, filename, link=os.readlink(filepath))

               if not ok : sys.exit(1)

               filepath = os.path.realpath(filepath)
               urlstr   = self.url.scheme + '://' + self.url.netloc + filepath
               self.url = urllib.parse.urlparse(urlstr)

           if not self.follow_symlinks : return True

          # Note: if (not link) and follow -> path is unchanged, so file is created through linked name.

        # ==============
        # p partflg special case
        # ==============

        if self.partflg == 'p' :
           ok = self.poster.post_local_part(filepath,self.exchange,self.url,self.to_clusters,rename)
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
        # fixed blocksize specified.
        # ==============

        else:
           self.blocksize = self.chunksize_from_str(self.partflg)

        # ===================
        # post file in blocks (inplace)
        # ===================

        if self.blocksize > 0 :
           ok = self.poster.post_local_inplace(filepath,self.exchange,self.url, \
                                                  self.to_clusters,self.blocksize,self.sumflg,rename)
           if not ok : sys.exit(1)
           return

        # ==============
        # whole file
        # ==============

        ok = self.poster.post_local_file(filepath,self.exchange,self.url,self.to_clusters,self.sumflg,rename)
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

    def watching(self, fpath, event ):
        self.logger.debug("sr_post watching %s, ev=%s" % ( fpath, event ) )

        self.event = event
        if sys.platform == 'win32' : # put the slashes in the right direction on windows
           fpath = fpath.replace('\\','/')

        if self.document_root != None :
           dr = self.document_root
           rpath = fpath.replace(dr,'',1)
           if rpath == fpath :
              if fpath[0] != os.sep :
                 rpath = dr + os.sep + fpath
              else :
                 self.logger.error("document_root %s not present in %s" % (dr,fpath))
                 self.logger.error("no posting")
                 return False
           fpath = rpath
           if fpath[0] == '/' : fpath = fpath[1:]

        url = self.url
        self.url = urllib.parse.urlparse('%s://%s/%s'%(url.scheme,url.netloc,fpath))

        self.logger.debug("sr_post watching %s, ev=%s, url=%s" % ( fpath, event, url.geturl() ) )
        self.posting()
        self.url = url
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
 
        if self.document_root != None :
           if not self.document_root in watch_path :
              watch_path = self.document_root + os.sep + watch_path
 
        if not os.path.exists(watch_path):
           self.logger.error("Not found %s " % watch_path )
           sys.exit(1)

        watch_path = os.path.abspath (watch_path)
        if self.realpath:
            watch_path = os.path.realpath(watch_path)
 
        if os.path.isfile(watch_path):
           self.logger.info("file %s " % watch_path )
 
        if os.path.isdir(watch_path):
           self.logger.info("directory %s " % watch_path )
           if self.rename != None and self.rename[-1] != '/' and 'modify' in self.events:
              self.logger.warning("renaming all modified files to %s " % self.rename )

        self.watch_path = watch_path
 
        return watch_path


# ===================================
# MAIN
# ===================================

def main():

    post = sr_post(config=None,args=sys.argv[1:])
    if post.in_error : sys.exit(1)

    try :
             post.connect()

             if len(post.postpath) == 0 :
                post.postpath = sys.argv[post.first_arg:]

             if len(post.postpath) == 0 :
                post.logger.error("no path to post")
                post.help()
                os._exit(1)
               
             post.poster.logger = post.logger

             post.lock_set()
             for watchpath in post.postpath :

                 if watchpath[0] != os.path.sep :
                      watchpath = os.getcwd() + os.path.sep + watchpath

                 post.watch_path = watchpath


                 if os.path.islink(watchpath) : 
                    post.watching(watchpath,'link')
                 elif os.path.isfile(watchpath) : 
                    post.watching(watchpath,'modify')
                 else :
                    post.scandir_and_post(watchpath,post.recursive)


             post.lock_unset()
             post.close()

    except :
             (stype, value, tb) = sys.exc_info()
             post.logger.error("Type: %s, Value:%s\n" % (stype, value))
             sys.exit(1)

    """
    Workaround closes stderr to suppress error messages from sys.exit(0).
    See bug #74 for details. 
    """
    if post.debug:
        post.logger.debug("FIXME: if you connect to SSL broker, there is a tear down bug bug #74." )
        post.logger.debug("FIXME: Message is harmless, but should take the time to fix eventually." )
        post.logger.debug("FIXME: outside debug mode, the message is suppressed." )
    else:
        os.close(2)

    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()

