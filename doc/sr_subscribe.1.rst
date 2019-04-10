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

 **sr_subscribe** foreground|start|stop|restart|reload|sanity|status configfile

 **sr_subscribe** cleanup|declare|edit|setup|disable|enable|list|add|remove configfile


DESCRIPTION
===========

[ `version francaise <fr/sr_subscribe.1.rst>`_ ]

.. contents::

Sr_subscribe is a program to download files from websites or file servers 
that provide `sr_post(7) <sr_post.7.rst>`_ protocol notifications.  Such sites 
publish messages for each file as soon as it is available.  Clients connect to a
*broker* (often the same as the server itself) and subscribe to the notifications.
The *sr_post* notifications provide true push notices for web-accessible folders (WAF),
and are far more efficient than either periodic polling of directories, or ATOM/RSS style 
notifications. Sr_subscribe can be configured to post messages after they are downloaded,
to make them available to consumers for further processing or transfers.

**sr_subscribe** can also be used for purposes other than downloading, (such as for 
supplying to an external program) specifying the -n (*notify_only*, or *no_download*) will
suppress the download behaviour and only post the URL on standard output.  The standard
output can be piped to other processes in classic UNIX text filter style.  

Sr_subscribe is very configurable and is the basis for other components of sarracenia:

 - `sr_report(1) <sr_report.1.rst>`_ - process report messages.
 - `sr_sender(1) <sr_sender.1.rst>`_ - copy messages, only, not files.
 - `sr_winnow(8) <sr_winnow.8.rst>`_ - suppress duplicates.
 - `sr_shovel(8) <sr_shovel.8.rst>`_ - copy messages, only, not files.
 - `sr_sarra(8) <sr_sarra.8.rst>`_ -   Subscribe, Acquire, and Recursival ReAdvertise Ad nauseam.
 
All of these components accept the same options, with the same effects.
There is also `sr_cpump(1) <sr_cpump.1.rst>`_ which is a C version that implements a
subset of the options here, but where they are implemented, they have the same effect.

The **sr_subscribe** command takes two arguments: an action start|stop|restart|reload|status, 
followed by a configuration file. 

When any component is invoked, an operation and a configuration file are specified. The operation is one of:

 - foreground: run a single instance in the foreground logging to stderr
 - restart: stop and then start the configuration.
 - sanity: looks for instances which have crashed or gotten stuck and restarts them.
 - start:  start the configuration running
 - status: check if the configuration is running.
 - stop: stop the configuration from running

Note that the *sanity* check is invoked by heartbeat processing in sr_audit on a regular basis.
The remaining operations manage the resources (exchanges, queues) used by the component on
the rabbitmq server, or manage the configurations.

 - cleanup:       deletes the component's resources on the server.
 - declare:       creates the component's resources on the server.
 - setup:         like declare, additionally does queue bindings.
 - add:           copy to the list of available configurations.
 - list:          list all the configurations available. 
 - list plugins:  list all the plugins available. 
 - edit:          modify an existing configuration.
 - remove:        remove a configuration.
 - disable:       mark a configuration as ineligible to run. 
 - enable:        mark a configuration as eligible to run. 


For example:  *sr_subscribe foreground dd* runs the sr_subscribe component with
the dd configuration as a single foreground instance.

The **foreground** action is used when building a configuration or for debugging.
The **foreground** instance will run regardless of other instances which are currently
running.  Should instances be running, it shares the same message queue with them.
A user stop the **foreground** instance by simply using <ctrl-c> on linux
or use other means to kill the process.

The actions **cleanup**, **declare**, **setup** can be used to manage resources on
the rabbitmq server. The resources are either queues or exchanges. **declare** creates
the resources. **setup** creates and additionally binds the queues.

The **add, remove, list, edit, enable & disable** actions are used to manage the list 
of configurations.  One can see all of the configurations available using the **list**
action.   to view available plugins use **list plugins**.  Using the **edit** option, 
one can work on a particular configuration.  A *disabled* configuration will not be 
started or restarted by the **start**,  
**foreground**, or **restart** actions. It can be used to set aside a configuration
temporarily. 

Documentation
-------------

While manual pages provide an index or reference for all options,
new users will find the guides provide more helpful examples and walk 
throughs and should start with them.

Users:

* `Installation <Install.rst>`_ - initial installation.
* `Subscriber Guide <subscriber.rst>`_ - effective downloading from a pump.
* `Source Guide <source.rst>`_ - effective uploading to a pump
* `Programming Guide <Prog.rst>`_ - Programming custom plugins for workflow integration.

Administrators:

* `Admin Guide <Admin.rst>`_ - Configuration of Pumps
* `Upgrade Guide <UPGRADING.rst>`_ - MUST READ when upgrading pumps.
 
Contributors:

* `Developer Guide <Dev.rst>`_ - contributing to sarracenia development.

Meta:

* `Overview <sarra.rst>`_ - Introduction.
* `Concepts <Concepts.rst>`_ - Concepts and Glossary

There are also other manual pages available here: `See Also`_

Some quick hints are also available when the command line is invoked with 
either the *help* action, or *-help* op **help** to have a component print 
a list of valid options. 


Configurations
--------------

If one has a ready made configuration called *q_f71.conf*, it can be 
added to the list of known ones with::

  sr_subscribe add q_f71.conf

In this case, xvan_f14 is included with examples provided, so *add* finds it in the examples
directory and copies into the active configuration one. 
Each configuration file manages the consumers for a single queue on
the broker. To view the available configurations, use::

  blacklab% sr_subscribe list

  configuration examples: ( /usr/lib/python3/dist-packages/sarra/examples/subscribe ) 
            all.conf     all_but_cap.conf            amis.conf            aqhi.conf             cap.conf      cclean_f91.conf 
      cdnld_f21.conf       cfile_f44.conf        citypage.conf       clean_f90.conf            cmml.conf cscn22_bulletins.conf 
        ftp_f70.conf            gdps.conf         ninjo-a.conf           q_f71.conf           radar.conf            rdps.conf 
           swob.conf           t_f30.conf      u_sftp_f60.conf 

  user plugins: ( /home/peter/.config/sarra/plugins ) 
        destfn_am.py         destfn_nz.py       msg_tarpush.py 

  general: ( /home/peter/.config/sarra ) 
          admin.conf     credentials.conf         default.conf

  user configurations: ( /home/peter/.config/sarra/subscribe )
     cclean_f91.conf       cdnld_f21.conf       cfile_f44.conf       clean_f90.conf         ftp_f70.conf           q_f71.conf 
          t_f30.conf      u_sftp_f60.conf
  blacklab%

one can then modify it using::

  sr_subscribe edit q_f71.conf

(The edit command uses the EDITOR environment variable, if present.)
Once satisfied, one can start the the configuration running::

  sr_subscibe foreground q_f71.conf

What goes into the files? See next section:


Option Syntax
-------------

Options are placed in configuration files, one per line, in the form:

  **option <value>**

For example::

  **debug true**
  **debug**

sets the *debug* option to enable more verbose logging.  If no value is specified,
the value true is implicit, so the above are equivalent.  A second example 
configuration line::

  broker amqps://anonymous@dd.weather.gc.ca

In the above example, *broker* is the option keyword, and the rest of the line is the 
value assigned to the setting. Configuration files are a sequence of settings, one per line. 
Note:

* the files are read from top to bottom, most importantly for *directory*, *strip*, *mirror*,
  and *flatten* options apply to *accept* clauses that occur after them in the file.

* The forward slash (/) as the path separator in Sarracenia configuration files on all 
  operating systems. Use of the backslash character as a path separator (as used in the 
  cmd shell on Windows) may not work properly. When files are read on Windows, the path
  separator is immediately converted to the forward slash, so all pattern matching,
  in accept, reject, strip etc... directives should use forward slashes when a path
  separator is needed.
  
Example::

    directory A
    accept X

Places files matching X in directory A.

vs::
    accept X
    directory A

Places files matching X in the current working directory, and the *directory A* setting 
does nothing in relation to X.

To provide non-functional descriptions of configurations, or comments, use lines that begin with a **#**.

**All options are case sensitive.**  **Debug** is not the same as **debug** or **DEBUG**.
Those are three different options (two of which do not exist and will have no effect,
but should generate an ´unknown option warning´).

Options and command line arguments are equivalent.  Every command line argument
has a corresponding long version starting with '--'.  For example *-u* has the
long form *--url*. One can also specify this option in a configuration file.
To do so, use the long form without the '--', and put its value separated by a space.
The following are all equivalent:

  - **url <url>**
  - **-u <url>**
  - **--url <url>**

Settings are interpreted in order.  Each file is read from top to bottom.
For example:

sequence #1::

  reject .*\.gif
  accept .*


sequence #2::

  accept .*
  reject .*\.gif


.. note::
   FIXME: does this match only files ending in 'gif' or should we add a $ to it?
   will it match something like .gif2 ? is there an assumed .* at the end?


In sequence #1, all files ending in 'gif' are rejected. In sequence #2, the 
accept .* (which accepts everything) is encountered before the reject statement, 
so the reject has no effect.  Some options have global scope, rather than being
interpreted in order.  for thoses cases, a second declaration overrides the first.

Options to be reused in different config files can be grouped in an *include* file:

  - **--include <includeConfigPath>**

The includeConfigPath would normally reside under the same config dir of its
master configs. If a URL is supplied as an includeConfigPATH, then a remote 
configuraiton will be downloaded and cached (used until an update on the server 
is detected.) See `Remote Configurations`_ for details.

Environment variables, and some built-in variables can also be put on the
right hand side to be evaluated, surrounded by ${..} The built-in variables are:
 
 - ${BROKER_USER} - the user name for authenticating to the broker (e.g. anonymous)
 - ${PROGRAM}     - the name of the component (sr_subscribe, sr_shovel, etc...)
 - ${CONFIG}      - the name of the configuration file being run.
 - ${HOSTNAME}    - the hostname running the client.
 - ${RANDID}      - a random id that will be consistent within a single invocation.

Option Order
~~~~~~~~~~~~

When a component is started up, a series of configuration files are read in
the following sequence:

 1. default.conf

 2. admin.conf

 3. <prog>.conf (subscribe.conf, audit.conf, etc...)

 4. <progr>/<config>.conf

