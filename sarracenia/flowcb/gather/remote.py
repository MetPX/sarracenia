
import logging


import sarracenia.transfer

from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class RemoteTransfer(FlowCB):
    """
    Use a sarracenia.transfer Protocol to list remote resources, and generate messages.

    This is supposed to be the basis for the re-factoring of Poll.  the code here
    just calls proto.walk (currently inexistant.) walk is going to be a stateful, incremental walk
    throught the file system, and all record of past polls will be dealt with via the recent_files cache.

    """
    def __init__(self, options):
 
        self.o = options

        logger.setLevel( getattr( logging, self.o.logLevel.upper() ) )

        # check destination

        self.details = None
        if self.o.destination is not None:
            ok, self.details = sarracenia.config.Config.credentials.get(
                self.o.destination)

        if self.o.destination is None or self.details == None:
            logger.error("destination option incorrect or missing\n")
            return

        if self.o.post_baseUrl is None:
            self.o.post_baseUrl = self.details.url.geturl()
            if self.o.post_baseUrl[-1] != '/': self.o.post_baseUrl += '/'
            if self.o.post_baseUrl.startswith('file:'):
                self.o.post_baseUrl = 'file:'
            if self.details.url.password:
                self.o.post_baseUrl = self.o.post_baseUrl.replace(
                    ':' + self.details.url.password, '')

        self.dest = sarracenia.transfer.Transfer.factory(
            self.details.url.scheme, self.o)

        if not 'destination' in self.o:
            logger.error('unsupported destination %s' )

      

    def gather(self):
        """
          return a list of messages corresponding to files available on the remote resource.
        """
        messages = []
        for d in self.pulls:
           messages.extend(self.dest.walk(d)) 

        return messages

