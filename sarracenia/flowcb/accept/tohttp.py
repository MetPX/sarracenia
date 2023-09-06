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

            #message['set_notice_url'](message['url'])
            # Updated to remove call to message.set_notice_url
            #This is more complex than the fixes in testretry, and httptohttps because 
            # it here we're calling the set_notice_url method, which had more logic
            baseUrl = ''
            relPath = url.path.strip('/').replace(' ', '%20').replace('#', '%23')

            if url.scheme == 'file':
                #self.notice = '%s %s %s' % (self.pubtime, 'file:', '/'+notice_path)
                baseUrl = 'file:'
                relPath = '/' + relPath
            else:
                
                static_part = url.geturl().replace(url.path, '') + '/'

                if url.scheme == 'http':
                    baseUrl = static_part
                    relPath = relPath

                elif url.scheme[-3:] == 'ftp':
                    if url.path[:2] == '//':
                        relPath = '/' + relPath

            logger.debug("ToHttp config; baseDir=%s, toHttpRoot" % (self.o.baseDir, self.o.toHttpRoot))
            logger.info("ToHttp message output: baseUrl=%s, relPath=%s" % (message['baseUrl'], message['relPath']))
