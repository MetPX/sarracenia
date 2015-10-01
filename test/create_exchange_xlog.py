#!/usr/bin/python3

import os,sys,time
import urllib,urllib.parse

try :    
         from dd_amqp           import *
         from dd_config         import *
except : 
         from sara.dd_amqp      import *
         from sara.dd_config    import *


broker = urllib.parse.urlparse(sys.argv[1])

cf = dd_config(args=sys.argv)

hc = HostConnect(cf.logger)
hc.set_url( broker )
hc.connect()

hc.channel.exchange_declare('xlog', 'topic', passive=False, durable=True,
        auto_delete=False, internal=False, nowait=False)

hc.close()
