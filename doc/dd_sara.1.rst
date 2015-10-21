
=========
 DD_Sara
=========

------------------------------------------------
Subscribe acquire and reannounce products
------------------------------------------------

:Manual section: 1 
:Date: Oct 2015
:Version: 0.0.1
:Manual group: MetPx Sarracenia Suite


SYNOPSIS
========

**dd_sara** configfile start|stop|restart|reload|status

DESCRIPTION
===========

**dd_sara** is a program that listens to file notifications, 
acquire the files and reannounce them at their new locations.

The notification protocol is defined here `dd_post(7) <dd_post.7.html>`_

**dd_sara** connects to a *source_broker* (often the same as the remote file server 
itself) and subscribes to the notifications of interest. It uses the 
notification information to download the file on the local server its running on. 
After, it notifies the file on a broker (usually on the local server).


**dd_sara** can be used to acquire files from `dd_post(1) <dd_post.1.html>`_
or `dd_watch(1) <dd_watch.1.html>`_  or to reproduce a web-accessible folders (WAF),
that notifies its products.

The **dd_sara** command takes two argument: a configuration file described below,
followed by an action start|stop|restart|reload|status... (self described).

CONFIGURATION
=============

Options are placed in the configuration file, one per line, of the form: 

**option <value>** 

Comment lines begins with **#**. 
Empty lines are skipped.


SOURCE NOTIFICATION OPTIONS
---------------------------

First, the program needs to set all the rabbitmq configurations for a source broker.

The source_broker option sets all the credential information to connect to the
  **RabbitMQ** server <F3> 

**source_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqp://guest:guest@localhost/ ) 


Once connected to an AMQP broker, the user needs to create a queue and bind it
to an exchange.  These options define which messages (URL notifications) the program receives:

 - **source_exchange      <name>         (default: amq.topic)** 
 - **source_topic         <amqp pattern> (default: v02.post.#)**
 - **queue_name           <name>         (default: dd_sara.config_name)** 

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

**dd_sara** expects the notification filepath to start with YYYYMMDD/sourceid.
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
  FIXME: lock option    : should it support file locking (.tmp, . prefix) ?
  FIXME: destfn script  : should it support a destination script
  FIXME: renamer script : should it support a file renamer script


DOWNLOAD CREDENTIALS 
--------------------

**ssh_keyfile  <filepath> (set if needed for sftp downloads)** 

.. NOTE::
  FIXME: usage of ~/.conf/sara/credentials.conf to be coded
         supports of various ftp/sftp... etc credentials at the same time
         *** much more easy for users and less restrictions on notifications


OUTPUT NOTIFICATION OPTIONS
---------------------------

The program needs to set all the rabbitmq configurations for an output broker.

The broker option sets all the credential information to connect to the
  output **RabbitMQ** server <F3> 

**broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqp://guest:guest@localhost/ ) 

Once connected to an AMQP broker, the program will build the notifications after
the download of the file has occured. To build the notification and send it to
the broker the user sets these options :

 - **url               <url>          (needs to be set)**
 - **recompute_chksum  <boolean>      (False)** 
 - **exchange          <name>         (default: amq.topic)** 

The **url** option sets how to get the file... it defined the protocol,
host, port, and optionnaly the credentials. It is a good practice not to 
notify the credentials and  inform the end users about it.

If **recompute_chksum** is set to True, the checksum will be recomputed
on the download file and the resulting value will overwrite the one in the
amqp message.  This might be usefull if a file gets modified quickly keeping
the same name... The download of the file may occur after the file is overwritten
but with its old notification... If the notification contains inexact information
about the file, this could lead to message/download looping.

The **exchange** option set under which exchange the new notification will be posted.


QUALITY INSURANCE
-----------------

Theses options can be used for quality insurance.

::

**message_validation_script    <script_path> (used if set)** 
**file_validation_script       <script_path> (used if set)** 

The  **message_validation_script**  receives a dd_message instance
containing all the amqp informations. The user can write checks on
any of the dd_message value.  Should it not comply to the checks,
a log message (and an amqp log message) will posted, the message will be
 acknowledge with out any further processing...  Only valid messages
will be treated. 

.. NOTE:: 
  FIXME: where should we put these scripts
  FIXME: details missing in doc on returned values
The return values of this script are :
OK,code,message    <boolean,integer,string>   accepted?,error code, error message


The  **file_validation_script**  receives the file path.
The user run any kind of file validation on the path.
Should the file not comply to the checks... 
a log message (and an amqp log message) will posted,
the message will be acknowledge with out any further processing... 
Only valid files are reannounce.

.. NOTE:: 
  FIXME: where should we put these scripts
  FIXME: what should we do with rejected files ... validation script removes it ?
  FIXME: details missing in doc on returned values
The return values of this script are :
OK,code,message    <boolean,integer,string>   accepted?,error code, error message



.. NOTE:: 
  FIXME: accept/reject should be coded... and documented
