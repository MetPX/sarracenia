
=============================
 Sarracenia Programming Guide
=============================

[ `version française <fr/Prog.rst>`_ ]

---------------------
 Working with Plugins
---------------------

.. warning::
  **FIXME**: Missing sections are highlighted by **FIXME**.  
  **FIXME**: NOT YET UPDATED for V3. bits here and there are.
  **FIXME**: V3 not documented, but exists.

.. Contents::

Revision Record
---------------

:version: @Version@
:date: @Date@

Audience
--------

Readers of this manual should be comfortable with light scripting in Python version 3.
Sarracenia includes a number of points where processing can be customized by
small snippets of user provided code, known as plugins. The plugins themselves
are expected to be concise, and an elementary knowledge of Python should suffice to
build new plugins in a copy/paste manner, with many samples being available to read.  


Extension Ideas
---------------

Examples of things that would be fun to do with plugins:

- Common Alerting Protocol (CAP), is an XML format that provides a warnings
  for many types of events, indicating the area of coverage.  There is a 
  'polygon' field in the warning, that the source could add to messages using
  an on_post plugin.  Subscribers would have access to the 'polygon' header
  through use of an on_message plugin, enabling them to determine whether the
  alert affected an area of interest without downloading the entire warning.

- A source that applies compression to products before posting, could add a
  header such as 'uncompressed_size' and 'uncompressed_sum' to allow 
  subscribers with an on_message plugin to compare a file that has been locally
  uncompressed to an upstream file offered in compressed form.

- add Bittorrent, S3, IPFS as transfer protocols (sub-classing Transfer)

- add additional message protocols (sub-classing Moth)

- additional checksums, subclassing Integrity.


Introduction
------------

A Sarracenia data pump is a web server with notifications for subscribers to
know, quickly, when new data has arrived.  To find out what data is already
available on a pump, view the tree with a web browser.  For simple immediate
needs, one can download data using the browser itself or through a standard tool
such as wget.  The usual intent is for sr_subscribe to automatically download
the data wanted to a directory on a subscriber machine where other software
can process it.

Often, the purpose of automated downloading is to have other code ingest
the files and perform further processing. Rather than having a separate
process look at a file in a directory, one can insert customized
processing at various points in the flow.

Examples are available using the list command::

    fractal% sr list fcb
    Provided plugins: ( /home/peter/Sarracenia/v03_wip/sarra ) 
    flowcb/accel_scp.py              flowcb/accel_wget.py             flowcb/gather/file.py            flowcb/gather/message.py         
    flowcb/line_log.py               flowcb/line_mode.py              flowcb/msg/deleteflowfiles.py    flowcb/msg/fdelay.py             
    flowcb/msg/log.py                flowcb/nodupe.py                 flowcb/post/log.py               flowcb/post/message.py           
    flowcb/retry.py                  flowcb/v2wrapper.py              
    fractal%
    fractal% fcbdir=/home/peter/Sarracenia/v03_wip/sarra


Flow Callbacks
~~~~~~~~~~~~~~

The many ways to extend functionality, the most common one being adding callbacks
to flow components. All of the Sarracenia components are implemented using
the sarra.flow class.  There is a parent class sarra.flowcb to implement them.
The package's plugins are shown in the first grouping of available ones. Many of them have arguments which
are documented by listing them. In a configuration file, one might have the line::

    flow_callback sarra.flowcb.msg.log.Log

That line cause Sarracenia to look in the Python search path for a class like:

.. code:: python

  blacklab% cat sarra/flowcb/msg/log.py

  from sarra.flowcb import FlowCB
  import logging

  logger = logging.getLogger(__name__)

  class Log(FlowCB):
    def on_filter(self, worklist):
        for msg in worklist.incoming:
            logger.info("received: %s " % msg)

To modify it, copy it from the directory listed in the *list fcb* command to the editable preference one::

  blacklab% cp $fcb_dir/msg_log.py ~/.config/sarra/plugins

And then modify it for the purpose::

  blacklab% vi ~/.config/sarra/plugins/log.py

One can also see which plugins are active in a configuration by looking at the messages on startup::

   blacklab% sr_subscribe foreground clean_f90
   2018-01-08 01:21:34,763 [INFO] sr_subscribe clean_f90 start

   .
   .
   .

   2020-10-12 15:20:06,250 [INFO] sarra.flow run callbacks loaded: ['sarra.flowcb.retry.Retry', 'sarra.flowcb.msg.log.Log', 'file_noop.File_Noop', 'sarra.flowcb.v2wrapper.V2Wrapper', 'sarra.flowcb.gather.message.Message'] 2
   .
   .
   .
   blacklab% 



