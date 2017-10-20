==============
 SR_Subscribe 
==============

-----------------------------------------------
Select and Conditionally Download Posted Files
-----------------------------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite



SYNOPSIS
========

 **sr_subscribe** foreground|start|stop|restart|reload|status configfile
 **sr_subscribe** cleanup|declare|setup configfile
 (formerly **dd_subscribe** )

DESCRIPTION
===========


Sr_subscribe is a program to efficiently download files from websites or file servers 
that provide `sr_post(7) <sr_post.7.html>`_ protocol notifications.  Such sites 
publish a message for each file as soon as it is available.  Clients connect to a
*broker* (often the same as the server itself) and subscribe to the notifications.
The *sr_post* notifications provide true push notices for web-accessible folders (WAF),
and are far more efficient than either periodic polling of directories, or ATOM/RSS style 
notifications. Sr_subscribe can be configured to post messages after they are downloaded,
to make them available to consumers for further processing or transfers.

**sr_subscribe** can also be used for purposes other than downloading, (such as for 
supplying to an external program) specifying the -n (*notify_only*, or *no download*) will
suppress the download behaviour and only post the URL on standard output.  The standard
output can be piped to other processes in classic UNIX text filter style.  

The **sr_subscribe** command takes two argument: action start|stop|restart|reload|status (self described)
followed by an a configuration file described below.

The **foreground** action is different. It would be used when building a configuration
or debugging things. It is used when the user wants to run the program and its configfile 
interactively...   The **foreground** instance is not concerned by other actions, 
but should the configured instances be running it shares the same (configured) message queue.
The user would stop using the **foreground** instance by simply pressing <ctrl-c> on linux 
or use other means to kill its process. That would be the old **dd_subscribe** behavior...

The actions **cleanup**, **declare**, **setup** can be used to manage resources on
the rabbitmq server. The resources are either queues or exchanges. **declare** creates
the resources. **setup** creates and additionnaly does the bindings of queues.

CONFIGURATION
=============

In general, the options for this component are described by the
`sr_config(7) <sr_config.7.html>`_  page which should be read first.
That page fully explains the option configuration language, and how to find
the option settings. briefly:


CONFIGURATION FILES
-------------------

Place settings, one per line with a keyword first, and the setting value afterward
example configuration line::

 broker amqp://anonymous@dd.weather.gc.ca

In the above example, *broker* is the option keyword, and the rest of the line is the value assigned to the setting.

The configuration file for an sr_subscribe configuration called *myflow*

 - linux: ~/.config/sarra/subscribe/myflow.conf (as per: `XDG Open Directory Specication <https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.html>`_ ) 


 - Windows: %AppDir%/science.gc.ca/sarra/myflow.conf , this might be:
   C:\Users\peter\AppData\Local\science.gc.ca\sarra\myflow.conf

It is just a sequence of settings, one per line. Note that the files are read in order, most importantly for
*directory* and *accept* clauses.  Example::

    directory A
    accept X

Places files matching X in directory A.

vs::
    accept X
    directory A

Places files matching X in the current working directory, and the *directory A* setting does nothing.

    
LOG FILES
---------

As sr_subscribe usually runs as a daemon (unless invoked in *foreground* mode) one normally examines its log
file to find out how processing is going.  The log files are placed, as per the  XDG Open Directory Specification,
There will be a log file for each *instance* (download process) of an sr_subscribe process running the myflow configuration::

   linux in linux: ~/.cache/sarra/log/sr_subscribe_myflow_0001.log
   Windows: FIXME? dunno.

One can override placement on linux by setting the XDG_CACHE_HOME environment variable.



CREDENTIAL OPTIONS
------------------

One normally does not specify passwords in configuration files.  Rather they are placed in the credentials file.
so for every url specified, that requires a password, one places a matching entry in credentials.conf.
The broker option sets all the credential information to connect to the  **RabbitMQ** server 

- **broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqp://anonymous:anonymous@dd.weather.gc.ca/ ) 

