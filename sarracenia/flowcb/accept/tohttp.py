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
        super().__init__(options,logger)

        self._ldocroot = None
        
        #self.o.add_option('baseDir', 'str')
        if self.o.baseDir:
            self._ldocroot = self.o.baseDir

        self.o.add_option('toHttpRoot', 'str')
        if self.o.toHttpRoot:
            self._ldocroot = self.o.toHttpRoot

        #self.o.hurlre = re.compile('file:/' + self.o.ldocroot)

    def after_accept(self, worklist):
        for message in worklist.incoming:
            logger.info("ToHttp message input: baseUrl=%s, relPath=%s" % (message['baseUrl'], message['relPath']))

            url = urllib.parse.urlparse(message['baseUrl'])

            new_baseUrl = 'http://' + url.netloc
            if self._ldocroot != None:
                new_baseUrl += self._ldocroot
            
            new_baseUrl += url.path

            message['baseUrl'] = new_baseUrl.replace('///', '//')

            logger.debug("ToHttp config; baseDir=%s, toHttpRoot=%s" % (self.o.baseDir, self.o.toHttpRoot))
            logger.info("ToHttp message output: baseUrl=%s, relPath=%s" % (message['baseUrl'], message['relPath']))
