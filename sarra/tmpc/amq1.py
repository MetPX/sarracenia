
from sarra.tmpc import TMPC

class AMQ1(TMPC):

    def __init__( self, broker ):
        """

        """
        print("__init__ AMQP 1.0 TMPC implementation using qpid-proton library")

    @classmethod
    def assimilate(cls,obj):
        obj.__class__ = AMQ1

    def url_proto(self):
        return "amq1"


