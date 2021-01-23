"""
   replace_new_dir, this is used in development as part of the flow_test suite,
   where files from a 'sub' directory, are sent by an sr_sender to a 'send' directory.
   see test/templates/sender for example.
   sample usage:

   msg_replace_new_dir sub,send

   on_message msg_replace_new_dir
 
"""


class Transformer():
    def __init__(self, parent):

        # make parent known about this possible option

        parent.declare_option('msg_replace_new_dir')

        if not hasattr(parent, 'msg_replace_new_dir'):
            parent.logger.error("msg_replace_new_dir setting mandatory")
            return

        parent.logger.debug("msg_replace_new_dir is %s " %
                            parent.msg_replace_new_dir)

    def on_message(self, parent):
        msg = parent.msg

        for p in parent.msg_replace_new_dir:
            (b, a) = p.split(",")
            parent.logger.info("msg_replace_new_dir is %s " % p)
            msg.new_dir = msg.new_dir.replace(b, a)

            # adjust oldname/newname/link  if related to strings to replace

            if 'oldname' in msg.headers:
                msg.headers['oldname'] = msg.headers['oldname'].replace(b, a)
            if 'newname' in msg.headers:
                msg.headers['newname'] = msg.headers['newname'].replace(b, a)
            if 'link' in msg.headers:
                msg.headers['link'] = msg.headers['link'].replace(b, a)

            # adjust new_relpath if posting

            if not parent.post_broker: return True

            msg.new_relpath = msg.new_dir + os.sep + msg.new_file
            if parent.post_base_dir:
                msg.new_relpath = msg.new_relpath.replace(
                    parent.post_base_dir, '')

        return True


transformer = Transformer(self)
self.on_message = transformer.on_message
