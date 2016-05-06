# used in sr_sender,  destfn_script can be used
# to run a script to modify the filename on the remote server

class Transformer():
      def __init__(self,parent):
          pass
      def perform(self,parent):
          parent.remote_file = "renamed_" + parent.remote_file
          # return true/false   but ignored at this point
          # the remote_file is modified or not... that is it
          return True

transformer = Transformer(self)
self.destfn_script = transformer.perform
