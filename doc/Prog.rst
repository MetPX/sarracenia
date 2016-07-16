
=============================
 Sarracenia Programming Guide
=============================

---------------------
 Working with Plugins 
---------------------

Status: Pre-Draft

.. note::
  Pardon the dust, This package is alpha, not ready for general use yet. Please Stay Tuned!
  **FIXME**: Missing sections are highlighted by **FIXME**.  What is here should be accurate!

.. Contents::

Audience
--------

Readers of this manual should be comfortable with light scripting in python version 3.
Sarracenia includes a number of points where processing can be customized by 
small snippets of user provided code, known as plugins.  The plugins themselves 
are expected to be rather concise, and an elementary knowledge of python should suffice to 
build new plugins in an essentially copy/paste manner, with many samples being 
available to read.  For some examples of how plugin processing might be of 
interest to users see the Ideas below:


Plugin Script Ideas
-------------------

Examples of things that would be fun to do with plugins.

- Common Alerting Protocol or CAP, is an XML format that provides a warnings for many types of events, indicating
  the area of coverage.  There is a 'polygon' field in the warning, that the source could add to messages using
  an on_post plugin.  Subscribers would have access to the 'polygon' header through use of an on_message plugin,
  enabling them  determine whether the alert affected an area of interest without downloading the entire warning.  

- A source that applies compression to products before posting, could add a header such as 'uncompressed_size'
  and 'uncompressed_sum' to allow subscribers, with an on_message plugin to compare a file that has been locally
  uncompressed to an upstream file offerred in compressed form.


------------
Introduction
------------

A Sarracenia data pump is a web server with notifications for subscribers to 
know, quickly, when new data has arrived.  To find out what data is already 
available on a pump, view the tree with a web browser.  For simple immediate 
needs, one can download data using the browser itself, or a standard tool 
such as wget.  The usual intent is for sr_subscribe to automatically download 
the data wanted to a directory on a subscriber machine where other software 
can process it.  

Often, the purpose of automated downloading is to have other code ingest 
the files and perform further processing.  Rather than having a separate 
process have to look at a file in a directory, Sarracenia provides a means 
of customizing processing via plugins written in python 3. A first example:

There are ways to insert scripts into the flow of messages and file downloads:
Should you want to implement tasks in various part of the execution of the 
program:

- **on_message  <script>        (default: msg_log)**
- **on_file     <script>        (default: file_log)**
- **on_part     <script>        (default: None)**
- **on_post     <script>        (default: post_log)**
- **on_line     <script>        (default: None)**

While the first four are self-evident, the on_line plugin is a bit obscure.  It 
is used to parse remote directories listings using sr_poll,
as the listing format varies by implementation of the remote server.

There are also do\_ scripts, which provide or replace functionality in programs:

- **do_download     <script>        (default: None)**
- **do_poll         <script>        (default: None)**
- **do_send         <script>        (default: None)**


---------------------
Plugin Scripts Basics
---------------------

An example, A file_noop.py script for **on_file**, could be ::

 class File_Noop(object): 
      def __init__(self,parent):
          if not hasattr(parent,'file_string'):
             parent.file_string='hello world'


      def perform(self,parent):
          logger = parent.logger

          logger.info("file_noop: I have no effect but adding a log line with %s in it" % parent.file_string )

          return True

 filenoop  = File_Noop(self)
 self.on_file = filenoop.perform

There is an initialization portion which runs when the component is started,
a perform section which is to be invoked on the appropriate event.  Setting
the plugin requires the magic last two lines in the sample plugin, where the last
line needs to reflect the type of plugin (on_file for an on_file plugin, on_message,
for an on_message one, etc...)

The only argument the script receives is **parent**, which has all of option 
settings from configuration files and command line as attributes.  For example,
if a setting like::

  msg_speedo_interval 10

is set in a configuration file, then the plugin script will see
*parent.msg_speedo_interval* as a variable set to '10' (the string, not the number)
By convention when inventing new configuration settings, the name of the
plugin is used as a prefix (In this example, msg_speedo)


