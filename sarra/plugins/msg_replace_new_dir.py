
"""
   replace_new_dir, this is used in development as part of the flow_test suite,
   where files from a 'sub' directory, are sent by an sr_sender to a 'send' directory.
   see test/templates/sender for example.
   sample usage:

   msg_replace_new_dir sub,send

   on_message msg_replace_new_dir
 
"""

class Transformer():
      def __init__(self,parent):

        if not hasattr(parent,'msg_replace_new_dir'):
           parent.logger.error("msg_replace_new_dir setting mandatory")
           return

        parent.logger.info("msg_replace_new_dir is %s " % parent.msg_replace_new_dir )

      def perform(self,parent):
          for p in parent.msg_replace_new_dir :
              ( b, a ) = p.split(",") 
              parent.logger.info("msg_replace_new_dir is %s " % p )
              parent.new_dir = parent.new_dir.replace(b, a)

          return True

transformer = Transformer(self)
self.on_message = transformer.perform
