

============================
Writing FlowCallback Plugins
============================

All Sarracenia components implement *the Flow* algorithm.
Sarracenia's main class is *sarracenia.flow* and the a great
deal of core functionality is implemented using the class created to add
custom processing to a flow, the flowcb (flow callback) class.

For a detailed discussion of the flow algorithm itself, have a look 
at `Concepts <../Explanation/Concepts.rst>`_ manual. For any flow, one can
add custom processing at a variety of times during processing by sub-classing 
the `sarracenia.flowcb <../../sarracenia/flowcb/__init__.py>`_ class.  

Briefly, the algorithm has the following steps:

* **gather** -- passively collect notification messages to be processed.
* **poll** -- actively collect notification messages to be processed.
* **filter** -- apply accept/reject regular expression matches to the notification message list.

  * *after_accept* callback entry point

* **work** -- perform a transfer or transformation on a file.

  * *after_work* callback entry point

* **post**  -- post the result of the work done for the next step.
  
A flow callback, is a python class built with routines named to
indicate when the programmer wants them to be called.

There are a number of examples of flowcallback classes included
with Sarracenia, given in the 
`Flowcallback Reference <../Reference/flowcb.html>`_
that can be used as the basis for building custom ones. 

This guide describes how to build flow callback classes from scratch.


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

(the prefix for the setting matches the type hierarchy in flowCallback)

when the constructor for the callback is called, it's options
argument will contain::

    options.logLevel = 'debug'

If no module specific override is present, then the more global
setting is used.


Worklists
---------

Besides option, the other main argument to after_accept and after_work callback
routines is the worklist. The worklist is given to entry points occurring during notification message
processing, and is a number of worklists of notification messages::

    worklist.incoming --> notification messages to process (either new or retries.)
    worklist.ok       --> successfully processed
    worklist.rejected --> notification messages to not be further processed.
    worklist.failed   --> notification messages for which processing failed.
                          failed notification messages will be retried.

Initially, all notification messages are placed in worklists.incoming.
if a plugin decides:

- a notification message is not relevant, moved it to the rejected worklist. 
- a no further processing of the notification message is needed, move it to ok worklist. 
- an operation failed and it should be retried later, move to failed worklist. 

Do not remove from all lists, only move notification messages between the worklists.
it is necessary to put rejected notification messages in the appropriate worklist
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

As is normal with the Python logging module, notification messages can then 
be posted to the log::

  logger.debug('got here')

Each notification message in the log will be prefixed with the class and routine 
emitting the log notification message, as well as the date/time.

One can also implement a per module override to log levels.
See sarracenia/moth/amqp.py as and example. For that module,
the notification message logging level is upped to warning by default.
One can override it with a config file setting::

   set sarracenia.moth.amqp.AMQP.logLevel info
 
in the *__init__(self,options)* function of the callback, 
include the lines::

   me = "%s.%s" % ( __class__.__module__ , __class__.__name__ )
   if 'logLevel' in self.o['settings'][me]:
                logger.setLevel( self.o['logLevel'].upper() )



Initialization and Settings
---------------------------

The next step is declaring a class::

  class Myclass(FlowCB):

as a subclass as FlowCB.  The main routines in the class  are entry points 
that will be called at the time their name implies. If you a class is missing a
given entry point, it will just not be called. The __init__() class is used to 
initialize things for the callback class::

    def __init__(self, options):

        super().__init__(options)

        logging.basicConfig(format=self.o.logFormat,
                            level=getattr(logging, self.o.logLevel.upper()))
        logger.setLevel(getattr(logging, self.o.logLevel.upper()))

        self.o.add_option( 'myoption', 'str', 'usuallythis')

