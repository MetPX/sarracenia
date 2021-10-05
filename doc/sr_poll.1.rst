
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

.. contents::

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

The notification protocol is defined here `sr_post(7) <sr_post.7.rst>`_

**sr_poll** connects to a *broker*.  Every *sleep* seconds, it connects to
a *destination* (sftp, ftp, ftps). For each of the *directory* defined, it lists
the contents. When a file matches a pattern given by *accept*, **sr_poll** builds
a notification for that product and sends it to the *broker*. The matching content
of the *directory* is kept in a file for reference. Should a matching file be changed,
or created at a later iteration, a new notification is sent.

**sr_poll** can be used to acquire remote files in conjunction with an `sr_sarra(8) <sr_sarra.8.rst>`_
subscribed to the posted notifications, to download and repost them from a data pump.

The **sr_poll** command takes two argument: a configuration file described below,
followed by an action start|stop|restart|reload|status...

The actions **cleanup**, **declare**, **setup** can be used to manage resources on
the rabbitmq server. The resources are either queues or exchanges. **declare** creates
the resources. **setup** creates and additionally does the bindings of queues.


CONFIGURATION
=============

In general, the options for this component are described by the
`sr_subscribe(1) <sr_subscribe.1.rst>`__  page which should be read first.
It fully explains the option configuration language, and how to find
the option settings.

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
- **poll_without_vip  <boolean> (default: True)**
- **file_time_limit <integer>   (default 60d)**
- **destination_timezone        (default 'UTC')**

The option *filename* can be used to set a global rename to the products.
Ex.:

**filename  rename=/naefs/grib2/**

For all posts created, the *rename* option would be set to '/naefs/grib2/filename'
because I specified a directory (path that ends with /).

The option *directory*  defines where to get the files on the server.
Combined with  **accept** / **reject**  options, the user can select the
files of interest and their directories of residence. 

The  **accept**  and  **reject**  options use regular expressions (regexp) to match URL.
These options are processed sequentially.
The URL of a file that matches a  **reject**  pattern is not published.
Files matching an  **accept**  pattern are published.
Again a *rename*  can be added to the *accept* option... matching products
for that *accept* option would get renamed as described... unless the *accept* matches
one file, the *rename* option should describe a directory into which the files
will be placed (prepending instead of replacing the file name).

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
(on an ls output that looks like: ---r-----, like a chmod 040 <file> command).
The **chmod** options specifies a mask, that is the permissions must be 
at least what is specified.  

As with all other components, the **vip** option can be used to indicate
that a poll should be active on only a single node in a cluster. Note that
as the poll will maintain state (such as the list of files that exist on the
remote hosts), by default, the vip will only keep the component from posting, 
but the actual poll will still happen, which can involve a high an unnecessary
load on the nodes that do not have the vip.

To have the nodes which do not have the vip perform no work, for example
if the corresponding sarra components have *delete* set, so that no state
persistence is needed in the poll, set the **poll_without_vip** option 
to *False* (or *off*). This reduces overhead forty-fold in some measured 
cases.  

By default, files that are more than 2 months are not posted. However, this can be modified to any specified time limit in the configurations by using the option *file_time_limit <integer>*. By default, seconds are used, but one can specify hours, days or weeks with 1, 1h, 1d, 1w respectively. One can also specify the *destination_timezone '<TIMEZONE>'* of such files by adding this option in the configurations in order convert all files to 'UTC'. By default, the destination_timezone is set to 'UTC' but one can specify another timezone in the format: '<TIMEZONE>' such as 'PST' or 'EST'.

POSTING SPECIFICATIONS
----------------------

These options set what files the user wants to be notified for and where
**sr_poll** polls the availability of file on a remote server by creating
an announcment for it.  Subscribers use `sr_subscribe <sr_subscribe.1.rst>`_
to consume the announcement and download the file (or **sr_sarra**).
To make files available to subscribers, **sr_poll** sends the announcements to
an AMQP server, also called a broker.  Format of argument to the *broker* option::

       [amqp|amqps]://[user[:password]@]host[:port][/vhost]

The announcement will have its url built from the *destination* option, with
the product's path (*directory*/"matched file").  There is one post per file.
The file's size is taken from the directory "ls"... but its checksum cannot
be determined, so the "sum" header in the posting is set to "0,0."

By default, sr_poll sends its post message to the broker with default exchange
(the prefix *xs_* followed by the broker username). The *broker* is mandatory.
It can be given incomplete if it is well defined in the credentials.conf file.

Refer to `sr_post(1) <sr_post.1.rst>`_ - to understand the complete notification process.
Refer to `sr_post(7) <sr_post.7.rst>`_ - to understand the complete notification format.

Here it is important to say that :

The *sum=0,0* is used because no checksum computation was performed. It is often
desirable to use the *sum=z,s* to have downloaders calculate a useful checksum as
they download for use by others.

The *parts=1,fsiz,1,0,0* is used and the file's size is taken from the ls of the file.
Under **sr_sarra** these fields could be reset.


ADVANCED FEATURES
-----------------

There are ways to insert scripts into the flow of messages and file downloads:
Should you want to implement tasks in various part of the execution of the program:

- **on_line      <script>        (default: line_mode)**
- **do_poll      <script>        (default: None)**
- **on_post      <script>        (default: None)**
- **on_html_page <script>        (default: html_page)**

The **on_line** plugin gives scripts that can read each line of an 'ls' on the polled
site, to interpret it further. It returns True if the line should be further processed,
or False to reject it.  By default, there is a line_mode plugin included with the package
which implements the comparison of file permissions on the remote server against
the **chmod** mask.

If the poll fetches using the http protocol, the 'ls' like entries must be derived from
an html page. The default plugin **html_page** provided with the package, gives an idea of
how to parse such a page into a python directory manageable by **sr_poll**.

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

The only arguments the script receives is **parent**, which is an instance of
the **sr_poll** class.

The **do_poll** script could be written to support other protocols than
ftp,ftps,sftp.  Again this script would be responsible to determine
what to do under its protocol with the various options **destination**,
**directory**, and should it determine to post a
file, it would need to build its url, partstr, sumstr and  use

**parent.poster.post(parent.exchange,url,parent.to_clusters, \**
**                   partstr,sumstr,rename,remote_file)**

to post the message, applying accept/reject clauses and triggering on_post processing. 


DEPRECATED
==========

The *get* option is a deprecated synonym for accept.  Please use *accept*.

**get    <regexp pattern> [rename=] (must be set)**


SEE ALSO
--------

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.rst>`_ - the format of report messages.

`sr_report(1) <sr_report.1.rst>`_ - process report messages.

`sr_post(1) <sr_post.1.rst>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.rst>`_ - the format of announcement messages.

`sr_sarra(8) <sr_sarra.8.rst>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.rst>`_ - the directory watching daemon.

`https://github.com/MetPX/ <https://github.com/MetPX/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
