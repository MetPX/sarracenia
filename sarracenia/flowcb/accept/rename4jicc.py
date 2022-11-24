import sys, os, os.path, time, stat
"""
Plugin rename4jicc.py:
    This is a very specific script unlikely to be useful to other except as a code example.
    
Example:    
    This renamer takes the complete px name : ccstn.dat
    and restructures it into an incoming pds  name : jicc.yyyymmddhhmm.ccstn.dat
                        2016-03-02 21:27:22,015 [INFO] 201 Downloaded : v02.report.20160302.MSC-CMC.METADATA.ccstn.dat:pull-ccstn:NCP:JICC:5:Codecon:20160302212706 20160302212715.58 http://ddi2.edm.ec.gc.ca/ 20160302/MSC-CMC/METADATA/ccstn.dat:pull-ccstn:NCP:JICC:5:Codecon:20160302212706 201 dms-op3-host3.edm.ec.gc.ca dms 6.955598 parts=1,55024600,1,0,0 sum=d,3da695f047174462ebe5d0352f4f8295 from_cluster=DDI.CMC source=metpx to_clusters=DDI.CMC,DDI.EDM rename=/apps/dms/dms-decoder-jicc/data/import/jicc.201603022127.ccstn.dat:pull-ccstn:NCP:JICC:5:Codecon:20160302212706 message=Downloaded 
    
    This renamer takes the complete px name :       http://ddi2.edm.ec.gc.ca/ 20160302/MSC-CMC/METADATA/ccstn.dat:pull-ccstn:NCP:JICC:5:Codecon:20160302212706
    and restructures it into an incoming pds  name : /apps/dms/dms-decoder-jicc/data/import/jicc.201603022127.ccstn.dat:pull-ccstn:NCP:JICC:5:Codecon:20160302212706   (jicc.yyyymmddhhmm.ccstn.dat )

Usage:
    flowcb sarracenia.flowcb.accept.rename4jicc.Rename4Jicc
"""

import logging
import time
from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)


class Rename4Jicc(FlowCB):
    def __init__(self, options):
        self.o = options

    def after_accept(self, worklist):
        for message in worklist.incoming:

            if not 'ccstn.dat' in message['new_file']:
                new_incoming.append(message)
                continue
            # build new name
            local_file = message['new_file']
            datestr = time.strftime('%Y%m%d%H%M', time.localtime())
            local_file = local_file.replace('ccstn.dat',
                                            'jicc.' + datestr + '.ccstn.dat')

            # set in message (and headers for logging)
            message['new_file'] = local_file

            # dont use this... new_file is where the file will be downloaded... so need to keep a rename in headers
            #message['headers']['rename'] = local_file
