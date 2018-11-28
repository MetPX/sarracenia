
"""

  a destfn plugin script is used by senders or subscribers to do complex file naming.
  this is an API demonstrator that prefixes the name delivered with 'renamed_'

  filename DESFTN=desftn_sample

  and whenever writing a file (new_file, when used in a sender)

"""
class Transformer():
      def __init__(self,parent):
          pass
      def perform(self,parent):
          parent.msg.new_file = "renamed_" + parent.msg.new_file
          # return true/false   but ignored at this point
          # the new_file is modified or not... that is it
          return True

transformer = Transformer(self)
self.destfn_script = transformer.perform
