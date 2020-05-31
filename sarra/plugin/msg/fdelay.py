#!/usr/bin/python3
"""
  This plugin delays processing of messages by *message_delay* seconds


  sarra.plugin.msg.fdelay 30
  import sarra.plugin.msg.fdelay.FDelay


  every message will be at least 30 seconds old before it is forwarded by this plugin.
  in the meantime, the message is placed on the retry queue by marking it as failed.

"""
import logging

from sarra.plugin import Plugin
from sarra.sr_util import timestr2flt, nowflt

logger = logging.getLogger( __name__ )


class FDelay(Plugin):
    def __init__(self, options):

        self.o = options

        logger.error('hoho! FIXME init')
        #parent.declare_option('fdelay')
        if hasattr(self.o, 'msg_fdelay'):
            self.o.fdelay = self.o.msg_fdelay 

        if hasattr(self.o, 'fdelay') and type(self.o.fdelay) is list:
            self.fdelay = int(self.o.fdelay[0])
        elif not hasattr(self.o, 'fdelay'):
            self.o.fdelay = 60



    def on_messages(self, worklist):
        import os
        import stat

        # Prepare msg delay test
        outgoing=[]
        for m in worklist.incoming:
            if m['integrity']['method'] == 'remove':
                # 'remove' msg will be removed by itself
                worklist.rejected.append(m)
                continue

            # Test msg delay
            elapsedtime = nowflt() - timestr2flt(m['pubTime'])
            if elapsedtime < self.o.fdelay:
                dbg_msg = "message not old enough, sleeping for {:.3f} seconds"
                logger.debug(dbg_msg.format(elapsedtime, self.o.fdelay - elapsedtime))
                m['isRetry'] = False
                message['_deleteOnPost'].append( 'isRetry' )
                worklist.failed.append(m)
                continue

            # Prepare file delay test
            if '/cfr/' in m['new_dir']:
                f = os.path.join( m['new_dir'], m['new_file'] )
            else:
                f = m['relPath']
            if not os.path.exists(f):
                logger.error("did not find file {}".format(f))
                worklist.failed.append(m)
                continue

            # Test file delay
            filetime = os.stat(f)[stat.ST_MTIME]
            elapsedtime = nowflt() - filetime
            if elapsedtime < self.o.fdelay:
                dbg_msg = "file not old enough, sleeping for {:.3f} seconds"
                logger.debug(dbg_msg.format(elapsedtime, self.o.fdelay - elapsedtime))
                m['isRetry'] = False
                message['_deleteOnPost'].append( 'isRetry' )
                worklist.failed.append(m)
                continue

            outgoing.append(m)

        worklist.incoming=outgoing
