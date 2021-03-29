#!/usr/bin/env python3

#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Shared Services Canada, 2020
#

import copy
import importlib
import logging
import sys
"""
1st draft of a v03 plugin method: flow_callback

sample call:

flow_callback sarracenia.flowcb.name.Name

will instantiate an object of that type whose appropriately name methods
will be called at the right time.


__init__ accepts options as an argument.

options is a dictionary of settings, used to override default behaviour

a setting is declared:

set sarracenia.flowcb.filter.log.Log.level debug

(the prefix for the setting matches the type hierarchy in flow_callback)

the plugin should get the setting:

    options.level = 'debug'


worklist given to on_plugins...

    worklist.incoming --> new messages to continue processing
    worklist.ok       --> successfully processed
    worklist.rejected --> messages to not be further processed.
    worklist.failed   --> messages for which processing failed.
                          failed messages will be retried.


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
    'ack', 'do_poll', 'gather', 'after_accept', 'on_data', 'after_work',
    'on_housekeeping', 'on_html_page', 'on_line', 
    'on_report', 'on_start', 'on_stop', 'post'
]

schemed_entry_points = ['do_get', 'do_put']


class FlowCB:
    """
    FIXME: document the API signatures for all the entry points. 

    def name(self):
        Task: return the name of a plugin for reference purposes.
        return __name__

    def registered_as(self):
        for schemed downloads, return the scheme this plugin provides.
        for example, an accel_wget will in on_message, change url scheme from http/https -> download/downloads.
        the do_get accellerate will need to be registered for download/downloads

        return [ "registration", "registrations" ]

    def ack(self,messagelist):
        Task: acknowledge messages from a gather source.

    def gather(self):
        Task: gather messages from a source... return a list of messages.
        return []

    def after_accept(self,worklist):
         Task: just after messages go through accept/reject masks,
               operate on worklist.incoming to help decide which messages to process further.
               and move messages to worklist.rejected to prevent further processing.
               do not delete any messages, only move between worklists.

    def do_poll(self):
        Task: build worklist.incoming, a form of gather()

    def on_data(self,data):
        Task:  return data transformed in some way.

        return new_data

    def after_work(self,worklist):
        Task: operate on worklist.ok (files which have arrived.)

    def post(self,worklist):
         Task: operate on worklist.ok, and worklist.failed. modifies them appropriately.
               message acknowledgement has already occurred before they are called.

    def on_housekeeping(self):
         do periodic processing.

    def on_html_page(self,page):
         Task: modify an html page.

    def on_line(self,line):
         used in FTP polls, because servers have different formats, modify to canonical use.

         Task: return modified line.

    def on_start(self):
         After the connection is established with the broker and things are instantiated, but
         before any message transfer occurs.

    def on_stop(self):


    """

    def __init__(self, options):
        self.o = options

        logging.basicConfig(format=self.o.logFormat,
                            level=getattr(logging, self.o.logLevel.upper()))

        logger.setLevel(getattr(logging, self.o.logLevel.upper()))


def load_library(factory_path, options):

    if not '.' in factory_path:
       logger.error('flow_callback <file>.<Class> no dot... missing something from: %s' % factory_path )
       return None

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
