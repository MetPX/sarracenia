#!/usr/bin/python

# usage :
#
# ./radar_XFT_messages.py

# This code was created using a sample given with python-amqplib
# It is only checking onto messages for a specific radar
# It creates an auto-delete queue... so nothing is kept between
# different sessions

import amqplib.client_0_8 as amqp
import os, sys, time

print("RADARS are every 10 MINS... ")
print("It may take that time to have something shown")

machine = "amqp.weather.gc.ca"
#machine       = "dd.weather.gc.ca"
#machine       = sys.argv[1]
user = "anonymous"
passwd = "anonymous"

exchange_realm = "/data"
exchange_name = "xpublic"
exchange_type = "topic"

# getting notifications for the GIF of the XFT radar
exchange_key = "v00.dd.notify.radar.PRECIP.GIF.XFT.#"

# connection
connection = amqp.Connection(machine, userid=user, password=passwd, ssl=False)
channel = connection.channel()

# exchange
channel.access_request(exchange_realm, active=True, read=True)
channel.exchange_declare(exchange_name, exchange_type, auto_delete=False)

# queue
_queuename, message_count, consumer_count = channel.queue_declare()
channel.queue_bind(_queuename, exchange_name, exchange_key)

# amqp callback


def amqp_callback(msg):

    hdr = msg.properties['application_headers']
    filename = hdr['filename']

    msg.channel.basic_ack(msg.delivery_tag)

    # Cancel this callback
    if msg.body == 'quit':
        msg.channel.basic_cancel(msg.consumer_tag)

        self.msg = None
        self.logger.error('CRITICAL ERROR...')
        self.logger.error('Requiered to quit the connection')
        sys.exit(1)

    # send url to user callback
    user_callback(msg.body)


###################################
# user callback
###################################


def user_callback(url):
    t = time.strftime("%Y%m%d %H:%M:%S", time.gmtime())
    print("%s %s" % (t, url))


# amqp callback activation

channel.basic_consume(_queuename, callback=amqp_callback)

# Wait for things to arrive on the queue

while True:
    try:
        channel.wait()
    except:
        channel.close()
        connection.close()
        sys.exit(1)

# close connections

channel.close()
connection.close()
