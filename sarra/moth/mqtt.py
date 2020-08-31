
from sarra.moth import Moth
import logging

logger = logging.getLogger( __name__ )

class MQTT(Moth):

    def __init__( self, broker ):
        """

          in AMQP: topic separator is dot (.) in MQTT, the topic separator is slash (/)
          have exchange arguments use protocol specific separator or mapped one?

        """
        logger.error("__init__ MQTT TMPC using paho client library: not implemented.")

    @classmethod
    def assimilate(cls,obj):
        obj.__class__ = MQTT

    def url_proto(self):
        return "mqtt"