Extending Classes
~~~~~~~~~~~~~~~~~

One can also add additional functionality to Sarracenia by creating new subclasses.

sarra.moth - Messages Organized into Topic Hierarchies. (existing ones: rabbitmq-amqp)

sarra.integrity - checksum algorithms ( existing ones: md5, sha512, arbitrary, random )

sarra.transfer - additional transport protocols  (https, ftp, sftp )

sarra.flow - creation of new components beyond the built-in ones. (post, sarra, shovel, etc...)
 
One would start with the one of the existing classes, copy it somewhere else in the python path,
and build your extension. These classes are added to Sarra using the *import* option
in the configuration files. the __init__ files in the source directories are the good
place to look for information about each class's API.


Why v3 API should be used whenever possible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* uses importlib from python, much more standard way to register plugins.
  now syntax errors will be picked up just like any other python module being imported,
  with a reasonable error message.

* no strange decoration at end of plugins (self.plugin = , etc... just plain python.)
  Entirely standard python modules, just with known methods/functions

* The strange choice of *parent* as a place for storing settings is puzzling to people.
  *parent* instance variable becomes *options*,  *self.parent* becomes *self.o*

* plural event callbacks replace singular ones.  on_filter replaces on_message

* messages are just python dictionaries. fields defined by json.loads( v03 payload format )
  messages only contain the actual fields, no settings or other things...
  plain data.

* what used to be called plugins, are now only a type of plugins, called flow_callbacks.
  They now move messages between worklists. A worklist is just a list of messages. There are four:

  * worklist.incoming -- messages yet to be processed.
  * worklist.rejected -- message which are not to be further processed.
  * worklist.ok -- messages which have been successfully processed.
  * worklist.retry   -- messages for which processing was attempted, but it failed.


With this API, dealing with different numbers of input and output files becomes much
more natural, when unpacking a tar file, messages for the unpacked files can be appended
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


Importing extensions
~~~~~~~~~~~~~~~~~~~~

Developers can add additional Transfer protocols for messages or 
data transport using the *import* directive to make the new class
available::

  import torr

would be a reasonable name for a Transfer protocol to retrieve
resources with bittorrent protocol. A skeleton of such a thing
would look like this:: 


  import logging

  logger = logging.getLogger(__name__)

  import sarra.transfer

  class torr(sarra.transfer.Transfer):
      pass

  logger.warning("loading")




----------------------
Callback Script Basics
----------------------

An example of the v2 *plugin* format, one can use of file_noop.py in a configuration like so::

  flow_callback file_noop.file_Noop

The content of the file to be placed (on Linux) in ~/.config/sarra/plugins would be:
.. code:: python

  import logging
  from sarra.flowcb import FlowCB

  logger = logging.getLogger(__name__)

  class File_Noop(FlowCB):

      def __init__(self, options):

          super().__init__(options) # usually a good idea, though not needed here.

          # declare options to avoid 'unknown option' messages being logged.
          options.add_option( option='file_string' , kind='str', default_value='hello world')  

      def on_work(self,worklist):
          logger.info("file_noop: received %d files. file_string is: %s " % (len(worklist.ok), self.o.file_string) )



See `Flow Callback Points`_ for a full list of names of methods which are significant.

There is an initialization portion which runs when the component is started and
a perform section which is to be invoked on the appropriate event.  Setting
the plugin requires the magic last two lines in the sample plugin, where the last
line needs to reflect the type of plugin (on_file for an on_file plugin, on_message
for an on_message one, etc...)

The only argument the script receives is **parent**, which has all of the option
settings from configuration files and command line as attributes.  For example,
if a setting like::

  msg_speedo_interval 10

is set in a configuration file, then the plugin script will see
*parent.msg_speedo_interval* as a variable set to '10' (the string, not the number).
By convention when inventing new configuration settings, the name of the
plugin is used as a prefix (in this example, msg_speedo).


In addition to the command line options, there is also a logger available
as shown in the sample above.  The *logger* is a Python3 logger object, as documented
here: https://docs.python.org/3/library/logging.html.   To allow users to tune the
verbosity of logs, use priority specific method to classify messages::

  logger.debug - spelunking in progress... a lot of detail.
  logger.info - informative messages that are not essential
  logger.warn - a difficulty that is likely problematic, but the component still functions to some degree.
  logger.error - The component failed to do something.

