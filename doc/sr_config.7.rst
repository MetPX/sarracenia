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

Metpx Sarracenia components are the programs that can be invoked from the command line: 
examples are: sr_subscribe, sr_sarra, sr_sender, sr_log, When any component is invoked, 
a configuration file and an operation are specified.  The operation is one of:

 - foreground:  run a single instance in the foreground logging to stderr
 - restart: stop and then start the configuration.
 - start:  start the configuration running
 - status: check if the configuration is running.
 - stop: stop the configuration from running 

For example:  *sr_subscribe dd foreground* runs the sr_subcribe component with 
the dd configuration as a single foreground instance.

The **foreground** action is used when building a configuration or for debugging. 
The **foreground** instance will run regardless of other instances which are currently 
running.  Should instances be running, it shares the same message queue with them.
A user stop the **foreground** instance by simply using <ctrl-c> on linux
or use other means to kill the process.


.. contents::


HELP
----

**help** has a component print a list of valid options.

.. note::
   FIXME: Cannot find a component where help works.  Remove? 
   FIXME: OK: sr_post -h works. but not sr_post 'help' (interpreted as a file, naturally.)

**-V**  has a component print out a version identifier and exit.



OPTIONS
=======


Finding Option Files
--------------------

Metpx Sarracenia is configured using a tree of text files using a common
syntax.  The location of config dir is platform dependent (see python appdirs)::

 - linux: ~/.config/sarra
 - Windows: %AppDir%/science.gc.ca/sarra, this might be:
   C:\Users\peter\AppData\Local\science.gc.ca\sarra

The top of the tree contains a file 'default.conf' which contains settings that
are read as defaults for any component on start up.   Individual configuration 
files can be placed anywhere and invoked with the complete path.   When components
are invoked, the provided file is interpreted as a file path (with a .conf
suffix assumed.)  If it is not found as file path, then the component will
look in the component's config directory ( **config_dir** / **component** )
for a matching .conf file.

