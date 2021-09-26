
Porting v2 Plugins to Sr3
=========================

This is a guide to porting plugins from Sarracenia version 2.X (metpx-sarracenia) to Sarracenia version 3.x (metpx-sr3)
If you are new to Sarracenia, and have no experience or need to look at v2 plugins, don't read this. it will just
confuse you. This guide is for those who need to take existing v2 plugins and port them to v3.
You are better off getting a fresh look by looking at the jupyter notebook examples::

    https://github.com/MetPX/sarracenia/tree/v03_wip/jupyter

Which provide an introduction to v3 without confusing references to v2.  In fact, Those notebooks
are probably a good pre-requisite for everyone, to understand how v3 plugins work, before trying
to port v2 ones. 

Sample v3 plugin::

    https://github.com/MetPX/sarracenia/blob/v03_wip/sarracenia/flowcb/log.py

Generally speaking v2 plugins were bolted onto existing code to allow some modification of behaviour.
v2 plugins when through a first generation, when only single routines were declared (e.g. *on_message*), 
and a second generation, when whole classes (e.g. *plugin*) were declared, but still in a stilted way.

Sr3 plugins are core design elements, composed together to implement part of Sarracenia itself. V3 plugins 
should be easier for Python programmers to debug and implement, and are strictly more flexible and powerful
than the v2 mechanism.

 * v3 uses standard python syntax, not v2's strange things ... e.g. *self.plugins*, *parent.logger*, Why doesn't *import* work?
 * standard python import; Syntax errors are detected and reported *the normal way*
 * v3 classes are designed to be usable outside the CLI itself (see jupyter notebook examples)
   callable by application programmers in their own code, like any other python library.
 * v3 classes can be sub-classed to add core functionality, like new message or file transport protocols.

File Placement
==============

v2 places configuration files under ~/.config/sarra, and state files under ~/.cache/sarra

v3 places configuration files under ~/.config/sr3, and state files under ~/.cache/sr3

v2 has a C implementation of sarra called sarrac. The C implementation for v3, is called sr3c,
and is the same as the v2 one, except it uses the new file locations.

Command Line Difference
=======================

Briefly, the sr3 entry point is used to start/stop/status things::

  v2:  sr_*component* start config

  v3:  sr3 start *component*/config

In sr3, one can also use file globbing style specifications to ask for a command
to be invoked on a group of configurations, wheras in v2, one could only operate on one at a time.

sr3_post is an exception to this change in that it works like v2's sr_post did, being
a tool for interactive posting.


What Will Work Without Change
=============================

The first step in porting a configuration subscribe/X to v3, is just to copy the configuration file from
~/.config/sarra to the corresponding location in ~/.config/sr3 and try::

sr3 show subscribe/X

The *show* command is new in sr3 and provides a way to view the configuration after 
it has been parsed. Most of it should work, unless you have do_* plugins. 

Examples of things that should work:

* all settings from v2 config files should be recognized by the v3 option parser, and converted
  to v3 equivalents, when they exist. v2 option -> v3 option some examples:

  * accept_scp_threshold -> accel_threshold
  * heartbeat -> housekeeping
  * chmod_log -> default_log_mode
  * loglevel -> logLevel
  * post_base_url -> post_baseUrl
  * post_rate_limit -> message_rate_max
  * cache, suppress_duplicates ->  nodupe_ttl
  * topic_prefix -> topicPrefix

* all on_message, on_file, on_post, on_heartbeat, routines will work, by sr3 using 
  the flowcb/v2wrapper.py plugin which will be automatically invoked when v2 plugins are 
  seen in the config file.

  Note that ideally, v2wrapper is used as a crutch to allow one to have a functional configuration
  quickly. There is a performance hit to using v2wrapper, and 


Things that will not work:

* do_*  they are just fundamentally different in v3.

If you have a configuration with a do_* plugin, then you need this guide, from day 1.
If you don't then 



Coding Differences between plugins in v2 vs. Sr3
================================================

The API for adding or customizing functionality in sr3 is quite different from v2.
In general, v3 plugins:

