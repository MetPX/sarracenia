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
        super().__init__(options,logger)

        self._ldocroot = None

        if self.o.baseDir:
            self._ldocroot = self.o.baseDir

        self.o.add_option('toLocalRoot', 'str')
        if self.o.toLocalRoot:
            self._ldocroot = self.o.toLocalRoot

        self._lurlre = re.compile("(http[s]{0,1}://[^/]+/)")

        self.o.add_option('toLocalUrl', 'str')
        if self.o.toLocalUrl:
            self._lurlre = re.compile(self.o.toLocalUrl)

    def after_accept(self, worklist):
        for message in worklist.incoming:
            # TODO should all these be logger.error? should we append
            #  to worklist.rejected or worklist.failed at some point?
            logger.debug("input: urlstr: %s" % message['urlstr'])

            message['savedurl'] = self._lurlre.match(message['urlstr']).group(1)
            message['urlstr'] = 'file:/%s' % self._lurlre.sub(self._ldocroot + '/', message['urlstr'])

            logger.debug("doc_root=%s " % (self.o.baseDir))
            logger.debug("output: savedurl: %s" % (message['savedurl']))
