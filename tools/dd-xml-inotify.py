#!/usr/bin/python

import os, socket, stat, sys, time
import amqplib.client_0_8 as amqp

import asyncore
import pyinotify

if sys.version[:3] >= '2.6':
    import hashlib
    md5sum = hashlib.md5
else:
    import md5
    md5sum = md5.new

# credential from args

USER = sys.argv[1]
PASSWORD = sys.argv[2]

# getting hostname

HOST = socket.gethostname() + '.cmc.ec.gc.ca'

# setting url according to host

URLS = {}
URLS['wxod-b5.cmc.ec.gc.ca'] = 'http://dd.wxod-dev.cmc.ec.gc.ca/'
URLS['wxos-b4.cmc.ec.gc.ca'] = 'http://dd2.wxod-stage.cmc.ec.gc.ca/'
URLS['wxos-b3.cmc.ec.gc.ca'] = 'http://dd1.wxod-stage.cmc.ec.gc.ca/'
URLS['wxo-b3.cmc.ec.gc.ca'] = 'http://dd3.weather.gc.ca/'
URLS['wxo-b2.cmc.ec.gc.ca'] = 'http://dd2.weather.gc.ca/'
URLS['wxo-b1.cmc.ec.gc.ca'] = 'http://dd1.weather.gc.ca/'

clusters = {}
clusters['wxod-b5.cmc.ec.gc.ca'] = 'dd.wxod-dev.cmc.ec.gc.ca'
clusters['wxos-b4.cmc.ec.gc.ca'] = 'dd.wxod-stage.cmc.ec.gc.ca'
clusters['wxos-b3.cmc.ec.gc.ca'] = 'dd.wxod-stage.cmc.ec.gc.ca'
clusters['wxo-b3.cmc.ec.gc.ca'] = 'dd.weather.gc.ca'
clusters['wxo-b2.cmc.ec.gc.ca'] = 'dd.weather.gc.ca'
clusters['wxo-b1.cmc.ec.gc.ca'] = 'dd.weather.gc.ca'

URL = URLS[HOST]
cluster = clusters[HOST]

# source  and  urldir

SRC = {}
SRC['/data/wxofeed/cmc/cache/xml/public/site'] = URL + 'citypage_weather/xml'
SRC['/data/wxofeed/cmc/cache/xml/public/marine'] = URL + 'marine_weather/xml'

# ===================================
# declare AMQP publisher
# ===================================


