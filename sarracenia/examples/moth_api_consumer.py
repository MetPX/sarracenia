"""

   An example of consuming data made available by a Sarracenia Data Pump.

"""
import sarracenia.moth
import sarracenia.moth.amqp
import sarracenia.config.credentials
import sarracenia.config.subscription

import time
import socket

options = sarracenia.moth.default_options()
options.update(sarracenia.moth.amqp.default_options)

options['broker'] = sarracenia.config.credentials.Credential(
    'amqps://anonymous:anonymous@hpfx.collab.science.gc.ca')

# binding tuple:  consists of prefix, exchange, rest.
# effect is to bind from queue using prefix/rest to exchange.
options['queueShare'] = 'SomethingHelpfulToYou'


# Note: queue name must start with q_<username> because server is configured to deny anything else.
#
options['queueName'] = 'q_${BROKER_USER}_${HOSTNAME}_${QUEUESHARE}'

queue = {'name': 'q_anonymous_' + socket.getfqdn() + '_' + options['queueShare'],
         'template': options['queueName'], 
         'auto_delete' : False, # AO == amqp only
         'clean_session': True, # MO == mqtt only.
         'durable': True, # AO: queue should survive broker reboots
         'expire': 600 ,  # MO: seconds until queue with no consumers disappears.
         'max_inflight_messages': 0, # MO: flow control.
         'max_queued_messages': 0,  
         'prefetch': 25, 
         'qos': 1, 
         'receiveMaximum': 0, 
         'tlsRigour': 'normal',
         'bind': True,  # whether to bind queues/subscriptions
         'declare': True # whether to declare queues/subscriptions
       }


options['subscriptions'] = sarracenia.config.subscription.Subscriptions( [ { 
   'broker': options['broker'],
   'bindings': [ { 'exchange':'xpublic', 'topic':'v02.post.#' } ],
   'bindings_to_remove': [],
   'queue' : queue
      } ] )

options['subscription_index'] = 0

# turn on debug output for these classes.
#options['settings'] = {}
#options['settings']['sarracenia.moth.mqtt.MQTT'] = { 'logLevel':'debug' }
#options['settings']['sarracenia.moth.amqp.AMQP'] = { 'logLevel':'debug' }

#options['logLevel'] = 'debug'

print(f'options: {options}')

h = sarracenia.moth.Moth.subFactory(options)

count = 0
while count < 5:
    m = h.getNewMessage()
    if m is not None:
        print(f"message: {m}")
        #content = m.getContent()
        #print("corresponding file: %s" % content)
        h.ack(m)
    time.sleep(0.1)
    count += 1

print(' got %d messages' % count)
h.cleanup()
h.close()
exit(count)
