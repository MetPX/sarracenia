"""
   compresses the files and then writes their path to a SQLiteQueue. Requires the "persistqueue" module.
   usage:


    rxq_name <fname>
    flowCallback rxqueue_gzip.RxQueue_gzip

"""

import gzip
import logging
import os
import persistqueue
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class RxQueue_gzip(FlowCB):

    def __init__(self,options):

        super().__init__(options,logger)
        self.o.add_option( option='rxq_name', kind='str' )

    def on_start(self):
        if not hasattr(self.o,'rxq_name'):
            logger.error("Missing rxq_name parameter")
            return
        self.rxq = persistqueue.SQLiteQueue(self.o.rxq_name, auto_commit=True)

    def after_work(self, worklist):
        for msg in worklist.ok:
            fname = f'{msg["new_dir"]}/{msg["new_file"]}'
            gzname = f'{fname}.gz'
            tname = f'{gzname}.tmp'
            if os.path.exists(fname):
                # Only try this if the uncompressed file actually exists
                gzf = gzip.open(tname, 'wb')
                gzf.write(open(fname,'rb').read())
                gzf.close()
                os.rename(tname, gzname)
                os.unlink(fname)
                self.rxq.put( gzname )
            else:
                self.rxq.put( fname )

        return None
