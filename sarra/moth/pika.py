
from sarra.moth import Moth

import logging

logger = logging.getLogger( __name__ )

class PIKA(Moth):

    def __init__( self, broker ):
        """

        """
        logger.error("__init__ AMQP 0.x (rabbitmq) using pika: not implemented ")

    @classmethod
    def assimilate(cls,obj):
        obj.__class__ = PIKA

    def url_proto(self):
        return "pika"


