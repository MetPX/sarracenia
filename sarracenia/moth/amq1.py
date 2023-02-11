from sarracenia.moth import Moth

import logging

logger = logging.getLogger(__name__)


class AMQ1(Moth):
    def __init__(self, broker, props, is_subscriber):
        """
            AMQP 1.0 library to be built with libqpid-proton (the only free amqp 1.0 library around.)

            stub, not implemented
        """
        super().__init__(broker, props, is_subscriber)

        logger.error(
            "__init__ AMQP 1.0 Moth using qpid-proton library: not implemented"
        )