* **are usually subclassed from sarracenia.flowcb.FlowCB.**

  In v2, one would declare::

      class Msg_Log(object): 

  v3 plugins are normal python source files (no magic at the end.)
  they are subclassed from sarracenia.flowcb::

      from sarracenia.flowcb import FlowCB

      class myplugin(Flowcb):

  To create an *after_accept* plugin in *myplugin* class, define a function
  with that name, and the appropriate signature.

* **are pythonic, not weird** : In v2, you need the last line to include something like::

     self.plugin = 'Msg_Delay'

  for a second generation plugin, the first generation ones had
  something like::

      msg_2localfile = Msg_2LocalFile(None)
      self.on_message = msg_2localfile.on_message

  at the end to assign entry points explicitly. either way a naive python
  of the file would invariably fail without some sort of test harness being
  wrapped around it.

  In v2, there were strange issues with imports, resulting in people putting
  import statements within some functions. That problem is fixed in v3;
  put the necessary imports at the beginning of the file, like any other python
  module.

  in v3 one can at least check syntax by doing *import X* in any python interpreter.

* **v3 plugins can be used by application programmers.** The plugins aren't
  bolted on after the fact, but a core element, implementing duplicate 
  suppression, reception and transmission of messages, file monitoring,
  etc.. understanding v3 plugins gives people important clues to being
  able to work on sarracenia itself.

  v3 plugins can be *imported* into existing applications to add the ability
  to interact with sarracenia pumps without using the Sarracenia CLI.
  see jupyter tutorials. 

* **use standard python logging** ::

      import logger
  
  Make sure the following logger declaration is after the last _import_ in the file::

      logger = logging.getLogger(__name__)

      #when you want a log message:
      logger.warning( ... )

  In v3 plugins: *logger.x* replaces *parent.logger.x* found in v2 plugins.
  In v2, to test outside the app, one had to build a test harness that had
  parent.logger declared. sometimes there is also self.logger x... dunno why...
  don't ask.


* *have options as an argument to the __init__(self, options): routine*.
  by convention, most modules include::

       self.o = options 

  so in v2 if you need to access settings, *replace parent.setting by self.o.setting*.

* **you can see what options are active by starting a component with the 'show' command** ::

      sr3 show subscribe/myconf

  these settings can be access from self.o

* in the settings generally, **look for replacement of many underscores with camelCase** in sr3, as per WMO standardization.
  the exception being post\_  where the underscore seems to better match intent.  so:

  *  post_base_dir becomes post_baseDir,   
  *  post_broker is unchanged. 
  *  post_base_url -> post_baseUrl

* **messages are python dictionaries** , so *msg.relpath becomes msg['relPath']*
  v3 messages, as dictionaries are the default internal representation.

