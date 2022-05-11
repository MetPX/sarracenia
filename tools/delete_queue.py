# in PIKA an administrative tool to get rid of a Queue
# on the rabbitmq server

import pika
import sys


HOST = sys.argv[1]
ADMIN = sys.argv[2]
PW = sys.argv[3]
QUEUE = sys.argv[4]


class DeleteQueueNamed(object):
    def __init__(self, amqp_url):
        self._connection = None
        self._channel = None
        self._url = amqp_url
        self.run()

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
        self._channel.queue_delete(None,
                                   QUEUE,
                                   if_unused=False,
                                   if_empty=False,
                                   nowait=True)
        self._channel.close()
        self._connection.close()


DeleteQueueNamed('amqp://%s:%s@%s:5672' % (ADMIN, PW, HOST) + '/%2F')
