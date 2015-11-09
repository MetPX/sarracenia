
=========
 SR_Sarra
=========

------------------------------------------
Subscribe, Acquire and ReAnnounce Products
------------------------------------------

:Manual section: 8
:Date: Oct 2015
:Version: 0.0.1
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
itself) and subscribes to the notifications of interest. It uses the 
notification information to download the file on the local server its running on. 
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


INSTANCES
---------

It is possible that one instance of sr_sarra using a certain config
is not enough to process & download all available notifications.

**instances      <integer>     (default:1)**

sr_sarra "configname" start   will fork  N instances of sr_sarra using that config.
.sr_sarra_configname_$instance.pid  are created and contain the PID  of $instance process.
sr_sarra_configname_$instance.log  are created and contain the logs of $instance process.

The logs can be written in another directory than the current one with option :

**log            <directory logpath>  (default:$PWD)**


.. NOTE:: 
  FIXME: standard installation/setup explanations ...
  FIXME: a standard place where all configs ?
  FIXME: a standard place where all the logs ?
  FIXME: a standard place where all the pid files ?
  FIXME: a sr process starting all sarra configs of various kind.



SOURCE NOTIFICATION OPTIONS
---------------------------

First, the program needs to set all the rabbitmq configurations for a source broker.
The source_broker option sets all the credential information to connect to the **AMQP** server 

**source_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqp://guest:guest@localhost/ ) 


Once connected to an AMQP broker, the user needs to create a queue and bind it
to an exchange.  These options define which messages (URL notifications) the program receives:

 - **source_exchange      <name>         (default: amq.topic)** 
 - **source_topic         <amqp pattern> (default: v02.post.#)**
 - **queue_name           <name>         (default: sr_sarra.config_name)** 

.. NOTE::
  FIXME: queue_name is sr_sarra.config_name? is that the file that contains the queue name?
  FIXME: probably should be "queue_info_file" ? is there other stuff in there other than the name?
  FIXME: queue_name is supposed to be q_guest (assuming default auth.)

To give a correct value to the subtopic, browse the remote server and
write down v02.post plus the directory of interest separated by a dot
as follow:

 **source_topic  v02.post.directory1.*.subdirectory3.*.subdirectory5.#** 

::

 where:  
       *                replaces a directory name 
       #                stands for the remaining possibilities

One has the choice of filtering using  **source_topic**  with only AMQP's limited 
wildcarding. 

.. NOTE:: 
  FIXME: no mention of the use of exchange argument.
  FIXME: defaults should be wiser or None...
  FIXME: queue settings : no support in code default auto_delete false,durable false
  FIXME: one source_topic only : no support for a list in code
  FIXME: option source_subtopic,source_topic_prefix : no support in code


DESTINATION OPTIONS
-------------------

Theses options set where and how the program will place the files to be downloaded.

::

**document_root <path>           (default: .)** 
**mirror        <boolean>        (default: true)** 
**strip         <integer>        (default: 0)** 
**overwrite     <boolean>        (default: true)** 
**inplace       <boolean>        (default: true)** 

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


Once the path is defined in the program, if the **overwrite** option is set to True,'
the program checks if the file is already there. If it is, it computes the checksum
on it according to the notification'settings. If the local file checksum matches the
one of the notification, the file is not downloaded, the incoming notification is 
acknowledge, and the file is not announced. If the file is not there, or the checksum
differs, the file is overwritten and a new notification is sent to the destination broker.

The **inplace** option defaults to True. The program receiving notifications of file 
parts, will put these parts inplace in the file in an orderly fashion. Each parts,
once inserted in the file, is notified to the destination broker.


.. NOTE:: 
  - FIXME: lock option    : should it support file locking (.tmp, . prefix) ?
  - FIXME: destfn script  : should it support a destination script
  - FIXME: renamer script : should it support a file renamer script
  - FIXME: working_directory ? .. should this be a config option to name where the queue_name, and other? state files live?



DOWNLOAD CREDENTIALS 
--------------------

**ssh_keyfile  <filepath> (set if needed for sftp downloads)** 

.. NOTE::
  FIXME: usage of ~/.conf/sarra/credentials.conf to be coded
  support of various ftp/sftp... etc credentials at the same time
  much easier for users and less restrictions on notifications


OUTPUT NOTIFICATION OPTIONS
---------------------------

The program needs to set all the rabbitmq configurations for an output broker.

The broker option sets all the credential information to connect to the
  output **RabbitMQ** server 

**broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqp://guest:guest@localhost/ ) 

Once connected to the source AMQP broker, the program builds notifications after
the download of a file has occured. To build the notification and send it to
the next hop broker, the user sets these options :

 - **url               <url>          (needs to be set)**
 - **recompute_chksum  <boolean>      (False)** 
 - **exchange          <name>         (default: amq.topic)** 

The **url** option sets how to get the file... it defines the protocol,
host, port, and optionally, the credentials. It is a good practice not to 
notify the credentials and separately inform the consumers about it.

If **recompute_chksum** is set to True, the checksum will be recomputed
on file download and value will overwrite the one from the incoming amqp message.  
If a file is repeatedly modified, the download may occur after the file is overwritten
but with its old notification... resulting in a checksum mismatch and potential
looping in a network of pumps.

.. NOTE::
   FIXME:  this is pathological case.  It ignores the incoming checksum.
   so data is forwarded in spite of checksum mismatch. We should think more about this.
   not sure this option is a good thing.


The **exchange** option set under which exchange the new notification will be posted.


QUALITY ASSURANCE
-----------------

These options can be used for quality assurance.

::

**message_validation_script    <script_path> (used if set)** 
**file_validation_script       <script_path> (used if set)** 

The  **message_validation_script**  receives a sr_message instance
containing all the amqp information. The user can write checks on
any of the sr_message values.  Should it not comply to the checks,
a log message (and an amqp log message) will posted, the message will be
acknowledged with out any further processing...  Only valid messages
will be processed further. 

.. NOTE:: 
  FIXME: where should we put these scripts
  FIXME: details missing in doc on returned values

The return values of this script are :
OK,code,message    <boolean,integer,string>   accepted?,error code, error message


The  **file_validation_script**  receives the file path.
The user may run any kind of validation on the path.
Should the file not comply to the checks, a log message (and an amqp log message) will posted,
the message will be acknowledged without any further processing... 
Only valid files are reannounced.

.. NOTE:: 
  FIXME: where should we put these scripts
  FIXME: what should we do with rejected files ... validation script removes it ?
  FIXME: details missing in doc on returned values

The return values of this script are :
OK,code,message    <boolean,integer,string>   accepted?,error code, error message



.. NOTE:: 
  FIXME: accept/reject should be coded... and documented
  not sure if we need accept/reject... interesting...
  work on other stuff first...

SEE ALSO
========

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcements.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`dd_subscribe(1) <dd_subscribe.1.html>`_ - the http-only download client.
