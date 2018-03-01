#!/usr/bin/python3

"""
This plugin simply turns message with baseurl http://...  into   https://...
Sample usage is to put this line anywhere in a configuration:

on_message msg_http_to_https.py

The process would need to be restarted. From now on, all http messages that would be
consumed, would be turned into an https message. The remaining of the process will
treat the message as if posted that way. That plugin is an easy way to turn transaction
between dd.weather.gc.ca and the user  into  secured https transfers.

"""

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
