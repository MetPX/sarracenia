==========
 SR_Report 
==========

-----------------------------------------------
Select and Process Subscription Report Messages
-----------------------------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite



SYNOPSIS
========

 **sr_report** configfile foreground|start|stop|restart|reload|status

DESCRIPTION
===========


sr_report is a program to efficiently sr_report messages and process them.
The message format is here: `sr_report(7) <sr_report.7.html>`_ .  The messages acquired
are produced by consumers of messages from a sarracenia data pump.  

The **sr_report** command takes two arguments: a configuration file described below,
followed by an action that is one of: foreground, start, stop, restart, reload, or status. 

While these actions are self-explanatory, the **foreground** action is different. It 
would be used when building a configuration or debugging things. It is used when the 
user wants to run the program and its configfile interactively...   The **foreground** 
instance is not concerned by other actions, but should the configured instances be 
running it shares the same (configured) message queue.  The user would stop using 
the **foreground** instance by simply pressing <ctrl-c> on linux 
or use other means to kill its process. That would be the old **dd_subscribe** behavior...

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

For more details, see: `sr_config(7) credentials <sr_config.7.html/#credentials>`_


AMQP QUEUE BINDINGS
-------------------

Once connected to an AMQP broker, the user needs to create a queue and bind it
to an exchange.  These options define which messages (URL notifications) the program receives:

 - **exchange      <name>         (default: either xl_<user>, or xlog)** 
 - **topic_prefix  <amqp pattern> (default: v00.dd.notify -- developer option)** 
 - **subtopic      <amqp pattern> (subtopic need to be set)** 

Several topic options may be declared. To give a correct value to the subtopic,

for more details, see: `sr_config(7) <sr_config.7.html>`_  

One has the choice of filtering using  **subtopic**  with only AMQP's limited wildcarding, 
or the more powerful regular expression based  **accept/reject**  mechanisms described 
below.  The difference being that the AMQP filtering is applied by the broker itself, 
saving the notices from being delivered to the client at all. The  **accept/reject**  
patterns apply to messages sent by the broker to the subscriber.  In other 
words,  **accept/reject**  are client side filters, whereas  **subtopic** provides 
server side filtering.  

It is best practice to use server side filtering to reduce the number of announcements 
sent to the client to a small superset of what is relevant, and perform only a 
fine-tuning with the client side mechanisms, saving bandwidth and processing for all.

topic_prefix is primarily of interest during protocol version transitions, where 
one wishes to specify a non-default protocol version of messages to subscribe to. 

When no **exchange** setting is given, for standard users (sources, and subscribers), 
the default exchange will be the user's own logging exchange, that is an exchange
that begins with *xl_* to which the broker username is appended.  For administrative
users, the default exchange is the system-wide logging exchange, named xlog.


DELIVERY SPECIFICATIONS
-----------------------

These options set what files the user wants and where it will be placed,
and under which name.

- **accept    <regexp pattern> (must be set)** 
- **reject    <regexp pattern> (optional)** 

With the  **accept** / **reject**  options, the user can select the
messages of interest with greater specificity.

The  **accept**  and  **reject**  options use regular expressions (regexp) to match URL.
Theses options are processed sequentially. 
The URL in a message that matches a  **reject**  pattern is never processed.
One that matches an  **accept**  pattern is processed.

::

  ex.   directory /mylocaldirectory/myradars
        accept    .*RADAR.*

        directory /mylocaldirectory/mygribs
        reject    .*Reg.*
        accept    .*GRIB.*


EXAMPLES
--------


Here is a short complete example configuration file (blog.conf) :: 

  broker amqps://feeder@boule.example.com/
  exchange xlog
  accept .*

Using that file, assuming feeder is a 'feeder' (Administrative) account on boule, one
could start it up as follows::

  blacklab% sr_report blog.conf foreground
  2016-05-05 23:33:38,198 [INFO] sr_report start
  2016-05-05 23:33:38,198 [INFO] sr_report run
  2016-05-05 23:33:38,198 [INFO] AMQP  broker(boule.example.com) user(feeder) vhost(/)
  2016-05-05 23:33:39,048 [INFO] Binding queue q_feeder.sr_report.blog.55881473.49130029 with key v02.report.# from exchange xlog on broker amqps://feeder@boule.example.com/
  2016-05-05 23:33:39,414 [INFO] msg_log received: 20160506033326.795 http://boule.example.com/ 20160506/metpx/bulletins/alphanumeric/20160506/UA/CWAO/03/UANT01_CWAO_060333___82718 201 blacklab anonymous 0.964417
  2016-05-05 23:33:39,507 [INFO] msg_log received: 20160506033329.346 http://boule.example.com/ 20160506/metpx/observations/swob-ml/20160506/CL2D/2016-05-06-0333-CL2D-AUTO-minute-swob.xml 201 boule.example.com feeder -0.722485
  2016-05-05 23:33:39,600 [INFO] msg_log received: 20160506033329.713 http://boule.example.com/ 20160506/metpx/observations/swob-ml/20160506/CXEG/2016-05-06-0300-CXEG-AUTO-swob.xml 201 boule.example.com feeder -0.833262


