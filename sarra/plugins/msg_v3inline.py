#!/usr/bin/python3

"""
  When shovelling messages which are being transformed from v2 to v3
  if inlining is desired, then add the inline header to the message.

  not sure if the this is a work-around for a *bug* that the shovel
  publish should just *do* this without requiring a plugin.

  This is used to provide the v3 WMO_Sketch feed´s inlining.

"""

class Msg_V3Inline(object): 

    def __init__(self,parent):
        parent.logger.debug("msg_v3inline initialized")
          
    def on_message(self,parent):

        import os.path
        from base64 import b64decode, b64encode
        from mimetypes import guess_type

        fn = parent.post_base_dir 
        
        if fn[-1] != '/':
            fn = fn + os.path.sep 

        if parent.msg.relpath[0] == '/':
            fn = fn +  parent.msg.relpath[1:]
        else:
            fn = fn + parent.msg.relpath

        sz = int( parent.msg.headers[ 'parts' ].split(',')[1] )
        if sz < parent.inline_max :

            if parent.inline_encoding == 'guess':
                e = guess_type(fn)[0]
                binary = not e or not ('text' in e )
            else:
                binary = (parent.inline_encoding == 'text' )

            f = open( fn , 'rb')
            d = f.read()
            f.close()
            if binary:
                parent.msg.headers[ "content" ] = { "encoding": "base64", "value": b64encode(d).decode('utf-8') }
            else:
                try:
                    parent.msg.headers[ "content" ] = { "encoding": "utf-8", "value": d.decode('utf-8') }
                except:
                    parent.msg.headers[ "content" ] = { "encoding": "base64", "value": b64encode(d).decode('utf-8') }


        parent.logger.info("msg_v3inline received: %s pbd=%s f=%s" % ( parent.consumer.raw_msg.body, parent.post_base_dir, fn ) )
        return True

msg_v3inline = Msg_V3Inline(self)

self.on_message = msg_v3inline.on_message

