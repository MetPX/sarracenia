#!/usr/bin/python3

"""
 poll_pulse: a kind of keepalive and client messaging mechanism

 usage:
     in an sr_poll configuration file:
     the post broker user must be the admin 
     because we pulse on all exchanges

 do_poll poll_pulse.py

 options:

 pulse_message
     a message to be logged to all sarracenia consuming messages
     This message can be considered as a startup message
     Might be usefull if message = 'pulse restarted'

 environment variable:

 PULSE_MESSAGE : environment variable that can be set
     to pulse a different message ... Just set this variable and
     sr_poll <pulse_config> restart

 The code tries to minimize the posting to one time
 But would repost on restart

 Environment variable overwrites pulse_message option settings

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
       logger      = parent.logger

       self.logger = logger
       self.parent = parent

       msg = parent.msg

       # we should sleep at least 2 mins

       if parent.sleep == 0 : parent.sleep = 120

       # check for a pulse message ... but post once

       pulse_message = None

       try   :
               pulse_message = os.environ.get('PULSE_MESSAGE')
       except: 
               if parent.pulse_message: pulse_message = parent.pulse_message

       # try to post message once

       if pulse_message == self.last_pulse_message :
          pulse_message = None

       # build message

       msg.topic    = 'v02.pulse'

       msg.set_time()
       msg.notice   = '%s' % msg.time
       if pulse_message : 
          msg.notice += ' ' + pulse_message
          self.last_pulse_message = pulse_message
        
       msg.headers = {}
       msg.headers['frequence'] = '%d' % parent.sleep
       msg.trim_headers()

       # pulse on all exchanges
       # because of its topic, it should not impact any process
       # that does not consider topic v02.pulse

       lst_dict = self.rabbitmqadmin("list exchanges name")

       ex = []
       for edict in lst_dict :
           exchange = edict['name']
           if exchange == ''        : continue
           if exchange[0] != 'x'    : continue
           if exchange == 'xreport' : continue
           # deprecated exchanges
           if exchange == 'xlog'    : continue
           if exchange[0:3] == 'xl_': continue
           if exchange[0:3] == 'xr_': continue
           ex.append(exchange)
           msg.pub_exchange = exchange
           msg.publish()

       if pulse_message :
          logger.info("message pulsed to exchanges %s" % ex)

       if pulse_message: logger.info("pulse %s %s" % (msg.topic,pulse_message))
       else            : logger.info("pulse %s" % msg.topic)

       return False

   # from sr_audit.py
   def rabbitmqadmin(self,options):
        try   : from sr_rabbit       import exec_rabbitmqadmin
        except: from sarra.sr_rabbit import exec_rabbitmqadmin

        self.logger.debug("sr_audit rabbitmqadmin %s" % options)
        try :
                 (status, answer) = exec_rabbitmqadmin(self.parent.post_broker,options,self.logger)
                 if status != 0 or answer == None or len(answer) == 0 or 'error' in answer :
                    self.logger.error("rabbitmqadmin invocation failed")
                    return []

                 if answer == None or len(answer) == 0 : return []

                 lst = []
                 try    : lst = eval(answer)
                 except : pass

                 return lst

        except :
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
                self.logger.error("rabbimtqadmin "+ options)
        return []


poll_script = POLL_SCRIPT(self)
self.do_poll = poll_script.perform
