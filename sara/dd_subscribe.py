#!/usr/bin/python3

import logging, logging.handlers, os, random, re, signal, string, sys, time, getopt

#============================================================
# usage example
#
# python dd_subscribe.py configfile.conf

#============================================================

try :    
         from dd_amqp           import *
         from dd_file           import *
         from dd_http           import *
         from dd_message        import *
except : 
         from sara.dd_amqp      import *
         from sara.dd_file      import *
         from sara.dd_http      import *
         from sara.dd_message   import *


#############################################################################################
# Class AlarmTimeout

class TimeoutException(Exception):
    """Classe d'exception specialises au timeout"""
    pass

class AlarmTimeout:
      def __init__(self, message ):
          self.state   = False
          self.message = message
      def sigalarm(self, n, f):
          raise TimeoutException(self.message)
      def alarm(self, time):
          self.state = True
          signal.signal(signal.SIGALRM, self.sigalarm)
          signal.alarm(time)
      def cancel(self):
          signal.alarm(0)
          self.state = False

#============================================================

class ConsumerX(object):

    def __init__(self,config,logger):
        self.logger     = logger

        self.connected  = False

        self.connection  = None
        self.channel     = None
        self.log_channel = None
        self.ssl        = False

        self.queue      = None
        self.durable    = False
        self.expire     = None

        self.notify_only = False
        self.discard = False
        
        self.config = config
        self.name   = config

        self.amqp_log = None
        self.myinit()

        self.timex = None

    def close(self):
       self.hc.close()
       self.connected = False

    def connect(self):

        self.hc = None

        self.hc = HostConnect( logger = self.logger )
        self.hc.set_credentials(self.protocol,self.amqp_user,self.amqp_passwd,self.host,self.port,self.vhost)
        self.hc.connect()

        self.consumer = Consumer(self.hc)
        self.consumer.add_prefetch(1)
        self.consumer.build()

        ex = Exchange(self.hc,self.exchange)
        ex.build()

        self.msg_queue = Queue(self.hc,self.queue)
        if self.expire != None :
           self.msg_queue.add_expire(self.expire)

        for k in self.exchange_key :
           self.logger.info('Binding %s to %s with %s', self.exchange, self.queue, k)
           self.msg_queue.add_binding(self.exchange, k )

        self.msg_queue.build()

        if self.log_back :
           self.amqp_log = Publisher(self.hc)
           self.amqp_log.build()
           xlog = Exchange(self.hc,'xlog')
           xlog.build()

    def reconnect(self):
        self.close()
        self.connect()

    def run(self):

        if self.discard:
           self.inplace   = False
           self.overwrite = True
           self.log_back  = False

        if self.notify_only :
           self.log_back  = False

        self.logger.info("AMQP  broker(%s) user(%s) vhost(%s)" % (self.host,self.amqp_user,'/') )
        for k in self.exchange_key :
            self.logger.info("AMQP  input :    exchange(%s) topic(%s)" % (self.exchange,k) )
        if self.log_back :
            self.logger.info("AMQP  output:    exchange(%s) topic(%s)\n" % ('xlog','v02.log.#') )


        if not self.connected : self.connect()

        if not hasattr(self,'msg') :
           self.msg = dd_message(self.logger)

        self.msg.amqp_log     = self.amqp_log
        self.msg.logger       = self.logger


        while True :

             try  :
                  raw_msg = self.consumer.consume(self.queue)
                  if raw_msg == None : continue

                  # make use it as a dd_message

                  self.msg.from_amqplib(raw_msg)

                  self.logger.debug("Received topic   %s" % self.msg.topic)
                  self.logger.debug("Received notice  %s" % self.msg.notice)
                  self.logger.debug("Received headers %s" % self.msg.hdrstr)

                  processed = self.treat_message()

                  if processed :
                     self.consumer.ack(raw_msg)
             except (KeyboardInterrupt, SystemExit):
                 break                 
             except :
                 (type, value, tb) = sys.exc_info()
                 self.logger.error("Type: %s, Value: %s,  ..." % (type, value))
                 
    def myinit(self):
        self.bufsize       = 128 * 1024     # read/write buffer size

        self.protocol      = 'amqp'
        self.host          = 'dd.weather.gc.ca'
        self.port          = '5672'
        self.amqp_user     = 'anonymous'
        self.amqp_passwd   = 'anonymous'
        self.vhost         = '/'
        self.masks         = []             # All the masks (accept and reject)
        self.lock          = '.tmp'         # file send with extension .tmp for lock

        self.exchange      = 'xpublic'
        self.exchange_type = 'topic'
        self.exchange_key  = []

        self.http_user     = None
        self.http_passwd   = None

        self.flatten       = '/'
        self.mirror        = False

        self.strip         = 0
        self.overwrite     = True
        self.inplace       = True
        self.log_back      = True
        
        self.readConfig()

        # if not set in config : automated queue name saved in queuefile

        if self.queue == None :
           self.queuefile = ''
           parts = self.config.split(os.sep)
           if len(parts) != 1 :  self.queuefile = os.sep.join(parts[:-1]) + os.sep

           fnp   = parts[-1].split('.')
           if fnp[0][0] != '.' : fnp[0] = '.' + fnp[0]
           self.queuefile = self.queuefile + '.'.join(fnp[:-1]) + '.queue'

           self.queuename()

    def queuename(self) :

        self.queue  = 'cmc'
        if sys.version[:1] >= '3' :
           self.queue += '.' + str(random.randint(0,100000000)).zfill(8)
           self.queue += '.' + str(random.randint(0,100000000)).zfill(8)
        else :
           self.queue += '.' + string.zfill(random.randint(0,100000000),8)
           self.queue += '.' + string.zfill(random.randint(0,100000000),8)

        if os.path.isfile(self.queuefile) :
           f = open(self.queuefile)
           self.queue = f.read()
           f.close()
        else :
           f = open(self.queuefile,'w')
           f.write(self.queue)
           f.close()


    # url path will be replicated under odir (the directory given in config file)
    def mirrorpath(self, odir, url ):
        nodir = odir

        start = 3
        if self.strip > 0 :
           start = start + self.strip
           if start > len(parts)-1 : return nodir
        
        try :
              parts = url.split("/")
              for d in parts[start:-1] :
                  nodir = nodir + os.sep + d
                  if os.path.isdir(nodir) : continue
                  os.mkdir(nodir)
        except :
              self.logger.error("could not create or use directory %s" % nodir)
              return None

        return nodir

    # process individual url notification
    def treat_message(self):

        url = self.msg.url.geturl()

        # root directory where the product will be put
        odir = self.getMatchingMask(url)

        # no root directory for this url means url not selected
        if not odir : return True
        
        # notify_only mode : print out received message
        if self.notify_only :
           self.logger.info("%s %s" % (self.msg.notice,self.msg.hdrstr))
           return True
        
        # root directory should exists
        if not os.path.isdir(odir) :
           self.logger.error("directory %s does not exist" % odir)
           return False

        # mirror mode True
        # means extend root directory with url directory
        nodir = odir
        if self.mirror :
           nodir = self.mirrorpath(odir,url)
           if nodir == None : return False

        # filename setting
        parts = url.split("/")
        fname = parts[-1]

        # flatten mode True
        # means use url to create filename by replacing "/" for self.flatten character
        if self.flatten != '/' :
           start = 3
           if self.strip > 0 :
              start = start + self.strip
              if start > len(parts)-1 :
                 fname = parts[-1]
              else :
                 fname = self.flatten.join(parts[start:])

        # setting filepath and temporary filepath
        opath = nodir + os.sep + fname

        # setting local_file and URL and how the file is renamed

        self.msg.set_local(self.inplace,opath,urllib.parse.urlparse('file:'+opath))
        self.msg.headers['rename'] = opath

        # if local_file has same checksum nothing to do

        if not self.overwrite and self.msg.checksum_match() :
           self.msg.code    = 304
           self.msg.message = 'not modified'
           self.msg.log_info()

           # a part unmodified can make a difference
           if self.inplace and self.msg.in_partfile :
              file_reassemble(self.msg)

           file_truncate(self.msg)
           return True

        # download the file

        self.download(self.msg,url,self.http_user,self.http_passwd)
        return True

    def house_keeping(self):

        # Delayed insertion
        # try reassemble the file, conditions may have changed since writing

        if self.inplace and self.msg.in_partfile :
           self.msg.code    = 307
           self.msg.message = 'Temporary Redirect'
           self.msg.log_info()
           file_reassemble(self.msg)
           return True

        # announcing the download or insert

        if self.msg.partflg != '1' :
           if self.inplace : self.msg.change_partflg('i')
           else            : self.msg.change_partflg('p')

        self.msg.set_topic_url('v02.post',self.msg.local_url)
        self.msg.set_notice(self.msg.local_url,self.msg.time)
        self.msg.code    = 201
        self.msg.message = 'Downloaded'
        self.msg.log_info()
              
        # if we inserted a part in file ... try reassemble

        if self.inplace and self.msg.partflg != '1' :
           file_reassemble(self.msg)

        return True

    def download(self,msg,url,user=None,password=None) :

        if sys.version[:1] >= '3' :
           import urllib.request, urllib.error
           urllib_request = urllib.request
           urllib_error   = urllib.error
        else :
           import urllib2
           urllib_request = urllib2
           urllib_error   = urllib2

        # get the file, in case of error it will try three times.
        nb_try = 0
        while nb_try < 3:
            nb_try = nb_try + 1
            # gives self.timeout seconds to get the product       
            if self.timex != None:self.timex.alarm(self.timeout)
            try :
                # create a password manager                
                if user != None :                          
                    # Add the username and password.
                    password_mgr = urllib_request.HTTPPasswordMgrWithDefaultRealm()
                    password_mgr.add_password(None, url, user, password)
                    handler = urllib_request.HTTPBasicAuthHandler(password_mgr)
                        
                    # create "opener" (OpenerDirector instance)
                    opener = urllib_request.build_opener(handler)
    
                    # use the opener to fetch a URL
                    opener.open(url)
    
                    # Install the opener.
                    # Now all calls to urllib2.urlopen use our opener.
                    urllib_request.install_opener(opener)

                # set a byte range to pull from remote file

                req   = urllib_request.Request(url)

                if msg.partflg == 'i' :
                   str_range = 'bytes=%d-%d'%(msg.offset,msg.offset+msg.length-1)
                   req.headers['Range'] = str_range
                   
                response = urllib_request.urlopen(req)

                self.write_to_file(response,msg)                    

                self.house_keeping()
                #self.logger.info('Download successful: %s', url)  
                
                #option to discard file
                if self.discard: 
                    try:
                        os.unlink(self.msg.local_file)
                        self.logger.info('Discard %s', self.msg.local_file)
                    except:
                        self.logger.error('Unable to discard %s', self.msg.local_file)
                else:
                    self.logger.info('Local file created: %s', self.msg.local_file)
                    
                if self.timex != None:self.timex.cancel()
                break
            except (KeyboardInterrupt, SystemExit):
                 break                     
            except TimeoutException:                    
                self.logger.error('Download failed: %s', url)                    
                self.logger.error('Connection timeout')
            except urllib_error.HTTPError as e:
                self.logger.error('Download failed: %s', url)                    
                self.logger.error('Server couldn\'t fulfill the request. Error code: %s, %s', e.code, e.reason)
            except urllib_error.URLError as e:
                self.logger.error('Download failed: %s', url)                                    
                self.logger.error('Failed to reach server. Reason: %s', e.reason)            
            except:
                self.logger.error('Download failed: %s', url )
                self.logger.error('Uexpected error')              
                
            if self.timex != None:self.timex.cancel()
            self.logger.info('Retry in 3 seconds...')
            time.sleep(3)

    def write_to_file(self,req,msg) :

        # no locking if insert
        if msg.partflg != '1' and not msg.in_partfile :
           local_file = msg.local_file
        else :
           local_file = msg.local_file + self.lock
           if self.lock == '.' :
              token = msg.local_file.split(os.sep)
              local_file = os.sep.join(token[-1]) + os.sep + '.' + token[-1]
              self.logger.debug("lock file = %s" % local_file)
           
        # download/write
        if not os.path.isfile(local_file) :
           fp = open(local_file,'w')
           fp.close

        fp = open(local_file,'r+b')
        if msg.local_offset != 0 : fp.seek(msg.local_offset,0)

        while True:
          chunk = req.read(msg.bufsize)
          if not chunk : break
          fp.write(chunk)

        fp.close()

        # unlock
        if local_file != msg.local_file :
           os.rename(local_file,msg.local_file)

    def readConfig(self):
        currentDir = '.'
        currentFileOption = 'NONE' 
        self.readConfigFile(self.config,currentDir,currentFileOption)

    def readConfigFile(self,filePath,currentDir,currentFileOption):
        
        def isTrue(s):
            if  s == 'True' or s == 'true' or s == 'yes' or s == 'on' or \
                s == 'Yes' or s == 'YES' or s == 'TRUE' or s == 'ON' or \
                s == '1' or  s == 'On' :
                return True
            else:
                return False

        try:
            config = open(filePath, 'r')
        except:
            (type, value, tb) = sys.exc_info()
            print("Type: %s, Value: %s" % (type, value))
            return 

        self.timeout = 180

        for line in config.readlines():
            words = line.split()
            if (len(words) >= 2 and not re.compile('^[ \t]*#').search(line)):
                try:
                    if   words[0] == 'accept':
                         cmask       = re.compile(words[1])
                         cFileOption = currentFileOption
                         if len(words) > 2: cFileOption = words[2]
                         self.masks.append((words[1], currentDir, cFileOption, cmask, True))
                    elif words[0] == 'reject':
                         cmask = re.compile(words[1])
                         self.masks.append((words[1], currentDir, currentFileOption, cmask, False))
                    elif words[0] == 'directory': currentDir = words[1]
                    elif words[0] == 'protocol': self.protocol = words[1]
                    elif words[0] == 'host': self.host = words[1]
                    elif words[0] == 'port': self.port = int(words[1])
                    elif words[0] == 'amqp-user': self.amqp_user = words[1]
                    elif words[0] == 'amqp-password': self.amqp_passwd = words[1]
                    elif words[0] == 'vhost': self.vhost = words[1]
                    elif words[0] == 'lock': self.lock = words[1]

                    elif words[0] == 'exchange': self.exchange = words[1]
                    elif words[0] == 'exchange_type': 
                         if words[1] in ['fanout','direct','topic','headers'] :
                            self.exchange_type = words[1]
                         else :
                            self.logger.error("Problem with exchange_type %s" % words[1])
                    elif words[0] == 'exchange_key': self.exchange_key.append(words[1])
                    elif words[0] == 'http-user': self.http_user = words[1]
                    elif words[0] == 'http-password': self.http_passwd = words[1]
                    elif words[0] == 'mirror': self.mirror = isTrue(words[1])
                    elif words[0] == 'flatten': self.flatten = words[1]
                    elif words[0] == 'timeout': self.timeout = int(words[1])

                    elif words[0] == 'durable': self.durable = isTrue(words[1])
                    elif words[0] == 'expire': self.expire = int(words[1]) * 60 * 1000
                    elif words[0] == 'strip': self.strip = int(words[1])
                    elif words[0] == 'overwrite': self.overwrite = isTrue(words[1])
                    elif words[0] == 'inplace': self.inplace = isTrue(words[1])
                    elif words[0] == 'log_back': self.log_back = isTrue(words[1])
                    elif words[0] == 'queue': self.queue = words[1] 
                    else:
                        self.logger.error("Unknown configuration directive %s in %s" % (words[0], self.config))
                        print("Unknown configuration directive %s in %s" % (words[0], self.config))
                except:
                    self.logger.error("Problem with this line (%s) in configuration file of client %s" % (words, self.name))
        config.close()
    
    def getMatchingMask(self, filename): 
        for mask in self.masks:
            if mask[3].match(filename) != None :
               if mask[4] : return mask[1]
               return None
        return None

