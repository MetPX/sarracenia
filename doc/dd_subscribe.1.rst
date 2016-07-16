==============
 DD_Subscribe 
==============

-----------------------------------------------
Select and Conditionally Download Posted Files
-----------------------------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite



SYNOPSIS
========

 **dd_subscribe** *[-n] configfile.conf*

DESCRIPTION
===========


dd_subscribe is a program to efficiently download files from websites or file servers 
that provide `sr_post(7) <sr_post.7.html>`_ protocol notifications.  Such sites 
publish a message for each file as soon as it is available.  Clients connect to a
*broker* (often the same as the server itself) and subscribe to the notifications.
The *sr_post* notifications provide true push notices for web-accessible folders (WAF),
and are far more efficient than either periodic polling of directories, or ATOM/RSS style 
notifications.

**dd_subscribe** can also be used for purposes other than downloading, (such as for 
supplying to an external program) specifying the -n (*notify_only*, or *no download*) will
suppress the download behaviour and only post the URL on standard output.  The standard
output can be piped to other processes in classic UNIX text filter style.

The **dd_subscribe** command takes one argument: a configuration file described below.

CONFIGURATION
=============

Options are placed in the configuration file, one per line, of the form:: 

  **option <value>** 

Comment lines begins with **#**. For example::

  **debug true**

would be a demonstration of setting the option to enable more verbose logging. 


RABBITMQ CREDENTIAL OPTIONS
---------------------------

The broker option sets all the credential information to connect to the  **RabbitMQ** server 

**broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqp://anonymous:anonymous@dd.weather.gc.ca/ ) 

one can use a single *broker* option as above, or it can be 
broken out: protocol,amqp-user,amqp-password,host,port,vhost

**host     <hostname> (default: dd.weather.gc.ca)** 
     the server running an AMQP broker which is publishing file announcements postings.

**port       <number> (default: 5672)** 
     the port on which a the AMQP broker service is running.

**protocol [amqp|amqps] (default: amqp)**
     the protocol used to communicate with the AMQP broker.

**amqp-user    <user> (default: anonymous)** 
     the user name to authenticate to the broker to obtain the announcements

**amqp-password  <pw> (default: anonymous)** 
     the password for the user name to authenticate to the broker to obtain the announcements

**vhost    <string>  (default: /)**
     AMQP broker vhost specification. 


AMQP QUEUE BINDINGS
-------------------

Once connected to an AMQP broker, the user needs to create a queue and bind it
to an exchange.  These options define which messages (URL notifications) the program receives:

 - **exchange      <name>         (default: xpublic)** 
 - **topic_prefix  <amqp pattern> (default: v00.dd.notify -- developer option)** 
 - **subtopic      <amqp pattern> (subtopic need to be set)** 

Several topic options may be declared. To give a correct value to the subtopic,
browse the our website  **http://dd.weather.gc.ca**  and write down all directories of interest.
For each directories write an  **subtopic**  option as follow:

 **subtopic  directory1.*.subdirectory3.*.subdirectory5.#** 

::

 where:  
       *                replaces a directory name 
       #                stands for the remaining possibilities

One has the choice of filtering using  **subtopic**  with only AMQP's limited wildcarding, or the 
more powerful regular expression based  **accept/reject**  mechanisms described below.  The 
difference being that the AMQP filtering is applied by the broker itself, saving the 
notices from being delivered to the client at all. The  **accept/reject**  patterns apply to 
messages sent by the broker to the subscriber.  In other words,  **accept/reject**  are 
client side filters, whereas  **subtopic**  is server side filtering.  

It is best practice to use server side filtering to reduce the number of announcements sent
to the client to a small superset of what is relevant, and perform only a fine-tuning with the 
client side mechanisms, saving bandwidth and processing for all.

topic_prefix is primarily of interest during protocol version transitions, where one wishes to 
specify a non-default protocol version of messages to subscribe to. 



AMQP QUEUE SETTINGS
-------------------

The queue is where the notifications are held on the server for each subscriber.

::

**queue         <name>         (default: None)** 
**durable       <boolean>      (default: False)** 
**expire        <minutes>      (default: None)** 
**message-ttl   <minutes>      (default: None)** 

By default, dd_subscribe creates a queue name that should be unique and starts with  **cmc** 
and puts it into a file .<configname>.queue, where <configname> is the config filename.
The  **queue**  option sets a queue name. It should always start with  **cmc** .

The  **expire**  option is expressed in minutes... it sets how long should live
a queue without connections The  **durable** option set to True, means writes the queue
on disk if the broker is restarted.
The  **message-ttl**  option set the time in minutes a message can live in the queue.
Past that time, the message is taken out of the queue by the broker.

HTTP DOWNLOAD CREDENTIALS 
-------------------------

::

**http-user   <user> (default: None)** 
**http-password <pw> (default: None)** 

DELIVERY SPECIFICATIONS
-----------------------

Theses options set what files the user wants and where it will be placed,
and under which name.

::

**accept    <regexp pattern> (must be set)** 
**directory <path>           (default: .)** 
**flatten   <boolean>        (default: false)** 
**lock      <.string>        (default: .tmp)** 
**mirror    <boolean>        (default: false)** 
**overwrite <boolean>        (default: true)** 
**reject    <regexp pattern> (optional)** 
**strip     <count>         (default: 0)**

