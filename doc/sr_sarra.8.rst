
=========
 SR_Sarra
=========

------------------------------------------
Subscribe, Acquire and ReAnnounce Products
------------------------------------------

:Manual section: 8
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite


SYNOPSIS
========

**sr_sarra** configfile foreground|start|stop|restart|reload|status

DESCRIPTION
===========

**sr_sarra** is a program that Subscribes to file notifications, 
Acquires the files and ReAnnounces them at their new locations.

The notification protocol is defined here `sr_post(7) <sr_post.7.html>`_

**sr_sarra** connects to a *broker* (often the same as the remote file server 
itself) and subscribes to the notifications of interest. It uses the notification 
information to download the file on the local server its running on. 
After, it produces a new notification for the local file on a broker (usually on the local server).

**sr_sarra** can be used to acquire files from `sr_post(1) <sr_post.1.html>`_
or `sr_watch(1) <sr_watch.1.html>`_  or to reproduce a web-accessible folders (WAF),
that announce its' products.

The **sr_sarra** command takes two argument: a configuration file described below,
followed by an action start|stop|restart|reload|status... (self described).

The **foreground** action is different. It would be used when building a configuration
or debugging things. It is used when the user wants to run the program and its configfile 
interactively...   The **foreground** instance is not concerned by other actions, 
but should the configured instances be running it shares the same (configured) message queue.
The user would stop using the **foreground** instance by simply pressing <ctrl-c> on linux 
or use other means to kill its process. 


CONFIGURATION
=============

This document focuses on detailing the program's options. We invite the reader to
read the document `sr_config(7) <sr_config.7.html>`_  first. It fully explains the
option syntax, the configuration file location, the credentials ... etc.

Standard sarracenia configuration would expect the config file to be found in :

 - linux: ~/.config/sarra/sarra/configfile.conf
 - Windows: %AppDir%/science.gc.ca/sarra/sarra, this might be:
   C:\Users\peter\AppData\Local\science.gc.ca\sarra\sarra\configfile.conf

When creating a new configuration file, the user can take advantage of executing
the program with  **--debug configfile foreground**  with a configfile.conf in
the current working directory.

The options used in the configfile are described in the next sections.


Multiple Streams
================

When executed,  the program uses the default queue name.
If it is stopped, the posted messages continue to accumulate on the 
broker in the queue.  When the program is restarted, the queue name 
is reused, and no messages are lost.

Message processing can be parallelized by running multiple instances of the program. 
The program shares the same queue. The messages will be distributed between instances.
Simply launch the program with option instances set to an integer greater than 1.


Consuming Options
=================

Setting the source broker :

**broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

Setting the queue on broker :

- **queue_name    <name>         (default: q_<brokerUser>.<programName>.<configName>)** 
- **durable       <boolean>      (default: False)** 
- **expire        <minutes>      (default: 10080 mins = 1 week)** 
- **message-ttl   <minutes>      (default: None)** 
- **prefetch      <N>            (default: 1)** 
- **reset         <boolean>      (default: False)** 

Setting the bindings on the queue :

 - **exchange      <name>         (default: xpublic)** 
 - **topic_prefix  <amqp pattern> (default: varies -- developer option)** 
 - **subtopic      <amqp pattern> (subtopic need to be set)** 

Using regular expression filtering messages

- **accept       <regexp pattern> (optional)** 
- **reject       <regexp pattern> (optional)** 
- **accept_unmatch      <boolean> (default: False)** 

Running a plugin on selected messages

- **on_message      <script_name> (default: msg_log)** 


Specific consuming requirements
--------------------------------

To consume messages, the mandatory options are:
 **broker**, **exchange**. The default bindings is
all post messages from that exchange.

The program will not process message that :

1- has no source      (message.headers['source'])
2- has no origin      (message.headers['from_cluster'])
3- has no destination (message.headers['to_clusters'])
4- the to_clusters destination list has no match with
   this pump's **cluster,cluster_aliases,gateway_for**  options


Important note 1:

If the messages are posted directly from a source,
the exchange used is 'xs_<brokerSourceUsername>'.
Such message does not contain a source nor an origin cluster.
The user must set this option to **True**:

- **source_from_exchange  <boolean> (default: False)** 

Upon reception, the program will set these values
in the parent class (here cluster is the value of
option **cluster** taken from default.conf):

self.msg.headers['source']       = <brokerUser>
self.msg.headers['from_cluster'] = cluster


Important note 2:

The **on_message** plugin (if provided)  is invoked
after a product has been selected for download as
described in the next section.


LOCAL DESTINATION OPTIONS
=========================

These options set where the program downloads the file
(or the part) described by the message.

- **document_root <path>           (default: .)** 
- **mirror        <boolean>        (default: true)** 
- **strip         <integer>        (default: 0)** 
- **inplace       <boolean>        (default: true)** 

The program starts by setting the relative path
of the product straight from the message url:

**relative_path = message's url path**

If message has self.msg.headers['rename'] than :

