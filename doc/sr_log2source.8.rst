
==============
 SR_Log2source
==============

------------------------------------
Return Log to Source of the Products
------------------------------------

:Manual section: 1 
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite


SYNOPSIS
========

**sr_log2source** -b <broker> -i <instances> start|stop|restart|reload|status

DESCRIPTION
===========

The administrator daemon to copy log messages to the relevant source.
**sr_log2source** subscribes to all log notifications 
(posted on the xlog exchange), ignoring the ones not from the current cluster, 
and copying those that concern "source" to the xs\_"source"' exchange. 

The log notification protocol is defined here `sr_log(7) <sr_log.7.html>`_

**sr_log2source** connects to a *broker* (often the same as the remote file server 
itself) and subscribes to all log notifications. It uses the **from_cluster** 
field in the notification header to make sure it will process its logs. It uses
the **source** field in the notification header to post to exchange 'xl\_'source
the log notifications. Any other log notifications are skipped.

The **sr_log2source** command can takes 3 arguments: a broker, a number of instances,
followed by an action start|stop|restart|reload|status... (self described).

CONFIGURATION
=============

In general, the options for this component are described by the
`sr_config(7) <sr_config.7.html>`_  page which should be read first. 
It fully explains the option configuration language, and how to find 
the option settings.

The broker option sets all the credential information to connect to 
the **AMQP** server: 

**--broker|-b amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqp://guest:guest@localhost/ ) 

Once connected to an AMQP broker, **sr_log2source** it will process all log messages. 




SEE ALSO
========

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcements.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the http-only download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`sr_log2clusters(8) <sr_log2clusters.8.html>`_ - the inter-cluster log copy daemon.

