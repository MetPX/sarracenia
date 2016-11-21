# used in sr_sender,  destfn_script can be used
# to run a script to modify the filename on the remote server
# 

class Transformer():
      def __init__(self,parent):

        if not hasattr(parent,'msg_replace_remote_dir'):
           parent.logger.info("msg_replace_remote_dir setting mandatory")
           return

        parent.logger.info("msg_replace_remote_dir is %s " % parent.msg_replace_remote_dir )

      def perform(self,parent):
          for p in parent.msg_replace_remote_dir :
              ( b, a ) = p.split(",") 
              parent.logger.info("msg_replace_remote_dir is %s " % p )
              parent.remote_dir = parent.remote_dir.replace(b, a)

          return True

transformer = Transformer(self)
self.on_message = transformer.perform
