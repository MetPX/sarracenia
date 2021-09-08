

============================
Writing FlowCallback Plugins
============================


The main algorithm of sarracenia is *the flow*. All the components implement
variations of *the flow.* For details of the flow, have a look 
at `Concepts <../Explanations/Concepts.rst>`_ For any flow, one can
add customer processing at a variety of times during processing by sub-classing 
the `sarracenia.flowcb <../../sarracenia/flowcb/__init__.py>`_ class.  

The class constructor accepts a dictionary of settings, called *options*.
options is used to override default behaviour of both flows and callbacks.
To add a callback to a a flow, a line is added to the config file::

    flowcb sarracenia.flowcb.log.Log

The argument to the flowcb is a standard python class that needs to be
in the normal python path for python *import*, and the last element
is the name of the class in within the file that needs to be instantiated
as a flowcb instance.

a setting for a callback is declared as follows::

    set sarracenia.flowcb.filter.log.Log.level debug

(the prefix for the setting matches the type hierarchy in flow_callback)

when the constructor for the callback is called, it's options
argument will contain::

    options.level = 'debug'


The other main argument to a number of callback routines is the worklist.
The worklist is given to entry points occurring during message processing,
and is a number of lists of messages::

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


Logging
-------

to have python logging work normally, after all other imports, do the standard:: 

  import logging
  logger = logging.getLogger(__name__)

and then logger messages will be like so::

  logger.debug('got here')

each message in the log will be prefixed with the class and routine emitting the log message,
as well as the date/time.



Initialization and Settings
---------------------------


These are the Entry Points that will be called if declared in a flow_callback.
If you don't define a given entry point, no harm done. It will just not be calledi.
the __init__ class is used to initialize things for the callback class::

    def __init__(self, options):
        self.o = options

        logging.basicConfig(format=self.o.logFormat,
                            level=getattr(logging, self.o.logLevel.upper()))

        logger.setLevel(getattr(logging, self.o.logLevel.upper()))
        
        self.o.add_option( 'myoption', 'str')

Options to be used in callbacks can be declared in the init function, so that 
users can include them in configuration files, just like built-in options::

        myoption IsReallyNeeded

The result of such a setting is that the self.o.myoption = 'IsReallyNeeded'.
There are various *kinds* of options, where the declared type modifies the parsing::
           
           'count'      integer count type. 
           'duration'   a floating point number indicating a quantity of seconds (0.001 is 1 milisecond)
                        modified by a unit suffix ( m-minute, h-hour, w-week ) 
           'flag'       boolean (True/False) option.
           'list'       a list of string values, each succeeding occurrence catenates to the total.
                        all v2 plugin options are declared of type list.
           'size'       integer size. Suffixes k, m, and g for kilo, mega, and giga (base 2) multipliers.
           'str'        an arbitrary string value, as will all of the above types, each succeeding occurrence overrides the previous one.



Entry Points
------------


Other entry_points::

    def name(self):
        Task: return the name of a plugin for reference purposes. (automatically there)

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



Example Callback Class
----------------------

This is an example callback class that accepts files from a UNIDATA flow, and renames the directory 
tree to a different standard, and evolving one for the WMO WIS 2.0::

  import json
  import logging
  import os.path

  from sarracenia.flowcb import FlowCB
  from sarracenia.flowcb.gather import msg_dumps
  import GTStoWIS2

  logger = logging.getLogger(__name__)


  class GTS2WIS2(FlowCB):

    def find_type(self, TT):
        """
            given the TT of a WMO AHL, return the corresponding file type suffix.
        """

        if TT[0] in ['G']: return '.grid'
        elif TT[0] in ['I']: return '.bufr'
        elif TT in ['IX']: return '.hdf'
        elif TT[0] in ['K']: return '.crex'
        elif TT in ['LT']: return '.iwxxm'
        elif TT[0] in ['L']: return '.grib'
        elif TT in ['XW']: return '.txt'
        elif TT[0] in ['X']: return '.cap'
        elif TT[0] in ['D', 'H', 'O', 'Y']: return '.grib'
        elif TT[0] in ['E', 'P', 'Q', 'R']: return '.bin'
        else: return '.txt'

    def __init__(self, options):

        # FIXME: should a logging module have a logLevel setting?
        #        just put in a cookie cutter for now...
        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, options.logLevel.upper()))
        else:
            logger.setLevel(logging.INFO)

        self.topic_builder=GTStoWIS2.GTStoWIS2()
        self.o = options


    def after_accept(self, worklist):

        new_incoming=[]

        for msg in worklist.incoming:

            # /20181218/UCAR-UNIDATA/WMO-BULLETINS/IX/21/IXTD99_KNES_182147_9d73fc80e12fca52a06bf41c716cd718

            logger.info("before: %s " % msg_dumps(msg) )

            # fix file name suffix.
            type_suffix = self.find_type(msg['new_file'][0:2] )

            # correct suffix if need be.
            if ( type_suffix != 'UNKNOWN' ) and ( msg['new_file'][-len(type_suffix):] != type_suffix ):
                msg['new_file'] += type_suffix
                if 'rename' in msg:
                    msg['rename'] += type_suffix

            # /20181218/UCAR-UNIDATA/WMO-BULLETINS/IX/21/IXTD99_KNES_182147_9d73fc80e12fca52a06bf41c716cd718.cap
            tpfx=msg['subtopic']
    
            # input has relpath=/YYYYMMDD/... + pubTime
            # need to move the date from relPath to BaseDir, adding the T hour from pubTime.
            new_baseSubDir=tpfx[0]+msg['pubTime'][8:11]
            t='.'.join(tpfx[0:2])+'.'+new_baseSubDir
            logger.error('new_baseSubDir=%s, t=%s' % ( new_baseSubDir, t ) )
            try:
                new_baseDir = msg['new_dir'] + os.sep + new_baseSubDir
                new_relDir = 'WIS' + os.sep + self.topic_builder.mapAHLtoTopic(msg['new_file'])
                msg['new_dir'] = new_baseDir + os.sep + new_relDir
                self.o.set_newMessageUpdatePaths( msg, new_baseDir + os.sep + new_relDir, msg['new_file'] )

            except Exception as ex:
                logger.error( "skipped" , exc_info=True )
                worklist.failed.append(msg)
                continue
    
            msg['_deleteOnPost'] |= set( [ 'from_cluster', 'sum', 'to_clusters' ] )
            new_incoming.append(msg)
            logger.info("accepted: %s " % msg_dumps(msg) )

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
directory tree on output. To change the delivery directory, one needs to change:

* new_dir - gives the complete directory path to which the file will be written.
* new_file - gives the name to which the file will be written.
* subtopic - will be used to build the topics for downstream subscribers.

There are a lot of fields to update when changing file placement, so
best to use::

   self.o.set_newMessageUpdatePaths( msg, new_dir, new_file )

when changing the file placement, as it will update all necessary fields in the
message properly.

If a file arrives with a name from which a topic tree cannot be built, then an exception
may occur, and the message is added to the failed worklist.