In addition to the command line options, there is also a logger available
as shown in the sample above.  The *logger* is a python3 logger object, as documented 
here: https://docs.python.org/3/library/logging.html.   To allow users to tune the 
verbosity of logs, use priority specific method to classify messages::

  logger.debug - something deeply wrong, spelunking in progress.
  logger.info - informative messages that are not essential
  logger.warn - a difficulty that is likely problematic, but the component still functions to some degree.
  logger.error - The component failed to do something.

In the above message, logger.info is used, indicating an informative message.
Another useful attribute available in parent, is 'msg', which has all the attributes 
of the message being processed.  All of the headers from the message, as defined
in the `sr_post(1) <sr_post.1.html>` configuration file, are available to the plugin,
such as the message checksum as *parent.msg.headers.sum*.  Consult the `Variables Available`_ 
section for an exhaustive list.

A popular variable in on_file and on_part plugins, is: *parent.msg.local_file*, 
giving the file name the downloaded product has been written to.

Should one of these scripts return False, the processing of the message/file
will stop there and another message will be consumed from the broker.



Sample Plugins
--------------

There is a number of examples of plugin scripts included with every
installation.  If installed with debian packages, they are here::

   /usr/lib/python3/dist-packages/sarra/plugins

Another good location to browse is::

  https://sourceforge.net/p/metpx/git/ci/master/tree/sarracenia/sarra/plugins/

The git repository with many plugins available to reference.

For example, the default settings of on_msg and on_file print log messages
for each message and file processed.  




---------------------
Better File Reception
---------------------

For example, rather than using the file system, sr_subscribe could indicates when each file is ready
by writing to a named pipe:: 

  blacklab% cat >../dd_swob.conf <<EOT

  broker amqp://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#

  file_rxpipe_name /local/home/peter/test/rxpipe

  on_file file_rxpipe
  directory /tmp
  mirror True
  accept .*
  # rxpipe is a builtin on_file script which writes the name of the file received to
  # a pipe named '.rxpipe' in the current working directory.
  EOT

With the *on_file* option, one can specify a processing option such as rxpipe.  With rxpipe, 
every time a file transfer has completed and is ready for post-processing, its name is written 
to the linux pipe (named .rxpipe) in the current working directory.  So the code for post-processing 
becomes::

  do_something <.rxpipe

No filtering out of working files by the user is required, and ingestion of partial files is
completely avoided.   

.. NOTE::
   In the case where a large number of sr_subscribe instances are working
   On the same configuration, there is slight probability that notifications
   may corrupt one another in the named pipe.  
   We should probably verify whether this probability is negligeable or not.


Advanced File Reception
-----------------------

While the *on_file* directive specifies the name of an action to perform on receipt
of a file, those actions are not fixed, but simply small scripts provided with the
package, and customizable by end users.  The rxpipe module is just an example 
provided with sarracenia::

  class File_RxPipe(object):

      def __init__(self,parent):
          if not hasattr(parent,'file_rxpipe_name'):
              parent.logger.error("Missing file_rxpipe_name parameter")
              return 

          self.rxpipe = open( parent.file_rxpipe_name[0], "w" )

      def perform(self, parent):
          self.rxpipe.write( parent.msg.local_file + "\n" )
          self.rxpipe.flush()
          return None

  rxpipe =File_RxPipe(self)

  self.on_file=rxpipe.perform

With this fragment of python, when sr_subscribe is first called, it ensures that
a pipe named npipe is opened in the specified directory by executing
the __init__ function within the declared RxPipe python class.  Then, whenever
a file reception is completed, the assignment of *self.on_file* ensures that 
the rx.perform function is called.  

The rxpipe.perform function just writes the name of the file dowloaded to
the named pipe.  The use of the named pipe renders data reception asynchronous
from data processing.   as shown in the previous example, one can then 
start a single task *do_something* which processes the list of files fed
as standard input to it, from a named pipe.  

