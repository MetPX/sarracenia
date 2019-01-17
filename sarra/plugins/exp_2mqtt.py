#!/usr/bin/python3
"""

exp_2mqtt  - posts messages to an MQTT broker as they are received (like sr_shovel)

STATUS: Experimental (may change at any upgrade, do not use if stability is desired.)
        This is just for exploration of interop with MQTT brokers. NOT FOR PRODUCTION!
        NO TESTING so far.

        messages are posted in v03 format, because v02 format is incompatible with
        MQTT 3.11  (requires at least v5, which isn't common yet.)

        tested with EMQ so far, authenticated to post, subscribe anonymous
        see after code for details.

This plugin posts messages to an MQTT broker as they are received (like sr_shovel)

requires:
   paho-mqtt library.
   (>= 1.3 either via pip, or python3-paho-mqtt)

for use with sr_subscribe.

<options are placed before do_download in the configuration>

no_download
post_exchange 

plugin exp_2mqtt

Options:
    exp_2mqtt_post_broker - URL to look up in credentials.conf for broker connection.


"""

import paho.mqtt.client as mqtt


class EXP_2MQTT(object): 

   import urllib.parse

   def __init__(self,parent):

      parent.declare_option( 'exp_2mqtt_post_broker' )


   def on_start(self,parent):

      import paho.mqtt.client as mqtt

      if not hasattr(parent,'exp_2mqtt_post_broker'):
         parent.exp_2mqtt_post_broker= [ 'mqtt://localhost' ]
 
      logger=parent.logger

      ok, details = parent.credentials.get(parent.exp_2mqtt_post_broker[0])
      if ok:
           parent.mqtt_bs = details
      else:
           logger.error( "exp_2mqtt: post_broker credential lookup failed for %s" % parent.exp_2mqtt_post_broker )

      if not hasattr(parent, 'post_exchange'):
         logger.error("exp_2mqtt: defaulting post_exchange to xpublic")
         parent.post_exchange='xpublic'
         
      u = parent.mqtt_bs.url
      if u.port == None:
            port = 1883
      else:
            port = u.port

      parent.mqtt_client = mqtt.Client()

      if u.username != None:
          logger.error("exp_2mqtt: authenticating as %s " % (u.username) )
          parent.mqtt_client.username_pw_set( u.username, u.password )

      parent.mqtt_client.connect( u.hostname, port )
      return True

   def on_message(self,parent):

      import os.path,json

      import paho.mqtt.client as mqtt

      logger = parent.logger
      msg    = parent.msg

      mqtt_topic = parent.post_exchange + '/v03/post' + os.path.dirname(parent.msg.relpath)
      body = json.dumps( (msg.pubtime, msg.baseurl, msg.relpath, msg.headers) )
      logger.info("exp_2mqtt publising topic=%s, body=%s" % ( mqtt_topic, body ))
      parent.mqtt_client.publish(mqtt_topic,body)

      return True


self.plugin='EXP_2MQTT'


"""
  {allow, all, subscribe, "xpublic/#" }
  {allow, {user, "tsource"}, publish, [ "xpublic/#" ] }.

  ...

  {deny, all}.

"""
