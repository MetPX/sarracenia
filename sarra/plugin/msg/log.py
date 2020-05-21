from sarra.plugin import Plugin
import logging

logger = logging.getLogger( __name__ ) 

class Log(Plugin):

    def __init__(self,options):
        pass

    def on_messages(self,worklist):

        for msg in worklist:
            logger.info( "msg/log received: %s " % msg )
  
        logger.info( "self.__dict__ %s" % self.__dict__ )

        return worklist