If it is still not found, it will look for it in the site config dir 
(linux: /usr/share/default/sarra/**component**). 

Finally, if the user has set option **remote_config** to True and if he has
configured web sites where configurations can be found (option **remote_config_url**),
The program will try to download the named file from each site until it finds one.  
If successful, the file is downloaded to **config_dir/Downloads** and interpreted 
by the program from there.  There is a similar process for all *plugins* that can 
be interpreted and executed within sarracenia components.  Components will first 
look in the *plugins* directory in the users config tree, then in the site 
directory, then in the sarracenia package itself, and finally it will look remotely.

.. note::
   FIXME provide some sample file locations
   FIXME network search path... 



Option Syntax
-------------

Options are placed in configuration files, one per line, in the form: 

 **option <value>** 

For example::

  **debug true**

sets the *debug* option to enable more verbose logging.  To provide non-functional 
description of configuration, or comments, use lines that begin with a **#**.  

**All options are case sensitive.**  **Debug** is not the same as **debug** or **DEBUG**.
Those are three different options (two of which do not exist and will have no effect,
but should generate an ´unknown option warning´.)

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

  reject .*\.gif
  accept .*

sequence #2::

  accept .*
  reject .*\.gif


.. note::
   FIXME: does this match only files ending in 'gif' or should we add a $ to it?
   will it match something like .gif2 ? is there an assumed .* at the end?


In sequence #1, all files ending in 'gif' are rejected.  In sequence #2, the accept .* (which
accepts everything) is encountered before the reject statement, so the reject has no effect.


Several options that need to be reused in different config file can be grouped in a file.
In each config where the options subset should appear, the user would then use :

  - **--include <includeConfigPath>**

The includeConfigPath would normally reside under the same config dir of its master configs.
There is no restriction, any option  can be placed in a config file included. The user must
be aware that, for most options, several declarations means overwriting their values.


CREDENTIALS 
===========

Usernames and passwords or keys used to access servers are examples of credentials.
In order to reduce the sensitivity of most configuration files, the credentials
are stored in a single file apart from all other settings.  The credentials.conf file
is the only mandatory configuration file for all users.

For all **sarracenia** programs, the confidential parts of credentials are stored
only in ~/.config/sarra/credentials.conf.  This includes the destination and the broker
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


CONSUMER
========

Most Metpx Sarracenia components loop on reception and consumption of sarracenia 
AMQP messages.  Usually, the messages of interest are sr_post messages, announcing 
the availability of a file by publishing it´s URL ( or a part of a file ), but there are 
also sr_log(7) messages which can be processed using the same tools.  AMQP messages are
published to an exchange on a broker (AMQP server.)  The exchange delivers
messages to queues.  To receive messages, one must provide the credentials to connect to
the broker (AMQP message pump).  Once connected, a consumer needs to create a queue to
hold pending messages.  The consumer must then bind the queue to one or more exchanges so that
they put messages in its queue.

Once the bindings are set, the program can receive messages. When a message is received,
further filtering is possible using regular expression onto the AMQP messages.
After a message passes this selection process, and other internal validation, the
component can run an **on_message** plugin script to perform additional message processing.
If this plugin returns False, the message is discarded. If True, processing continues.

The following sections explains all the options to set this "consuming" part of
sarracenia programs. 


Setting the Broker 
------------------

**broker amqp{s}://<user>:<password>@<brokerhost>[:port]/<vhost>**

An AMQP URI is used to configure a connection to a message pump (aka AMQP broker.)
Some sarracenia components set a reasonable default for that option.
You provide the normal user,host,port of connections.  In most configuration files,
the password is missing.  The password is normally only included in the credentials.conf file.

Sarracenia work has not used vhosts, so **vhost** should almost always be **/**.

for more info on the AMQP URI format: ( https://www.rabbitmq.com/uri-spec.html )


either in the default.conf or each specific configuration file.
The broker option tell each component which broker to contact.

**broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::
      (default: None and it is mandatory to set it ) 

Once connected to an AMQP broker, the user needs to bind a queue
to exchanges and topics to determine the messages of interest.

Creating the Queue
------------------

Usually components guess reasonable defaults for all these values
and users do not need to set them.  For less usual cases, the user
may need to override the defaults.  The queue is where the notifications 
are held on the server for each subscriber.

- **queue_name    <name>         (default: q_<brokerUser>.<programName>.<configName>)** 
- **durable       <boolean>      (default: False)** 
- **expire        <minutes>      (default: None)** 
- **message-ttl   <minutes>      (default: None)** 

By default, components create a queue name that should be unique. The default queue_name
components create follows :  **q_<brokerUser>.<programName>.<configName>** .
Users can override the defaul provided that it starts with **q_<brokerUser>**.
Some variables can also be used within the queue_name like
**${BROKER_USER},${PROGRAM},${CONFIG},${HOSTNAME}**

The  **durable** option, if set to True, means writes the queue
on disk if the broker is restarted.

The  **expire**  option is expressed in minutes... it sets how long should live
a queue without connections The  **durable** option set to True, means writes the queue
on disk if the broker is restarted.

The  **message-ttl**  option set the time in minutes a message can live in the queue.
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


Binding a Queue to an Exchange
------------------------------

Users almost always need to set these options.  Once a queue exists
on the broker, it must be bound to an exchange.  Bindings define which 
messages (URL notifications) the program receives.  The root of the topic 
tree is fixed to indicate the protocol version and type of the 
message (but developers can override it with the **topic_prefix**
option.)

So the binding options are:

 - **exchange      <name>         (default: xpublic)** 
 - **topic_prefix  <amqp pattern> (default: varies by component)** 
 - **subtopic      <amqp pattern> (subtopic need to be set)** 

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


Regexp Message Filtering 
------------------------

We have selected our messages through **exchange**, **subtopic** and
perhaps patterned  **subtopic** with AMQP's limited wildcarding.
The broker puts the corresponding messages in our queue.
The component downloads the these messages.

Sarracenia clients implement a the more powerful client side filtering
using regular expression based mechanisms.

- **accept    <regexp pattern> (optional)**
- **reject    <regexp pattern> (optional)**
- **accept_unmatch   <boolean> (default: False)**

The  **accept**  and  **reject**  options use regular expressions (regexp).
The regexp is applied to the the message's URL for a match.

If the message's URL of a file matches a **reject**  pattern, the message
is acknowledged as consumed to the broker and skipped.

One that matches an **accept** pattern is processed by the component.

In many configurations, **accept** and **reject** options are mixed
with the **directory** option.  They then relate accepted messages
to the **directory** value they are specified under.

After all **accept** / **reject**  options are processed, normally
the message acknowledged as consumed and skipped. To override that
default, set **accept_unmatch** to True.   However,  if
no **accept** / **reject** are specified, the program assumes it
should accept all messages and sets **accept_unmatch** to True.

The **accept/reject** are interpreted in order.
Each option is processed orderly from top to bottom.
for example:

sequence #1::

  reject .*\.gif
  accept .*

sequence #2::

  accept .*
  reject .*\.gif


In sequence #1, all files ending in 'gif' are rejected.  In sequence #2, the accept .* (which
accepts everything) is encountered before the reject statement, so the reject has no effect.

It is best practice to use server side filtering to reduce the number of announcements sent
to the component to a small superset of what is relevant, and perform only a fine-tuning with the
client side mechanisms, saving bandwidth and processing for all.


On_message Plugins
------------------

Once a message has gone through the filtering above, the user can run a plugin 
on the message and perform arbitrary processing (in Python 3.)  For example: to do statistics,
rename a product, changing its destination... 

Plugin scripts are more fully explained in the `Plugin Scripts <#plugin-scripts-1>`_ of 
this manual page.

- **on_message    <script_name> (default: msg_log)**

The **on_message** plugin scripts is the very last step in consuming messages.
All plugin scripts return a boolean. If False is returned, the component
acknowledges the message to the broker and does not process it.  If no on_message plugin 
is set, or if the plugin provided returns True, the message is processed by the component.


ROUTING
=======

Sources of data need to indicate the clusters to which they would like data to be delivered.
Data Pumps need to identify themselves, and their neighbors in order to pass data to them.

- **cluster** The name of the local cluster (where data is injected.)

- **cluster_aliases** <alias>,<alias>,...  Alternate names for the cluster.

- **gateway_for** <cluster>,<cluster>,... additional clusters reachable from local pump.

- **to** <cluster>,<cluster>,<cluster>... destination pumps targetted by injectors.

Components which inject data into a network (sr_post, sr_poll, sr_watch) need to set 'to' addresses
for all data injected.  Components which transfer data between pumps, such as sr_sarra and sr_sender, 
interpret *cluster, cluster_aliases*, and *gateway_for*, such that products which are not 
meant for the destination cluster are not transferred.  

The network will not process a message that ::

 1- has no source     (message.headers['source'])
 2- has no origin      (message.headers['from_cluster'])
 3- has no destination (message.headers['to_clusters']) (**to** option on post/watch/poll)
 4- the to_clusters destination list has no match with
    this pump's **cluster,cluster_aliases,gateway_for**  options

.. Important note 1::

  If messages are posted directly from a source,
  the exchange used is 'xs_<brokerSourceUsername>'.
  Such message does not contain a source nor an origin cluster.
  Initial validation of these messages the **source_from_exchange**

  Upon reception, a component will set these values
  in the parent class (here cluster is the value of
  option **cluster** taken from default.conf):

    self.msg.headers['source']       = <brokerUser>
    self.msg.headers['from_cluster'] = cluster


.. note::
   FIXME: all of the above, I'm a bit confused about, explanation seems complicated
   need to rephrase...

DELIVERY 
========

These options set what files will be downloaded, where they will be placed,
and under which name.

- **directory <path>           (default: .)** 
- **flatten   <boolean>        (default: false)** 
- **inflight  <.string>        (default: .tmp)** 
- **mirror    <boolean>        (default: false)** 
- **overwrite <boolean>        (default: true)** 
- **strip     <count>         (default: 0)**
- **kbytes_ps** <count>       (default: 0)**


The  **inflight**  option sets a temporary file name used
during the download so that other programs reading the directory ignore 
them.  The file is renamed to a permanent name when the transfer is complete.
It is usually a suffix applied to file names, but if **inflight**  is set to  **.**,
then it is prefix, to conform with the standard for "hidden" files on unix/linux.

**Directory** sets where to put the files on your server.
Combined with  **accept** / **reject**  options, the user can select the
files of interest and their directories of residence. 

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

Use the option **strip**  set to N  (an integer) to trim the beginnning of
the directory tree.  For example::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   strip     3
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/WGJ/201312141900_WGJ_PRECIP_SNOW.gif, stripping out *radar, PRECIP,* and *GIF*
from the path.

The  **flatten**  option is use to set a separator character. This character
replaces the '/' in the url to create a "flattened" filename from its dd.weather.gc.ca path.  
For example, retrieving the following url with options::

 http://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/12/015/CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

   flatten   -
   directory /mylocaldirectory
   accept    .*model_gem_global.*

results in the creating ::

 /mylocaldirectory/model_gem_global-25km-grib2-lat_lon-12-015-CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2


The  **overwrite**  option, when set, forces overwriting of an existing file even if it 
has the same checksum as the newly advertised version.

.. note::
  FIXME: Is it correct for this to be different for sr_subscribe? why is default not False everywhere?


**kbytes_ps** is greater than 0, the process attempts to respect this delivery 
speed in kilobytes per second... ftp,ftps,or sftp)


