#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, 2008-2021
#

import sarracenia.moth
import copy
import dateparser
import datetime
import logging
import os
import paramiko

import sarracenia 
import sarracenia.config
from sarracenia.flow import Flow
import sarracenia.transfer
import stat
import pytz
import sys, time



logger = logging.getLogger(__name__)

default_options = {
    'acceptUnmatched': False,
    'blocksize': 1,
    'bufsize': 1024 * 1024,
    'poll_builtinGather': True,
    'chmod': 0o400,
    'destination': None,
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
    'nodupe_ttl': 7*60*60,
    'nodupe_fileAgeMax': 30*24*60*60,
}


#  'sumflg': 'cod,md5',


class Poll(Flow):
    def __init__(self, options):

        super().__init__(options)

        if not 'poll' in self.plugins['load']:
            self.plugins['load'].append('sarracenia.flowcb.poll.Poll')

        if options.vip:
            self.plugins['load'].insert(0,'sarracenia.flowcb.gather.message.Message')

        self.plugins['load'].insert(0,'sarracenia.flowcb.post.message.Message')


    def gather(self):

        super().gather()

        if self.have_vip:
            for plugin in self.plugins['poll']:
                new_incoming = plugin()
                if len(new_incoming) > 0:
                    self.worklist.incoming.extend(new_incoming)

       

