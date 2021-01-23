from sarracenia.moth import Moth

import logging

logger = logging.getLogger(__name__)


class PIKA(Moth):
    def __init__(self, broker):
        """

        """
        super().__init__(broker, props, is_subscriber)

        logger.error(
            "__init__ AMQP 0.x (rabbitmq) using pika: not implemented ")
