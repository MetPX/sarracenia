#!/usr/bin/python3
"""
  This plugin delays processing of messages by *message_delay* seconds


  sarracenia.flowcb.msg.fdelay 30
  import sarracenia.flowcb.msg.fdelay.FDelay


  every message will be at least 30 seconds old before it is forwarded by this plugin.
  in the meantime, the message is placed on the retry queue by marking it as failed.

"""
import logging
import os
import stat


from sarracenia.flowcb import FlowCB
from sarracenia import timestr2flt, nowflt

logger = logging.getLogger(__name__)


class FDelay(FlowCB):
    def __init__(self, options):

        self.o = options

        logging.basicConfig(format=self.o.logFormat,
                            level=getattr(logging, self.o.logLevel.upper()))

        logger.debug('hoho! FIXME init')
        #parent.declare_option('fdelay')
        if hasattr(self.o, 'msg_fdelay'):
            self.o.fdelay = self.o.msg_fdelay

        if not hasattr(self.o, 'fdelay'):
            self.o.fdelay = 60

        if type(self.o.fdelay) is list:
            self.o.fdelay = self.o.fdelay[0]

        if type(self.o.fdelay) not in [int, float]:
            self.o.fdelay = float(self.o.fdelay)

    def after_accept(self, worklist):
        # Prepare msg delay test
        logger.info('FIXME: fdelay? setting: %f ' % self.o.fdelay )
        outgoing = []
        for m in worklist.incoming:
            # Test msg delay
            elapsedtime = nowflt() - timestr2flt(m['pubTime'])

            logger.info('FIXME: message[pubTime]=%s elapsed: %f ' % (m['pubTime'], elapsedtime ) )
            if m['integrity']['method'] == 'remove':
                # 'remove' msg will be removed by itself
                worklist.rejected.append(m)
                logger.debug('marked rejected 0 (file removal)')
                continue

            # Test msg delay
            elapsedtime = nowflt() - timestr2flt(m['pubTime'])
            if elapsedtime < self.o.fdelay:
                dbg_msg = "message not old enough, sleeping for {:.3f} seconds"
                logger.debug(
                    dbg_msg.format(elapsedtime, self.o.fdelay - elapsedtime))
                m['isRetry'] = False
                m['_deleteOnPost'] |= set(['isRetry'])
                worklist.failed.append(m)
                logger.debug('marked failed 1 (message not old enough)')
                continue

            # Prepare file delay test
            if '/cfr/' in m['new_dir']:
                f = os.path.join(m['new_dir'], m['new_file'])
            else:
                f = '/' + m['relPath']
            if not os.path.exists(f):
                logger.debug("did not find file {}".format(f))
                worklist.failed.append(m)
                logger.debug('marked failed 2 (file not found)')
                continue

            # Test file delay
            filetime = os.stat(f)[stat.ST_MTIME]
            elapsedtime = nowflt() - filetime
            if elapsedtime < self.o.fdelay:
                dbg_msg = "file not old enough, sleeping for {:.3f} seconds"
                logger.debug(
                    dbg_msg.format(elapsedtime, self.o.fdelay - elapsedtime))
                m['isRetry'] = False
                m['_deleteOnPost'] |= set(['isRetry'])
                worklist.failed.append(m)
                logger.debug('marked failed 3 file not old enough')
                continue

            logger.debug('appending to outgoing')
            outgoing.append(m)

        worklist.incoming = outgoing
