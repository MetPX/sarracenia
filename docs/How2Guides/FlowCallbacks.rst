

============================
Writing FlowCallback Plugins
============================

All sarracenia components implement *the Flow* algorithm, with different
callbacks.  Sarracenia's main class is *sarracenia.flow* and the a great
deal of core functionality is implemented using the class created to add
custom processing to a flow, the flowcb (flow callback) class.

For a detailed discussion of the flow algorithm itself, have a look 
at `Concepts <../Explanations/Concepts.rst>`_ manual. For any flow, one can
add custom processing at a variety of times during processing by sub-classing 
the `sarracenia.flowcb <../../sarracenia/flowcb/__init__.py>`_ class.  

Briefly, the algorithm has the following steps:

* **gather** -- collect messages to be processed.
* **filter** -- apply accept/reject regular expression matches to the message list.

  * *after_accept* callback entry point

* **work** -- perform a transfer or transformation on a file.

  * *after_work* callback entry point

* **post**  -- post the result of the work done for the next step.
  
A flow callback, is a python class built with routines named to
indicate when the programmer wants them to be called.
To do that, create a routine which subclasses *sarracenia.flowcb.FlowCB*
so the class will normally have::

   from sarracenia.flowcb import FlowCB

in among the imports.


Config File Entries to use Flow_Callbacks
-----------------------------------------

To add a callback to a a flow, a line is added to the config file::

    flowcb sarracenia.flowcb.log.Log

If you follow the convention, and the name of the class is a capitalized 
version (Log) of the file name (log), then a shorthand is available::

   callback log 

The class constructor accepts a sarracenia.config.Config class object,
called options, that stores all the settings to be used by the running flow.
Options is used to override default behaviour of both flows and callbacks.
The argument to the flowcb is a standard python class that needs to be
in the normal python path for python *import*, and the last element
is the name of the class in within the file that needs to be instantiated
as a flowcb instance.

a setting for a callback is declared as follows::

    set sarracenia.flowcb.filter.log.Log.logLevel debug

(the prefix for the setting matches the type hierarchy in flow_callback)

when the constructor for the callback is called, it's options
argument will contain::

    options.logLevel = 'debug'

If no module specific override is present, then the more global
setting is used.


Worklists
---------

Besides option, the other main argument to after_accept and after_work callback
routines is the worklist. The worklist is given to entry points occurring during message
processing, and is a number of worklists of messages::

    worklist.incoming --> messages to process (either new or retries.)
    worklist.ok       --> successfully processed
    worklist.rejected --> messages to not be further processed.
    worklist.failed   --> messages for which processing failed.
                          failed messages will be retried.

Initially, all messages are placed in worklists.incoming.
if a plugin decides:

- a message is not relevant, moved it to the rejected worklist. 
- a no further processing of the message is needed, move it to ok worklist. 
- an operation failed and it should be retried later, move to failed worklist. 

Do not remove from all lists, only move messages between the worklists.
it is necessary to put rejected messages in the appropriate worklist
so that they are acknowledged as received. Messages can only removed 
after the acknowledgement has been taken care of.


Logging
-------

Python has great built-in logging, and once has to just use the module
in a normal, pythonic way, with::

  import logging

After all imports in your python source file, then define a logger
for the source file::

  logger = logging.getLogger(__name__)

As is normal with the Python logging module, messages can then 
be posted to the log::

  logger.debug('got here')

Each message in the log will be prefixed with the class and routine 
emitting the log message, as well as the date/time.


Initialization and Settings
---------------------------

The next step is declaring a class::

  class Myclass(FlowCB):

as a subclass as FlowCB.  The main routines in the class  are entry points 
that will be called at the time their name implies. If you a class is missing a
given entry point, it will just not be called. The __init__() class is used to 
initialize things for the callback class::

    def __init__(self, options):

        self.o = options

        logging.basicConfig(format=self.o.logFormat,
                            level=getattr(logging, self.o.logLevel.upper()))
        logger.setLevel(getattr(logging, self.o.logLevel.upper()))

        self.o.add_option( 'myoption', 'str', 'usuallythis')

The logging setup lines in __init__ allow setting a specific logging level
for this flow_callback class. Once the logging boiler-plate is done, 
the add_option routine to define settings to for the class.
users can include them in configuration files, just like built-in options::

        myoption IsReallyNeeded

The result of such a setting is that the *self.o.myoption = 'IsReallyNeeded'*.
If no value is set in the configuration, *self.o.myoption* will default to *'usuallyThis'*
There are various *kinds* of options, where the declared type modifies the parsing::
           
   'count'    integer count type. 
   'duration' a floating point number indicating a quantity of seconds (0.001 is 1 milisecond)
              modified by a unit suffix ( m-minute, h-hour, w-week ) 
   'flag'     boolean (True/False) option.
   'list'     a list of string values, each succeeding occurrence catenates to the total.
              all v2 plugin options are declared of type list.
   'size'     integer size. Suffixes k, m, and g for kilo, mega, and giga (base 2) multipliers.
   'str'      an arbitrary string value, as will all of the above types, each 
              succeeding occurrence overrides the previous one.


Entry Points
------------


