import json
import logging
import os.path
import re

from sarracenia.flowcb import FlowCB
import GTStoWIS2
import uuid

logger = logging.getLogger(__name__)


class Wistree(FlowCB):
    """
       Given a file whose name begins with a WMO GTS AHL
       (World Meteorological Organization, Global Telecommunications' System, Abbreviated Header Line)
       map the given AHL to a WIS-compliant topic tree. (WIS-WMO Information Service.)

       So when downloading, instead of writing the file to a single directory, it is
       written to a WIS-compliant folder structure.
    """
    def __init__(self, options):

        super().__init__(options,logger)
        self.topic_builder = GTStoWIS2.GTStoWIS2()
        self.date_pattern = re.compile("^[0-9]{8}$")

    def after_accept(self, worklist):

        new_incoming = []

        for msg in worklist.incoming:

            # /20181218/UCAR-UNIDATA/WMO-BULLETINS/IX/21/IXTD99_KNES_182147_9d73fc80e12fca52a06bf41c716cd718

            try:
                # fix file name suffix.
                type_suffix = self.topic_builder.mapAHLtoExtension(
                    msg['new_file'][0:2])

                # /20181218/UCAR-UNIDATA/WMO-BULLETINS/IX/21/IXTD99_KNES_182147_9d73fc80e12fca52a06bf41c716cd718.cap
                tpfx = msg['subtopic']

                msg['id']= str(uuid.uuid4())

                # input has relpath=/YYYYMMDD/... + pubTime
                # need to move the date from relPath to BaseDir, adding the T hour from pubTime.
                if self.date_pattern.match(tpfx[0]):
                    new_baseSubDir = tpfx[0] + msg['pubTime'][8:11]
                else:
                    # or default to using pubTime...
                    new_baseSubDir = msg['pubTime'][0:11]


                new_baseDir = msg['new_dir'] + os.sep + new_baseSubDir
                new_relDir = str(uuid.uuid4()).replace('-','/')
                msg['topic'] = 'WIS' + os.sep + self.topic_builder.mapAHLtoTopic( msg['new_file'])
                msg['new_file'] = str(uuid.uuid4())

                if msg['new_file'][-len(type_suffix):] != type_suffix:
                    new_file = msg['new_file'] + type_suffix
                else:
                    new_file = msg['new_file']

                if type_suffix == 'bufr' :
                    mtype='application/x-bufr'
                elif type_suffix == 'grib':
                    mtype='application/x-grib'
                else:
                    mtype='unknown'

                msg['links'] =  { "href": msg['baseUrl'] + '/' + msg['relPath'], 'rel':'canonical', 'type': mtype }
                msg.updatePaths(self.o, new_baseDir + os.sep + new_relDir,
                                new_file)

            except Exception as ex:
                logger.error("failed to map %s to a topic, skipped." %
                             msg['new_file'],
                             exc_info=True)
                worklist.failed.append(msg)
                continue

            # remove some legacy fields in the messages, to de-clutter.
            msg['_deleteOnPost'] |= set([
                'from_cluster',
                'sum',
                'to_clusters',
                'sundew_extension',
                'filename',
                'source',
            ])
            new_incoming.append(msg)

        worklist.incoming = new_incoming
