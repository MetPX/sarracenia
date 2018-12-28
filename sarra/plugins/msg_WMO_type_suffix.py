
"""
Given the WMO-386 TT designator of a WMO file, file type suffix to the file name.
Web browsers and modern operating systems may do *the right thing* if files have a recognizable suffix.

Status: proof of concept demonstrator... missing many TT's. please add!
  
IX used by Americans for HDF, unsure if that is kosher/halal/blessed, but it is in the UNIDATA feed.

IU/IS/IB are BUFR 

other type designators welcome... for example, GRIB isn't identified yet.

default to .txt.  
  
"""

class WMO_type_suffix(object):

      def __init__(self) :
          pass

      def find_type(self,TT):

          if TT in [ 'IX' ]:
              return '.hdf'

          if TT[0] in [ 'I' ]:
              return '.bufr'

          if TT[0] in [ 'Y' ]:
              return '.grib'

          return '.txt'


      def on_message(self,parent):

          type_suffix = self.find_type( parent.msg.new_file[0:2] )

          if type_suffix == 'UNKNOWN': 
              return True

          # file name already has suffix
          if parent.msg.new_file[-len(type_suffix):] == type_suffix:
              return True

          parent.msg.new_file         = parent.msg.new_file + type_suffix
          if 'rename' in parent.msg.headers:
              parent.msg.headers['rename']  = parent.msg.headers['rename'] + type_suffix

          return True

wmo_type_suffix=WMO_type_suffix()
self.on_message=wmo_type_suffix.on_message

# test interactif
#print wmo_type_suffix.on_message(sys.argv[1])