LOGS
====

Components write to log files, which by default are found in ~/.cache/sarra/var/log/<component>_<config>_<instance>.log.
at the end of the day, These logs are rotated automatically by the components, and the old log gets a date suffix.
The directory in which the logs are stored can be overridden by the **log** option, and the number of days' logs to keep 
is set by the 'logdays' parameter.  Log files older than **logdays** days are deleted.

- **debug**  setting option debug is identical to use  **loglevel debug**

- **log** the directory to store log files in.  Default value: ~/.cache/sarra/var/log (on Linux) 

- **logdays** the number of days' log files to keep online, assuming a daily rotation.

- **loglevel** the level of logging as expressed by python's logging. 
               possible values are :  critical, error, info, warning, debug.

Note: for **sr-post** only,  option **log** should be a logfile

.. note::
   FIXME:  I don't understand the point of logging a post... it seems like it should always be 'foreground'
   and that it would just write to stderr... it is a one-time thing... confused. what would it log?

   FIXME: We need a verbosity setting. should probably be documented here.  on INFO, the logs are way over the top
   verbose.  Probably need to trim that down. log_level?


INSTANCES
=========

Sometimes one instance of a component and configuration is not enough to process & send all available notifications.  

**instances      <integer>     (default:1)**

The instance option allows launching serveral instances of a component and configuration.
When running sr_sender for example, a number of runtime files that are created.
In the ~/.cache/sarra/sender/configName directory::

  A .sr_sender_configname.state         is created, containing the number instances.
  A .sr_sender_configname_$instance.pid is created, containing the PID  of $instance process.

