#!/usr/bin/python3

"""
  compare files to look for copy errors.

  also:
  delete files in the flow test once in all the components' directories.

"""

class Msg_AuditFlow(object): 

    def __init__(self,parent):
        parent.audit_flow_topdir="TESTDOCROOT"
        parent.logger.debug("msg_delete initialized")
        parent.audit_flow_Atotal=0
        parent.audit_flow_Bgood=0
        parent.audit_flow_BtoAratio=4
  
          
    def perform(self,parent):
 
        import os,filecmp
        msg = parent.msg
        #parent.logger.info("msg_delete received: %s %s%s topic=%s lag=%g %s" % \
        #   tuple( msg.notice.split()[0:3] + [ msg.topic, msg.get_elapse(), msg.hdrstr ] ) )
        
        a= "%s/%s/%s" % ( parent.audit_flow_topdir, "downloaded_by_sub_t", msg.new_file )
        parent.audit_flow_Atotal+=1

        for d in [ "downloaded_by_sub_u", "posted_by_srpost_test2", "recd_by_srpoll_test1", "sent_by_tsource2send" ]:
            b= "%s/%s/%s" % ( parent.audit_flow_topdir, d, msg.new_file )
            try: 
                if filecmp.cmp( a, b ):
                    parent.audit_flow_Bgood+=1
                else:
                    parent.logger.error("msg_auditflow: files differ: %s vs. %s " % ( a, b ) ) 
            except:
                parent.logger.error("msg_auditflow: compare failed: %s vs. %s " % ( a, b ) ) 

        for d in [ "downloaded_by_sub_t", "posted_by_srpost_test2", "recd_by_srpoll_test1" ]:
            f= "%s/%s/%s" % ( parent.audit_flow_topdir, d, msg.new_file )
            parent.logger.info("msg_delete: %s" % f )
            os.unlink( f )
            # sr_watch running here should propagate the deletion to the other directories.
        
        tally = ( parent.audit_flow_Atotal*parent.audit_flow_BtoAratio  /  parent.audit_flow_Bgood ) 
        if ( tally > 0.90 ) and ( tally < 1.1 ) : 
            so_far="GOOD" 
        else: 
            so_far="BAD" 

        parent.logger.info( "msg_auditflow: %s so far ( a: %d b: %d ) \n" % \
           ( so_far, parent.audit_flow_Atotal, parent.audit_flow_Bgood ) )
        return True

msg_auditflow = Msg_AuditFlow(self)

self.on_message = msg_auditflow.perform

