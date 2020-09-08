import sarra.moth
import sarra.moth.amqp

import time
import socket
from urllib.parse import urlparse, urlunparse

options = sarra.moth.default_options
options.update(sarra.moth.amqp.default_options)

broker = urlparse('amqps://anonymous:anonymous@hpfx.collab.science.gc.ca')
options['broker'] = broker

# binding tuple:  consists of prefix, exchange, rest.
# effect is to bind from queue using prefix/rest to exchange.
options['bindings'] = [('v02.post', 'xpublic', '#')]

# Note: queue name must start with q_<username> because server is configured to deny anything else.
#
options['queue_name'] = 'q_anonymous_' + socket.getfqdn(
) + '_SomethingHelpfulToYou'

print('options: %s' % options)

h = sarra.moth.Moth(broker, options)

while True:
    m = h.getNewMessage()
    if m is not None:
        print("message: %s" % m)
        h.ack(m)
    time.sleep(0.1)

h.close()