Settings in an individual .conf file are read in after the default.conf
file, and so can override defaults. Options specified on
the command line override configuration files.



plugin options
~~~~~~~~~~~~~~

Sarracenia makes extensive use of small python code snippets that customize
processing called *plugins.* Plugins define and use additional settings,
that are usually prefixed with the name of the plugin::

  msg_to_clusters DDI
  msg_to_clusters DD

  on_message msg_to_clusters

A setting 'msg_to_clusters' is needed by the *msg_to_clusters* plugin
referenced in the *on_message*

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

On can also reference environment variables in configuration files,
using the *${ENV}* syntax.  If Sarracenia routines needs to make use
of an environment variable, then they can be set in configuration files::

  declare env HTTP_PROXY=localhost


Choosing an alternate client library 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sarracenia now uses amqp_ module as its default AMQP client library which is provided by the installation.
This library uses AMQP 0-9-1 standard and it replaces amqplib which uses AMQP 0-8. However, if the user
need to use another client library, there is 2 options which are mutually exclusive (they cannot be used together):

.. _amqp: https://pypi.org/project/amqp/

- **use_amqplib [<boolean>]**
- **use_pika [<boolean>]**

In the cases where the user want to enable one option, he will first need to install the module in 
his python environment, whether it's amqplib or pika.

    
LOG FILES
---------

As sr_subscribe usually runs as a daemon (unless invoked in *foreground* mode) 
one normally examines its log file to find out how processing is going.  When only
a single instance is running, one can normally view the log of the running process
like so::

   sr_subscribe log *myconfig*

Where *myconfig* is the name of the running configuration. Log files 
are placed as per the XDG Open Directory Specification. There will be a log file 
for each *instance* (download process) of an sr_subscribe process running the myflow configuration::

   in linux: ~/.cache/sarra/log/sr_subscribe_myflow_01.log

One can override placement on linux by setting the XDG_CACHE_HOME environment variable.


CREDENTIALS
-----------

One normally does not specify passwords in configuration files.  Rather they are placed 
in the credentials file::

   sr_subscribe edit credentials

For every url specified that requires a password, one places 
a matching entry in credentials.conf.
The broker option sets all the credential information to connect to the  **RabbitMQ** server 

- **broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqps://anonymous:anonymous@dd.weather.gc.ca/ )

For all **sarracenia** programs, the confidential parts of credentials are stored
only in ~/.config/sarra/credentials.conf.  This includes the destination and the broker
passwords and settings needed by components.  The format is one entry per line.  Examples:

- **amqp://user1:password1@host/**
- **amqps://user2:password2@host:5671/dev**

- **sftp://user5:password5@host**
- **sftp://user6:password6@host:22  ssh_keyfile=/users/local/.ssh/id_dsa**

- **ftp://user7:password7@host  passive,binary**
- **ftp://user8:password8@host:2121  active,ascii**

- **ftps://user7:De%3Aize@host  passive,binary,tls**
- **ftps://user8:%2fdot8@host:2121  active,ascii,tls,prot_p**


In other configuration files or on the command line, the url simply lacks the
password or key specification.  The url given in the other files is looked
up in credentials.conf.

Note::
 SFTP credentials are optional, in that sarracenia will look in the .ssh directory
 and use the normal SSH credentials found there.

 These strings are URL encoded, so if an account has a password with a special 
 character, its URL encoded equivalent can be supplied.  In the last example above, 
 **%2f** means that the actual password isi: **/dot8**
 The next to last password is:  **De:olonize**. ( %3a being the url encoded value for a colon character. )


CONSUMER
========

Most Metpx Sarracenia components loop on reception and consumption of sarracenia 
AMQP messages.  Usually, the messages of interest are `sr_post(7) <sr_post.7.rst>`_ 
messages, announcing the availability of a file by publishing its URL ( or a part 
of a file ), but there are also `sr_report(7) <sr_report.7.rst>`_ messages which 
can be processed using the same tools. AMQP messages are published to an exchange 
on a broker (AMQP server). The exchange delivers messages to queues. To receive 
messages, one must provide the credentials to connect to the broker (AMQP message 
pump). Once connected, a consumer needs to create a queue to hold pending messages.
The consumer must then bind the queue to one or more exchanges so that they put 
messages in its queue.

Once the bindings are set, the program can receive messages. When a message is received,
further filtering is possible using regular expressions onto the AMQP messages.
After a message passes this selection process, and other internal validation, the
component can run an **on_message** plugin script to perform additional message 
processing. If this plugin returns False, the message is discarded. If True, 
processing continues.

The following sections explains all the options to set this "consuming" part of
sarracenia programs.



Setting the Broker 
------------------

**broker amqp{s}://<user>:<password>@<brokerhost>[:port]/<vhost>**

An AMQP URI is used to configure a connection to a message pump (aka AMQP broker.)
Some sarracenia components set a reasonable default for that option. 
You provide the normal user,host,port of connections. In most configuration files,
the password is missing. The password is normally only included in the credentials.conf file.

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

Once connected to an AMQP broker, the user needs to create a queue.

Setting the queue on broker :

- **queue         <name>         (default: q_<brokerUser>.<programName>.<configName>)**
- **durable       <boolean>      (default: False)**
- **expire        <duration>      (default: 5m  == five minutes. RECOMMEND OVERRIDING)**
- **message-ttl   <duration>      (default: None)**
- **prefetch      <N>            (default: 1)**
- **reset         <boolean>      (default: False)**
- **restore       <boolean>      (default: False)**
- **restore_to_queue <queuename> (default: None)**
- **save          <boolean>      (default: False)**


Usually components guess reasonable defaults for all these values
and users do not need to set them.  For less usual cases, the user
may need to override the defaults.  The queue is where the notifications
are held on the server for each subscriber.

[ queue|queue_name|qn <name>]
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, components create a queue name that should be unique. The 
default queue_name components create follows the following convention: 

   **q_<brokerUser>.<programName>.<configName>.<random>.<random>** 

Where:

* *brokerUser* is the username used to connect to the broker (often: *anonymous* )

* *programName* is the component using the queue (e.g. *sr_subscribe* ),

* *configName* is the configuration file used to tune component behaviour.

* *random* is just a series of characters chosen to avoid clashes from multiple
  people using the same configurations

Users can override the default provided that it starts with **q_<brokerUser>**.

When multiple instances are used, they will all use the same queue, for trivial
multi-tasking. If multiple computers have a shared home file system, then the
queue_name is written to: 

 ~/.cache/sarra/<programName>/<configName>/<programName>_<configName>_<brokerUser>.qname

Instances started on any node with access to the same shared file will use the
same queue. Some may want use the *queue_name* option as a more explicit method
of sharing work across multiple nodes.



durable <boolean> (default: False)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **durable** option, if set to True, means writes the queue
on disk if the broker is restarted.

expire <duration> (default: 5m  == five minutes. RECOMMEND OVERRIDING)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **expire**  option is expressed as a duration... it sets how long should live
a queue without connections. 

A raw integer is expressed in seconds, if the suffix m,h,d,w
are used, then the interval is in minutes, hours, days, or weeks. After the queue expires,
the contents are dropped, and so gaps in the download data flow can arise.  A value of
1d (day) or 1w (week) can be appropriate to avoid data loss. It depends on how long
the subscriber is expected to shutdown, and not suffer data loss.

The **expire** setting must be overridden for operational use. 
The default is set low because it defines how long resources on the broker will be assigned,
and in early use (when default was 1 week) brokers would often get overloaded with very 
long queues for left-over experiments.  


message-ttl <duration>  (default: None)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **message-ttl**  option set the time a message can live in the queue.
Past that time, the message is taken out of the queue by the broker.

prefetch <N> (default: 1)
~~~~~~~~~~~~~~~~~~~~~~~~~

The **prefetch** option sets the number of messages to fetch at one time.
When multiple instances are running and prefetch is 4, each instance will obtain up to four
messages at a time.  To minimize the number of messages lost if an instance dies and have
optimal load sharing, the prefetch should be set as low as possible.  However, over long
haul links, it is necessary to raise this number, to hide round-trip latency, so a setting
of 10 or more may be needed.

reset <boolean> (default: False)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When **reset** is set, and a component is (re)started, its queue is
deleted (if it already exists) and recreated according to the component's
queue options.  This is when a broker option is modified, as the broker will
refuse access to a queue declared with options that differ from what was
set at creation.  It can also be used to discard a queue quickly when a receiver 
has been shut down for a long period. If duplicate suppression is active, then
the reception cache is also discarded.

The AMQP protocol defines other queue options which are not exposed
via sarracenia, because sarracenia itself picks appropriate values.

save/restore
~~~~~~~~~~~~

The **save** option is used to read messages from the queue and write them
to a local file, saving them for future processing, rather than processing
them immediately.  See the `Sender Destination Unavailable`_ section for more details.
The **restore** option implements the reverse function, reading from the file
for processing.  

If **restore_to_queue** is specified, then rather than triggering local
processing, the messages restored are posted to a temporary exchange 
bound to the given queue.  For an example, see `Shovel Save/Restore`_ 


AMQP QUEUE BINDINGS
-------------------

Once one has a queue, it must be bound to an exchange.
Users almost always need to set these options. Once a queue exists
on the broker, it must be bound to an exchange. Bindings define which
messages (URL notifications) the program receives. The root of the topic
tree is fixed to indicate the protocol version and type of the
message (but developers can override it with the **topic_prefix**
option.)

These options define which messages (URL notifications) the program receives:

 - **exchange      <name>         (default: xpublic)** 
 - **exchange_suffix      <name>  (default: None)** 
 - **topic_prefix  <amqp pattern> (default: v02.post -- developer option)** 
 - **subtopic      <amqp pattern> (no default, must appear after exchange)** 

exchange <name> (default: xpublic) and exchange_suffix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The convention on data pumps is to use the *xpublic* exchange. Users can establish
private data flow for their own processing. Users can declare their own exchanges
that always begin with *xs_<username>*, so to save having to specify that each
time, one can just set *exchange_suffix kk* which will result in the exchange
being set to *xs_<username>_kk* (overriding the *xpublic* default). 
These settings must appear in the configuration file before the corresponding 
*topic_prefix* and *subtopic* settings.

