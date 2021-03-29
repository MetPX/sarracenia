
import logging
import os
from sarracenia.flowcb import FlowCB 

logger = logging.getLogger(__name__)


class RxPipe(FlowCB):

      def __init__(self,options):

          self.o=options
          logger.setLevel(getattr(logging, self.o.logLevel.upper()))
          self.o.add_option( option='rxpipe_name', kind='str' )

      def on_start(self):
          if not hasattr(self.o,'rxpipe_name') and self.o.file_rxpipe_name:
              logger.error("Missing rxpipe_name parameter")
              return
          self.rxpipe = open( self.o.rxpipe_name, "w" )

      def after_work(self, worklist):

          for msg in worklist.ok:
              self.rxpipe.write( msg['new_dir'] + os.sep + msg['new_file'] + '\n' )
          self.rxpipe.flush()
          return None