All sr\_ tools store all sensitive authentication info in the credentials.conf file.
Passwords for SFTP, AMQP, and HTTP accounts are stored in URL´s there, as well as other pointers
to things such as private keys, or FTP modes.  SFTP is a special case, in that if the .ssh config files
are configured for use by OpenSSH, the tools will try to interpret them such that likel no sftp entry 
is required as long as one can sftp onto the host without a challenge (the configuration specifies which keys
to present, and no passphrase is needed.) 

For more details, see: `sr_config(7) credentials <sr_config.7.html/#credentials>`_  

AMQP QUEUE DECLARATION
----------------------

Once connected to an AMQP broker, the user needs to create a queue.

Setting the queue on broker :

- **queue_name    <name>         (default: q_<brokerUser>.<programName>.<configName>)**
- **durable       <boolean>      (default: False)**
- **expire        <duration>      (default: 5m  == five minutes)**
- **message-ttl   <duration>      (default: None)**
- **prefetch      <N>            (default: 1)**
- **reset         <boolean>      (default: False)**

Usually components guess reasonable defaults for all these values
and users do not need to set them.  For less usual cases, the user
may need to override the defaults.  The queue is where the notifications
are held on the server for each subscriber.

By default, components create a queue name that should be unique. The default queue_name
components create follows :  **q_<brokerUser>.<programName>.<configName>** .
Users can override the defaul provided that it starts with **q_<brokerUser>**.
Some variables can also be used within the queue_name like
**${BROKER_USER},${PROGRAM},${CONFIG},${HOSTNAME}**

The  **durable** option, if set to True, means writes the queue
on disk if the broker is restarted.

The  **expire**  option is expressed as a duration... it sets how long should live
a queue without connections.  A raw integer is expressed in seconds, if the suffix m,h.d,w
are used, then the interval is in minutes, hours, days, or weeks.

The  **durable** option set to True, means writes the queue
on disk if the broker is restarted.

The  **message-ttl**  option set the time a message can live in the queue.
Past that time, the message is taken out of the queue by the broker.

The **prefetch** option sets the number of messages to fetch at one time.
When multiple instances are running and prefetch is 4, each instance will obtain upto four
messages at a time.  To minimize the number of messages lost if an instance dies and have
optimal load sharing, the prefetch should be set as low as possible.  However, over long
haul links, it is necessary to raise this number, to hide round-trip latency, so a setting
of 10 or more may be needed.

When **--reset** is set, and a component is (re)started, its queue is
deleted (if it already exists) and recreated according to the component's
queue options.  This is when a broker option is modified, as the broker will
refuse access to a queue declared with options that differ from what was
set at creation.  It can also be used to discard a queue
quickly when a receiver has been shut down for a long period.

The AMQP protocol defines other queue options which are not exposed
via sarracenia, because sarracenia itself picks appropriate values.



AMQP QUEUE BINDINGS
-------------------

Once one has a queue, it must be bounde to an exchange.
Users almost always need to set these options.  Once a queue exists
on the broker, it must be bound to an exchange.  Bindings define which
messages (URL notifications) the program receives.  The root of the topic
tree is fixed to indicate the protocol version and type of the
message (but developers can override it with the **topic_prefix**
option.)

These options define which messages (URL notifications) the program receives:

 - **exchange      <name>         (default: xpublic)** 
 - **topic_prefix  <amqp pattern> (default: v00.dd.notify -- developer option)** 
 - **subtopic      <amqp pattern> (subtopic need to be set)** 

Several topic options may be declared. To give a correct value to the subtopic,

for more details, see: `sr_config(7) <sr_config.7.html>`_  

One has the choice of filtering using  **subtopic**  with only AMQP's limited wildcarding and
length limited to 255 encoded bytes, or the 
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

Usually, the user specifies one exchange, and several subtopic options.
**Subtopic** is what is normally used to indicate messages of interest.
To use the subtopic to filter the products, match the subtopic string with
the relative path of the product.

For example, consuming from DD, to give a correct value to subtopic, one can
browse the our website  **http://dd.weather.gc.ca** and write down all directories
of interest.  For each directory tree of interest, write a  **subtopic**
option as follow:

 **subtopic  directory1.*.subdirectory3.*.subdirectory5.#**

