
from sarra.tmpc import TMPC

class PIKA(TMPC):

    def __init__( self, broker ):
        """

        """
        print("__init__ AMQP 0.x (rabbitmq) using pika ")

    @classmethod
    def assimilate(cls,obj):
        obj.__class__ = PIKA

    def url_proto(self):
        return "pika"


