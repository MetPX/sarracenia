
class Subscription(dict):

    def __init__(self, options, queueName, subtopic):

        self['broker'] = options.broker
        self['topic'] = { 'exchange': options.exchange, 'prefix': options.topicPrefix, 'sub': subtopic }
        self['queue']={ 'name': queueName }
        for a in [ 'auto_delete', 'broker', 'durable', 'exchange', 'expire', \
                'message_ttl', 'prefetch', 'qos', 'queueBind', 'queueDeclare', 'topicPrefix' ]:
            if hasattr(options, a) and getattr(options,a):
                self['queue'][a] = getattr(options,a)
