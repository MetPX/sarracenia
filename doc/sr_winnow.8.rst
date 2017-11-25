==========
 SR_Winnow 
==========

---------------------------
Suppress Redundant Messages
---------------------------

:Manual section: 8 
:Date: @Date@
:Version: @Version@
:Manual group: MetPX-Sarracenia

SYNOPSIS
========

**sr_winnow** foreground|start|stop|restart|reload|status configfile
**sr_winnow** cleanup|declare|setup configfile

DESCRIPTION
===========

**sr_winnow** is a program that Subscribes to file notifications, 
and reposts the notifications, suppressing the redundant ones by comparing their 
fingerprints (or checksums.)  The **sum** header stores a file's fingerprint as described
in the `sr_post(7) <sr_post.7.html>`_ man page.

**sr_winnow** is an `sr_subscribe(1) <sr_subscribe.1.html>`_ with the following options forced::

   no-download True  
   suppress_duplicates on
   accept_unmatch True

The suppress_duplicates lifetime can be adjusted, but it is always on.

**sr_winnow** connects to a *broker* (often the same as the posting broker)
and subscribes to the notifications of interest. On reception if a notification,
it looks up its **sum** in its cache.  if it is found, the file has already come through,
so the notification is ignored. If not, then the file is new, and the **sum** is added 
to the cache and the notification is posted.  

**sr_winnow** can be used to trim messages from `sr_post(1) <sr_post.1.html>`_,
`sr_poll(1) <sr_poll.1.html>`_  or `sr_watch(1) <sr_watch.1.html>`_  etc... It is 
used when there are multiple sources of the same data, so that clients only download the
source data once, from the first source that posted it.

The **sr_winnow** command takes two argument: an action start|stop|restart|reload|status... (self described)
followed by a configuration file described below.

The **foreground** is used when debugging a configuration, when the user wants to 
run the program and its configfile interactively...   The **foreground** instance 
is not concerned by other actions. 
The user would stop using the **foreground** instance by simply pressing <ctrl-c> on linux 
or use other means to kill its process.

The actions **cleanup**, **declare**, **setup** can be used to manage resources on
the rabbitmq server. The resources are either queues or exchanges. **declare** creates
the resources. **setup** creates and additionnaly does the bindings of queues.

CONFIGURATION
=============

In general, the options for this component are described by the
`sr_subscribe(1) <sr_subscribe.1.html>`_  page which should be read first.
It fully explains the option configuration language, and how to find
the option settings.

See `sr_subscribe(1) <sr_subscribe.1.html>`_  for more details.

 
DEPRECATED
==========

**interface -option formerly required in conjunction with *vip*.  **
Now just scans all interfaces.

SEE ALSO
========

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_report(1) <sr_report.1.html>`_ - process report messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcements.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`dd_subscribe(1) <dd_subscribe.1.html>`_ - the http-only download client.
