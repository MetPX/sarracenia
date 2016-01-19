===========
 SR_CONFIG 
===========

-------------------------------------
Overview of Sarra Configuration Files
-------------------------------------

:Manual section: 7
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite



SYNOPSIS
========

 - **sr_component** <config> [foreground|start|stop|restart|status]
 - **<config_dir>**/ [ default.conf ]
 - **<config_dir>**/ [ sarra | subscribe | log | sender ] / <config.conf>
 - **<config_dir>**/ scripts / <script.py>

DESCRIPTION
===========

Metpx Sarracenia components are the specific functional programs: sr_subscribe, 
sr_sarra, sr_sender, sr_log, etc...  When any component is invoked, a configuration
file is given to indicate which configuration to operate on, and an operation
is given:  The operation is one of:

 - foreground:  run a single instance in the foreground logging to stderr
 - restart: stop and then start the configuration.
 - start:  start the configuration running
 - status: check if the configuration is running.
 - stop: stop the configuration from running 

For example:  *sr_subscribe dd foreground* runs the sr_subcribe component with the dd configuration
as a single foreground instance.

Metpx Sarracenia is configured using a tree of text files using a common
syntax.  The location of config dir is platform dependent::

 - linux: ~/.config/sarra
 - Windows: %AppDir%/science.gc.ca/sarra, this might be:
   C:\Users\peter\AppData\Local\science.gc.ca\sarra

The top of the tree contains a file 'default.conf' which contains setting that
are read as defaults for any component which is started up.   default.conf
will be read by every component on startup.   
Individual configuration files
can be placed anywhere and invoked with the complete path.   When components
are invoked, the provided file is interpreted as a file path (with a .conf
suffix assumed)  If it is not found as file path, then the component will
look in the component's config directory ( **config_dir** / **component** )
for a matching .conf file.

Options are placed in configuration files, one per line, in the form: 

 **option <value>** 

For example::

  **debug true**

sets the *debug* option to enable more verbose logging.  To provide non-functional 
description of configuration, or comments, use lines that begin with a **#**.  

Options and command line arguments are equivalent.  Every command line argument 
has a corresponding long version starting with '--'.  For example *-u* has the 
long form *--url*. One can also specify this option in a configuration file. 
To do so, use the long form without the '--', and put its value separated by a space.
The following are all equivalent:

  - **url <url>** 
  - **-u <url>**
  - **--url <url>**

Settings in an individual .conf file are read in after the default.conf
file, and so can override defaults.   Options specified on
the command line override configuration files.

Settings are interpreted in order.  Each file is read from top to bottom.
for example:

sequence #1::

  reject *gif
  accept .*

sequence #2::

  accept .*
  reject *gif

In sequence #1, all files ending in 'gif' are rejected.  In sequence #2, the accept .* (which
accepts everything) is encountered before the reject statement, so the reject has no effect.


CREDENTIALS 
-----------

Ther username and password or keys used to access servers are examples of credentials.
In order to reduce the sensitivity of most configuration files, the credentials
are stored in a single file apart from all other settings.  The credentials.conf file
is the only mandatory configuration file for all users.

For all **sarracenia** programs, the confidential parts of credentials are stored
only in ~/.conf/sarra/credentials.conf.  This includes the destination and the broker
passwords and settings needed by components.  The format is one entry per line.  Examples:

- **amqp://user1:password1@host/**
- **amqps://user2:password2@host:5671/dev**

- **sftp://user5:password5@host**
- **sftp://user6:password6@host:22  ssh_keyfile=/users/local/.ssh/id_dsa**

- **ftp://user7:password7@host  passive,binary**
- **ftp://user8:password8@host:2121  active,ascii**

- **ftps://user7:password7@host  passive,binary,tls**
- **ftps://user8:password8@host:2121  active,ascii,tls,prot_p**

In other configuration files or on the command line, the url simply lacks the
password or key specification.  The url given in the other files is looked
up in credentials.conf.

To implement supported of additional protocols, one would write 
a **_do_download** script.  the scripts would access the credentials 
value in the script with the code :   

- **ok, details = parent.credentials.get(msg.urlcred)**
- **if details  : url = details.url**


BROKER
------

All components interact with a broker in some way, so this option will be found
either in the default.conf or each specific configuration file.
The broker option tell each component which broker to contact.

**broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::
      (default: None and it is mandatory to set it ) 

Once connected to an AMQP broker, the user needs to bind a queue
to exchanges and topics to determine the messages of interest.

To configure in administrative mode, set an option *manager* in the same
format as broker, to specify how to connect to the broker for administrative
purposes.  See Administration Guide for more information.

AMQP QUEUE BINDINGS
-------------------

