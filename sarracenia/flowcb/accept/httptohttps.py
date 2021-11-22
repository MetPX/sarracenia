#!/usr/bin/python3
"""
This plugin simply turns message with baseurl http://...  into   https://...
Sample usage is to put this line anywhere in a configuration:

on_message httptohttps.py #TODO change this .. is it callback HttpTpHttps ?

The process would need to be restarted. From now on, all http messages that would be
consumed, would be turned into an https message. The remaining of the process will
treat the message as if posted that way. That plugin is an easy way to turn transaction
between dd.weather.gc.ca and the user  into  secured https transfers.

"""
import logging
from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)

class HttpToHttps(FlowCB):
    def __init__(self, options):
        self.o = options

    def after_accept(self, worklist):
        new_incoming = []
        for message in worklist.incoming:
            if not 'http:' in msg['baseUrl']:
                new_incoming.append(message)
                continue
            baseUrl = message['baseUrl'].replace('http:', 'https:')
            message['set_notice'](baseUrl, message['relpath'])
            new_incoming.append(message)

        worklist.incoming = new_incoming


