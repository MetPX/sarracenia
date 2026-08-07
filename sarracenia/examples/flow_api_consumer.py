import copy
import re
import sarracenia.config
from sarracenia.flow.subscribe import Subscribe
import sarracenia.flowcb
import sarracenia.config.credentials
import socket

cfg = sarracenia.config.no_file_config()

cfg.broker = sarracenia.config.credentials.Credential(
    'amqps://anonymous:anonymous@hpfx.collab.science.gc.ca')
cfg.topicPrefix = ['v02', 'post']
cfg.component = 'subscribe'
cfg.config = 'flow_demo'
cfg.action = 'foreground'
bindings = [ {'exchange':'xpublic', 'topic':'v02.post.*.WXO-DD.observations.swob-ml.#'}]
cfg.queueName = 'q_${BROKER_USER}_${HOSTNAME}_${QUEUESHARE}'
cfg.download = True
cfg.batch = 1
cfg.logReject = True
cfg.expire = 600
cfg.messageCountMax = 5
cfg.queueShare = 'SomethingSessionfulToYou'


cfg.settings = { 'sarracenia.moth.amqp.AMQP': { 'logLevel':'debug' } }



# Note: queue name must start with q_<username> because server is configured to deny anything else.
#

queue = {'name': 'q_anonymous_' + socket.getfqdn() + '_' + cfg.queueShare,
         'template': cfg.queueName,
         'auto_delete' : False, # AO == amqp only
         'durable': True, # AO: queue should survive broker reboots
         'expire': 600,  # MO: seconds until queue with no consumers disappears.
         'prefetch': 5,
         'qos': 1,
         'tlsRigour': 'normal',
         'bind': True,  # whether to bind queues/subscriptions
         'declare': True # whether to declare queues/subscriptions
       }


cfg.subscriptions = sarracenia.config.subscription.Subscriptions( [ {
   'broker': cfg.broker,
   'bindings': bindings,
   'bindings_to_remove': [],
   'queue' : queue
      } ] )


# set the instance number for the flow class.
cfg.no = 0

# set other settings based on what is provided, for things like state files.
cfg.finalize()

# accept/reject patterns:
pattern = ".*"
#              to_match, write_to_dir, DESTFN, regex_to_match, accept=True,mirror,strip, pstrip,flatten
cfg.masks = [(pattern, "/tmp/flow_demo", None, re.compile(pattern), True, False, False, False, '/', None)]

subscriber = sarracenia.flow.subscribe.Subscribe(cfg)

subscriber.run()
