
=========
 SR_Poll
=========

------------------------------------------
Poll products from a remote server
------------------------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite


SYNOPSIS
========

**sr_poll** configfile foreground|start|stop|restart|reload|status

DESCRIPTION
===========

**sr_poll** is a component that connects to a remote server to 
check in various directories for some files. When a file is
present, modified or created in the remote directory, the program will
notify about the new product.

The notification protocol is defined here `sr_post(7) <sr_post.7.html>`_

**sr_poll** connects to a *broker*.  Every *sleep* seconds, it connects to 
a *destination* (sftp, ftp, ftps). For each of the *directory* defined, it lists
the contents. When a file matches a pattern given by *accept*, **sr_poll** builds
a notification for that product and sends it to the *broker*. The matching content 
of the *directory* is kept in a file for reference. Should a matching file be changed,
or created at a later iteration, a new notification is sent.

**sr_poll** can be used to acquire remote files in conjunction with an `sr_sarra(1) <sr_sarra.1.html>`_  
subscribed to the posted notifications, to download and repost them from a data pump.

The **sr_poll** command takes two argument: a configuration file described below,
followed by an action start|stop|restart|reload|status... 

CONFIGURATION
=============

In general, the options for this component are described by the
`sr_config(7) <sr_config.7.html>`_  page which should be read first. 
It fully explains the option configuration language, and how to find 
the option settings.

CREDENTIAL OPTIONS
------------------

The broker option sets all the credential information to connect to the  **RabbitMQ** server

- **broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::
      (default: amqp://anonymous:anonymous@dd.weather.gc.ca/ ) 

All sr_ tools store all sensitive authentication info is stored in the credentials file.
Passwords for SFTP, AMQP, and HTTP accounts are stored in URL´s there, as well as other pointers
to thins such as private keys, or FTP modes.

For more details, see: `sr_config(7) <sr_config.7.html/#credentials>`_


VIP, INTERFACE, INSTANCE
------------------------

As only one instance of sr_poll that should be used for each configuration,
the *instances* option is forced to 1. It also behaves as a singleton: **sr_poll** perform 
sr_poll is often configured on multiple servers, and have the posting occur only from 
whichever one owns the virtual IP address, at a given time.  Its task if invoked on a 
server where the ip *vip* from an *interface* is present...
If not, **sr_poll** will sleep.  When asleep, it will wakeup 
on the server every *sleep* seconds, to update its reference file and be perhaps
take over the work.

**vip       <ip>         (None)**
**interface <string>     (None)**


When these options are omitted, sr_poll is always active.



DESTINATION OPTIONS
-------------------

The destination option specify what is needed to connect to the remote server 

**destination protocol://<user>@<server>[:port]**

::
      (default: None and it is mandatory to set it ) 

The *destination* should be set with the minimum required information...
**sr_poll**  uses *destination* setting not only when polling, but also
in the sr_post messages produced.

For example, the user can set :

**destination ftp://myself@myserver**

And complete the needed information in the credentials file with the line  :

**ftp://myself:mypassword@myserver:2121  passive,binary**


POLLING SPECIFICATIONS
----------------------

These options set what files the user wants to be notified for and where
 it will be placed, and under which name.

- **filename  <option>         (optional)** 
- **directory <path>           (default: .)** 
- **accept    <regexp pattern> [rename=] (must be set)** 
- **reject    <regexp pattern> (optional)** 

The option *filename* can be used to set a global rename to the products.
Ex.:

**filename  rename=/naefs/grib2/**

For all notification created, the *rename* option would be set to '/naefs/grib2/filename'
because I specified a directory (ends with /)

The option *directory*  defines where to get the files on the server.
Combined with  **accept** / **reject**  options, the user can select the
files of interest and their directories of residence. **get** is a synonym
for **accept** and is defined for backward compatibility.

The  **accept**  and  **reject**  options use regular expressions (regexp) to match URL.
These options are processed sequentially. 
The URL of a file that matches a  **reject**  pattern is never notified.
One that match an  **accept**  pattern is notified from its residing directory.
Again a *rename*  can be added to the *accept* option... matching products
for that *accept* option would get renamed as described... unless the *accept* matches
one file, the *rename* option should describe a directory.

The directory can have some patterns. These supported patterns concern date/time .
They are fixed... 

**${YYYY}         current year**
**${MM}           current month**
**${JJJ}          current julian**
**${YYYYMMDD}     current date**

**${YYYY-1D}      current year   - 1 day**
**${MM-1D}        current month  - 1 day**
**${JJJ-1D}       current julian - 1 day**
**${YYYYMMDD-1D}  current date   - 1 day**

::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*

        directory /mylocaldirectory/${YYYYMMDD}/mydailies
        accept    .*observations.*



POSTING SPECIFICATIONS
----------------------

These options set what files the user wants to be notified for and where
**sr_poll** polls the availability of file on a remote server by creating
an announcment for it.  Subscribers use `sr_subscribe <sr_subscribe.1.html>`_  
to consume the announcement and download the file (or **sr_sarra**).
To make files available to subscribers, **sr_poll** sends the announcements to
an AMQP server, also called a broker.  Format of argument to the *broker* option:: 

       [amqp|amqps]://[user[:password]@]host[:port][/vhost]

The announcement will have its url built from the *destination* option, with
the product's path (*directory*/"matched file").  There is one post per file.
The file's size is taken from the directory "ls"... but it's checksum cannot
be determined, so the "sum" header in the posting is set to "0,0."