In the examples above, file reception and processing are kept entirely separate.  If there
is a problem with processing, the file reception directories will fill up, potentially
growing to an unwieldy size and causing many practical difficulties.  When a plugin such 
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
a **_do_download** script.  the scripts would access the credentials
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
the connection, once opened, is kept opened. It is reset
(closed and reopened) only when the number of downloads (uploads)
reaches the number given by the  **batch**  option (default 100)

All download (upload) operations uses a buffer. The size, in bytes,
of the buffer used is given by the **bufsize** option (default 8192)

-----------------------
Sending vs. Subscribing
-----------------------

FIXME: local_file vs. remote_file
if you are using 


Variables Available 
-------------------

Without peering into the python source code of sarracenia, it is hard to know
what values are available to plugin scripts.  As a cheat to save developers
from having to understand the source code, a diagnostic plugin might be helpful.

if one sets **on_message msg_dump** in a configuration, the entire
list of available variables can be displayed in a log file::

Make the above file an on_file (or other trigger) script in a configuration, start up a receiver 
(and if it is a busy one, then stop it immediately, as it creates very large log messages for 
every message received.)  Essentially the entire program state is available to plugins. 

A sample output is shown (reformatted for legibility) is given below.  For every field *xx* listed,
a plugin script can access it as *parent.xx*  (e.g. *parent.queue_name* )::

  peter@idefix:~/test$ sr_subscribe dd.conf foreground
  ^C to stop it immediately after the first message.
  peter@idefix:~/test$ tail -f ~/.cache/sarra/log/sr_subscribe_dd_0001.log 
  
  # the following is reformatted to look reasonable on a page.
  2016-01-14 17:13:01,649 [INFO] {
  'kbytes_ps': 0, 
  'queue_name': None, 
  'flatten': '/', 
  'exchange': 'xpublic',
  'discard': False,
  'log_back': True,
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
  'local_url': ParseResult(scheme='file', netloc='',
  path='/local/home/peter/test/dd/bulletins/alphanumeric/20160114/SA/CYVT/22/SACN62_CYVT_142200___11878',
  params='', query='', fragment=''),
  'sumflg': 'd',
  'user_log_dir': '/local/home/peter/.cache/sarra/log',
  'topic_prefix': 'v02.post',
  'local_file': 'SACN62_CYVT_142200___11878',
  'on_post': None,
  'do_poll': None,
  'message_ttl': None,
  'user_scripts_dir': '/local/home/peter/.config/sarra/scripts',
  'recursive': False,
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
  'log_clusters': {},
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
  'local_dir': '/local/home/peter/test/dd/bulletins/alphanumeric/20160114/SA/CYVT/22',
  'user_config': 'dd.conf',
  'lpath': '/local/home/peter/.cache/sarra/log/sr_subscribe_dd_0001.log',
  'bufsize': 8192,
  'do_download': None,
  'post_exchange': None,
  'log_exchange': 'xlog',
  'local_path': '/local/home/peter/test/dd/bulletins/alphanumeric/20160114/SA/CYVT/22/SACN62_CYVT_142200___11878',
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


No thought has yet been given to plug_in compatatibility across versions.  Unclear how much of 
this state will vary over time.  Similar to program configuration settings, all of the fields
involved in processing individual messages are available in the parent.msg object.  A similar
dump to the above is here (e.g of a python scripts can use *parent.msg.partsr* , 
and/or *parent.msg.header.parts*  in their code.):: 


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
 'log_exchange': 'xs_anonymous', 
 'part_ext': 'Part', 
 'topic_prefix': 'v02.post', 
 'current_block': 0, 
 'tbegin': 1466165094.82, 
 'local_file': '/home/peter/test/dd/bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919', 
 'remainder': 0, 
 'to_clusters': ['DD', 'DDI.CMC', 'DDI.EDM'], 
 'local_offset': 0, 
 'mtype': 'post', 
  'user': 'anonymous', 
  'bufsize': 8192, 'local_url': 
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
  'log_notice': '20160617120454.820 http://dd2.weather.gc.ca/ bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919 201 blacklab anonymous 3.591402', 
  'version': 'v02', 
  'parent': <sarra.sr_subscribe.sr_subscribe object at 0x7f775682b4a8>, 
  'logger': <logging.RootLogger object at 0x7f77563359e8>, 
  'length': 78, 
  'topic': 'v02.post.bulletins.alphanumeric.20160617.CA.CWAO.12', 
  'inplace': True, 
  'urlcred': 'http://dd2.weather.gc.ca/', 
  'sumstr': 'd,ab1ba0020e91119fb024a2c115ccd908', 
  'log_topic': 'v02.report.bulletins.alphanumeric.20160617.CA.CWAO.12', 
  'publisher': None, 
  'code': 201, 
  'urlstr': 'http://dd2.weather.gc.ca/bulletins/alphanumeric/20160617/CA/CWAO/12/CACN00_CWAO_171133__WAR_00919', 
  'lastchunk': True, 
  'sumflg': 'd', 
  'offset': 0, 
  'partflg': '1', 
  'log_publisher': <sarra.sr_amqp.Publisher object at 0x7f77551c7518>}


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
    
    class File_Noop(object):
          def __init__(self,parent):
              if not hasattr(parent,'file_string'):
                 parent.file_string='hello world'
    
    
          def perform(self,parent):
              logger = parent.logger
    
              logger.info("file_noop: I have no effect but adding a log line with %s in it" % parent.file_string )
    
              return True
    
    #file_noop=File_Noop(self)
    #self.on_file=file_noop.perform

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
    testparent.on_file = filenoop.perform

