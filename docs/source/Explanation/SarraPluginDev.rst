
=============================
 Sarracenia Programming Guide
=============================

---------------------
 Working with Plugins
---------------------

Revision Record
---------------

:version: |release|
:date: |today|

Audience
--------

Readers of this manual should be comfortable with light scripting in Python version 3.
While a great deal of v2 compatibility is included in Sarracenia version 3, wholesale
replacement of the programming interfaces is a big part of what is in Version 3. 
If working with version 2, Programmers should refer to the version 2 programmer's Guide,
as the two are very different.

Introduction
------------

Sarracenia v3 includes a number of points where processing can be customized by
small snippets of user provided code, known as flowCallbacks. The flowCallbacks themselves
are expected to be concise, and an elementary knowledge of Python should suffice to
build new ones in a copy/paste manner, with many samples being available to read.  

There are other ways to extend Sarracenia v3 by subclassing of:

* Sarracenia.transfer.Transfer to add more data transfer protocols 
* Sarracenia.identity.Identity to add more checksumming methods.
* Sarracenia.moth.Moth to add support for more messaging protocols.
* Sarracenia.flow.Flow to create new flows. 
* Sarracenia.flowcb.FlowCB to add custom callback routines to flows.
* Sarracenia.flowcb.poll.Poll to customize poll flows.
* Sarracenia.flowcb.scheduled.Scheduled to customize scheduled flows.

That will be discussed after callbacks are dealt with.


Introduction
------------

A Sarracenia data pump is a web server with notifications for subscribers to
know, quickly, when new data has arrived. To find out what data is already
available on a pump, view the tree with a web browser.  For simple immediate
needs, one can download data using the browser itself or through a standard tool
such as wget. The usual intent is for sr_subscribe to automatically download
the data wanted to a directory on a subscriber machine where other software
can process it.

Often, the purpose of automated downloading is to have other code ingest
the files and perform further processing. Rather than having a separate
process look at a file in a directory, one can insert customized
processing at various points in the flow.

Examples are available using the list command::

    fractal% sr3 list fcb
    Provided plugins: ( /home/peter/Sarracenia/v03_wip/sarra ) 
    flowcb/gather/file.py            flowcb/gather/message.py         flowcb/line_log.py               flowcb/line_mode.py
    flowcb/filter/deleteflowfiles.py flowcb/filter/fdelay.py          flowcb/filter/log.py             flowcb/nodupe.py
    flowcb/post/log.py               flowcb/post/message.py           flowcb/retry.py                  flowcb/v2wrapper.py
    fractal%
    fractal% fcbdir=/home/peter/Sarracenia/v03_wip/sarra

Worklists
~~~~~~~~~

The worklist data structure is a set of lists of notification messages.  There are four:

  * worklist.incoming -- notification messages yet to be processed. (built by gather)
  * worklist.rejected -- notification message which are not to be further processed. (usually by filtering.)
  * worklist.ok -- notification messages which have been successfully processed. (usually by work.)
  * worklist.failed   -- notification messages for which processing was attempted, but it failed. 

The worklist is passed to the *after_accept* and *after_work* plugins as detailed in the next section.

The Flow Algorithm
~~~~~~~~~~~~~~~~~~

All of the components (post, subscribe, sarra, sender, shovel, watch, winnow)
share substantial code and differ only in default settings.  The Flow
algorithm is:

* Gather a list of notification messages, from a file, or an upstream source of notification messages (a data pump.)
  places new notification messages in _worklist.incoming_

* Filter them with accept/reject clauses, rejected notification messages are moved to _worklist.rejected_ .
  after_accept callbacks further manipulate the worklists after initial accept/reject filtering.

* Work on the remaining incoming notification messages, by doing the download, send or other work that creates new files.
  when work for a notification message succeeds, the notification message is moved to the _worklist.ok_ .
  work work for a notification message fails, the notification message is moved to the _worklist.failed_ .
  
* (optional) Post the work accomplished (notification messages on _worklist.ok_ ) for the next flow to consume.


Flow Callbacks
--------------

The many ways to extend functionality, the most common one being adding callbacks
to flow components. All of the Sarracenia components are implemented using
the sarra.flow class. There is a parent class sarra.flowcb to implement them.
The package's plugins are shown in the first grouping of available ones. Many of them have arguments which
are documented by listing them. In a configuration file, one might have the line::

    flowCallback sarracenia.flowcb.log.Log

That line cause Sarracenia to look in the Python search path for a class like:

.. code:: python

  blacklab% cat sarra/flowcb/msg/log.py

  from sarracenia.flowcb import FlowCB
  import logging

  logger = logging.getLogger(__name__)

  class Log(FlowCB):
    def after_accept(self, worklist):
        for msg in worklist.incoming:
            logger.info("received: %s " % msg)

    def after_work(self, worklist):
        for msg in worklist.ok:
            logger.info("worked successfully: %s " % msg)

