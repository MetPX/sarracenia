==============
 SR_Shovel 
==============

-----------------------------
Copy Messages Between Brokers
-----------------------------

:Manual section: 1
:Date: @Date@
:Version: @Version@
:Manual group: Metpx-Sarracenia Suite



SYNOPSIS
========

 **sr_shovel** configfile foreground|start|stop|restart|reload|status

DESCRIPTION
===========


sr_shovel is a program to easily subscribe to messages on one broker and 
repost them on another one.  Sr_shovel does not copy any data, only post or log
messages.  The component takes two argument: a configuration file described below,
and an action start|stop|restart|reload|status... (self described).

The **foreground** action is different. It would be used when building a configuration
or debugging things. It is used when the user wants to run the program and its configfile 
interactively...   The **foreground** instance is not concerned by other actions, 
but should the configured instances be running it shares the same (configured) message queue.
The user would stop using the **foreground** instance by simply pressing <ctrl-c> on linux 
or use other means to kill its process. 

CONFIGURATION
=============

Options are placed in the configuration file, one per line, of the form: 

**option <value>** 

Comment lines begins with **#**. 
For example::

  **debug true**

would be a demonstration of setting the option to enable more verbose logging.


RABBITMQ CREDENTIAL OPTIONS
---------------------------

The broker option sets all the credential information to connect to the  **RabbitMQ** server 

- **broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqp://anonymous:anonymous@dd.weather.gc.ca/ ) 


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
messages sent by the broker to the shovel.  In other words,  **accept/reject**  are 
client side filters, whereas  **subtopic**  is server side filtering.  

It is best practice to use server side filtering to reduce the number of announcements sent
to the client to a small superset of what is relevant, and perform only a fine-tuning with the 
client side mechanisms, saving bandwidth and processing for all.

topic_prefix is primarily of interest during protocol version transitions, where one wishes to 
specify a non-default protocol version of messages to subscribe to. 

.. NOTE:: 
  FIXME: no mention of the use of exchange argument.


AMQP QUEUE SETTINGS
-------------------

The queue is where the notifications are held on the server for each shovel.

- **queue_name    <name>         (default: q_<brokerUser>.sr_shovel.<configname>)** 
- **durable       <boolean>      (default: False)** 
- **expire        <minutes>      (default: None)** 
- **message-ttl   <minutes>      (default: None)** 

By default, **sr_shovel** creates a queue name that should be unique and starts with  **q_** 
followed by the broker username, than dot separated follows the program name **sh_shovel**,
and the configuration name.
The  **queue_name**  option sets a queue name. It should always start with  **q_brokerUser** .

The  **expire**  option is expressed in minutes... it sets how long should live
a queue without connections The  **durable** option set to True, means writes the queue
on disk if the broker is restarted.
The  **message-ttl**  option set the time in minutes a message can live in the queue.
Past that time, the message is taken out of the queue by the broker.

CREDENTIALS 
-----------

The configuration for credentials that concerns product download is stored in the
 ~/.config/sarra/credentials.conf. There is one entry per line. Pseudo example :

- **amqp://user:passwd@host:port/**
- **amqps://user:passwd@host:port/**

- **sftp://user:passwd@host:port/**
- **sftp://user@host:port/ ssh_keyfile=/abs/path/to/key_file**

- **ftp://user:passwd@host:port/**
- **ftp://user:passwd@host:port/ [passive|active] [binary|ascii]**

- **http://user:passwd@host:port/**

to implement supported of additional protocols, one would write 
a **_do_download** script.  the scripts would access the credentials 
value in the script with the code :   

- **ok, details = parent.credentials.get(msg.urlcred)**
- **if details  : url = details.url**

.. note::
   FIXME: how does this work with ssh_keyfile, active/passive, ascii/binary ?
   non url elements of the entry. details.ssh_keyfile?

MORE MESSAGE SELECTION
-----------------------

Theses options set what files the user wants and where it will be placed,
and under which name.

- **accept    <regexp pattern> (must be set)** 
- **reject    <regexp pattern> (optional)** 

With  **accept** / **reject**  options, the user can select the
messages of interest.  These options use regular expressions (regexp) to match
the message URL.  Theses options are processed sequentially. 
The URL of a file that matches a  **reject**  pattern is not reposted.
One that match an  **accept**  pattern it is processed.
If no  **accept** / **reject** is specified, all messages are processed.
If it is used, only messages that match **accept** pattern are processed

::

        accept    .*RADAR.*
        reject    .*Reg.*
        accept    .*GRIB.*

 
OUTPUT NOTIFICATION OPTIONS
---------------------------

The program needs to set all the rabbitmq configurations for an output broker.

The post_broker option sets all the credential information to connect to the
  output **RabbitMQ** server 

**post_broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**
      (default to the value of the feeder option in default.conf) 

The **post_exchange** option can set under which exchange the notification 
will be reposted.  If it is not specified,  the message will be reposted with
the same exchange they were annonced with.

Whenever a publish happens for a product, a user can set to trigger a script.
The option **on_post** would be used to do such a setup.


MULTIPLE STREAMS
----------------

When executed,  **sr_shovel**  chooses a queue name, which it writes
to a file named after the configuration file given as an argument to sr_shovel**
with a .queue suffix ( ."configfile".queue). 
If sr_shovel is stopped, the posted messages continue to accumulate on the 
broker in the queue.  When the program is restarted, it uses the queuename 
stored in that file to connect to the same queue, and not lose any messages.

The message reposting can be parallelized by running multiple sr_shovel using
the same queue.  The processes will share the queue and messages will be 
distributed  between processes.  Simply launch sr_shovel with option instances
set to an integer greater than 1.

RABBITMQ LOGGING
----------------

The fact of shovelling messages is not logged back to the source broker.

.. note::
  FIXME  should it ?
  thinking:  log me


ADVANCED FEATURES
-----------------

There are ways to insert scripts into the flow of messages:
Should you want to implement tasks in various part of the execution of the program:

- **on_message  <script>        (default: None)** 
- **on_post     <script>        (default: None)** 

A do_nothing.py script for **on_message**, and **on_post** could be:
(this one being for **on_file**)

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
the **sr_shovel** class
Should one of these scripts return False, the processing of the message/file
will stop there and another message will be consumed from the broker.


SEE ALSO
--------

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcement messages.

`sr_sarra(1) <sr_sarra.1.html>`_ - Subscribe, Acquire, and ReAdvertise tool.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`http://metpx.sf.net/ <http://metpx.sf.net/>`_ - sr_subscribe is a component of MetPX-Sarracenia, the AMQP based data pump.
