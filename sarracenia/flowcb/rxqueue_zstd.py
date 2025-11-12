"""
   compresses the files using zstd and then writes their path to a SQLiteQueue. Requires the "persistqueue" module.
   usage:


    rxq_name <fname>
    flowCallback rxqueue_zstd.RxQueue_zstd

"""

# This module is only available in Python 3.14
from compression import zstd
import logging
import os
import persistqueue
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)


class RxQueue_zstd(FlowCB):

    def __init__(self, options):

        super().__init__(options, logger)
        self.o.add_option(option='rxq_name', kind='str')
        self.o.add_option(option='zstd_level', kind='int', default_value=7)

    def on_start(self):
        if not hasattr(self.o, 'rxq_name'):
            logger.error("Missing rxq_name parameter")
            return
        self.rxq = persistqueue.SQLiteQueue(self.o.rxq_name, auto_commit=True)

        self.compression_level = self.o.zstd_level

    def after_work(self, worklist):
        for msg in worklist.ok:
            fname = f'{msg["new_dir"]}/{msg["new_file"]}'
            zstname = f'{fname}.zst'
            tname = f'{zstname}.tmp'
            if os.path.exists(fname):
                # Only try this if the uncompressed file actually exists
                with open(fname, 'rb') as input_file:
                    data = input_file.read()
                
                compressed_data = zstd.compress(data, self.compression_level)
                
                with open(tname, 'wb') as output_file:
                    output_file.write(compressed_data)
                
                os.rename(tname, zstname)
                os.unlink(fname)
                self.rxq.put(zstname)
            else:
                self.rxq.put(fname)

        return None