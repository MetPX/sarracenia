
from sarra.moth import Moth

import logging
 
logger = logging.getLogger( __name__ )

class AMQ1(Moth):

    def __init__( self, broker ):
        """

        """
        logger.error("__init__ AMQP 1.0 Moth using qpid-proton library: not implemented")

    @classmethod
    def assimilate(cls,obj):
        obj.__class__ = AMQ1

    def url_proto(self):
        return "amq1"


