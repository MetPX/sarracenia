"""
  Append _N2Z_HOHO to the names of files.
"""
class Transformer():
      def __init__(self,parent):
          pass

      def perform(self,parent):
          parent.new_file = parent.new_file + "_N2Z_HOHO"
          return True

transformer = Transformer(self)
self.destfn_script = transformer.perform
