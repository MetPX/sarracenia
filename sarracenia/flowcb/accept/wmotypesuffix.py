"""
Plugin wmotypesuffix.py:
    Given the WMO-386 TT designator of a WMO file, file type suffix to the file name.
    Web browsers and modern operating systems may do *the right thing* if files have a recognizable suffix.

    http://www.wmo.int/pages/prog/www/ois/Operational_Information/Publications/WMO_386/AHLsymbols/TableA.html

    Status: proof of concept demonstrator... missing many TT's. please add!
    Tested with UNIDATA feeds, discrepancies:
    TableA says L is Aviation XML, but UNIDATA Feed, it is all GRIB.
    XW - should be CAP, but is GRIB.
    IX used by Americans for HDF, unsure if that is kosher/halal/blessed, but it is in the UNIDATA feed.

    IU/IS/IB are BUFR
    other type designators welcome... for example, GRIB isn't identified yet.
    default to .txt.

Usage:
    flowcb sarracenia.flowcb.accept.wmotypesuffix.WmoTypeSuffix
  
"""
import logging
from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)


class WmoTypeSuffix(FlowCB):
    def __init__(self, options):
        super().__init__(options,logger)

    def __find_type(self, TT):
        if TT[0] in ['G']: return '.grid'
        if TT in ['IX']: return '.hdf'
        if TT[0] in ['I']: return '.bufr'
        if TT[0] in ['K']: return '.crex'
        if TT in ['LT']: return '.iwxxm'
        if TT[0] in ['L']: return '.grib'
        if TT in ['XW']: return '.txt'
        if TT[0] in ['X']: return '.cap'
        if TT[0] in ['D', 'H', 'O', 'Y']: return '.grib'
        if TT[0] in ['E', 'P', 'Q', 'R']: return '.bin'
        return '.txt'

    def after_accept(self, worklist):
        for message in worklist.incoming:

            if 'fileOp' in message and 'directory' in message['fileOp']:
                continue

            type_suffix = self.__find_type(message['new_file'][0:2])
            ## FIXME confused as to how this could ever be true since find_type never returns "UNKNOWN"
            #if type_suffix == 'UNKNOWN':
            #    continue

            # file name already has suffix
            if message['new_file'][-len(type_suffix):] == type_suffix:
                continue

            message['new_file'] = message['new_file'] + type_suffix

            if 'rename' in message:
                message['rename'] += type_suffix

            if 'fileOp' in message and 'rename' in message['fileOp']:
                message['fileOp']['rename'] += type_suffix

            # TODO else -> worklist.rejected.append(message) ?? should this be happening at any point?