The module will print each notification message accepted, and each notification message after work on it 
has finished (download has occurred, for example.) To modify the callback class, 
copy it from the directory listed in the *list fcb* command to somewher in the
environment's PYTHONPATH, and then modify it for the intended purpose.

One can also see which plugins are active in a configuration by looking at the notification messages on startup::

   blacklab% sr3 foreground subscribe/clean_f90
   2018-01-08 01:21:34,763 [INFO] sr_subscribe clean_f90 start

   .
   .
   .

   2020-10-12 15:20:06,250 [INFO] sarra.flow run callbacks loaded: ['sarra.flowcb.retry.Retry', 'sarra.flowcb.msg.log.Log', 'file_noop.File_Noop', 'sarra.flowcb.v2wrapper.V2Wrapper', 'sarra.flowcb.gather.message.Message'] 2
   .
   .
   .
   blacklab% 

Use of the *flowCallbackPrepend* option will have the the class loaded at the beginning of the list, rather than
at the end.



Settings
--------

Often when writing extensions through subclassing, additional options need to be set. The 
sarracenia.config class does command-line and configuration file based
option parsing. and has a routine that can be called from new code
to define additional settings, usually from the __init__ routine, which
in built-in classes and such as flowcb accept as an _options_ parameter
on their __init__() routines::

      somewhere in the __init__(self, options):

      options.add_option('accel_wget_command', 'str', '/usr/bin/wget')


      def add_option(self, option, kind='list', default_value=None):
           
      """
           options can be declared in any plugin. There are various *kind* of options, where the declared type modifies the parsing.
           
           'count'      integer count type. 
           'duration'   a floating point number indicating a quantity of seconds (0.001 is 1 milisecond)
                        modified by a unit suffix ( m-minute, h-hour, w-week ) 
           'flag'       boolean (True/False) option.
           'list'       a list of string values, each succeeding occurrence catenates to the total.
                        all v2 plugin options are declared of type list.
           'size'       integer size. Suffixes k, m, and g for kilo, mega, and giga (base 2) multipliers.
           'str'        an arbitrary string value, as will all of the above types, each succeeding occurrence overrides the previous one.
           
      """

The example above defines an "accel\_wget\_command" option 
as being of string type, with default value _/usr/bin/wget\_ .

Other useful methods in the sarracenia.config.Config class:

* variableExpansion( value, Message=None) ... to expand patterns such as ${YYYYMMDD-5m} in configuration files.
  one may want to evaluate these expansions at different times in processing, depending on the purpose
  of the user defined options.

full list here: https://metpx.github.io/sarracenia/Reference/code.html#sarracenia.config.Config


Hierarchical Settings
~~~~~~~~~~~~~~~~~~~~~

One can also create settings specifically for individual callback classes using the _set_ 
command and by identifying the exact class to which the setting applies. For example,
sometimes turning the logLevel to debug can result in very large log files, and one would
like to only turn on debug output for select callback classes. That can be done via::

    set sarracenia.flowcb.gather.file.File.logLevel debug

The _set_ command, can also be used to set options to be passed to any plugin.


Viewing all Settings
~~~~~~~~~~~~~~~~~~~~

Use the _sr3_ _show_ command to view all active settings resulting from a configuration file::

    fractal% sr3 show sarra/download_f20.conf
    
    Config of sarra/download_f20: 
    _Config__admin=amqp://bunnymaster@localhost, _Config__broker=amqp://tfeed@localhost, _Config__post_broker=amqp://tfeed@localhost, accel_threshold=100.0,
    accept_unmatch=True, accept_unmatched=False, announce_list=['https://tracker1.com', 'https://tracker2.com', 'https://tracker3.com'], attempts=3,
    auto_delete=False, baseDir=None, batch=1, bind=True, bindings=[('v03', 'xsarra', '#')], bufsize=1048576, bytes_per_second=None, bytes_ps=0,
    cfg_run_dir='/home/peter/.cache/sr3/sarra/download_f20', chmod=0, chmod_dir=509, chmod_log=384, config='download_f20', currentDir=None, debug=False,
    declare=True, declared_exchanges=['xpublic', 'xcvan01'], declared_users="...rce', 'anonymous': 'subscriber', 'ender': 'source', 'eggmeister': 'subscriber'}",
    delete=False, directory='/home/peter/sarra_devdocroot', documentRoot=None, download=False, durable=True, exchange=['xflow_public'],
    expire=25200.0, feeder=amqp://tfeed@localhost, filename=None, fixed_headers={}, flatten='/', hostdir='fractal', hostname='fractal', housekeeping=60.0,
    imports=[], inflight=None, inline=False, inlineEncoding='guess', inlineByteMax=4096, instances=1,
    logFormat='%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s', logLevel='info', log_reject=True, lr_backupCount=5, lr_interval=1,
    lr_when='midnight', masks="...nia/insects/flakey_broker', None, re.compile('.*'), True, True, 0, False, '/')]", message_count_max=0, message_rate_max=0,
    message_rate_min=0, message_strategy={'reset': True, 'stubborn': True, 'failure_duration': '5m'}, message_ttl=0, mirror=True, notify_only=False,
    overwrite=True, plugins=['sample.Sample', 'sarracenia.flowcb.log.Log'], post_baseDir='/home/peter/sarra_devdocroot', post_baseUrl='http://localhost:8001',
    post_documentRoot=None, post_exchange=['xflow_public'], post_exchanges=[], prefetch=1, preserve_mode=True, preserve_time=False, program_name='sarra',
    pstrip=False, queue_filename='/home/peter/.cache/sr3/sarra/download_f20/sarra.download_f20.tfeed.qname',
    queue_name='q_tfeed_sarra.download_f20.65966332.70396990', randid='52f9', realpathPost=False, report=False, report_daemons=False, reset=False,
    resolved_exchanges=['xflow_public'], resolved_qname='q_tfeed_sarra.download_f20.65966332.70396990', settings={}, sleep=0.1, statehost=False, strip=0,
    subtopic=None, suppress_duplicates=0, suppress_duplicates_basis='path', timeout=300, tlsRigour='normal', topicPrefix='v03',
    undeclared=['announce_list'], users=False, v2plugin_options=[], v2plugins={}, vhost='/', vip=None
    
    fractal% 


