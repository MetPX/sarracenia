"""
plugins intended for on_message entry_point.

(when messages are received.)

"""

import dateparser
import datetime
import html.parser
import logging
import paramiko
import pytz
import sarracenia
from sarracenia import nowflt, timestr2flt
from sarracenia.flowcb import FlowCB
import urllib.request

logger = logging.getLogger(__name__)



class Poll(FlowCB):

    def __init__(self,options):
        self.o = options
        logger.info( 'FIXME: parent poll hello')
        self.parser = html.parser.HTMLParser()
        self.parser.handle_starttag = self.handle_starttag
        self.parser.handle_data = self.handle_data

    def file_size_fix(self):
        try:
            str_value = self.mysize

            factor = 1
            if   str_value[-1] in 'bB'   : str_value = str_value[:-1]
            elif str_value[-1] in 'kK'   : factor = 1024
            elif str_value[-1] in 'mM'   : factor = 1024 * 1024
            elif str_value[-1] in 'gG'   : factor = 1024 * 1024 * 1024
            elif str_value[-1] in 'tT'   : factor = 1024 * 1024 * 1024 * 1024
            if str_value[-1].isalpha() : str_value = str_value[:-1]
 
            fsize = (float(str_value) + 0.5) * factor
            isize = int(fsize)

            self.mysize = isize

        except:
               logger.debug("bad size %s" % self.mysize)
               return

        return


    def handle_starttag(self, tag, attrs):
        for attr in attrs:
            c,n = attr
            if c == "href":
               self.myfname = n.strip().strip('\t')

    def handle_data(self, data):
        import time

        if self.myfname == None : return
        if self.myfname == data : return

        words = data.split()

        if len(words) != 3 :
           self.myfname = None
           return

        sdate = words[0] + ' ' + words[1]

        current_date = datetime.datetime.now(pytz.utc)
        standard_date_format = dateparser.parse(sdate,
            settings={
                'RELATIVE_BASE': datetime.datetime(current_date.year, 1, 1),
                'TIMEZONE': self.o.timezone, #turn this into an option - should be EST for mtl
                'TO_TIMEZONE': 'UTC'})

        logger.error( f'standard_date_format {standard_date_format}' )
        mydate = datetime.datetime.timestamp(standard_date_format)

        logger.error( f'mydate type={type(mydate)} value={mydate}' )
        #try   : t = time.strptime(sdate,'%d-%b-%Y %H:%M')
        #except: t = time.strptime(sdate,'%Y-%m-%d %H:%M')
        #mydate = time.strftime('%b %d %H:%M',t)

        logger.error( f'self.mydate type is {type(mydate)}, value is {mydate}' )

        self.mysize = words[-1]
        self.file_size_fix()

        st = paramiko.SFTPAttributes()
        st.st_mtime = mydate
        st.st_size = self.mysize
        st.filename = self.myfname
        entry = sarracenia.Message.fromFileInfo( self.myfname, self.o, st )
        
        if self.myfname[-1] != '/':
              self.entries.append(entry)
        else:
              # directory? what?
              pass


    def parse_line(self,line) -> paramiko.SFTPAttributes:
        """
         reformat a single line to build SFTPAttributes record.
        """
        #ret = paramiko.SFTPAttributes()
        pass

    def parse_result(self,raw_content) -> list:
       """
         reformat the byte stream into a series of messages


         note for v2: something like on_html_path in v2.
       """

       self.parser.feed(raw_content.decode('utf-8'))
       self.parser.close()

       return self.entries
       pass

   

    def poll(self) -> list:

       url_to_poll = self.o.destination
       logger.info( f'polling: {url_to_poll}' )

       self.entries = []
       self.myfname = None

       response = urllib.request.urlopen( url_to_poll ) 
       content = response.read()

       lines = self.parse_result(content) 

       logger.error( f'type of lines: {type(lines)} ' )
       for l in lines:
           logger.info( f'line: {l}' )

       return lines
       
