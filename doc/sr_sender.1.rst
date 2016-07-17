==========
 SR_Sender 
==========

--------------------------------------------------------------------------
Sends file from messages to remote server (option repost to remote broker)
--------------------------------------------------------------------------

:Manual section: 1 
:Date: @Date@
:Version: @Version@
:Manual group: MetPX-Sarracenia

SYNOPSIS
========

**sr_sender** configfile foreground|start|stop|restart|reload|status

DESCRIPTION
===========

**sr_sender** is a program that Subscribes to file notifications, 
and sends the file to a remote server. It can also, if needed,
post a notification on a remote broker. It is used to send products
directly from a **pump**.

The notification protocol is defined here `sr_post(7) <sr_post.7.html>`_

**sr_sender** connects to a *broker* and subscribes to the notifications
of interest. On reception of a notification, it determines the location
of the file on the server it runs. Than it determines its remote directory
and name. Now being ready to deliver the file, it connects to the destination
server and delivers the file accordingly.  If the user sets up a **post_broker**
a notification is created and sent to that broker.

The primary purpose of this program is to replicate (or partially replicate) a pump
onto another that would not be allowed to acquire the products directly (PAZ, or 
firewalled network pump)...  or to provide direct file delivery to clients.
For this second objective, we added **metpx-sundew** like options and behaviors.

The **sr_sender** command takes two argument: a configuration file described below,
followed by an action start|stop|restart|reload|status... (self described).

The **foreground** action is different. It would be used when building a configuration
or debugging things. It is used when the user wants to run the program and its configfile 
interactively...   The **foreground** instance is not concerned by other actions, 
but should the configured instances be running it shares the same (configured) message queue.
The user would stop using the **foreground** instance by simply pressing <ctrl-c> on linux 
or use other means to kill its process.

In general, the options for this component are described by the
`sr_config(7) <sr_config.7.html>`_  page which should be read first.
It fully explains the option configuration language, and how to find
the option settings.

sr_sender is a standard consumer, using all the normal AMQP settings for brokers,exchanges,
queues, and all the standard client side filtering with accept, reject, on_message.


SOURCE NOTIFICATION OPTIONS
---------------------------

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


QUEUE BINDINGS OPTIONS
----------------------

First, the program needs to set all the rabbitmq configurations for a source broker.
These options define which messages (URL notifications) the program receives:

