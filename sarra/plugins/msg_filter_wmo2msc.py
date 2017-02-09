#!/usr/bin/env python3

"""
msg_filter_wmo2msc.py is an on_message plugin script to convert WMO bulletins on local disk
to MSC internal format in an alternate tree.  It is analogous to sundew 'bulletin-file'.
Meant to be called as an sr_shovel plugin.

It prints an output line:

filter_wmo2msc: <input_file> -> <output_file> (<detected format>)

usage:
     Use the directory setting to know the root of tree where files are placed.
     FIXME: well, likely what you really what is something like:

     <date>/<source>/dir1/dir2/dir3

     <date>/<source>/dir1/dir2/newdir4/...

          -- so Directory doesn't cut it.

In a sr_shovel configuration:

directory /.... 
on_message msg_filter_wmo2msc


Parameters:

  msg_filter_wmo2msc_replace_dir  old,new

  msg_filter_wmo2msc_bad_tac SFUK45 EGRR,FPCN11 CWAO
     - When receiving bulletins with the given Abbreviated Headers, force their type to 'unknown binary'
     - list of AHL's comma separated.
     - default: SFUK45 EGRR

  msg_filter_wmo2msc_uniquify hash|time|anything else
     - whether to add a string in addition to the AHL to make the filename unique.
     - hash - means apply a hash, so that the additional string is content based.
     - if time, add a suffix _YYYYMMDDHHMMSS_99999 which ensures file name uniqueness.
     - otherwise, no suffix will be added.
     - default: hash


NOTE: Look at the end of the file for SUPPLEMENTARY INFORMATION 
      including hints about debugging.

"""

import sys
import os
import re