This above file will connect to the boule.example.com broker, connecting as
feeder with a password stored in the credentials.conf file to obtain report messages
created by consumers of data on that pump.  By connecting to the report exchange,
one is obtaining all of the report messages from all consumers of data on the pump.


.. note::
  FIXME, they aren't.

A variety of example configuration files are available here:

 `http://sourceforge.net/p/metpx/git/ci/master/tree/sarracenia/samples/config/ <http://sourceforge.net/p/metpx/git/ci/master/tree/sarracenia/samples/config>`_

for more details, see: `sr_config(7) <sr_config.7.html>`_  



QUEUES and MULTIPLE STREAMS
---------------------------

When executed,  **sr_report**  chooses a queue name, which it writes
to a file named after the configuration file given as an argument to sr_report**
with a .queue suffix ( ."configfile".queue). 
If sr_report is stopped, the posted messages continue to accumulate on the 
broker in the queue.  When the program is restarted, it uses the queuename 
stored in that file to connect to the same queue, and not lose any messages.

File downloads can be parallelized by running multiple sr_report using
the same queue.  The processes will share the queue and each download 
part of what has been selected.  Simply launch multiple instances
of sr_report in the same user/directory using the same configuration file, 

You can also run several sr_report with different configuration files to
have multiple download streams delivering into the the same directory,
and that download stream can be multi-streamed as well.

.. Note::

  While the brokers keep the queues available for some time, Queues take resources on 
  brokers, and are cleaned up from time to time.  A queue which is not accessed for 
  a long (implementation dependent) period will be destroyed.  A queue which is not
  accessed and has too many (implementation defined) files queued will be destroyed.
  Processes which die should be restarted within a reasonable period of time to avoid
  loss of notifications.


ADVANCED FEATURES
-----------------

There are ways to insert scripts into the flow of messages. 
Should you want to implement tasks in various part of the execution of the program:

- **on_message  <script>        (default: None)** 

By default (if not on_message pluging is specified), the plugin msg_log.py is used,
which simply prints the body of each message accepted.  sr_report can be used
to generate statistics, are rudimentary version being to invoke it like so::

  sr_report --on_message msg_speedo blog.conf foreground

Using the same file as above, one can  add a command-line option to change the message 
handling plugin used to process report messages::

  blacklab% sr_report --on_message msg_speedo blog.conf foreground
  2016-05-05 23:40:15,179 [INFO] sr_report start
  2016-05-05 23:40:15,179 [INFO] sr_report run
  2016-05-05 23:40:15,179 [INFO] AMQP  broker(boule.example.com) user(feeder) vhost(/)
  2016-05-05 23:40:16,208 [INFO] Binding queue q_feeder.sr_report.blog.55881473.49130029 with key v02.report.# from exchange xlog on broker amqps://feeder@boule.example.com/
  2016-05-05 23:40:20,260 [INFO] speedo:  41 messages received:   8.1 msg/s, 15.5K bytes/s, lag: 4e+02 s
  2016-05-05 23:40:20,260 [WARNING] speedo: Excessive lag: 395.412 seconds 
  2016-05-05 23:40:25,313 [INFO] speedo:  55 messages received:    11 msg/s, 8.9K bytes/s, lag: 4e+02 s
  2016-05-05 23:40:25,313 [WARNING] speedo: Excessive lag: 399.444 seconds 
  2016-05-05 23:40:30,394 [INFO] speedo:  53 messages received:    10 msg/s, 12.6K bytes/s, lag: 3.8e+02 s
  2016-05-05 23:40:30,394 [WARNING] speedo: Excessive lag: 380.164 seconds 
  2016-05-05 23:40:30,508 [INFO] signal stop
  2016-05-05 23:40:30,508 [INFO] sr_report stop
  blacklab% 

One can monitor arbitrary data by creating report configurations with a variety of selection criteria and processing options.

A do_nothing.py script for **on_message**::

 class Transformer(object): 
      def __init__(self,parent):
          pass

      def perform(self,parent):
          logger = parent.logger

          logger.info("I have no effect but adding this log line")

          return True

 transformer  = Transformer(self)
 self.on_message = transformer.perform

The only arguments the script receives it **parent**, which is an instance of
the **sr_report** class. 

for more details, see: `sr_config(7) <sr_config.7.html>`_  


SEE ALSO
--------

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - subscription client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_report is a component of MetPX-Sarracenia, the AMQP based data pump.
