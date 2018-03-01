"""
  Append _am to the names of files.
"""
class Transformer():
      def __init__(self,parent):
          pass

      def perform(self,parent):
          parent.new_file = parent.new_file + "_a2m"
          return True

transformer = Transformer(self)
self.destfn_script = transformer.perform
