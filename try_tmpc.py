

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

import logging
import time
import sys

import appdirs
from sarra.sr_cfg2 import one_config

from urllib.parse import urlparse,urlunparse

l = TestLogger()
logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG)
logger.setLevel( logging.DEBUG )

print( 'ihpc default properties: %s' % TMPC.default_props() )
print( 'amqp default properties: %s' % AMQP.default_props() )

cfg=one_config( "sarra", "download_f20.conf", logger, TMPC.default_props() )

#cfg.dump()


#print( "in the end: %s" % cfg.__dict__ )

cd=cfg.dictify()

for k in sorted(cd):
   if k not in [ 'env' ]:
       print('setting: {} = {} '.format( k, cd[k] ) )

print('hoho... have a config... broker: %s ' % urlunparse(cfg.broker) )


h=TMPC( cfg.broker, logger, cd)
print( "This one is an: %s" % h.url_proto() )
#h=tmpc.TMPC( "amqp://localhost", { 'Queue':'try_tmpc'  } , l )

i=0
while i < 10:
    m = h.getNewMessage()
    if m is not None:
        print( "message: %s" % m )
        print( "message body: %s" % m.body )
    time.sleep(1)
    i += 1
