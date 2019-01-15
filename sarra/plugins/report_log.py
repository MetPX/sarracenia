#!/usr/bin/python3

"""
  an example of a default on_report handler logs 
  prints a simple code message notice.

"""

import os,stat,time

class Report_Log(object): 

    def __init__(self,parent):
        parent.logger.debug("report_log initialized")
          
    def perform(self,parent):

        msg = parent.msg

        parent.logger.info("report_log : (%d) '%s' - notice = %s %s %s" % (msg.code,msg.headers['message'], msg.pubtime, msg.baseurl, msg.relpath))

        # other report info :  msg.report_topic   and msg.headers  or  msg.hdrstr 

        return True

report_log     = Report_Log(self)
self.on_report = report_log.perform
