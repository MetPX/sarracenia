
==============
 DD_Log2source
==============

------------------------------------
Return Log to Source of the Products
------------------------------------

:Manual section: 1 
:Date: Oct 2015
:Version: 0.0.1
:Manual group: MetPx Sarracenia Suite


SYNOPSIS
========

**dd_log2source** -b <broker> -i <instances> start|stop|restart|reload|status

DESCRIPTION
===========

The administrator daemon to copy log messages to the relevant source.
**dd_log2source** subscribes to all log notifications 
(posted on the xlog exchange), ignoring the ones not from the current cluster, 
and copying those that concern "source" to the xs\_"source"' exchange. 

The log notification protocol is defined here `dd_log(7) <dd_log.7.html>`_

**dd_log2source** connects to a *broker* (often the same as the remote file server 
itself) and subscribes to all log notifications. It uses the **from_cluster** 
field in the notification header to make sure it will process its logs. It uses
the **source** field in the notification header to post to exchange 'xl\_'source
the log notifications. Any other log notifications are skipped.

The **dd_log2source** command can takes 3 arguments: a broker, a number of instances,
followed by an action start|stop|restart|reload|status... (self described).

CONFIGURATION
=============

Options are placed in the command line in the form: 

**-option <value>** 

BROKER
------

First, the program needs to set the rabbitmq configurations of a source broker.
The broker option sets all the credential information to connect to the **AMQP** server 

**--broker|-b amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqp://guest:guest@localhost/ ) 


Once connected to an AMQP broker, **dd_log2source** use exchange xlog, and topic v02.log.#
to get all logs messages. 



INSTANCES
---------

It is possible that one instance of dd_log2source 
is not enough to process & download all available log notifications.

**--instances|-i    <integer>     (default:1)**


dd_log2source -i 10 start   will fork  10 instances of dd_log2source.
.dd_log2source_$instance.pid  are created and contain the PID  of $instance process.
dd_log2source_$instance.log  are created and contain the logs of $instance process.

The logs can be written in another directory than the current one with option :

**log            <directory logpath>  (default:$PWD)**


.. NOTE:: 
  FIXME: standard installation/setup explanations ...
  FIXME: a standard place where all the logs ?
  FIXME: a standard place where all the pid files ?




SEE ALSO
========

`dd_log(7) <dd_log.7.html>`_ - the format of log messages.

`dd_post(1) <dd_post.1.html>`_ - post announcemensts of specific files.

`dd_post(7) <dd_post.7.html>`_ - The format of announcements.

`dd_subscribe(1) <dd_subscribe.1.html>`_ - the http-only download client.

`dd_watch(1) <dd_watch.1.html>`_ - the directory watching daemon.

`dd_log2clusters(8) <dd_log2clusters.8.html>`_ - the inter-cluster log copy daemon.