* **No Need to set message fields in plugins**
  in v2, one would set partstr, and sumstr for v2 messages in plugins. This required
  an excessive understanding of message formats, and meant that changing message formats
  requireed modifying plugins (v03 message format is not supported by most v2 plugins,
  for example. To build a message from a local file::

     from sarracenia.flowcb.gather import msg_fromFile

     m = msg_fromFile(sample_fileName, self.o, os.stat(sample_fileName) )


* **Really, No Need to set message fields in plugins**
  To build a message, without a local file, use msg_init::
  
     from sarracenia.flowcb.gather import msg_init

     m = msg_init(sample_fileName, cfg)

  builds an message from scratch, without checksums, or file size.
  This can be used for polling, when you don't have the local file.
  to request a normal checksum be computed when the file is downloaded,
  specify::

     m['size'] = size_you_got_from_your_poll
     m['integrity'] = { 'method': 'cod', 'value': 'sha512' }

  One can also build an supply a fake stat record to msg_init in order to
  get 'mtime', 'atime', 'size', and 'mode' message fields set::


     from sarracenia.flowcb.gather import fakeStat

     st = fakeStat( mtime=99, atime=99, size=129, mode=0o666 )
     m = msg_init(sample_fileName, cfg, st)

* **rarely, involve subclassing of moth or transfer classes.**
  The sarracenia.moth class implements support for message queueing protocols
  that support topic hierarchy based subscriptions. There are currently
  two subclasses of Moth: amqp (for rabbitmq), and mqtt.  It would be
  great for someone to add an amq1 (for qpid amqp 1.0 support.)

  It might be reasonable to add an SMTP class there for sending email,
  not sure.

  The sarracenia.transfer classes include http, ftp, and sftp today.
  They are used to interact with remote services that provide a fileish
  interface (supporting things like listing files, and downloading and/or
  sending.) Other sub-classes such as S3, IPFS, or webdav, would be 
  great additions.


Configuration Files
===================

in v2, the primary configuration option to declare a plugin is::

   plugin X

Generally speaking, there should be a file plugins/x.py
with a class X.py in that file in either ~/.config/plugins
or in the sarra/plugins directory in the package itself.
This is already a second generation style of plugin declaration
in Sarracenia. The original version, one declared individual
entry points::

    on_message, on_file, on_post, on_..., do_... 

In Sr3, the above entries are taken to be requests for v2
plugins, and should only be used for continuity reasons.
Ideally, one should invoke v3 plugins like so::

   callback x

Where x will be a subclass of sarracenia.flowcb, which
will contain a class X (first letter capitalized) in the
file x.py a in the python search path, or in the
*sarracenia/flowcb* directory included as part of the package.
This is actually a shorthand version of the python import.
If you need to declare a callback that does not obey that
convention, one can also use a more flexible but longer-winded::

  flowcb sarracenia.flowcb.x.X

the above two are equivalent. The flowcb version can be used to import classes 
that don't match the convention of the x.X (a file named x.py containing a class called X.py)



    
Mapping Entry Points
====================

on_message, on_post --> after_accept
------------------------------------

v2: receives one message, returns True/False


v3: receives worklist 
    modify worklist.incoming 
    transferring rejected messages to worklist.rejected, or worklist.failed.

examples:
  v2: plugins/msg_gts2wistopic.py
  v3: flowcb/wistree.py

on_file --> after_work
----------------------

v2: receives one message, returns True/False

v3: receives worklist 
    modify worklist.ok (transfer has already happenned.) 
    transferring rejected messages to worklist.rejected, or worklist.failed.

    can also be used to work on worklist.failed (retry logic does this.)

examples:


on_heartbeat -> on_housekeeping
-------------------------------

v2: receives parent as argument.
    will work unchanged.


v3: only receives self (which should have self.o)

examples:

  * v2: hb_cache.py -- cleans out cache (references sr_cache.)
  * v3: flowcb/nodupe.py -- implements entire caching routine.


on_line -> on_line (but different)
-----------------------------------

v2:  modify parent.line and return True if processing should confinue, otherwise False.
v3:  return (potentially modified) line if processing should continue, otherwise None.

examples:
  * v2: plugins/line_mode.py
  * v3: flowcb/line_mode.py


do_poll -> gather
-----------------

v2: call poll from plugin.

v3: build a list of messages to return.



do_download/do_send -> post or sub-classing of transfer/ or moth/
----------------------------------------------------------------- 

There are a number of different options here...  





v3 only: post,gather
--------------------

The polling/posting is actually done in flow callback (flowcb) classes.
The exit status does not matter, all such routines will be called in order.

The return of a gather is a list of messages to be appended to worklist.incoming

The return of post is undefined. The whole point is to create a side-effect
that affects some other process or server.


examples: 
 * flowcb/gather/file.py - read files from disk (for post and watch)
 * flowcb/gather/message.py - how messages are received by all components
 * flowcb/post/message.py - how messages are posted by all components.


v3 Complex Examples
-------------------


flowcb/nodupe
~~~~~~~~~~~~~

duplicate suppression in v3, has:

*  an after_accept routing the prunes duplicates from worklist.incoming.
   ( adding non-dupes to the reception cache.)


flowcb/retry 
~~~~~~~~~~~~

  * has an after_accept function to append messages to the 
    incoming queue, in order to trigger another attempt to process them.
  * has an after_work routine doing something unknown... FIXME.
  * has a post function to take failed downloads and put them
    on the retry list for later consideration.
