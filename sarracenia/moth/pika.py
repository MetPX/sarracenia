from sarracenia.moth import Moth

import logging

logger = logging.getLogger(__name__)


class PIKA(Moth):
    """
       moth subclass based on the pika AMQP/rabbitmq client library.

       stub: not implemented.

    """
    def __init__(self, broker):
        super().__init__(broker, props, is_subscriber) #FIXME unresolved reference to props and is_subscriber

        logger.error(
            "__init__ AMQP 0.x (rabbitmq) using pika: not implemented ")
