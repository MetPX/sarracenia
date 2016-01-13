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

**sr_sender** configfile start|stop|restart|reload|status

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
firewalled network pump)...  But we discovered that, if we do not have to repost
the notification, it can serves as a product disseminator. For this second objective
we added **metpx-sundew** like options and option behaviors.

The **sr_sender** command takes two argument: a configuration file described below,
followed by an action start|stop|restart|reload|status... (self described).

CONFIGURATION
=============

Options are placed in the configuration file, one per line, of the form: 

**option <value>** 

Comment lines begins with **#**. 
Empty lines are skipped.
For example:

**debug true**

would be a demonstration of setting the option to enable more verbose logging.
The configuration default for all sr_* commands is stored in 
the ~/.config/sarra/default.conf file, and while the name given on the command 
line may be a file name specified as a relative or absolute path, sr_sender 
will also look in the ~/.config/sarra/sender directory for a file 
named *config.conf*  The configuration in specific file always overrides
the default, and the command line overrides any configuration file.

CREDENTIALS 
-----------

Ther username and password or keys used to access servers are credentials.
For all **sarracenia** programs, the confidential parts of credentials are stored
only in ~/.conf/sarra/credentials.conf.  This includes the destination and the broker
passwords and settings needed by **sr_sender**.  The format is one entry per line.  Examples:

- **amqp://user1:password1@host/**
- **amqps://user2:password2@host:5671/dev**

- **sftp://user5:password5@host**
- **sftp://user6:password6@host:22  ssh_keyfile=/users/local/.ssh/id_dsa**

- **ftp://user7:password7@host  passive,binary**
- **ftp://user8:password8@host:2121  active,ascii**

- **ftps://user7:password7@host  passive,binary,tls**
- **ftps://user8:password8@host:2121  active,ascii,tls,prot_p**

In other configuration files or on the command line, the url simply lacks the 
password or key specification.  The url given in the other files is looked 
up in credentials.conf. 

INSTANCES
---------

It is possible that one instance of sr_sender using a certain config
is not enough to process & send all available notifications.

**instances      <integer>     (default:1)**

Invoking the command::

  sr_sender "configname" start 

will result in launching N instances of sr_sender using that config.
In the ~/.cache/sarra directory, a number of runtime files are created::

  A .sr_sender_configname_$instance.pid is created, containing the PID  of $instance process.
  A sr_sender_configname_$instance.log  is created as a log of $instance process.

The logs can be written in another directory than the default one with option :

**log            <directory logpath>  (default:~/.cache/sarra/log)**


.. NOTE:: 
  FIXME: standard installation/setup explanations ...



SOURCE NOTIFICATION OPTIONS
---------------------------

First, the program needs to set all the rabbitmq configurations for a source 
broker.  The broker option sets all the credential information to connect 
to the **AMQP** server 

**broker amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: None and it is mandatory to set it ) 


Once connected to an AMQP broker, the user needs to bind a queue
to exchanges and topics to determine the messages of interest.

QUEUE BINDINGS OPTIONS
----------------------

First, the program needs to set all the rabbitmq configurations for a source broker.
These options define which messages (URL notifications) the program receives:

