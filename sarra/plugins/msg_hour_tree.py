import sys, os, os.path, time, stat

"""
 When receiving a file, insert an hourly directory into the local delivery path hierarchy.

 input A/B/c.gif  --> output A/B/<hour>/c.gif


"""

class Renamer(object):

      def __init__(self) :
          pass

      def perform(self,parent):
          import time

          datestr = time.strftime('%H',time.localtime())   # pick the hour.
          parent.new_dir += '/' + datestr    # append the hourly element to the directory tree.

          # insert the additional hourly directory into the path of the file to be written.
          new_fname = parent.msg.new_file.split('/')
          parent.msg.new_file = '/'.join(new_fname[0:-1]) + '/' + datestr + '/' + new_fname[-1] 

          return True

renamer=Renamer()
self.on_message=renamer.perform