subtopic <amqp pattern> (subtopic need to be set)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Within an exchange's postings, the subtopic setting narrows the product selection.
To give a correct value to the subtopic,
one has the choice of filtering using **subtopic** with only AMQP's limited wildcarding and
length limited to 255 encoded bytes, or the more powerful regular expression 
based  **accept/reject**  mechanisms described below. The difference being that the 
AMQP filtering is applied by the broker itself, saving the notices from being delivered 
to the client at all. The  **accept/reject**  patterns apply to messages sent by the 
broker to the subscriber. In other words,  **accept/reject**  are client side filters, 
whereas **subtopic** is server side filtering.  

It is best practice to use server side filtering to reduce the number of announcements sent
to the client to a small superset of what is relevant, and perform only a fine-tuning with the 
client side mechanisms, saving bandwidth and processing for all.

topic_prefix is primarily of interest during protocol version transitions, 
where one wishes to specify a non-default protocol version of messages to 
subscribe to. 

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
       *                matches a single directory name 
       #                matches any remaining tree of directories.

note:
  When directories have these wild-cards, or spaces in their names, they 
  will be URL-encoded ( '#' becomes %23 )
  When directories have periods in their name, this will change
  the topic hierarchy.

  FIXME: 
      hash marks are URL substituted, but did not see code for other values.
      Review whether asterisks in directory names in topics should be URL-encoded.
      Review whether periods in directory names in topics should be URL-encoded.
 
One can use multiple bindings to multiple exchanges as follows::

  exchange A
  subtopic directory1.*.directory2.#

  exchange B
  subtopic *.directory4.#

Will declare two separate bindings to two different exchanges, and two different file trees.



Client-side Filtering
---------------------

We have selected our messages through **exchange**, **subtopic** and
perhaps patterned  **subtopic** with AMQP's limited wildcarding which
is all done by the broker (server-side). The broker puts the 
corresponding messages in our queue. The subscribed component 
downloads these messages.  Once the message is downloaded, Sarracenia 
clients apply more flexible client side filtering using regular expressions.

Brief Introduction to Regular Expressions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Regular expressions are a very powerful way of expressing pattern matches. 
They provide extreme flexibility, but in these examples we will only use a
very trivial subset: The . is a wildcard matching any single character. If it
is followed by an occurrence count, it indicates how many letters will match
the pattern. The * (asterisk) character, means any number of occurrences.
So:

 - .* means any sequence of characters of any length. In other words, match anything.
 - cap.* means any sequence of characters that starts with cap.
 - .*CAP.* means any sequence of characters with CAP somewhere in it. 
 - .*cap means any sequence of characters that ends with CAP.  In the case where multiple portions of the string could match, the longest one is selected.
 - .*?cap same as above, but *non-greedy*, meaning the shortest match is chosen.

Please consult various internet resources for more information on the full
variety of matching possible with regular expressions:

 - https://docs.python.org/3/library/re.html
 - https://en.wikipedia.org/wiki/Regular_expression
 - http://www.regular-expressions.info/ 


accept, reject and accept_unmatch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **accept    <regexp pattern> (optional)**
- **reject    <regexp pattern> (optional)**
- **accept_unmatch   <boolean> (default: False)**

The  **accept**  and  **reject**  options process regular expressions (regexp).
The regexp is applied to the the message's URL for a match.

If the message's URL of a file matches a **reject**  pattern, the message
is acknowledged as consumed to the broker and skipped.

One that matches an **accept** pattern is processed by the component.

In many configurations, **accept** and **reject** options are mixed
with the **directory** option.  They then relate accepted messages
to the **directory** value they are specified under.

After all **accept** / **reject**  options are processed, normally
the message is acknowledged as consumed and skipped. To override that
default, set **accept_unmatch** to True. The **accept/reject** 
settings are interpreted in order. Each option is processed orderly 
from top to bottom. For example:

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
client side mechanisms, saving bandwidth and processing for all. More details on how
to apply the directives follow:


DELIVERY SPECIFICATIONS
-----------------------

These options set what files the user wants and where it will be placed,
and under which name.

- **accept    <regexp pattern> (must be set)** 
- **accept_unmatch   <boolean> (default: off)**
- **attempts     <count>          (default: 3)**
- **batch     <count>          (default: 100)**
- **default_mode     <octalint>       (default: 0 - umask)**
- **default_dir_mode <octalint>       (default: 0755)**
- **delete    <boolean>>       (default: off)**
- **directory <path>           (default: .)** 
- **discard   <boolean>        (default: off)**
- **base_dir <path>       (default: /)**
- **flatten   <string>         (default: '/')** 
- **heartbeat <count>                 (default: 300 seconds)**
- **inline   <boolean>         (default: False)**
- **inline_max   <counts>         (default: 1024)**
- **inplace       <boolean>        (default: On)**
- **kbytes_ps <count>               (default: 0)**
- **inflight  <string>         (default: .tmp or NONE if post_broker set)** 
- **mirror    <boolean>        (default: off)** 
- **no_download|notify_only    <boolean>        (default: off)** 
- **outlet    post|json|url    (default: post)** 
- **overwrite <boolean>        (default: off)** 
- **preserve_mode <boolead>  (default: on)**
- **preserve_time <boolead>  (default: on)**
- **reject    <regexp pattern> (optional)** 
- **retry    <boolean>         (default: On)** 
- **retry_ttl    <duration>         (default: same as expire)** 
- **source_from_exchange  <boolean> (default: off)**
- **strip     <count|regexp>   (default: 0)**
- **suppress_duplicates   <off|on|999[smhdw]>     (default: off)**
- **suppress_duplicates_basis   <data|name|path>     (default: path)**
- **timeout     <float>         (default: 0)**


attempts <count> (default: 3)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **attempts** option indicates how many times to 
attempt downloading the data before giving up.  The default of 3 should be appropriate 
in most cases.  When the **retry** option is false, the file is then dropped immediately.

When The **retry** option is set (default), a failure to download after prescribed number
of **attempts** (or send, in a sender) will cause the message to be added to a queue file 
for later retry.  When there are no messages ready to consume from the AMQP queue, 
the retry queue will be queried.

retry_ttl <duration> (default: same as expire)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **retry_ttl** (retry time to live) option indicates how long to keep trying to send 
a file before it is aged out of a the queue.  Default is two days.  If a file has not 
been transferred after two days of attempts, it is discarded.

