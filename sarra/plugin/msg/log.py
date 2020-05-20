from sarra.plugin import Plugin
import logging

logger = logging.getLogger( __name__ ) 

class Log(Plugin):

    def on_messages(self,worklist):

        for msg in worklist:
            logger.info( "msg/log received: %s " % msg )

        return worklist

