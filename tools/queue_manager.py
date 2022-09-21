#!/usr/bin/python

import commands, pika, sys, time

# defines limits

max_messages = 25000
max_memory = 50000000

#===========================
# defines rabbitmqctl commands
#===========================


class DeleteQueueNamed(object):
    def __init__(self, amqp_url):
        self._connection = None
        self._channel = None
        self._url = amqp_url
        self.queue = None

    def run(self):
        self._connection = self.connect()
        self._connection.ioloop.start()

    def connect(self):
        return pika.SelectConnection(pika.URLParameters(self._url),
                                     self.on_connection_open,
                                     stop_ioloop_on_close=True)

    def on_connection_open(self, unused_connection):
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        self._channel = channel
        print(self.queue)
        self._channel.queue_delete(None,
                                   self.queue,
                                   if_unused=False,
                                   if_empty=False,
                                   nowait=True)
        self._channel.close()
        self._connection.close()


#===========================
# defines rabbitmqctl commands
#===========================


def rabbitmqctl(options):
    cmd = "/usr/sbin/rabbitmqctl " + options
    (status, text) = commands.getstatusoutput(cmd)
    if len(text) == 0: return []
    if status != 0:
        print("Error could not execute this:")
        print(cmd)
        sys.exit(1)
    return text.split('\n')


#===========================

# get active clients

clients = rabbitmqctl(
    "list_consumers | grep -v  ^Listing | grep -v ^...done | awk '{print $1}'")

#===========================

# get active queues (first word is the queue it uses)

queues = {}
qmm = rabbitmqctl(
    "list_queues name messages memory | grep -v  ^Listing | grep -v ^...done")

# build queue dictionnary   dic[queuename] = [ nb_message, qmemory ]

for l in qmm:
    l = l.strip()
    parts = l.split()
    queues[parts[0]] = [int(parts[1]), int(parts[2])]

#===========================

# find queue binding with exchange

bindings = {}

qx = rabbitmqctl(
    "list_bindings destination_name source_name | grep -v  ^Listing | grep -v ^...done"
)

# build bindings dictionnary

for l in qx:
    l = l.strip()
    parts = l.split()
    if len(parts) != 2: continue
    bindings[parts[0]] = parts[1]

# check queue without consumers
# delete queue if out of max settings

qdeleted = []

for q in queues:

    # queue used by a client
    if q in clients: continue

    nb_messages, qmemory = queues[q]

    if max_messages < nb_messages or max_memory < qmemory:
        exchange = bindings[q]
        qdeleted.append(q)
        dq = DeleteQueueNamed('amqp://root:r00t4rabbitmq@localhost:5672/%2F')
        dq.queue = q
        dq.run()

datim = time.strftime("%Y-%m-%d %H:%M:%S,000", time.gmtime())
print("%s queues  : %s " % (datim, queues.keys()))
print("%s deleted : %s " % (datim, qdeleted))
print()