In the above message, logger.info is used, indicating an informative message.
Another useful attribute available in parent is 'msg', which has all the attributes
of the message being processed.  All of the headers from the message, as defined
in the `sr_post(1) <sr_post.1.rst>` configuration file, are available to the plugin,
such as the message checksum as *msg['headers.sum*.  Consult the `Variables Available`_
section for an exhaustive list.  Generally, it is best to output only debug log
messages in the __init__ routine for a plugin, because it is executed every time an
*sr status* command is run, which can rapidly become unwieldy. 

Should one of these scripts return False, the processing of the message/file
will stop there and another message will be consumed from the broker.



Variables in Messages
---------------------

plugins, receive parent as a parameter.  parameter.msg is the message
being processed. variables variables most used:

*msg['exchange']*  
  The exchange through which the message is being posted or consumed.

*msg['isRetry']*
  If this is a subsequent attempt to send or download a message.

*msg['new_dir']*
  The directory which will contain *msg['new_file']*

*msg['new_file']*
  A popular variable in on_file and on_part plugins is: *msg['new_file*,
  giving the file name the downloaded product has been written to.  When the
  same variable is modified in an on_message plugin, it changes the name of
  the file to be downloaded. Similarly another often used variable is 
  *parent.new_dir*, which operates on the directory to which the file
  will be downloaded.

*msg['pubtime']*
  The time the message was originally inserted into the network (first field of a notice.)

*msg['baseurl']*
  The root URL of the publication tree from which relative paths are constructed.

*msg['relpath']*
  The relative path from the baseURL of the file.
  concatenating the two gives the complete URL.

*msg['notice']*
  The body of the message being processed. see `sr_post(7) <sr_post.7.rst>`_
  a space-separated tuple of: pubtime,baseurl,and relpath, 
  If parts here are modified, one must modify extracted fields for full effect.

*msg['partstr']*
  The partition string ( same as msg['headers['parts'] )

*msg['sumstr']*
  The checksum string ( same as msg['headers['sum'] ) indicating the checksum
  algorithm used, and the 

*msg['topic']*
  the AMQP topic of the message.

*msg['url']*
  The equivalent url after it has been parsed with urlparse
  (see Python3 documentation of urlparse for detailed usage). This gives access
  to, for example, *msg['url.hostname* for the remote host from which a file is to be obtained,
  or *msg['url.username* for the account to use, parent.url.path gives the path on the
  remote host.

*msg['urlstr']*
  There is also msg['urlstr which is the completed download URL of the file,


These are the variable which are most often of interest, but many other 
program states are available.  See the  `Variables Available`_ section for a more thorough
discussion.



Accessing Options
-----------------

The settings resulting from parsing the configuration files are also readily available.
Plugins can define their own options by calling::

   FIXME: api incomplete.
   Config.add_option( option='name_of_option', kind, default_value  )

Options so declared just become instance variables in the options passed to init.
By convention, plugins set self.o to contain the options passed at init time, so that 
all the built-in options are similarly processing.  If consult the `sr_subscribe(1) <sr_subscribe.1.rst>`_
manual page, and most of the options will have a corresponing instance variable.

Some examples:

*self.o.baseDir*
  the base directory for where files are when consuming a post.

*self.o.caching*
  Numerical value indicating the caching lifetime (how old entries should be before they age out.)
  Value of 0 indicates caching is disabled.

*self.o.inflight*
  The current setting of *inflight* (see `Delivery Completion <sr_subscribe.1.rst#Delivery%20Completion%20(inflight)>`_

*self.o.overwrite*
  setting which controls whether to files already downloaded should be overwritten unconditionally.

*self.o.discard*
  Whether files should be removed after they are downloaded.




Flow Callback Points
--------------------

Sarracenia will interpret the names of functions as indicating times in processing when
a given routine should be called.

+-------------------+----------------------------------------------------+
|  Name             | When/Why it is Called                              |
+===================+====================================================+
|                   | called by sr_poll, meant select files to be posted |
| do_poll           | For local files, use parent.post1file(self,stat)   |
|                   | Where stat is the return tuple from an os.lstat()  |
|                   | call.                                              |
|                   |                                                    |
|                   | Example:                                           |
|                   | FIXME: the GPFS poll script should be here.        |
|                   |                                                    |
+-------------------+----------------------------------------------------+
|                   | very freqently used.                               |
|                   | examine parent.msg for finer grained filtering.    |
| on_filter         | Return False to stop further processing of message.|
|                   | return True to proceed                             |
|                   |                                                    |
|                   | Examples: msg_* in the examples directory          |
|                   |                                                    |
|                   | msg_delay - make sure messages are old before      |
|                   | processing them.                                   |
|                   |                                                    |
|                   | msg_download - change messages to use different    |
|                   | downloaders based on file size (built-in for small |
|                   | ones, binary downloaders for large files.)         |
|                   |                                                    |
|                   |                                                    |
+-------------------+----------------------------------------------------+
|                   | change msg['new_file'] to taste.                   |
| destfn_script     | called when renaming the file from inflight to     |
|                   | permanent name.                                    |
|                   |                                                    |
+-------------------+----------------------------------------------------+
|                   | When a transfer has been completed.                |
| on_work           |                                                    |
|                   | return False to stop further processing.           |
|                   | return True to proceed                             |
|                   |                                                    |
+-------------------+----------------------------------------------------+
|                   | Called every housekeeping interval (minutes)       |
|                   | used to clean cache, check for occasional issues.  |
|                   | manage retry queues.                               |
| on_housekeeping   |                                                    |
|                   | return False to abort further processing           |
|                   | return True to proceed                             |
|                   |                                                    |
|                   |                                                    |
+-------------------+----------------------------------------------------+
|                   | in sr_poll if you only want to change how the      |
| on_html_page      | downloaded html URL is parsed, override this       |
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
|                   | when a componente (e.g. sr_subscribe) is started.  |
| on_start          | Can be used to read state from files.              |
|                   |                                                    |
|                   | state files in parent.user_cache_dir               |
|                   |                                                    |
|                   | return value ignored                               |
|                   |                                                    |
|                   | example: file_total_save.py [#]_                   |
|                   |                                                    |
+-------------------+----------------------------------------------------+
|                   | when a component (e.g. sr_subscribe) is stopped.   |
| on_stop           | can be used to persist state.                      |
|                   |                                                    |
|                   | state files in parent.user_cache_dir               |
|                   |                                                    |
|                   | return value ignored                               |
|                   |                                                    |
+-------------------+----------------------------------------------------+
|                   | Returns one or more labels, often protocols,       |
| registered_as     | examples [ 'imap', 'pop', 'imaps', 'pops' ]        |
|                   | example: samples/poll_email_ingest.py [#]_         |
+-------------------+----------------------------------------------------+

.. [#] see `smc_download_cp <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/smc_download_cp.py>`_
.. [#] see `Issue 74 <https://github.com/MetPX/sarracenia/issues/74>`_
.. [#] see `part_clanav_scan.py  <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/part_clanav_scan.py>`_
.. [#] see `file_total_save.py  <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/file_total_save.py>`_
.. [#] see `poll_email_ingest.py  <https://github.com/MetPX/sarracenia/blob/master/sarra/plugins/poll_email_ingest.py>`_

---------------------
Better File Reception
---------------------

For example, rather than using the file system, sr_subscribe could indicate when each file is ready
by writing to a named pipe::

  blacklab% sr_subscribe edit dd_swob.conf 

  broker amqps://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#

  file_rxpipe_name /local/home/peter/test/rxpipe

  on_file file_rxpipe directory /tmp
  mirror True
  accept .*

  # rxpipe is a builtin on_file script which writes the name of the file received to
  # a pipe named '.rxpipe' in the current working directory.

With the *on_file* option, one can specify a processing option such as rxpipe.  With rxpipe,
every time a file transfer has completed and is ready for post-processing, its name is written
to the linux pipe (named .rxpipe) in the current working directory.  So the code for post-processing
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

While the *on_file* directive specifies the name of an action to perform on receipt
of a file, those actions are not fixed but simply small scripts provided with the
package and customizable by end users.  The rxpipe module is just an example
provided with sarracenia::

  from sarra.flowcb import FlowCB
  from sarra.config import add_option

  add_option( option='file_rxpipe_name', kind='str' ):

  class File_RxPipe(FlowCB):

      def on_start(self,parent):
          if not hasattr(self.o,'file_rxpipe_name') and self.o.file_rxpipe_name:
              parent.logger.error("Missing file_rxpipe_name parameter")
              return
          self.rxpipe = open( parent.file_rxpipe_name, "w" )

      def on_file(self, parent):
          self.rxpipe.write( msg['new_file + "\n" )
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

To implement support of additional protocols, one would write
a **_do_download** script.  The scripts would access the credentials
value in the script with the code :

- **ok, details = parent.credentials.get(msg.urlcred)**
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

Methods Available
-----------------

parent.post1file(path,stat):

Used in poll or posting scripts when a local file is available, to create 
a post using existing settings (for ownership, partitioning, checksums, 
symlink handling, etc...) The path is that of the local file to be posted, 
and the stat record is a tuple as returned by os.lstat() that corresponds 
to the file. If the stat record is None, then a remove posting event is 
generated. If the stat record corresponds to a symbolic link, then a 
link record is generated. If the stat record corresponds to an regular 
file, then a normal posting will be generated.



Variables Available
-------------------


Without peering into the Python source code of sarracenia, it is hard to know
what values are available to plugin scripts. As a cheat to save developers
from having to understand the source code, a diagnostic plugin might be helpful.

If one sets **on_message msg_dump** in a configuration, the entire
list of available variables can be displayed in a log file.

Make the above file an on_file (or other trigger) script in a configuration, start up a receiver
(and if it is a busy one, then stop it immediately, as it creates very large report messages for
every message received).  Essentially the entire program state is available to plugins.

A sample output (reformatted for legibility) is given below.  For every field *xx* listed,
a plugin script can access it as *parent.xx*  (e.g. *parent.queue_name* )::

  peter@idefix:~/test$ sr_subscribe foreground dd.conf 
  ^C to stop it immediately after the first message.
  peter@idefix:~/test$ tail -f ~/.cache/sarra/log/sr_subscribe_dd_0001.log

  # the following is reformatted to look reasonable on a page.
  2016-01-14 17:13:01,649 [INFO] {
  'kbytes_ps': 0,
  'queue_name': None,
  'flatten': '/',
  'exchange': 'xpublic',
  'discard': False,
  'report_back': True,
  'source': None,
  'pidfile': '/local/home/peter/.cache/sarra/.sr_subscribe_dd_0001.pid',
  'event': 'IN_CLOSE_WRITE|IN_ATTRIB|IN_MOVED_TO|IN_MOVE_SELF',
  'basic_name': 'sr_subscribe_dd',
  'cluster_aliases': [],
  'expire': None,
  'currentRegexp': re.compile('.*'),
  'handler': <logging.handlers.TimedRotatingFileHandler
  object at 0x7f4fcdc4d780>,
  'accept_unmatch': False,
  'reconnect': False,
  'isrunning': False,
  'on_line': None,
  'masks': [('.*/grib2/.*', '/local/home/peter/test/dd', None, re.compile('.*/grib2/.*'), False),
  ('.*grib2.tar.*', '/local/home/peter/test/dd', None, re.compile('.*grib2.tar.*'), False),
  ('.*', '/local/home/peter/test/dd', None, re.compile('.*'), True)],
  'logrotate': 5,
  'pid': 14079,
  'consumer': <sarra.sr_consumer.sr_consumer object at 0x7f4fcdc489b0>,
  'post_document_root': None,
  'manager': None,
  'publisher': <sarra.sr_amqp.Publisher object at 0x7f4fcdbdae48>,
  'post_broker': ParseResult(scheme='amqp',
  netloc='guest:guest@localhost',
  path='/',
  params='',
  query='',
  fragment=''),
  'currentPattern': '.*',
  'partflg': '1',
  'notify_only': False,
  'program_dir': 'subscribe',
  'on_part': None,
  'to_clusters': None,
  'site_data_dir': '/usr/share/ubuntu/sarra',
  'source_from_exchange': False,
  'new_url': ParseResult(scheme='file', netloc='',
  path='/local/home/peter/test/dd/bulletins/alphanumeric/20160114/SA/CYVT/22/SACN62_CYVT_142200___11878',
  params='', query='', fragment=''),
  'sumflg': 'd',
  'user_log_dir': '/local/home/peter/.cache/sarra/log',
  'topic_prefix': 'v02.post',
  'on_post': None,
  'do_poll': None,
  'message_ttl': None,
  'user_scripts_dir': '/local/home/peter/.config/sarra/scripts',
  'appname': 'sarra',
  'debug': False,
  'chmod': 775,
  'destination': None,
  'subtopic': None,
  'events': 'IN_CLOSE_WRITE|IN_DELETE',
  'document_root': '/local/home/peter/test/dd',
  'inplace': True,
  'last_nbr_instances': 6,
  'config_name': 'dd',
  'instance_str': 'sr_subscribe dd 0001',
  'randomize': False,
  'vip': None,
  'parts': '1',
  'inflight': '.tmp',
  'cache_url': {},
  'queue_share': True,
  'overwrite': True,
  'appauthor': 'science.gc.ca',
  'no': 1,
  'url': None,
  'bindings': [('xpublic', 'v02.post.#')],
  'blocksize': 0,
  'cluster': None,
  'rename': None,
  'user_config_dir': '/local/home/peter/.config/sarra',
  'users': {},
  'currentDir': '/local/home/peter/test/dd',
  'instance': 1,
  'sleep': 0,
  'user_cache_dir': '/local/home/peter/.cache/sarra',
  'report_clusters': {},
  'strip': 0,
  'msg': <sarra.sr_message.sr_message object at 0x7f4fcdc54518>,
  'site_config_dir': '/etc/xdg/xdg-ubuntu/sarra',
  'user_args': ['--no', '1'],
  'program_name': 'sr_subscribe',
  'on_file': <bound method Transformer.perform of <sarra.sr_config.Transformer object at 0x7f4fcdc48908>>,
  'cwd': '/local/home/peter/test',
  'nbr_instances': 6,
  'credentials': <sarra.sr_credentials.sr_credentials object at 0x7f4fcdc911d0>,
  'on_message': None,
  'currentFileOption': None,
  'user_config': 'dd.conf',
  'lpath': '/local/home/peter/.cache/sarra/log/sr_subscribe_dd_0001.log',
  'bufsize': 8192,
  'do_download': None,
  'post_exchange': None,
  'report_exchange': 'xlog',
  'new_path': '/local/home/peter/test/dd/bulletins/alphanumeric/20160114/SA/CYVT/22/SACN62_CYVT_142200___11878',
  'instance_name': 'sr_subscribe_dd_0001',
  'statefile': '/local/home/peter/.cache/sarra/.sr_subscribe_dd.state',
  'use_pattern': True,
  'admin': None,
  'gateway_for': [],
  'interface': None,
  'logpath': '/local/home/peter/.cache/sarra/log/sr_subscribe_dd_0001.log',
  'recompute_chksum': False,
  'user_queue_dir': '/local/home/peter/.cache/sarra/queue',
  'mirror': True,
  'broker': ParseResult(scheme='amqp', netloc='anonymous:anonymous@dd.weather.gc.ca', path='/', params='', query='', fragment=''),
  'durable': False,
  'logger': <logging.RootLogger object at 0x7f4fcdc48a20>,
  'user_data_dir': '/local/home/peter/.local/share/sarra',
  'flow': None}


No thought has yet been given to plugin compatibility across versions.  Unclear how much of
this state will vary over time.  Similar to program configuration settings, all of the fields
involved in processing individual messages are available in the parent.msg object.  A similar
dump to the above is here (e.g of a Python scripts can use *msg['partsr* ,
and/or *msg['header.parts*  in their code)::


 2016-01-14 17:13:01,649 [INFO] message =
 {'partstr': '1,78,1,0,0',
 'suffix': '.78.1.0.0.d.Part',
 'subtopic': 'alphanumeric.20160617.CA.CWAO.12',
 'in_partfile': False,
 'notice': '20160617120454.820 http://dd2.weather.gc.ca/ bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919',
 'checksum': 'ab1ba0020e91119fb024a2c115ccd908',
 'pub_exchange': None,
 'local_checksum': None,
 'chunksize': 78,
 'time': '20160617120454.820',
 'path': 'bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919',
 'report_exchange': 'xs_anonymous',
 'part_ext': 'Part',
 'topic_prefix': 'v02.post',
 'current_block': 0,
 'tbegin': 1466165094.82,
 'remainder': 0,
 'to_clusters': ['DD', 'DDI.CMC', 'DDI.EDM'],
 'local_offset': 0,
 'mtype': 'post',
  'user': 'anonymous',
  'bufsize': 8192, 'new_url':
  ParseResult(scheme='file', netloc='', path='/home/peter/test/dd/bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919', params='', query='', fragment=''), 'exchange': 'xpublic', 'url': ParseResult(scheme='http', netloc='dd2.weather.gc.ca', path='/bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919', params='', query='', fragment=''),
 'onfly_checksum': 'ab1ba0020e91119fb024a2c115ccd908',
  'host': 'blacklab',
  'filesize': 78,
  'block_count': 1,
 'sumalgo': <sarra.sr_util.checksum_d object at 0x7f77554234e0>,
 'headers': {
      'sum': 'd,ab1ba0020e91119fb024a2c115ccd908',
      'parts': '1,78,1,0,0',
      'filename': 'CACN00_CWAO_171133__WAR_00919',
      'to_clusters': 'DD,DDI.CMC,DDI.EDM',
      'source': 'metpx',
      'rename': '/home/peter/test/dd/bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919',
      'from_cluster': 'DD'},
 'hdrstr': 'parts=1,78,1,0,0 sum=d,ab1ba0020e91119fb024a2c115ccd908 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=/home/peter/test/dd/bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919 message=Downloaded ',
  'report_notice': '20160617120454.820 http://dd2.weather.gc.ca/ bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919 201 blacklab anonymous 3.591402',
  'version': 'v02',
  'parent': <sarra.sr_subscribe.sr_subscribe object at 0x7f775682b4a8>,
  'logger': <logging.RootLogger object at 0x7f77563359e8>,
  'length': 78,
  'topic': 'v02.post.bulletins.alphanumeric.20160617.CA.CWAO.12',
  'inplace': True,
  'urlcred': 'http://dd2.weather.gc.ca/',
  'sumstr': 'd,ab1ba0020e91119fb024a2c115ccd908',
  'report_topic': 'v02.report.bulletins.alphanumeric.20160617.CA.CWAO.12',
  'publisher': None,
  'code': 201,
  'urlstr': 'http://dd2.weather.gc.ca/bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919',
  'lastchunk': True,
  'sumflg': 'd',
  'offset': 0,
  'partflg': '1',
  'report_publisher': <sarra.sr_amqp.Publisher object at 0x7f77551c7518>}


----------------------
Debugging on\_ Scripts
----------------------

When initially developing a plugin script, it can be painful to run it in the complete framework.
Attempting to run even the above trivial plugin::

   blacklab% python noop.py
   Traceback (most recent call last):
     File "noop.py", line 25, in <module>
       filenoop  = File_Noop(self)
   NameError: name 'self' is not defined
   blacklab%

To do basic syntax work, one can add some debugging scaffolding.  Taking the above code just add::

    from sarra.flowcb import FlowCB

    class File_Noop(FlowCB):
          def __init__(self,parent):
              parent.declare_option( 'file_string' )

          def on_start(self,parent):
              if not hasattr(parent,'file_string'): # prior to 2.18.1a4, include on_start code in __init__
                 parent.file_string='hello world'

          def on_file(self,parent):
              logger = parent.logger

              logger.info("file_noop: I have no effect but adding a log line with %s in it" % parent.file_string )

              return True

    ## DEBUGGING CODE START

    class TestLogger:
        def silence(self,str):
            pass

        def __init__(self):
            self.debug   = self.silence
            self.error   = print
            self.info    = self.silence
            self.warning = print


    class TestParent(object):
        def __init__(self):
            self.logger=TestLogger()
            pass

    testparent=TestParent()

    filenoop  = File_Noop(testparent)
    testparent.on_file = filenoop.on_file

So now it can be invoked with::

    blacklab% python noop.py
    blacklab%

Which confirms that there are at least no syntax errors. One will need to add more scaffolding
depending on the complexity of the plugin.  One can append an invocation of the plugin to the test
script, like so::

   self.on_file(self)


and then the routine will run. The more complex the plugin, the more needs to be added to the
debugging scaffolding.  Once that sort of basic testing is completed, just remove the scaffolding.

For more complicated tests, just add more testing code::

  cat >fifo_test.py <<EOT
  #!/usr/bin/python3

  """
  when a file is downloaded, write the name of it to a named pipe called .rxpipe
  at the root of the file reception tree.

  """
  import os,stat,time

  class Transformer(object):

      def __init__(self):
          pass

      def on_file(self,parent):
          msg    = parent.msg

          # writing filename in pipe
          f = open('/users/dor/aspy/mjg/mon_fifo','w')
          f.write(parent.new_file)
          f.flush()
          f.close()

          # resume process as usual ?
          return True

  transformer=Transformer()
  #self.on_file = transformer.on_file

  """
  for testing outside of a sr_ component plugin environment,
  we comment out the normal activiation line of the script above
  and insert a little wrapper, so that it can be invoked
  at the command line:
         python3  fifo_test.py

  """
  class TestLogger():
      def silence(self,str):
          pass

      def __init__(self):
          self.debug   = print
          self.error   = print
          self.info    = print
          self.warning = print

  class TestMessage() :
      def __init__(self):
          self.headers = {}

  class TestParent(object):
      def __init__(self):
          self.new_file = "a string"
          self.msg = TestMessage()
          self.logger = TestLogger()
          pass

  testparent=TestParent()

  transformer.on_file(testparent)

The part after the #self.on_file line is only a test harness.
One creates a calling object with the fields needed to test the
fields the plugin will use in the TestParent and TestMessage classes.
Also consult the harness.py plugin available to include the above
code for plugin testing.


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
  no_download
  on_message msg_2local
  on_message do_something

  accept .*
  


on_message is a scripting hook, exactly like on_file, that allows
specific processing to be done on receipt of a message.  A message will
usually correspond to a file, but for large files, there will be one
message per part. One can use the msg['partstr to find out which part
you have (See `sr_post.1 <sr_post.1.rst>`_ for details on partstr encoding.

Ensure the on_message plugin returns 'False' to prevent downloading.


.. warning::
   **FIXME**: perhaps show a way of checking the parts header to
   with an if statement in order to act on only the first part message
   for long files.


----------
do_scripts
----------

In the case where large files are being downloaded, and one wants to do it quickly, the sarracenia's
built-in methods are inherently a bit limited by the speed of python for low-level operations.  While
built-in methods are reasonably efficient and have low overhead, it could be argued that when large files
are to be downloaded, using an efficient, dedicated downloader written in a low level language like
C is more effective.  These examples are included with every installation of sarracenia, and
can be modified to be used with other tools.

Here is an example of implementing conditional use of a more efficient download method.  Start with
an on_message script that evaluates the condition to determine whether to invoke the custom downloader:


.. include:: ../sarracenia/plugins/msg_download.py 
   :code:

So one "invents" a new URL scheme that refers to the alternate downloader.   In this case, URLs which are
to be downloaded using an alternate tool get the their 'http:' replaced by 'download:'.    In the example above,
posts where the file is bigger than a threshold value (10 megabytes by default) will be marked for download 
with an alternate method by having their URL altered.

This on_message msg_download plugin needs to be coupled with the use of a do_download plugin. 
When the alternate schema is encountered, the component will invoke that plugin. Example of that plugin:

.. include:: ../sarracenia/plugins/download_wget.py
   :code:


------------------------
Why Doesn't Import Work?
------------------------

There is an issue where the place in the code where plugins are read is different
from where the plugin routines are executed, and so class level imports do not work as expected.

.. code:: python

    #!/usr/bin/python3

    import os,sys,stat,time,datetime,string,socket
    from ftplib import FTP

    class Renamer(object):
        def __init__(self):
            pass
     
        def perform(self,parent):
            infile = parent.local_file
            Path = os.path.dirname(infile)
            Filename = os.path.basename(infile)
     
            # FTP upload
            def uploadFile(ftp, upfile):
                ftp.storbinary('STOR ' + upfile, open(upfile, 'rb'), 1024)
                ftp.sendcmd('SITE CHMOD 666 ' + upfile)

            # ftp = FTP('hoho.haha.ec.gc.ca')
            ftp = FTP('127.272.44.184')
            logon = ftp.login('px', 'pwgoeshere')
            path = ftp.cwd('/apps/px/rxq/ont2/')
            os.chdir( Path )
            uploadFile(ftp, Filename)
            ftp.quit()
    
    renamer=Renamer()
    self.on_file = renamer.perform
 
When the code is run, this happens::

  2018-05-23 20:57:31,958 [ERROR] sr_subscribe/run going badly, so sleeping for 0.01 Type: <class 'NameError'>, Value: name 'FTP' is not defined,  ...
  2018-05-23 20:57:32,091 [INFO] file_log downloaded to: /apps/urp/sr_data/TYX_N0S:NOAAPORT2:CMC:RADAR_US:BIN:20180523205529
  2018-05-23 20:57:32,092 [INFO] confirmed added to the retry process 20180523205531.8 http://ddi1.cmc.ec.gc.ca/ 20180523/UCAR-UNIDATA/RADAR_US/NEXRAD3/N0S/20/TYX_N0S:NOAAPORT2:CMC:RADAR_US:BIN:20180523205529
   
  2018-05-23 20:57:32,092 [ERROR] sr_subscribe/run going badly, so sleeping for 0.02 Type: <class 'NameError'>, Value: name 'FTP' is not defined,  ...
  2018-05-23 20:57:32,799 [INFO] file_log downloaded to: /apps/urp/sr_data/CXX_N0V:NOAAPORT2:CMC:RADAR_US:BIN:20180523205533
  2018-05-23 20:57:32,799 [INFO] confirmed added to the retry process 20180523205535.46 http://ddi2.cmc.ec.gc.ca/ 20180523/UCAR-UNIDATA/RADAR_US/NEXRAD3/N0V/20/CXX_N0V:NOAAPORT2:CMC:RADAR_US:BIN:20180523205533
  2018-05-23 20:57:32,799 [ERROR] sr_subscribe/run going badly, so sleeping for 0.04 Type: <class 'NameError'>, Value: name 'FTP' is not defined,  ...
 
The solution is to move the import inside the perform routine as the first line, like so::

	.
	.
	.

        def perform(self,parent):
            from ftplib import FTP
            infile = parent.local_file
            Path = os.path.dirname(infile)
  	.
	.
	. 



-------
Polling
-------

.. warning::
    **FIXME** Sample polling.


----------------
Checksum Plugins
----------------

.. warning::
    **FIXME**


-------------------------------------
Accessing Messages without Sarracenia
-------------------------------------

.. warning::
    **FIXME**, link to amqplib, or java bindings, and a pointer to the sr_post and sr_report section 7 man pages.
