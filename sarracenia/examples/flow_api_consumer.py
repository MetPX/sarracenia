import re
import sarracenia.config
from sarracenia.flow.subscribe import Subscribe
import sarracenia.flowcb
import sarracenia.credentials

cfg = sarracenia.config.no_file_config()

cfg.broker = sarracenia.credentials.Credential(
    'amqps://anonymous:anonymous@hpfx.collab.science.gc.ca')
cfg.topicPrefix = ['v02', 'post']
cfg.component = 'subscribe'
cfg.config = 'flow_demo'
cfg.action = 'hoho'
cfg.bindings = [('xpublic', ['v02', 'post'],
                 ['*', 'WXO-DD', 'observations', 'swob-ml', '#'])]
cfg.queueName = 'q_anonymous.subscriber_test2'
cfg.download = True
cfg.batch = 1
cfg.messageCountMax = 5

# set the instance number for the flow class.
cfg.no = 0

# set other settings based on what is provided, for things like state files.
cfg.finalize()

# accept/reject patterns:
pattern = ".*"
#              to_match, write_to_dir, DESTFN, regex_to_match, accept=True,mirror,strip, pstrip,flatten
cfg.masks = [(pattern, "/tmp/flow_demo", None, re.compile(pattern), True,
              False, False, False, '/')]

subscriber = sarracenia.flow.subscribe.Subscribe(cfg)

subscriber.run()
