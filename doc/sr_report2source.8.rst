
==============
 SR_Log2source
==============

-------------------------------------------------------
Copy Log Messages from xlog to the Corresponding Source 
-------------------------------------------------------

:Manual section: 1 
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite


SYNOPSIS
========

**sr_report2source** -b <broker> -i <instances> start|stop|restart|reload|status

DESCRIPTION
===========

The administrator daemon to copy report messages to the relevant source.
**sr_report2source** subscribes to all report messages 
(posted on the xlog exchange), ignoring the ones not from the current cluster, 
and copying those that concern "source" to the xs\_"source"' exchange, where
the user concerned can read them.

The report notification protocol is defined here `sr_report(7) <sr_report.7.html>`_

**sr_report2source** connects to a *broker* and subscribes to all report messages. 
It uses the **from_cluster** 
field in the notification header to make sure it will process its logs. It uses
the **source** field in the notification header to post to exchange 'xr\_'source
the report messages. Any other messages are skipped.

The **sr_report2source** command can takes 3 arguments: a broker, a number of instances,
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

Once connected to an AMQP broker, **sr_report2source** it will process all report messages. 




SEE ALSO
========

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcements.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the http-only download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`sr_report2clusters(8) <sr_report2clusters.8.html>`_ - the inter-cluster report copy daemon.

