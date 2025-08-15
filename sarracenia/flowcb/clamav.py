"""
 A sample on_part plugin to perform virus scanning, using the ClamAV engine.

 requires a clamd binding package to be installed. On debian derived systems:: 

    sudo apt-get install python3-pyclamd

 on others::

    pip3 install pyclamd

 author: Peter Silva
"""

import logging
import os
import stat
import time

from sarracenia import nowflt
import sarracenia
from sarracenia.flowcb import FlowCB

#
# Support for features inventory mechanism.
#
from sarracenia.featuredetection import features

features['clamd'] = { 'modules_needed': [ 'pyclamd' ], 'Needed': True,
        'lament' : 'cannot use clamd to av scan files transferred',
        'rejoice' : 'can use clamd to av scan files transferred' }

try:
    import pyclamd
    features['clamd']['present'] = True
except:
    features['clamd']['present'] = False



logger = logging.getLogger(__name__)


class Clamav(FlowCB):
    """
       Invoke ClamAV anti-virus scanning on files as they pass through a data pump.
       when it is invoked depends on the component it is used from.

       from a sender, post, or poll, the scan should stop processing prior
       to the transfer.

       for other components, subsscribers that download, it needs to take place
       after downloading.

    """
    def __init__(self, options) -> None:

        super().__init__(options,logger)

        self.metric_scanned = 0
        self.metric_hits = 0
       
        if sarracenia.features['pyclamd']['present']:
            import pyclamd
            self.av = pyclamd.ClamdAgnostic()
            print("clam_scan on_part plugin initialized")

    def avscan_hit(self, scanfn) -> bool:

        # worried about how long the scan will take.
        start = nowflt()
        virus_found = self.av.scan_file(scanfn)
        end = nowflt()
        self.metric_scanned += 1

        if virus_found:
            logger.error(
                "part_clamav_scan took %g not forwarding, virus detected in %s"
                % (end - start, scanfn))
            self.metric_hits += 1
            return False

        logger.info("part_clamav_scan took %g seconds, no viruses in %s" %
                    (end - start, scanfn))
        return True

    def after_accept(self, worklist) -> None:
        if self.o.component in ['sender', 'post', 'watch']:
            new_incoming = []
            for m in worklist.incoming:
                scanfn = m['new_dir'] + os.sep + m['new_file']
                logger.info(f'scanning: {scanfn}')
                if self.avscan_hit(scanfn):
                    worklist.rejected.append(m)
                else:
                    new_incoming.append(m)
            worklist.incoming = new_incoming

    def after_work(self, worklist) -> None:
        if self.o.component in ['subscribe', 'sarra']:
            new_ok = []
            for m in worklist.ok:
                scanfn = m['new_dir'] + os.sep + m['new_file']
                logger.info(f'scanning: {scanfn}')
                if self.avscan_hit(scanfn):
                    worklist.rejected.append(m)
                else:
                    new_ok.append(m)
            worklist.ok = new_ok

    def on_housekeeping(self):
        logger.info(
            f'files scanned {self.metric_scanned}, hits: {self.metric_hits} ')
        self.metric_scanned = 0
        self.metric_hits = 0