Logging Control
---------------

The method of understanding sr3 flow activity is by examining its logs.
Logging can be very heavy in sr3, so there are many ways of fine tuning it.


logLevel
~~~~~~~~

the normal logLevel one is used to in the built-in python Log classes. It has 
levels: *debug, info, warning, error,* and *critical,*  where level indicates
the lowest priority message to print.  Default value is *info*.

Because a simple binary switch of the logLevel can result in huge logs, for
example when polling, where every time every line is polled could generate a log line.
The monitoring of MQP protocols can be similarly verbose, so by default neither
of these are actually put into debug mode by the global logLevel setting.
some classes do not honour the global setting, and ask for explicit
enabling:

set sarracenia.transfer.Transfer.logLevel debug
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Can control the logLevel used in transfer classes, to set it lower or higher
than the rest of sr3.


set sarracenia.moth.amqp.AMQP.logLevel debug
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Print out debug messages specific to the AMQP message queue (sarracenia.moth.amqp.AMQP class).
used only when debugging with the MQP itself, such as dealing with broker connectivity issues.
interop diagnostics & testing.

set sarracenia.moth.mqtt.MQTT.logLevel debug
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Print out debug messages specific to the MQTT message queue (sarracenia.moth.mqtt.MQTT class).
used only when debugging with the MQP itself, such as dealing with broker connectivity issues.
interop diagnostics & testing.

logEvents
~~~~~~~~~

default: *after_accept, after_work, on_housekeeping*
available: after_accept, after_work, all, gather, on_housekeeping, on_start, on_stop, post

implemented by the *sarracenia.flowcb.log.Log* class, one can select which events generate log
messages. wildcard: *all* generates log messages for every event known to the *Log* class.



logMessageDump
~~~~~~~~~~~~~~

implemented by sarracenia.flowcb.log, at each logging event, print out the current content
of the notification message being processed.

logReject
~~~~~~~~~

print out a log message for each notification message rejected (normally silently ignored.)


messageDebugDump
~~~~~~~~~~~~~~~~

Implemented in moth sub-classes, prints out the bytes actually received or sent
for the MQP protocol in use.


Debugging in callbacks
~~~~~~~~~~~~~~~~~~~~~~

Pythonic logging involves having distinct logging objects per file. So adding debugging levels
requires setting debug up in each class where you need it.  To turn debugging on in callback,
for example one called convert.geps_untar, in the config file place::

  convert.geps_untar.logLevel debug

and in addition, if that flow_callback does not have an __init__() entry point, one will
need to add it::


    def __init__(self,options):
        super().__init__(options,logger)

This will apply the log formatting and priority to the logger in the current file.


Extending Classes
-----------------

One can add additional functionality to Sarracenia by creating subclassing.

* sarra.moth - Messages Organized into Topic Hierarchies. (existing ones: rabbitmq-amqp)

* sarra.identity - checksum algorithms ( existing ones: md5, sha512, arbitrary, random )

* sarra.transfer - additional transport protocols  (https, ftp, sftp )

* sarra.flow - creation of new components beyond the built-in ones. (post, sarra, shovel, etc...)
 
* sarra.flowcb - customization of component flows using callbacks.

* sarra.flowcb.poll - customization of poll callback for non-standard sources.


One would start with the one of the existing classes, copy it somewhere else in the python path,
and build your extension. These classes are added to Sarra using the *import* option
in the configuration files. the __init__ files in the source directories are the good
place to look for information about each class's API.


The Simplest Flow_Callback
--------------------------



Sample Extensions
-----------------