timeout <float> (default: 0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **timeout** option, sets the number of seconds to wait before aborting a
connection or download transfer (applied per buffer during transfer).

inflight <string> (default: .tmp or NONE if post_broker set)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **inflight**  option sets how to ignore files when they are being transferred
or (in mid-flight betweeen two systems). Incorrect setting of this option causes
unreliable transfers, and care must be taken.  See `Delivery Completion (inflight)`_ for more details.

The value can be a file name suffix, which is appended to create a temporary name during 
the transfer.  If **inflight**  is set to **.**, then it is a prefix, to conform with 
the standard for "hidden" files on unix/linux.  
If **inflight**  ends in / (example: *tmp/* ), then it is a prefix, and specifies a 
sub-directory of the destination into which the file should be written while in flight. 

Whether a prefix or suffix is specified, when the transfer is 
complete, the file is renamed to its permanent name to allow further processing.

The  **inflight**  option can also be specified as a time interval, for example, 
10 for 10 seconds.  When set to a time interval, a reader of a file ensures that 
it waits until the file has not been modified in that interval. So a file will 
not be processed until it has stayed the same for at least 10 seconds. 

Lastly, **inflight** can be set to *NONE*, which case the file is written directly
with the final name, where the recipient will wait to receive a post notifying it
of the file's arrival.  This is the fastest, lowest overhead option when it is available.
It is also the default when a *post_broker* is given, indicating that some
other process is to be notified after delivery.

delete <boolean> (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When the **delete** option is set, after a download has completed successfully, the subscriber
will delete the file at the upstream source.  Default is false.

batch <count> (default: 100)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **batch** option is used to indicate how many files should be transferred 
over a connection, before it is torn down, and re-established.  On very low 
volume transfers, where timeouts can occur between transfers, this should be
lowered to 1.  For most usual situations the default is fine. For higher volume
cases, one could raise it to reduce transfer overhead. It is only used for file
transfer protocols, not HTTP ones at the moment.

directory <path> (default: .)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *directory* option defines where to put the files on your server.
Combined with  **accept** / **reject**  options, the user can select the
files of interest and their directories of residence (see the  **mirror**
option for more directory settings).

The  **accept**  and  **reject**  options use regular expressions (regexp) to match URL.
These options are processed sequentially. 
The URL of a file that matches a  **reject**  pattern is never downloaded.
One that matches an  **accept**  pattern is downloaded into the directory
declared by the closest  **directory**  option above the matching  **accept** option.
**accept_unmatch** is used to decide what to do when no reject or accept clauses matched.

::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*

mirror <boolean> (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
mirror settings can be changed between directory options.

strip <count|regexp> (default: 0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can modify the relative mirrored directories with the **strip** option. 
If set to N  (an integer) the first 'N' directories from the relative path 
are removed. For example::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   strip     3
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/WGJ/201312141900_WGJ_PRECIP_SNOW.gif
when a regexp is provide in place of a number, it indicates a pattern to be removed
from the relative path.  For example if::

   strip  .*?GIF/

Will also result in the file being placed the same location. 
Note that strip settings can be changed between directory options.

NOTE::
    with **strip**, use of **?** modifier (to prevent regular expression *greediness* ) is often helpful. 
    It ensures the shortest match is used.

    For example, given a file name:  radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.GIF
    The expression:  .*?GIF   matches: radar/PRECIP/GIF
    whereas the expression: .*GIF matches the entire name.

flatten <string> (default: '/')
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **flatten**  option is use to set a separator character. The default value ( '/' )
nullifies the effect of this option.  This character replaces the '/' in the url 
directory and create a "flatten" filename from its dd.weather.gc.ca path.  
For example retrieving the following url, with options::

 http://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/12/015/CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

   flatten   -
   directory /mylocaldirectory
   accept    .*model_gem_global.*

would result in the creation of the filepath::

 /mylocaldirectory/model_gem_global-25km-grib2-lat_lon-12-015-CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

One can also specify variable substitutions to be performed on arguments to the directory 
option, with the use of *${..}* notation::

   SOURCE   - the amqp user that injected data (taken from the message.)
   BD       - the base directory
   PBD      - the post base dir
   YYYYMMDD - the current daily timestamp.
   HH       - the current hourly timestamp.
   *var*    - any environment variable.

The YYYYMMDD and HH time stamps refer to the time at which the data is processed by
the component, it is not decoded or derived from the content of the files delivered.
All date/times in Sarracenia are in UTC.

Refer to *source_from_exchange* for a common example of usage.  Note that any sarracenia
built-in value takes precedence over a variable of the same name in the environment.
Note that flatten settings can be changed between directory options.

base_dir <path> (default: /)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**base_dir** supplies the directory path that, when combined with the relative
one in the selected notification gives the absolute path of the file to be sent.
The default is None which means that the path in the notification is the absolute one.

**FIXME**::
    cannot explain this... do not know what it is myself. This is taken from sender.
    in a subscriber, if it is set... will it download? or will it assume it is local?
    in a sender.

inline <boolean> (default: False)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When posting messages, The **inline** option is used to have the file content
included in the post. This can be efficient when sending small files over high
latency links, a number of round trips can be saved by avoiding the retrieval
of the data using the URL.  One should only inline relatively small files,
so when **inline** is active, only files smaller than **in_line_max** bytes
(default: 1024) will actually have their content included in the post messages.


inplace <boolean> (default: On)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Large files may be sent as a series of parts, rather than all at once.
When downloading, if **inplace** is true, these parts will be appended to the file 
in an orderly fashion. Each part, after it is inserted in the file, is announced to subscribers.
This can be set to false for some deployments of sarracenia where one pump will 
only ever see a few parts, and not the entirety, of multi-part files. 

The **inplace** option defaults to True. 
Depending of **inplace** and if the message was a part, the path can
change again (adding a part suffix if necessary).

outlet post|json|url (default: post)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **outlet** option is used to allow writing of posts to file instead of
posting to a broker. The valid argument values are:

**post:**

  post messages to an post_exchange

  **post_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**
  **post_exchange     <name>         (MANDATORY)**
  **post_topic_prefix <string>       (default: "v02.post")**
  **on_post           <script>       (default: None)**

  The **post_broker** defaults to the input broker if not provided.
  Just set it to another broker if you want to send the notifications
  elsewhere.

  The **post_exchange** must be set by the user. This is the exchange under
  which the notifications will be posted.

**json:**

  write each message to standard output, one per line in the same json format used for
  queue save/restore by the python implementation.

**url:**

  just output the retrieval URL to standard output.

FIXME: The **outlet** option came from the C implementation ( *sr_cpump*  ) and it has not
been used much in the python implementation. 

overwrite <boolean> (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **overwrite**  option,if set to false, avoid unnecessary downloads under these conditions :

1- the file to be downloaded is already on the user's file system at the right place and

2- the checksum of the amqp message matched the one of the file.

The default is False. 

discard <boolean> (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The  **discard**  option,if set to true, deletes the file once downloaded. This option can be
usefull when debugging or testing a configuration.

source_from_exchange <boolean> (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **source_from_exchange** option is mainly for use by administrators.
If messages received are posted directly from a source, the exchange used 
is 'xs_<brokerSourceUsername>'. Such messages could be missing *source* and *from_cluster* 
headings, or a malicious user may set the values incorrectly.
To protect against both problems, administrators should set the **source_from_exchange** option.

When the option is set, values in the message for the *source* and *from_cluster* headers will then be overridden::

  self.msg.headers['source']       = <brokerUser>
  self.msg.headers['from_cluster'] = cluster

replacing any values present in the message. This setting should always be used when ingesting data from a
user exchange. These fields are used to return reports to the origin of injected data.
It is commonly combined with::

       *mirror true*
       *source_from_exchange true*
       *directory ${PBD}/${YYYYMMDD}/${SOURCE}*
  
To have data arrive in the standard format tree.

heartbeat <count> (default: 300 seconds)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **heartbeat** option sets how often to execute periodic processing as determined by 
the list of on_heartbeat plugins. By default, it prints a log message every heartbeat.

suppress_duplicates <off|on|999[smhdw]> (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When **suppress_duplicates** (also **cache** ) is set to a non-zero time interval, each new message
is compared against ones received within that interval, to see if it is a duplicate. 
Duplicates are not processed further. What is a duplicate? A file with the same name (including 
parts header) and checksum. Every *hearbeat* interval, a cleanup process looks for files in the 
cache that have not been referenced in **cache** seconds, and deletes them, in order to keep 
the cache size limited. Different settings are appropriate for different use cases.

A raw integer interval is in seconds, if the suffix m,h,d, or w are used, then the interval 
is in minutes, hours, days, or weeks. After the interval expires the contents are 
dropped, so duplicates separated by a large enough interval will get through.
A value of 1d (day) or 1w (week) can be appropriate. 

**Use of the cache is incompatible with the default *parts 0* strategy**, one must specify an 
alternate strategy.  One must use either a fixed blocksize, or always never partition files. 
One must avoid the dynamic algorithm that will change the partition size used as a file grows.

**Note that the duplicate suppresion store is local to each instance**. When N 
instances share a queue, the first time a posting is received, it could be 
picked by one instance, and if a duplicate one is received it would likely 
be picked up by another instance. **For effective duplicate suppression with instances**, 
one must **deploy two layers of subscribers**. Use 
a **first layer of subscribers (sr_shovels)** with duplicate suppression turned 
off and output with *post_exchange_split*, which route posts by checksum to 
a **second layer of subscibers (sr_winnow) whose duplicate suppression caches are active.**
  
suppress_duplicates_basis <data|name|path> (default: path)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A keyword option (alternative: *cache_basis* ) to identify which files are compared for 
duplicate suppression purposes. Normally, the duplicate suppression uses the entire path
to identify files which have not changed. This allows for files with identical 
content to be posted in different directories and not be suppressed. In some
cases, suppression of identical files should be done regardless of where in 
the tree the file resides.  Set 'name' for files of identical name, but in
different directories to be considered duplicates. Set to 'data' for any file, 
regardless of name, to be considered a duplicate if the checksum matches.


kbytes_ps <count> (default: 0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**kbytes_ps** is greater than 0, the process attempts to respect this delivery
speed in kilobytes per second... ftp,ftps,or sftp)

**FIXME**: kbytes_ps... only implemented by sender? or subscriber as well, data only, or messages also?

preserve_time (default: on)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

On unix-like systems, when the *ls* commend or a file browser shows modification or 
access times, it is a display of the posix *st_atime*, and *st_ctime* elements of a 
struct struct returned by stat(2) call.  When *preserve_time* is on, headers
reflecting these values in the messages are used to restore the access and modification 
times respectively on the subscriber system. To document delay in file reception,
this option can be turned off, and then file times on source and destination compared.

When set in a posting component, it has the effect of eliding the *atime* and *mtime* 
headers from the messages.

default_mode, default_dir_mode, preserve_mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Permission bits on the destination files written are controlled by the *preserve_mode* directives.
*preserve_modes* will apply the mode permissions posted by the source of the file.
If no source mode is available, the *default_mode* will be applied to files, and the
*default_dir_mode* will be applied to directories. If no default is specified,
then the operating system  defaults (on linux, controlled by umask settings)
will determine file permissions. (Note that the *chmod* option is interpreted as a synonym
for *default_mode*, and *chmod_dir* is a synonym for *default_dir_mode*).

recompute_chksum <boolean> (Always on now)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

recompute_chksum option has been removed in 2.19.03b2. Recomputing will occur
whenever appropriate without the need for a setting.

xattr_disable (default: off)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, on receipt of files, the mtime and checksum are written to a file's
extended attributes (on unix/linux/mac) or to alternate data stream called *sr_.json*
(on windows on NTFS.) This can save re-reading the file to re-calculate the checksum.
Some use cases may not want files to have Alternate Data Streams or extended 
attributes to be used.

Delivery Completion (inflight)
------------------------------

Failing to properly set file completion protocols is a common source of intermittent and
difficult-to-diagnose file transfer issues. For reliable file transfers, it is 
critical that both the sender and receiver agree on how to represent a file that isn't complete.
The *inflight* option (meaning a file is *in flight* between the sender and the receiver) supports
many protocols appropriate for different situations:

+--------------------------------------------------------------------------------------------+
|                                                                                            |
|               Delivery Completion Protocols (in Order of Preference)                       |
|                                                                                            |
+-------------+---------------------------------------+--------------------------------------+
| Method      | Description                           | Application                          |
+=============+=======================================+======================================+
|             |File sent with right name.             |Sending to Sarracenia, and            |
|   NONE      |Send `sr_post(7) <sr_post.7.rst>`_     |post only when file is complete       |
|             |by AMQP after file is complete.        |                                      |
|             |                                       |(Best when available)                 |
|             | - fewer round trips (no renames)      | - Default on sr_sarra.               |
|             | - least overhead / highest speed      | - Default on sr_subscribe and sender |
|             |                                       |   when post_broker is set.           |
+-------------+---------------------------------------+--------------------------------------+
|             |Files transferred with a *.tmp* suffix.|sending to most other systems         |
| .tmp        |When complete, renamed without suffix. |(.tmp support built-in)               |
| (Suffix)    |Actual suffix is settable.             |Use to send to Sundew                 |
|             |                                       |                                      |
|             | - requires extra round trips for      |(usually a good choice)               |
|             |   rename (a little slower)            | - default when no post broker set    |
+-------------+---------------------------------------+--------------------------------------+
|             |Files transferred to a subdir.         |sending to some other systems         |
| tmp/        |When complete, renamed to parent dir.  |                                      |
| (subdir)    |Actual subdir is settable.             |                                      |
|             |                                       |                                      |
|             |same performance as Suffix method.     |                                      |
+-------------+---------------------------------------+--------------------------------------+
|             |Use Linux convention to *hide* files.  |Sending to systems that               |
| .           |Prefix names with '.'                  |do not support suffix.                |
| (Prefix)    |that need that. (compatibility)        |                                      |
|             |same performance as Suffix method.     |                                      |
+-------------+---------------------------------------+--------------------------------------+
|             |Minimum age (modification time)        |Last choice                           |
|  number     |of the file before it is considered    |guaranteed delay added                |
|  (mtime)    |complete.                              |                                      |
|             |                                       |Receiving from uncooperative          |
|             |Adds delay in every transfer.          |sources.                              |
|             |Vulnerable to network failures.        |                                      |
|             |Vulnerable to clock skew.              |(ok choice with PDS)                  |
+-------------+---------------------------------------+--------------------------------------+

By default ( when no *inflight* option is given ), if the post_broker is set, then a value of NONE
is used because it is assumed that it is delivering to another broker. If no post_broker
is set, the value of '.tmp' is assumed as the best option.

NOTES:
 
  On versions of sr_sender prior to 2.18, the default was NONE, but was documented as '.tmp'
  To ensure compatibility with later versions, it is likely better to explicitly write
  the *inflight* setting.
 
  *inflight* was renamed from the old *lock* option in January 2017. For compatibility with
  older versions, can use *lock*, but name is deprecated.
  
  The old *PDS* software (which predates MetPX Sundew) only supports FTP. The completion protocol 
  used by *PDS* was to send the file with permission 000 initially, and then chmod it to a 
  readable file. This cannot be implemented with SFTP protocol, and is not supported at all
  by Sarracenia.


Frequent Configuration Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Setting NONE when sending to Sundew.**

   The proper setting here is '.tmp'.  Without it, almost all files will get through correctly,
   but incomplete files will occasionally picked up by Sundew.  

**Using mtime method to receive from Sundew or Sarracenia:**

   Using mtime is last resort. This approach injects delay and should only be used when one 
   has no influence to have the other end of the transfer use a better method. 
 
   mtime is vulnerable to systems whose clocks differ (causing incomplete files to be picked up.)

   mtime is vulnerable to slow transfers, where incomplete files can be picked up because of a 
   networking issue interrupting or delaying transfers. 

   Sources may not to include mtime data in their posts ( *preserve_time* option on post.)


**Setting NONE when delivering to non-Sarracenia destination.**

   NONE is to be used when there is some other means to figure out if a file is delivered.
   For example, when sending to another pump, the sender will post the announcement to 
   the destination after the file is complete, so there is no danger of it being 
   picked up early.

   When used inappropriately, there will occasionally be incomplete files delivered.


On Windows
==========

The python tools are ubiquitously installed with the operating system on Linux,
and installation methods are somewhat more consistent there.  On Windows,
there is a wide variety of methods of installation, stemming from the
variety of python distributions available. The various methods conflict, to the
extent that using the .exe files, as one would expect using winpython, does not
work at all when installed using Anaconda. 

A setting is provided *windows_run* to allow selection. the choices are:

* exe - run sr_subscribe.exe as installed by pip (what one would expect to start)

* pyw - run the pythonw.exe executable with sr_subscribe.py (or sr_subscribe-script.py) 
  as the argument. (sometimes needed to have the component continue to run
  after calling process is terminated.

* py - run the python.exe executable with sr_subscribe.py (or sr_subscribe-script.py) 
  as the argument. (sometimes also works.)



PERIODIC PROCESSING
===================

Most processing occurs on receipt of a message, but there is some periodic maintenance
work that happens every *heartbeat* (default is 5 minutes.)  Evey heartbeat, all of the
configured *on_heartbeat* plugins are run. By default there are three present:

 * hb_log - prints "heartbeat" in the log.
 * hb_cache - ages out old entries in the cache, to minimize its size.
 * hb_memory - checks the process memory usage, and restart if too big.
 * hb_pulse - confirms that connectivity with brokers is still good. Restores if needed.
 * hb_sanity - runs sanity check.

The log will contain messages from all three plugins every heartbeat interval, and
if additional periodic processing is needed, the user can configure addition
plugins to run with the *on_heartbeat* option. 

sanity_log_dead <interval> (default: 1.5*heartbeat)
---------------------------------------------------

The **sanity_log_dead** option sets how long to consider too long before restarting
a component.

suppress_duplicates <off|on|999> (default: off)
-----------------------------------------------

The cleanup of expired elements in the duplicate suppression store happens at
each heartbeat.


ERROR RECOVERY
==============

The tools are meant to work well unattended, and so when transient errors occur, they do
their best to recover elegantly.  There are timeouts on all operations, and when a failure
is detected, the problem is noted for retry.  Errors can happen at many times:
 
 * Establishing a connection to the broker.
 * losing a connection to the broker
 * establishing a connection to the file server for a file (for download or upload.)
 * losing a connection to the server.
 * during data transfer.
 
Initially, the programs try to download (or send) a file a fixed number (*attempts*, default: 3) times.
If all three attempts to process the file are unsuccessful, then the file is placed in an instance's
retry file. The program then continues processing of new items. When there are no new items to
process, the program looks for a file to process in the retry queue. It then checks if the file
is so old that it is beyond the *retry_expire* (default: 2 days). If the file is not expired, then
it triggers a new round of attempts at processing the file. If the attempts fail, it goes back
on the retry queue.

This algorithm ensures that programs do not get stuck on a single bad product that prevents
the rest of the queue from being processed, and allows for reasonable, gradual recovery of 
service, allowing fresh data to flow preferentially, and sending old data opportunistically
when there are gaps.

While fast processing of good data is very desirable, it is important to slow down when errors
start occurring. Often errors are load related, and retrying quickly will just make it worse.
Sarracenia uses exponential back-off in many points to avoid overloading a server when there
are errors. The back-off can accumulate to the point where retries could be separated by a minute
or two. Once the server begins responding normally again, the programs will return to normal
processing speed.


EXAMPLES
========

Here is a short complete example configuration file:: 

  broker amqps://dd.weather.gc.ca/

  subtopic model_gem_global.25km.grib2.#
  accept .*

This above file will connect to the dd.weather.gc.ca broker, connecting as
anonymous with password anonymous (defaults) to obtain announcements about
files in the http://dd.weather.gc.ca/model_gem_global/25km/grib2 directory.
All files which arrive in that directory or below it will be downloaded 
into the current directory (or just printed to standard output if -n option 
was specified.) 

A variety of example configuration files are available here:

 `https://github.com/MetPX/sarracenia/tree/master/sarra/examples <https://github.com/MetPX/sarracenia/tree/master/sarra/examples>`_


NAMING EXCHANGES AND QUEUES
===========================

While in most common cases, a good value is generated by the application, in some cases
there may be a need to override those choices with an explicit user specification.
To do that, one needs to be aware of the rules for naming queues:

1. queue names start with q\_
2. this is followed by <amqpUserName> (the owner/user of the queue's broker username)
3. followed by a second underscore ( _ )
4. followed by a string of the user's choice.

The total length of the queue name is limited to 255 bytes of UTF-8 characters.

The same applies for exchanges.  The rules for those are:

1. Exchange names start with x
2. Exchanges that end in *public* are accessible (for reading) by any authenticated user.
3. Users are permitted to create exchanges with the pattern:  xs_<amqpUserName>_<whatever> such exchanges can be written to only by that user. 
4. The system (sr_audit or administrators) create the xr_<amqpUserName> exchange as a place to send reports for a given user. It is only readable by that user.
5. Administrative users (admin or feeder roles) can post or subscribe anywhere.

For example, xpublic does not have xs\_ and a username pattern, so it can only be posted to by admin or feeder users.
Since it ends in public, any user can bind to it to subscribe to messages posted.
Users can create exchanges such as xs_<amqpUserName>_public which can be written to by that user (by rule 3), 
and read by others (by rule 2.) A description of the conventional flow of messages through exchanges on a pump.  
Subscribers usually bind to the xpublic exchange to get the main data feed. This is the default in sr_subscribe.

Another example, a user named Alice will have at least two exchanges:

  - xs_Alice the exhange where Alice posts her file notifications and report messages (via many tools).
  - xr_Alice the exchange where Alice reads her report messages from (via sr_report).
  - Alice can create a new exchange by just posting to it (with sr_post or sr_cpost) if it meets the naming rules.

Usually an sr_sarra run by a pump administrator will read from an exchange such as xs_Alice_mydata, 
retrieve the data corresponding to Alice´s *post* message, and make it available on the pump, 
by re-announcing it on the xpublic exchange.




QUEUES and MULTIPLE STREAMS
===========================

When executed,  **sr_subscribe**  chooses a queue name, which it writes
to a file named after the configuration file given as an argument to **sr_subscribe**
with a .queue suffix ( ."configfile".queue). 
If sr_subscribe is stopped, the posted messages continue to accumulate on the 
broker in the queue.  When the program is restarted, it uses the queuename 
stored in that file to connect to the same queue, and not lose any messages.

File downloads can be parallelized by running multiple sr_subscribes using
the same queue.  The processes will share the queue and each download 
part of what has been selected.  Simply launch multiple instances
of sr_subscribe in the same user/directory using the same configuration file. 

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


report_back and report_exchange
===============================

For each download, by default, an amqp report message is sent back to the broker.
This is done with option :

- **report_back <boolean>        (default: True)** 
- **report_exchange <report_exchangename> (default: xreport|xs_*username* )**

When a report is generated, it is sent to the configured *report_exchange*. Administrative
components post directly to *xreport*, whereas user components post to their own 
exchanges (xs_*username*). The report daemons then copy the messages to *xreport* after validation.

These reports are used for delivery tuning and for data sources to generate statistical information.
Set this option to **False**, to prevent generation of reports.



LOGS
====

Components write to log files, which by default are found in ~/.cache/sarra/log/<component>_<config>_<instance>.log.
At the end of the day (at midnight), these logs are rotated automatically by the components, and the old log gets a
date suffix. The directory in which the logs are stored can be overridden by the **log** option, the number of rotated
logs to keep are set by the **logrotate** parameter. The oldest log file is deleted when the
maximum number of logs has been reach and this continues for each rotation. An interval takes a duration
of the interval and it may takes a time unit suffix, such as 'd\|D' for days, 'h\|H' for hours, or 'm\|M' for minutes.
If no unit is provided logs will rotate at midnight.

- debug  
   Setting option debug is identical to use  **loglevel debug**

- log <dir> ( default: ~/.cache/sarra/log ) (on Linux)
   The directory to store log files in.
 
- logrotate <max_logs> ( default: 5 )
   Maximum number of logs archived.
 
- logrotate_interval <duration>[<time_unit>] ( default: 1 )
   The duration of the interval with an optional time unit (ie 5m, 2h, 3d)

- loglevel ( default: info )
   The level of logging as expressed by python's logging. Possible values are :  critical, error, info, warning, debug.

- chmod_log ( default: 0600 )
   The permission bits to set on log files.

Placement is as per: `XDG Open Directory Specification <https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.html>`_ setting the XDG_CACHE_HOME environment variable.


INSTANCES
=========

Sometimes one instance of a component and configuration is not enough to process & send all available notifications.

**instances      <integer>     (default:1)**

The instance option allows launching several instances of a component and configuration.
When running sr_sender for example, a number of runtime files are created.
In the ~/.cache/sarra/sender/configName directory::

  A .sr_sender_configname.state         is created, containing the number instances.
  A .sr_sender_configname_$instance.pid is created, containing the PID  of $instance process.

In directory ~/.cache/sarra/var/log::

  A .sr_sender_configname_$instance.log  is created as a log of $instance process.

The logs can be written in another directory than the default one with option :

**log            <directory logpath>  (default:~/.cache/sarra/var/log)**

.. note::  
  FIXME: indicate Windows location also... dot files on Windows?


.. Note::

  While the brokers keep the queues available for some time, Queues take resources on 
  brokers, and are cleaned up from time to time.  A queue which is not
  accessed and has too many (implementation defined) files queued will be destroyed.
  Processes which die should be restarted within a reasonable period of time to avoid
  loss of notifications.  A queue which is not accessed for a long (implementation dependent)
  period will be destroyed. 

.. Note::
   FIXME  The last sentence is not really right...sr_audit does track the queues' age. 
          sr_audit acts when a queue gets to the max_queue_size and not running.
          

vip - ACTIVE/PASSIVE OPTIONS
----------------------------

**sr_subscribe** can be used on a single server node, or multiple nodes
could share responsibility. Some other, separately configured, high availability
software presents a **vip** (virtual ip) on the active server. Should
the server go down, the **vip** is moved on another server.
Both servers would run **sr_subscribe**. It is for that reason that the
following options were implemented:

 - **vip          <string>          (None)**

When you run only one **sr_subscribe** on one server, these options are not set,
and sr_subscribe will run in 'standalone mode'.

In the case of clustered brokers, you would set the options for the
moving vip.

**vip 153.14.126.3**

When **sr_subscribe** does not find the vip, it sleeps for 5 seconds and retries.
If it does, it consumes and processes a message and than rechecks for the vip.


POSTING OPTIONS
===============

When advertising files downloaded for downstream consumers, one must set 
the rabbitmq configuration for an output broker.

The post_broker option sets all the credential information to connect to the 
output **AMQP** broker.

**post_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

Once connected to the source AMQP broker, the program builds notifications after
the download of a file has occurred. To build the notification and send it to
the next hop broker, the user sets these options :

 - **[--blocksize <value>]            (default: 0 (auto))**
 - **[--outlet <post|json|url>]       (default: post)**
 - **[-pbd|--post_base_dir <path>]    (optional)**
 - **[-ptp|--post_topic_prefix <pfx>] (default: 'v02.post')**
 - **post_exchange     <name>         (default: xpublic)**
 - **post_exchange_split   <number>   (default: 0)**
 - **post_base_url          <url>     (MANDATORY)**
 - **on_post           <script>       (default: None)**


[--blocksize <value>] (default: 0 (auto))
-----------------------------------------

This **blocksize** option controls the partitioning strategy used to post files.
The value should be one of::

   0 - autocompute an appropriate partitioning strategy (default)
   1 - always send entire files in a single part.
   <blocksize> - used a fixed partition size (example size: 1M )

Files can be announced as multiple parts.  Each part has a separate checksum.
The parts and their checksums are stored in the cache. Partitions can traverse
the network separately, and in parallel.  When files change, transfers are
optimized by only sending parts which have changed.

The *outlet* option allows the final output to be other than a post.  
See `sr_cpump(1) <sr_cpump.1.rst>`_ for details.

[-pbd|--post_base_dir <path>] (optional)
----------------------------------------

The *post_base_dir* option supplies the directory path that, when combined (or found) 
in the given *path*, gives the local absolute path to the data file to be posted.
The *post_base_dir* part of the path will be removed from the posted announcement.
For sftp urls it can be appropriate to specify a path relative to a user account.
Example of that usage would be:  -pbd ~user  -url sftp:user@host
For file: url's, base_dir is usually not appropriate.  To post an absolute path,
omit the -pbd setting, and just specify the complete path as an argument.

post_url <url> (MANDATORY)
--------------------------

The **post_base_url** option sets how to get the file... it defines the protocol,
host, port, and optionally, the user. It is best practice to not include 
passwords in urls.

post_exchange <name> (default: xpublic)
---------------------------------------

The **post_exchange** option set under which exchange the new notification
will be posted.  In most cases it is 'xpublic'.

Whenever a publish happens for a product, a user can set to trigger a script.
The option **on_post** would be used to do such a setup.

post_exchange_split   <number>   (default: 0)
---------------------------------------------

The **post_exchange_split** option appends a two digit suffix resulting from 
hashing the last character of the checksum to the post_exchange name,
in order to divide the output amongst a number of exchanges.  This is currently used
in high traffic pumps to allow multiple instances of sr_winnow, which cannot be
instanced in the normal way.  Example::

    post_exchange_split 5
    post_exchange xwinnow

will result in posting messages to five exchanges named: xwinnow00, xwinnow01,
xwinnow02, xwinnow03 and xwinnow04, where each exchange will receive only one fifth
of the total flow.

Remote Configurations
---------------------

One can specify URI's as configuration files, rather than local files. Example:

  - **--config http://dd.weather.gc.ca/alerts/doc/cap.conf**

On startup, sr_subscribe checks if the local file cap.conf exists in the 
local configuration directory.  If it does, then the file will be read to find
a line like so:

  - **--remote_config_url http://dd.weather.gc.ca/alerts/doc/cap.conf**

In which case, it will check the remote URL and compare the modification time
of the remote file against the local one. The remote file is not newer, or cannot
be reached, then the component will continue with the local file.

If either the remote file is newer, or there is no local file, it will be downloaded, 
and the remote_config_url line will be prepended to it, so that it will continue 
to self-update in future.


PUMPING
=======

*This is of interest to administrators only*

Sources of data need to indicate the clusters to which they would like data to be delivered.
PUMPING is implemented by administrators, and refers copying data between pumps. Pumping is
accomplished using on_message plugins which are provided with the package.

When messages are posted, if no destination is specified, the delivery is assumed to be 
only the pump itself.  To specify the further destination pumps for a file, sources use 
the *to* option on the post.  This option sets the to_clusters field for interpretation 
by administrators.

Data pumps, when ingesting data from other pumps (using shovel, subscribe or sarra components)
should include the *msg_to_clusters* plugin and specify the clusters which are reachable from
the local pump, which should have the data copied to the local pump, for further dissemination.
Sample settings::

  msg_to_clusters DDI
  msg_to_clusters DD

  on_message msg_to_clusters

Given this example, the local pump (called DDI) would select messages destined for the DD or DDI clusters,
and reject those for DDSR, which isn't in the list.  This implies that the DD pump may flow
messages to the DD pump.

The above takes care of forward routing of messages and data-to-data consumers.  Once consumers
obtain data, they generate reports, and those reports need to propagate in the opposite direction,
not necessarily by the same route, back to the sources.  Report routing is done using the *from_cluster*
header.  Again, this defaults to the pump where the data is injected, but may be overridden by
administrator action.

Administrators configure report routing shovels using the msg_from_cluster plugin. Example::

  msg_from_cluster DDI
  msg_from_cluster DD

  on_message msg_from_cluster

so that report routing shovels will obtain messages from downstream consumers and make
them available to upstream sources.


PLUGIN SCRIPTS
==============

One can override or add functionality with python plugins scripts.
Sarracenia comes with a variety of example plugins, and uses some to implement base functionality,
such as logging (implemented by default use of msg_log, file_log, post_log plugins).

Users can place their own scripts in the script sub-directory
of their config directory tree ( on Linux, the ~/.config/sarra/plugins). 

There are three varieties of scripts:  do\_* and on\_*.  Do\_* scripts are used
to implement functions, adding or replacing built-in functionality, for example, to implement
additional transfer protocols.

- do_download - to implement additional download protocols.

- do_get  - under ftp/ftps/http/sftp implement the get file part of the download process

- do_poll - to implement additional polling protocols and processes.

- do_put  - under ftp/ftps/http/sftp implement the put file part of the send process

- do_send - to implement additional sending protocols and processes.

These transfer protocol scripts should be declared using the **plugin** option.
Aside the targetted built-in function(s), a module **registered_as** that defines
a list of protocols that these functions provide.  Example :

def registered_as(self) :
       return ['ftp','ftps']

In the example above, if function **do_download** was provided in that plugin
then for any download of a message with an ftp or ftps url, it is that function that would be called.


On\_* plugins are used more often. They allow actions to be inserted to augment the default
processing for various specialized use cases. The scripts are invoked by having a given
configuration file specify an on_<event> option. The event can be one of:

- plugin -- declare a set of plugins to achieve a collective function.

- on_data -- when the reception of a block of data has occured, trigger a transformation
  action.  As this entry point is for content transformation, the api adds the content
  of the block as an additional argument, and rather than returning True or Fale,
  it returns the transformed data. This isn't particularly efficient, so should only be used
  to transform small files, but it provides a way of reducing overall i/o by transforming
  during transfer. It is imcompatible with binary transfer plugins (do_download, do_send )
  When active, the checksum of downloaded data will be set according to the transformed
  content, rather than the original.

- on_file -- When the reception of a file has been completed, trigger followup action.
  The **on_file** option defaults to file_log, which writes a downloading status message.

- on_heartbeat -- trigger periodic followup action (every *heartbeat* seconds.)
  defaults to heatbeat_cache, and heartbeat_log.  heartbeat_cache cleans the cache periodically,
  and heartbeat_log prints a log message ( helpful in detecting the difference between problems
  and inactivity. ) 

- on_html_page -- In **sr_poll**, turns an html page into a python dictionary used to keep in mind
  the files already published. The package provide a working example under plugins/html_page.py.

- on_line -- In **sr_poll** a line from the ls on the remote host is read in.

- on_message -- when an sr_post(7) message has been received.  For example, a message has been received
  and additional criteria are being evaluated for download of the corresponding file.  If the on_msg
  script returns false, then it is not downloaded.  (See discard_when_lagging.py, for example,
  which decides that data that is too old is not worth downloading).

- on_part -- Large file transfers are split into parts.  Each part is transferred separately.
  When a completed part is received, one can specify additional processing.

- on_post -- when a data source (or sarra) is about to post a message, permit customized
  adjustments of the post. on_part also defaults to post_log, which prints a message
  whenever a file is to be posted.

- on_start -- runs on startup, for when a plugin needs to recover state.

- on_stop -- runs on startup, for when a plugin needs to save state.

- on_watch -- when the gathering of **sr_watch** events starts, on_watch plugin is invoked.
  It could be used to put a file in one of the watch directory and have it published when needed.


The simplest example of a plugin: A do_nothing.py script for **on_file**::

  class Transformer(object): 
      def __init__(self):
          pass

      def on_file(self,parent):
          logger = parent.logger

          logger.info("I have no effect but adding this log line")

          return True

  self.plugin = 'Transformer'

The last line of the script is specific to the kind of plugin being
written, and must be modified to correspond (on_file or an on_file, on_message 
for an on_message, etc...) the plugin's stack. For example, one can have 
multiple *on_message* plugins specified, and they will be invoked in the order 
given in the configuration file.  Should one of these scripts return False, 
the processing of the message/file will stop there.  Processing will only 
continue if all configured plugins return True.  One can specify *on_message None* to 
reset the list to no plugins (removes msg_log, so it suppresses logging of message receipt).

The only argument the script receives is **parent**, which is a data
structure containing all the settings, as **parent.<setting>**, and
the content of the message itself as **parent.msg** and the headers
are available as **parent.msg[ <header> ]**.  The path to write a file
to is available as there is also **parent.msg.new_dir** / **parent.msg.new_file**

There are also registered plugins used to add or overwrite built-in 
transfer protocol scripts. They should be declared using the **plugin** option.
They must register the protocol (url scheme) that they intend to provide services for.
The script for transfer protocols are :

- do_download - to implement additional download protocols.

- do_get  - under ftp/ftps/http/sftp implement the get part of the download process

- do_poll - to implement additional polling protocols and processes.

- do_put  - under ftp/ftps/http/sftp implement the put part of the send process

- do_send - to implement additional sending protocols and processes.

The registration is done with a module named **registered_as** . It defines
a list of protocols that the provided module supports.

The simplest example of a plugin: A do_nothing.py script for **on_file**::

  class Transformer(object): 
      def __init__(self):
          pass

      def on_put(self,parent):
          msg = parent.msg

          if ':' in msg.relpath : return None

          netloc = parent.destination.replace("sftp://",'')
          if netloc[-1] == '/' : netloc = netloc[:-1]

          cmd = '/usr/bin/scp ' + msg.relpath + ' ' +  netloc + ':' + msg.new_dir + os.sep + msg.new_file

          status, answer = subprocess.getstatusoutput(cmd)

          if status == 0 : return True

          return False

      def registered_as(self) :
          return ['sftp']

  self.plugin = 'Transformer'


This plugin registers for sftp. A sender with such a plugin would put the product using scp.
It would be confusing for scp to have the source path with a ':' in the filename... Here the
case is handled by returning None and letting python sending the file over. The **parent**
argument holds all the needed program information.
Some other available variables::

  parent.msg.new_file     :  name of the file to write
  parent.msg.new_dir      :  name of the directory in which to write the file
  parent.msg.local_offset :  offset position in the local file
  parent.msg.offset       :  offset position of the remote file
  parent.msg.length       :  length of file or part
  parent.msg.in_partfile  :  T/F file temporary in part file
  parent.msg.local_url    :  url for reannouncement


See the `Programming Guide <Prog.rst>`_ for more information on plugin development.


Queue Save/Restore
==================


Sender Destination Unavailable
------------------------------

If the server to which the files are being sent is going to be unavailable for
a prolonged period, and there is a large number of messages to send to them, then
the queue will build up on the broker. As the performance of the entire broker
is affected by large queues, one needs to minimize such queues.

The *-save* and *-restore* options are used get the messages away from the broker
when too large a queue will certainly build up.
The *-save* option copies the messages to a (per instance) disk file (in the same directory
that stores state and pid files), as json encoded strings, one per line.
When a queue is building up::

   sr_sender stop <config> 
   sr_sender -save start <config> 

And run the sender in *save* mode (which continually writes incoming messages to disk)
in the log, a line for each message written to disk::

  2017-03-03 12:14:51,386 [INFO] sr_sender saving 2 message topic: v02.post.home.peter.sarra_devdocroot.sub.SASP34_LEMM_031630__LEDA_60215

Continue in this mode until the absent server is again available.  At that point::

   sr_sender stop <config> 
   sr_sender -restore start <config> 

While restoring from the disk file, messages like the following will appear in the log::

  2017-03-03 12:15:02,969 [INFO] sr_sender restoring message 29 of 34: topic: v02.post.home.peter.sarra_devdocroot.sub.ON_02GD022_daily_hydrometric.csv


After the last one::

  2017-03-03 12:15:03,112 [INFO] sr_sender restore complete deleting save file: /home/peter/.cache/sarra/sender/tsource2send/sr_sender_tsource2send_0000.save 


and the sr_sender will function normally thereafter.



Shovel Save/Restore
-------------------

If a queue builds up on a broker because a subscriber is unable to process
messages, overall broker performance will suffer, so leaving the queue lying around
is a problem. As an administrator, one could keep a configuration like this
around::

  % more ~/tools/save.conf
  broker amqp://tfeed@localhost/
  topic_prefix v02.post
  exchange xpublic

  post_rate_limit 50
  on_post post_rate_limit
  post_broker amqp://tfeed@localhost/

The configuration relies on the use of an administrator or feeder account.
Note the queue which has messages in it, in this case q_tsub.sr_subscribe.t.99524171.43129428. Invoke the shovel in save mode to consume messages from the queue
and save them to disk::

  % cd ~/tools
  % sr_shovel -save -queue q_tsub.sr_subscribe.t.99524171.43129428 foreground save.conf

  2017-03-18 13:07:27,786 [INFO] sr_shovel start
  2017-03-18 13:07:27,786 [INFO] sr_sarra run
  2017-03-18 13:07:27,786 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2017-03-18 13:07:27,788 [WARNING] non standard queue name q_tsub.sr_subscribe.t.99524171.43129428
  2017-03-18 13:07:27,788 [INFO] Binding queue q_tsub.sr_subscribe.t.99524171.43129428 with key v02.post.# from exchange xpublic on broker amqp://tfeed@localhost/
  2017-03-18 13:07:27,790 [INFO] report_back to tfeed@localhost, exchange: xreport
  2017-03-18 13:07:27,792 [INFO] sr_shovel saving to /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save for future restore
  2017-03-18 13:07:27,794 [INFO] sr_shovel saving 1 message topic: v02.post.observations.swob-ml.20170318.CPSL.2017-03-18-1600-CPSL-AUTO-swob.xml
  2017-03-18 13:07:27,795 [INFO] sr_shovel saving 2 message topic: v02.post.hydrometric.doc.hydrometric_StationList.csv
          .
          .
          .
  2017-03-18 13:07:27,901 [INFO] sr_shovel saving 188 message topic: v02.post.hydrometric.csv.ON.hourly.ON_hourly_hydrometric.csv
  2017-03-18 13:07:27,902 [INFO] sr_shovel saving 189 message topic: v02.post.hydrometric.csv.BC.hourly.BC_hourly_hydrometric.csv

  ^C2017-03-18 13:11:27,261 [INFO] signal stop
  2017-03-18 13:11:27,261 [INFO] sr_shovel stop


  % wc -l /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save
  189 /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save
  % 

The messages are written to a file in the caching directory for future use, with
the name of the file being based on the configuration name used. The file is in
json format, one message per line (lines are very long) and so filtering with other tools
is possible to modify the list of saved messages. Note that a single save file per
configuration is automatically set, so to save multiple queues, one would need one configurations
file per queue to be saved.  Once the subscriber is back in service, one can return the messages
saved to a file into the same queue::

  % sr_shovel -restore_to_queue q_tsub.sr_subscribe.t.99524171.43129428 foreground save.conf

  2017-03-18 13:15:33,610 [INFO] sr_shovel start
  2017-03-18 13:15:33,611 [INFO] sr_sarra run
  2017-03-18 13:15:33,611 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2017-03-18 13:15:33,613 [INFO] Binding queue q_tfeed.sr_shovel.save with key v02.post.# from exchange xpublic on broker amqp://tfeed@localhost/
  2017-03-18 13:15:33,615 [INFO] report_back to tfeed@localhost, exchange: xreport
  2017-03-18 13:15:33,618 [INFO] sr_shovel restoring 189 messages from save /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save 
  2017-03-18 13:15:33,620 [INFO] sr_shovel restoring message 1 of 189: topic: v02.post.observations.swob-ml.20170318.CPSL.2017-03-18-1600-CPSL-AUTO-swob.xml
  2017-03-18 13:15:33,620 [INFO] msg_log received: 20170318165818.878 http://localhost:8000/ observations/swob-ml/20170318/CPSL/2017-03-18-1600-CPSL-AUTO-swob.xml topic=v02.post.observations.swob-ml.20170318.CPSL.2017-03-18-1600-CPSL-AUTO-swob.xml lag=1034.74 sundew_extension=DMS:WXO_RENAMED_SWOB:MSC:XML::20170318165818 source=metpx mtime=20170318165818.878 sum=d,66f7249bd5cd68b89a5ad480f4ea1196 to_clusters=DD,DDI.CMC,DDI.EDM,DDI.CMC,CMC,SCIENCE,EDM parts=1,5354,1,0,0 toolong=1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ß from_cluster=DD atime=20170318165818.878 filename=2017-03-18-1600-CPSL-AUTO-swob.xml 
     .
     .
     .
  2017-03-18 13:15:33,825 [INFO] post_log notice=20170318165832.323 http://localhost:8000/hydrometric/csv/BC/hourly/BC_hourly_hydrometric.csv headers={'sundew_extension': 'BC:HYDRO:CSV:DEV::20170318165829', 'toolong': '1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ßñç1234567890ß', 'filename': 'BC_hourly_hydrometric.csv', 'to_clusters': 'DD,DDI.CMC,DDI.EDM,DDI.CMC,CMC,SCIENCE,EDM', 'sum': 'd,a22b2df5e316646031008654b29c4ac3', 'parts': '1,12270407,1,0,0', 'source': 'metpx', 'from_cluster': 'DD', 'atime': '20170318165832.323', 'mtime': '20170318165832.323'}
  2017-03-18 13:15:33,826 [INFO] sr_shovel restore complete deleting save file: /home/peter/.cache/sarra/shovel/save/sr_shovel_save_0000.save 


  2017-03-18 13:19:26,991 [INFO] signal stop
  2017-03-18 13:19:26,991 [INFO] sr_shovel stop
  % 

All the messages saved are returned to the named *return_to_queue*. Note that the use of the *post_rate_limit*
plugin prevents the queue from being flooded with hundreds of messages per second. The rate limit to use will need
to be tuned in practice.

By default the file name for the save file is chosen to be in ~/.cache/sarra/shovel/<config>_<instance>.save.
To choose a different destination, *save_file* option is available::

  sr_shovel -save_file `pwd`/here -restore_to_queue q_tsub.sr_subscribe.t.99524171.43129428 ./save.conf foreground

will create the save files in the current directory named here_000x.save where x is the instance number (0 for foreground.)




ROLES - feeder/admin/declare
============================

*of interest only to administrators*

Administrative options are set using::

  sr_subscribe edit admin

The *feeder* option specifies the account used by default system transfers for components such as
sr_shovel, sr_sarra and sr_sender (when posting).

- **feeder    amqp{s}://<user>:<pw>@<post_brokerhost>[:port]/<vhost>**

- **admin   <name>        (default: None)**

When set, the admin option will cause sr start to start up the sr_audit daemon.
FIXME: current versions, all users run sr_audit to notice dead subscribers.
Most users are defined using the *declare* option.

- **declare <role> <name>   (no defaults)**

subscriber
----------

  A subscriber is user that can only subscribe to data and return report messages. Subscribers are
  not permitted to inject data.  Each subscriber has an xs_<user> named exchange on the pump,
  where if a user is named *Acme*, the corresponding exchange will be *xs_Acme*.  This exchange
  is where an sr_subscribe process will send its report messages.

  By convention/default, the *anonymous* user is created on all pumps to permit subscription without
  a specific account.

source
------

  A user permitted to subscribe or originate data.  A source does not necessarily represent
  one person or type of data, but rather an organization responsible for the data produced.
  So if an organization gathers and makes available ten kinds of data with a single contact
  email or phone number for questions about the data and its availability, then all of
  those collection activities might use a single 'source' account.

  Each source gets a xs_<user> exchange for injection of data posts, and, similar to a subscriber
  to send report messages about processing and receipt of data. Source may also have an xl_<user>
  exchange where, as per report routing configurations, report messages of consumers will be sent.

User credentials are placed in the credentials files, and *sr_audit* will update
the broker to accept what is specified in that file, as long as the admin password is
already correct.


CONFIGURATION FILES
===================

While one can manage configuration files using the *add*, *remove*,
*list*, *edit*, *disable*, and *enable* actions, one can also do all
of the same activities manually by manipulating files in the settings
directory.  The configuration files for an sr_subscribe configuration 
called *myflow* would be here:

 - linux: ~/.config/sarra/subscribe/myflow.conf (as per: `XDG Open Directory Specication <https://specifications.freedesktop.org/basedir-spec/basedir-spec-0.6.rst>`_ ) 


 - Windows: %AppDir%/science.gc.ca/sarra/myflow.conf , this might be:
   C:\Users\peter\AppData\Local\science.gc.ca\sarra\myflow.conf

 - MAC: FIXME.

The top of the tree has  *~/.config/sarra/default.conf* which contains settings that
are read as defaults for any component on start up.  In the same directory, *~/.config/sarra/credentials.conf* contains credentials (passwords) to be used by sarracenia ( `CREDENTIALS`_ for details. )

One can also set the XDG_CONFIG_HOME environment variable to override default placement, or 
individual configuration files can be placed in any directory and invoked with the 
complete path.   When components are invoked, the provided file is interpreted as a 
file path (with a .conf suffix assumed.)  If it is not found as a file path, then the 
component will look in the component's config directory ( **config_dir** / **component** )
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


SEE ALSO
========


**User Commands:**

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - Select and Conditionally Download Posted Files

`sr_post(1) <sr_post.1.rst>`_ - post announcemensts of specific files.

`sr_watch(1) <sr_watch.1.rst>`_ - post that loops, watching over directories.

`sr_sender(1) <sr_sender.1.rst>`_ - subscribes to messages pointing at local files, and sends them to remote systems and reannounces them there.

`sr_report(1) <sr_report.1.rst>`_ - process report messages.


**Pump Adminisitrator Commands:**

`sr_shovel(8) <sr_shovel.8.rst>`_ - process messages (no downloading).

`sr_winnow(8) <sr_winnow.8.rst>`_ - a shovel with cache on, to winnow wheat from chaff.

`sr_sarra(8) <sr_sarra.8.rst>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_audit(8) <sr_audit.8.rst>`_ - Monitoring daemon, audits running configurations, restarts missing instances.

`sr_log2save(8) <sr_log2save.8.rst>`_ - Convert logfile lines to .save Format for reload/resend.


**Formats:**

`sr_post(7) <sr_post.7.rst>`_ - The format of announcement messages.

`sr_report(7) <sr_report.7.rst>`_ - The format of report messages.

`sr_pulse(7) <sr_pulse.7.rst>`_ - The format of pulse messages.

**Home Page:**

`https://github.com/MetPX/ <https://github.com/MetPX>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.


SUNDEW COMPATIBILITY OPTIONS
============================

For compatibility with sundew, there are some additional delivery options which can be specified.

destfn_script <script> (default:None)
-------------------------------------

This option defines a script to be run when everything is ready
for the delivery of the product.  The script receives the sr_sender class
instance.  The script takes the parent as an argument, and for example, any
modification to  **parent.msg.new_file**  will change the name of the file written locally.

filename <keyword> (default:WHATFN)
-----------------------------------

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
options.  A message that matched against the accept regexp pattern, will have its remote_file
plied this keyword option.  This keyword has priority over the preceeding **filename** one.

The **regexp pattern** can be use to set directory parts if part of the message is put
to parenthesis. **sr_sender** can use these parts to build the directory name. The
rst enclosed parenthesis strings will replace keyword **${0}** in the directory name...
the second **${1}** etc.

Example of use::


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

It's named  */this/20160123/pattern/RAW_MERGER_GRIB/directory* if the message would have a notice like:

**20150813161959.854 http://this.pump.com/ relative/path/to/20160123_product_RAW_MERGER_GRIB_from_CMC**


Field Replacements
------------------

In MetPX Sundew, there is a much more strict file naming standard, specialised for use with 
World Meteorological Organization (WMO) data.   Note that the file naming convention predates, and 
bears no relation to the WMO file naming convention currently approved, but is strictly an internal 
format.   The files are separated into six fields by colon characters.  The first field, DESTFN, 
gives the WMO (386 style) Abbreviated Header Line (AHL) with underscores replacing blanks::

   TTAAii CCCC YYGGGg BBB ...  

(see WMO manuals for details) followed by numbers to render the product unique (as in practice, 
though not in theory, there are a large number of products which have the same identifiers).
The meanings of the fifth field is a priority, and the last field is a date/time stamp.  
The other fields vary in meaning depending on context.  A sample file name::

   SACN43_CWAO_012000_AAA_41613:ncp1:CWAO:SA:3.A.I.E:3:20050201200339

If a file is sent to sarracenia and it is named according to the sundew conventions, then the 
following substitution fields are available::

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

The 'R' fields come from the sixth field, and the others come from the first one.
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
=======

Dd_subscribe was initially developed for  **dd.weather.gc.ca**, an Environment Canada website 
where a wide variety of meteorological products are made available to the public. It is from
the name of this site that the sarracenia suite takes the dd\_ prefix for its tools.  The initial
version was deployed in 2013 on an experimental basis.  The following year, support of checksums
was added, and in the fall of 2015, the feeds were updated to v02.  dd_subscribe still works,
but it uses the deprecated settings described above.  It is implemented in python2, whereas
the sarracenia toolkit is in python3.

In 2007, when the MetPX was originally open sourced, the staff responsible were part of
Environment Canada.  In honour of the Species At Risk Act (SARA), to highlight the plight
of disappearing species which are not furry (the furry ones get all the attention) and
because search engines will find references to names which are more unusual more easily, 
the original MetPX WMO switch was named after a carnivorous plant on the Species At
Risk Registry:  The *Thread-leaved Sundew*.  

The organization behind MetPX have since moved to Shared Services Canada, but when
it came time to name a new module, we kept with a theme of carnivorous plants, and 
chose another one indigenous to some parts of Canada: *Sarracenia*,  a variety
of insectivorous pitcher plants. We like plants that eat meat!  


dd_subscribe Renaming
---------------------

The new module (MetPX-Sarracenia) has many components, is used for more than 
distribution, and more than one website, and causes confusion for sysadmins thinking
it is associated with the dd(1) command (to convert and copy files).  So, we switched
all the components to use the sr\_ prefix.

