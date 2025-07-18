import os

import urllib.parse

import logging

from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class ShiftDir2baseUrl(FlowCB):
    """
       modify message to shift directories from relPath to baseUrl:

       given the setting shiftDir2baseUrl == 2 and given message with 
           baseDir=https://a  relPath=b/c/d/e subtopic=b/c/d -->  baseDir=https://a/b/c  relPath=d/e  subtopic=d

    """
    def __init__(self, options):

        super().__init__(options,logger)
        self.o.add_option('shiftDir2baseUrl', 'count', 1)

    def after_work(self, worklist):
        for m in worklist.ok:
            logger.debug("before: base_url=%s, subtopic=%s relPath=%s" %
                         (m['baseUrl'], m['subtopic'], m['relPath']))

            dirs2shift = '/'.join(m['subtopic'][0:self.o.shiftDir2baseUrl])
            m['subtopic'] = m['subtopic'][self.o.shiftDir2baseUrl:]
            m['baseUrl'] = m['baseUrl'] + '/' + dirs2shift
            m['relPath'] = '/'.join(
                m['relPath'].split('/')[self.o.shiftDir2baseUrl:])

            logger.info(
                "shifted %d done: base_url=%s, subtopic=%s relPath=%s" %
                (self.o.shiftDir2baseUrl, m['baseUrl'], m['subtopic'],
                 m['relPath']))
