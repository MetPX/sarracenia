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

    def check(self):

        if self.url == None :
           self.logger.error("url required")
           sys.exit(1)

        # sarra exchange default value is xs_username
        # username being the broker's

        if self.exchange == None :
           self.exchange = 'xs_%s' % self.broker.username

        if self.to_clusters == None :
           self.logger.error("-to option is mandatory\n")
           self.help()
           sys.exit(1)

    def close(self):
        self.poster.close()

    def connect(self):

        # sr_post : no loop to reconnect to broker

        self.loop = True
        if self.program_name == 'sr_post' :
           self.loop = False

        # message

        self.msg = sr_message( self.logger )

        # publisher

        self.post_broker   = self.broker
        self.poster        = sr_poster(self, self.loop)
        self.msg.publisher = self.poster.publisher

                                   
    def help(self):
        print("\nUsage: %s -u <url> -b <broker> ... [OPTIONS]\n" % self.program_name )
        print("OPTIONS:")
        print("-b   <broker>          default:amqp://guest:guest@localhost/")
        print("-c   <config_file>")
        print("-dr  <document_root>   default:None")
        if self.program_name == 'sr_watch' : print("-e   <events>          default:IN_CLOSE_WRITE\n")
        print("-ex  <exchange>        default:xs_\"broker.username\"")
        print("-f   <flow>            default:None\n")
        print("-h|--help\n")
        print("-l   <logpath>         default:stdout")
        print("-p   <parts>           default:1")
        print("-to  <name1,name2,...> defines target clusters, mandatory")
        print("-tp  <topic_prefix>    default:v02.post")
        print("-sub <subtopic>        default:'path.of.file'")
        print("-rn  <rename>          default:None")
        print("-sum <sum>             default:d")
        print("-on_post <script>      default:None")
        print("DEBUG:")
        print("-debug")
        print("-r  : randomize chunk posting")
        print("-rr : reconnect between chunks\n")

    def instantiate(self,i=0):
        self.instance = i
        self.setlog()

    # =============
    # __on_post__ internal posting of message
    # =============

    def __on_post__(self):
        self.logger.debug("sr_post __on_post__")

        # invoke on_post when provided

        if self.on_post :
           self.logger.debug("sr_post user on_post")
           ok = self.on_post(self)
           if not ok: return ok

        # should always be ok

        ok = self.msg.publish( )

        return ok

    def overwrite_defaults(self):

        ok, details = self.credentials.get("amqp://guest:guest@localhost/")
        self.broker = details.url

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

        # rename path given with no filename

        rename = self.rename
        if self.rename != None and self.rename[-1] == os.sep :
           rename += os.path.basename(self.url.path)

        filename = os.path.basename(filepath)

        # ==============
        # delete event...
        # ==============

        if self.event == 'IN_DELETE' :
           ok = self.poster.post(self.exchange,self.url,self.to_clusters,None,'R,0',rename,filename)
           if not ok : sys.exit(1)
           return

        # ==============
        # p partflg special case
        # ==============

        if self.partflg == 'p' :
           ok = self.poster.post_local_part(filepath,self.exchange,self.url,self.to_clusters,rename)
           if not ok : sys.exit(1)
           return

        # ==============
        # blocksize != 0
        # ==============

        if self.blocksize != 0 :
           ok = self.poster.post_local_inplace(filepath,self.exchange,self.url, \
                                                  self.to_clusters,self.blocksize,self.sumflg,rename)
           if not ok : sys.exit(1)
           return

        # ==============
        # regular file
        # ==============

        ok = self.poster.post_local_file(filepath,self.exchange,self.url,self.to_clusters,self.sumflg,rename)
        if not ok: sys.exit(1)
        return

    def watching(self, fpath, event ):

        self.event = event

        if sys.platform == 'win32' : # put the slashes in the right direction on windows
           fpath = fpath.replace('\\','/')

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

