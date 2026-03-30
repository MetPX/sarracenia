
import copy
import json
import os

import sarracenia.config

import logging

logger = logging.getLogger(__name__)

class Subscription(dict):

    def __init__(self, options, queueName_template, queueName, subtopic, topicOverride=False):

        exchange=None
        if hasattr(options,'exchange') and options.exchange != 'default':
            exchange=options.exchange
        else:
            if not hasattr(options.broker.url,'username') or ( options.broker.url.username == 'anonymous' ):
                exchange = 'xpublic'
            else:
                exchange = f'xs_{options.broker.url.username}'

            if options.component in [ 'poll', 'post', 'watch' ]:
                if hasattr(options,'post_exchange') and options.post_exchange:
                    exchange = options.post_exchange

                if hasattr(options,'post_exchangeSuffix') and options.post_exchangeSuffix:
                    exchange += f'_{options.post_exchangeSuffix}'

                if hasattr(options, 'post_exchangeSplit') and hasattr( options, 'no') and (options.no > 0):
                    exchange += "%02d" % (options.no % options.post_exchangeSplit)
            else:
                if hasattr(options, 'exchangeSuffix'):
                    exchange += f'_{options.exchangeSuffix}'

                if hasattr(options, 'exchangeSplit') and hasattr( options, 'no') and (options.no > 0):
                    exchange += "%02d" % (options.no % options.exchangeSplit)

        self['broker'] = options.broker

        if options.topicPrefix:
            prefix=options.topicPrefix
        else:
            prefix=[]
        if exchange and not self['broker'].url.scheme.lower().startswith('amqp'):
            prefix= [ exchange ] + prefix

        # For MQTTv5 usage with >1 instance, you need MQTT shared subscriptions. 
        #  
        if  'mqtt' in self['broker'].url.scheme.lower():
           prefix= [ '$share', queueName ] + prefix
           topic_separator='/'
        else:
           topic_separator='.'


        if topicOverride:
            if self['broker'].url.scheme.lower().startswith('amqp'):
                self['bindings'] = [ { 'exchange': exchange, 'topic': topic_separator.join(subtopic) } ]
            elif exchange:
                self['bindings'] = [ { 'topic': topic_separator.join([exchange] + subtopic) } ]
            else:
                self['bindings'] = [ { 'topic': topic_separator.join(subtopic) } ]
        else:
            if self['broker'].url.scheme.lower().startswith('amqp'):
                self['bindings'] = [ { 'exchange': exchange, 'topic': topic_separator.join(prefix + subtopic) } ]
            else:
                self['bindings'] = [ { 'topic':  topic_separator.join(prefix + subtopic) } ]


        self['queue']={ 'name': queueName, 'template': queueName_template, 'cleanup_needed': None, 'mismatch':[] }
        for a in [ 'queueBind', 'queueDeclare' , 'queueType' ]:
            aa = a.replace('queue','').lower()
            if hasattr(options, a):
                self['queue'][aa] = getattr(options,a)

        self['bindings_to_remove'] = []
        for a in [ 'auto_delete', 'clean_session', 'durable', 'expire', 'max_inflight_messages', \
                'max_queued_messages',  'prefetch', 'qos', 'receiveMaximum', 'tlsRigour', 'topic' ]:
            if hasattr(options, a):
                self['queue'][a] = getattr(options,a)

        # parse list option amqp_queue_args, e.g.:
        #   amqp_queue_args x-consumer-timeout=12345
        a = 'amqp_queue_args'
        if hasattr(options, a):
            if not self['broker'].url.scheme.lower().startswith('amqp'):
                logger.warning(f"{a} option is set, but broker scheme is not AMQP(S): {self['broker']}")
            aqa = getattr(options, a)
            aqa_dict = {}
            for arg in aqa:
                if '=' not in arg:
                    logger.error(f"invalid amqp_queue_args line: {arg} (key and value must be separated by =)")
                    continue
                k, v = arg.split('=', maxsplit=1)
                v = sarracenia.config.guess_type(v.strip())
                aqa_dict[k] = v
            self['queue'][a] = aqa_dict

        self['baseDir'] = options.baseDir