def help():     
    #print chr(27)+'[1m'+'Script'+chr(27)+'[0m'
    print("Usage: dd_subscribe [OPTION]...[CONFIG_FILE]")
    print("dd_subscribe [-n|--no-download] [-d|--download-and-discard] [-l|--log-dir] config-file")
    print("rabbitmq python client connects to rabbitmq server for getting notice in real time to download new files")
    print("Examples:")    
    print("dd_subscribe subscribe.conf  # download files and display log in stout")
    print("dd_subscribe -d subscribe.conf  # discard files after downloaded and display log in stout")
    print("dd_subscribe -l /tmp subscribe.conf  # download files,write log file in directory /tmp")
    print("dd_subscribe -n subscribe.conf  # get notice only, no file downloaded and display log in stout")        

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    #print('Resume in 5 seconds...')
    #time.sleep(5)
    sys.exit()
    #os.kill(os.getpid(),9)

def verify_version():    
    python_version = (2,6,0)
    if sys.version_info < python_version :
        sys.stderr.write("Python version higher than 2.6.0 required.\n")
        exit(1)
        
    amqplib_version = '1.0.0'   
    if amqp.connection.LIBRARY_PROPERTIES['library_version'] < amqplib_version:
        sys.stderr.write("Amqplib version %s or higher required.\n" % amqplib_version)        
        exit(1)
    
