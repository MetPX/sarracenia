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
        if hasattr(self.o, 'baseDir'):
            self.o.ldocroot = self.o.baseDir
        if hasattr(self.o, 'toHttpRoot'):
            self.o.ldocroot = self.o.toHttpRoot[0]

        self.o.hurlre = re.compile('file:/' + self.o.ldocroot)

    def after_accept(self, worklist):
        for message in worklist.incoming:
            logger.debug("ToHttp input: urlstr: %s" % message['urlstr'])
            message['urlstr'] = self.o.hurlre.sub(message['savedurl'], message['urlstr'])
            url = urllib.parse.urlparse(message['urlstr'])

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

            message['baseUrl'] = baseUrl
            message['relPath'] = relPath

            logger.debug("ToHttp config.baseDir=%s" % (self.o.baseDir))
            logger.info("ToHttp message output: urlstr=%s, baseUrl=%s, relPath=%s" % (message['urlstr'], message['baseUrl'], message['relPath']))
