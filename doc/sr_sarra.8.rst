
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

**sr_sarra** configfile start|stop|restart|reload|status

DESCRIPTION
===========

**sr_sarra** is a program that Subscribes to file notifications, 
Acquires the files and ReAnnounces them at their new locations.

The notification protocol is defined here `sr_post(7) <sr_post.7.html>`_

**sr_sarra** connects to a *source_broker* (often the same as the remote file server 
itself) and subscribes to the notifications of interest. It uses the notification 
information to download the file on the local server its running on. 
After, it produces a new notification for the local file on a broker (usually on the local server).

**sr_sarra** can be used to acquire files from `sr_post(1) <sr_post.1.html>`_
or `sr_watch(1) <sr_watch.1.html>`_  or to reproduce a web-accessible folders (WAF),
that announce its' products.

The **sr_sarra** command takes two argument: a configuration file described below,
followed by an action start|stop|restart|reload|status... (self described).

CONFIGURATION
=============

Options are placed in the configuration file, one per line, of the form: 

**option <value>** 

Comment lines begins with **#**. 
Empty lines are skipped.
For example::

  **debug true**

would be a demonstration of setting the option to enable more verbose logging.
The configuration default for all sr_* commands is stored in 
the ~/.config/sarra/default.conf file, and while the name given on the command 
line may be a file name specified as a relative or absolute path, sr_sarra 
will also look in the ~/.config/sarra/sarra directory for a file 
named *config.conf*  The configuration in specific file always overrides
the default, and the command line overrides any configuration file.


INSTANCES
---------

It is possible that one instance of sr_sarra using a certain config
is not enough to process & download all available notifications.

**instances      <integer>     (default:1)**

Invoking the command::

  sr_sarra "configname" start 

will result in launching N instances of sr_sarra using that config.
In the ~/.cache/sarra directory, a number of runtime files are created::

  A .sr_sarra_configname_$instance.pid is created, containing the PID  of $instance process.
  A sr_sarra_configname_$instance.log  is created as a log of $instance process.

The logs can be written in another directory than the default one with option :

**log            <directory logpath>  (default:~/.cache/sarra/log)**


.. NOTE:: 
  FIXME: standard installation/setup explanations ...



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

QUEUE BINDINGS OPTIONS
----------------------

First, the program needs to set all the rabbitmq configurations for a source broker.
These options define which messages (URL notifications) the program receives:

