#!/usr/bin/env python3
"""
dod_filter_wmo2msc.py is a do_download plugin script to convert WMO bulletins on local disk
to MSC internal format in an alternate tree.  It is analogous to sundew 'bulletin-file'.

STATUS: work in progress.  Doesn't really work yet. local testing works.

      Only tested standalone so far (see SUPPLEMENTARY INFO on how to do that.)

FIXME: The normal URL's announced would be HTTP, but how to get actual directory?
      do we require a separate announcement as file URL's  just add a substition?
      do we need a parameter to supply the document_root for the upstream?
      
FIXME: No uniquifier in the file names.
      According to WMO rules, should not be necessary.  MSC practice does not reflect that.

usage:

In a sr_sarra configuration:

msg_download_protocol 'http'
on_message msg_download
do_download do_filter_wmo2msc


NOTE: Look at the end of the file for SUPPLEMENTARY INFORMATION 
      including hints about debugging.

"""

import sys
import os
import re

class Xwmo2msc(object):

    def __init__(self,parent):
        self.trimre=re.compile(b" +\n")

    def replaceChar(self,oldchar,newchar):
        self.bintxt = self.bintxt.replace(bytearray(oldchar,'latin_1'),bytearray(newchar,'latin_1'))      

    def doSpecificProcessing(self):
        """doSpecificProcessing()

           Modify bulletins received from Washington via the WMO socket protocol.

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
        
        input_file = msg.urlstr.replace("download:/","")        

        print( 'reading file: %s ' % (input_file) )
        # read once to figure out headers and type.
        with open( input_file, 'rb' ) as s:
            self.bulletin = [ s.readline(), s.read(4) ]
        
        # read second time for the body in one string.
        with open( input_file, 'rb' ) as s:
            self.bintxt = s.read()
        
        
        AHLfn = (self.bulletin[0].replace(b' ',b'_').strip()).decode('ascii')
        msg.local_file = os.path.dirname(msg.local_file) + os.sep + AHLfn
                     
        
        
        if self.bulletin[1].lstrip()[:4] in [ 'BUFR', 'GRIB', '\211PNG' ]: 
            logger.debug( 'file %s -> binary %s' % (input_file, msg.local_file) )
            self.replaceChar('\r','')

        elif self.bulletin[0][:11] in [ 'SFUK45 EGRR' ]:
            # This file is encoded in an indecipherably non-standard format.
            logger.debug( 'file %s -> SKUK45 EGRR strangencoding %s' % (input_file, msg.local_file) )
            #self.replaceChar('\r','',2) replace only the first 2 carriage returns.
            self.bintxt = \
                self.bintxt.replace( bytearray('\r','latin_1'), bytearray('','latin_1'), 2)

        else:
            logger.debug( 'file %s -> alphanumeric %s' % (msg.local_file, AHLfn) )
            self.doSpecificProcessing()        
        
        d = open( msg.local_file, 'wb+') 
        d.write(self.bintxt)
        d.close()
        return True
        


if __name__ != '__main__':

    # real activation as a do_download filtering script.
    xwmo2msc  = Xwmo2msc(self)
    self.on_file = xwmo2msc.perform
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

The output files are named based based on the Abbreviated Header Line (AHL)
from first line of each input file. 

It operates on local files, One subscribes to a source messages that are already downloaded, 
and then this 'download' filter will produce a second tree of converted bulletins.

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
when a study was done over a few days in the mid 2000's, it was determined that approximately 6% of traffic on the GTS is carriage returns, which seems sad, but the formats are too entrenched to be changed.
(Hopefully) same logic ported to Sarracenia for use as a sarra plugin in 2017.

Adaptation of sundew code to sarracenia by Peter Silva - 2017/01 

"""