Below is a minimal flowCallback sample class, that would be in a sample.py
file placed in any directory in the PYTHONPATH::

    import logging
    import sarracenia.flowcb

    # this logger declaration  must be after last import (or be used by imported module)
    logger = logging.getLogger(__name__)

    class Sample(sarracenia.flowcb.FlowCB):

        def __init__(self, options):

            super().__init__(options,logger)
            # declare a module specific setting.
            options.add_option('announce_list', list )

        def on_start(self):

            logger.info('announce_list: %s' % self.o.announce_list )

All it does is add a setting called 'announce-list' to the configuration
file grammar, and then print the value on start up.  

In a configuration file one, would expect to see::

   flowCallback sample.Sample

   announce_list https://tracker1.com
   announce_list https://tracker2.com
   announce_list https://tracker3.com

And on startup, the logger message would print::

   021-02-21 08:27:16,301 [INFO] sample on_start announce_list: ['https://tracker1.com', 'https://tracker2.com', 'https://tracker3.com']



Developers can add additional Transfer protocols for notification messages or 
data transport using the *import* directive to make the new class
available::

  import torr

would be a reasonable name for a Transfer protocol to retrieve
resources with bittorrent protocol.  *import* can also be used
to import arbitrary python modules for use by callbacks.


Fields in Messages
------------------

callbacks receive the parsed sarracenia.options as a parameter.  
self is the notification message being processed. variables variables most used:

*msg['exchange']*  
  The exchange through which the notification message is being posted or consumed.

*msg['isRetry']*
  If this is a subsequent attempt to send or download a notification message.

*msg['new_dir']*
  The directory which will contain *msg['new_file']*

