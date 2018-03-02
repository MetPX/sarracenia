#if __name__ != '__main__':

#    msg_log = Log(self)
#    self.on_message = msg_log.on_message


#else:  # unit testing code goes here.

import time

class TestLogger:
        def silence(self,str):
            pass
    
        def __init__(self):
            self.debug   = print
            self.error   = print
            self.info    = print
            self.warning = print
    
    
class TestMessage():
    
        def __init__(self):
            self.urlstr = "download://" 
            self.headers = {}
            self.notice = "20171230232323.111 http://localhost:8000 lolo/lala"
            self.topic = "v02.post.lolo"
            self.get_elapse= lambda: 1.2
            self.hdrstr= " sum=0,234 parts=1,1,0,0"
            self.new_file = 'hoho'
            self.new_dir = "/tmp/lolo"
    
class TestParent(object):
    
        def __init__(self):
            self.msg= TestMessage()
            self.logger=TestLogger()
            pass

#    tp=TestParent() 
#    ml=Log(tp) 
#    ml.on_message(tp)
#    ml.on_file(tp)


