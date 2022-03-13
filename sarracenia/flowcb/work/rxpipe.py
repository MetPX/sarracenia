
import logging
import os
from sarracenia.flowcb import FlowCB 

logger = logging.getLogger(__name__)


class Rxpipe(FlowCB):

      def __init__(self,options):

          self.o=options
          logger.setLevel(getattr(logging, self.o.logLevel.upper()))
          self.o.add_option( option='rxpipe_name', kind='str' )

      def on_start(self):
          if not hasattr(self.o,'rxpipe_name') and self.o.file_rxpipe_name:
              logger.error("Missing rxpipe_name parameter")
              return
          self.rxpipe = open( self.o.rxpipe_name, "w" )
          logger.info( f'opened rxpipe_name: {self.o.rxpipe_name} for append' )

      def after_work(self, worklist):

          for msg in worklist.ok:
              fname= msg['new_dir'] + os.sep + msg['new_file']
              self.rxpipe.write( fname + '\n' )
          self.rxpipe.flush()
          return None

