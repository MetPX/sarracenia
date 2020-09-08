"""

   With this plugin, in sr_sender, replaces parent.consumer.consume
   by messages built from a file parsed/read each lines contains
   server: product/relpath

"""


class Msg_From_File(object):
    def __init__(self, parent):
        self.parent = parent
        parent.declare_option('msg_file')

    def get_subtopics(self, parent):
        import re

        self.subtopic_regexp = []

        for x, t in parent.bindings:
            subtopic = t.replace(parent.topic_prefix + '.', '')
            parent.logger.info("subtopic %s" % subtopic)
            pattern = subtopic.replace('.', '/')
            pattern = pattern.replace('#', '*')
            pattern = pattern.replace('*', '.*')
            self.subtopic_regexp.append(re.compile(pattern))

    def on_start(self, parent):
        self.parent = parent

        if not hasattr(parent, 'msg_file'): return

        self.fp_msg_file = open(parent.msg_file[0], 'r')

        self.orig_consume = parent.consumer.consume
        parent.consumer.consume = self.consume

        self.get_subtopics(parent)

    # This is really tuned for my migration testing

    def consume(self):
        import sys
        parent = self.parent
        msg = parent.msg

        line = self.fp_msg_file.readline()
        if not line:
            parent.logger.info("We are done with %s" % parent.msg_file[0])
            parent.consumer.consume = self.orig_consume
            # if you would like to go back in normal mode
            # simply comment parent.stop()
            parent.stop()
            return False, msg

        # line = server: product/relpath
        parts = line.split()
        frpath = parts[1]

        # manual subtopic check ...

        match = False
        for re_pat in self.subtopic_regexp:
            if not re_pat.match(frpath): continue
            match = True
            break
        if not match: return False, msg

        # message is within subtopic acceptance

        msg.baseurl = 'http://localhost'
        msg.relpath = frpath.replace('/apps/sarra/public_data', '')
        msg.urlstr = msg.baseurl + msg.relpath
        msg.url = urllib.parse.urlparse(msg.urlstr)

        # check pattern matching

        if not parent.isMatchingPattern(msg.urlstr, parent.accept_unmatch):
            return False, msg

        # product is good ... make its message

        msg.set_notice(msg.baseurl, msg.relpath)

        msg.filesize = 30

        msg.headers['source'] = 'metpx'

        msg.partstr = '1,%d,1,0,0' % 30
        msg.headers['parts'] = msg.partstr

        msg.sumstr = 'z,0'
        msg.headers['sum'] = msg.sumstr

        msg.to_clusters = []
        msg.headers['to_clusters'] = None

        msg.suffix = ''

        msg.set_parts('1', 30)
        msg.set_sum_str(msg.sumstr)
        msg.set_suffix()
        msg.set_hdrstr()

        return True, msg


self.plugin = 'Msg_From_File'