The logging setup lines in __init__ allow setting a specific logging level
for this flowCallback class. Once the logging boiler-plate is done, 
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

    def ack(self,messagelist):
        Task: acknowledge notification messages from a gather source.

    """
      application of the accept/reject clauses happens here, so after_accept callbacks
      run on a filtered set of notification messages.

    """

    def after_accept(self,worklist):
        """
         Task: just after notification messages go through accept/reject masks,
               operate on worklist.incoming to help decide which notification messages to process further.
               and move notification messages to worklist.rejected to prevent further processing.
               do not delete any notification messages, only move between worklists.
        """

    def after_work(self,worklist):
        Task: operate on worklist.ok (files which have arrived.)

    def download(self,msg) -> bool::

         Task: looking at msg['new_dir'], msg['new_file'], msg['new_inflight_file'] 
               and the self.o options perform a download of a single file.
               return True on a successful transfer, False otherwise.


    def gather(self):
        Task: gather notification messages from a source... return a list of notification messages.
        return []

    def metrics_report(self) -> dict:

        Return a dictionary of metrics. Example: number of messages remaining in retry queues.

    def on_housekeeping(self):
         do periodic processing.

    def on_html_page(self,page):
         Task: modify an html page.

    def on_line(self,line):
         used in FTP polls, because servers have different formats, modify to canonical use.

         Task: return modified line.

    def on_start(self):
         After the connection is established with the broker and things are instantiated, but
         before any notification message transfer occurs.

    def on_stop(self):
         cleanup processing when stopping.

    def poll(self):
        Task: build worklist.incoming, a form of gather()

    def post(self,worklist):
         Task: operate on worklist.ok, and worklist.failed. modifies them appropriately.
               notification message acknowledgement has already occurred before they are called.

   def send(self,msg) -> bool::

         Task: looking at msg['new_dir'], msg['new_file'], and the self.o options perform a transfer
               of a single file.
               return True on a successful transfer, False otherwise.

         This replaces built-in send functionality for individual files.

    def stop_requested(self):
         Pre-warn a flowcb that a stop has been requested, allowing processing to wrap up
         before the full stop happens.


new_* Fields
------------

During processing of notification messages, the original standard field values are generally left un-changed (as-read in.)
To change fields of notification messages forwarded to downstream consumers, one modifies new_field instead
of the one from the message, as the original is necessary for successful upstream retrieval:

* msg['new_baseUrl'] ... baseUrl to pass to downstream consumers.

* msg['new_dir'] ... the directory into which a file will be downloaded or sent.

* msg['new_file'] .... final name of the file to write.

* msg['new_inflight_path'] ... calculated name of the temporary file to be written before renaming to msg['new_file'] ... do not set manually.

* msg['new_relPath'] ... calculated from 'new_baseUrl', 'post_baseDir', 'new_dir', 'new_file' ... do not set manually.

* msg['post_version'] ... calculated the encoding format of the message to post (from settings)

* msg['new_subtopic'] ... the subtopic hierarchy that will be encoded in the notification message for downstream consumers.


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
  import GTStoWIS2

  logger = logging.getLogger(__name__)


  class GTS2WIS2(FlowCB):

    def __init__(self, options):

        super().__init__(options,logger)
        self.topic_builder=GTStoWIS2.GTStoWIS2()

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
                msg.updatePaths( self.o, new_baseDir + os.sep + new_relDir, msg['new_file'] )

            except Exception as ex:
                logger.error( "skipped" , exc_info=True )
                worklist.failed.append(msg)
                continue
    
            msg['_deleteOnPost'] |= set( [ 'from_cluster', 'sum', 'to_clusters' ] )
            new_incoming.append(msg)

        worklist.incoming=new_incoming 

The *after_accept* routine is one of the two most common ones in use.

The after_accept routine has an outer loop that cycles through the entire
list of incoming notification messages. The normal processing is that is builds a new list of 
incoming notification messages, appending all the rejected ones to *worklist.failed.* The 
list is just a list of notification messages, where each notification message is a python dictionary with
all the fields stored in a v03 format notification message. In the notification message there are, 
for example, *baseURL* and *relPath* fields:

* baseURL - the baseURL of the resource from which a file would be obtained.
* relPath - the relative path to append to the baseURL to get the complete download URL.

This is happenning before transfer (download or sent, or processing) of the file
has occurred, so one can change the behaviour by modifying fields in the notification message.
Normally, the download paths (called new_dir, and new_file) will reflect the intent
to mirror the original source tree. so if you have *a/b/c.txt*  on the source tree, and
are downloading in to directory *mine* on the local system, the new_dir would be
*mine/a/b* and new_file would be *c.txt*.

