#!/usr/bin/python3

"""
  delete files in the flow test once in all the components' directories.

"""

class Msg_DelFlow(object): 

    def __init__(self,parent):
        parent.delflow_topdir="TESTDOCROOT"
        parent.logger.debug("msg_delete initialized")
          
    def perform(self,parent):
 
        import os
        msg = parent.msg
        #parent.logger.info("msg_delete received: %s %s%s topic=%s lag=%g %s" % \
        #   tuple( msg.notice.split()[0:3] + [ msg.topic, msg.get_elapse(), msg.hdrstr ] ) )
        for d in [ "downloaded_by_sub_t", "downloaded_by_sub_u", "recd_by_srpoll_test1", "sent_by_tsource2send", "posted_by_srpost_test2" ]:
            f= "%s/%s/%s" % ( parent.delflow_topdir, d, msg.new_file )
            parent.logger.info("msg_delete: %s" % f )
            os.unlink( f )

        return True

msg_delflow = Msg_DelFlow(self)

self.on_message = msg_delflow.perform