- **exchange      <name>         (MANDATORY)** 
- **topic_prefix  <name>         (default: v02.post)**
- **subtopic      <amqp pattern> (default: #)**

The **exchange** is mandatory.

If **sr_sarra** is to be used to get products from a source 
(**sr_post**, **sr_watch**, **sr_poll**)  then the exchange would
be name 'xs\_'SourceUserName.  SourceUserName is the amqp username the source
uses to announce his products.

If **sr_sarra** is to be used to dessiminate products from another pump
then the exchange would usially be  'xpublic'.

topic_prefix is primarily of interest during protocol version transitions,
where one wishes to specify a non-default protocol version of messages to subscribe to. 

To give a correct value to the subtopic, browse the remote server and
write down the directory of interest separated by a dot
as follow:

 **subtopic  directory1.*.subdirectory3.*.subdirectory5.#** 

::

 where:  
       *                replaces a directory name 
       #                stands for the remaining possibilities

The concatenation of the topic_prefix + . + subtopic gives the AMQP topic
One has the choice of filtering using  **topic**  with only AMQP's limited 
wildcarding. 

BROKER LOGGING OPTIONS
----------------------

 - **log_exchange     <nane>   (MANDATORY)**

The state and actions performed with the messages/products of the broker
are logged back to it again through AMQP LOG MESSAGES.  When the broker
pulls products from sources and announces the products on himself, the
**log_exchange** should be set to 'xlog'.  In a broker to broker dessimination 
this option should be set to 'xs\_'brokerUserName.


QUEUE SETTING OPTIONS
---------------------

 - **durable      <boolean>         (default: False)** 
 - **expire       <minutes>         (default: None)**
 - **message-ttl  <minutes>         (default: None)**
 - **queue_share  <boolean>         (default: True)**

These options (except for queue_share)  are all AMQP queue attributes.
The queue's name is automatically build by the program. The name has
the form :  q\_'brokerUsername'.sr_sarra.'config_name'
It is easier to have this fix name when it is time to determine if 
the program such a config on that broker has a problem.
A program running several instances must set **queue_share** to True


MESSAGE SELECTION OPTIONS
-------------------------

 - **accept        <regexp pattern> (default: False)** 
 - **reject        <regexp pattern> (default: False)** 
 - **source_from_exchange <boolean> (default: False)** 
 - **on_message            <script> (default: None)** 

One has the choice of filtering using  **subtopic**  with only AMQP's limited 
wildcarding, or the more powerful regular expression based  **accept/reject**  
mechanisms described below.  The difference being that the AMQP filtering is 
applied by the broker itself, saving the notices from being delivered to the 
client at all. The  **accept/reject**  patterns apply to messages sent by the 
broker to the subscriber.  In other words,  **accept/reject**  are client 
side filters, whereas  **subtopic**  is server side filtering.  

It is best practice to use server side filtering to reduce the number of 
announcements sent to the client to a small superset of what is relevant, and 
perform only a fine-tuning with the client side mechanisms, saving bandwidth 
and processing for all.

**sr_sarra** checks, in the received message, the destination clusters. A 
message without this information in the header is discarted as incorrect.  It 
compares it to his cluster name, his cluster_alias list, and his gateway list 
(options CLUSTER,cluster_alias and gateway_for set in default.conf).  If the 
message was not designated to be process by this instance, the message is 
discarded. 

All messages should contain the entry 'source'in the message.headers. But 
this restriction does not apply for suppliers (**sr_post**,**sr_watch**). In 
this case, **sr_sarra** would be used with option **source_from_exchange**  
and if the message is processed and published, its 'source' would be set to 
the suppliers broker's username.

The user can provide an **on_message** script. When a message is accepted up 
to this level of verification, the **on_message** script is called... with 
the **sr_sarra** class instance as argument.  The script can perform whatever 
you want... if it returns False, the processing of the message will stop 
there. If True, the program will continue processing from there.  

DESTINATION OPTIONS
-------------------

Theses options set where and how the program will place the files to be 
downloaded.

- **document_root <path>           (default: .)** 
- **mirror        <boolean>        (default: true)** 
- **strip         <integer>        (default: 0)** 
- **overwrite     <boolean>        (default: true)** 
- **inplace       <boolean>        (default: true)** 
- **do_download   <script>         (default: None)**
- **on_file       <script>         (default: None)**

The **document_root** sets a directory the root of the download tree.
This directory never appears in the newly created amqp notifications.

By default, **mirror** option is True, the default path for a file is :

path = document_root + 'notification filepath'

**sr_sarra** expects the notification filepath to start with YYYYMMDD/sourceid.
The user will set **mirror** to False, if it is not the case. The path
for the file becomes :

path = document_root + YYYYMMDD/sourceid + 'notification_filepath'

The **strip** option defines the number of directories to remove
from the path... This applies for subdirectories starting after the document_root
If the number of directories is greated than the subdirectories the path would
become :

path = document_root + filename

Once the path is defined in the program, if the **overwrite** option is set to 
True, the program checks if the file is already there. If it is, it computes 
the checksum on it according to the notification'settings. If the local file 
checksum matches the one of the notification, the file is not downloaded, the 
incoming notification is acknowledge, and the file is not announced. If the 
file is not there, or the checksum differs, the file is overwritten and a 
new notification is sent to the destination broker.

The **inplace** option defaults to True. The program receiving notifications 
of file parts, will put these parts inplace in the file in an orderly fashion. 
Each part, once inserted in the file, is announced to subscribers.

The **do_download** option defaults to None. If used it defines a script that 
will be called when an unsupported protocol is received in a message. The user 
can use all the **sr_sarra** class elements including the message in order to 
set the proper download of the product.

The **on_file** option defaults to None. If used it defines a script that will 
be called once the file is downloaded. The user can do whatever he wants with 
the downloaded file perform checks... etc. Again it should return True to tell 
the program to resume processing.  If false, it will continue to the next 
message.

.. NOTE:: 
  - FIXME: destfn script  : should it support a destination script
  - FIXME: renamer script : should it support a file renamer script


CREDENTIALS 
-----------

Ther username and password or keys used to access servers are credentials.
The confidential parts of credentials are stored only in ~/.conf/sarra/credentials.conf.  This includes all download, upload, or broker passwords and settings 
needed by the various configurations.  The format is one entry per line.  Examples:

- **amqp://user1:password1@host/**
- **amqps://user2:password2@host:5671/dev**

- **http://user3:password3@host**
- **https://user4:password4@host:8282**

- **sftp://user5:password5@host**
- **sftp://user6:password6@host:22  ssh_keyfile=/users/local/.ssh/id_dsa**

- **ftp://user7:password7@host  passive,binary**
- **ftp://user8:password8@host:2121  active,ascii**

In other configuration files or on the command line, the url simply lacks the 
password or key specification.  The url given in the other files is looked 
up in credentials.conf. 
 
OUTPUT NOTIFICATION OPTIONS
---------------------------

The program needs to set all the rabbitmq configurations for an output broker.

The post_broker option sets all the credential information to connect to the
  output **RabbitMQ** server 

**post_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::
      FIXME: do not understand following parenthetical
      (default: manager defined in default.conf) 

Once connected to the source AMQP broker, the program builds notifications after
the download of a file has occured. To build the notification and send it to
the next hop broker, the user sets these options :

 - **url               <url>          (MANDATORY)**
 - **recompute_chksum  <boolean>      (False)** 
 - **post_exchange     <name>         (default: xpublic)** 
 - **on_post           <script>       (default: None)** 

The **url** option sets how to get the file... it defines the protocol,
host, port, and optionally, the credentials. It is a good practice not to 
notify the credentials and separately inform the consumers about it.

If **recompute_chksum** is set to True, the checksum will be recomputed
on file download and value will overwrite the one from the incoming amqp 
message.  If a file is repeatedly modified, the download may occur after the 
file is overwritten but with its old notification... resulting in a checksum 
mismatch and potential looping in a network of pumps.

.. NOTE::
   FIXME:  this is pathological case.  It ignores the incoming checksum.
   so data is forwarded in spite of checksum mismatch. We should think more about this.
   not sure this option is a good thing.

The **post_exchange** option set under which exchange the new notification 
will be posted.  Im most cases it is 'xpublic'.

Whenever a publish happens for a product, a user can set to trigger a script.
The option **on_post** would be used to do such a setup.


SEE ALSO
========

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcements.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`dd_subscribe(1) <dd_subscribe.1.html>`_ - the http-only download client.
