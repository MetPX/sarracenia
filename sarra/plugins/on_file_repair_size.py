"""
   http size was 4.1M an approximation
   get the right size set in post message
"""


class Repair_Size(object):
    def __init__(self, parent):
        pass

    def on_file(self, parent):
        import os, stat

        logger = parent.logger
        msg = parent.msg
        path = msg.new_dir + '/' + msg.new_file
        fsiz = os.stat(path)[stat.ST_SIZE]
        partstr = '1,%d,1,0,0' % fsiz

        if partstr == msg.partstr: return True

        msg.partstr = partstr
        msg.headers['parts'] = msg.partstr

        parent.logger.debug("file size repaired in message %s" % partstr)

        return True


repair_size = Repair_Size(self)
self.on_file = repair_size.on_file
