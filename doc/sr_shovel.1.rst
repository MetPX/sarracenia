==============
 SR_Shovel 
==============

-----------------------------
Copy Messages Between Brokers
-----------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite



SYNOPSIS
========

 **sr_shovel** configfile foreground|start|stop|restart|reload|status

DESCRIPTION
===========

sr_shovel copies messages on one broker to another. 

The sr_shovel component takes two argument: a configuration file described below,
and an action start|stop|restart|reload|status... (self explanatory.)


CONFIGURATION
=============

In General, the options for this component are described by the
`sr_config(7) <sr_config.7.html>`_  page which should be read first. 

It fully explains the option syntax, the configuration file location, 
credentials ... etc.

Standard sarracenia configuration would expect the config file to be found in :

 - linux: ~/.config/sarra/shovel/configfile.conf
 - Windows: %AppDir%/science.gc.ca/sarra/shovel, this might be:
   C:\Users\peter\AppData\Local\science.gc.ca\sarra\shovel\configfile.conf

When creating a new configuration file, the user can executing the program 
with  **--debug configfile foreground**  where a configfile.conf in the current 
working directory.

The options used in the configfile are described in the next sections.


Multiple streams
================

When executed,  the program  uses the default queue name.
If it is stopped, the posted messages continue to accumulate on the 
broker in the queue.  When the program is restarted, the queue name 
is reused, and no messages are lost.

The message processing can be parallelized by running multiple instances of the program. 
The program shares the same queue. The messages will be distributed  between processes.
Simply launch the program with option instances set to an integer greater than 1.


Consuming options
=================

This program consumes sr_post(7) or sr_log(7) messages. The options that cover this task are
fully explained in `sr_consumer(7) <sr_consumer.7.html>`_ . In this section,
as a reference, they are simply listed:

Setting the source broker :

**broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

Setting the queue on broker :

- **queue_name    <name>         (default: q_<brokerUser>.<programName>.<configName>)** 
- **durable       <boolean>      (default: False)** 
- **expire        <minutes>      (default: 10080 mins = 1 week)** 
- **message-ttl   <minutes>      (default: None)** 
- **prefetch      <N>            (default: 1)** 
- **reset         <boolean>      (default: False)** 

Setting the bindings on the queue :

 - **exchange      <name>         (default: xpublic)** 
 - **topic_prefix  <amqp pattern> (default: varies -- developer option)** 
 - **subtopic      <amqp pattern> (subtopic need to be set)** 

Using regular expression filtering messages

- **accept       <regexp pattern> (optional)** 
- **reject       <regexp pattern> (optional)** 
- **accept_unmatch      <boolean> (default: False)** 

Running a plugin on selected messages

- **on_message      <script_name> (optional)** 


POSTING OPTIONS
===============

There is no required option for posting messages.
By default, the program publishes the selected consumed message with its exchange
onto the current cluster, with the feeder account.

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

When a message is shoveled (consumed and published), an AMQP log message is published
on the consuming cluster under the log_exchange 'xlog'.

- **log_exchange <log_exchangename> (default: xlog)** 


PLUGINS ADVANCED FEATURES
=========================

As mentionned below, one can insert scripts into the flow of messages:
Should you want to implement tasks in various part of the execution of the program:

- **on_message  <script>        (default: None)** 
- **on_post     <script>        (default: None)** 

A do_nothing.py script for **on_message**, and **on_post** could be:
(this one being for **on_file**)

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
the program class.
Should one of these scripts return False, the processing of the message/file
will stop there and another message will be consumed from the broker.


SEE ALSO
--------

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_consumer(7) <sr_consumer.7.html>`_ - the options for message consuming in MetPX-Sarracenia.

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
