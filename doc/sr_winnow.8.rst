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

**sr_winnow** configfile foreground|start|stop|restart|reload|status

DESCRIPTION
===========

**sr_winnow** is a program that Subscribes to file notifications, 
and reposts the notifications, suppressing the redundant ones by comparing their 
fingerprints (or checksums.)  The **sum** header stores a file's fingerprint as described
in the `sr_post(7) <sr_post.7.html>`_ man page.

**sr_winnow** connects to a *broker* (often the same as the posting broker)
and subscribes to the notifications of interest. On reception if a notification,
it looks up its **sum** in its cache.  if it is found, the file has already come through,
so the notification is ignored. If not, then the file is new, and the **sum** is added 
to the cache and the notification is posted.  

**sr_winnow** can be used to trim messages from `sr_post(1) <sr_post.1.html>`_,
`sr_poll(1) <sr_poll.1.html>`_  or `sr_watch(1) <sr_watch.1.html>`_  etc... It is 
used when there are multiple sources of the same data, so that clients only download the
source data once, from the first source that posted it.

The **sr_winnow** command takes two argument: a configuration file described below,
followed by an action start|stop|restart|reload|status... (self described).

The **foreground** is used when debugging a configuration, when the user wants to 
run the program and its configfile interactively...   The **foreground** instance 
is not concerned by other actions. 
The user would stop using the **foreground** instance by simply pressing <ctrl-c> on linux 
or use other means to kill its process.

CONFIGURATION
=============

In general, the options for this component are described by the
`sr_config(7) <sr_config.7.html>`_  page which should be read first.
It fully explains the option configuration language, and how to find
the option settings.


ACTIVE/PASSIVE OPTIONS
----------------------

**sr_winnow** can be used on a single server.
Idealy, to make it more robust, you would run it on clustered brokers.
An high availability software presents a **vip** (virtual ip) on the active
server. Should the server go down, the **vip** is moved on another server.
Both servers would run **sr_winnow**. It is for that reason that the 
following options were implemented:

 - **vip          <string>          (None)** 
 - **interface    <string>          (None)**

When you run only one **sr_winnow** on one server, these options are not set,
and sr_winnow will run in 'standalone mode'.

In the case of clustered brokers, you would set the options for the 
moving vip.

**vip 153.14.126.3**
**interface eth0**

When **sr_winnow** does not find the vip, it sleeps for 5 seconds and retries.
If it does, it consumes and process a message and than rechecks for the vip.


SOURCE NOTIFICATION OPTIONS
---------------------------

First, the program needs to set all the rabbitmq configurations for a source 
broker.  The broker option sets all the credential information to connect 
to the **AMQP** server 

**broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: None and it is mandatory to set it ) 


Once connected to an AMQP broker, the user needs to bind a queue
to exchanges and topics to determine the messages of interest.

QUEUE BINDING OPTIONS
---------------------

First, the program needs to set all the rabbitmq configurations for a source broker.
These options define which messages (URL notifications) the program receives:

- **exchange      <name>         (MANDATORY)** 
- **topic_prefix  <name>         (default: v02.post)**
- **subtopic      <amqp pattern> (default: #)**

The **exchange** is mandatory.

If **sr_winnow** is to be used to winnow products from a source 
(**sr_post**, **sr_watch**, **sr_poll**)  then the exchange would
be named 'xs\_'SourceUserName.  SourceUserName is the one set in the broker
option, (the amqp user the source uses to announce products.)


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

**sr_winnow** does not check, in the received message, the destination clusters. 
So no message is discarted if without destination, source or other missing attributs.

The user can provide an **on_message** script. When a message is accepted up 
to this level of verification, the **on_message** script is called... with 
the **sr_winnow** class instance as argument.  The script can perform whatever 
you want... if it returns False, the processing of the message will stop 
there. If True, the program will continue processing from there.  


See `sr_config(7) <sr_config.7.html>`_  for more details.

 
OUTPUT NOTIFICATION OPTIONS
---------------------------

The notifications that are not ignored by **sr_winnow** are reposted.
The options ar

**post_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**
**post_exchange     <name>         (MANDATORY)** 
**on_post           <script>       (default: None)** 

The **post_broker** defaults to the input broker if not provided.
Just set it to another broker if you want to send the notifications
elsewhere.

The **post_exchange** must be set by the user. This is the exchange under
which the notifications will be posted.

The user can provide an **on_post** script. Just before the message gets
publish to the **post_broker** and under the **post_exchange**, the 
**on_post** script is called... with the **sr_winnow** class instance as argument.
The script can perform whatever you want... if it returns False, the message will not 
bepublished. If True, the program will continue processing from there.  

SEE ALSO
========

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcements.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`dd_subscribe(1) <dd_subscribe.1.html>`_ - the http-only download client.