::

 where:  
       *                replaces a directory name 
       #                stands for the remaining possibilities

One has the choice of filtering using  **subtopic**  with only AMQP's limited wildcarding and
header length limited to 255 encoded bytes, or the more powerful regular expression based  **accept/reject**
mechanisms described below, which are not length limited.  The difference being that
the AMQP filtering is applied by the broker itself, saving the notices from being delivered
to the client at all. The  **accept/reject**  patterns apply to messages sent by the
broker to the subscriber.  In other words,  **accept/reject**  are
client side filters, whereas  **subtopic**  is server side filtering.

It is best practice to use server side filtering to reduce the number of announcements sent
to the client to a small superset of what is relevant, and perform only a fine-tuning with the
client side mechanisms, saving bandwidth and processing for all.

topic_prefix is primarily of interest during protocol version transitions, where one wishes to
specify a non-default protocol version of messages to subscribe to.



DELIVERY SPECIFICATIONS
-----------------------

These options set what files the user wants and where it will be placed,
and under which name.

- **accept    <regexp pattern> (must be set)** 
- **batch     <count>          (default: 100)**
- **default_mode     <octalint>       (default: 0 - umask)**
- **default_dir_mode <octalint>       (default: 0755)**
- **accept_unmatch   <boolean> (default: False)**
- **attempts     <count>          (default: 3)**
- **destfn_script (sundew compatibility... see that section)**
- **directory <path>           (default: .)** 
- **discard   <boolean>        (default: false)**
- **document_root <path>       (default: /)**
- **filename (for sundew compatibility..  see that section)**
- **flatten   <string>         (default: '/')** 
- **inflight  <string>         (default: .tmp)** 
- **mirror    <boolean>        (default: false)** 
- **overwrite <boolean>        (default: true)** 
- **suppress_duplicates   <off|on|999>     (default: off) 
- **reject    <regexp pattern> (optional)** 
- **strip     <count|regexp>   (default: 0)**
- **source_from_exchange  <boolean> (default: False)**


The **attempts** option indicates how many times to attempt downloading the data 
before giving up.  The default of 3 should be appropriate in most cases.
The  **inflight**  option is a suffix given to the file during the download
and taken away when it is completed... If  **inflight**  is set to  **.** 
then it is prefixed with it and taken away when it is completed...
This gives a mean to avoid processing the file prematurely.

The **batch** option is used to indicate how many files should be transferred over a connection, before it is torn down, and re-established.  On very low volume transfers, where timeouts can occur between transfers, this should be lowered to 1.  For most usual situations the default is fine. for higher volume cases, one could raise it to reduce transfer overhead. It is only used for file transfer protocols, not HTTP ones at the moment.

The option directory  defines where to put the files on your server.
Combined with  **accept** / **reject**  options, the user can select the
files of interest and their directories of residence. (see the  **mirror**
option for more directory settings).

The  **accept**  and  **reject**  options use regular expressions (regexp) to match URL.
Theses options are processed sequentially. 
The URL of a file that matches a  **reject**  pattern is never downloaded.
One that match an  **accept**  pattern is downloaded into the directory
declared by the closest  **directory**  option above the matching  **accept** option.
**accept_unmatch** is used to decide what to do when no reject or accept clauses matched.

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
For example ::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   strip     3
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/WGJ/201312141900_WGJ_PRECIP_SNOW.gif
when a regexp is provide in place of a number, it indicates a pattern to be removed
from the relative path.  for example if::

   strip  .*?GIF/

Will also result in the file being placed the same location. 

NOTE::
    with **strip**, use of ? modifier (to prevent *greediness* ) is often helpful. 
    It ensures the shortest match is used.

    For example, given a file name:  radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.GIF
    The expression:  .*?GIF   matches: radar/PRECIP/GIF
    whereas the expression: .*GIF   matches the entire name.


The  **flatten**  option is use to set a separator character. The default value ( '/' )
nullifies the effect of this option.  This character replaces the '/' in the url 
directory and create a "flatten" filename form its dd.weather.gc.ca path.  
For example retrieving the following url, with options::

 http://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/12/015/CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

   flatten   -
   directory /mylocaldirectory
   accept    .*model_gem_global.*

