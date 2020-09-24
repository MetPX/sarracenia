#!/usr/bin/env python3

#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Shared Services Canada, 2020
#

import copy
import importlib
import logging

from abc import ABCMeta, abstractmethod
"""
1st draft of a v03 plugin method: flow_plugins

sample call:

flow_plugin sarra.plugin.name.Name

will instantiate an object of that type whose appropriately name methods
will be called at the right time.


__init__ accepts options as an argument.

options is a dictionary of settings, used to override default behaviour

a setting is declared:

set sarra.plugin.msg.log.Log.level debug

(the prefix for the setting matches the type hierarchy in flow_plugin)

the plugin should get the setting:

    options.level = 'debug'


worklist given to on_plugins...

    worklist.incoming --> new messages to continue processing
    worklist.ok       --> successfully processed
    worklist.rejected --> messages to not be further processed.
    worklist.failed    --> messages for which processing failed.


Initially all messages are placed in incoming.
if a plugin decides:

- a message is not relevant, it is moved to rejected. 
- all processing has been done, it moves it to ok. 
- an operation failed and it should be retried later, move to retry 

Do not remove from all lists, only move messages between them.
   it is necessary to put rejected messages in the appropriate worklist
   so they can be acknowledged as received. Messages can only removed after ack.

"""

logger = logging.getLogger(__name__)

entry_points = [
    'ack', 'do_poll', 'gather', 'on_messages', 'on_data', 'on_files',
    'on_housekeeping', 'on_html_page', 'on_line', 'on_part', 'on_posts',
    'on_report', 'on_start', 'on_stop', 'post'
]

schemed_entry_points = ['do_get', 'do_put']


class Plugin:
    """
    FIXME: document the API signatures for all the entry points. 
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, options):
        self.o = options

        logging.basicConfig(format=self.o.logFormat,
                            level=getattr(logging, self.o.logLevel.upper()))

        #logger.info( 'intializing %s' % self.name )
        pass


# FIXME:
#    @abstractmethod
#    def name(self):
#        """
#          Task: return the name of a plugin for reference purposes.
#        """
#        return __name__
#
#    @abstractmethod
#    def registered_as(self):
#        """
#          for schemed downloads, return the scheme this plugin provides.
#          for example, an accel_wget will in on_message, change url scheme from http/https -> download/downloads.
#          the do_get accellerate will need to be registered for download/downloads
#        """
#        return [ "registration", "registrations" ]
#
#    @abstractmethod
#    def on_files(self,worklist):
#        """
#          Task: operate on worklist.ok (files which have arrived.)
#        """
#        pass
#
#    @abstractmethod
#    def gather(self):
#        """
#          Task: gather messages from a source... return a list of messages.
#        """
#        return []
#
#    @abstractmethod
#    def ack(self,messagelist):
#        """
#          Task: acknowledge messages from a gather source.
#        """
#        pass
#
#    @abstractmethod
#    def on_messages(self,worklist):
#        """
#          Task: operate on worklist.incoming to help decide which messages to process further.
#                and move messages to worklist.rejected to prevent further processing.
#                do not delete any messages, only move between worklists, because acknowledgements have not happenned yet.
#        """
#        pass
#
#    @abstractmethod
#    def do_download(self,msg):
#        """
#          FIXME: Deprecated, replaced by do_get?
#
#          Task: operate on worklist.incoming to do corresponding file transfers
#                moving messages to worklist.ok on success, worklist.failed otherwise.
#                do not delete any messages, only move between worklists, because acknowledgements have not happenned yet.
#        """
#        pass
#
#    @abstractmethod
#    def do_get(self, msg, remote_file, local_file, remote_offset, local_offset, length ):
#        """
#          schemed method. (that is, installed based on registered_as() value.
#
#          Task: do a single file transfer. The local_file is not the final file name, but one constructed
#                based on the inflight option.
#
#                Return value is the number of bytes transferred.
#                If the return value is different from the length, then that is some kind of error.
#        """
#        pass
#
#    @abstractmethod
#    def do_poll(self):
#        """
#          Task: build worklist.incoming, a form of gather()
#        """
#        pass
#
#    @abstractmethod
#    def do_put(self, msg, local_file, remote_file, local_offset=0, remote_offset=0, length=0 ):
#        """
#          schemed method.
#
#          Task: do a single file transfer. The local_file is not the final file name, but one constructed
#                based on the inflight option.
#
#                Return value is the number of bytes transferred.
#                If the return value is different from the length, then that is some kind of error.
#
#        """
#        pass
#
#    @abstractmethod
#    def do_send(self):
#        """
#          FIXME: Deprecated, replaced by do_put?
#          Task:
#        """
#        pass
#
#    @abstractmethod
#    def on_data(self,data):
#        """
#          Task:  return data transformed in some way.
#        """
#        pass
#
#    @abstractmethod
#    def on_posts(self,worklist):
#        """
#          Task: operate on worklist.ok, and worklist.failed.
#                this is just prior to posting, to make final adjustments.
#                all messages are already aknowledged, so deleting messages from worklists here is fine.
#                if you delete a message from the worklist.ok, it will not be posted.
#        """
#        pass
#
#    @abstractmethod
#    def post(self,worklist):
#        """
#          Task: operate on worklist.ok, and worklist.failed. modifies them appropriately.
#                message acknowledgement has already occurred before they are called.
#        """
#        pass
#
#    @abstractmethod
#    def on_housekeeping(self):
#        """
#          Task:
#        """
#        pass
#
#    @abstractmethod
#    def on_html_page(self,page):
#        """
#          Task: modify an html page.
#        """
#        pass
#
#    @abstractmethod
#    def on_line(self,line):
#        """
#          used in FTP polls, because servers have different formats, modify to canonical use.
#
#          Task: return modified line.
#
#        """
#        pass
#
#    @abstractmethod
#    def on_part(self):
#        """
#          Task:
#        """
#        pass
#
#    @abstractmethod
#    def on_report(self):
#        """
#          Task:
#        """
#        pass
#
#    @abstractmethod
#    def on_start(self):
#        """
#          Task:
#        """
#        pass
#
#    @abstractmethod
#    def on_stop(self):
#        """
#          Task:
#        """
#        pass
#


def load_library(factory_path, options):

    #logger.debug( 'load_plugin: %s' % factory_path )
    packagename, classname = factory_path.rsplit('.', 1)
    module = importlib.import_module(packagename)
    class_ = getattr(module, classname)

    if hasattr(options, 'settings'):
        opt = copy.deepcopy(options)
        # strip off the class prefix.
        if factory_path in options.settings:
            for s in options.settings[factory_path]:
                setattr(opt, s, options.settings[factory_path][s])
    else:
        opt = options

    plugin = class_(opt)
    return plugin
