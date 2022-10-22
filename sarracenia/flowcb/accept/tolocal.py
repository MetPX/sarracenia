"""
Plugin tolocal.py:
    This is a helper script to work with filters.
    What a data pump advertises, it will usually use Web URL, but if one is
    on a server where the files are available, it is more efficient to access 
    them as local files, so filters operate on file urls.  
    
Example:
    baseDir /var/www/html
    url is http://localhost/<date>/<src>/input/file.txt

    flowcb sarracenia.flowcb.accept.tolocal.ToLocal   # converts web URL to file URL

               http://localhost/ --> file://var/www/html/
               url is now file://var/www/html/<date>/<src>/input/file.txt
               m.savedurl = http://localhost/

    flowcb sarracenia.flowcb.accept.<some converter that works on local files.>

               A new file is created in another directory.
               url is now file://var/www/<date>/<src>/output/file.txt

    flowcb sarracenia.flowcb.accept.tohttp.ToHttp     # turns the file URL back into a web one.

               file://var/www/html/ --> http:///localhost/
               url is now:   http://localhost/<date>/<src>/output/file.txt


    The regular expression used to find the web url matches either http or https
    and just captures upto the first '/'.

    if you need to capture a different kind of url, such as ...

    https://hostname/~user/ ....

    The easiest way is to set toLocalUrl as follows:

    baseDir /home/user/www
    toLocalUrl (https://hostname/~user/)

    the parentheses around the URL set the value of to be put in m.savedurl that
    will be restored when the companion plugin msg_2http is called.

Usage: 
    flowcb sarracenia.flowcb.accept.tolocal.ToLocal
"""
import logging
import re
from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)


class ToLocal(FlowCB):
    def __init__(self, options):
        self.o = options
        if hasattr(self.o, 'baseDir'):
            self.o.ldocroot = self.o.baseDir

        if hasattr(self.o, 'toLocalRoot'):
            self.o.ldocroot = self.o.toLocalRoot[0]

        self.o.lurlre = re.compile("(http[s]{0,1}://[^/]+/)")

        if hasattr(self.o, 'toLocalUrl'):
            self.o.lurlre = re.compile(self.o.toLocalUrl[0])

    def after_accept(self, worklist):
        for message in worklist.incoming:
            # TODO should all these be logger.error? should we append
            #  to worklist.rejected or worklist.failed at some point?
            logger.error("input: urlstr: %s" % message['urlstr'])

            message['savedurl'] = self.o.lurlre.match(
                message['urlstr']).group(1)
            message['urlstr'] = 'file:/%s' % self.o.lurlre.sub(
                self.o.ldocroot + '/', message['urlstr'])

            logger.error("doc_root=%s " % (self.o.baseDir))
            logger.error("output: urlstr: %s saved url: %s" %
                         (message['urlstr'], message['savedurl']))
