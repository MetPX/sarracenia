import sarracenia.moth
import sarracenia.moth.amqp

import time
import socket
from urllib.parse import urlparse, urlunparse

options = sarracenia.moth.default_options
options.update(sarracenia.moth.amqp.default_options)

broker = urlparse('amqps://anonymous:anonymous@hpfx.collab.science.gc.ca')
options['broker'] = broker

# binding tuple:  consists of prefix, exchange, rest.
# effect is to bind from queue using prefix/rest to exchange.
options['bindings'] = [('v02.post', 'xpublic', '#')]

# Note: queue name must start with q_<username> because server is configured to deny anything else.
#
options['queue_name'] = 'q_anonymous_' + socket.getfqdn(
) + '_SomethingHelpfulToYou'

options['debug'] = True

print('options: %s' % options)

h = sarracenia.moth.Moth.subFactory(broker, options)

while True:
    m = h.getNewMessage()
    if m is not None:
        print("message: %s" % m)
        h.ack(m)
    time.sleep(0.1)

h.close()
