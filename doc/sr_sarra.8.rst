
=========
 SR_Sarra
=========

---------------------------------------------------------
Subscribe, Acquire and Recursively Re-announce Ad nauseam
---------------------------------------------------------

:Manual section: 8
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite

.. contents::


SYNOPSIS
========

**sr_sarra** foreground|start|stop|restart|reload|status configfile

**sr_sarra** cleanup|declare|setup configfile


DESCRIPTION
===========

**sr_sarra** is a program that Subscribes to file notifications,
Acquires the files and ReAnnounces them at their new locations.
The notification protocol is defined here `sr_post(7) <sr_post.7.rst>`_

**sr_sarra** connects to a *broker* (often the same as the remote file server
itself) and subscribes to the notifications of interest. It uses the notification
information to download the file on the local server its running on.
It then posts a notification for the downloaded files on a broker (usually on the local server).

**sr_sarra** can be used to acquire files from `sr_post(1) <sr_post.1.rst>`_
or `sr_watch(1) <sr_watch.1.rst>`_  or to reproduce a web-accessible folders (WAF),
that announce its' products.

The **sr_sarra** is an `sr_subscribe(1) <sr_subscribe.1.rst>`_  with the following presets::

   mirror True


Specific consuming requirements
--------------------------------

If the messages are posted directly from a source,
the exchange used is 'xs_<brokerSourceUsername>'.
Such message may not contain a source nor an origin cluster,
or a malicious user may set the values incorrectly.
To protect against malicious settings, administrators
should set *source_from_exchange* to **True**.


- **source_from_exchange  <boolean> (default: False)**

Upon reception, the program will set these values
in the parent class (here cluster is the value of
option **cluster** taken from default.conf):

self.msg.headers['source']       = <brokerUser>
self.msg.headers['from_cluster'] = cluster

overriding any values present in the message.  This setting
should always be used when ingesting data from a 
user exchange.


SEE ALSO
========

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.rst>`_ - the format of report messages.

`sr_report(1) <sr_report.1.rst>`_ - process report messages.

`sr_post(1) <sr_post.1.rst>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.rst>`_ - The format of announcements.

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - the download client.

`sr_watch(1) <sr_watch.1.rst>`_ - the directory watching daemon.

`dd_subscribe(1) <dd_subscribe.1.rst>`_ - the http-only download client.