- **exchange      <name>         (default: xpublic)** 
- **topic_prefix  <name>         (default: v02.post)**
- **subtopic      <amqp pattern> (default: #)**

as described in `sr_config(7) <sr_config.7.html>`_  

MESSAGE SELECTION OPTIONS 
-------------------------

 - **accept        <regexp pattern> (default: None)** 
 - **reject        <regexp pattern> (default: None)** 
 - **on_message            <script> (default: None)** 

as described in `sr_config(7) <sr_config.7.html>`_  

One has the choice of filtering using  **subtopic**  with only AMQP's limited 
wildcarding, and/or with the more powerful regular expression based  **accept/reject**  
mechanisms described below.  The difference being that the AMQP filtering is 
applied by the broker itself, saving the notices from being delivered to the 
client at all. The  **accept/reject**  patterns apply to messages sent by the 
broker to the subscriber.  In other words,  **accept/reject**  are client 
side filters, whereas  **subtopic**  is server side filtering.  

It is best practice to use server side filtering to reduce the number of 
announcements sent to the client to a small superset of what is relevant, and 
perform only a fine-tuning with the client side mechanisms, saving bandwidth 
and processing for all.

The user can provide an **on_message** script. When a message is accepted up 
to this level of verification, the **on_message** script is called... with 
the **sr_sender** class instance as argument.  The script can perform whatever 
you want... if it returns False, the processing of the message will stop 
there. If True, the program will continue processing from there.  

If a **post_broker** is set, **sr_sender** checks if the clustername given
by the **to** option if found in one of the message's destination clusters.
If not, the message is skipped.


SETUP 1 : PUMP TO PUMP REPLICATION 
----------------------------------

 - **mirror             <boolean>   (default: True)** 
 - **document_root      <directory> (None)** 

 - **destination        <url>       (MANDATORY)** 
 - **do_send            <script>    (None)** 
 - **kbytes_ps          <int>       (default: 0)** 
 - **post_document_root <directory> (default: '')** 

 - **to               <clustername> (default: None)** 
 - **on_post           <script>     (default: None)** 
 - **post_broker        amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**
 - **url                <url>       (default: destination)** 

For pump replication, **mirror** is set to True (default)

**document_root** supplies the directory path that, when combined with the relative
one in the selected notification gives the absolute path of the file to be sent.
The defaults is None which means that the path in the notification is the absolute one.

The **destination** defines the protocol and server to be used to deliver the products.
Its form is a partial url, for example:  **ftp://myuser@myhost**
The program uses the file ~/.conf/sarra/credentials.conf to get the remaining details
(password and connection options).  Supported protocol are ftp,ftps and sftp. Should the
user need to implement another sending mechanism, he would provide the plugin script 
through option **do_send**.

On the remote site, the **post_document_root** serves the same purpose as the
**document_root** on this server.  The defaults is None which means that the delivered path
is the absolute one.

Now we are ready to send the product... For example, if the selected notification looks like this :

**20150813161959.854 http://this.pump.com/ relative/path/to/IMPORTANT_product**

**sr_sender**  performs the following pseudo-delivery:

sends local file [**document_root**]/relative/path/to/IMPORTANT_product
to    **destination**/[**post_document_root**]/relative/path/to/IMPORTANT_product
(**kbytes_ps** is greater than 0, the process attempts to respect this delivery speed... ftp,ftps,or sftp)

At this point, a pump to pump setup need needs to send the remote notification...
(If the post_broker is not set, there will be no posting... just products replication)

The selected notification contains all the right informations 
(topic and header attributes) except for url field in the
notice... in our example :  **http://this.pump.com/**

By default, **sr_sender** puts the **destination** in that field. 
The user can overwrite this by specifying the option **url**. For example:

**url http://remote.apache.com**

The user can provide an **on_post** script. Just before the message gets
publish to the **post_broker** and under the **post_exchange**, the 
**on_post** script is called... with the **sr_sender** class instance as argument.
The script can perform whatever you want... if it returns False, the message will not 
be published. If True, the program will continue processing from there.  


DESTINATION SETUP 2 : METPX-SUNDEW LIKE DISSEMINATION
-----------------------------------------------------

In this type of usage, we would not usually repost... but if the 
**post_broker** and **post_exchange** (**url**,**on_post**) are set,
the product will be announced (with its possibly new location and new name)
Lets reintroduce the options in a different order 
with some new ones  to ease explanation.


 - **mirror             <boolean>   (default: True)** 
 - **document_root      <directory> (None)** 

 - **destination        <url>       (MANDATORY)** 
 - **post_document_root <directory> (default: '')** 

 - **directory          <path>      (MANDATORY)** 
 - **on_message            <script> (default: None)** 
 - **accept        <regexp pattern> (default: None)** 
 - **reject        <regexp pattern> (default: None)** 

There are 2 differences with the previous case : 
the **directory**, and the **filename** options.

The **document_root** is the same, and so are the
**destination**  and the **post_document_root** options.

The **directory** option defines another "relative path" for the product
at its destination.  It is tagged to the **accept** options defined after it.
If another sequence of **directory**/**accept** follows in the configuration file,
the second directory is tagged to the following accepts and so on.

The  **accept/reject**  patterns apply to message notice url as above.
Here is an example, here some ordered configuration options :

::

  directory /my/new/important_location

  accept .*IMPORTANT.*

  directory /my/new/location/for_others

  accept .*

If the notification selected is, as above, this :

**20150813161959.854 http://this.pump.com/ relative/path/to/IMPORTANT_product**

It was selected by the first **accept** option. The remote relative path becomes
**/my/new/important_location** ... and **sr_sender**  performs the following pseudo-delivery:

sends local file [**document_root**]/relative/path/to/IMPORTANT_product
to    **destination**/[**post_document_root**]/my/new/important_location/IMPORTANT_product


Usually this way of using **sr_sender** would not require posting of the product.
But if **post_broker** and **post_exchange** are provided, and **url** , as above, is set to
**http://remote.apache.com**,  than **sr_sender** would reconstruct :

Topic:
**v02.post.my.new.important_location.IMPORTANT_product**

Notice:
**20150813161959.854 http://remote.apache.com/ my/new/important_location/IMPORTANT_product**



SEE ALSO
========

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcements.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`dd_subscribe(1) <dd_subscribe.1.html>`_ - the http-only download client.