In directory ~/.cache/sarra/var/log::

  A .sr_sender_configname_$instance.log  is created as a log of $instance process.

The logs can be written in another directory than the default one with option :

**log            <directory logpath>  (default:~/.cache/sarra/var/log)**

.. note::  
  FIXME: indicate windows location also... dot files on windows?


.. Note::

  While the brokers keep the queues available for some time, Queues take resources on 
  brokers, and are cleaned up from time to time.  A queue which is not
  accessed and has too many (implementation defined) files queued will be destroyed.
  Processes which die should be restarted within a reasonable period of time to avoid
  loss of notifications.  A queue which is not accessed for a long (implementation dependent)
  period will be destroyed. 

.. Note::
   FIXME  The last sentence is not really right...sr_audit does track the queues'age... 
          sr_audit acts when a queue gets to the max_queue_size and not running ... nothing more.
          


POSTING OPTIONS
===============

These options are only used when more than one broker needs to be configured for a component,
( such as sr_sarra(8), sr_sender(1), sr_shovel(1), sr_winnow(1).)
These options specify the broker to which messages are output, or "posted."
By default, components publishes the selected consumed message with its 
exchange onto the current cluster, with the feeder account.

The user can overwrite the defaults with options :

- **post_broker    amqp{s}://<user>:<pw>@<post_brokerhost>[:port]/<vhost>**
- **post_exchange   <name>        (default: None)**
- **on_post         <script_name> (optional)**

