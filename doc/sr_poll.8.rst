
=========
 SR_Poll
=========

------------------------------------------
Poll products from a remote server
------------------------------------------

:Manual section: 8
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite


SYNOPSIS
========

**sr_poll** configfile start|stop|restart|reload|status

DESCRIPTION
===========

**sr_poll** is a program that connects onto a remote server,
checks in various directories for some files. When a file is
present, modified or created in the directory, the program will
notify that new product.

The notification protocol is defined here `sr_post(7) <sr_post.7.html>`_

**sr_poll** connects to a *broker*. Than every *sleep* seconds, it connects to 
a *destination* (sftp, ftp, ftps). For each of the *directory* defined, it lists
its content... When a file matched a pattern given by *accept*, **sr_poll** builds
a notification for that product and sends it to the *broker*. The matching content 
of the *directory* is kept in a file for reference. Should a matching file be changed,
or created at the next iteration, another notification is being sent.

**sr_poll** can be used to acquire files remote files. The notifications created can
be listen by `sr_sarra(1) <sr_sarra.1.html>`_  , downloaded and reposted from its new location.

The **sr_poll** command takes two argument: a configuration file described below,
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
line may be a file name specified as a relative or absolute path, sr_poll 
will also look in the ~/.config/sarra/poll directory for a file 
named *config.conf*  The configuration in specific file always overrides
the default, and the command line overrides any configuration file.

Invoking the command::

  sr_poll "configname" start 

will result in one instance of sr_poll for that config.
In the ~/.cache/sarra directory, a number of runtime files are created::

  A .sr_poll_configname_$instance.pid is created, containing the PID  of $instance process.
  A log/sr_poll_configname_$instance.log  is created as a log of $instance process.

The logs can be written in another directory than the default one with option :

**log            <directory logpath>  (default:~/.cache/sarra/log)**


.. NOTE:: 
  FIXME: standard installation/setup explanations ...


VIP, INTERFACE, INSTANCE
------------------------

There is only one instance of sr_poll that should be used for a 
certain config. So the *instances* option is forced to 1. Moreover
we enforced it to be a singleton. **sr_poll** perform its task if envoke
on a server where the ip *vip*  from an *interface*  is present...
If not, **sr_poll** will be put asleep.  When asleep, it will still 
go onto the server every *sleep* seconds, to update its reference file
and be up to date to takeover the work.

**vip       <ip>         (MANDATORY)**
**interface <string>     (MANDATORY)**


CREDENTIALS 
-----------

The configuration for credentials that concerns destination to be reached
is stored in the
 ~/.config/sarra/credentials.conf. There is one entry per line. Pseudo example :

- **sftp://user:passwd@host:port/**
- **sftp://user@host:port/ ssh_keyfile=/abs/path/to/key_file**

- **ftp://user:passwd@host:port/**
- **ftp://user:passwd@host:port/ [passive|active] [binary|ascii]**

- **ftps://user:passwd@host:port/ tls **
- **ftps://user:passwd@host:port/ [passive|active] [binary|ascii] tls [prot_p]**


DESTINATION OPTIONS
-------------------

The program needs to set all the configurations of the destination. 
The destination option sets the information to connect to the remote server 

**destination protocol://<user>:<pw>@<server>[:port]**

::

      (default: None and it is mandatory to set it ) 


The *destination* should be set with the minimum requiered information...
**sr_poll**  uses *destination* in the *AMQP* notification. It is accepted, but not a good
practice to have a password in a notification. To reach the remote server,
the *destination*, is resolved from the credential file.

For example, the user can set :

**destination ftp://myself@myserver**

And complete the requiered information in the credential file with the line  :

**ftp://myself:mypassword@myserver:2121  passive,binary**


POLLING SPECIFICATIONS
----------------------

Theses options set what files the user wants to be notified for and where
 it will be placed, and under which name.

- **filename  <option>         (optional)** 
- **directory <path>           (default: .)** 
- **accept    <regexp pattern> [rename=] (must be set)** 
- **reject    <regexp pattern> (optional)** 

The option *filename* can be uses to set a global rename to the products.
Ex.:

**filename  rename=/naefs/grib2/**

For all notification created, the *rename* option would be set to '/naefs/grib2/filename'
because I specified a directory (ends with /)

The option *directory*  defines where to get the files on the server.
Combined with  **accept** / **reject**  options, the user can select the
files of interest and their directories of residence. **get** is a synonym
for **accept** and is defined for backward compatibility.

The  **accept**  and  **reject**  options use regular expressions (regexp) to match URL.
Theses options are processed sequentially. 
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

Theses options set what files the user wants to be notified for and where
**sr_poll** polls the availability of file on a remote server by creating
an announcment for it.  Subscribers use `sr_subscribe <sr_subscribe.1.html>`_  
to consume the announcement and download the file (or **sr_sarra**).
To make files available to subscribers, **sr_poll** sends the announcements to
an AMQP server, also called a broker.  Format of argument to the *broker* option:: 

       [amqp|amqps]://[user[:password]@]host[:port][/vhost]

The announcement will have its url build from the *destination* option, with
the product's path (*directory*/"matched file").  There is one post per file.
The file'size is taken from the directory "ls"... but the "sum" is set to "0,0"

By default, sr_poll sends its post message, to the broker with default exchange 
is the prefix *xs_* followed by the broker username. The *broker* is mandatory.
It can be given incomplete if, it is well defined in the credentials.conf file.

Refer to `sr_post(1) <sr_post.1.html>`_ - to understand the complete notification.
Here it is important to say that : 

The *sum=0,0* is used because no checksum computation was performed... 

The *parts=1,fsiz,1,0,0* is used and the file'size is taken from the ls of the file.
Under **sr_sarra** these fields could be reset. **FIXME  recompute_checksum in sr_sarra
is available ... but reset filesize does not exist**


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

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
 
