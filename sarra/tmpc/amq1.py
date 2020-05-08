
from sarra.tmpc import TMPC

import logging
 
logger = logging.getLogger( __name__ )

class AMQ1(TMPC):

    def __init__( self, broker ):
        """

        """
        logger.error("__init__ AMQP 1.0 TMPC using qpid-proton library: not implemented")

    @classmethod
    def assimilate(cls,obj):
        obj.__class__ = AMQ1

    def url_proto(self):
        return "amq1"


