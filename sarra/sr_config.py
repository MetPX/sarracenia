#!/usr/bin/python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SaraDocumentation
#
# sr_config.py : python3 utility tool to configure sarracenia programs
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

import logging
import os,re,socket,sys
import urllib,urllib.parse

try :    from sr_util      import *
except : from sarra.sr_util import *

class sr_config:

    def __init__(self,config=None,args=None):

        self.program_name   = re.sub(r'(-script\.pyw|\.exe|\.py)?$', '', os.path.basename(sys.argv[0]) )
        self.config_name    = config
        self.etcdir         = os.getcwd()
        self.exedir         = os.getcwd()
        self.logdir         = os.getcwd()

        self.credentials    = []
        self.log_clusters   = {}

        if config != None :
           self.config_name = re.sub(r'(\.cfg|\.conf|\.config)','',os.path.basename(config))

        # set logging to printit until we are fixed with it

        self.setlog()
        self.logger.debug("sr_config __init__")

        # check arguments

        if args == [] : args = None

        # no settings call help

        if config == None and args == None :
           if hasattr(self,'help') : self.help()
           sys.exit(0)

        # initialisation settings

        self.user_args   = args
        self.user_config = config

    def args(self,args):

        self.logger.debug("sr_config args")

        if args == None : return

        i = 0
        while i < len(args):
              n = self.option(args[i:])
              if n == 0 : n = 1
              i = i + n

    def config(self,path):
        self.logger.debug("sr_config config")

        if path == None : return

        try:
            f = open(path, 'r')
        except:
            (type, value, tb) = sys.exc_info()
            self.logger.error("Type: %s, Value: %s" % (type, value))
            return 

        for line in f.readlines():
            words = line.split()
            if (len(words) >= 2 and not re.compile('^[ \t]*#').search(line)):
                self.option(words)

        f.close()

    def defaults(self):
        self.logger.debug("sr_config defaults")

        self.debug                = False

        self.document_root        = None

        self.events               = 'IN_CLOSE_WRITE|IN_DELETE'
        self.event                = 'IN_CLOSE_WRITE|IN_ATTRIB|IN_MOVED_TO|IN_MOVE_SELF'

        self.flow                 = None

        self.logpath              = None

        self.instance             = 0
        self.nbr_instances        = 1

        self.broker               = urllib.parse.urlparse('amqp://guest:guest@localhost/')
        self.exchange             = None
        self.topic_prefix         = 'v02.post'
        self.subtopic             = None
        self.url                  = None

        self.mirror               = True

        self.queue_name           = None

        self.randomize            = False

        self.reconnect            = False

        self.recursive            = False

        self.rename               = None

        self.source_broker        = urllib.parse.urlparse('amqp://guest:guest@localhost/')

        self.source_exchange      = None

        self.source_topic         = None

        self.source_from_exchange = False

        # cluster stuff
        self.from_cluster         = None
        self.from_aliases         = []
        self.to_clusters          = None
        self.gateway_for          = []

        self.ftp_user             = None
        self.ftp_password         = None
        self.ftp_mode             = 'passive'
        self.ftp_binary           = True
        self.http_user            = None
        self.http_password        = None
        self.sftp_user            = None
        self.sftp_password        = None
        self.sftp_keyfile         = None

        self.sleep                = 0
        self.strip                = 0

        self.parts                = '1'
        self.partflg              = '1'

        self.sumflg               = 'd'
        self.blocksize            = 0

        self.msg_script           = None
        self.file_script          = None

        #

        #self.destination          = URL()
        #self.destination.set('amqp://guest:guest@localhost/')
        #self.destination_exchange = 'sx_guest'

        self.exchange_key         = []


        self.inplace              = False
        self.overwrite            = False
        self.recompute_chksum     = False

    def general(self):
        self.logger.debug("sr_config general")

        homedir = os.path.expanduser("~")
        confdir = homedir + '/.config/sarra/'

        # read in provided credentials
        credent = confdir + 'credentials.conf'
        try :
                 f = open(credent,'r')
                 lines = f.readlines()
                 f.close
                 for line in lines :
                     line = line.strip()
                     if len(line) == 0 or line[0] == '#' : continue
                     parts = line.split()
                     url   = urllib.parse.urlparse(parts[0])
                     # fixme parts[1] ssh keyfile for sftp should be an option
                     self.credentials.append(url)

        # credential file is not mandatory
        except : 
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.debug("Type: %s, Value: %s" % (stype, svalue))
        self.logger.debug("credentials = %s\n" % self.credentials)

        # read in provided log cluster infos
        log_cluster = confdir + 'log2clusters.conf'
        i = 0
        try :
                 f = open(log_cluster,'r')
                 lines = f.readlines()
                 f.close
                 for line in lines :
                     line = line.strip()
                     if len(line) == 0 or line[0] == '#' : continue
                     parts = line.split()
                     name  = parts[0]
                     u     = urllib.parse.urlparse(parts[1])
                     ok, url = self.validate_amqp_url(u)
                     if not ok :
                        self.logger.error("problem with %s" % parts[1])
                     # fixme parts[2] exchange should be optional
                     exch  = parts[2]
                     self.log_clusters[i] = (name,url,exch)
                     i = i + 1

        # cluster file is not mandatory
        except : 
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.debug("Type: %s, Value: %s" % (stype, svalue))
        self.logger.debug("log_clusters = %s\n" % self.log_clusters)

        # sarra.conf ... defaults for the server
        sarra = homedir + '/.config/sarra/sarra.conf'
        if os.path.isfile(sarra) : self.config(sarra)


    def isTrue(self,s):
        if  s == 'True' or s == 'true' or s == 'yes' or s == 'on' or \
            s == 'Yes'  or s == 'YES' or s == 'TRUE' or s == 'ON' or \
            s == '1'    or s == 'On' :
            return True
        else:
            return False


    def option(self,words):
        self.logger.debug("sr_config option %s" % words[0])

        needexit = False
        n        = 0
        try:
                if words[0] in ['config','-c','--config']:
                     self.config(words[1])
                     n = 2

                elif words[0] in ['debug','-debug','--debug']:
                     if words[0][0:1] == '-' : 
                        self.debug = True
                        n = 1
                     else :
                        self.debug = self.isTrue(words[1])
                        n = 2
                     if self.debug :
                        self.logger.setLevel(logging.DEBUG)

                elif words[0] in ['document_root','-dr','--document_root']:
                     self.document_root = words[1]
                     n = 2

                elif words[0] in ['events','-e','--events']:
                     i = 0
                     if 'IN_CLOSE_WRITE' in words[1] : i = i + 1
                     if 'IN_DELETE'      in words[1] : i = i + 1
                     if i == 0 :
                        self.logger.error("events invalid (%s)" % words[1])
                        needexit = True
                     self.events = words[1]
                     n = 2

                elif words[0] in ['file_validation_script','-fs','--file_validation_script']:
                     ok = True
                     try    : exec(compile(open(words[1]).read(), words[1], 'exec'))
                     except : 
                              self.logger.error("file_validation_script invalid (%s)" % words[1])
                              ok = False

                     if self.file_script == None :
                        self.logger.error("file_validation_script invalid (%s)" % words[1])
                        ok = False

                     if not ok : needexit = True
                     n = 2

                elif words[0] in ['from_aliases','-fa','--from_aliases']:
                     self.from_aliases = words[1].split(',')
                     n = 2

                elif words[0] in ['from_cluster','-fc','--from_cluster']:
                     self.from_cluster = words[1] 
                     n = 2

                elif words[0] in ['flow','-f','--flow']:
                     self.flow = words[1] 
                     n = 2

                elif words[0] in ['help','-h','-help','--help']:
                     self.help()
                     needexit = True

                elif words[0] in ['log','-l','-log','--log']:
                     self.logpath = words[1]
                     n = 2

                elif words[0] in ['inplace','-in','--inplace']:
                     self.inplace = self.isTrue(words[1])
                     n = 2

                elif words[0] in ['instances','-i','--instances']:
                     self.nbr_instances = int(words[1])
                     n = 2

                elif words[0] in ['message_validation_script','-ms','--message_validation_script']:
                     ok = True
                     try    : exec(compile(open(words[1]).read(), words[1], 'exec'))
                     except : 
                              self.logger.error("message_validation_script invalid (%s)" % words[1])
                              ok = False
                     if self.msg_script == None :
                        self.logger.error("message_validation_script invalid (%s)" % words[1])
                        ok = False
                     if not ok : needexit = True
                     n = 2

                elif words[0] in ['parts','-p','--parts']:
                     self.parts   = words[1]
                     ok = self.validate_parts()
                     if not ok : needexit = True
                     n = 2

                elif words[0] in ['broker','-b','--broker'] :
                     self.broker = urllib.parse.urlparse(words[1])
                     ok, self.broker = self.validate_amqp_url(self.broker)
                     if not ok :
                        self.logger.error("broker has wrong protocol (%s)" % self.broker.scheme)
                        needexit = True
                     n = 2

                elif words[0] in ['exchange','-ex','--exchange'] :
                     self.exchange = words[1]
                     n = 2

                elif words[0] in ['to','-to','--to']:
                     self.to_clusters = words[1]
                     n = 2

                elif words[0] in ['topic_prefix','-tp','--topic_prefix'] :
                     self.topic_prefix = words[1]

                elif words[0] in ['subtopic','-sub','--subtopic'] :
                     self.subtopic = words[1]
                     n = 2

                elif words[0] in ['overwrite','-o','--overwrite'] :
                     self.overwrite = self.isTrue(words[1])
                     n = 2

                elif words[0] in ['queue_name','-qn','--queue_name'] :
                     self.queue_name = words[1]
                     n = 2

                elif words[0] in ['randomize','-r','--randomize']:
                     if words[0][0:1] == '-' : 
                        self.randomize = True
                        n = 1
                     else :
                        self.randomize = self.isTrue(words[1])
                        n = 2

                elif words[0] in ['recompute_chksum','-rc','--recompute_chksum']:
                     if words[0][0:1] == '-' : 
                        self.recompute_chksum = True
                        n = 1
                     else :
                        self.recompute_chksum = self.isTrue(words[1])
                        n = 2

                elif words[0] in ['reconnect','-rr','--reconnect']:
                     if words[0][0:1] == '-' : 
                        self.reconnect = True
                        n = 1
                     else :
                        self.reconnect = self.isTrue(words[1])
                        n = 2

                elif words[0] in ['recursive','-rec','--recursive']:
                     if words[0][0:1] == '-' : 
                        self.recursive = True
                        n = 1
                     else :
                        self.recursive = self.isTrue(words[1])
                        n = 2

                elif words[0] in ['rename','-rn','--rename']:
                     self.rename = words[1]
                     n = 2

                elif words[0] in ['gateway_for','-gf','--gateway_for']:
                     self.gateway_for = words[1].split(',')
                     n = 2

                elif words[0] in ['url','-u','--url']:
                     self.url = urllib.parse.urlparse(words[1])
                     n = 2

                elif words[0] in ['source_broker','-sb','--source_broker'] :
                     self.source_broker = urllib.parse.urlparse(words[1])
                     ok, self.source_broker = self.validate_amqp_url(self.source_broker)
                     if not ok :
                        self.logger.error("source_broker has wrong protocol (%s)" % self.source_broker.scheme)
                        needexit = True
                     n = 2

                elif words[0] in ['source_exchange','-se','--source_exchange']:
                     self.source_exchange = words[1]
                     n = 2

                elif words[0] in ['source_from_exchange','-sfe','--source_from_exchange']:
                     if words[0][0:1] == '-' : 
                        self.source_from_exchange = True
                        n = 1
                     else :
                        self.source_from_exchange = self.isTrue(words[1])
                        n = 2

                elif words[0] in ['ftp_user','-fu','--ftp_user']:
                     self.ftp_user = words[1]
                     n = 2

                elif words[0] in ['ftp_password','-fp','--ftp_password']:
                     self.ftp_password = words[1]
                     n = 2

                elif words[0] in ['ftp_mode','-fm','--ftp_mode']:
                     if not words[1] in ['active','passive'] :
                        self.logger.error("ftp_mode is active or passive")
                        needexit = True
                     self.ftp_mode = words[1]
                     n = 2

                elif words[0] in ['ftp_binary','-fb','--ftp_binary']:
                     self.ftp_binary = self.isTrue(words[1])
                     n = 2

                elif words[0] in ['mirror','-mirror','--mirror']:
                     self.mirror = self.isTrue(words[1])
                     n = 2

                elif words[0] in ['http_user','-hu','--http_user']:
                     self.http_user = words[1]
                     n = 2

                elif words[0] in ['http_password','-hp','--http_password']:
                     self.http_password = words[1]
                     n = 2

                elif words[0] in ['url_password','-up','--url_password']:
                     self.password = words[1]
                     n = 2

                elif words[0] in ['sftp_user','-su','--sftp_user']:
                     self.sftp_user = words[1]
                     n = 2

                elif words[0] in ['sftp_password','-sp','--sftp_password']:
                     self.sftp_password = words[1]
                     n = 2

                elif words[0] in ['sftp_keyfile','-sk','--sftp_keyfile']:
                     self.sftp_keyfile = words[1]
                     n = 2

                elif words[0] in ['source_topic','-st','--source_topic']:
                     self.source_topic = words[1]
                     n = 2

                elif words[0] in ['sleep','-sleep','--sleep']:
                     self.sleep = int(words[1])
                     n = 2

                elif words[0] in ['strip','-strip','--strip']:
                     self.strip = int(words[1])
                     n = 2

                elif words[0] in ['sum','-sum','--sum']:
                     self.sumflg = words[1]
                     ok = self.validate_sum()
                     if not ok : needexit = True
                     n = 2

                # XXX
                elif words[0] in ['destination_exchange','-de','--destination_exchange']:
                     self.dest_exchange = words[1]
                     n = 2
                elif words[0] in ['destination','-d','--destination'] :
                     self.destination.set(words[1])
                     n = 2
                elif words[0] in ['exchange_key','-ek','--exchange_key']:
                     self.exchange_key.append(words[1])
                     n = 2
                elif words[0] in ['transmission_url','-tr','--transmission_url']:
                     self.transmission.set(words[1])
                     n = 2
                elif words[0] in ['transmission_document_root','-tdr','--transmission_document_root']:
                     self.trx_document_root = words[1]
                     n = 2


        except:
                (stype, svalue, tb) = sys.exc_info()
                self.logger.debug("Type: %s, Value: %s,  ..." % (stype, svalue))

        if needexit :
           sys.exit(0)

        return n

    def setlog(self):

        import logging.handlers

        LOG_FORMAT  = ('%(asctime)s [%(levelname)s] %(message)s')

        if not hasattr(self,'logger') :
           logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
           self.logger = logging.getLogger()
           self.lpath  = None
           self.logger.debug("sr_config setlog 1")
           return

        if self.logpath == self.lpath :
           self.logger.debug("sr_config setlog 2")
           if hasattr(self,'debug') and self.debug : self.logger.setLevel(logging.DEBUG)
           return

        if self.logpath == None :
           self.logger.debug("switching log to stdout")
           del self.logger
           self.setlog()
           return

        self.logger.debug("switching to log file %s" % self.logpath )
          
        self.lpath   = self.logpath
        self.handler = logging.handlers.TimedRotatingFileHandler(self.lpath, when='midnight', interval=1, backupCount=5)
        fmt          = logging.Formatter( LOG_FORMAT )
        self.handler.setFormatter(fmt)

        del self.logger

        self.logger = logging.RootLogger(logging.WARNING)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

        if self.debug :
           self.logger.setLevel(logging.DEBUG)

    def validate_amqp_url(self,url):
        if not url.scheme in ['amqp','amqps'] :
           return False,url

        return self.validate_url(url)

    # check url and add credentials if needed from credential file

    def validate_url(self,url):

        rebuild = False
        user    = url.username
        pasw    = url.password

        # default vhost is '/'
        if url.scheme in ['amqp','amqps'] :
           path = url.path
           if path == None or path == '' :
              path = '/'
              rebuild = True

        if user == None or pasw == None :
           for u in self.credentials :
               if url.scheme    != u.scheme  : continue
               if url.hostname  != u.hostname: continue
               if url.port      != u.port    : continue
               if user and user != u.username: continue
               user = u.username
               pasw = u.password
               rebuild = True
               break

        if url.scheme in ['amqp','amqps'] :
           if user == None :
              user = 'guest'
              rebuild = True
           if pasw == None :
              pasw = 'guest'
              rebuild = True
               
        if path == None : path = ''

        if rebuild :
           netloc = url.hostname
           if url.port != None : netloc += ':%d'%url.port
           urls = '%s://%s:%s@%s%s' % (url.scheme,user,pasw,netloc,path)
           url  = urllib.parse.urlparse(urls)

        return True,url

    def validate_parts(self):
        if not self.parts[0] in ['1','p','i']:
           self.logger.error("parts invalid (%s)" % self.parts)
           return False

        self.partflg = self.parts[0]
        token = self.parts.split(',')
        if self.partflg in ['1','p'] and len(token) != 1 :
           self.logger.error("parts invalid (%s)" % self.parts)
           return False
        if self.partflg == 'i':
           if len(token) != 2 :
              self.logger.error("parts invalid (%s)" % self.parts)
              return False
           try    : self.blocksize = chunksize_from_str(token[1])
           except :
                    self.logger.error("parts invalid (%s)" % self.parts)
                    return False
        return True

    def validate_sum(self):
        if self.sumflg[0] in ['0','n','d']: return True
        try :
                 chkclass = Checksum()
                 chkclass.from_list(self.sumflg)
                 return True
        except : 
                 (stype, svalue, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s" % (stype, svalue))
                 self.logger.error("sum invalid (%s)" % self.sumflg)
                 return False
        return False


# ===================================
# MAIN
# ===================================

def main():

    if len(sys.argv) == 1 :
       print(" None None")
       cfg = sr_config(None,None)
    elif os.path.isfile(sys.argv[1]):
       args = None
       if len(sys.argv) > 2 : args = sys.argv[2:]
       print(" Conf %s" % args)
       cfg = sr_config(sys.argv[1],args)
    else :
       print(" None %s" % sys.argv[1:])
       cfg = sr_config(None,sys.argv[1:])
    cfg.defaults()
    #to get more details
    cfg.debug = True
    cfg.setlog()
    cfg.general()
    cfg.args(cfg.user_args)
    cfg.config(cfg.user_config)
    print("  %s" % cfg.source_from_exchange)
    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()