def main():

    ldir = None
    notice_only = False
    discard = False
    config = None
    timex = None
    
    #get options arguments
    try:
      opts, args = getopt.getopt(sys.argv[1:],'hl:dtn',['help','log-dir=','download-and-discard','timeout','no-download'])
    except getopt.GetoptError as err:    
      print("Error 1: %s" %err)
      print("Try `dd_subscribe --help' for more information.")
      sys.exit(2)                    
    
    #validate options
    if opts == [] and args == []:
      help()  
      sys.exit(1)
    for o, a in opts:
      if o in ('-h','--help'):
        help()
        sys.exit(1)
      elif o in ('-n','--no-download'):
        notice_only = True        
      elif o in ('-l','--log-dir'):
        ldir = a       
        if not os.path.exists(ldir) :
          print("Error 2: specified logging directory does not exist.")
          print("Try `dd_subscribe --help' for more information.")
          sys.exit(2)
      elif o in ('-d','--download-and-discard'):
        discard = True        
        
    #validate arguments
    if len(args) == 1:
      config = args[0]
      if not os.path.exists(config) :
         print("Error 3: configuration file does not exist.")
         sys.exit(2)
    elif len(args) == 0:
      help()  
      sys.exit(1)
    else:      
      print("Error 4: too many arguments given: %s." %' '.join(args))
      print("Try `dd_subscribe --help' for more information.")
      sys.exit(2)            
             
    # logging to stdout
    LOG_FORMAT = ('%(asctime)s [%(levelname)s] %(message)s')

    if ldir == None :
       LOGGER = logging.getLogger(__name__)
       logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    # user wants to logging in a directory/file
    else :       
       fn     = config.replace(".conf","")
       lfn    = fn + "_%s" % os.getpid() + ".log"
       lfile  = ldir + os.sep + lfn

       # Standard error is redirected in the log
       sys.stderr = open(lfile, 'a')

       # python logging
       LOGGER = None
       fmt    = logging.Formatter( LOG_FORMAT )
       hdlr   = logging.handlers.TimedRotatingFileHandler(lfile, when='midnight', interval=1, backupCount=5) 
       hdlr.setFormatter(fmt)
       LOGGER = logging.getLogger(lfn)
       LOGGER.setLevel(logging.INFO)
       LOGGER.addHandler(hdlr)

    # instanciate consumer

    consumer = ConsumerX(config,LOGGER)
    consumer.notify_only = notice_only
    consumer.discard = discard
    consumer.timex = timex
    
    consumer.run()
    """
    while True:
         try:
                consumer.run()
         except :
                (type, value, tb) = sys.exc_info()
                LOGGER.error("Type: %s, Value: %s,  ..." % (type, value))
                time.sleep(10)
                pass
                
    """
    consumer.close()


if __name__ == '__main__':
    verify_version()
    signal.signal(signal.SIGINT, signal_handler)
    main()

