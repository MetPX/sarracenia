import sys, os, os.path, time, stat

# This is an  example of the usage of on_message script
# to rename the product when it is downloaded
# It adds a ':datetime' to the name of the product
#
# takes px name     : CACN00_CWAO_081900__WZS_14623:pxatx:CWAO:CA:5:Direct:20081008190602
# add datetimestamp : CACN00_CWAO_081900__WZS_14623:pxatx:CWAO:CA:5:Direct:20081008190602:20081008190612

class Renamer(object):

      def __init__(self,parent) :
          pass

      # old in metpx
      #def perform(self,path):
          #datestr = time.strftime('%Y%m%d%H%M%S',time.localtime())
          #new_path = path + ':' + datestr
          #return new_path

      def perform(self,parent):
          import time

          datestr = time.strftime(':%Y%m%d%H%M%S',time.localtime())

          parent.msg.local_file        += datestr
          parent.msg.headers['rename'] += datestr

          return True

renamer=Renamer(self)
self.on_message=renamer.perform

# test interactif
#print renamer.perform(sys.argv[1])

