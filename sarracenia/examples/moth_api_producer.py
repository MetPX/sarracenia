"""
    Example of posting data to a Sarracenia Data Pump.

"""
import sarracenia.moth
import sarracenia
import sarracenia.credentials
from sarracenia.config import default_config

import os
import time
import socket
import sys

"""
  supply broker argument as a command line argument.

"""
if len(sys.argv) > 1:
    broker = sys.argv[1]
else:
    broker = 'amqp://tfeed:HungryCat@localhost'

cfg = default_config()
#cfg.logLevel = 'debug'
cfg.broker = sarracenia.credentials.Credential( broker )
cfg.exchange = 'xsarra'
cfg.post_baseUrl = 'http://host'
cfg.post_baseDir = '/tmp'
cfg.topicPrefix = [ 'v03', 'post' ]
cfg.logLevel = 'debug'

print('cfg: %s' % cfg)

# moth wants a dict as options, rather than sarracenia.config.Config instance.
posting_engine = sarracenia.moth.Moth.pubFactory(cfg.dictify())

sample_fileName = '/tmp/sample.txt'
sample_file = open(sample_fileName, 'w')
sample_file.write("""
CACN00 CWAO 161800
PMN
160,2021,228,1800,1065,100,-6999,20.49,43.63,16.87,16.64,323.5,9.32,27.31,1740,317.8,19.22,1.609,230.7,230.7,230.7,230.7,0,0,0,16.38,15.59,305.
9,17.8,16.38,19.35,55.66,15.23,14.59,304,16.67,3.844,20.51,18.16,0,0,-6999,-6999,-6999,-6999,-6999,-6999,-6999,-6999,0,0,0,0,0,0,0,0,0,0,0,0,0,
13.41,13.85,27.07,3473
""")
sample_file.close()

# you can supply msg_init with your files, it will build a message appropriate for it.
m = sarracenia.Message.fromFileData(sample_fileName, cfg, sarracenia.stat(sample_fileName))

# here is the resulting message.
print(m)

# feed the message to the posting engine.
posting_engine.putNewMessage(m)

# when done, should close... cleaner...
posting_engine.close()