*msg['new_file']*
  A popular variable in on_file and on_part plugins is: *msg['new_file*,
  giving the file name the downloaded product has been written to.  When the
  same variable is modified in an after_accept plugin, it changes the name of
  the file to be downloaded. Similarly another often used variable is 
  *parent.new_dir*, which operates on the directory to which the file
  will be downloaded.

*msg['new_inflight_file']*
  in download and send callbacks this field will be set with the temporary name
  of a file used while the transfer is in progress. Once the transfer is complete,
  the file should be renamed to what is in *msg['new_file']*.

*msg['pubTime']*
  The time the notification message was originally inserted into the network (first field of a notice.)

*msg['baseUrl']*
  The root URL of the publication tree from which relative paths are constructed.

*msg['relPath']*
  The relative path from the baseURL of the file.
  concatenating the two gives the complete URL.

*msg['fileOp']*
  for non data download file operations, such as creation of symbolic links, file renames and removals.
  content described in `sr_post(7) <../Reference/sr_post.7.html>`_

*msg['identity']*
  The checksum structure, a python dictionary with 'method' and 'value' fields.

*msg['subtopic'], msg['new_subtopic']*
  list of strings (with the topic prefix stripped off)
  do not use, as it will be generated from msg['new_relPath'] when the message is published.

*msg['_deleteOnPost']*
  when state needs to be stored in messages, one can declare additional temporary fields
  for use only within the running process.  To mark them for deletion when forwarding,
  this set valued field is used::

      msg['my_new_field'] = my_temporary_state
      msg['_deleteOnPost'] |= set(['my_new_field'])

  For example, all of the *new_* fields are in the *_deleteOnPost* by default.

*msg['onfly_checksum'], msg['data_checksum']*
   the value of an *Identity* checksum field calculated as data is downloaded.
   In the case where data is modified while downloading, the *onfly_checksum*
   is to verify that the upstream data was correctly received, while the
   *data_checksum* is calculated for downstream consumers.

These are the notification message fields which are most often of interest, but many other 
can be viewed by the following in a configuration::

   logMessageDump True
   callback log

Which ensures the log flowcb class is active, and turns on the setting
to print rawish notification messages during processing.


Accessing Options
-----------------

The settings resulting from parsing the configuration files are also readily available.
Plugins can define their own options by calling::

   FIXME: api incomplete.
   Config.add_option( option='name_of_option', kind, default_value  )

Options so declared just become instance variables in the options passed to init.
By convention, plugins set self.o to contain the options passed at init time, so that 
all the built-in options are similarly processing.  If consult the `sr_subscribe(1) <../Reference/sr3.1.html#subscribe>`_
manual page, and most of the options will have a corresponing instance variable.

Some examples:

*self.o.baseDir*
  the base directory for where files are when consuming a post.

*self.o.suppress_duplicates*
  Numerical value indicating the caching lifetime (how old entries should be before they age out.)
  Value of 0 indicates caching is disabled.

*self.o.inflight*
  The current setting of *inflight* (see `Delivery Completion <FileCompletion.html>`_

*self.o.overwrite*
  setting which controls whether to files already downloaded should be overwritten unconditionally.

*self.o.discard*
  Whether files should be removed after they are downloaded.




Flow Callback Points
--------------------

Sarracenia will interpret the names of functions as indicating times in processing when
a given routine should be called.

View the `FlowCB source <https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/__init__.py>`_
for detailed information about call signatures and return values, etc...

+---------------------+----------------------------------------------------+
|  Name               | When/Why it is Called                              |
+=====================+====================================================+
|  ack                | acknowledge notification messages from a broker.   |
|                     |                                                    |
+---------------------+----------------------------------------------------+
|                     | very freqently used.                               |
|                     |                                                    |
|                     | can just modify messages in worklist.incoming.     |
|                     | adding a field, or changing a value.               |
|                     |                                                    |
|                     | Move messages among lists of messages in worklist. |
| after_accept        | to reject a message, it is moved from              |
| (self,worklist)     | worklist.incoming -> worklist.rejected.            |
|                     | (will be acknowledged and discarded.)              |
|                     |                                                    |
|                     | To indicate a message has been processed, move     |
|                     | worklist.incoming -> worklist.ok                   |
|                     | (will be acknowledged and discarded.)              |
|                     |                                                    |
|                     | To indicate failure to process, move:              |
|                     | worklist.incoming -> worklist.failed               |
|                     | (will go on retry queue for later.)                |
|                     |                                                    |
|                     | Examples: msg_* in the examples directory          |
|                     |                                                    |
|                     | msg_delay - make sure messages are old before      |
|                     | processing them.                                   |
|                     |                                                    |
|                     | msg_download - change messages to use different    |
|                     | downloaders based on file size (built-in for small |
|                     | ones, binary downloaders for large files.)         |
|                     |                                                    |
|                     |                                                    |
+---------------------+----------------------------------------------------+
|                     | called after When a transfer has been attempted.   |
| after_work          |                                                    |
| (self,worklist)     | All messages are acknowledged by this point.       |
|                     | worklist.ok contains successful transfers          |
|                     | worklist.failed contains failed transfers          |
|                     | worklist.rejected contains transfers rejected      |
|                     | during transfer.                                   |
|                     |                                                    |
|                     | usually about doing something with the file after  |
|                     | download has completed.                            |
|                     |                                                    |
+---------------------+----------------------------------------------------+
| destfn(self,msg):   | called when renaming the file from inflight to     |
|                     | permanent name.                                    |
|                     |                                                    |
|                     | return the new name for the downloaded/sent file.  |
+---------------------+----------------------------------------------------+
| download(self,msg)  | replace built-in downloader return true on success |
|                     | takes message as argument.                         |
+---------------------+----------------------------------------------------+
| gather(self)        | gather messages from a source, returns a list of   |
|                     | messages.                                          |
+---------------------+----------------------------------------------------+
|                     | Called every housekeeping interval (minutes)       |
|                     | used to clean cache, check for occasional issues.  |
|                     | manage retry queues.                               |
| on_housekeeping     |                                                    |
| (self)              | return False to abort further processing           |
|                     | return True to proceed                             |
|                     |                                                    |
|                     |                                                    |
+---------------------+----------------------------------------------------+
|                     | when a componente (e.g. sr_subscribe) is started.  |
| on_start(self)      | Can be used to read state from files.              |
|                     |                                                    |
|                     | state files in self.o.user_cache_dir               |
|                     |                                                    |
|                     | return value ignored                               |
|                     |                                                    |
|                     | example: file_total_save.py [#]_                   |
|                     |                                                    |
+---------------------+----------------------------------------------------+
|                     | when a component (e.g. sr_subscribe) is stopped.   |
| on_stop(self)       | can be used to persist state.                      |
|                     |                                                    |
|                     | state files in self.o.user_cache_dir               |
|                     |                                                    |
|                     | return value ignored                               |
|                     |                                                    |
+---------------------+----------------------------------------------------+
| poll(self)          | replace the built-in poll method.                  |
|                     | return a list of notification messages.            |
+---------------------+----------------------------------------------------+
| post(self,worklist) | replace the built-in post routine.                 |
|                     |                                                    |
+---------------------+----------------------------------------------------+
| send(self,msg)      | replace the built-in send routine.                 |
|                     |                                                    |
+---------------------+----------------------------------------------------+

DESTFNSCRIPTS
~~~~~~~~~~~~~

As a compatibility layer with the ancestor MetPX Sundew, Sarracenia implements
*Destination File Naming Scripts*, where the one can create a flowcallback
class with a *destfn* entry point, and then use that to set the name of
the file that will be downloaded. 

In the configuration file, one can use the filename option like so::

  filename DESTFNSCRIPT=destfn.sample

To identify a class containing the destfn entry point to be applied.
using the filename directive applies it to all files. One can also
do it selectively in the configuration file's accept clause::

  accept k.* DESTFNSCRIPT=destfn.sample

which has it call the routine to rename only selected files (starting with *k*
as per the accept clause) 

The destfn routine takes the notification message as an argument and should return
the new file name as a string.


Callbacks that need Python Modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some callbacks need to use other python modules.  While normal imports
are fine, one can integrate them better for sr3 users by supporting
the *features* mechism::

    from sarracenia.featuredetection import features
    #
    # Support for features inventory mechanism.
    #
    features['clamd'] = { 'modules_needed': [ 'pyclamd' ], 'Needed': True,
            'lament' : 'cannot use clamd to av scan files transferred',
            'rejoice' : 'can use clamd to av scan files transferred' }

    try:
        import pyclamd
        features['clamd']['present'] = True
    except:
        features['clamd']['present'] = False

This lets users know which *features* are available in their installetion
so when they run *sr3 features* it provides an easily understood list of missing
libraries::

    fractal% sr3 features
    2023-08-07 13:18:09,219 1993037 [INFO] sarracenia.flow loadCallbacks flowCallback plugins to load: ['sarracenia.flowcb.retry.Retry', 'sarracenia.flowcb.housekeeping.resources.Resources', 'dcpflow', 'log', 'post.message', 'clamav']
    2023-08-07 13:18:09,224 1993037 [INFO] dcpflow __init__ really I mean hi
    2023-08-07 13:18:09,224 1993037 [WARNING] sarracenia.config add_option multiple declarations of lrgs_download_redundancy=['Yes', 'on'] choosing last one: on
    2023-08-07 13:18:09,225 1993037 [INFO] dcpflow __init__  lrgs_download_redundancy is True
    2023-08-07 13:18:09,225 1993037 [INFO] sarracenia.flowcb.log __init__ flow initialized with: {'post', 'on_housekeeping', 'after_work', 'after_accept', 'after_post'}
    2023-08-07 13:18:09,226 1993037 [CRITICAL] sarracenia.flow loadCallbacks flowCallback plugin clamav did not load: 'pyclamd'
    
    Status:    feature:   python imports:      Description:
    Installed  amqp       amqp                 can connect to rabbitmq brokers
    Installed  appdirs    appdirs              place configuration and state files appropriately for platform (windows/mac/linux)
    Installed  filetypes  magic                able to set content headers
    Installed  ftppoll    dateparser,pytz      able to poll with ftp
    Installed  humanize   humanize             humans numbers that are easier to read.
    Absent     mqtt       paho.mqtt.client     cannot connect to mqtt brokers
    Installed  redis      redis,redis_lock     can use redis implementations of retry and nodupe
    Installed  sftp       paramiko             can use sftp or ssh based services
    Installed  vip        netifaces            able to use the vip option for high availability clustering
    Installed  watch      watchdog             watch directories
    Installed  xattr      xattr                on linux, will store file metadata in extended attributes
    MISSING    clamd      pyclamd              cannot use clamd to av scan files transferred
    
     state dir: /home/peter/.cache/sr3
     config dir: /home/peter/.config/sr3
    
    fractal%
    
You can see that that clamd feature is disabled because the pyclamd python library is not installed.




Flow Callback Poll Customization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A built-in subclass of flowcb, sarracenia.flowcb.poll.Poll implements the bulk
of sr3 polling. There are many times different types resources to poll, and 
so many options to customize it are needed. Customization is accomplished
via sub-classing, so the top of such an callback looks like::

   ...
   from sarracenia.flowcb.poll import Poll
   ....

   class Nasa_mls_nrt(Poll):

Rather than implementing a flowcb class, one subclasses the 
flowcb.poll.Poll class.  Here are the common poll
subclass specific entry points usually implemented in sub-classes:

+-------------------+----------------------------------------------------+
|                   | in sr_poll if you only want to change how the      |
| handle_data       | downloaded html URL is parsed, override this       |
|                   |                                                    |
|                   | action:                                            |
|                   | parse parent.entries to make self.entries          |
|                   |                                                    |
|                   | Examples:  html_page* in the examples directory    |
|                   |                                                    |
|                   |                                                    |
+-------------------+----------------------------------------------------+
|                   | in sr_poll if sites have different remote formats  |
|                   | called to parse each line in parent.entries.       |
| on_line           |                                                    |
|                   | Work on parent.line                                |
|                   |                                                    |
|                   | return False to abort further processing           |
|                   | return True to proceed                             |
|                   |                                                    |
|                   | Examples:  line_* in the examples directory        |
|                   |                                                    |
+-------------------+----------------------------------------------------+

Examination of the built-in `flowcb Poll <https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/poll/__init__.py>`_
class is helpful 

.. [#] see `smc_download_cp <https://github.com/MetPX/sarracenia/blob/v2_stable/sarra/plugins/smc_download_cp.py>`_
.. [#] see `Issue 74 <https://github.com/MetPX/sarracenia/issues/74>`_
.. [#] see `part_clanav_scan.py  <https://github.com/MetPX/sarracenia/blob/v2_stable/sarra/plugins/part_clanav_scan.py>`_
.. [#] see `file_total_save.py  <https://github.com/MetPX/sarracenia/blob/v2_stable/sarra/plugins/file_total_save.py>`_
.. [#] see `poll_email_ingest.py  <https://github.com/MetPX/sarracenia/blob/v2_stable/sarra/plugins/poll_email_ingest.py>`_

---------------------
Better File Reception
---------------------

For example, rather than using the file system, sr_subscribe could indicate when each file is ready
by writing to a named pipe::

  blacklab% sr_subscribe edit dd_swob.conf 

  broker amqps://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#

  flowcb sarracenia.flowcb.work.rxpipe.RxPipe
  rxpipe_name /tmp/dd_swob.pipe

  directory /tmp/dd_swob
  mirror True
  accept .*

  # rxpipe is a builtin on_file script which writes the name of the file received to
  # a pipe named '.rxpipe' in the current working directory.

With the *flowcb* option, one can specify a processing option such as rxpipe. With rxpipe,
every time a file transfer has completed and is ready for post-processing, its name is written
to the linux pipe (named .rxpipe) in the current working directory. So the code for post-processing
becomes::

  do_something <.rxpipe

No filtering out of working files by the user is required, and ingestion of partial files is
completely avoided.

.. NOTE::
   In the case where a large number of sr_subscribe instances are working
   on the same configuration, there is slight probability that notifications
   may corrupt one another in the named pipe.
   We should probably verify whether this probability is negligeable or not.


Advanced File Reception
-----------------------

The *after_work* entry point in a *sarracenia.flowcb* class is an action to perform 
after receipt of a file (or after sending, in a sender.) The RxPipe module is an example
provided with sarracenia::

  import logging
  import os
  from sarracenia.flowcb import FlowCB

  logger = logging.getLogger(__name__)

  class RxPipe(FlowCB):

      def __init__(self,options):

          super().__init__(options,logger)
          self.o.add_option( option='rxpipe_name', kind='str' )

      def on_start(self):
          if not hasattr(self.o,'rxpipe_name') and self.o.file_rxpipe_name:
              logger.error("Missing rxpipe_name parameter")
              return
          self.rxpipe = open( self.o.rxpipe_name, "w" )

      def after_work(self, worklist):

          for msg in worklist.ok:
              self.rxpipe.write( msg['new_dir'] + os.sep + msg['new_file'] + '\n' )
          self.rxpipe.flush()
          return None


With this fragment of Python, when sr_subscribe is first called, it ensures that
a pipe named npipe is opened in the specified directory by executing
the __init__ function within the declared RxPipe python class.  Then, whenever
a file reception is completed, the assignment of *self.on_file* ensures that
the rx.on_file function is called.

The rxpipe.on_file function just writes the name of the file downloaded to
the named pipe.  The use of the named pipe renders data reception asynchronous
from data processing. As shown in the previous example, one can then
start a single task *do_something* which processes the list of files fed
as standard input to it, from a named pipe.

In the examples above, file reception and processing are kept entirely separate. If there
is a problem with processing, the file reception directories will fill up, potentially
growing to an unwieldy size and causing many practical difficulties. When a plugin such
as on_file is used, the processing of each file downloaded is run before proceeding
to the next file.

If the code in the on_file script is changed to do actual processing work, then
rather than being independent, the processing could provide back pressure to the
data delivery mechanism.  If the processing gets stuck, then the sr_subscriber
will stop downloading, and the queue will be on the server, rather than creating
a huge local directory on the client.  Different models apply in different
situations.

An additional point is that if the processing of files is invoked
in each instance, providing very easy parallel processing built
into sr_subscribe.


Using Credentials in Plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To implement support of additional protocols, one often needs credentials
value in the script with the code :

- **ok, details = self.o.credentials.get(msg.urlcred)**
- **if details  : url = details.url**

The details options are element of the details class (hardcoded):

- **print(details.ssh_keyfile)**
- **print(details.passive)**
- **print(details.binary)**
- **print(details.tls)**
- **print(details.prot_p)**

For the credential that defines protocol for download (upload),
the connection, once opened, is kept open. It is reset
(closed and reopened) only when the number of downloads (uploads)
reaches the number given by the  **batch**  option (default 100).

All download (upload) operations use a buffer. The size, in bytes,
of the buffer used is given by the **bufsize** option (default 8192).


Why v3 API should be used whenever possible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* uses importlib from python, much more standard way to register plugins.
  now syntax errors will be picked up just like any other python module being imported,
  with a reasonable error message.

* no strange decoration at end of plugins (self.plugin = , etc... just plain python.)
  Entirely standard python modules, just with known methods/functions

* The strange choice of *parent* as a place for storing settings is puzzling to people.
  *parent* instance variable becomes *options*,  *self.parent* becomes *self.o*

* plural event callbacks replace singular ones.  after_accept replaces on_message

* notification messages are just python dictionaries. fields defined by json.loads( v03 payload format )
  notification messages only contain the actual fields, no settings or other things...
  plain data.

* what used to be called plugins, are now only a type of plugins, called flowCallbacks.
  They now move notification messages between worklists. 


With this API, dealing with different numbers of input and output files becomes much
more natural, when unpacking a tar file, notification messages for the unpacked files can be appended
to the ok list, so they will be posted when the flow arrives there.
Similarly a large number of small files may be bucketed together to make one
large file. so rather than transferring all the incoming files to the list,
only the resulting tar bucket will be placed in ok.

The *import* mechanism described below provides a straightforward means
of extending Sarracenia by creating children of the main classes 

* moth (messages organized in topic hierarchies) for dealing with new message protocols.
* transfer ... for adding new protocols for file transfers.
* flow .. new components with different flow from the built-in ones.

In v2, there was no equivalent extension mechanism, and adding protocols
would have required re-working of core code in a custom way for every addition.


-------------------------------------
File Notification Without Downloading
-------------------------------------

If the data pump exists in a large shared environment, such as
a Supercomputing Centre with a site file system, 
the file might be available without downloading.  So just
obtaining the file notification and transforming it into a
local file is sufficient::

  blacklab% sr_subscribe edit dd_swob.conf 

  broker amqps://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#
  document_root /data/web/dd_root
  download off
  flowcb msg_2local.Msg2Local
  flowcb do_something.DoSomething

  accept .*
  
There should be two files in the PYTHONPATH somewhere containing 
classes derived from FlowCB with after_accept routines declared.
The processing in those routines will be done on receipt of a batch
of notification messages.  A notification message will correspond to a file.

the after_accept routins accept a worklist as an argument.  


.. warning::
   **FIXME**: perhaps show a way of checking the parts header to
   with an if statement in order to act on only the first part notification message
   for long files.



Extension Ideas
---------------

Examples of things that would be fun to do with plugins:

- Common Alerting Protocol (CAP), is an XML format that provides a warnings
  for many types of events, indicating the area of coverage.  There is a 
  'polygon' field in the warning, that the source could add to messages using
  an on_post plugin.  Subscribers would have access to the 'polygon' header
  through use of an after_accept plugin, enabling them to determine whether the
  alert affected an area of interest without downloading the entire warning.

- A source that applies compression to products before posting, could add a
  header such as 'uncompressed_size' and 'uncompressed_sum' to allow 
  subscribers with an after_accept plugin to compare a file that has been locally
  uncompressed to an upstream file offered in compressed form.

- add Bittorrent, S3, IPFS as transfer protocols (sub-classing Transfer)

- add additional message protocols (sub-classing Moth)

- additional checksums, subclassing Identity. For example, to get GOES DCP
  data from sources such as USGS Sioux Falls, the reports have a trailer
  that shows some antenna statistics from the reception site.  So if one
  receives GOES DCP from Wallops, for example, the trailer will be different
  so checksumming the entire content will have different results for the
  same report.


-------
Polling
-------

To implement a customized poll, declare it as a subclass of Poll 
(sarracenia.flowcb.poll.Poll), and only the needed The routine (in this case 
the html parsing "handle_data") need be written to override the behaviour provided 
by the parent class.

( https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/poll/__init__.py )

The plugin has a main "parse" routine, which invokes the html.parser class, in which
the data_handler is called for each line, gradually building the self.entries 
dictionary where each entry with an SFTPAttributes structure describing one file being polled.

So the work in handle_data is just to fill an paramiko.SFTPAttributes structure. 
Since the web site doesn't actually provide any metadata, it is just filled in with sensible
default info, that provides enough information to build a notification message and run it through
duplicate suppression.

Here it the complete poll callback::

    import logging
    import paramiko
    import sarracenia
    from sarracenia import nowflt, timestr2flt
    from sarracenia.flowcb.poll import Poll
    
    logger = logging.getLogger(__name__)
    
    class Nasa_mls_nrt(Poll):
    
        def handle_data(self, data):
    
            st = paramiko.SFTPAttributes()
            st.st_mtime = 0
            st.st_mode = 0o775
            st.filename = data
    
            if 'MLS-Aura' in data:
                   logger.debug("data %s" %data)
                   self.entries[data]=st
    
                   logger.info("(%s) = %s" % (self.myfname,st))
            if self.myfname == None : return
            if self.myfname == data : return


The file is here:

( https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/poll/nasa_mls_nrt.py )

and matching config file provided here:

( https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/examples/poll/nasa-mls-nrt.conf )






------------------------------
Accessing Messages from Python
------------------------------

So far, we have presented methods of writing customizations of Sarracenia
processing, where one writes extensions, via either callbacks or extension 
classes to change what sarracenia flow instances do. 

Some may not want to use the Sarracenia and configuration language at all. 
They may have existing code, that they want call some sort of data ingesting code from.
One can call sarracenia related functions directly from existing python programs.

For now, best to consult the `Tutorials <../Tutorials>`_  included with Sarracenia,
which have some examples of such use.



.. warning::
    **FIXME**, link to amqplib, or java bindings, and a pointer to the sr_post and sr_report section 7 man pages.
