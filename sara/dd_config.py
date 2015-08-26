#!/usr/bin/python3

import os,re,sys
import urllib,urllib.parse

try :    from dd_util      import *
except : from sara.dd_util import *

class dd_config:

    def __init__(self,config=None,args=None):

        self.program_name = re.sub(r'(-script\.pyw|\.exe|\.py)?$', '', os.path.basename(sys.argv[0]) )
        self.config_name  = config
        self.etcdir       = os.getcwd()
        self.exedir       = os.getcwd()
        self.logdir       = os.getcwd()

        if config != None :
           self.config_name = re.sub(r'(\.cfg|\.conf|\.config)','',os.path.basename(config))

        # set logging to printit until we are fixed with it

        self.setlog()
        
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

        if args == None : return

        i = 0
        while i < len(args):
              n = self.option(args[i:])
              if n == 0 : n = 1
              i = i + n

    def config(self,path):

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

    def configure(self):

        # defaults general and proper to dd_post

        self.defaults()

        # arguments from command line

        self.args(self.user_args)

        # config from file

        self.config(self.user_config)

        # verify all settings

        if hasattr(self,'check') : self.check()

    def defaults(self):

        self.debug                = False

        self.document_root        = None

        self.flow                 = None

        self.logpath              = None

        self.instance             = 0
        self.nbr_instances        = 0

        self.post_broker          = urllib.parse.urlparse('amqp://guest:guest@localhost/')

        self.post_exchange        = None

        self.post_topic_key       = None

        self.post_url             = None

        self.queue_name           = None

        self.randomize            = False

        self.reconnect            = False

        self.rename               = None

        self.source               = None

        self.source_broker        = urllib.parse.urlparse('amqp://guest:guest@localhost/')

        self.source_exchange      = None

        self.source_topic_key     = None

        self.parts                = '1'
        self.partflg              = '1'

        self.blocksize            = 0

        self.sumflg               = 'd'

        #

        self.destination          = URL()
        self.destination.set('amqp://guest:guest@localhost/')
        self.destination_exchange = 'sx_guest'

        self.exchange_key         = []

        self.recompute_chksum     = False


    def isTrue(self,s):
        if  s == 'True' or s == 'true' or s == 'yes' or s == 'on' or \
            s == 'Yes'  or s == 'YES' or s == 'TRUE' or s == 'ON' or \
            s == '1'    or s == 'On' :
            return True
        else:
            return False


    def option(self,words):

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

                if   words[0] in ['blocksize','-bz','--blocksize']:
                     self.blocksize = chunksize_from_str(words[1])
                     n = 2

                elif words[0] in ['flow','-f','--flow']:
                     self.flow = words[1] 
                     n = 2

                elif words[0] in ['help','-h','-help','--help']:
                     needexit = True
                     if hasattr(self,'help') : self.help()

                elif words[0] in ['log','-l','-log','--log']:
                     self.logpath = words[1]
                     n = 2

                elif words[0] in ['instances','-i','--instances']:
                     self.nbr_instances = int(words[1])
                     n = 2

                elif words[0] in ['parts','-p','--parts']:
                     self.parts   = words[1]
                     ok = self.validate_parts()
                     if not ok : 
                        if hasattr(self,'help') : self.help()
                        needexit = True
                     n = 2

                elif words[0] in ['post_broker','-pb','--post_broker'] :
                     self.post_broker = urllib.parse.urlparse(words[1])

                elif words[0] in ['post_exchange','-pe','--post_exchange'] :
                     self.post_exchange = words[1]
                     n = 2

                elif words[0] in ['post_topic_key','-pk','--post_topic_key'] :
                     self.post_topic_key = words[1]
                     n = 2

                elif words[0] in ['post_url','-pu','--post_url'] :
                     self.post_url = urllib.parse.urlparse(words[1])

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

                elif words[0] in ['rename','-rn','--rename']:
                     self.rename = words[1]
                     n = 2


                elif words[0] in ['source','-s','--source']:
                     self.source = urllib.parse.urlparse(words[1])
                     n = 2

                elif words[0] in ['source_broker','-sb','--source_broker'] :
                     self.source_broker = urllib.parse.urlparse(words[1])
                     n = 2

                elif words[0] in ['source_exchange','-se','--source_exchange']:
                     self.source_exchange = words[1]
                     n = 2

                elif words[0] in ['source_topic_key','-stk','--source_topic_key']:
                     self.source_topic_key = words[1]
                     n = 2

                elif words[0] in ['sum','-sum','--sum']:
                     self.sumflg = words[1]
                     ok = self.validate_sum()
                     if not ok : 
                        if hasattr(self,'help') : self.help()
                        needexit = True
                     n = 2

                elif words[0] in ['destination_exchange','-de','--destination_exchange']:
                     self.dest_exchange = words[1]
                     n = 2
                elif words[0] in ['destination','-d','--destination'] :
                     self.destination.set(words[1])
                     n = 2
                elif words[0] in ['exchange_key','-ek','--exchange_key']:
                     self.exchange_key.append(words[1])
                     n = 2

                elif words[0] in ['ssh_keyfile','-sk','--ssh_keyfile']:
                     self.ssh_keyfile = words[1]
                     n = 2
                elif words[0] in ['strip','-st','--strip']:
                     self.strip = int(words[1])
                     n = 2
                elif words[0] in ['transmission_url','-tr','--transmission_url']:
                     self.transmission.set(words[1])
                     n = 2
                elif words[0] in ['transmission_document_root','-tdr','--transmission_document_root']:
                     self.trx_document_root = words[1]
                     n = 2


                elif words[0] in ['clustered','-cl','--clustered']:
                     if words[0][0:1] == '-' : 
                        self.clustered = True
                        n = 1
                     else :
                        self.clustered = self.isTrue(words[1])
                        n = 2
        except:
                pass

        if needexit : sys.exit(0)

        return n

    def setlog(self):

        import logging
        import logging.handlers

        LOG_FORMAT  = ('%(asctime)s [%(levelname)s] %(message)s')

        if not hasattr(self,'logger') :
           logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
           self.logger = logging.getLogger()
           self.lpath  = None
           return

        if self.logpath == self.lpath :
           if self.debug : self.logger.setLevel(logging.DEBUG)
           return

        if self.logpath == None :
           self.logger.debug("switching log to stdout")
           del self.logger
           self.setlog()
           return

        logpath = self.logpath
        logpath = logpath.replace('PGM',self.program_name)
        logpath = logpath.replace('PID',     "%s"   % os.getpid())
        logpath = logpath.replace('INSTANCE',"%.4d" % self.instance )
        if self.user_config != None :
           logpath = logpath.replace('CONFIG',self.user_config)

        self.logger.debug("switching to log file %s" % logpath )
          
        self.lpath   = self.logpath
        self.handler = logging.handlers.TimedRotatingFileHandler(logpath, when='midnight', interval=1, backupCount=5)
        fmt          = logging.Formatter( LOG_FORMAT )
        self.handler.setFormatter(fmt)

        del self.logger

        self.logger = logging.RootLogger(logging.WARNING)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

        if self.debug :
           self.logger.setLevel(logging.DEBUG)

    def validate_parts(self):
        if not self.parts[0] in ['1','p','i']:
           self.logger.error("parts invalid (%s)" % self.parts)
           return False

        self.partflg = self.parts[0]
        token = self.parts.split(',')
        if self.partflg == '1' and len(token) != 1 :
           self.logger.error("parts invalid (%s)" % self.parts)
           return False
        if self.partflg in ['p','i'] :
           if len(token) != 2 :
              self.logger.error("parts invalid (%s)" % self.parts)
              return False
           try    : self.blocksize = chunksize_from_str(token[1])
           except :
                    self.logger.error("parts invalid (%s)" % self.parts)
                    return False
        return True

    def validate_sum(self):
        if not self.sumflg[0] in ['0','n','d','c']:
           self.logger.error("sum invalid (%s)" % self.sumflg)
           return false
        return True


# ===================================
# MAIN
# ===================================

def main():

    cfg = dd_config(None,sys.argv[1:])
    sys.exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
   main()

