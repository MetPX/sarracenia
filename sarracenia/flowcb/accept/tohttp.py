"""
Plugin tohttp.py:
    ToHttp is the converse of ToFile.
    After processing on a filter, a file URL needs to be turned back into a web url.
    Uses savedUrl created by ToFile, to convert file url back to original.

Usage:
    flowcb sarracenia.flowcb.accept.tohttp.ToHttp
"""
import logging
import re
import urllib

from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)


class ToHttp(FlowCB):
    def __init__(self, options):
        self.o = options
        if hasattr(self.o, 'baseDir'):
            self.o.ldocroot = self.o.baseDir
        if hasattr(self.o, 'toHttpRoot'):
            self.o.ldocroot = self.o.toHttpRoot[0]

        self.o.hurlre = re.compile('file:/' + self.o.ldocroot)

    def after_accept(self, worklist):
        for message in worklist.incoming:
            logger.debug("msg_2http input: urlstr: %s" % message['urlstr'])
            message['urlstr'] = self.o.hurlre.sub(message['savedurl'],
                                                  message['urlstr'])
            message['url'] = urllib.parse.urlparse(message['urlstr'])
            message['set_notice_url'](message['url'])
            logger.debug("msg_2http baseDir=%s " % (self.o.baseDir))
            logger.info("msg_2http output: urlstr: %s" % message['urlstr'])