So now it can be invoked with::

    blacklab% python noop.py
    blacklab% 

Which confirms that there are at least no syntax errors. One will need to add more scaffolding
depending on the complexity of the plugin.  One can append an invocation of the plugin to the test
script, like so::
  
   self.on_file(self)


and then the routine will run. the more complex the plugin, the more needs to be added to the 
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

      def perform(self,parent):
          msg    = parent.msg

          # writing filename in pipe
          f = open('/users/dor/aspy/mjg/mon_fifo','w')
          f.write(msg.local_file)
          f.flush()
          f.close()

          # resume process as usual ?
          return True

  transformer=Transformer()
  #self.on_file = transformer.perform

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
          self.local_file = "a string"
          self.headers = {}

  class TestParent(object):
      def __init__(self):
          self.msg = TestMessage()
          self.logger = TestLogger()
          pass

  testparent=TestParent()

  transformer.perform(testparent)

The part after the #self.on_file line is only a test harness.  
One creates a calling object with the fields needed to test the 
fields the plugin will use in the TestParent and TestMessage classes.


-------------------------------------
File Notification Without Downloading
-------------------------------------

If the data pump exists in a large shared environment, such as
a Supercomputing Centre with a site file system.  In that case,
the file might be available without downloading.  So just
obtaining the file notification and transforming it into a 
local file is sufficient::

  blacklab% cat >../dd_swob.conf <<EOT

  broker amqp://anonymous@dd.weather.gc.ca
  subtopic observations.swob-ml.#
  document_root /data/web/dd_root
  on_message do_something

  accept .*
  # do_something will catenate document_root with the path in 
  # the notification to obtain the full local path.


on_message is a scripting hook, exactly like on_file, that allows
specific processing to be done on receipt of a message.  A message will
usually correspond to a file, but for large files, there will be one
message per part. One can use the parent.msg.partstr to find out which part 
you have (See `sr_post.1 <sr_post.1.html>`_ for details on partstr encoding. 

Ensure the on_message plugin returns 'False' to prevent downloading.


.. note:: 
   **FIXME**: perhaps show a way of checking the parts header to 
   with an if statement in order to act on only the first part message
   for long files.

   **FIXME**: is .py needed on on\_ triggers?


----------
do_scripts
----------

FIXME

-------
Polling
-------

Sample polling.


----------------
Checksum Plugins
----------------

FIXME




-------------------------------------
Accessing Messages without Sarracenia
-------------------------------------

FIXME, link to amqplib, or java bindings, and a pointer to the sr_post and sr_report section 7 man pages.
