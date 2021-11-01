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

options is a sarracenia.config.Config object, used to override default behaviour

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
    worklist.directories_ok --> list of directories created during processing.

Initially all messages are placed in incoming.
if a plugin decides:

- a message is not relevant, it is moved to the rejected worklist. 
- all processing has been done, it moves it to the ok worklist
- an operation failed and it should be retried later, append it to the failed
  worklist

Do not remove any message from all lists, only move messages between them.
   it is necessary to put rejected messages in the appropriate worklist
   so they can be acknowledged as received. Messages can only removed after ack.

"""

logger = logging.getLogger(__name__)

entry_points = [
    'ack', 'do_poll', 'gather', 'after_accept', 'on_data', 'after_work',
    'on_housekeeping', 'on_html_page', 'on_line', 
    'on_report', 'on_start', 'on_stop', 'poll', 'post', 'send'
]

schemed_entry_points = ['do_get', 'do_put']


class FlowCB:
    """
    FIXME: document the API signatures for all the entry points. 

    def __init__(self,options):
        Task: initialization of the flow_callback at instantiation time.

        usually contains:

        self.o = options

    def ack(self,messagelist):
        Task: acknowledge messages from a gather source.

    def gather(self):
        Task: gather messages from a source... return a list of messages.

              in a poll, gather is always called, regardless of vip posession.
              in all other components, gather is only called when in posession
              of the vip.
        return []

    def after_accept(self,worklist):
         Task: just after messages go through accept/reject masks,
               operate on worklist.incoming to help decide which messages to process further.
               and move messages to worklist.rejected to prevent further processing.
               do not delete any messages, only move between worklists.

    def on_data(self,data):
        Task:  return data transformed in some way.

        return new_data

        The "work" step will do the downloads and/or sends, placing successful ones
        in worklist.ok, and failed ones in worklist.failed.


    def after_work(self,worklist):
        Task: operate on worklist.ok (files which have arrived.)

        All messages on the worklist.ok list have been acknowledged, so to suppress posting
        of them, or futher processing, the messages must be removed from worklist.ok.

        worklist.failed processing should occur in here as it will be zeroed out after this step.
        The flowcb/retry.py plugin, for example, processes failed messages.

    def on_housekeeping(self):
         do periodic processing.

    def on_html_page(self,page):
         Task: modify an html poll page. used in transfer/https.py to interpret weirdly 
               formatted lists of files.
         return True|False

    def on_line(self,line):
         used in FTP polls, because servers have different formats, modify to canonical use.

         Task: return modified line.

    def on_start(self):
         After the connection is established with the broker and things are instantiated, but
         before any message transfer occurs.

    def on_stop(self):
         

    def poll(self):
        Task: gather messages from a destination... return a list of messages.
              works like a gather, but...

              When specified, poll replaces the built-in poll of the poll component.
              it runs only when the machine running the poll has the vip.
              in components other than poll, poll is never called.
        return []

    def post(self,worklist):
         
         Task: operate on worklist.ok, and worklist.failed. modifies them appropriately.
               message acknowledgement has already occurred before they are called.

         to indicate failure to process a message, append to worklist.failed.
         worklist.failed processing should occur in here as it will be zeroed out after this step.

    def send(self,msg):

         Task: looking at msg['new_dir'], msg['new_file'], and the self.o options perform a transfer
               of a single file.
               return True on a successful transfer, False otherwise.

         This replaces built-in send functionality, is a crutch to support do_send.
         which is why it does not operate on lists. It is expected to be used very rarely.

    """

    def __init__(self, options):
        self.o = options

        logging.basicConfig(format=self.o.logFormat,
                            level=getattr(logging, self.o.logLevel.upper()))

        logger.setLevel(getattr(logging, self.o.logLevel.upper()))


def load_library(factory_path, options):
    """
       Loading the entry points for a python module. It searches 
       the normal python module pat using the importlib module. 

       the factory_path is a combined file specification with a dot separator
       with a special last entry being the name of the class within the file.

       factory_path  a.b.c.C

       means import the module named a.b.c and instantiate an object of type
       C. In that class-C object, look for the known callback entry points. 

       note that the ~/.config/sr3/plugins will also be in the python library 
       path, so modules placed there will be found, in addition to those in the
       package itself in the *sarracenia/flowcb*  directory

    """

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
