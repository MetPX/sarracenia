"""
  msg_2http:  is the converse of msg_2file.
  after processing on a filter, a file URL needs to be turned back into a web url.
  
  uses savedurl created by msg_2file, to convert file url back to original.
   
"""
import logging
import re
from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)

class ToHttp(FlowCB):
    def __init__(self, options):
        self.o = options
        if hasattr(self.o, 'baseDir'):
            self.o.ldocroot = self.o.base_dir
        if hasattr(self.o, 'msg_2http_root'):
            self.o.ldocroot = self.o.msg_2http_root[0]

        self.o.hurlre = re.compile('file:/' + self.o.ldocroot)

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:
            logger.debug("msg_2http input: urlstr: %s" % message['urlstr'])
            message['urlstr'] = self.o.hurlre.sub(message['savedurl'], message['urlstr'])
            message['url'] = urllib.parse.urlparse(message['urlstr'])
            message['set_notice_url'](message['url'])
            logger.debug("msg_2http base_dir=%s " % (self.o.baseDir))
            logger.info("msg_2http output: urlstr: %s" % message['urlstr'])
            new_incoming.append(message)
        worklist.incoming = new_incoming