class Subscriptions(list):
    # list of subscription

    def read(self,options,fn):

        if not os.path.exists(fn):
            return []

        try:
            with open(fn,'r') as f:
                data = json.load(f)
                self[:] = copy.deepcopy(data)

            for s in self:
                if type(s['broker']) is str:
                    ok, broker = options.credentials.validate_urlstr(s['broker'])
                    if ok:
                        s['broker'] = broker

                # old subscriptions (pre 3.02) that have "sub" fields in them need conversion.
                if 'mqtt' in s['broker'].url.scheme.lower(): 
                    proto='mqtt'
                    sep = '/' 
                else:
                    proto= 'amqp'
                    sep = '.'

                # subscription format change, recover for version before 3.02

                for b in s['bindings']:
                    if 'sub' in b:
                         pfx=b.get('prefix',[])
                         sub=b['sub']
                         if not type(pfx) == list:
                             pfx=list(pfx)
                         if not type(sub) == list:
                             sub=list(sub)
                         if proto in ['mqtt']:
                             b['topic'] =  sep.join( [ '$share', s['queue']['name'] ] + pfx + sub )
                         else:
                             b['topic'] =  sep.join(pfx+sub)

                    if 'sub' in b:
                        del b['sub']
                    if 'prefix' in b:
                        del b['prefix']

                if 'queue' in s:
                    if not 'tlsRigour' in s['queue']:
                         s['queue']['tlsRigour'] = options.tlsRigour

                if 'auto_delete' not in s:
                    s['auto_delete'] = options.auto_delete
     
            return self

        except Exception as Ex:
            logger.debug('failed %s: %s', fn, Ex)
            logger.debug('Exception details: ', exc_info=True)
            return []

    def write(self,fn):

        jl=[]
        badness=False
        for s in self:
            jd=copy.deepcopy(s)
            jd['broker']=str(s['broker'])
            if 'mismatch' in jd['queue'] and jd['queue']['mismatch']:
                badness=True
                logger.critical( f"cannot persist configuration with inconsistent queue" \
                    f" {jd['queue']['name']} state: {jd['queue']['mismatch']} ")

            jl.append(jd)
            
        if badness:
           return

        try:
            with open(fn,'w') as f:
                f.write(json.dumps(jl,sort_keys=True, indent=4))
        except Exception as Ex:
            logger.error( f"failed: {fn}: {Ex}" )
            logger.debug('Exception details: ', exc_info=True)

    def add(self, new_subscription):

        found=False
        for s in self:
            if ( str(s['broker']) == str(new_subscription['broker']) ) and \
               ( s['queue']['name'] == new_subscription['queue']['name'] ):
               newb = new_subscription['bindings'][0]
               for b in s['bindings']:
                   if newb == b:
                      found=True
               if not found:
                  s['bindings'].append( newb )
                  found=True

        if not found:
            #logger.critical( f"appending {new_subscription=} " )
            self.append(new_subscription)

            
    def finalize(self,old_subscriptions):
        """
           NOT IMPLEMENTED!

           given one list of subscriptions, and another set of subscriptions.

           return the list of subscriptions that are in other, but not in self.
           or perhaps:

           * for each subscription add s['bindings_to_remove'] ...
           * got each subscription add s['queue']['cleanup_needed'] = "reason"

           the reason could be: 
               * current expiry mismatch 
               * durable mismatch
               * auto-delete mismatch
               * exclusive mismatch
        """
        if self == old_subscriptions:
            return None

        bindings_in_both=[]
        for os in old_subscriptions:        
            for s in self:
                bindings_to_remove=[]
                if s['broker'] != os['broker']:
                     continue
                if s['queue']['name'] != os['queue']['name']:
                     continue 
                q_bad=[]
                for x in [ 'auto_delete', 'durable', 'expire', 'prefetch' ]:
                    if x not in s['queue'] or x not in os['queue']:
                        continue
                    if s['queue'][x] != os['queue'][x]:
                       logger.critical( f"INVARIANT queue parameter {x} changed, lossy message queue cleanup required to implement" )
                       q_bad.append(x)
                s['queue']['mismatch'] = q_bad

                for b in s['bindings']:
                    for ob in os['bindings']:
                        if ( 'exchange' in b and not 'exchange' in ob ) or ( 'exchange' not in b and 'exchange' in ob ) :
                             continue
                        if 'exchange' in b and b['exchange'] != ob['exchange']:
                             continue                     
                        if b['topic'] != ob['topic']:
                             continue                     
                        bindings_in_both.append(b)
                bindings_to_remove=[]
                for ob in os['bindings']:
                    if not ob in bindings_in_both:
                        bindings_to_remove.append(ob)
                s['bindings_to_remove']  = bindings_to_remove
