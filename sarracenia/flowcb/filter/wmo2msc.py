r"""
wmo2msc.py is an on_message plugin script to convert WMO bulletins on local disk
to MSC internal format in an alternate tree.  It is analogous to Sundew's 'bulletin-file'.
Meant to be called as an sr_shovel plugin.

It prints an output line:

wmo2msc: <input_file> -> <output_file> (<detected format>)

usage:

Use the directory setting to know the root of tree where files are placed.
FIXME: well, likely what you really what is something like::

     <date>/<source>/dir1/dir2/dir3

     <date>/<source>/dir1/dir2/newdir4/...

     -- so Directory doesn't cut it.

In a sr_shovel configuration:: 

    directory /.... 
    callback filter.wmo2msc


Parameters:

* filter_wmo2msc_replace_dir  old,new

* filter_wmo2msc_uniquify hash|time|anything else
  - whether to add a string in addition to the AHL to make the filename unique.
  - hash - means apply a hash, so that the additional string is content based.
  - if time, add a suffix _YYYYMMDDHHMMSS_99999 which ensures file name uniqueness.
  - otherwise, no suffix will be added.
  - default: hash

* filter_wmo2msc_convert on|off
  if on, then traditional conversion to MSC-BULLETINS is done as per TANDEM/APPS & MetPX Sundew
  this involves \n as termination character, and other charater substitutions.

* filter_wmo2msc_tree  on|off
  if tree is off, files are just placed in destination directory.
  if tree is on, then the file is placed in a subdirectory tree, based on
  the WMO 386 AHL::

         TTAAii CCCC YYGGgg  ( example: SACN37 CWAO 300104 )
 
         TT = SA - surface observation.
         AA = CN - Canada ( but the AA depends on TT value, in many cases not a national code. )
         ii = 37 - a number.. there are various conventions, they are picked to avoid duplication.
     
  The first line of the file is expected to contain an AHL. and when we build a tree
  from it, we build it as follows::

      TT/CCCC/GG/TTAAii_CCCC_YYGGgg_<uniquify>

  assuming tree=on, uniquify=hash:

     SA/CWAO/01/SACN37_CWAO_300104_1c699da91817cc4a84ab19ee4abe4e22

NOTE: Look at the end of the file for SUPPLEMENTARY INFORMATION 
      including hints about debugging.

"""

import sys
import os
import re
import time
import hashlib
import logging
import random
from sarracenia.flowcb import FlowCB

logger = logging.getLogger('__name__')


