
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

**sr_poll** foreground|start|stop|restart|reload|status configfile 

**sr_poll** cleanup|declare|setup configfile 


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

The actions **cleanup**, **declare**, **setup** can be used to manage resources on
the rabbitmq server. The resources are either queues or exchanges. **declare** creates
the resources. **setup** creates and additionnaly does the bindings of queues.


CONFIGURATION
=============

In general, the options for this component are described by the
`sr_subscribe(1) <sr_subscribe.1.html>`__  page which should be read first.
It fully explains the option configuration language, and how to find
the option settings.

CREDENTIAL OPTIONS
------------------

The broker option sets all the credential information to connect to the  **RabbitMQ** server

- **broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::
      (default: amqp://anonymous:anonymous@dd.weather.gc.ca/ )

All sr\_ tools store all sensitive authentication info in the credentials.conf file.
Passwords for SFTP, AMQP, and HTTP accounts are stored in URL´s there, as well as other pointers
to thins such as private keys, or FTP modes.

For more details, see: `sr_subscribe(1) <sr_subscribe.1.html#credentials>`__


VIP, INTERFACE 
--------------

sr_poll can be configured on multiple servers, where posting should occur only from
whichever one owns the virtual IP address (VIP) at a given time.  
As only one instance of sr_poll that should be used for each configuration, the *instances* option is forced to 1. 
To check that the *vip* is present on any *interface* on the server periodically::

**vip       <ip>         (None)**

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
- **chmod     <integer>        (default: 0o400)**

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

The **chmod** option allows users to specify a linux-style numeric octal
permission mask::

  chmod 040

means that a file will not be posted unless the group has read permission 
(on an ls output that looks like: ---r-----, like a chmod 040 <file> command.)
The **chmod** options specifies a mask, that is the permissions must be 
at least what is specified.  



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

**[-to_clusters|--to <csv-string>]**

  Once a messages is delivered to the first pump, the *to_clusters* option 
  suggests other pumps to which the data should be disseminated.  The default 
  value is the hostname of the broker being posted to.  Multiple pump 
  identifiers can be specified by separating the names by commas. 

**[-sub|--subtopic <key>]**

  The subtopic default can be overwritten with the *subtopic* option.
  The default being the file's path with '/' replaced by '.'

**[-tp|--topic_prefix <key>]**

  *Not usually used*
  By default, the topic is made of the default topic_prefix : version *V02*, an action *post*,
  followed by the default subtopic: the file path separated with dots (dot being the topic separator for amqp).
  You can overwrite the topic_prefix by setting this option.


ADVANCED FEATURES
-----------------

There are ways to insert scripts into the flow of messages and file downloads:
Should you want to implement tasks in various part of the execution of the program:

- **on_line      <script>        (default: line_mode)**
- **do_poll      <script>        (default: None)**
- **on_post      <script>        (default: None)**
- **on_html_page <script>        (default: html_page)**

The **on_line** plugin gives scripts that can read each line of an 'ls' on the polled
site, to interpret it further.  return True, if the line should be further processed,
or False to reject it.  by default, there is a line_mode plugin included with the package
which implements the comparison of file permission on the remote server against
the **chmod** mask.

If the poll fetches using the http protocol, the 'ls' like entries must be derived from
an html page. The default plugin **html_page** provided with the package, gives an idea
how to parse such a page into a python directory managable by **sr_poll**.

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
**directory**, and should it determine to post a
file, it would need to build its url, partstr, sumstr and  use

**parent.poster.post(parent.exchange,url,parent.to_clusters, \**
**                   partstr,sumstr,rename,remote_file)**

to post the message, applying accept/reject clauses and triggering on_post processing. 


DEVELOPER SPECIFIC OPTIONS
==========================

**[-debug|--debug]**

Active if *-debug|--debug* appears in the command line... or
*debug* is set to True in the configuration file used.

DEPRECATED
==========

The interface option used to be required with *vip*, now all interfaces are scanned.

**interface <string>     (None)**

SEE ALSO
--------

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_report(1) <sr_report.1.html>`_ - process report messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
