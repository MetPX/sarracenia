============
 SR_CONSUMER 
============

--------------------------------------------------------
Overview of Sarra Configuration to consume amqp messages
--------------------------------------------------------

:Manual section: 7
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite


DESCRIPTION
===========

Most Metpx Sarracenia components loop and proceed with their specific tasks
on the reception of sarracenia AMQP messages.
This document is meant to be the reference to explain and detail this
important task called "consuming" a message in AMQP jargon. 

To summarize what this document covers : to receive AMQP messages, one must 
provide the credentials for a broker (AMQP message switch). On the broker,
a queue must be created and configured in order to hold AMQP messages for
the process.  To put messages in that queue, the users must bind one or more
exchanges and specify topics of interest within them.

Once this set, the program can receive messages... We have found that having
messages through exchanges/topics bindings was not enough granular for our needs.
When a message is received, the user can also make more selections using 
regular expression onto the AMQP messages.

Once a message passes this selection process, the process verifies if the message
is correct. (has all infos, is properly routed?). At this point, the user
can run a plugin on the message and perform a task on the message.
(ex.: do stats, renaming the product, changing its destination... whatever...) 
If this plugin return False, the message is discarded. With True, process resumes.

This document explains all the options one can use to set this "consuming"
part of sarracenia programs. It will be referenced in the documentation of
the programs where applicable.

When a component does not comply to the standards in this document, it is
explained in the component's document.


OPTIONS
=======

Since this document focuses on the consuming options. We invite the reader to
read the option's syntax fully explained in  `sr_config(7) <sr_config.7.html>`_ 
and also to spend some time on the **credentials** section in it. 


Setting the broker 
------------------

**broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