class Wmo2msc(FlowCB):
    def __init__(self, options):
        super().__init__(options,logger)

        self.o.add_option( 'filter_wmo2msc_uniquify', 'str', 'hash' )
        self.o.add_option( 'filter_wmo2msc_replace_dir', 'str' )
        self.o.add_option( 'filter_wmo2msc_treeify', 'flag', True )
        self.o.add_option( 'filter_wmo2msc_convert', 'flag', True )

        if not hasattr(self.o, 'filter_wmo2msc_replace_dir'):
            logger.error("filter_wmo2msc_replace_dir setting is mandatory")
            return

        (self.o.filter_olddir, self.o.filter_newdir) = self.o.filter_wmo2msc_replace_dir.split(',')

        logger.info("filter_wmo2msc old-dir=%s, newdir=%s" %
                    (self.o.filter_olddir, self.o.filter_newdir))

        self.trimre = re.compile(b" +\n")

    def replaceChar(self, oldchar, newchar):
        """
           replace all occurrences of oldchar by newchar in the the message byte stream.
           started as a direct copy from sundew of routine with same name in bulletin.py
           - the storage model is a bit different, we store the entire message as one bytearray.
           - sundew stored it as a series of lines, so replaceChar implementation changed.

        """
        self.bintxt = self.bintxt.replace(bytearray(oldchar, 'latin_1'),
                                          bytearray(newchar, 'latin_1'))

    def doSpecificProcessing(self):
        """doSpecificProcessing()

           Modify bulletins received from Washington via the WMO socket protocol.
           started as a direct copy from sundew of routine with same name in bulletinManagerWmo.py
      
           - encode/decode, and binary stuff came because of python3
        """

        ahl2 = self.bulletin[0][:2].decode('ascii')
        ahl4 = self.bulletin[0][:4].decode('ascii')

        if ahl2 in [
                'SD', 'SO', 'WS', 'SR', 'SX', 'FO', 'WA', 'AC', 'FA', 'FB',
                'FD'
        ]:
            self.replaceChar('\x1e', '')

        if ahl2 in ['SR', 'SX']:
            self.replaceChar('~', '\n')

        if ahl2 in ['UK']:
            self.replaceChar('\x01', '')

        if ahl4 in ['SICO']:
            self.replaceChar('\x01', '')

        if ahl2 in ['SO', 'SR']:
            self.replaceChar('\x02', '')

        if ahl2 in ['SX', 'SR', 'SO']:
            self.replaceChar('\x00', '')

        if ahl2 in ['SX']:
            self.replaceChar('\x11', '')
            self.replaceChar('\x14', '')
            self.replaceChar('\x19', '')
            self.replaceChar('\x1f', '')

        if ahl2 in ['SR']:
            self.replaceChar('\b', '')
            self.replaceChar('\t', '')
            self.replaceChar('\x1a', '')
            self.replaceChar('\x1b', '')
            self.replaceChar('\x12', '')

        if ahl2 in ['FX']:
            self.replaceChar('\x10', '')
            self.replaceChar('\xf1', '')

        if ahl2 in ['WW']:
            self.replaceChar('\xba', '')

        if ahl2 in ['US']:
            self.replaceChar('\x18', '')

        if ahl4 in ['SXUS', 'SXCN', 'SRCN']:
            self.replaceChar('\x7f', '?')

        if ahl4 in ['SRCN']:
            self.replaceChar('\x0e', '')
            self.replaceChar('\x11', '')
            self.replaceChar('\x16', '')
            self.replaceChar('\x19', '')
            self.replaceChar('\x1d', '')
            self.replaceChar('\x1f', '')

        if ahl4 in ['SXVX', 'SRUS', 'SRMT']:
            self.replaceChar('\x7f', '')

        self.replaceChar('\r', '')

        if ahl2 in ['SA', 'SM', 'SI', 'SO', 'UJ', 'US', 'FT']:
            self.replaceChar('\x03', '')

        #trimming of trailing blanks.
        lenb = len(self.bintxt)
        self.bintxt = self.trimre.sub(b"\n", self.bintxt)
        if len(self.bintxt) < lenb:
            print('Trimmed %d trailing blanks!' % (lenb - len(self.bintxt)))

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:
            if message['baseUrl'] != 'file:':
                logger.error(
                    'filter_wmo2msc needs local files invalid url: %s ' %
                    (message['baseUrl'] + message['relPath']))
                worklist.rejected.append(message)
                continue

            input_file = message['relPath']

            # read once to get headers and type.

            logger.debug('filter_wmo2msc reading file: %s' % (input_file))

            with open(input_file, 'rb') as s:
                self.bulletin = [s.readline(), s.read(4)]

            AHLfn = (self.bulletin[0].replace(b' ',
                                              b'_').strip()).decode('ascii')

            if len(AHLfn) < 18:
                logger.error(
                    'filter_wmo2msc: not a WMO bulletin, malformed header: (%s)'
                    % (AHLfn))
                worklist.rejected.append(message)
                continue

            # read second time for the body in one string.
            with open(input_file, 'rb') as s:
                self.bintxt = s.read()

            logger.debug('filter_wmo2msc read twice: %s ' % (input_file))

            # Determine file format (fmt) and apply transformation.
            if self.bulletin[1].lstrip()[:4] in ['BUFR', 'GRIB', '\211PNG']:
                fmt = 'wmo-binary'
                self.replaceChar('\r', '')
            elif self.bulletin[0][:11] in ['SFUK45 EGRR']:
                # This file is encoded in an indecipherably non-standard format.
                fmt = 'unknown-binary'

                #self.replaceChar('\r','',2) replace only the first 2 carriage returns.
                self.bintxt = self.bintxt.replace(bytearray('\r', 'latin_1'),
                                                  bytearray('', 'latin_1'), 2)
            else:
                fmt = 'wmo-alphanumeric'
                if self.o.filter_wmo2msc_convert:
                    self.doSpecificProcessing()

            # apply 'd' checksum (md5)

            s = hashlib.md5()
            s.update(self.bintxt)
            sumstr = ''.join(format(x, '02x') for x in s.digest())

            # Determine local file name.
            if self.o.filter_wmo2msc_uniquify in ['time']:

                AHLfn += '_' + time.strftime( "%Y%m%d%H%M%S", time.gmtime(time.time()) ) + \
                         '_%05d' % random.randint(0,9999)
            elif self.o.filter_wmo2msc_uniquify in ['hash']:
                #AHLfn += '_%s' % ''.join( format(x, '02x') for x in s.digest() )
                AHLfn += '_' + sumstr

            if self.o.filter_wmo2msc_treeify:
                d = os.path.dirname(input_file)
                logger.debug('filter_wmo2msc check %s start match: %s' %
                             (d, self.o.filter_olddir))
                d = d.replace(self.o.filter_olddir, self.o.filter_newdir)
                logger.debug('filter_wmo2msc check %s after replace' % (d))
                if not os.path.isdir(d):
                    os.makedirs(d, self.o.permDirDefault, True)

                d = d + os.sep + self.bulletin[0][0:2].decode('ascii')
                d = d + os.sep + self.bulletin[0][7:11].decode('ascii')
                logger.debug('filter_wmo2msc check %s' % (d))
                if not os.path.isdir(d):
                    os.makedirs(d, self.o.permDirDefault, True)

                d = d + os.sep + self.bulletin[0][14:16].decode('ascii')
                logger.debug('filter_wmo2msc check %s' % (d))
                if not os.path.isdir(d):
                    os.makedirs(d, self.o.permDirDefault, True)

                local_file = d + os.sep + AHLfn
            else:
                local_file = self.o.currentDir + os.sep + AHLfn

            # write the data.
            fileOK = False

            if not self.o.filter_wmo2msc_convert:
                try:
                    os.link(input_file, local_file)
                    fileOK = True
                except:
                    pass

            if self.o.filter_wmo2msc_convert or not fileOK:
                d = open(local_file, 'wb+')
                d.write(self.bintxt)
                d.close()

            logger.debug('filter_wmo2msc %s -> %s (%s)' %
                         (input_file, local_file, fmt))

            # set how the file will be announced

            baseDir = self.o.base_dir
            if baseDir == None: baseDir = self.o.post_base_dir

            relPath = local_file
            if baseDir != None: relPath = local_file.replace(baseDir, '')

            baseUrl = 'file:'
            # from tolocal.py if used
            if 'savedUrl' in message.keys(): baseUrl = message['savedUrl']
            # from tolocalfile.py if used
            if 'saved_baseUrl' in message.keys():
                baseUrl = message['saved_baseUrl']

            relPath = relPath.replace('//', '/')
            logger.debug('filter_wmo2msc relPath %s' % relPath)

            message['set_topic'](self.o.topic_prefix, relPath)
            #message['set_notice'](baseUrl, relPath)
            message['baseUrl'] = baseUrl
            message['relPath'] = relPath
            new_incoming.append(message)
        worklist.incoming = new_incoming


