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

**sr_sender** foreground|start|stop|restart|reload|status configfile

**sr_sender** cleanup|declare|setup configfile

DESCRIPTION
===========

**sr_sender** is a component derived from `sr_subscribe(1) <sr_subscribe.1.html>`_
used to send loca files to a remote one using a file transfer protocol, primarily SFTP.
**sr_sender** is a standard consumer, using all the normal AMQP settings for brokers,exchanges,
queues, and all the standard client side filtering with accept, reject, on_message.

Often, a broker will announce files using a remote protocol such as HTTP,
but for the sender it is actually a local file.  In such cases, one will
see a message: **ERROR: The file to send is not local.** 
An on message plugin will convert the web url into a local file one::

  document_root /var/httpd/www
  on_message msg_2localfile

This on_message plugin is part of the default settings for senders, but one
still needs to specify document_root for it to function.

If a **post_broker** is set, **sr_sender** checks if the clustername given
by the **to** option if found in one of the message's destination clusters.
If not, the message is skipped.


DESTINATION UNAVAILABLE
-----------------------

If the server to which the files are being sent is going to be unavailable for 
a prolonged period, and there is a large number of messages to send to them, then
the queue will build up on the broker. As the performance of the entire broker
is affected by large queues, one needs to minimize such queues.

The *-save* and *-restore* options are used get the messages away from the broker
when too large a queue will certainly build up.
The *-save* option copies the messages to a (per instance) disk file (in the same directory
that stores state and pid files), as json encoded strings, one per line.
When a queue is building up::

   sr_sender stop <config> 
   sr_sender -save start <config> 

And run the sender in *save* mode (which continually writes incoming messages to disk)
in the log, a line for each message written to disk::

  2017-03-03 12:14:51,386 [INFO] sr_sender saving 2 message topic: v02.post.home.peter.sarra_devdocroot.sub.SASP34_LEMM_031630__LEDA_60215

Continue in this mode until the absent server is again available.  At that point::

   sr_sender stop <config> 
   sr_sender -restore start <config> 

While restoring from the disk file, messages like the following will appear in the log::

  2017-03-03 12:15:02,969 [INFO] sr_sender restoring message 29 of 34: topic: v02.post.home.peter.sarra_devdocroot.sub.ON_02GD022_daily_hydrometric.csv


After the last one::

  2017-03-03 12:15:03,112 [INFO] sr_sender restore complete deleting save file: /home/peter/.cache/sarra/sender/tsource2send/sr_sender_tsource2send_0000.save 


and the sr_sender will function normally thereafter.



SETUP 1 : PUMP TO PUMP REPLICATION 
----------------------------------

 - **mirror             <boolean>   (default: True)** 
 - **document_root      <directory> (None)** 

 - **destination        <url>       (MANDATORY)** 
 - **do_send            <script>    (None)** 
 - **kbytes_ps          <int>       (default: 0)** 
 - **post_document_root <directory> (default: '')** 

 - **to               <clustername> (default: <post_broker host>)** 
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

`sr_subscribe(7) <sr_subscribe.7.html>`_ - the format of configurations for MetPX-Sarracenia.

`sr_report(7) <sr_report.7.html>`_ - the format of report messages.

`sr_report(1) <sr_report.1.html>`_ - process report messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcements.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`dd_subscribe(1) <dd_subscribe.1.html>`_ - the http-only download client.
