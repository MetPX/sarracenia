
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Shared Services Canada, 2020
#

import copy
import importlib
import logging
import sys

entry_points = [

    'ack', 'after_accept', 'after_post', 'after_work', 'destfn', 'do_poll', 
    'download', 'gather', 'on_housekeeping', 'on_report', 'on_start', 'on_stop',
    'poll', 'post', 'send', 'please_stop', 'metrics_report',

]

logger = logging.getLogger(__name__)


class FlowCB:
    """
    Flow Callback is the main class for implementing plugin customization to flows.

    sample activation in a configuration file:
    
    flowCallback sarracenia.flowcb.name.Name
    
    will instantiate an object of that type whose appropriately name methods
    will be called at the right time.
    
    __init__ accepts options as an argument.
    
    options is a sarracenia.config.Config object, used to override default behaviour
    
    a setting is declared in a configuration file like so::
    
        set sarracenia.flowcb.filter.log.Log.level debug
    
    (the prefix for the setting matches the type hierarchy in flowCallback)
    the plugin should get the setting::
    
        options.level = 'debug'
    
    
    worklist given to on_plugins...
    
    * worklist.incoming --> new messages to continue processing
    * worklist.ok       --> successfully processed
    * worklist.rejected --> messages to not be further processed.
    * worklist.failed   --> messages for which processing failed. Failed messages will be retried.
    * worklist.directories_ok --> list of directories created during processing.
    
    Initially, all messages are placed in incoming.
    if a plugin entry_point decides:
    
    - a message is not relevant, it is moved to the rejected worklist. 
    - all processing has been done, it moves it to the ok worklist
    - an operation failed and it should be retried later, append it to the failed
      worklist
    
    Do not remove any message from all lists, only move messages between them.
    it is necessary to put rejected messages in the appropriate worklist
    so they can be acknowledged as received. Messages can only removed after ack.
    
    
    def __init__(self,options) -> None::

        Task: initialization of the flowCallback at instantiation time.

        usually contains:

        self.o = options

    def ack(self,messagelist) -> None::

        Task: acknowledge messages from a gather source.

    def gather(self) -> list::

        Task: gather messages from a source... return a list of messages.

              in a poll, gather is always called, regardless of vip posession.
              in all other components, gather is only called when in posession
              of the vip.
        return []

    def after_accept(self,worklist) -> None::

         Task: just after messages go through accept/reject masks,
               operate on worklist.incoming to help decide which messages to process further.
               and move messages to worklist.rejected to prevent further processing.
               do not delete any messages, only move between worklists.

    def after_work(self,worklist) -> None::

        Task: operate on worklist.ok (files which have arrived.)

        All messages on the worklist.ok list have been acknowledged, so to suppress posting
        of them, or futher processing, the messages must be removed from worklist.ok.

        worklist.failed processing should occur in here as it will be zeroed out after this step.
        The flowcb/retry.py plugin, for example, processes failed messages.

    def destfn(self,msg) -> str::

         Task: look at the fields in the message, and perhaps settings and
               return a new file name for the target of the send or download.

         kind of a last resort function, exists mostly for sundew compatibility.
         can be used for selective renaming using accept clauses.

    def download(self,msg) -> bool::

         Task: looking at msg['new_dir'], msg['new_file'], msg['new_inflight_file'] 
               and the self.o options perform a download of a single file.
               return True on a successful transfer, False otherwise.

               if self.o.dry_run is set, simulate the output of a download without
               performing it.

         This replaces built-in download functionality, providing an override.
         for individual file transfers. ideally you set checksums as you download.
            
    def metrics_report(self) -> dict:

        Return a dictionary of metrics. Example: number of messages remaining in retry queues.

    def on_housekeeping(self) -> None::

         do periodic processing.

    def on_start(self) -> None::

         After the connection is established with the broker and things are instantiated, but
         before any message transfer occurs.

    def on_stop(self) -> None::
        
         what it says on the tin... clean up processing when stopping.         

    def poll(self) -> list::

        Task: gather messages from a destination... return a list of messages.
              works like a gather, but...

              When specified, poll replaces the built-in poll of the poll component.
              it runs only when the machine running the poll has the vip.
              in components other than poll, poll is never called.
        return []

    def post(self,worklist) -> None::
         
         Task: operate on worklist.ok, and worklist.failed. modifies them appropriately.
               message acknowledgement has already occurred before they are called.

         to indicate failure to process a message, append to worklist.failed.
         worklist.failed processing should occur in here as it will be zeroed out after this step.

    def send(self,msg) -> bool::

         Task: looking at msg['new_dir'], msg['new_file'], and the self.o options perform a transfer
               of a single file.
               return True on a successful transfer, False otherwise.

               if self.o.dry_run is set, simulate the output of a send without
               performing it.

         This replaces built-in send functionality for individual files.

    def stop_requested(self):
         Pre-warn a flowcb that a stop has been requested, allowing processing to wrap up
         before the full stop happens.

    """
    def __init__(self, options):
        self.o = options

        logging.basicConfig(format=self.o.logFormat,
                            level=getattr(logging, self.o.logLevel.upper()))

        logger.setLevel(getattr(logging, self.o.logLevel.upper()))


def load_library(factory_path, options):
    """
       Loading the entry points for a python module. It searches 
       the normal python module path using the importlib module. 

       the factory_path is a combined file specification with a dot separator
       with a special last entry being the name of the class within the file.

       factory_path  a.b.c.C

       means import the module named a.b.c and instantiate an object of type
       C. In that class-C object, look for the known callback entry points. 

       or C might be guessed by the last class in the path not following
       python convention by not starting with a capital letter, in which case,
       it will just guess.

       re
       note that the ~/.config/sr3/plugins will also be in the python library 
       path, so modules placed there will be found, in addition to those in the
       package itself in the *sarracenia/flowcb*  directory

       callback foo  -> foo.Foo
                        sarracenia.flowcb.foo.Foo

       callback foo.bar -> foo.bar.Bar
                           sarracenia.flowcb.foo.bar.Bar
                           foo.bar
                           sarracenia.flowcb.foo.bar 
    """

    if not '.' in factory_path:
        packagename = factory_path
        classname =factory_path.capitalize()
    else:
        if factory_path.split('.')[-1][0].islower():
            packagename = factory_path
            classname = factory_path.split('.')[-1].capitalize()
        else:
            packagename, classname = factory_path.rsplit('.', 1)

    try:
        module = importlib.import_module('sarracenia.flowcb.' + packagename)
        class_ = getattr(module, classname)
    except ModuleNotFoundError:
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
