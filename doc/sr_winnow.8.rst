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

.. contents::

SYNOPSIS
========

**sr_winnow** foreground|start|stop|restart|reload|status configfile
**sr_winnow** cleanup|declare|setup configfile

DESCRIPTION
===========

**sr_winnow** is a program that subscribes to file notifications 
and reposts the notifications, suppressing the redundant ones by comparing their 
fingerprints (or checksums).  The **sum** header stores a file's fingerprint as described
in the `sr_post(7) <sr_post.7.rst>`_ man page.

**sr_winnow** is an `sr_subscribe(1) <sr_subscribe.1.rst>`_ with the following options forced::

   no-download True  
   suppress_duplicates on
   accept_unmatch True

The suppress_duplicates lifetime can be adjusted, but it is always on.

**sr_winnow** connects to a *broker* (often the same as the posting broker)
and subscribes to the notifications of interest. On reception of a notification,
it looks up its **sum** in its cache.  If it is found, the file has already come through,
so the notification is ignored. If not, then the file is new, and the **sum** is added 
to the cache and the notification is posted.  

**sr_winnow** can be used to trim messages from `sr_post(1) <sr_post.1.rst>`_,
`sr_poll(1) <sr_poll.1.rst>`_  or `sr_watch(1) <sr_watch.1.html>`_  etc... It is 
used when there are multiple sources of the same data, so that clients only download the
source data once, from the first source that posted it.

The **sr_winnow** command takes two argument: an action start|stop|restart|reload|status... (self described)
followed by a configuration file described below.

The **foreground** is used when debugging a configuration, when the user wants to 
run the program and its configfile interactively. 

The actions **cleanup**, **declare**, **setup** can be used to manage resources on
the rabbitmq server. The resources are either queues or exchanges. **declare** creates
the resources. **setup** creates and additionally does the bindings of queues.

CONFIGURATION
=============

In general, the options for this component are described by the
`sr_subscribe(1) <sr_subscribe.1.rst>`_  page which should be read first.
It fully explains the option configuration language and how to find
the option settings.

See `sr_subscribe(1) <sr_subscribe.1.rst>`_  for more details.

Multiple Instances
------------------

- **exchange_split       <boolean>      (default: False)**
- **instances            <integer>      (default: 1)**

when there a flow has too many messages to be handled by a single instance,
sr_winnow performs differently from the other other components because
splitting sr_winnows work across multiple instances requires that the
files with the same name always go to the same instance.  

To use multiple processes, the upstream component feeding the winnow
will include in it's configuration, for example::

   post_exchange xs_hoho
   post_exchange_split 4

that will cause the following exchanges to be created: xs_hoho00, xs_hoho01,
xs_hoho02, xs_hoho03, and files to be sent to the exchanges based on the
hash of their names. The corresponding winnows need to be configured as follows::

   echange xs_hoho
   exchange_split 
   instances 4
   
With this configuration, winnow will be started with four instances.
Instances for other components, share a common queue, 
sr_winnow instances, with the above settings, will each bind to 
one of the exchanges using a non-shared queue.


 
SEE ALSO
========

`sr_report(7) <sr_report.7.rst>`_ - the format of report messages.

`sr_report(1) <sr_report.1.rst>`_ - process report messages.

`sr_post(1) <sr_post.1.rst>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.rst>`_ - the format of announcements.

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - the download client.

`sr_watch(1) <sr_watch.1.rst>`_ - the directory watching daemon.

`dd_subscribe(1) <dd_subscribe.1.rst>`_ - the http-only download client.