Once connected to an AMQP broker, the user needs to create a queue and bind it
to an exchange.  These options define which messages (URL notifications) the program receives:

 - **exchange      <name>         (default: xpublic)** 
 - **topic_prefix  <amqp pattern> (default: v00.dd.notify -- developer option)** 
 - **subtopic      <amqp pattern> (subtopic need to be set)** 

Several topic options may be declared. To give a correct value to the subtopic,
browse the our website  **http://dd.weather.gc.ca**  and write down all directories of interest.
For each directories write an  **subtopic**  option as follow:

 **subtopic  directory1.*.subdirectory3.*.subdirectory5.#** 

::

 where:  
       *                replaces a directory name 
       #                stands for the remaining possibilities

One has the choice of filtering using  **subtopic**  with only AMQP's limited wildcarding, or the 
more powerful regular expression based  **accept/reject**  mechanisms described below.  The 
difference being that the AMQP filtering is applied by the broker itself, saving the 
notices from being delivered to the client at all. The  **accept/reject**  patterns apply to 
messages sent by the broker to the subscriber.  In other words,  **accept/reject**  are 
client side filters, whereas  **subtopic**  is server side filtering.  

It is best practice to use server side filtering to reduce the number of announcements sent
to the client to a small superset of what is relevant, and perform only a fine-tuning with the 
client side mechanisms, saving bandwidth and processing for all.

topic_prefix is primarily of interest during protocol version transitions, where one wishes to 
specify a non-default protocol version of messages to subscribe to. 

.. NOTE:: 
  FIXME: no mention of the use of exchange argument.


AMQP QUEUE SETTINGS
-------------------

The queue is where the notifications are held on the server for each subscriber.

- **queue_name    <name>         (default: q_<brokerUser>)** 
- **durable       <boolean>      (default: False)** 
- **expire        <minutes>      (default: None)** 
- **message-ttl   <minutes>      (default: None)** 

By default, components create a queue name that should be unique and starts with  **q_** 
and is usually followe
and puts it into a file .<configname>.queue, where <configname> is the config filename.

.. note::
   FIXME, this file placement is obsolete, goes in .cache now?

The  **expire**  option is expressed in minutes... it sets how long should live
a queue without connections The  **durable** option set to True, means writes the queue
on disk if the broker is restarted.
The  **message-ttl**  option set the time in minutes a message can live in the queue.
Past that time, the message is taken out of the queue by the broker.



.. note::
   FIXME: how does this work with ssh_keyfile, active/passive, ascii/binary ?
   non url elements of the entry. details.ssh_keyfile?

ROUTING
-------

Sources of data need to indicate the clusters to which they would like data to be delivered.
Data Pumps need to identify themselves, and their neighbors in order to pass data to them.

**cluster** 
   The name of the local cluster.

**cluster_aliases** <alias>,<alias>,...
   Alternate names for the cluster.

**gateway_for**
   If this pump sees data on a remote cluster that is destined for one of the clusters in this list, 
   then retrieve it for forwarding there.

**to** <cluster>,<cluster>,<cluster>...
   for programs that inject data, to inform the pumping network of the intended destination of data
   being injected.

sr_sarra interprets *cluster, cluster_aliases*, and *gateway_for*, such that products which are not 
meant for the local cluster are not downloaded.  Similarly, sr_sender interprets these options such that only 
intended is sent to remote clusters.



DELIVERY SPECIFICATIONS
-----------------------

Theses options set what files the user wants and where it will be placed,
and under which name.

- **accept    <regexp pattern> (must be set)** 
- **directory <path>           (default: .)** 
- **flatten   <boolean>        (default: false)** 
- **lock      <.string>        (default: .tmp)** 
- **mirror    <boolean>        (default: false)** 
- **overwrite <boolean>        (default: true)** 
- **reject    <regexp pattern> (optional)** 
- **strip     <count>         (default: 0)**

The  **lock**  option is a suffix given to the file during the download
and taken away when it is completed... If  **lock**  is set to  **.** 
then it is prefixed with it and taken away when it is completed...
This gives a mean to avoid processing the file prematurely.

The option directory  defines where to put the files on your server.
Combined with  **accept** / **reject**  options, the user can select the
files of interest and their directories of residence. (see the  **mirror**
option for more directory settings).

The  **accept**  and  **reject**  options use regular expressions (regexp) to match URL.
Theses options are processed sequentially. 
The URL of a file that matches a  **reject**  pattern is never downloaded.
One that match an  **accept**  pattern is downloaded into the directory
declared by the closest  **directory**  option above the matching  **accept**  option.

::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*

The  **mirror**  option can be used to mirror the dd.weather.gc.ca tree of the files.
If set to  **True**  the directory given by the  **directory**  option
will be the basename of a tree. Accepted files under that directory will be
placed under the subdirectory tree leaf where it resides under dd.weather.gc.ca.
For example retrieving the following url, with options::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

You can modify the mirrored directoties with the option **strip**  .
If set to N  (an integer) the first 'N' directories are withdrawn.
For example :

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   strip     3
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

