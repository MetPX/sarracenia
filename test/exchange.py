#!/usr/bin/python3

import os,sys,time
import urllib,urllib.parse

try :    
         from dd_amqp           import *
         from dd_config         import *
except : 
         from sara.dd_amqp      import *
         from sara.dd_config    import *


broker = urllib.parse.urlparse('amqp://guest:guest@localhost/')

cf = dd_config(args=sys.argv)

hc = HostConnect(cf.logger)
hc.set_url( broker )
hc.connect()

# consumer exchange : make sure it exists
if sys.argv[2] == 'add' :
   ex = Exchange(hc,sys.argv[1])
   ex.build()
if sys.argv[2] == 'del' :
   ch = hc.new_channel()
   ch.exchange_delete(sys.argv[1])

hc.close()
