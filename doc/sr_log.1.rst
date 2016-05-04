========
 SR_Log 
========

--------------------------------------------
Select and Process Subscription Log Messages
--------------------------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite



SYNOPSIS
========

 **sr_log** configfile foreground|start|stop|restart|reload|status

DESCRIPTION
===========


sr_log is a program to efficiently acquire download messages and process them.
The message format is here: `sr_log(7) <sr_log.7.html>`_ .  The messages acquired
are produced by consumers of messages from a sarracenia data pump.  

The **sr_log** command takes two arguments: a configuration file described below,
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


RABBITMQ CREDENTIAL OPTIONS
---------------------------

The broker option sets all the credential information to connect to the  **RabbitMQ** server 

- **broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqp://anonymous:anonymous@dd.weather.gc.ca/ ) 

for more details, see: `sr_config(7) <sr_config.7.html>`_  

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

for more details, see: `sr_config(7) <sr_config.7.html>`_  


QUEUES and MULTIPLE STREAMS
---------------------------

When executed,  **sr_log**  chooses a queue name, which it writes
to a file named after the configuration file given as an argument to sr_log**
with a .queue suffix ( ."configfile".queue). 
If sr_log is stopped, the posted messages continue to accumulate on the 
broker in the queue.  When the program is restarted, it uses the queuename 
stored in that file to connect to the same queue, and not lose any messages.

File downloads can be parallelized by running multiple sr_log using
the same queue.  The processes will share the queue and each download 
part of what has been selected.  Simply launch multiple instances
of sr_log in the same user/directory using the same configuration file, 

You can also run several sr_log with different configuration files to
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

There are ways to insert scripts into the flow of messages and file downloads:
Should you want to implement tasks in various part of the execution of the program:

- **on_message  <script>        (default: None)** 

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
 self.on_file = transformer.perform

The only arguments the script receives it **parent**, which is an instance of
the **sr_log** class
Should one of these scripts return False, the processing of the message/file
will stop there and another message will be consumed from the broker.

for more details, see: `sr_config(7) <sr_config.7.html>`_  


SEE ALSO
--------

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - subscription client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_log is a component of MetPX-Sarracenia, the AMQP based data pump.
