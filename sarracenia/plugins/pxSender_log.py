#!/usr/bin/python3
"""
This plugin IS ONLY LOGGING  NO DOWNLOAD, NO SEND

It provides a do_download to use in sr_subscribe
It provides a do_send     to use in sr_sender

And the announcement is restricted to http,ftp,sftp
it will only LOG

This interest of this plugin is that the log format is
similar to sundew's pxSender

The main purpose of this plugin is to have a tool to 
compare the routing of products between sundew and sarra

No files are actually being sent or downloaded

Sample usage:

  plugin pxSender_log.py

This is restricted to a mean to verify between logs of sundew
and logs on sarracenia... when the download or delivery of the products
are exactly the same on both side, taking out the plugin should
simply do the job... and let go of the sundew config

"""

import os, stat, time, sys
import calendar


class PXSENDER_LOG(object):

    import urllib.parse

    def __init__(self, parent):
        self.registered_list = ['http', 'ftp', 'sftp']

    def do_download(self, parent):
        parent.on_file_list = []
        msg = parent.msg

        src = msg.baseurl + ':' + msg.relpath
        src = src.replace(' ', '\ ')

        dest = msg.new_dir + os.sep + msg.new_file

        self.pxSender_print(parent, src, dest)

        return True

    def do_send(self, parent):
        msg = parent.msg

        src = parent.base_dir + msg.relpath
        src = src.replace(' ', '\ ')

        dest = parent.destination + msg.new_dir + os.sep + msg.new_file

        self.pxSender_print(parent, src, dest)

        return True

    def pxSender_print(self, parent, src, dest):
        logger = parent.logger
        msg = parent.msg

        if msg.headers['sum'][0] == 'L': return True
        if msg.headers['sum'][0] == 'R': return True

        # file size
        parts = msg.partstr.split(',')
        if parts[0] == '1':
            sz = int(parts[1])
        else:
            sz = int(parts[1]) * int(parts[2])

        logger.info("(%d Bytes) File %s delivered to %s (lat=0.1,speed=0.1)",
                    sz, src, dest)

    def registered_as(self):
        return self.registered_list


self.plugin = 'PXSENDER_LOG'
