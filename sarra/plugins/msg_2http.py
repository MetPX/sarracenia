"""
  msg_2http:  is the converse of msg_2file.
  after processing on a filter, a file URL needs to be turned back into a web url.
  
  uses savedurl created by msg_2file, to convert file url back to original.
   
"""
import re

class Http2Local(object):

    def __init__(self,parent) :
        if hasattr(parent, 'document_root'):
           parent.ldocroot = parent.document_root

        if hasattr(parent, 'msg_2http_root'):
           parent.ldocroot = parent.msg_2http_root[0]

        parent.hurlre = re.compile( 'file:/' + parent.ldocroot )


    def perform(self,parent):
        import re

        l = parent.logger
        m = parent.msg

        l.debug( "msg_2http input: urlstr: %s"  % m.urlstr )

        m.urlstr = parent.hurlre.sub( m.savedurl, m.urlstr )
        m.url = urllib.parse.urlparse( m.urlstr )
        m.set_notice(m.url)
        l.debug( "msg_2http doc_root=%s " % ( parent.document_root ) )
        l.info( "msg_2http output: urlstr: %s"  % m.urlstr )
        return True

ren2local=Http2Local(self)
self.on_message=ren2local.perform