would result in the creation of the filepath ::

 /mylocaldirectory/model_gem_global-25km-grib2-lat_lon-12-015-CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

**document_root** supplies the directory path that is the root of, say a web server tree.
one in the selected notification gives the absolute path of the file.  This can be
provided when the URL actually refers to a local file, to avoid a needless download.
The defaults is None which means that the path in the notification is the absolute one.
**FIXME**: cannot explain this... do not know what it is myself.


The  **overwrite**  option,if set to false, avoid unnecessary downloads under these conditions :
1- the file to be downloaded is already on the user's file system at the right place and
2- the checksum of the amqp message matched the one of the file.
The default is True (overwrite without checking).

The  **discard**  option,if set to true, deletes the file once downloaded. This option can be
usefull when debugging or testing a configuration.

The **source_from_exchange** option is mainly for use by administrators.
If messages is received posted directly from a source, the exchange used is 'xs_<brokerSourceUsername>'.
Such message be missing a source from_cluster headings, or a malicious user may set the values incorrectly.
To protect against malicious settings, administrators should set the **source_from_exchange** option.

When the option is set, values in the message for the *source* and *from_cluster* headers will then be overridden.
self.msg.headers['source']       = <brokerUser>
self.msg.headers['from_cluster'] = cluster

replacing any values present in the message.  This setting should always be used when ingesting data from a
user exchange.  These fields are used to return reports to the origin of injected data.


When **suppress_duplicates** (also **cache** ) is set to a non-zero value, each new message
is compared against previous ones received, to see if it is a duplicate.  If the message is considered a duplicate, it is skipped. What is a duplicate? A file with the same name (including parts header)
and checksum.  every *hearbeat* interval, a cleanup process looks for files in the cache that
have not been referenced in **cache** seconds, and deletes them, in order to keep the cache size
limited.  Different settings are appropriate for different use cases.

Note:: 

  Use of the cache is incompatible with the default *parts 0* strategy, one must specify an 
  alternate strategy.  One must use either a fixed blocksize, or always never partition files. 
  One must avoid the dynamic algorithm that will change the partition size used as a file grows.

  The cache is local to each instance.  When using N instances, the first time a posting is 
  received, it could be picked by one instance, and the second potentially by another one.
  So one should generally use a winnowing configuration (sr_winnow) ahead of a download with
  multiple parallel instances.  


Permission bits on the destination files written are controlled by the *mode* directives.
*preserve_modes* will apply the mode permissions posted by the source of the file.
If no source mode is available, the *default_mode* will be applied to files, and the
*default_dir_mode* will be applied to directories. If no default is specified,
then the operating system  defaults (on linux, controlled by umask settings)
will determine file permissions. (note that the *chmod* option is interpreted as a synonym
for *default_mode*, and *chmod_dir* is a synonym for *default_dir_mode*.)





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

for more details, see: `sr_config(7) <sr_config.7.html>`_  



QUEUES and MULTIPLE STREAMS
---------------------------

When executed,  **sr_subscribe**  chooses a queue name, which it writes
to a file named after the configuration file given as an argument to sr_subscribe**
with a .queue suffix ( ."configfile".queue). 
If sr_subscribe is stopped, the posted messages continue to accumulate on the 
broker in the queue.  When the program is restarted, it uses the queuename 
stored in that file to connect to the same queue, and not lose any messages.

File downloads can be parallelized by running multiple sr_subscribes using
the same queue.  The processes will share the queue and each download 
part of what has been selected.  Simply launch multiple instances
of sr_subscribe in the same user/directory using the same configuration file, 

You can also run several sr_subscribe with different configuration files to
have multiple download streams delivering into the the same directory,
and that download stream can be multi-streamed as well.

.. Note::

  While the brokers keep the queues available for some time, Queues take resources on 
  brokers, and are cleaned up from time to time.  A queue which is not accessed for 
  a long (implementation dependent) period will be destroyed.  A queue which is not
  accessed and has too many (implementation defined) files queued will be destroyed.
  Processes which die should be restarted within a reasonable period of time to avoid
  loss of notifications.


