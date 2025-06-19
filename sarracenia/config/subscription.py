
import copy
import json
import os

import logging

logger = logging.getLogger(__name__)


class Subscription(dict):

    def __init__(self, options, queueName_template, queueName, subtopic):

        exchange=None
        if hasattr(options,'exchange') and options.exchange:
            exchange=options.exchange
        else:
            if not hasattr(options.broker.url,'username') or ( options.broker.url.username == 'anonymous' ):
                exchange = 'xpublic'
            else:
                exchange = 'xs_%s' % options.broker.url.username

            if options.component in [ 'poll', 'post', 'watch' ]:
                if hasattr(options,'post_exchangeSuffix') and options.post_exchangeSuffix:
                    exchange += '_%s' % options.post_exchangeSuffix

                if hasattr(options, 'post_exchangeSplit') and hasattr( options, 'no') and (options.no > 0):
                    exchange += "%02d" % (options.no % options.post_exchangeSplit)
            else:
                if hasattr(options, 'exchangeSuffix'):
                    exchange += '_%s' % options.exchangeSuffix

                if hasattr(options, 'exchangeSplit') and hasattr( options, 'no') and (options.no > 0):
                    exchange += "%02d" % (options.no % options.exchangeSplit)

        self['broker'] = options.broker
        self['bindings'] = [ { 'exchange': exchange, 'prefix': options.topicPrefix, 'sub': subtopic } ]

        self['queue']={ 'name': queueName, 'template': queueName_template, 'cleanup_needed': None }
        for a in [ 'queueBind', 'queueDeclare' , 'queueType' ]:
            aa = a.replace('queue','').lower()
            if hasattr(options, a):
                self['queue'][aa] = getattr(options,a)

        for a in [ 'auto_delete', 'clean_session', 'durable', 'expire', 'max_inflight_messages', \
                'max_queued_messages',  'prefetch', 'qos', 'receiveMaximum', 'tlsRigour', 'topic' ]:
            if hasattr(options, a):
                self['queue'][a] = getattr(options,a)
        self['baseDir'] = options.baseDir


class Subscriptions(list):
    # list of subscription

    def read(self,options,fn):

        if not os.path.exists(fn):
            return []

        try:
            with open(fn,'r') as f:
                #self=json.loads(f.readlines())
                self=copy.deepcopy(json.load(f))

            for s in self:
                if type(s['broker']) is str:
                    ok, broker = options.credentials.validate_urlstr(s['broker'])
                    if ok:
                        s['broker'] = broker
            if 'auto_delete' not in self:
                s['auto_delete'] = options.auto_delete
            return self

        except Exception as Ex:
            logger.debug( f"failed {fn}: {Ex}" )
            logger.debug('Exception details: ', exc_info=True)
            return []

    def write(self,fn):

        jl=[]
        for s in self:
            jd=copy.deepcopy(s)
            jd['broker']=str(s['broker'])
            jl.append(jd)

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

            
    def deltAnalyze(self, other):
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
        if self == other:
            return None

        different_subscriptons=[]
