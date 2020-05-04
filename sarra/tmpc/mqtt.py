
from sarra.tmpc import TMPC

class MQTT(TMPC):

    def __init__( self, broker ):
        """

        """
        print("__init__ MQTT TMPC implementation using paho client library")

    @classmethod
    def assimilate(cls,obj):
        obj.__class__ = MQTT

    def url_proto(self):
        return "mqtt"