class Publisher:
    def __init__(self, host):

        self.connected = False

        self.connection = None
        self.channel = None
        self.ssl = False

        self.host = host
        self.user = USER
        self.passwd = PASSWORD

        self.realm = '/data'
        self.exchange_name = 'xpublic'
        self.exchange_type = 'topic'
        self.exchange_key = None

        self.cluster = cluster

        self.connect()

    def close(self):
        try:
            self.channel.close()
        except:
            pass
        try:
            self.connection.close()
        except:
            pass
        self.connected = False

    def connect(self):

        self.connection = None
        self.channel = None

        while True:
            try:
                # connect
                self.connection = amqp.Connection(self.host,
                                                  userid=self.user,
                                                  password=self.passwd,
                                                  ssl=self.ssl)
                self.channel = self.connection.channel()

                # what kind of exchange
                self.channel.access_request(self.realm,
                                            active=True,
                                            write=True)
                self.channel.exchange_declare(self.exchange_name,
                                              self.exchange_type,
                                              auto_delete=False)

                self.connected = True
                print("AMQP Sender is now connected to: %s" % str(self.host))
                break
            except:
                (type, value, tb) = sys.exc_info()
                print("AMQP Sender cannot connected to: %s" % str(self.host))
                print("Type: %s, Value: %s, Sleeping 5 seconds ..." %
                      (type, value))
                time.sleep(5)

    def reconnect(self):
        self.close()
        self.connect()

    def old_publish(self, message, exchange_key, filename):
        try:
            hdr = {'filename': filename}
            msg = amqp.Message(message,
                               content_type='text/plain',
                               application_headers=hdr)
            self.channel.basic_publish(msg, self.exchange_name, exchange_key)
            print("Key %s Message %s " % (exchange_key, message))
        except:
            (type, value, tb) = sys.exc_info()
            print("AMQP cound not publish...reconnecting")
            print("Type: %s, Value: %s, Sleeping 5 seconds ..." %
                  (type, value))
            time.sleep(5)
            self.reconnect()
            self.old_publish(message, exchange_key, filename)

    def publish(self, parts, message, exchange_key, filename):
        import amqplib.client_0_8 as amqp
        try:
            msec = '.%d' % (int(round(time.time() * 1000)) % 1000)
            now = time.strftime("%Y%m%d%H%M%S", time.gmtime()) + msec
            v02_msg = "%s %s %s" % (now, parts[-2], parts[-1])

            filesize = parts[1]
            partstr = '1,%s,1,0,0' % filesize

            checksum = parts[0]
            sumstr = 'd,%s' % checksum

            hdr = {}
            hdr['source'] = 'dd-xml-inotify'
            hdr['parts'] = partstr
            hdr['sum'] = sumstr
            hdr['from_cluster'] = self.cluster

            # filename is added for backward compatibility
            hdr['filename'] = os.path.basename(filename)

            print("\nkey    = %s" % exchange_key)
            print("notice = %s" % v02_msg)
            print("header = %s" % hdr)

            msg = amqp.Message(v02_msg,
                               content_type='text/plain',
                               application_headers=hdr)
            self.channel.basic_publish(msg, self.exchange_name, exchange_key)
        except:
            (type, value, tb) = sys.exc_info()
            print("AMQP cound not publish...reconnecting")
            print("Type: %s, Value: %s, Sleeping 5 seconds ..." %
                  (type, value))
            time.sleep(5)
            self.reconnect()
            self.publish(parts, message, exchange_key, filename)


# =========================================
# Create one instanciation and publish urls
# =========================================

publisher = Publisher(HOST)

# =========================================
# setup the async inotifier
# =========================================


class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        for spath in SRC:
            if not spath in event.pathname: continue
            if event.pathname[-4:] == '.tmp': continue

            filepath = event.pathname
            f = open(filepath, 'rb')
            data = f.read()
            f.close()
            checksum = md5sum(data).hexdigest()

            lstat = os.stat(filepath)
            fsiz = lstat[stat.ST_SIZE]
            ssiz = "%d" % fsiz

            url = event.pathname.replace(spath, SRC[spath])
            parts = url.split('/')
            msg = checksum + ' ' + ssiz + ' ' + '/'.join(
                parts[:3]) + '/ ' + '/'.join(parts[3:])

            filename = 'msg_' + parts[-1] + ':WXO:LOCAL:FILE:XML'
            key_final = '.'.join(parts[3:])

            token = msg.split()
            exchange_key = 'v02.post.' + key_final
            publisher.publish(token, msg, exchange_key, filename)

            # publish old message and exchange_key

            exchange_key = 'exp.dd.notify.' + key_final
            publisher.old_publish(url, exchange_key, filename)

            # publish old message and exchange_key

            exchange_key = 'v00.dd.notify.' + key_final
            publisher.old_publish(msg, exchange_key, filename)


# start inotify engine

wm = pyinotify.WatchManager()
notifier = pyinotify.AsyncNotifier(wm, EventHandler())

# =========================================
# setup the watch of the sources
# =========================================

# read in the directory

for spath in SRC:

    entries = os.listdir(spath)
    wdd = wm.add_watch(spath, pyinotify.IN_CLOSE_WRITE, rec=True)
    print( "watching = " + spath)

    for d in entries:
        currentDir = spath + '/' + d
        if os.path.isfile(currentDir): continue
        wdd = wm.add_watch(currentDir, pyinotify.IN_CLOSE_WRITE, rec=True)
        print( "watching = " + currentDir)

# start event loop
asyncore.loop()

# close publisher (if we ever get here)
publisher.close()