By default, sr_poll sends its post message to the broker with default exchange 
is the prefix *xs_* followed by the broker username. The *broker* is mandatory.
It can be given incomplete if, it is well defined in the credentials.conf file.

Refer to `sr_post(1) <sr_post.1.html>`_ - to understand the complete notification process.
Refer to `sr_post(7) <sr_post.7.html>`_ - to understand the complete notification format.

Here it is important to say that : 

The *sum=0,0* is used because no checksum computation was performed... 

The *parts=1,fsiz,1,0,0* is used and the file's size is taken from the ls of the file.
Under **sr_sarra** these fields could be reset. 

.. note::
  **FIXME  recompute_checksum in sr_sarra is available ... but reset filesize does not exist**


POSTING OPTIONS
===============

To notify about files available **sr_poll**
sends the announcements to an AMQP server, also called a broker.
The options are :

**[-b|--broker <broker>]**

  the broker to which the post is sent.


**[-ex|--exchange <exchange>]**

  By default, the exchange used is *xs_*"broker_username".
  This exchange must be previously created on broker by its administrator.
  The default can be overwritten with this *exchange* option.

**[-f|--flow <string>]**

  An arbitrary label that allows the user to identify a specific flow.
  The flow string is sets in the amqp message header.  By default, there is no flow.

**[-rn|--rename <path>]**

  With the *rename*  option, the user can suggest a destination path to its files. If the given
  path ends with '/' it suggests a directory path...  If it doesn't, the option specifies a file renaming.
  In this case, the *directory, accept/reject* combination should target only one file.

**[-tp|--topic_prefix <key>]**

  *Not usually used*
  By default, the topic is made of the default topic_prefix : version *V02*, an action *post*,
  followed by the default subtopic: the file path separated with dots (dot being the topic separator for amqp).
  You can overwrite the topic_prefix by setting this option.

**[-sub|--subtopic <key>]**

The subtopic default can be overwritten with the *subtopic* option.
The default being the file's path with '/' replaced by '.'


ADVANCED FEATURES
-----------------

There are ways to insert scripts into the flow of messages and file downloads:
Should you want to implement tasks in various part of the execution of the program:

- **do_poll     <script>        (default: None)** 
- **on_post     <script>        (default: None)** 

A do_nothing.py script for **on_post** could be:

class Transformer(object): 
      def __init__(self):
          pass

      def perform(self,parent):
          logger = parent.logger

          logger.info("I have no effect but adding this log line")

          return True

transformer  = Transformer()
self.on_post = transformer.perform

The only arguments the script receives it **parent**, which is an instance of
the **sr_poll** class

The **do_poll** script could be written to support other protocol than
ftp,ftps,sftp.  Again this script would be responsible to determine 
what to do under its protocol with the various options **destination**,
**directory**, **accept(get)/reject** and should it determine to post a
file, it would need to build its url, partstr, sumstr and  use

**parent.poster.post(parent.exchange,url,parent.to_clusters, \**
**                   partstr,sumstr,rename,remote_file)**

to post the message (and trigger **on_post** if provided)


DEVELOPER SPECIFIC OPTIONS
==========================

**[-debug|--debug]**

Active if *-debug|--debug* appears in the command line... or
*debug* is set to True in the configuration file used.


SEE ALSO
--------

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
 
