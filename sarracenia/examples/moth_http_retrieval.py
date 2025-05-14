"""
    Example of consuming data from a Sarracenia Data Pump.

"""
import sarracenia.moth
import sarracenia.moth.amqp
import sarracenia.config.credentials
import sarracenia.config.subscription

import time
import socket
import urllib.request
import xml.etree.ElementTree as ET

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
   'bindings': [ { 'exchange':'xpublic', 'prefix': ['v02','post'], 'sub':['*','WXO-DD','observations','swob-ml','#'] } ],
   'queue' : queue
      } ] )

options['subscription_index'] = 0

# turn on debug output for these classes.
#options['settings'] = {}
#options['settings']['sarracenia.moth.mqtt.MQTT'] = { 'logLevel':'debug' }
#options['settings']['sarracenia.moth.amqp.AMQP'] = { 'logLevel':'debug' }

options['logLevel'] = 'debug'


#print('options: %s' % options)

h = sarracenia.moth.Moth.subFactory(options)

count = 0

while count < 10:
    messages = h.newMessages()
    for m in messages:
        dataUrl = m['baseUrl']
        if 'retreivePath' in m:
            dataUrl += m['retreivePath']
        else:
            dataUrl += m['relPath']

        print("url %d: %s" % (count, dataUrl))
        with urllib.request.urlopen(dataUrl) as f:
            vxml = f.read().decode('utf-8')
            xmlData = ET.fromstring(vxml)

            stn_name = ''
            tc_id = ''
            lat = ''
            lon = ''
            air_temp = ''

            for i in xmlData.iter():
                name = i.get('name')
                if name == 'stn_nam':
                    stn_name = i.get('value')
                elif name == 'tc_id':
                    tc_id = i.get('value')
                elif name == 'lat':
                    lat = i.get('value')
                elif name == 'long':
                    lon = i.get('value')
                elif name == 'air_temp':
                    air_temp = i.get('value')

            print('station: %s, tc_id: %s, lat: %s, long: %s, air_temp: %s' %
                  (stn_name, tc_id, lat, lon, air_temp))
        h.ack(m)
        count += 1
        if count > 10:
            break
    time.sleep(1)

h.cleanup()  # remove server-side queue defined by Factory.
h.close()
print("obtained 10 product announcements")
