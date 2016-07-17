==============
 SR_Shovel 
==============

-----------------------------
Copy Messages Between Brokers
-----------------------------

:Manual section: 8
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite



SYNOPSIS
========

 **sr_shovel** configfile foreground|start|stop|restart|reload|status

DESCRIPTION
===========

sr_shovel copies messages on one broker (given by the *broker* option) to 
another (given by the *post_broker* option.) subject to filtering 
by (*exchange*, *subtopic*, and optionally, *accept*/*reject*.) 

The *topic_prefix* option must to be set to:

 - **v02.post** to shovel `sr_post(7) <sr_post.7.html>`_ messages 
 - **v02.log** to shovel `sr_report(7) <sr_report.7.html>`_ messages

There is no default.  On startup, the sr_shovel component takes two 
argument: a configuration file described below, and 
an action start|stop|restart|reload|status... (self explanatory.)

CONFIGURATION
=============

In general, the options for this component are described by the
`sr_config(7) <sr_config.7.html>`_  page which should be read first. 
It fully explains the option configuration language, and how to find 
the option settings.

Consuming Options
=================

This program consumes `sr_post(7) <sr_post.7.html>`_ or `sr_report(7) <sr_report.7.html>`_ 
messages.  One needs to set the options to connect to the broker to receive messages from:

**broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

Setting the bindings on the queue :

- **exchange      <name>         (default: xpublic)** 
- **topic_prefix  <amqp pattern> (default: varies -- developer option)** 
- **subtopic      <amqp pattern> (subtopic need to be set)** 

Using regular expression filtering messages :

- **accept       <regexp pattern> (optional)** 
- **reject       <regexp pattern> (optional)** 
- **accept_unmatch      <boolean> (default: False)** 

Running a plugin on selected messages :

- **on_message      <script_name> (optional)** 


POSTING OPTIONS
===============

There is no required option for posting messages.
By default, the program publishes the selected consumed message with its exchange
onto the current cluster, with the feeder account.

The user can overwrite the defaults with options :

- **post_broker    amqp{s}://<user>:<pw>@<post_brokerhost>[:port]/<vhost>**
- **post_exchange   <name>        (default: None)** 
- **post_exchange_split <number> (default: 0)**
- **on_post         <script_name> (optional)** 

The post_broker option sets the credential informations to connect to the
output **RabbitMQ** server. The default is the value of the **feeder** option
in default.conf.

The **post_exchange** option sets a new exchange for the selected messages.
The default is to publish under the exchange it was consumed.

The **post_exchange_split** is documented in sr_config.

Before a message is published, a user can set to trigger a script.
The option **on_post** would be used to do such a setup. 
The message is only published if the script returns True.


SEE ALSO
--------

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