The plugin above changes the layout of the files that are to be downloaded, based on the 
`GTStoWIS <https://github.com/wmo-im/GTStoWIS>`_ class, which prescribes a different
directory tree on output.  There are a lot of fields to update when changing file 
placement, so best to use::

   msg.updatePaths( self.o, new_dir, new_file )

to update all necessary fields in the notification message properly. It will update 
'new_baseURL', 'new_relPath', 'new_subtopic' for use when posting.

The try/except part of the routine deals with the case that, should
a file arrive with a name from which a topic tree cannot be built, then an exception
may occur, and the notification message is added to the failed worklist, and will not be
processed by later plugins.

Download Renaming
------------------

Sometimes the URL used to obtain data from a server isn't the same as the name
one wants to assign to the downloaded result. This occurs often when polling upstream
arbitrary web services. For such cases the message format defines the *retrievePath*, or 
retrieval path, used as follows:

* msg['retrievePath'] = https://server/cgi-bin/get?param1=hoho&.... The retrieval URL

* msg['relPath'] = https://server/relPath/defining/local/placement ... where to download it to.

Standard subscribers will download using *retrievePath* but assign the download path using *relPath.*
When forwarding after download, the *retrievePath* should often be removed (to avoid downstream clients
pulling from the original source instead of the downloaded copy.)

While the above is a preferred way of defining messages where the download will have a different
name from the upstream source, a second method is available, the *rename* used as follows:

* msg['rename'] = alternate *relPath* ... download it to here instead of using relPath.

again, once downloaded, the *rename* header should be removed from the message prior to
forwarding to downstream clients. the *relPath* needs to be adjusted.

Note that both of these methods work the same for senders as well. The term 'download' is
used for simplicity.
  
Web Sites with non-standard file listings
-----------------------------------------

The poll/nasa_mls

Other Examples
--------------

Subclassing of Sarracenia.flowcb is used internally to do a lot of core work.
It's a good idea to look at the sarracenia source code itself. For example:

* sr3 list fcb  is a command to list all the callback classes that are
  included in the metpx-sr3 package.

* *sarracenia.flowcb* have a look at the __init__.py file in there, which
  provides this information on a more programmatically succinct format.

* *sarracenia.flowcb.gather.file.File*  is a class that implements 
  file posting and directory watching, in the sense of a callback that 
  implements the *gather* entry point, by reading a file system and building a
  list of notification messages for processing.

* *sarracenia.flowcb.gather.message.Message* is a class that implements
  reception of notification messages from message queue protocol flows.

* *sarracenia.flowcb.nodupe.NoDupe* This modules removes duplicates from message
  flows based on Integrity checksums.

* *sarracenia.flowcb.post.message.Message* is a class that implements posting
  notification messages to Message queue protocol flows

* *sarracenia.flowcb.retry.Retry* when the transfer of a file fails,
  Sarracenia needs to persist the relevant notification message to a state file for 
  a later time when it can be tried again.  This class implements
  that functionality.


Modifying Files in Flight
-------------------------

The sarracenia.transfer class has an on_data entry point::

    def on_data(self, chunk) -> bytes:
        """
            transform data as it is being read. 
            Given a buffer, return the transformed buffer. 
            Checksum calculation is based on pre transformation... likely need
            a post transformation value as well.
        """
        # modify the chunk in this body...
        return chunk

   def registered_as():
        return ['scr' ]

   # copied from sarracenia.transfer.https

   def connect(self):

        if self.connected: self.close()

        self.connected = False
        self.sendTo = self.o.sendTo.replace('scr', 'https', 1)
        self.timeout = self.o.timeout

        if not self.credentials(): return False

        return True
        


to perform inflight data modification, one can sub-class the relevant transfer class.
Such a class (scr - strip carriage returns) can be added by putting an import in the configuration 
file::

    import scr.py

then messages where the retrieval url is set to use the *scr* retrieval scheme will use this 
custome transfer protocol.


Subclassing Flow
----------------

If none of the built-in components ( poll, post, sarra, shovel, subscribe, watch, winnow ) have the 
behaviour desired, one can build a custom component to do the right thing by sub-classing flow.

Copy one of the flow sub-classes from the source code, and modify to taste.  In the configuration
file, add the line::

   flowMain myComponent

to have the flow use the new component.