REPORTING
---------

For each download, by default, an amqp report message is sent back to the broker.
This is done with option :

- **report_back <boolean>        (default: True)** 
- **report_exchange <report_exchangename> (default: xreport|xs_*username* )**

When a report is generated, it is sent to the configured *report_exchange*. Administrive
components post directly to *xreport*, whereas user components post to their own 
exchanges (xs_*username*.) The report daemons then copy the messages to *xreport* after validation.

These reports are used for delivery tuning and for data sources to generate statistical information.
Set this option to **False**, to prevent generation of reports for this usage.


OUTPUT POSTING OPTIONS
----------------------

When advertising files downloaded for downstream consumers, one must set 
the rabbitmq configuration for an output broker.

The post_broker option sets all the credential information to connect to the
  output **RabbitMQ** server

**post_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

Once connected to the source AMQP broker, the program builds notifications after
the download of a file has occured. To build the notification and send it to
the next hop broker, the user sets these options :

 - **[--blocksize <value>]            (default: 0 (auto))**
 - **[-pdr|--post_document_root <path>]     (optional)**
 - **post_exchange     <name>         (default: xpublic)**
 - **post_exchange_split   <number>   (default: 0) **
 - **post_url          <url>          (MANDATORY)**
 - **on_post           <script>       (default: None)**


This **blocksize** option controls the partitioning strategy used to post files.
the value should be one of::

   0 - autocompute an appropriate partitioning strategy (default)
   1 - always send entire files in a single part.
   <blocksize> - used a fixed partition size (example size: 1M )

Files can be announced as multiple parts.  Each part has a separate checksum.
The parts and their checksums are stored in the cache. Partitions can traverse
the network separately, and in paralllel.  When files change, transfers are
optimized by only sending parts which have changed.


The *post_document_root* option supplies the directory path that, when combined (or found) 
in the given *path*, gives the local absolute path to the data file to be posted.
The post document root part of the path will be removed from the posted announcement.
for sftp: url's it can be appropriate to specify a path relative to a user account.
Example of that usage would be:  -pdr ~user  -url sftp:user@host
for file: url's, document_root is usually not appropriate.  To post an absolute path,
omit the -dr setting, and just specify the complete path as an argument.

The **url** option sets how to get the file... it defines the protocol,
host, port, and optionally, the user.  It is a good practice not to
notify the credentials and separately inform the consumers about it.

The **post_exchange** option set under which exchange the new notification
will be posted.  Im most cases it is 'xpublic'.

Whenever a publish happens for a product, a user can set to trigger a script.
The option **on_post** would be used to do such a setup.

The **post_exchange_split** option appends a two digit suffix resulting from 
hashing the last character of the checksum to the post_exchange name,
in order to divide the output amongst a number of exchanges.  This is currently used
in high traffic pumps to allow multiple instances of sr_winnow, which cannot be
instanced in the normal way.  example::

    post_exchange_split 5
    post_exchange xwinnow

will result in posting messages to five exchanges named: xwinnow00, xwinnow01,
xwinnow02, xwinnow03 and xwinnow04, where each exchange will receive only one fifth
of the total flow.




PLUGINS
-------

There are ways to insert scripts into the flow of messages and file downloads:
Should you want to implement tasks in various part of the execution of the program:

- **do_download <script>        (default: None)** 
- **on_message  <script>        (default: msg_log)** 
- **on_file     <script>        (default: file_log)** 
- **on_parts    <script>        (default: None)** 

A do_nothing.py script for **on_message**, **on_file**, and **on_part** could be
(this one being for **on_file**)::

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

for more details, see: `sr_config(7) <sr_config.7.html>`_  


ROUTING
=======

*This is of interest to administrators only*

Sources of data need to indicate the clusters to which they would like data to be delivered.
Routing is implemented by administrators, and refers copying data between pumps. Routing is
accomplished using on_message plugins which are provided with the package.

