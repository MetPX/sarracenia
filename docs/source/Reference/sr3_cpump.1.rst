==========
 SR_CPUMP 
==========

-----------------
sr_shovel in C
-----------------

:Manual section: 1 
:Date: |today|
:Version: |release|
:Manual group: MetPX-Sarracenia

SYNOPSIS
========

**sr_cpump** foreground|start|stop|restart|reload|status configfile
**sr_cpump** cleanup|declare configfile

DESCRIPTION
===========

**sr_cpump** is an alternate implementation of the *shovel* component of `sr3(1) <sr3.1.html>`_ 
with some limitations.  

 - doesn't download data, only circulates posts.
 - runs as only a single instance (no multiple instances). 
 - does not support any plugins.
 - does not support vip for high availability.
 - different regular expression library: POSIX vs. python.
 - does not support regex for the strip command (no non-greedy regex).

It can therefore act as a drop-in replacement for:

   `sr3 shovel <sr3.1.rst>`_ - process shovel messages.

   `sr3 winnow <sr3.1.rst>`_ - process winnow messages.

The C implementation may be easier to make available in specialized environments, 
such as High Performance Computing, as it has far fewer dependencies than the python version.
It also uses far less memory for a given role.  Normally the python version 
is recommended, but there are some cases where use of the C implementation is sensible.

**sr_cpump** connects to a *broker* (often the same as the posting broker)
and subscribes to the notifications of interest. On reception of a post,
it looks up its **sum** in its cache.  If it is found, the file has already come through,
so the notification is ignored. If not, then the file is new, and the **sum** is added 
to the cache and the notification is posted.  

**sr_cpump** can be used, like `sr3 winnow(1) <sr3.1.html>`_,  to trim messages 
from `sr3_post(1) <sr3_post.1.html>`_, `sr3 poll(1) <sr3.1.html>`_  
or `sr3 watch (1) <sr3.1.html>`_  etc... It is used when there are multiple 
sources of the same data, so that clients only download the source data once, from 
the first source that posted it.

The **sr3_cpump** command takes two arguments: an action start|stop|restart|reload|status... (self described)
followed by a configuration file.

The **foreground** action is used when debugging a configuration, when the user wants to 
run the program and its configfile interactively...   The **foreground** instance 
is not concerned by other actions.  The user would stop using the **foreground** instance 
by simply <ctrl-c> on linux or use other means to send SIGINT or SIGTERM to the process.

The actions **cleanup**, **declare**, can be used to manage resources on
the rabbitmq server. The resources are either queues or exchanges. **declare** creates
the resources. creates and additionally does the bindings of queues.

The actions **add**, **remove**, **edit**, **list**, **enable**, **disable** act
on configurations.

CONFIGURATION
=============

In general, the options for this component are described by 
the `sr3_options(7) <sr3_options.7.html>`_  page which should be read first.
It fully explains the option configuration language, and how to find
the option settings.

**NOTE**: The regular expression library used in the C implementation is the POSIX
one, and the grammar is slightly different from the python implementation.  Some
adjustments may be needed.


ENVIRONMENT VARIABLES
=====================

If the SR_CONFIG_EXAMPLES variable is set, then the *add* directive can be used
to copy examples into the user's directory for use and/or customization.

An entry in the ~/.config/sarra/default.conf (created via sr_subscribe edit default.conf )
could be used to set the variable::

  declare env SR_CONFIG_EXAMPLES=/usr/lib/python3/dist-packages/sarra/examples

The value should be available from the output of a list command from the python
implementation.

SEE ALSO
========


**User Commands:**

`sr3(1) <sr3.1.html>`_ - Sarracenia main command line interface.

`sr3_post(1) <sr3_post.1.html>`_ - post file notification messages (python implementation.)

`sr3_cpost(1) <sr3_cpost.1.html>`_ - post file announcemensts (C implementation.)

**Formats:**

`sr3_credentials(7) <sr3_credentials.7.html>`_ - Convert logfile lines to .save Format for reload/resend.

`sr3_options(7) <sr3_options.7.html>`_ - Convert logfile lines to .save Format for reload/resend.

`sr_post(7) <sr_post.7.html>`_ - The format of notification message messages.

**Home Page:**

`https://metpx.github.io/sarracenia <https://metpx.github.io/sarracenia>`_ - Sarracenia: a real-time pub/sub data sharing management toolkit

                                     
