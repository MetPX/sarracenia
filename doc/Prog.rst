
===================
 Programmers Guide
===================

------------------------------------------
 Working with Plugins for Metpx-Sarracenia
------------------------------------------

Status: Pre-Draft

.. note::
  Pardon the dust, This package is alpha, not ready for general use yet. Please Stay Tuned!
  **FIXME**: Missing sections are highlighted by **FIXME**.  What is here should be accurate!

.. Contents::

Introduction
------------

A Sarracenia data pump is a web server with notifications for subscribers to know, quickly, 
when new data has arrived.  To find out what data is already available on a pump, view the 
tree with a web browser.  For simple immediate needs, one can download data using the browser 
itself, or a standard tool such as wget.  The usual intent is for sr_subscribe to automatically 
download the data wanted to a directory on a subscriber machine where other software can process it.  

Often, the purpose of automated downloading is to have other code ingest the files and perform further
processing.  Rather than having a separate process have to look at a file in a directory, Sarracenia
provides a means of customizing processing via plugins written in python 3. A first example:

There are ways to insert scripts into the flow of messages and file downloads:
Should you want to implement tasks in various part of the execution of the program:

- **on_message  <script>        (default: msg_log)**
- **on_file     <script>        (default: file_log)**
- **on_part     <script>        (default: None)**
- **on_post     <script>        (default: None)**

There are also do\_ scripts, which provide or replace functionality in programs:

- **do_download     <script>        (default: None)**
- **do_poll         <script>        (default: None)**
- **do_send         <script>        (default: None)**


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

The only argument the script receives is **parent**, which has all of option settings from configuration
files and command line as attributes, and so are available for use.  In any configuration file,
one would set::

  file_string oh my goodness
  on_file file_noop

Should one of these scripts return False, the processing of the message/file
will stop there and another message will be consumed from the broker.







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
   **FIXME**


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
          self.rxpipe.write( msg.local_file + "\n" )
          self.rxpipe.flush()
          return None

  rxpipe =File_RxPipe(self)

  self.on_file=rxpipe.perform

Before running this code, at the command line, create the named pipe::

  mkfifo /local/home/peter/test/npipe

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


What Fields are Available to on\_ Scripts?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Without peering into the python source code of sarracenia, it is hard to know
what values are available to plugin scripts.  As a cheat to save developers
from having to understant the source code, a diagnostic plugin might be helpful.

if one sets the following script as a trigger in a configuration, the entire
list of available variables can be displayed in a log file::

  cat >dump_msg.py <<EOT
  import os,stat,time

  class Transformer(object):
      def __init__(self):
          pass

      def perform(self,parent):
          parent.logger.info("PARENT = \n")
          parent.logger.info(vars(parent))
          parent.logger.info("message = \n")
          parent.logger.info(vars(parent.msg))
          return False

transformer = Transformer()
self.on_file = transformer.perform

EOT

Make the above file an on_file (or other trigger) script in a configuration, start up a receiver (and if it is a busy one, then stop it immediately, as it creates
very large log messages for every message received.)  Essentially the entire program state is available to plugins. A sample output is shown

below::

  peter@idefix:~/test$ sr_subscribe dd.conf start
  peter@idefix:~/test$ sr_subscribe dd.conf stop  # do this immediately for a receiver with high traffic!
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

  2016-01-14 17:13:01,649 [INFO] message = 

No thought has yet been given to plug_in compatatibility across versions.  Unclear how much of this state will vary over time.


Debugging on\_ Scripts
~~~~~~~~~~~~~~~~~~~~~~

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
message per part. Checking the xxx...**FIXME** to find out which part 
you have. One can use sr_subscribe and set an the on_message 
plugin to return 'False' to prevent downloading.


.. note:: 
   **FIXME**: perhaps show a way of checking the parts header to 
   with an if statement in order to act on only the first part message
   for long files.

   **FIXME**: is .py needed on on\_ triggers?


do_scripts
----------

FIXME


Polling
-------

Sample polling.


Checksum Plugins
----------------

FIXME


Accessing Messages without Sarracenia
-------------------------------------

FIXME, link to amqplib, or java bindings, and a pointer to the sr_post and sr_log section 7 man pages.
