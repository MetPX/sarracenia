#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, 2008-2021
#

import logging
import sarracenia
from sarracenia.flow import Flow
import sys



logger = logging.getLogger(__name__)

default_options = {
    'acceptUnmatched': False,
    'blocksize': 1,
    'bufsize': 1024 * 1024,
    'chmod': 0o400,
    'pollUrl': None,
    'follow_symlinks': False,
    'force_polling': False,
    'inflight': None,
    'integrity_method': 'cod,sha512',
    'part_ext': 'Part',
    'partflg': '1',
    'post_baseDir': None,
    'permCopy': True,
    'timeCopy': True,
    'randomize': False,
    'rename': None,
    'post_on_start': False,
    'sleep': -1,
    'nodupe_ttl': 7 * 60 * 60,
    'nodupe_fileAgeMax': 30 * 24 * 60 * 60,
}

#  'sumflg': 'cod,md5',


class Poll(Flow):
    """
       repeatedly query a remote (non-sarracenia) server to list the files there.
       post messages (to post_broker) for every new file discovered there.

       the sarracenia.flowcb.poll class is used to implement the remote querying,
       and is highly customizable to that effect.

       if the vip option is set, 
       * subscribe to the same settings that are being posted to.
       * consume all the messages posted, keeping new file duplicate cache updated.
          
    """
    def __init__(self, options):

        super().__init__(options)

        if not 'poll' in ','.join(self.plugins['load']):
            logger.info( f"adding poll plugin, because missing from: {self.plugins['load']}" ) 
            self.plugins['load'].append('sarracenia.flowcb.poll.Poll')

        if options.vip:
            self.plugins['load'].insert(
                0, 'sarracenia.flowcb.gather.message.Message')

        self.plugins['load'].insert(0,
                                    'sarracenia.flowcb.post.message.Message')

        if not sarracenia.extras['ftppoll']['present']:
            if hasattr( self.o, 'pollUrl' ) and ( self.o.pollUrl.startswith('ftp') ):
                logger.critical( f"attempting to configure an FTP poll pollUrl={self.o.pollUrl}, but missing python modules: {' '.join(sarracenia.extras['ftppoll']['modules_needed'])}" )
                sys.exit(1)

    def do(self):
        """
            stub to do the work: does nothing, marking everything done.
            to be replaced in child classes that do transforms or transfers.
        """

        # mark all remaining messages as rejected.
        if self.worklist.poll_catching_up:
            # in catchup mode, just reading previously posted messages.
            self.worklist.rejected = self.worklist.incoming
        else:
            self.worklist.ok = self.worklist.incoming

        logger.debug('processing %d messages worked! (stop requested: %s)' %
                     (len(self.worklist.incoming), self._stop_requested))
        self.worklist.incoming = []


    def gather(self):

        super().gather()

        if len(self.worklist.incoming) > 0:
            logger.info('ingesting %d postings into duplicate suppression cache' % len(self.worklist.incoming) )
            self.worklist.poll_catching_up = True
            return 
        else:
            self.worklist.poll_catching_up = False

        if self.have_vip:
            for plugin in self.plugins['poll']:
                new_incoming = plugin()
                if len(new_incoming) > 0:
                    self.worklist.incoming.extend(new_incoming)

    def please_stop(self):
        """
           since poll has no state to flush, one can exit it immediately at any point.
        """
        sys.exit(0)