when messages are posted, if not destination is specified, the delivery is assumed to be 
only the pump itself.  To specify the further destination pumps for a file, sources use 
the *to* option on the post.  This option sets the to_clusters field for interpretation 
by administrators.

Data pumps, when ingesting data from other pumps (using shovel, subscribe or sarra components)
should include the *msg_to_clusters* plugin and specify the clusters which are reachable from
the local pump, which should have the data copied to the local pump, for further dissemination.
sample settings::

  msg_to_clusters DDI
  msg_to_clusters DD

  on_message msg_to_clusters

Given this example, the local pump (called DDI) would select messages destined for the DD or DDI clusters,
and reject those for DDSR, which isn't in the list.  This implies that there DD pump may flow
messages to the DD pump.

The above takes care of forward routing of messages and data to data consumers.  Once consumers
obtain data, they generate reports, and those reports need to propagate in the opposite direction,
not necessarily by the same route, back to the sources.  report routing is done using the *from_cluster*
header.  Again, this defaults to the pump where the data is injected, but may be overridden by
administrator action.

Administrators configure report routing shovels using the msg_from_cluster plugin. Example::

  msg_from_cluster DDI
  msg_from_cluster DD

  on_message msg_from_cluster

so that report routing shovels will obtain messages from downstream consumers and make
them available to upstream sources.





