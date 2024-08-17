
import json
import logging

logger = logging.getLogger(__name__)


class Subscription(dict):

    def __init__(self, options, queueName, subtopic):

        self['broker'] = options.broker
        self['topic'] = { 'exchange': options.exchange, 'prefix': options.topicPrefix, 'sub': subtopic }
        self['queue']={ 'name': queueName }
        for a in [ 'auto_delete', 'durable', 'exchange', 'expire', \
                'message_ttl', 'prefetch', 'qos', 'queueBind', 'queueDeclare', 'topicPrefix' ]:
            if hasattr(options, a) and getattr(options,a):
                self['queue'][a] = getattr(options,a)


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
        except Exception as Ex:
            logger.error( f"failed to read to {fn}: {Ex}" )
            logger.debug('Exception details: ', exc_info=True)
        return self

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

     
