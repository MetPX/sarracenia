import sys, os, os.path, time, stat

"""
 This is a very specific script unlikely to be useful to other except as a code example.

 this renamer takes the complete px name : ccstn.dat
 and restructure it into an incoming pds  name : jicc.yyyymmddhhmm.ccstn.dat
                     2016-03-02 21:27:22,015 [INFO] 201 Downloaded : v02.report.20160302.MSC-CMC.METADATA.ccstn.dat:pull-ccstn:NCP:JICC:5:Codecon:20160302212706 20160302212715.58 http://ddi2.edm.ec.gc.ca/ 20160302/MSC-CMC/METADATA/ccstn.dat:pull-ccstn:NCP:JICC:5:Codecon:20160302212706 201 dms-op3-host3.edm.ec.gc.ca dms 6.955598 parts=1,55024600,1,0,0 sum=d,3da695f047174462ebe5d0352f4f8295 from_cluster=DDI.CMC source=metpx to_clusters=DDI.CMC,DDI.EDM rename=/apps/dms/dms-decoder-jicc/data/import/jicc.201603022127.ccstn.dat:pull-ccstn:NCP:JICC:5:Codecon:20160302212706 message=Downloaded 

 this renamer takes the complete px name :       http://ddi2.edm.ec.gc.ca/ 20160302/MSC-CMC/METADATA/ccstn.dat:pull-ccstn:NCP:JICC:5:Codecon:20160302212706
 and restructure it into an incoming pds  name : /apps/dms/dms-decoder-jicc/data/import/jicc.201603022127.ccstn.dat:pull-ccstn:NCP:JICC:5:Codecon:20160302212706   (jicc.yyyymmddhhmm.ccstn.dat )

"""


class Renamer(object):

      def __init__(self) :
          pass

      def perform(self,parent):
          import time

          if not 'ccstn.dat' in parent.msg.new_file : return True

          # build new name
          local_file = parent.msg.new_file
          datestr    = time.strftime('%Y%m%d%H%M',time.localtime())
          local_file = local_file.replace('ccstn.dat', 'jicc.' + datestr + '.ccstn.dat')

          # set in message (and headers for logging)
          parent.msg.new_file        = local_file
          parent.msg.headers['rename'] = local_file

          # on garde tous les messages
          return True

renamer=Renamer()
self.on_message=renamer.perform

