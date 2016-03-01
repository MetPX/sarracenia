=============
 SR_CONSUMER 
=============

--------------------------------------------------------
Overview of Sarra Configuration to Consume AMQP Messages
--------------------------------------------------------

:Manual section: 7
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite


DESCRIPTION
===========

Most Metpx Sarracenia components loop on reception of sarracenia AMQP messages.
Usually, the messages of interest are sr_post messages, announcing the availability 
of a file by publishing it´s URL ( or a part of a file ), but there are also
sr_log(7) messages which can be processed using the same tools.  AMQP messages are 
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

This document explains all the options used to set this "consuming" part of sarracenia programs. 


OPTIONS
=======

Since this document focuses on the consuming options. We invite the reader to
read the option syntax fully explained in  `sr_config(7) <sr_config.7.html>`_ 
and also to spend some time on the **credentials** section in it. 


Setting the broker 
==================

**broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

A AMQP URI to configure a connection to a message pump ( aka AMQP broker.)
Some sarracenia components set a reasonable default for that option.
You provide the normal user,host,port of connections.  In most configuration files, 
the password is missing.  The password is normally only included in the credentials.conf file.

Sarracenia work has not used vhosts, so **vhost** should almost always be **/**.

for more info on the AMQP URI format: ( https://www.rabbitmq.com/uri-spec.html )


Creating the Queue 
==================

The following are broker level options to create/set the queue.

- **queue_name    <name>         (default: q_<brokerUser>.<programName>.<configName>)** 
- **durable       <boolean>      (default: False)** 
- **expire        <minutes>      (default: 10080 mins = 1 week)** 
- **message-ttl   <minutes>      (default: None)** 
- **prefetch      <N>            (default: 1)** 
- **reset         <boolean>      (default: False)** 

Sarracenia components create a queue name automatically.
The default queue_name is:  **q_<brokerUser>.<programName>.<configName>** .
The user can override the defaul provided that it starts with **q_<brokerUser>**.
Some variables can also be used within the queue_name like 
**${BROKER_USER},${PROGRAM},${CONFIG},${HOSTNAME}**

The  **expire**  option is expressed in minutes...
it sets how long should live a queue without connections.
Default is set to one week.  (Note: on broker the real
unit is milliseconds but we implemented it in minutes)

The  **durable** option, if set to True, means writes the queue
on disk if the broker is restarted.

The  **message-ttl** option set the time in minutes a message can live in the queue.
Past that time, the message is taken out of the queue by the broker.

The **prefetch** option sets the number of messages to fetch at one time.
When multiple instances are running and prefetch is 4, each instance will obtain upto four 
messages at a time.  To minimize the number of messages lost if an instance dies and have 
optimal load sharing, the prefetch should be set as low as possible.  However, over long
haul links, it is necessary to raise this number, to hide round-trip latency, so a setting
of 10 or more may be needed. 

When **--reset** is set, and a component is (re)started,
its queue is deleted (if it already exists) and recreated 
according to the component's queue options.  This is 
when a broker option is modified, as the broker will refuse access 
to a queue declared with options that differ from what was 
set at creation.  It can also be used to discard a queue
quickly when a receiver has been shut down for a long period.

AMQP queue options not presented are fixed to a sensible value.

As the default settings are usually appropriate, these options should 
rarely be needed.



Binding a Queue to an Exchange
==============================

The options in this section are often used.

Now we have a queue, it needs to be bound to one or more exchanges.
types of exchanges, but Sarracenia uses 'topic' exchanges exclusively.

In Sarracenia, the root of the topic tree is fixed to indicate the protocol version 
and type of the message (but developers can override it with the **topic_prefix**  
option.)


Hence the queue binding options:
a **subtopic**.  

 - **exchange      <name>         (default: xpublic)** 
 - **topic_prefix  <amqp pattern> (default: varies -- developer option)** 
 - **subtopic      <amqp pattern> (subtopic need to be set)** 

Usually, the user specifies one exchange, and several subtopic options.
**Subtopic** is what is normally used to indicate messages of interest.
To use the subtopic to filter the products, match the subtopic string with 
the relative path of the product.

For example, consuming from DD, to give a correct value to subtopic, one can
browse the our website  **http://dd.weather.gc.ca** and write down all directories
of interest.  For each directories write an  **subtopic**  option as follow:

 **subtopic  directory1.*.subdirectory3.*.subdirectory5.#** 

::

 where:  
       *                replaces a directory name 
       #                stands for the remaining possibilities

This wildcarding in subtopic is a limited feature supported by AMQP.


Regexp messages filtering 
=========================

We have selected our messages through **exchange**, **subtopic** and 
perhaps patterned  **subtopic** with only AMQP's limited wildcarding.
The broker puts the corresponding messages in our queue.
The component now consumes these messages.

Sarracenia consumers implement a the more powerful client side filtering
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


Verification and On_message Plugins
===================================

Once a message passes through the selection process, the component verifies
if the message is correct. (has required infos, is properly routed?). 
If it is found correct at this point, the user can run a plugin on the message
and perform any task on the message.  (ex.: do stats, renaming the product,
changing its destination... whatever...) 

The plugin scripts are fully explained in  `sr_config(7) <sr_config.7.html>`_ 

- **on_message    <script_name> (must be set)** 

The **on_message** plugin scripts is the very last step in consuming messages.
As all plugin scripts, it returns a boolean. If False is returned, the component
acknowledge the message to the broker and does not process it.  If no on_message is 
provided or if it returns True, the message is processed by the component.  


SEE ALSO
--------

`sr_config(7) <sr_config.7.html>`_ - the format of log messages.

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
