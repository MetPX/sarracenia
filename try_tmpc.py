

class TestLogger:
    def silence(self,str):
        pass

    def __init__(self):
        self.debug   = print
        self.info    = print
        self.warning = print
        self.error   = print

from sarra.tmpc import TMPC
from sarra.tmpc.amqp import AMQP
import copy
import logging
import time
import sys

import appdirs
from sarra.config import one_config

from urllib.parse import urlparse,urlunparse

l = TestLogger()
logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG)
logger.setLevel( logging.DEBUG )

print( 'ihpc default properties: %s' % TMPC.default_props() )
print( 'amqp default properties: %s' % AMQP.default_props() )

cfg=one_config( "sarra", "download_f20.conf", TMPC.default_props() )

#cfg.dump()


#print( "in the end: %s" % cfg.__dict__ )

cd=cfg.dictify()

for k in sorted(cd):
   if k not in [ 'env' ]:
       print('setting: {} = {} '.format( k, cd[k] ) )

print('hoho... have a config... broker: %s ' % urlunparse(cfg.broker) )


h=TMPC( cfg.broker, cd)
print( "This one is an: %s" % h.url_proto() )

i=0
while i < 5:
    m = h.getNewMessage()
    if m is not None:
        print( "message: %s" % m )
        print( "message body: %s" % m )
    time.sleep(0.1)
    i += 1

h.close()

body = { 
    "to_clusters": "localhost", "mtime": "20200219T052341.602167606",
    "atime": "20200503T193742.142436504", "mode": "644", 
    "pubTime": "20200504T010014.301291943", 
    "baseUrl": "http://localhost:8090", 
    "relPath": "/20200105/WXO-DD/meteocode/atl/csv/2020-01-05T03-00-01Z_FPHX14_r20zf_WG.csv", 
    "integrity": { 
          "method": "sha512", 
          "value": "bu9QBxNCqIJ+of4He6G5eTAIYptTlHRK6Hp1G3ILeg5+U2lu8Y9S4JXmiuTsxUCgvGrERculuzN4\n49q7cb1wJg=="
    }, 
    "size": 410,
    'topic': 'v03.post.20200105.WXO-DD.meteocode.atl'
} 

#modify config for posting...
pd=copy.deepcopy(cd)
for k in cd.keys():
     if k.startswith('post_'):
        pd[k[5:]] = pd[k]

p=TMPC( cfg.post_broker, pd, is_subscriber=False)

p.putNewMessage( 
body )