This option defines the essentials to connect to a message switch called broker.
Some of the sarracenia programs already set a reasonable default to that option.
You provide the normal user,password,host,port of secured connections. The **vhost**
is a particular AMQP option that sarracenia could use. But it is enough to say 
that it is always **/**.


Creating the queue 
------------------

As described above, the next step is to create a queue.
The following are broker level options to create/set the queue.

- **queue_name    <name>         (default: q_<brokerUser>.<programName>.<configName>)** 
- **durable       <boolean>      (default: False)** 
- **expire        <minutes>      (default: 10080 mins = 1 week)** 
- **message-ttl   <minutes>      (default: None)** 
- **prefetch      <N>            (default: 1)** 
- **reset         <boolean>      (default: False)** 

By default, sarracenia components create a queue name automatically.
The default queue_name is:  **q_<brokerUser>.<programName>.<configName>** .
The user can specify its own queue_name provided that it starts with **q_<brokerUser>**.
Some variables can also be used within the queue_name like 
**${BROKER_USER},${PROGRAM},${CONFIG},${HOSTNAME}**

The  **expire**  option is expressed in minutes...
it sets how long should live a queue without connections.
Default is set to one week.  (Note: on broker the real
mesure is millisec. but we implemented it in minutes)

The  **durable** option, if set to True, means writes the queue
on disk if the broker is restarted.

The  **message-ttl** option set the time in minutes a message can live in the queue.
Past that time, the message is taken out of the queue by the broker.

The  **prefetch**  option set the number of messages distributed amongst
connections that share the queue... This rabbitmq option is applied to the queue
if the sarracenia option **queue_share** is True (the default).

When a component is (re)started, with the argument **--reset**,
its queue is deleted (if it already exists) and recreated 
according to the component's queue options.

(Note: Usefull everytime a broker option is modified. The
broker will not grant access to a queue declared 
options that differs from the one at creation)

Broker queue options not presented here have fixed settings.
(auto_delete False, FIXME others?)

Having reasonable defaults, the reader will rarely use any of these options.

(Note: Sometime on clusters, all nodes running the same component and its
config file default to an identical **queue_name**. Targetting the 
same broker, it forces the queue to be shared. If it should be avoided,
the user can just overwrite the default **queue_name** inserting **${HOSTNAME}**.
Each node will have its own queue, only shared by the node instances.
ex.:  queue_name q_${BROKER_USER}.${PROGRAM}.${CONFIG}.${HOSTNAME} )


Binding messages to the queue 
-----------------------------

The options in this section are often used.

Now we have a queue, we need to bind messages to it.
AMQP messages are all published to a broker under one exchange.

The exchange sarracenia uses is of type 'topic'.
In such an exchange, a message is always published with an attached
topic.

In sarracenia, the topic is reimplemented into a **topic_prefix** and
a **subtopic**. The topic_prefix is a developer option. The reader should
not use it. Internaly, it is used to define the protocol version of the message.
Hence the queue binding options:


 - **exchange      <name>         (default: xpublic)** 
 - **topic_prefix  <amqp pattern> (default: v00.dd.notify -- developer option)** 
 - **subtopic      <amqp pattern> (subtopic need to be set)** 

Usually, the user would declare one exchange, and several subtopic options.
Internally, a patterned topic is generated from the topic_prefix.subtopic pair.
The component binds the messages from the derived list of  exchange,topic
to the queue.

In sarracenia the message's main purpose is to announce the readyness of a
product giving its url. To use the subtopic to filter the products,
we have match subtopic string with the relative path of the product.

For example, consuming from DD, to give a correct value to the subtopic, one can
browse the our website  **http://dd.weather.gc.ca** and write down all directories
of interest.  For each directories write an  **subtopic**  option as follow:

 **subtopic  directory1.*.subdirectory3.*.subdirectory5.#** 

::

 where:  
       *                replaces a directory name 
       #                stands for the remaining possibilities

This wildcarding in subtopic is a limited feature supported by AMQP.

(Note: just to mention that it is supported to declare an exchange followed by
 some of its subtopics, another exchange some if its subtopics... the code
 supports it.  So far we used only one exchange)



regexp messages filtering 
-------------------------

We have selected our messages through **exchange**, **subtopic** and 
perhaps patterned  **subtopic** with only AMQP's limited wildcarding.
The broker puts the corresponding messages in our queue.
The component now consumes these messages.

Sarracenia consumers implement a the more powerful client side filtering
using regular expression based mechanisms. 

- **accept    <regexp pattern> (must be set)** 
- **reject    <regexp pattern> (optional)** 
- **accept_unmatch   <boolean> (default: False)** 


The  **accept**  and  **reject**  options use regular expressions (regexp).
The regexp is applied to the the message's URL for a match.

If the message's URL of a file matches a **reject**  pattern, the message
is acknowledged as consumed to the broker and skipped.

One that matches an  **accept**  pattern is processed by the
component.

In some components, the **accept/reject** are interlace under
a **directory** option. They then relate accepted messages to the **directory**
value they are specified under.

When using **accept** / **reject**  there are cases where after
going through all occurences of theses options, the URL did not matched.
The **accept_unmatch** option defines what to do in this case.
If set to **True** it will be accepted and **False** rejected. 

If no **accept** / **reject** is specified,
the program assumes it accepts all URL and sets
**accept_unmatch** to True.

The **accept/reject** are interpreted in order.
Each option is processed orderly from top to bottom.
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

It is best practice to use server side filtering to reduce the number of announcements sent
to the component to a small superset of what is relevant, and perform only a fine-tuning with the 
client side mechanisms, saving bandwidth and processing for all.


Verification and on_message plugins
-----------------------------------

Once a message passes through the selection process, the component verifies
if the message is correct. (has requiered infos, is properly routed?). 
If it is found correct at this point, the user can run a plugin on the message
and perform any task on the message.  (ex.: do stats, renaming the product,
changing its destination... whatever...) 

The plugin scripts are fully explained in  `sr_config(7) <sr_config.7.html>`_ 

- **on_message    <script_name> (must be set)** 

The **on_message** plugin scripts is the very last step in consuming messages.
As all plugin scripts, it returns a boolean. If False is returned, the component
acknowledge the message to the broker and does not process it.


If no on_message is provided or if it returns True,
the message has gone through all selecting mecanism
and it is processed by the component.



SEE ALSO
--------

`sr_config(7) <sr_config.7.html>`_ - the format of log messages.

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
