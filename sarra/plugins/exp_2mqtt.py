#!/usr/bin/python3
"""

exp_2mqtt  - posts messages to an MQTT broker as they are received (like sr_shovel)

STATUS: Experimental (may change at any upgrade, do not use if stability is desired.)
        This is just for exploration of interop with MQTT brokers. NOT FOR PRODUCTION!
        NO TESTING so far.

        posts received and processed must be v02 format.

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
                            can be specified more than once, and instances will use
                            one from the resulting list.  
    
"""

import paho.mqtt.client as mqtt


class EXP_2MQTT(object): 

   import urllib.parse

   def __init__(self,parent):

      parent.declare_option( 'exp_2mqtt_post_broker' )


   def on_start(self,parent):

      import paho.mqtt.client as mqtt
      import time

      if not hasattr(parent,'exp_2mqtt_post_broker'):
         parent.exp_2mqtt_post_broker= [ 'mqtt://localhost' ]
 
      logger=parent.logger

      if parent.no < 1: # randomize broker used in foreground testing.
         i = int( time.time() % len(parent.exp_2mqtt_post_broker) )
      else:
         i = (parent.no-1) % len(parent.exp_2mqtt_post_broker)

      logger.info( "using: %s parent.no=%d exp_2mqtt_broker=%s" % \
           (parent.exp_2mqtt_post_broker[i], parent.no, parent.exp_2mqtt_post_broker) )

      ok, details = parent.credentials.get(parent.exp_2mqtt_post_broker[i])
      if ok:
           parent.mqtt_bs = details
      else:
           logger.error( "exp_2mqtt: post_broker credential lookup failed for %s" % parent.exp_2mqtt_post_broker )
           return

      if not hasattr(parent, 'post_exchange'):
         logger.error("exp_2mqtt: defaulting post_exchange to xpublic")
         parent.post_exchange='xpublic'
         
      u = parent.mqtt_bs.url
      if u.port == None:
            port = 1883
      else:
            port = u.port

      # https://www.iso.org/standard/69466.html - ISO standard v3.1.1 is most common.
      parent.mqtt_client = mqtt.Client( protocol=mqtt.MQTTv311 )

      if u.username != None:
          logger.error("exp_2mqtt: authenticating as %s " % (u.username) )
          parent.mqtt_client.username_pw_set( u.username, u.password )

      parent.mqtt_client.connect( u.hostname, port )
      parent.mqtt_client.loop_start()
      return True

   def on_message(self,parent):

      import os.path,json
      from sarra.sr_util import timev2tov3str
      import paho.mqtt.client as mqtt
      from codecs import decode,encode

      logger = parent.logger
      msg    = parent.msg

      mqtt_topic = parent.post_exchange + '/v03/post' + os.path.dirname(parent.msg.relpath)

      if parent.topic_prefix == 'v02' :
          msg.headers[ "pubTime" ] = timev2tov3str( msg.pubtime )
          msg.headers[ "atime" ] = timev2tov3str( msg.headers[ "atime" ] )
          msg.headers[ "mtime" ] = timev2tov3str( msg.headers[ "mtime" ] )
          msg.headers[ "baseUrl" ] = msg.baseurl
          msg.headers[ "relPath" ] = msg.relpath
      
          sum_algo_map = { "d":"md5", "s":"sha512", "n":"md5name", "0":"zero" }
          sm = sum_algo_map[ msg.headers["sum"][0] ]
          sv = encode( decode( msg.headers["sum"][2:], 'hex'), 'base64' ).decode('utf-8').strip()
          msg.headers[ "integrity" ] = { "method": sm, "value": sv }
          del msg.headers[ "sum" ]
          body = json.dumps( msg.headers )
      else:
          # in v03, no translation required.
          body = parent.consumer.raw_msg.body

      logger.info("exp_2mqtt publishing topic=%s, lag=%g body=%s" % ( mqtt_topic, msg.get_elapse(), body ))
      info = parent.mqtt_client.publish(mqtt_topic,body,qos=1)
      info.wait_for_publish()
      return True


self.plugin='EXP_2MQTT'


"""
  {allow, all, subscribe, "xpublic/#" }
  {allow, {user, "tsource"}, publish, [ "xpublic/#" ] }.

  ...

  {deny, all}.

"""
