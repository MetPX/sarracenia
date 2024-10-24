
import json
import logging

logger = logging.getLogger(__name__)


class Subscription(dict):

    def __init__(self, options, queueName, subtopic):

        self['broker'] = options.broker
        self['bindings'] = [ { 'exchange': options.exchange, 'prefix': options.topicPrefix, 'sub': subtopic } ]

        self['queue']={ 'name': queueName, 'cleanup_needed': None }
        for a in [ 'auto_delete', 'durable', 'expire', 'message_ttl', 'prefetch', 'qos', 'queueBind', 'queueDeclare' ]:
            aa = a.replace('queue','').lower()
            if hasattr(options, a) and getattr(options,a):
                self['queue'][aa] = getattr(options,a)

class Subscriptions(list):
    # list of subscription

    def read(self,options,fn):
        try:
            with open(fn,'r') as f:
                #self=json.loads(f.readlines())
                self=json.load(f)

            for s in self:
                if type(s['broker']) is str:
                    ok, broker = options.credentials.validate_urlstr(s['broker'])
                    if ok:
                        s['broker'] = broker
            return self
        except Exception as Ex:
            logger.debug( f"failed {fn}: {Ex}" )
            logger.debug('Exception details: ', exc_info=True)
            return None

    def write(self,fn):

        jl=[]
        for s in self:
            jd=s
            jd['broker']=str(s['broker'])
            jl.append(jd)

        try:
            with open(fn,'w') as f:
                f.write(json.dumps(jl))
        except Exception as Ex:
            logger.error( f"failed: {fn}: {Ex}" )
            logger.debug('Exception details: ', exc_info=True)

    def add(self, new_subscription):

        found=False
        for s in self:
            if ( s['broker'] == new_subscription['broker'] ) and \
               ( s['queue']['name'] == new_subscription['queue']['name'] ):
               newb = new_subscription['bindings'][0]
               for b in s['bindings']:
                   if newb == b:
                      found=True
               if not found:
                      s['bindings'].append( newb )

        if not found:
            self.append(new_subscription)

            
    def deltAnalyze(self, other):
        """
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
