"""

   An example of consuming data made available by a Sarracenia Data Pump.

"""
import sarracenia.moth
import sarracenia.moth.amqp
import sarracenia.credentials

import time
import socket

options = sarracenia.moth.default_options
options.update(sarracenia.moth.amqp.default_options)

options['broker'] = sarracenia.credentials.Credential(
    'amqps://anonymous:anonymous@hpfx.collab.science.gc.ca')

# binding tuple:  consists of prefix, exchange, rest.
# effect is to bind from queue using prefix/rest to exchange.
options['topicPrefix'] = ['v02', 'post']
options['bindings'] = [('xpublic', ['v02', 'post'], ['#'])]

# turn on debug output for these classes.
#options['settings'] = { 'sarracenia.moth.mqtt.MQTT': { 'logLevel':'debug' }}
#options['settings'] = { 'sarracenia.moth.amqp.AMQP': { 'logLevel':'debug' }}

# Note: queue name must start with q_<username> because server is configured to deny anything else.
#
options['queueName'] = 'q_anonymous_' + socket.getfqdn(
) + '_SomethingHelpfulToYou'

print('options: %s' % options)

h = sarracenia.moth.Moth.subFactory(options)

count = 0
while count < 5:
    m = h.getNewMessage()
    if m is not None:
        print("message: %s" % m)
        #content = m.getContent()
        #print("corresponding file: %s" % content)
        h.ack(m)
    time.sleep(0.1)
    count += 1

print(' got %d messages' % count)
h.cleanup()
h.close()
exit(count)
