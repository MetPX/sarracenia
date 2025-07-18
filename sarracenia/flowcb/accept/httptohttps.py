"""
Plugin httptohttps.py:
    This plugin simply turns messages with baseUrl http://...  into   https://...

    The process would need to be restarted. From now on, all http messages that would be
    consumed, would be turned into an https message. The remaining of the process will
    treat the message as if posted that way. That plugin is an easy way to turn transaction
    between dd.weather.gc.ca and the user into secured https transfers.

Usage:
    flowcb sarracenia.flowcb.accept.httptohttps.HttpToHttps
"""

import logging
from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)


class HttpToHttps(FlowCB):
    def __init__(self, options):
        super().__init__(options,logger)

    def after_accept(self, worklist):
        for message in worklist.incoming:
            if not 'http:' in message['baseUrl']:
                continue
            message['baseUrl'] = message['baseUrl'].replace('http:', 'https:')
