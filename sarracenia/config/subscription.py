
import json
import logging

logger = logging.getLogger(__name__)


class Subscription(dict):

    def __init__(self, options, queueName, subtopic):

        self['broker'] = options.broker
        self['bindings'] = [ { 'exchange': options.exchange, 'prefix': options.topicPrefix, 'sub': subtopic } ]
        self['queue']={ 'name': queueName }
        for a in [ 'auto_delete', 'durable', 'expire', 'message_ttl', 'prefetch', 'qos', 'queueBind', 'queueDeclare' ]:
            aa = a.replace('queue','').lower()
            if hasattr(options, a) and getattr(options,a):
                self['queue'][aa] = getattr(options,a)

        #self['topic'] = { 'exchange': options.exchange, 'prefix': options.topicPrefix, 'sub': subtopic }
        #self['queue']={ 'name': queueName }
        #for a in [ 'auto_delete', 'broker', 'durable', 'exchange', 'expire', \
        #        'message_ttl', 'prefetch', 'qos', 'queueBind', 'queueDeclare', 'topicPrefix' ]:
        #   if hasattr(options, a) and getattr(options,a):
        #       self['queue'][a] = getattr(options,a)


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
            logger.error( f"failed to read to {fn}: {Ex}" )
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
            logger.error( f"failed to write to {fn}: {Ex}" )
            logger.debug('Exception details: ', exc_info=True)

    def add(self, new_subscription):

        found=False
        for s in self:
            if ( s['broker'] == new_subscription['broker'] ) and \
               ( s['queue']['name'] == new_subscription['queue']['name'] ):
               for b in s['bindings']:
                   newb = new_subscription['bindings'][0]
                   if (b['sub'] != newb['sub']) or (b['prefix'] != newb['prefix']):
                      s['bindings'].append( { 'exchange': newb['exchange'], \
                                   'prefix':newb['prefix'], 'sub':newb['sub'] } )
                      found=True

        if not found:
            self.append(new_subscription)

            
    def differences(self, other):
        """
           return None if there are no differentces.
        """
        if self == other:
            return None

        different_subscriptons=[]
        


=======
>>>>>>> 218cb8ad (refactored configuration parsing classes: BREAKING CHANGE)
