#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, 2008-2021
#

import logging
import sarracenia
from sarracenia.flow import Flow
from sarracenia.featuredetection import features
import sys



logger = logging.getLogger(__name__)

default_options = {
    'acceptUnmatched': True,
    'blockSize': 1,
    'bufSize': 1024 * 1024,
    'chmod': 0o400,
    'pollUrl': None,
    'follow_symlinks': False,
    'force_polling': False,
    'inflight': None,
    'identity_method': 'cod,sha512',
    'part_ext': 'Part',
    'partflg': '1',
    'post_baseDir': None,
    'permCopy': True,
    'timeCopy': True,
    'randomize': False,
    'post_on_start': False,
    'nodupe_ttl': 7 * 60 * 60,
    'fileAgeMax': 30 * 24 * 60 * 60,
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

        if hasattr(self.o,'post_exchange') and hasattr(self.o,'exchange'):
            px = self.o.post_exchange if type(self.o.post_exchange) != list else self.o.post_exchange[0]
            if px != self.o.exchange:
                logger.warning( f"post_exchange: {px} is different from exchange: {self.o.exchange}. The settings need for multiple instances to share a poll." )
            else:
                logger.info( f"Good! post_exchange: {px} and exchange: {self.o.exchange} match so multiple instances to share a poll." )

        if not 'scheduled' in ','.join(self.plugins['load']):
            self.plugins['load'].append('sarracenia.flowcb.scheduled.poll.Poll')

        if options.vip:
            self.plugins['load'].insert( 0, 'sarracenia.flowcb.gather.message.Message')

        self.plugins['load'].insert( 0, 'sarracenia.flowcb.post.message.Message')

        if self.o.nodupe_ttl < self.o.fileAgeMax:
            logger.warning( f"nodupe_ttl < fileAgeMax means some files could age out of the cache and be re-ingested ( see : https://github.com/MetPX/sarracenia/issues/904")

        if not features['ftppoll']['present']:
            if hasattr( self.o, 'pollUrl' ) and ( self.o.pollUrl.startswith('ftp') ):
                logger.critical( f"attempting to configure an FTP poll pollUrl={self.o.pollUrl}, but missing python modules: {' '.join(features['ftppoll']['modules_needed'])}" )

    def on_start(self):

        if 'poll' not in self.plugins or not self.plugins['poll']:
            logger.info( f"adding built-in poll plugin, because no other poll provided from: {self.plugins['load']}" ) 

            self.plugins['load'].append('sarracenia.flowcb.poll.Poll')
            plugin = sarracenia.flowcb.load_library("sarracenia.flowcb.poll.Poll", self.o)
            self.plugins['poll'] = [ getattr(plugin, 'poll') ]
        else:
            logger.info( f"not adding built-in poll, because already present: {self.plugins['poll']} " )
