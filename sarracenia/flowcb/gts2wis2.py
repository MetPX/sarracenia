import json
import logging
import os.path

from sarracenia.flowcb import FlowCB
from sarracenia.flowcb.gather import msg_dumps
import GTStoWIS2

logger = logging.getLogger(__name__)



class GTS2WIS2(FlowCB):

    def find_type(self, TT):
        """
            given the TT of a WMO AHL, return the corresponding file type suffix.
        """

        if TT[0] in ['G']: return '.grid'
        elif TT[0] in ['I']: return '.bufr'
        elif TT in ['IX']: return '.hdf'
        elif TT[0] in ['K']: return '.crex'
        elif TT in ['LT']: return '.iwxxm'
        elif TT[0] in ['L']: return '.grib'
        elif TT in ['XW']: return '.txt'
        elif TT[0] in ['X']: return '.cap'
        elif TT[0] in ['D', 'H', 'O', 'Y']: return '.grib'
        elif TT[0] in ['E', 'P', 'Q', 'R']: return '.bin'
        else: return '.txt'

    def __init__(self, options):

        # FIXME: should a logging module have a logLevel setting?
        #        just put in a cookie cutter for now...
        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, options.logLevel.upper()))
        else:
            logger.setLevel(logging.INFO)

        self.topic_builder=GTStoWIS2.GTStoWIS2()
        self.o = options


    def after_accept(self, worklist):

        new_incoming=[]

        for msg in worklist.incoming:

            # /20181218/UCAR-UNIDATA/WMO-BULLETINS/IX/21/IXTD99_KNES_182147_9d73fc80e12fca52a06bf41c716cd718

            # fix file name suffix.
            type_suffix = self.find_type(msg['new_file'][0:2] )

            # correct suffix if need be.
            if ( type_suffix != 'UNKNOWN' ) and ( msg['new_file'][-len(type_suffix):] != type_suffix ):
                msg['new_file'] += type_suffix
                if 'rename' in msg:
                    msg['rename'] += type_suffix

            # /20181218/UCAR-UNIDATA/WMO-BULLETINS/IX/21/IXTD99_KNES_182147_9d73fc80e12fca52a06bf41c716cd718.cap
            tpfx=msg['subtopic']
    
            # input has relpath=/YYYYMMDD/... + pubTime
            # need to move the date from relPath to BaseDir, adding the T hour from pubTime.
            new_baseSubDir=tpfx[0]+msg['pubTime'][8:11]
            t='.'.join(tpfx[0:2])+'.'+new_baseSubDir
            try:
                new_baseDir = msg['new_dir'] + os.sep + new_baseSubDir
                new_relDir = 'WIS' + os.sep + self.topic_builder.mapAHLtoTopic(msg['new_file'])
                msg['new_dir'] = new_baseDir + os.sep + new_relDir
                self.o.set_newMessageUpdatePaths( msg, new_baseDir + os.sep + new_relDir, msg['new_file'] )

            except Exception as ex:
                logger.error( "failed to map %s to a topic, skipped." % msg['new_file'] , exc_info=True )
                worklist.failed.append(msg)
                continue
    
            msg['_deleteOnPost'] |= set( [ 'from_cluster', 'sum', 'to_clusters' ] )
            new_incoming.append(msg)

        worklist.incoming=new_incoming 
