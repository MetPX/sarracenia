#!/usr/bin/env python3

# trivial Sarracenia/MQTT client.
#    just a demo.
#
# AMQP -> mqtt mappings.
#
# note: MQTT leading slash should be avoided.

# exchange   -> root of the topic tree.
#    vaguely maps to a device, or source in MQTT.
#    topic_prefix -> next two elements of topic tree.
#  obviously:  topic separator . -> /,  # is the same, * --> +  (single topic wildcard)
#
# queue_name ->  client_id
#
# subtopic -> results in bindings -> topic arguments to subscribe.
#

import paho.mqtt.client as mqtt
import os, os.path
import urllib.request
import json

rcs = [
    "Connection successful", "Connection refused – incorrect protocol version",
    "Connection refused – invalid client identifier",
    "Connection refused – server unavailable",
    "Connection refused – bad username or passwor",
    "Connection refused – not authorised", "unknown error"
]


def on_connect(client, userdata, flags, rc):

    if (rc >= 6): rc = 6
    print("Connection result code: " + rcs[rc])

    client.subscribe("xpublic/#")


id = 0


def on_message(client, userdata, msg):
    global id
    id = id + 1
    m = json.loads(msg.payload.decode("utf-8"))
    print("     id: ", id)
    print("  topic: ", msg.topic)
    print("payload: ", m)

    # from sr_postv3.7.rst:   [ m[0]=<datestamp> m[1]=<baseurl> m[2]=<relpath> m[3]=<headers> ]

    d = os.path.dirname(m[2])[1:]
    url = m[1] + m[2]
    fname = os.path.basename(m[2])

    if not os.path.isdir(d):
        os.makedirs(d)

    p = d + '/' + fname
    print("writing: ", p)
    urllib.request.urlretrieve(url, p)


client = mqtt.Client(clean_session=False,
                     client_id='my_queue_name',
                     protocol=mqtt.MQTTv311)

client.on_connect = on_connect
client.on_message = on_message

print('about to connect')
#client.username_pw_set( 'guest', 'guestpw' )
client.connect('localhost')
print('done connect')

client.loop_forever()
