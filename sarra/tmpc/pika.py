
from sarra.tmpc import TMPC

import logging

logger = logging.getLogger( __name__ )

class PIKA(TMPC):

    def __init__( self, broker ):
        """

        """
        logger.error("__init__ AMQP 0.x (rabbitmq) using pika: not implemented ")

    @classmethod
    def assimilate(cls,obj):
        obj.__class__ = PIKA

    def url_proto(self):
        return "pika"