The  **flatten**  option is use to set a separator character. This character
will be used to replace the '/' in the url directory and create a "flatten" filename
form its dd.weather.gc.ca path.  For example retrieving the following url, 
with options::

 http://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/12/015/CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

   flatten   -
   directory /mylocaldirectory
   accept    .*model_gem_global.*

would result in the creation of the filepath ::

 /mylocaldirectory/model_gem_global-25km-grib2-lat_lon-12-015-CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2


The  **overwrite**  option,if set to false, avoid unnecessary downloads under these conditions :
1- the file to be downloaded is already on the user's file system at the right place and
2- the checksum of the amqp message matched the one of the file.
The default is True (overwrite without checking).

EXAMPLES
--------

Here is a short complete example configuration file:: 

  broker amqp://dd.weather.gc.ca/

  subtopic model_gem_global.25km.grib2.#
  accept .*

This above file will connect to the dd.weather.gc.ca broker, connecting as
anonymous with password anonymous (defaults) to obtain announcements about
files in the http://dd.weather.gc.ca/model_gem_global/25km/grib2 directory.
All files which arrive in that directory or below it will be downloaded 
into the current directory (or just printed to standard output if -n option 
was specified.) 

A variety of example configuration files are available here:

 `http://sourceforge.net/p/metpx/git/ci/master/tree/sarracenia/samples/config/ <http://sourceforge.net/p/metpx/git/ci/master/tree/sarracenia/samples/config>`_



INSTANCES
---------

It is possible that one instance of a component and configuration is not enough to process & send all available notifications.  The *instances* option allows several processes running the same configuration to share the load. the following option in a configuration file:

**instances      <integer>     (default:1)**

will result in launching N instances of the component using that config.
In the ~/.cache/sarra directory, a number of runtime files are created::

  A .sr_sender_configname_$instance.pid is created, containing the PID  of $instance process.
  A sr_sender_configname_$instance.log  is created as a log of $instance process.

The logs can be written in another directory than the default one with option :

**log            <directory logpath>  (default:~/.cache/<component>/log)**

.. note::  
  FIXME: indicate windows location also... dot files on windows?


.. Note::

  While the brokers keep the queues available for some time, Queues take resources on 
  brokers, and are cleaned up from time to time.  A queue which is not accessed for 
  a long (implementation dependent) period will be destroyed.  A queue which is not
  accessed and has too many (implementation defined) files queued will be destroyed.
  Processes which die should be restarted within a reasonable period of time to avoid
  loss of notifications.


RABBITMQ LOGGING
----------------

For each download, an amqp log message is sent back to the broker.
Should you want to turned them off the option is :

- **log_back <boolean>        (default: true)** 



PLUGIN SCRIPTS
--------------

Metpx Sarracenia provides minimum functionality to deal with the most common cases, but provides
flexibility to override those common cases with user plugins scripts, written in python.  
MetPX comes with a variety of scripts which can act as examples.   

Users can place their own scripts in the script sub-directory 
of their config directory tree.

.. note:: 
   FIXME: where the default scripts are stored is an unresolved issue. 
   sr components are supposed to look there, but we have not figured that out yet.

There are two varieties of
scripts:  do\_* and on\_*.  Do\_* scripts are used to implement functions, replacing built-in
functionality, for example, to implement additional transfer protocols.  

- do_download - to implement additional protocols.


On\_* scripts are used more often. They allow actions to be inserted to augment the default 
processing for various specialized use cases. The scripts are invoked by having a given 
configuration file specify an on_<event> option. The event can be one of:

- on_file -- When the reception of a file has been completed, trigger followup action.

- on_log -- when an sr_log message is received by sr_log, or about to be sent by any other
  component.

- on_msg -- when an sr_post(7) message has been received.  For example, a message has been received 
  and additional criteria are being evaluated for download of the corresponding file.  if the on_msg 
  script returns false, then it is not downloaded.  (see discard_when_lagging.py, for example,
  which decides that data that is too old is not worth downloading.)

- on_part -- Large file transfers are split into parts.  Each part is transferred separately.
  When a completed part is received, one can specify additional processing.

- on_post -- when a data source (or sarra) is about to post a message, permit customized
  adjustments of the post.

The simplest example of a script: A do_nothing.py script for **on_file**::

  class Transformer(object): 
      def __init__(self):
          pass

      def perform(self,parent):
          logger = parent.logger

          logger.info("I have no effect but adding this log line")

          return True

  transformer  = Transformer()
  self.on_file = transformer.perform

The only arguments the script receives it **parent**, which is an instance of
the **sr_subscribe** class
Should one of these scripts return False, the processing of the message/file
will stop there and another message will be consumed from the broker.
For other events, the last line of the script must be modified to correspond.

More examples are available in the Guide documentation.


SEE ALSO
--------

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