SEE ALSO
--------

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_report(1) <sr_report.1.html>`_ - process report messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.


SUNDEW COMPATIBILITY OPTIONS
----------------------------

For compatibility with sundew, there are some additional delivery options which can be specified.

**destfn_script <script> (default:None)**

This option defines a script to be run when everything is ready
for the delivery of the product.  The script receives the sr_sender class
instance.  The script takes the parent as an argument, and for example, any
modification to  **parent.new_file**  will change the name of the file written locally.

**filename <keyword> (default:WHATFN)**

From **metpx-sundew** the support of this option give all sorts of possibilities
for setting the remote filename. Some **keywords** are based on the fact that
**metpx-sundew** filenames are five (to six) fields strings separated by for colons.
The possible keywords are :


**WHATFN**
 - the first part of the sundew filename (string before first :)

**HEADFN**
 - HEADER part of the sundew filename

**SENDER**
 - the sundew filename may end with a string SENDER=<string> in this case the <string> will be the remote filename

**NONE**
 - deliver with the complete sundew filename (without :SENDER=...)

**NONESENDER**
 - deliver with the complete sundew filename (with :SENDER=...)

**TIME**
 - time stamp appended to filename. Example of use: WHATFN:TIME

**DESTFN=str**
 - direct filename declaration str

**SATNET=1,2,3,A**
 - cmc internal satnet application parameters

**DESTFNSCRIPT=script.py**
 - invoke a script (same as destfn_script) to generate the name of the file to write


**accept <regexp pattern> [<keyword>]**

keyword can be added to the **accept** option. The keyword is any one of the **filename**
tion.  A message that matched against the accept regexp pattern, will have its remote_file
plied this keyword option.  This keyword has priority over the preceeding **filename** one.

The **regexp pattern** can be use to set directory parts if part of the message is put
to parenthesis. **sr_sender** can use these parts to build the directory name. The
rst enclosed parenthesis strings will replace keyword **${0}** in the directory name...
the second **${1}** etc.

example of use::


      filename NONE

      directory /this/first/target/directory

      accept .*file.*type1.*

      directory /this/target/directory

      accept .*file.*type2.*

      accept .*file.*type3.*  DESTFN=file_of_type3

      directory /this/${0}/pattern/${1}/directory

      accept .*(2016....).*(RAW.*GRIB).*


A selected message by the first accept would be delivered unchanged to the first directory.

A selected message by the second accept would be delivered unchanged to the second directory.

A selected message by the third accept would be renamed "file_of_type3" in the second directory.

A selected message by the forth accept would be delivered unchanged to a directory.

named  */this/20160123/pattern/RAW_MERGER_GRIB/directory* if the message would have a notice like:

**20150813161959.854 http://this.pump.com/ relative/path/to/20160123_product_RAW_MERGER_GRIB_from_CMC**


Field Replacements
~~~~~~~~~~~~~~~~~~

In MetPX Sundew, there is a much more strict file naming standard, specialised for use with 
World Meteorological Organization (WMO) data.   Note that the file naming convention predates, and 
bears no relation to the WMO file naming convention currently approved, but is strictly an internal 
format.   The files are separated into six fields by colon characters.  The first field, DESTFN, 
gives the WMO (386 style) Abbreviated Header Line (AHL) with underscores replacing blanks::

   TTAAii CCCC YYGGGg BBB ...  

(see WMO manuals for details) followed by numbers to render the product unique (as in practice, 
though not in theory, there are a large number of products which have the same identifiers.)
The meanings of the fifth field is a priority, and the last field is a date/time stamp.  A sample 
file name::

   SACN43_CWAO_012000_AAA_41613:ncp1:CWAO:SA:3.A.I.E:3:20050201200339

If a file is sent to sarracenia and it is named according to the sundew conventions, then the 
following substition fields are available::

  ${T1}    replace by bulletin's T1
  ${T2}    replace by bulletin's T2
  ${A1}    replace by bulletin's A1
  ${A2}    replace by bulletin's A2
  ${ii}    replace by bulletin's ii
  ${CCCC}  replace by bulletin's CCCC
  ${YY}    replace by bulletin's YY   (obs. day)
  ${GG}    replace by bulletin's GG   (obs. hour)
  ${Gg}    replace by bulletin's Gg   (obs. minute)
  ${BBB}   replace by bulletin's bbb
  ${RYYYY} replace by reception year
  ${RMM}   replace by reception month
  ${RDD}   replace by reception day
  ${RHH}   replace by reception hour
  ${RMN}   replace by reception minutes
  ${RSS}   replace by reception second

The 'R' fields from from the sixth field, and the others come from the first one.
When data is injected into sarracenia from Sundew, the *sundew_extension* message header
will provide the source for these substitions even if the fields have been removed
from the delivered file names.




DEPRECATED SETTINGS
-------------------

These settings pertain to previous versions of the client, and have been superceded.

- **host          <broker host>  (unsupported)** 
- **amqp-user     <broker user>  (unsupported)** 
- **amqp-password <broker pass>  (unsupported)** 
- **http-user     <url    user>  (now in credentials.conf)** 
- **http-password <url    pass>  (now in credentials.conf)** 
- **topic         <amqp pattern> (deprecated)** 
- **exchange_type <type>         (default: topic)** 
- **exchange_key  <amqp pattern> (deprecated)** 
- **lock      <locktext>         (renamed to inflight)** 



HISTORY
-------

Dd_subscribe was initially developed for  **dd.weather.gc.ca**, an Environment Canada website 
where a wide variety of meteorological products are made available to the public. It is from
the name of this site that the sarracenia suite takes the dd\_ prefix for it's tools.  The initial
version was deployed in 2013 on an experimental basis.  The following year, support of checksums
was added, and in the fall of 2015, the feeds were updated to v02.  dd_subscribe still works,
but it uses the deprecated settings described above.  It is implemented python2, whereas
the sarracenia toolkit is in python3.

In 2007, when the MetPX was originally open sourced, the staff responsible were part of
Environment Canada.  In honour of the Species At Risk Act (SARA), to highlight the plight
of disappearing species which are not furry (the furry ones get all the attention) and
because search engines will find references to names which are more unusual more easily, 
the original MetPX WMO switch was named after a carnivorous plant on the Species At
Risk Registry:  The *Thread-leaved Sundew*.  

The organization behind Metpx have since moved to Shared Services Canada, but when
it came time to name a new module, we kept with a theme of carnivorous plants, and 
chose another one indigenous to some parts of Canada: *Sarracenia* any of a variety
of insectivorous pitcher plants. We like plants that eat meat!  


dd_subscribe Renaming
~~~~~~~~~~~~~~~~~~~~~

The new module (MetPX-Sarracenia) has many components, is used for more than 
distribution, and more than one web site, and causes confusion for sys-admins thinking
it is associated with the dd(1) command (to convert and copy files).  So, we switched
all the components to use the sr\_ prefix.

