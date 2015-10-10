==============
 DD_Subscribe 
==============

----------------------------------------
Select and perhaps download posted files
----------------------------------------

:Manual section: 1
:Date: Oct 2013 
:Version: 1.0.0
:Manual group: Metpx-Sarracenia Suite


SYNOPSIS
========

 **dd_subscribe** *[-n] configfile.conf*

DESCRIPTION
===========

dd_subscribe is an efficient real-time file downloader, initially developed for  **dd.weather.gc.ca**  which is an Environment Canada website where a wide variety of meteorological products are
made available to the public. The website servers publish a message for each product as 
soon as it is available.  Clients subscribe to the notifications which use AMQP, a protocol 
that supports publish/subscribe communications patterns without the expensive polling 
involved in traditional ATOM/RSS schemes.

the **dd_subscribe**  command takes one argument, a configuration file. 
If you want  **dd_subscribe**  not to retrieve the products but only post the URL on standard
output, execute:   dd_subscribe -n config_file.  -n stands for "notify_only" or "no_download"

CONFIGURATION
=============

Options are placed in the configuration file, one per line, of the form:

 **option <value>** 

A comment is a line that begins with  **#** . Empty lines are permitted.

RABBITMQ CREDENTIAL OPTIONS
===========================

These options set all the credential information to connect to the  **RabbitMQ**
server ::

 broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>
      (default: amqp://anonymous:anonymous@dd.weather.gc.ca/ ) 
      broken out: protocol,amqp-user,amqp-password,host,port,vhost

      **host     <hostname> (default: dd.weather.gc.ca)** 
      **port       <number> (default: 5672)** 
      **amqp-user    <user> (default: anonymous)** 
      **amqp-password  <pw> (default: anonymous)** 


AMQP QUEUE BINDINGS
===================

Once connected to an AMQP broker, the user needs to create a queue and bind it
to an exchange.  These options define which messages (URL notifications) the program receives::

 **exchange      <name>         (default: xpublic)** 
 **topic_prefix  <amqp pattern> (default: v00.dd.notify -- developer option)** 
 **subtopic      <amqp pattern> (topic or subtopic need to be set)** 

Several topic options may be declared. To give a correct value to the subtopic,
browse the our website  **http://dd.weather.gc.ca**  and write down all directories of interest.
For each directories write an  **subtopic**  option as follow::

 **subtopic  directory1.*.subdirectory3.*.subdirectory5.#** 

 where:  
       *                replaces a directory name 
       #                stands for the remaining possibilities

One has the choice of filtering using  **subtopic**  with only AMQP's limited wildcarding, or the 
more powerful regular expression based  **accept/reject**  mechanisms described below.  The 
difference being that the AMQP filtering is applied by the broker itself, saving the 
notices from being delivered to the client at all. The  **accept/reject**  patterns apply to 
messages sent by the broker to the subscriber.  In other words,  **accept/reject**  are 
client side filters, whereas  **subtopic**  is server side filtering.  

It is best practice to use server side filtering to winnow out products to a small superset 
of what is relevant, and perform only a fine-tuning with the client side mechanisms, in order
to economize bandwidth and processing for all.

topic_prefix is primarily of interest during protocol version transitions, where one wishes to specify a non-default protocol version of messages to subscribe to. 

AMQP QUEUE SETTINGS
===================

The queue is where the notifications are held on the server for each subscriber.

::

 **queue         <name>         (default: None)** 
 **durable       <boolean>      (default: False)** 
 **expire        <minutes>      (default: None)** 
 **message-ttl   <minutes>      (default: None)** 
 **timeout   <integer>        (default: 180)** 

By default, dd_subscribe creates a queue name that should be unique and starts with  **cmc** 
and puts it into a file .<configname>.queue, where <configname> is the config filename.
The  **queue**  option sets a queue name. It should always start with  **cmc** .
The  **expire**  option is expressed in minutes... it sets how long should live
a queue without connections The  **durable** option set to True, means writes the queue
on disk if the broker is restarted.
The  **message-ttl**  option set the time in minutes a message can live in the queue.
Past that time, the message is taken out of the queue by the broker.

HTTP DOWNLOAD CREDENTIALS 
=========================

::

 **http-user   <user> (default: None)** 
 **http-password <pw> (default: None)** 

DELIVERY SPECIFICATIONS
=======================

Theses options set what products the user wants and where it will be placed,
and under which name.

::

**accept    <regexp pattern> (must be set)** 
**directory <path>           (default: .)** 
**flatten   <boolean>        (default: false)** 
**lock      <.string>        (default: .tmp)** 
**mirror    <boolean>        (default: false)** 
**overwrite <boolean>        (default: true)** 
**reject    <regexp pattern> (optional)** 

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
The URL of a product that match a  **reject**  pattern is never downloaded.
One that match an  **accept**  pattern is downloaded into the directory
declared by the closest  **directory**  option above the matching  **accept**  option.

::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*

The  **mirror**  option can be used to mirror the dd.weather.gc.ca tree of the products.
If set to  **True**  the directory given by the  **directory**  option
will be the basename of a tree. Accepted products under that directory will be
placed under the subdirectory tree leaf where it resides under dd.weather.gc.ca.
For example retrieving the following url, with options::

 http://dd.weather.gc.ca/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

   mirror    True
   directory /mylocaldirectory
   accept    .*RADAR.*

would result in the creation of the directories and the file
/mylocaldirectory/radar/PRECIP/GIF/WGJ/201312141900_WGJ_PRECIP_SNOW.gif

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


The  **timeout**  option is use to set a time limit to the file download, avoiding network freeze.
If a download takes more than  **timeout**  seconds, the download is restarted. This looping continues
until the file is properly downloaded... Only than, the amqp message is acknowledge.

The  **overwrite**  option,if set to false, avoid unnecessary downloads under these conditions :
1- the file to be downloaded is already on the user's file system at the right place and
2- the checksum of the amqp message matched the one of the file.
The default is True (overwrite without checking).

PRODUCT QUEUING
===============

When executed,  **dd_subscribe**  creates a queue name, which it writes
to a file named after the configuration file given as an argument to dd_subcribe
with a .queue suffix ( ."configfile".queue). Normally  **dd_subscribe** 
runs like a daemon. If it is stopped, the messages (URL notifications) are queued.
When the program is restarted, it uses the queuename stored in that file in order
to connect to the same queue, and not lose any messages.
You can parallelize the download of products by running multiple dd_subscribe
processes in the same user/directory using the same configuration file, the processes
will share the queue and each download part of what has been selected.

You can also run several dd_subscribe with different configuration files.

Queues take resources on brokers, and are therefore cleaned up from time to time.
A queue which is unaccessed for a long (implementation dependent) period will be destroyed.
A queue which is unaccessed and has too many (implementation defined) products queued will be destroyed.

DEPRECATED SETTINGS
===================

::

 **exchange_type <type>         (default: topic)** 
 **exchange_key  <amqp pattern> (deprecated)** 

NOTES
=====

SARRACENIA -- Just for fun, another rare, mostly carnivorous, canadian plant... (as sundew,columbo)

The **dd_subscribe**  is a python program that uses python-amqplib to receive these amqp messages
and optionally retrieve the web products and place them in a chosen local directory.

http://metpx.sf.net/ - dd_subscribe is a component of MetPX-Sarracenia, the AMQP based file switch.