The post_broker option sets the credential informations to connect to the
output **RabbitMQ** server. The default is the value of the **feeder** option
in default.conf.

The **post_exchange** option sets a new exchange for the selected messages.
The default is to publish under the exchange it was consumed.  
Before a message is published, a user can set to trigger a script.
The option **on_post** would be used to do such a setup. If the script returns
True, the message is published... and False it wont.



RABBITMQ LOGGING
================

For each download, an amqp log message is sent back to the broker.
Should you want to turned them off the option is :

- **log_back <boolean>        (default: true)** 
- **log_daemons <boolean>     (default: false)**
- **log_exchange <log_exchangename> (default: xlog)**

The *log_daemons* option indicates to sr whether the sr_log2source, sr_2xlog, and sr_log2cluster 
component configurations should be included in processing for start, stop, etc...

When a log message is generated, it is sent to the configured *log_exchange*. Administrive 
components log directly to xlog, whereas user components log to their own exchanges.  The 
log_daemons copy the messages to *xlog* after validation.

Administration-Specific Options
===============================

The *feeder* option specifies the account used by default system transfers for components such as 
sr_2xlog, sr_log2source, sr_log2cluster, sr_sarra and sr_sender (when posting).

- **feeder    amqp{s}://<user>:<pw>@<post_brokerhost>[:port]/<vhost>**

- **admin   <name>        (default: None)**

When set, the feeder option will trigger start up of the sr_2xlog, sr_log2source, and sr_log2cluster daemons.
When set, the admin option will cause sr start to start up the sr_audit daemon.

.. note::
  FIXME:: feeder is perhaps an archeological artifact. perhaps should disappear and just use broker
  for this, when run as the admin user.  then the trigger to run all admin daemons would be the presence
  of the admin user in the configuration.

Most users are defined using the *role* option.  

- **role <role> <name>   (no defaults)**

Role:

subscriber

  A subscriber is user that can only subscribe to data and return log messages. Subscribers are
  not permitted to inject data.  Each subscriber has an xs_<user> named exchange on the pump, 
  where if a user is named *Acme*, the corresponding exchange will be *xs_Acme*.  This exchange 
  is where an sr_subscribe process will send it's log messages.

  By convention/default, the *anonymous* user is created on all pumps to permit subscription without
  a specific account.

source

  A user permitted to subscribe or originate data.  A source does not necessarily represent
  one person or type of data, but rather an organization responsible for the data produced.
  So if an organization gathers and makes available ten kinds of data with a single contact
  email or phone number for questions about the data and it's availability, then all of
  those collection activities might use a single 'source' account.

  Each source gets a xs_<user> exchange for injection of data posts, and, similar to a subscriber
  to send log messages about processing and receipt of data. source may also have an xl_<user>
  exchange where, as per log routing configurations, log messages of consumers will be sent.




PLUGIN SCRIPTS
==============

Metpx Sarracenia provides minimum functionality to deal with the most common cases, but provides
flexibility to override those common cases with user plugins scripts, written in python.  
MetPX comes with a variety of scripts which can act as examples.   

Users can place their own scripts in the script sub-directory 
of their config directory tree.

A user script should be placed in the ~/.config/sarra/plugins directory.

There are two varieties of scripts:  do\_* and on\_*.  Do\_* scripts are used 
to implement functions, replacing built-in functionality, for example, to implement 
additional transfer protocols.  

- do_download - to implement additional download protocols.

- do_poll - to implement additional polling protocols and processes.

- do_send - to implement additional sending protocols and processes.


On\_* scripts are used more often. They allow actions to be inserted to augment the default 
processing for various specialized use cases. The scripts are invoked by having a given 
configuration file specify an on_<event> option. The event can be one of:

- on_file -- When the reception of a file has been completed, trigger followup action.

- on_line -- In **sr_poll** a line from the ls on the remote host is read in.

- on_message -- when an sr_post(7) message has been received.  For example, a message has been received 
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




EXAMPLES
========

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



SEE ALSO
========

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