- **exchange      <name>         (default: xpublic)** 
- **topic_prefix  <name>         (default: v02.post)**
- **subtopic      <amqp pattern> (default: #)**

topic_prefix is primarily of interest during protocol version transitions,
where one wishes to specify a non-default protocol version of messages to subscribe to. 

To give a correct value to the subtopic, browse the remote server and
write down the directory of interest separated by a dot
as follow:

 **subtopic  directory1.*.subdirectory3.*.subdirectory5.#** 

::

 where:  
       *                replaces a directory name 
       #                stands for the remaining possibilities

The concatenation of the topic_prefix + . + subtopic gives the AMQP topic
One has the choice of filtering using  **topic**  with only AMQP's limited 
wildcarding. 

QUEUE SETTING OPTIONS
---------------------

 - **queue_name   <string>          (default: None)** 
 - **queue_share  <boolean>         (default: True)** 
 - **durable      <boolean>         (default: False)** 
 - **expire       <minutes>         (default: None)**
 - **message-ttl  <minutes>         (default: None)**

These options (except for queue_share)  are all AMQP queue attributes.
If a **queue_name** is not provided, it is automatically build by the program.
The name has the form :  q\_'brokerUsername'.sr_sender.'config_name'
It is easier to have this fix name when it is time to look on the broker
and determine the queue of the program... to see if it is in problem 
for example... you exactly know for which program/config it belongs to.

The option **queue_share** defaults to True because most of the time
sr_sender is used with multiple instances sharing the same queue.

MESSAGE SELECTION OPTIONS 
-------------------------

 - **accept        <regexp pattern> (default: None)** 
 - **reject        <regexp pattern> (default: None)** 
 - **on_message            <script> (default: None)** 

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


BROKER LOGGING OPTIONS
----------------------

 - **log_exchange     <nane>   (default xlog)**

The state and actions performed with the messages/products of the broker
are logged back to it again through AMQP LOG MESSAGES.  When the broker
sends products to a destination it logs it to the
**log_exchange**. The default is 'xlog'.  


SUNDEW COMPATIBILITY OPTIONS
----------------------------

**destfn_script <script> (default:None)**

This option defines a script to be run when everything is ready
for the delivery of the product.  The script receives the sr_sender class
instance.  If you receive it as argument parent for example than any
modification to  **parent.remote_file**  will set a new destination filename

**filename <keyword> (default:WHATFN)**

From **metpx-sundew** the support of this option give all sorts of possibilities
for setting the remote filename. Some **keywords** are based on the fact that
**metpx-sundew** filenames are five (to six) fields strings separated by for colons.
The possible keywords are :

WHATFN      
  the first part of the metpx filename (string before first :)

HEADFN      
  HEADER part of the metpx filename

SENDER      
  the metpx filename may end with a string SENDER=<string>
  in this case the <string> will be the remote filename

NONE        
  deliver with the complete metpx filename (without :SENDER=...)

NONESENDER  
  deliver with the complete metpx filename (with :SENDER=...)

TIME        
 time stamp appended to filename. Example of use: WHATFN:TIME

DESTFN=str  
 direct filename declaration str

SATNET=1,2,3,A  
 cmc internal satnet application parameters

DESTFNSCRIPT=script.py  
 invoke a script (same as destfn_script) to generate the name of 
 the file to write.


**accept <regexp pattern> [<keyword>]**

A keyword can be added to the **accept** option. The keyword is any one of the **filename**
option.  A message that matched against the accept regexp pattern, will have its remote_file
applied this keyword option.  This keyword has priority over the preceeding **filename** one.

The **regexp pattern** can be use to set directory parts if part of the message is put
into parenthesis. **sr_sender** can use these parts to build the directory name. The
first enclosed parenthesis strings will replace keyword **${0}** in the directory name...
the second **${1}** etc.



Example of use:

::
        filename NONE

        directory /this/first/target/directory

        accept .*file.*type1.*

        directory /this/target/directory

        accept .*file.*type2.*

        accept .*file.*type3.*  DESTFN=file_of_type3

        directory /this/${0}/pattern/${1}/directory

        accept .*(2016....).*(RAW.*GRIB).*

A selected message from the first accept would be delivered unchanged to the first directory.
A selected message from the second accept would be delivered unchanged to the second directory.
A selected message from the third  accept would be renamed "file_of_type3" in the second directory.
A selected message from the forth  accept would be delivered unchanged to a directory
named  /this/20160123/pattern/RAW_MERGER_GRIB/directory   if the message would have a notice like :

**20150813161959.854 http://this.pump.com/ relative/path/to/20160123_product_RAW_MERGER_GRIB_from_CMC**

SEE ALSO
========

`sr_log(7) <sr_log.7.html>`_ - the format of log messages.

`sr_post(1) <sr_post.1.html>`_ - post announcemensts of specific files.

`sr_post(7) <sr_post.7.html>`_ - The format of announcements.

`sr_subscribe(1) <sr_subscribe.1.html>`_ - the download client.

`sr_watch(1) <sr_watch.1.html>`_ - the directory watching daemon.

`dd_subscribe(1) <dd_subscribe.1.html>`_ - the http-only download client.
