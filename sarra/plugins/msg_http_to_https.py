#!/usr/bin/python3

import os,stat,time

class msg_http_to_https(object): 

    def __init__(self,parent):
        logger     = parent.logger

    def on_message(self,parent):

        msg = parent.msg

        if not 'http:' in msg.baseurl : return True

        baseurl = msg.baseurl.replace('http:','https:')

        msg.set_notice(baseurl,msg.relpath)

        return True

h= msg_http_to_https(self)
self.on_message=h.on_message
