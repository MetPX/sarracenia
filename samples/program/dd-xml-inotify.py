#!/usr/bin/python

import os, socket, stat, sys, time
import amqplib.client_0_8 as amqp

import asyncore 
import pyinotify 


# credential from args

USER     = sys.argv[1]
PASSWORD = sys.argv[2]

# getting hostname

HOST=socket.gethostname()+'.cmc.ec.gc.ca'

# setting url according to host

URLS = {}
URLS['wxod-b5.cmc.ec.gc.ca'] = 'http://dd.wxod-dev.cmc.ec.gc.ca/'
URLS['wxos-b4.cmc.ec.gc.ca'] = 'http://dd2.wxod-stage.cmc.ec.gc.ca/'
URLS['wxos-b3.cmc.ec.gc.ca'] = 'http://dd1.wxod-stage.cmc.ec.gc.ca/'
URLS['wxo-b3.cmc.ec.gc.ca' ] = 'http://dd3.weather.gc.ca/'
URLS['wxo-b2.cmc.ec.gc.ca' ] = 'http://dd2.weather.gc.ca/'
URLS['wxo-b1.cmc.ec.gc.ca' ] = 'http://dd1.weather.gc.ca/'

URL = URLS[HOST]

# source  and  urldir

SRC = {}
SRC['/data/wxofeed/cmc/cache/xml/public/site'  ] = URL + 'citypage_weather/xml'
SRC['/data/wxofeed/cmc/cache/xml/public/marine'] = URL + 'marine_weather/xml'


# ===================================
# declare AMQP publisher
# ===================================

class Publisher: 
   
   def __init__(self, host ):
      self.connection = None                          # The connection
      self.ssl        = False

      self.host       = host
      self.user       = USER
      self.passwd     = PASSWORD

      self.realm         = '/data'
      self.exchange_name = 'xpublic'
      self.exchange_type = 'topic'

      self._connect()

   def close(self):
       try:
              self.channel.close()
              self.connection.close()
       except:
              (type, value, tb) = sys.exc_info()
              print("Problem in closing socket! Type: %s, Value: %s" % (type, value))

   def _connect(self):

      self.connection = None
      self.channel    = None

      while True:
         try:
              # connect
              self.connection = amqp.Connection(self.host, userid=self.user, password=self.passwd, ssl=self.ssl)
              self.channel    = self.connection.channel()

              # what kind of exchange
              self.channel.access_request(self.realm, active=True, write=True)
              self.channel.exchange_declare(self.exchange_name, self.exchange_type, auto_delete=False)

              print("AMQP Sender is now connected to: %s" % str(self.host))
              break
         except:
              (type, value, tb) = sys.exc_info()
              print("AMQP Sender cannot connected to: %s" % str(self.host))
              print("Type: %s, Value: %s, Sleeping 5 seconds ..." % (type, value))
              time.sleep(5)


   def publish_url(self, url):

       # build exchange_key

       parts = url.split('/')
       exchange_key = 'exp.dd.notify.' + '.'.join(parts[3:])
       print("exchange_key %s created" % exchange_key)

       # build filename

       filename = '.'.join(parts[3:-1]) + '++'+ parts[-1] + ':WXO:LOCAL:FILE:XML'

       # publish message

       hdr = {'filename': filename }
       msg = amqp.Message(url, content_type= 'text/plain',application_headers=hdr)

       self.channel.basic_publish(msg, self.exchange_name, exchange_key )

       print("Message %s  delivered" % url )


   def publish_safe(self, url):

       try:
               self.publish_url(url)
       except:
               (type, value, tb) = sys.exc_info()
               print("Error publishing %s ! Type: %s, Value: %s" % (url,type, value))
               self.reconnect()
               self.publish_url(url)
            
   def reconnect(self):

       # We close the connection
       try:
                self.channel.close()
                self.connection.close()
       except:
                (type, value, tb) = sys.exc_info()
                print("Problem in closing socket! Type: %s, Value: %s" % (type, value))

       # We try to reconnect. 
       self._connect()

# =========================================
# Create one instanciation and publish urls
# =========================================

publisher = Publisher(HOST)

# =========================================
# setup the async inotifier
# =========================================

class EventHandler(pyinotify.ProcessEvent):
  def process_IN_CLOSE_WRITE(self,event):
      for spath in SRC :
          if not spath in event.pathname : continue
          url = event.pathname.replace(spath,SRC[spath])
      publisher.publish_safe(url)

# start inotify engine

wm  = pyinotify.WatchManager()
notifier = pyinotify.AsyncNotifier(wm,EventHandler())

# =========================================
# setup the watch of the sources
# =========================================

# read in the directory

for spath in SRC :

    entries = os.listdir(spath)
    wdd     = wm.add_watch(spath, pyinotify.IN_CLOSE_WRITE, rec=True)
    print "watching = " + spath

    for d in entries :
        currentDir = spath + '/' + d
        if os.path.isfile(currentDir) : continue
        wdd = wm.add_watch(currentDir, pyinotify.IN_CLOSE_WRITE, rec=True)
        print "watching = " + currentDir

# start event loop
asyncore.loop()

# close publisher (if we ever get here)
publisher.close()
