==========
 SR_CPUMP 
==========

-----------------
sr_subscribe in C
-----------------

:Manual section: 1 
:Date: @Date@
:Version: @Version@
:Manual group: MetPX-Sarracenia

SYNOPSIS
========

**sr_cpump** foreground|start|stop|restart|reload|status configfile
**sr_cpump** cleanup|declare|setup configfile

DESCRIPTION
===========

**sr_cpump** is an alternate implementation of `sr_subscribe(7) <sr_subscribe.1.html>`_ 
with some limitations.  

 - doesn't download data, but only circulates posts.
 - runs as only a single instance (no multiple instances.) 
 - does not support any plugins.
 - does not support vip for high availability.
 - different regular expression library: POSIX vs. python.
 - does not support regex for the strip command (no non-greedy regex)

It can therefore act as a drop-in replacement for:

   `sr_report(1) <sr_report.1.html>`_ - process report messages.

   `sr_shovel(1) <sr_shovel.1.html>`_ - process shovel messages.

   `sr_winnow(1) <sr_winnow.1.html>`_ - process winnow messages.

The C implementation may be easier to make available in specialized environments, 
such as High Performance Computing, as it has far fewer dependencies than the python version.
It also uses far less memory for a given role.  Normally the python version 
is recommended, but there are some cases where use of the C implementation is sensible.

**sr_cpump** connects to a *broker* (often the same as the posting broker)
and subscribes to the notifications of interest. On reception if a notification,
it looks up its **sum** in its cache.  if it is found, the file has already come through,
so the notification is ignored. If not, then the file is new, and the **sum** is added 
to the cache and the notification is posted.  

**sr_cpump** can be used, like `sr_winnow(1) <sr_winnow.1.html>`_,  to trim messages 
from `sr_post(1) <sr_post.1.html>`_, `sr_poll(1) <sr_poll.1.html>`_  
or `sr_watch(1) <sr_watch.1.html>`_  etc... It is used when there are multiple 
sources of the same data, so that clients only download the source data once, from 
the first source that posted it.

The **sr_cpump** command takes two argument: an action start|stop|restart|reload|status... (self described)
followed by a configuration file.

The **foreground** action is used when debugging a configuration, when the user wants to 
run the program and its configfile interactively...   The **foreground** instance 
is not concerned by other actions.  The user would stop using the **foreground** instance 
by simply <ctrl-c> on linux or use other means send SIGINT or SIGTERM to the process.

The actions **cleanup**, **declare**, **setup** can be used to manage resources on
the rabbitmq server. The resources are either queues or exchanges. **declare** creates
the resources. **setup** creates and additionally does the bindings of queues.

The actions **add**, **remove**, **edit**, **list**, **enable**, **disable** act
on configurations.

CONFIGURATION
=============

In general, the options for this component are described by 
the `sr_subscribe(1) <sr_subscribe.1.html>`_  page which should be read first.
It fully explains the option configuration language, and how to find
the option settings.

**NOTE**: The regular expression library used in the C implementation is the POSIX
one, and the grammar is slightly different from the python implementation.  Some
adjustments may be needed.


MESSAGE SELECTION OPTIONS
-------------------------

 - **accept        <regexp pattern> (default: False)** 
 - **reject        <regexp pattern> (default: False)** 
 - **on_message            <script> (default: None)** 

One has the choice of filtering using  **subtopic**  with only AMQP's limited 
wildcarding, and/or with the more powerful regular expression based  **accept/reject**  
mechanisms described below.  The difference being that the AMQP filtering is 
applied by the broker itself, saving the notices from being delivered to the 
client at all. The  **accept/reject**  patterns apply to messages sent by the 
broker to the subscriber.  In other words,  **accept/reject**  are client 
side filters, whereas  **subtopic**  is server side filtering.  

It is best practice to use server side filtering to reduce the number of 
announcements sent to the client to a small superset of what is relevant, and 
perform only a fine-tuning with the client side mechanisms, saving bandwidth 
and processing for all.

See `sr_subscribe(1) <sr_subscribe.1.html>`_  for more details.

 
OUTPUT NOTIFICATION OPTIONS
---------------------------

sr_cpump has one option that is different from the python implementation:

**outlet  <post|json|url>**

the options are:

post:

  post messages to an post_exchange
  
  **post_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**
  **post_exchange     <name>         (MANDATORY)** 
  **on_post           <script>       (default: None)** 
  
  The **post_broker** defaults to the input broker if not provided.
  Just set it to another broker if you want to send the notifications
  elsewhere.
  
  The **post_exchange** must be set by the user. This is the exchange under
  which the notifications will be posted.
  
json:
 
  write each message to standard output, one per line in the same json format used for 
  queue save/restore by the python implementation.

url:

  just output the retrieval URL to standard output.


ENVIRONMENT VARIABLES
=====================

if the SR_CONFIG_EXAMPLES variable is set, then the *add* directive can be used
to copy examples into the user's directory for use and/or customization.

An entry in the ~/.config/sarra/default.conf (created via sr_subscribe edit default.conf )
could be used to set the variable::

  declare env SR_CONFIG_EXAMPLES=/usr/lib/python3/dist-packages/sarra/examples

the value should be available from the output of a list command from the python
implementation.

SEE ALSO
========

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_report(1) <sr_report.1.html>`_ - process report messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcements.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`dd_subscribe(1) <dd_subscribe.1.html>`_ - the http-only download client.