class Xwmo2msc(object):

    def __init__(self,parent):

        parent.uniquify='hash'
        if not hasattr(parent,'msg_filter_wmo2msc_replace_dir'):
           parent.logger.error("msg_filter_wmo2msc_replace_dir setting is mandatory")
           return

        ( parent.filter_olddir, parent.filter_newdir ) = \
                parent.msg_filter_wmo2msc_replace_dir[0].split(',')

        parent.logger.info( "msg_filter_wmo2msc old-dir=%s, newdir=%s" \
               % ( parent.filter_olddir, parent.filter_newdir ) )
        if hasattr(parent,'msg_filter_wmo2msc_uniquify'):
           parent.logger.info('msg_filter_wmo2msc, override' )
           parent.uniquify = parent.msg_filter_wmo2msc_uniquify[0]

        if hasattr(parent,'msg_filter_wmo2msc_bad_ahls'):
            parent.bad_ahl= [ ]
            for i in parent.msg_filter_wmo2msc_bad_ahls:
               for j in i.split(','):
                   parent.bad_ahl.append(j.replace('_',' '))
        else:
            parent.bad_ahl= [ 'SFUK45 EGRR' ]

        parent.treeify=False
        if hasattr(parent,'msg_filter_wmo2msc_tree'):
           parent.treeify=parent.isTrue(parent.msg_filter_wmo2msc_tree[0])


        self.trimre=re.compile(b" +\n")
        parent.logger.info('msg_filter_wmo2msc initialized, uniquify=%s bad_ahls=%s' % \
           ( parent.uniquify, parent.bad_ahl ) )


    def replaceChar(self,oldchar,newchar):
        """
           replace all occurrences of oldchar by newchar in the the message byte stream.
           started as a direct copy from sundew of routine with same name in bulletin.py
           - the storage model is a bit different, we store the entire message as one bytearray.
           - sundew stored it as a series of lines, so replaceChar implementation changed.

        """
        self.bintxt = self.bintxt.replace(bytearray(oldchar,'latin_1'),bytearray(newchar,'latin_1'))      

    def doSpecificProcessing(self):
        """doSpecificProcessing()

           Modify bulletins received from Washington via the WMO socket protocol.
           started as a direct copy from sundew of routine with same name in bulletinManagerWmo.py
      
           - encode/decode, and binary stuff came because of python3
        """

        ahl2=self.bulletin[0][:2].decode('ascii')
        ahl4=self.bulletin[0][:4].decode('ascii')

        if ahl2 in ['SD','SO','WS','SR','SX','FO','WA','AC','FA','FB','FD']:
            self.replaceChar('\x1e','')

        if ahl2 in ['SR','SX']:
            self.replaceChar('~','\n')

        if ahl2 in ['UK']:
            self.replaceChar('\x01','')

        if ahl4 in ['SICO']:
            self.replaceChar('\x01','')

        if ahl2 in ['SO','SR']:
            self.replaceChar('\x02','')

        if ahl2 in ['SX','SR','SO']:
            self.replaceChar('\x00','')

        if ahl2 in ['SX']:
            self.replaceChar('\x11','')
            self.replaceChar('\x14','')
            self.replaceChar('\x19','')
            self.replaceChar('\x1f','')

        if ahl2 in ['SR']:
            self.replaceChar('\b','')
            self.replaceChar('\t','')
            self.replaceChar('\x1a','')
            self.replaceChar('\x1b','')
            self.replaceChar('\x12','')

        if ahl2 in ['FX']:
            self.replaceChar('\x10','')
            self.replaceChar('\xf1','')

        if ahl2 in ['WW']:
            self.replaceChar('\xba','')

        if ahl2 in ['US']:
            self.replaceChar('\x18','')

        if ahl4 in ['SXUS','SXCN','SRCN']:
            self.replaceChar('\x7f','?')

        if ahl4 in ['SRCN']:
            self.replaceChar('\x0e','')
            self.replaceChar('\x11','')
            self.replaceChar('\x16','')
            self.replaceChar('\x19','')
            self.replaceChar('\x1d','')
            self.replaceChar('\x1f','')

        if ahl4 in ['SXVX','SRUS','SRMT']:
            self.replaceChar('\x7f','')

        self.replaceChar('\r','')


        if ahl2 in ['SA','SM','SI','SO','UJ','US','FT']:
            self.replaceChar('\x03','')

        #trimming of trailing blanks.
        lenb=len(self.bintxt)
        self.bintxt = self.trimre.sub(b"\n",self.bintxt)
        if len(self.bintxt) < lenb:
           print('Trimmed %d trailing blanks!' % (lenb - len(self.bintxt)) )


    def perform(self,parent):
        logger = parent.logger
        msg    = parent.msg

        if msg.urlstr[0:5] != 'file:' :
            logger.error( 'filter_wmo2msc needs local files invalid url: %s ' % (msg.urlstr) )
            return False

        input_file = msg.urlstr.replace("file:","")        

        # read once to get headers and type.

        logger.debug( 'filter_wmo2msc reading file: %s' % (msg.urlstr) )

        with open( input_file, 'rb' ) as s:
            self.bulletin = [ s.readline(), s.read(4) ]
        
        AHLfn = (self.bulletin[0].replace(b' ',b'_').strip()).decode('ascii')

        if len(AHLfn) < 18:
            logger.error( 'filter_wmo2msc: not a WMO bulletin, malformed header: (%s)' % (AHLfn) )
            return False

        # read second time for the body in one string.
        with open( input_file, 'rb' ) as s:
            self.bintxt = s.read()

        logger.debug( 'filter_wmo2msc read twice: %s ' % (input_file) )
        
        # Determine file format (fmt) and apply transformation.
        if self.bulletin[1].lstrip()[:4] in [ 'BUFR', 'GRIB', '\211PNG' ]: 
            fmt='wmo-binary'
            self.replaceChar('\r','')
        elif self.bulletin[0][:11] in [ 'SFUK45 EGRR' ]:
            # This file is encoded in an indecipherably non-standard format.
            fmt='unknown-binary'

            #self.replaceChar('\r','',2) replace only the first 2 carriage returns.
            self.bintxt = \
                self.bintxt.replace( bytearray('\r','latin_1'), bytearray('','latin_1'), 2)
        else:
            fmt='wmo-alphanumeric'
            self.doSpecificProcessing()        
        
        # apply 'd' checksum (md5)
        import hashlib
        s = hashlib.md5()
        s.update(self.bintxt)
        sumstr= ''.join( format(x, '02x') for x in s.digest() )

        # Determine local file name.
        if parent.uniquify in [ 'time' ]:
            import time
            AHLfn += '_' + time.strftime( "%Y%m%d%H%M%S", time.gmtime(time.time()) ) + \
                     '_%05d' % random.randint(0,9999)
        elif parent.uniquify in [ 'hash' ]:
            #AHLfn += '_%s' % ''.join( format(x, '02x') for x in s.digest() )
            AHLfn += '_' + sumstr

        if parent.treeify :
            #d = parent.currentDir + os.sep + self.bulletin[0][0:2].decode('ascii') 
            d = os.path.dirname(input_file)
            logger.info( 'filter_wmo2msc check %s start match: %s' % (d, parent.filter_olddir) )
            d = d.replace( parent.filter_olddir, parent.filter_newdir )
            logger.info( 'filter_wmo2msc check %s after replace' % (d) )
            if not os.path.isdir( d ):
                os.mkdir( d, parent.chmod_dir ) 

            d = d + os.sep + self.bulletin[0][2:4].decode('ascii') 
            logger.info( 'filter_wmo2msc check %s' % (d) )
            if not os.path.isdir( d ):
                os.mkdir( d, parent.chmod_dir ) 

            d = d + os.sep + self.bulletin[0][14:16].decode('ascii') 
            logger.info( 'filter_wmo2msc check %s' % (d) )
            if not os.path.isdir( d ):
                os.mkdir( d, parent.chmod_dir ) 

            local_file = d + os.sep + AHLfn
        else:
            local_file = parent.currentDir + os.sep + AHLfn

        # write the data.
        d = open( local_file, 'wb+') 
        d.write(self.bintxt)
        d.close()

        logger.info( 'filter_wmo2msc %s -> %s (%s)' % (input_file, local_file, fmt) )

        # change the file being announced.
        parent.msg.set_file( local_file, 'd,' + sumstr )

        return True


if __name__ != '__main__':

    # real activation as a do_download filtering script.
    xwmo2msc  = Xwmo2msc(self)
    self.on_message = xwmo2msc.perform

else:
    
    class TestLogger:
        def silence(self,str):
            pass
    
        def __init__(self):
            self.debug   = print
            self.error   = print
            self.info    = print
            self.warning = print
    
    
    class TestMessage():
    
        def __init__(self,fname,dest):
            self.urlstr = "download://" + fname
            self.local_file = dest + os.sep + 'hoho'
            self.headers = {}
    
    class TestParent(object):
    
        def __init__(self,fname):
            self.msg= TestMessage(fname,'/tmp/dest/')
            self.logger=TestLogger()
            pass
    
    if len(sys.argv) > 1:
       l = sys.argv[1:] 
    else:
       l = os.listdir()
    
    for f in l:
    
        if f[0].isdigit():
            testparent=TestParent( os.getcwd() + os.sep + f)
            xwmo2msc  = Xwmo2msc(testparent)
            xwmo2msc.perform(testparent)
    
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