Other entry_points, extracted from sarracenia/flowcb/__init__.py ::

    def name(self):
        Task: return the name of a plugin for reference purposes. (automatically there)

    def ack(self,messagelist):
        Task: acknowledge messages from a gather source.

    def gather(self):
        Task: gather messages from a source... return a list of messages.
        return []

    """
      application of the accept/reject clauses happens here, so after_accept callbacks
      run on a filtered set of messages.

    """

    def after_accept(self,worklist):
        """
         Task: just after messages go through accept/reject masks,
               operate on worklist.incoming to help decide which messages to process further.
               and move messages to worklist.rejected to prevent further processing.
               do not delete any messages, only move between worklists.
        """
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



Sample Flowcb Sub-Class
-----------------------

This is an example callback class file (gts2wis2.py) that accepts files whose
names begin with AHL's, and renames the directory tree to a different standard, 
the evolving one for the WMO WIS 2.0 (for more information on that module: 
https://github.com/wmo-im/GTStoWIS2) ::

  import json
  import logging
  import os.path

  from sarracenia.flowcb import FlowCB
  from sarracenia.flowcb.gather import msg_dumps
  import GTStoWIS2

  logger = logging.getLogger(__name__)


  class GTS2WIS2(FlowCB):

    def __init__(self, options):

        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, options.logLevel.upper()))
        else:
            logger.setLevel(logging.INFO)
        self.topic_builder=GTStoWIS2.GTStoWIS2()
        self.o = options


    def after_accept(self, worklist):

        new_incoming=[]

        for msg in worklist.incoming:

            # fix file name suffix.
            type_suffix = self.topic_builder.mapAHLtoExtension( msg['new_file'][0:2] )
            tpfx=msg['subtopic']
    
            # input has relpath=/YYYYMMDD/... + pubTime
            # need to move the date from relPath to BaseDir, adding the T hour from pubTime.
            try:
                new_baseSubDir=tpfx[0]+msg['pubTime'][8:11]
                t='.'.join(tpfx[0:2])+'.'+new_baseSubDir
                new_baseDir = msg['new_dir'] + os.sep + new_baseSubDir
                new_relDir = 'WIS' + os.sep + self.topic_builder.mapAHLtoTopic(msg['new_file'])
                msg['new_dir'] = new_baseDir + os.sep + new_relDir
                self.o.set_newMessageUpdatePaths( msg, \
                     new_baseDir + os.sep + new_relDir, \
                     msg['new_file'] )

            except Exception as ex:
                logger.error( "skipped" , exc_info=True )
                worklist.failed.append(msg)
                continue
    
            msg['_deleteOnPost'] |= set( [ 'from_cluster', 'sum', 'to_clusters' ] )
            new_incoming.append(msg)

        worklist.incoming=new_incoming 

The *after_accept* routine is one of the two most common ones in use.

The after_accept routine has an outer loop that cycles through the entire
list of incoming messages. The normal processing is that is builds a new list of 
incoming messages, appending all the rejected ones to *worklist.failed.* The 
list is just a list of messages, where each message is a python dictionary with
all the fields stored in a v03 format message. In the message there are, 
for example, *baseURL* and *relPath* fields:

* baseURL - the baseURL of the resource from which a file would be obtained.
* relPath - the relative path to append to the baseURL to get the complete download URL.

This is happenning before transfer (download or sent, or processing) of the file
has occurred, so one can change the behaviour by modifying fields in the message.
Normally, the download paths (called new_dir, and new_file) will reflect the intent
to mirror the original source tree. so if you have *a/b/c.txt*  on the source tree, and
are downloading in to directory *mine* on the local system, the new_dir would be
*mine/a/b* and new_file would be *c.txt*.

The plugin above changes the layout of the files that are to be downloaded, based on the 
`GTStoWIS <https://github.com/wmo-im/GTStoWIS>`_ class, which prescribes a different
directory tree on output.  There are a lot of fields to update when changing file 
placement, so best to use::

   self.o.set_newMessageUpdatePaths( msg, new_dir, new_file )

to update all necessary fields in the message properly. It will update 
'new_baseURL', 'new_relPath', 'new_subtopic' for use when posting.

The try/except part of the routine deals with the case that, should
a file arrive with a name from which a topic tree cannot be built, then an exception
may occur, and the message is added to the failed worklist, and will not be
processed by later plugins.

Other Examples
--------------

Subclassing of Sarracenia.flowcb is used internally to do a lot of core work.
It's a good idea to look at the sarracenia source code itself. For example:

* *sarracenia.flowcb* have a look at the __init__.py file in there, which
  provides this information on a more programmatically succinct format.

* *sarracenia.flowcb.gather.file.File*  is a class that implements 
  file posting and directory watching, in the sense of a callback that 
  implements the *gather* entry point, by reading a file system and building a
  list of messages for processing.

* *sarracenia.flowcb.gather.message.Message* is a class that implements
  reception of messages from message queue protocol flows.

* *sarracenia.flowcb.nodupe.NoDupe* This modules removes duplicates from message
  flows based on Integrity checksums.

* *sarracenia.flowcb.post.message.Message* is a class that implements posting
  messages to Message queue protocol flows

* *sarracenia.flowcb.retry.Retry* when the transfer of a file fails,
  Sarracenia needs to persist the relevant message to a state file for 
  a later time when it can be tried again.  This class implements
  that functionality.


