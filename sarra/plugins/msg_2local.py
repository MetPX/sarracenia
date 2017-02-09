"""
  msg_2local:  this is a helper script to work with filters.

  What a data pump advertises, it will usually use Web URL, but if one is
  on a server where the files are available, it is more efficient to access 
  them as local files, so filters operate on file urls.  
   
  Normal usage:

  document_root /var/www/html

               url is http://localhost/<date>/<src>/input/file.txt

  on_message msg_2local   # converts web URL to file URL 

               http://localhost/ --> file://var/www/html/
               url is now file://var/www/html/<date>/<src>/input/file.txt 
               m.savedurl = http://localhost/

  on_message <some converter that works on local files.>

               A new file is created in another directory.
               url is now file://var/www/<date>/<src>/output/file.txt

  on_message msg_2http     # turns the file URL back into a web one.

               file://var/www/html/ --> http:///localhost/
               url is now:   http://localhost/<date>/<src>/output/file.txt
 

  The regular expression used to find the web url matches either http or https
  and just captures upto the first '/'.

  if you need to capture a different kind of url, such as ...

  https://hostname/~user/ ....

  The easiest way is to set msg_2local_url as follows:

  document_root /home/user/www
  msg_2local_url (https://hostname/~user/)

  the parentheses around the URL set the value of to be put in m.savedurl that
  will be restored when the companion plugin msg_2http is called.
    


"""
import re

class Http2Local(object):

    def __init__(self,parent) :
        if hasattr(parent, 'document_root'):
           parent.ldocroot = parent.document_root 

        if hasattr(parent, 'msg_2local_root'):
           parent.ldocroot = parent.msg_2local_root[0]

        parent.lurlre = re.compile("(http[s]{0,1}://[^/]+/)")

        if hasattr(parent, 'msg_2local_url'):
            parent.lurlre = re.compile(parent.msg_2local_url[0])
        pass

    def perform(self,parent):
        import re

        l = parent.logger
        m = parent.msg

        l.error( "input: urlstr: %s"  % m.urlstr )

        m.savedurl = parent.lurlre.match( m.urlstr ).group(1)
        m.urlstr = 'file:/%s' % parent.lurlre.sub( parent.ldocroot + '/', m.urlstr )

        l.error( "doc_root=%s " % ( parent.document_root ) )
        l.error( "output: urlstr: %s saved url: %s"  % (m.urlstr, m.savedurl) )

        return True

ren2local=Http2Local(self)

self.on_message=ren2local.perform