The  **lock**  option is a suffix given to the file during the download
and taken away when it is completed... If  **lock**  is set to  **.** 
then it is prefixed with it and taken away when it is completed...
This gives a mean to avoid processing the file prematurely.

The option directory  defines where to put the files on your server.
Combined with  **accept** / **reject**  options, the user can select the
files of interest and their directories of residence. (see the  **mirror**
option for more directory settings).

The  **accept**  and  **reject**  options use regular expressions (regexp) to match URL.
Theses options are processed sequentially. 
The URL of a file that matches a  **reject**  pattern is never downloaded.
One that match an  **accept**  pattern is downloaded into the directory
declared by the closest  **directory**  option above the matching  **accept**  option.

::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*

The  **mirror**  option can be used to mirror the dd.weather.gc.ca tree of the files.
If set to  **True**  the directory given by the  **directory**  option
will be the basename of a tree. Accepted files under that directory will be
placed under the subdirectory tree leaf where it resides under dd.weather.gc.ca.
For example retrieving the following url, with options::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

You can modify the mirrored directoties with the option **strip**  .
If set to N  (an integer) the first 'N' directories are withdrawn.
For example :

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   strip     3
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

The  **flatten**  option is use to set a separator character. This character
will be used to replace the '/' in the url directory and create a "flatten" filename
form its dd.weather.gc.ca path.  For example retrieving the following url, 
with options::

 http://dd.weather.gc.ca/model_gem_global/25km/grib2/lat_lon/12/015/CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2

   flatten   -
   directory /mylocaldirectory
   accept    .*model_gem_global.*

would result in the creation of the filepath ::

 /mylocaldirectory/model_gem_global-25km-grib2-lat_lon-12-015-CMC_glb_TMP_TGL_2_latlon.24x.24_2013121612_P015.grib2


The  **overwrite**  option,if set to false, avoid unnecessary downloads under these conditions :
1- the file to be downloaded is already on the user's file system at the right place and
2- the checksum of the amqp message matched the one of the file.
The default is True (overwrite without checking).

EXAMPLES
--------

Here is a short complete example configuration file:: 

  broker amqp://dd.weather.gc.ca/

  subtopic model_gem_global.25km.grib2.#
  accept .*

This above file will connect to the dd.weather.gc.ca broker, connecting as
anonymous with password anonymous (defaults) to obtain announcements about
files in the http://dd.weather.gc.ca/model_gem_global/25km/grib2 directory.
All files which arrive in that directory or below it will be downloaded 
into the current directory (or just printed to standard output if -n option 
was specified.) 

A variety of example configuration files are available here:

 `http://sourceforge.net/p/metpx/git/ci/master/tree/sarracenia/samples/config/ <http://sourceforge.net/p/metpx/git/ci/master/tree/sarracenia/samples/config>`_



QUEUES and MULTIPLE STREAMS
---------------------------

When executed,  **dd_subscribe**  chooses a queue name, which it writes
to a file named after the configuration file given as an argument to dd_subcribe
with a .queue suffix ( ."configfile".queue). 
If dd_subscribe is stopped, the posted messages continue to accumulate on the 
broker in the queue.  When the program is restarted, it uses the queuename 
stored in that file to connect to the same queue, and not lose any messages.

File downloads can be parallelized by running multiple dd_subscribe using
the same queue.  The processes will share the queue and each download 
part of what has been selected.  Simply launch multiple instances
of dd_subscribe in the same user/directory using the same configuration file, 

You can also run several dd_subscribe with different configuration files to
have multiple download streams delivering into the the same directory,
and that download stream can be multi-streamed as well.

.. Note::

  While the brokers keep the queues available for some time, Queues take resources on 
  brokers, and are cleaned up from time to time.  A queue which is not accessed for 
  a long (implementation dependent) period will be destroyed.  A queue which is not
  accessed and has too many (implementation defined) files queued will be destroyed.
  Processes which die should be restarted within a reasonable period of time to avoid
  loss of notifications.


RABBITMQ LOGGING
----------------

For each download, an amqp report message is sent back to the broker.
Should you want to turned them off the option is :

**report_back <boolean>        (default: true)** 


DEPRECATED SETTINGS
-------------------

These settings pertain to previous versions of the client, and have been superceded.

::

 **topic         <amqp pattern> (deprecated)** 
 **exchange_type <type>         (default: topic)** 
 **exchange_key  <amqp pattern> (deprecated)** 

SEE ALSO
--------

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - dd_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.


HISTORY
-------

dd_subscribe was initially developed for  **dd.weather.gc.ca**, an Environment Canada website 
where a wide variety of meteorological products are made available to the public. it is from
the name of this site that the sarracenia suite takes the sr\_ prefix for it's tools.  The initial
version was deployed in 2013 on an experimental basis.  The following year, support of checksums
was added, and in the fall of 2015, the feeds were updated to v02.

Sarracenia 
   Just for fun, a rare, mostly carnivorous, plant found in Canada.  The *Thread-leaved Sundew*
   is another one, and the source of the name of the earlier MetPX file switching project.

