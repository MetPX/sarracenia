"""
  msg_2http:  is the converse of msg_2file.
  after processing on a filter, a file URL needs to be turned back into a web url.
  
  uses savedurl created by msg_2file, to convert file url back to original.
   
"""
import re

class Http2Local(object):

    def __init__(self,parent) :
        if hasattr(parent, 'base_dir'):
           parent.ldocroot = parent.base_dir

        if hasattr(parent, 'msg_2http_root'):
           parent.ldocroot = parent.msg_2http_root[0]

        parent.hurlre = re.compile( 'file:/' + parent.ldocroot )


    def on_message(self,parent):
        import re

        l = parent.logger
        m = parent.msg

        l.debug( "msg_2http input: urlstr: %s"  % m.urlstr )

        m.urlstr = parent.hurlre.sub( m.savedurl, m.urlstr )
        m.url = urllib.parse.urlparse( m.urlstr )
        m.set_notice_url(m.url)
        l.debug( "msg_2http base_dir=%s " % ( parent.base_dir ) )
        l.info( "msg_2http output: urlstr: %s"  % m.urlstr )
        return True

http2local=Http2Local(self)
self.on_message=http2local.on_message


