=========
SR_Report 
=========

---------------------------------
Select and Process Posted Reports 
---------------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite

.. contents::

SYNOPSIS
========

 **sr_report** foreground|start|stop|restart|reload|status configfile

 **sr_report** cleanup|declare|setup configfile


DESCRIPTION
===========

sr_report is a program to efficiently process reports of file transfers from 
sarracenia. The format of the reports is shown in the `sr_report(7) <sr_report.7.rst>`_ manual 
page.  When clients download a message from a site running sarracenia, they post
information about their success in doing so.  

The **sr_report** command takes two arguments: a configuration file described below,
followed by an action, one of: start|stop|restart|reload|status or foreground... (self described).
sr_report is sr_subscribe with the following settings changed::

  no-download True
  topic-prefix v02.report
  cache off
  accept_unmatch True
  report_back False

The **foreground** action is different. It is used when building a configuration
or debugging things, when the user wants to run the program and its configfile 
interactively...   The **foreground** instance is not concerned by other actions, 
but should the configured instances be running, it shares the same (configured) message queue.
The user would stop using the **foreground** instance by simply pressing <ctrl-c> on linux 
or use other means to kill its process. That would be the old **dd_subscribe** behavior...

The actions **cleanup**, **declare**, **setup** can be used to manage resources on
the rabbitmq server. The resources are either queues or exchanges. **declare** creates
the resources. **setup** creates and additionnaly does the bindings of queues.

CONFIGURATION
=============

In general, the options for this component are described by the
`sr_subscribe(1) <sr_subscribe.1.rst>`_  page which should be read first.
It fully explains the option configuration language, and how to find
the option settings.


CREDENTIAL OPTIONS
------------------

The broker option sets all the credential information to connect to the  **RabbitMQ** server 

- **broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqp://anonymous:anonymous@dd.weather.gc.ca/ ) 

All sr\_ tools store all sensitive authentication info is stored in the credentials file.
Passwords for SFTP, AMQP, and HTTP accounts are stored in URL´s there, as well as other pointers
to thins such as private keys, or FTP modes.

For more details, see: `sr_subscribe(1) credentials <sr_subscribe.1.html#credentials>`_  

AMQP QUEUE BINDINGS
-------------------

Once connected to an AMQP broker, the user needs to create a queue and bind it
to an exchange.  These options define which messages (URL notifications) the program receives:

 - **exchange      <name>         (default: xpublic)** 
 - **topic_prefix  <amqp pattern> (default: v02.report -- developer option)** 
 - **subtopic      <amqp pattern> (subtopic need to be set)** 

Several topic options may be declared. To give a correct value to the subtopic,

for more details, see: `sr_subscribe(1) <sr_subscribe.1.rst>`_  

One has the choice of filtering using  **subtopic**  with only AMQP's limited wildcarding and
length limited to 255 encoded bytes, or the 
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

With  **accept** / **reject**  options, the user can further refine the selection of
files of interest . 

The  **accept**  and  **reject**  options use regular expressions (regexp) to match URL.
Theses options are processed sequentially. 
The URL of a file that matches a  **reject**  pattern is never downloaded.
One that match an  **accept**  pattern is downloaded into the directory
declared by the closest  **directory**  option above the matching  **accept**  option.

::

  ex.   
        accept    .*RADAR.*
        reject    .*Reg.*
        accept    .*GRIB.*

will show reports only for the accepted file paths.

EXAMPLES
--------

Here is a short complete example configuration file:: 

  broker amqp://dd.weather.gc.ca/

  subtopic model_gem_global.25km.grib2.#
  accept .*

This above file will connect to the dd.weather.gc.ca broker, connecting as
anonymous with password anonymous (defaults) to obtain announcements about
files in the http://dd.weather.gc.ca/model_gem_global/25km/grib2 directory.
All reports of downloads of those files present on the pump will be
accepted for processing by sr_report.

A variety of example configuration files are available here:

 `http://sourceforge.net/p/metpx/git/ci/master/tree/sarracenia/samples/config/ <http://sourceforge.net/p/metpx/git/ci/master/tree/sarracenia/samples/config>`_

for more details, see: `sr_subscribe(1) <sr_subscribe.1.rst>`_  



ADVANCED FEATURES
-----------------

There are ways to insert scripts into the flow of messages and file downloads:
Should you want to implement tasks in various part of the execution of the program:

- **on_message  <script>        (default: msg_log)** 

A do_nothing.py script for **on_message**, **on_file**, and **on_part** could be
(this one being for **on_file**)::

 class Transformer(object): 
      def __init__(self):
          pass

      def perform(self,parent):
          logger = parent.logger

          logger.info("I have no effect but adding this log line")

          return True

 transformer  = Transformer()
 self.on_message = transformer.perform

The only arguments the script receives is **parent**, which is an instance of
the **sr_report** class

for more details, see: `sr_subscribe(1) <sr_subscribe.1.rst>`_  


SEE ALSO
--------

`sr_report(7) <sr_report.7.rst>`_ - the format of report messages.

`sr_post(1) <sr_post.1.rst>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.rst>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.rst>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_subscribe(1) <sr_subscribe.1.rst>`_ - Selectively Download files.

`sr_watch(1) <sr_watch.1.rst>`_ - the directory watching daemon.

`https://github.com/MetPX/ <https://github.com/MetPX/>`_ - sr_report is a component of MetPX-Sarracenia, the AMQP based data pump.
