"""
  a data transformation plugin to remove all carriage returns.

"""


class Data_Nocr(object):
    def __init__(self, parent):
        parent.logger.debug("data_nocr initialized")

    def on_data(self, parent, chunk):
        parent.logger.debug("data_nocr sz=%d, cr=%d" %
                            (len(chunk), chunk.count(b'\r')))
        return chunk.replace(b'\r', b'')


data_nocr = Data_Nocr(self)

self.on_data = data_nocr.on_data
