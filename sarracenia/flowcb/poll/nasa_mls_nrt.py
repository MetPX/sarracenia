


import logging
import paramiko
import sarracenia
from sarracenia import nowflt, timestr2flt
from sarracenia.flowcb.poll import Poll


logger = logging.getLogger(__name__)

class Nasa_mls_nrt(Poll):

    def handle_data(self, data):
        import time


        st = paramiko.SFTPAttributes()
        st.st_mtime = 0
        st.st_mode = 0o775
        st.filename = data

        if 'MLS-Aura' in data:
               logger.debug("data %s" %data)
               #self.entries[self.myfname] = '-rwxr-xr-x 1 101 10 ' +'_' + ' ' + 'Jan 1 00:01' + ' ' + data
               self.entries[data]=st

               logger.info("(%s) = %s" % (self.myfname,st))
        if self.myfname == None : return
        if self.myfname == data : return
