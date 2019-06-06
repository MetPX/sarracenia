
"""
  A trivial data transformation plugin, just logs that it was called.

"""
class Data_Log(object):
 
    def __init__(self,parent):
        parent.logger.debug( "data_log initialized")

    def on_data(self,parent,chunk):
        parent.logger.info( "data_log sz=%d" % len(chunk))
        return chunk

data_log = Data_Log(self)

self.on_data = data_log.on_data