"""

SUPPLEMENTARY INFORMATION

SUNDEW COMPATIBILITY:   This script is the sarra version of a 'bulletin-file' receiver.

dod_filter_wmo2msc.py is a do_download plugin script used with sr_sarra to convert
World Meteorological Organisation (WMO) standard (See WMO-386 and WMO-306) bulletins 
into the similar but different internal format used by the Meteorological Service of 
Canada (MSC.)

transformation of bulletins is based on detecting the format by reading the first 
line of the file, and the first four bytes of after the first line.  detected format 
is one of:
   wmo-binary: GRIB, BUFR, or PNG, which require carriage returns to be removed ?
   wmo-alpha:  extensive filtering.
   unknown-binary: unknown format, remove only carriage returns from AHL.

The file is read entirely into memory as the WMO standard specifies a maximum message
size of 500,000 bytes with no segmentation and re-assembly being ruled out.

The output files are named based based on the Abbreviated Header Line (AHL)
from first line of each input file. 

It operates on local files.  One subscribes to a source messages that are already 
downloaded, then this 'download' filter produces a second tree of converted bulletins.

STANDALONE DEBUGGING:
Instead of being used purely as a plugin, the script can also be invoked directly.
In that case, if given no arguments, it will read the current working directory,
looking for files that start with a digit (which is what NWS feed provides.)
and feed those file for processing.

To process a particular files, go into the directory containing the file, and supply
the file names as an arguments.


MSC Format description:

Given a file containing a single WMO 386 / WMO 306 conformant encoded bulletin,
produce an MSC formatted one. Most obvious change is the line termination, but there
are other subtle differences learned through pain, over a year or two of parallel testing.

The MSC format is simply the output of the (late lamented Tandem computer system
which was the bulletin switch from the 80's until 2007) The internal 'AM' circuits
used by the Meteorological Service of Canada used only line feed for termination, as
is standard in Unix/Linux land, and not two carriage returns followed by a line feed required
by the ancient tomes of the WMO.

This processing was determined by blackbox reverse engineering for MetPX sundew in the mid-2000's.
when a study was done over a few days in the mid 2000's, it was determined that approximately 
6% of traffic on the GTS is carriage returns, which seems sad, but the formats are too entrenched 
to be changed.  

Hopefully identical logic has been ported to Sarracenia for use as a sarra plugin in 2017.

Adaptation of sundew code to sarracenia by Peter Silva - 2017/01 

"""
