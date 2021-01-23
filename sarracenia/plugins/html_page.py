#!/usr/bin/env python3


class Html_parser():
    def __init__(self, parent):
        parent.logger.debug("Html_parser __init__")
        import html.parser

        self.parent = parent
        self.logger = parent.logger

        self.parser = html.parser.HTMLParser()
        self.parser.handle_starttag = self.handle_starttag
        self.parser.handle_data = self.handle_data

    def file_size_fix(self):
        try:
            str_value = self.mysize

            factor = 1
            if str_value[-1] in 'bB': str_value = str_value[:-1]
            elif str_value[-1] in 'kK': factor = 1024
            elif str_value[-1] in 'mM': factor = 1024 * 1024
            elif str_value[-1] in 'gG': factor = 1024 * 1024 * 1024
            elif str_value[-1] in 'tT': factor = 1024 * 1024 * 1024 * 1024
            if str_value[-1].isalpha(): str_value = str_value[:-1]

            fsize = (float(str_value) + 0.5) * factor
            isize = int(fsize)

            self.mysize = "%d" % isize

        except:
            self.logger.debug("bad size %s" % self.mysize)
            return

        return

    def handle_starttag(self, tag, attrs):
        for attr in attrs:
            c, n = attr
            if c == "href":
                self.myfname = n.strip().strip('\t')

    def handle_data(self, data):
        import time

        if self.myfname == None: return
        if self.myfname == data: return

        words = data.split()

        if len(words) != 3:
            self.myfname = None
            return

        sdate = words[0] + ' ' + words[1]
        try:
            t = time.strptime(sdate, '%d-%b-%Y %H:%M')
        except:
            t = time.strptime(sdate, '%Y-%m-%d %H:%M')
        mydate = time.strftime('%b %d %H:%M', t)

        self.mysize = words[-1]
        self.file_size_fix()

        if self.myfname[-1] != '/':
            self.entries[
                self.
                myfname] = '-rwxr-xr-x 1 101 10 ' + self.mysize + ' ' + mydate + ' ' + self.myfname
        else:
            self.entries[
                self.
                myfname] = 'drwxr-xr-x 1 101 10 ' + self.mysize + ' ' + mydate + ' ' + self.myfname

        self.myfname = None

    def parse(self, parent):
        self.logger.debug("Html_parser parse")
        self.entries = {}
        self.myfname = None

        self.parser.feed(parent.data)
        self.parser.close()

        parent.entries = self.entries

        return True


html_parser = Html_parser(self)
self.on_html_page = html_parser.parse
