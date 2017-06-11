#!/usr/bin/python3

"""
 A sample on_part plugin to perform virus scanning, using the ClamAV engine.

 Options:

 part_clamav_maxblock 3

 then when files are sent in more than 3 parts, only the first 3 will be scanned.
 if the option is not set, all blocks of files will be scanned.

 STATUS: FIXME.. not tested on multi-part files!

 requires a clamd binding package to be installed.
 on debian derived systems: 
    sudo apt-get install python3-pyclamd
 on others:
    pip3 install pyClamd

 blame: PS
"""

import os,stat,time

class PartClamAvScan(object): 

    def __init__(self,parent):
        import pyclamd
        self.av = pyclamd.ClamdAgnostic()
        print( "clam_scan on_part plugin initialized" )
  
    def perform(self,parent):
        logger = parent.logger
        msg    = parent.msg

        # it is possible to optimize scanning by not  ... FIXME! this is not tested. not sure how PS!
        if hasattr(parent,'part_clamav_maxblock'):
            if parent.current_block > parent.part_clamav_maxblock[0] :
               logger.info("part_clamav_scan scan skipped, too far into file %s" % (end-start,msg.new_file) )
               return True  

        # scanner wants an absolute path name... dunno why.
        if msg.new_file[0] != '/' : 
             scanfn= os.getcwd() + '/' + msg.new_file
        else:
             scanfn= msg.new_file 

        # worried about how long the scan will take.
        start=time.time()
        virus_found = self.av.scan_file(scanfn)
        end=time.time()

        if virus_found:
           logger.error("part_clamav_scan took %g not forwarding, virus detected in %s" % (end-start,msg.new_file) )
           return False
                   
        logger.info("part_clamav_scan took %g seconds, no viruses in %s" % (end-start,msg.new_file) )
        return True

partclamavscan = PartClamAvScan(self)
self.on_part = partclamavscan.perform

