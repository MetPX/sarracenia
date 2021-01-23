from sarracenia.moth import Moth
import logging

logger = logging.getLogger(__name__)


class MQTT(Moth):
    def __init__(self, broker, props, is_subscriber):
        """

          in AMQP: topic separator is dot (.) in MQTT, the topic separator is slash (/)
          have exchange arguments use protocol specific separator or mapped one?

        """
        super().__init__(broker, props, is_subscriber)

        logger.error(
            "__init__ MQTT TMPC using paho client library: not implemented.")
