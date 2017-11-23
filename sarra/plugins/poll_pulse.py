#!/usr/bin/python3

"""
 poll_pulse: a kind of keepalive and client messaging mechanism

 usage:
     in an sr_poll configuration file:

 do_poll poll_pulse.py

 options:

 pulse_message
     a message to be logged to all sarracenia clients on that broker

 The PULSE_MESSAGE environment variable can be set and used 
 just sr_poll <config> restart  after setting it

 The message will be placed in the post message once

 A default message can be set in the config with pulse_message
 Might be usefull if message = 'pulse restarted'

"""

class POLL_SCRIPT(object): 

   def __init__(self,parent):

       parent.declare_option('pulse_message')

       if not hasattr(parent,'pulse_message'):
          parent.pulse_message = None

       # fake destination

       if not hasattr(parent,'destination') or not parent.destination:
          parent.destination = parent.post_broker.geturl()

       self.last_pulse_message = None
          
   def perform(self,parent):
       logger = parent.logger
       msg    = parent.msg

       # we should sleep at least 2 mins

       if parent.sleep == 0 : parent.sleep = 120

       # check for a pulse message ... but post once

       pulse_message = None

       try   :
               pulse_message = os.environ.get('PULSE_MESSAGE')
               logger.info("env message = %s" % pulse_message)
       except: 
               if parent.pulse_message: pulse_message = parent.pulse_message

       if pulse_message == self.last_pulse_message :
          pulse_message = None

       # warn if not xpublic

       if parent.post_exchange != 'xpublic' :
          logger.warning("pulsing on %s" % parent.post_exchange)

       msg.exchange = parent.post_exchange
       msg.topic    = 'v02.pulse'

       msg.set_time()
       msg.notice   = '%s' % msg.time
       if pulse_message : 
          msg.notice += ' ' + pulse_message
          self.last_pulse_message = pulse_message
        
       msg.headers = {}
       msg.headers['pulse'] = '%d' % parent.sleep
       msg.trim_headers()

       msg.publish()

       if pulse_message: logger.info("pulse %s %s" % (msg.topic,pulse_message))
       else            : logger.info("pulse %s" % msg.topic)

       return False

poll_script = POLL_SCRIPT(self)
self.do_poll = poll_script.perform
