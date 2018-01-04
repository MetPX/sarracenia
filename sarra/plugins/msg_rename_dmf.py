import sys, os, os.path, time, stat

"""
 unlikely to be useful to others, except as example.

 this renamer
 takes px name     : CACN00_CWAO_081900__WZS_14623:pxatx:CWAO:CA:5:Direct:20081008190602
 add datetimestamp : CACN00_CWAO_081900__WZS_14623:pxatx:CWAO:CA:5:Direct:20081008190602:20081008190612

"""

class Renamer(object):

      def __init__(self) :
          pass

      def on_message(self,parent):
          import time

          datestr = time.strftime(':%Y%m%d%H%M%S',time.localtime())

          parent.msg.new_file        += datestr
          parent.msg.headers['rename'] += datestr

          return True

renamer=Renamer()
self.on_message=renamer.on_message