**relative_path = message's rename path**

When **mirror** is true, we are usually in a pump to pump
configuration and we are satisfied with the message's path as is.

If **mirror** is false, it means that we need to add the sarracenia
standard   yyyymmdd/source pair in front of the relative_path

**if not mirror: relative_path = YYYYMMDD/<brokerUser>/relative_path**

Next, the **strip** option is applied, if set to N>0. The relative_path
has its N first directories removed... if N is too big, the filename
is kept.

The **document_root** sets a directory the root of the download tree.
This directory never appears in the newly created amqp notifications.
But it serves to set the absolute path of the local file (destination)

path = document_root + relative_path (after all options applied)

The **inplace** option defaults to True. The program receiving notifications 
of file parts, will put these parts inplace in the file in an orderly fashion. 
Each part, once inserted in the file, is announced to subscribers.

Depending of **inplace** and if the message was a part, the path can
change again (adding a part suffix if necessary). The resulting variables used for
the local destination to download a file (or a part) are :

self.msg.local_file   :  the local path where to download the file(part)
self.msg.local_offset :  offset position in the local file
self.msg.offset       :  offset position of the remote file
self.msg.length       :  length of file or part
self.msg.in_partfile  :  T/F file temporary in part file
self.msg.local_url    :  url for reannouncement

These variables are important to know if one wants to use an **on_message**,
**on_part** or **on_file** plugin.


DOWNLOAD OPTIONS
================

There are a few options that impact the dowload of a product:

- **delete           <boolean> (default: False)** 
- **do_download      <script>  (default: None)**
- **on_file          <script>  (default: file_log)**
- **on_part          <script>  (default: None)**
- **overwrite        <boolean> (default: False)** 
- **recompute_chksum <boolean> (default: False)** 
- **timeout          <float>   (default: None)** 
- **kbytes_ps        <int>     (default: 0)** 

Once the path is defined in the program, if the **overwrite** option is set to 
True, the program checks if the file is already there. If it is, it computes 
the checksum on it according to the notification'settings. If the local file 
checksum matches the one of the notification, the file is not downloaded, the 
incoming notification is acknowledge, and the file is not reannounced. If the 
file is not there, or the checksum differs, the file is overwritten and a 
new notification is sent to the destination broker.

.. note:: 
   FIXME: overwrite explanation is backwards, if 'overwrite' is true, it should overwrite the files
   regardless of checksum ?  PS.

If **delete** is set to True, when the product is downloaded, it is removed from
the remote server.

**timeout** when the protocol supports it, this option set 
the number of seconds to raise a TCP connect timeout. (ftp/ftps/sftp supports it)

**kbytes_ps** can be use to set a target for the download speed in Kbytes per second.
Default is 0, meaning no control over speed. (ftp/ftps/sftp supports it)


The **do_download** option defaults to None. If used it defines a script that 
will be called when an unsupported protocol is received in a message. The user 
can use all the **sr_sarra** class elements including the message in order to 
set the proper download of the product. It returns True if the download succeeded.

The **on_part** option defaults to None. If used it defines a script that will 
be called when a part is downloaded. The same ideas apply, the user
can do whatever he wants with the downloaded part... etc. Again 
it should return True to tell the program to resume processing.
If false, it will continue to the next message.

The **on_file** option defaults to file_log, which writes a downloading status message. 
If used it defines a script that will be called once the file is downloaded 
(or all its parts are inplace). The user can do whatever he wants with 
the downloaded file perform checks... etc. Again 
it returns True to tell the program to resume processing.
If it returns false, processing of the current message is stopped, and
the program skips to the next message.

For each download, the checksum is computed during transfer. If **recompute_chksum** 
is set to True, and the recomputed checksum differ from the on in the message,
the new value will overwrite the one from the incoming amqp message. 

 
OUTPUT NOTIFICATION OPTIONS
---------------------------

The program needs to set all the rabbitmq configurations for an output broker.

The post_broker option sets all the credential information to connect to the
  output **RabbitMQ** server 

**post_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

The program seeks for the **feeder** option (usually defined in default.conf)
and (if found) sets it as the default for **post_broker**. It is usually from
that account that the pump deals internally with AMQP messages.

Once connected to the source AMQP broker, the program builds notifications after
the download of a file has occured. To build the notification and send it to
the next hop broker, the user sets these options :

 - **url               <url>          (MANDATORY)**
 - **post_exchange     <name>         (default: xpublic)** 
 - **on_post           <script>       (default: None)** 

The **url** option sets how to get the file... it defines the protocol,
host, port, and optionally, the credentials. It is a good practice not to 
notify the credentials and separately inform the consumers about it.

The **post_exchange** option set under which exchange the new notification 
will be posted.  Im most cases it is 'xpublic'.

Whenever a publish happens for a product, a user can set to trigger a script.
The option **on_post** would be used to do such a setup.


SEE ALSO
========

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcements.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`dd_subscribe(1) <dd_subscribe.1.html>`_ - the http-only download client.
