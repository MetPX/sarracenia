
# usage: mqtt_file_publish.py  file1 file2 file4 ...

# assuming there is a web server running on *broker_host*
# post messages 
#

broker_host = 'localhost'
post_base_url = 'http://localhost/wmo_mesh'
post_base_dir = os.getcwd() + '/wmo_mesh'
import paho.mqtt.client as mqtt

import os
import json
import sys

import time

from hashlib import md5

client = mqtt.Client()


client.connect( broker_host )

exchange='/xpublic'
topic_prefix='/v03/post'

for fn in sys.argv[1:]:
    os.stat( fn )
    
    f = open(fn,'rb')
    d = f.read()
    f.close()
     
    hash = md5()
    hash.update(d)
    
    now=time.time()
    nsec = ('%.9g' % (now%1))[1:]
    datestamp  = time.strftime("%Y%m%d%H%M%S",time.gmtime(now)) + nsec
      
    relpath = os.path.abspath(fn).replace( post_base_dir, '' )
    
    p = json.dumps( (datestamp, post_base_url, relpath, { "sum":"d,"+hash.hexdigest() } )) 
    
    t = exchange + topic_prefix + os.path.dirname(relpath)
    
    print( "topic=%s , payload=%s" % ( t, p ) )
    client.publish(topic=t, payload=p, qos=2 )
    
    client.disconnect()
