
from sarra.tmpc import TMPC
import logging

logger = logging.getLogger( __name__ )

class MQTT(TMPC):

    def __init__( self, broker ):
        """

        """
        logger.error("__init__ MQTT TMPC using paho client library: not implemented.")

    @classmethod
    def assimilate(cls,obj):
        obj.__class__ = MQTT

    def url_proto(self):
        return "mqtt"


