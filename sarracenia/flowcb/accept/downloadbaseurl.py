"""
Plugin downloadbaseurl.py:
    Downloads files sourced from the baseUrl of the poster, and saves them in the
    directory specified in the config. Created to use with the poll_nexrad.py
    plugin to download files uploaded in the NEXRAD US Weather Radar public dataset.
    Compatible with Python 3.5+.

Example:
    A sample do_download option for subscribe.
	Downloads the file located at message['baseUrl'] and saves it

Usage:
	flowcb sarracenia.flowcb.accept.downloadbaseurl.DownloadBaseUrl
"""

import logging
import os
import urllib.request
from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)


class DownloadBaseUrl(FlowCB):
    def __init__(self, options):
        self.o = options
        logger.debug("msg_download_baseurl initialized")

    def after_accept(self, worklist):
        for message in worklist.incoming:
            # if mirror is set to True, comment these two lines out
            #TODO: this self.o.new_dir could be instead message['new_dir'] I think.. to see..
            keypath, key = os.path.split(self.o.new_dir + message['new_file'])
            if not os.path.exists(keypath): os.makedirs(keypath)

            with open(keypath + '/' + key, 'wb') as f:
                with urllib.request.urlopen(message['baseUrl']) as k:
                    f.write(k.read())
