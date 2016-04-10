
=====================================
 MetPX-Sarracenia for Administrators
=====================================

.. note::
   Pardon the dust, This package is alpha, not ready for general use yet. Please Stay Tuned!  

   **FIXME**: Missing sections are highlighted by **FIXME**.  What is here should be accurate!

.. Contents::


Revision Record
---------------

.. warning:: 
   **Pre-Draft.**  This document is still being built and should not be reviewed or relied upon.

:version: @Version@ 
:date: @Date@



Introduction
------------

Sarracenia pumps form a network.  The network use rabbitmq brokers as a transfer manager
which sends advertisements in one direction and log messages in the opposite direction.
Administrators configure the paths that data flows through at each pump, as each broker acts 
independently, managing transfers from transfer engines it can reach, with no knowledge of 
the overall network.  The locations of pump and the directions of traffic flow are 
chosen to work with permitted flows.  Ideally, no firewall exceptions are needed.

Sarracenia does no data transport.  It is a management layer to co-ordinate the use of
transport layers.  So to get a running pump, actual transport mechanisms need to be set up
as well.  The two mechanisms currently supported are web servers, and SFTP.  In the simplest
case, all of the components are on the same server, but there is no need for that.  the
broker could be on a different server from both ends of a given hop of a data transfer.

The best way for data transfers to occur is to avoid polling (use of sr_watch.) It is more
efficient if writers can be coaxed into emitting appropriate sr_post messages.  Similarly, 
when delivering, it is ideal if the receivers use sr_subscribe, and a on_file plugin
to trigger their further processing, so that the file is handed to them without polling.
This is the most efficient way of working, but it is understood that not all software
can be made co-operative.

Generally speaking, Linux is the main deployment target, and the only platform on which
server configurations are deployed.  Other platforms are used as client end points.
This isn´t a limitation, it is just what is used and tested.  Implementations of
the pump on Windows should work, they just are not tested.

Minimum Requirements
~~~~~~~~~~~~~~~~~~~~

The AMQP broker is extremely light on today's servers.  The examples in this manual were implemented
on a commercial virtual private server (VPS) with 256 MB of RAM, and 700MB of swap taken from a 20 GByte 
disk. Such a tiny configuration is able to keep up with almost a full feed from dd.weather.gc.ca
(which includes, all public facing weather and environmental data from Environment and Climate Change
Canada.) the large numerical prediction files (GRIB and multiple GRIB's in tar files) were excluded
to reduce bandwidth usage, but in terms of performance in message passing, it kept up with one client
quite well.

Each Sarra process is around 80 mb of virtual memory, but only about 3 mb is resident, and you need to run
enough of them to keep up (on the small VPS, ran 10 of them.)  so about 30 mbytes of RAM actually used.
The broker's RAM usage is what determines the number of clients which can be served.  Slower clients require
more RAM for their queues.  So running brokerage tasks and aggressive cleaning can reduce the overall 
memory footprint.  The broker was configured to use 128 MB of RAM in the examples in this manual.
The rest of the RAM was used by the apache processes for the web transport engine.

While the above was adequate for proof of concept, it would be impractical to be clearing out
data from disk after only an hour, and the number of clients supportable is likely quite limited.
1GB of RAM for all the sarra related activities should be ample for many useful cases.


IPv6
~~~~

The configuration shown in this manual was implemented on a small VPS with IPv6 enabled.  A client 
from far away connected to the rabbitmq broker using IPv6, and the subscription to the apache httpd
worked without issues.  It just works.  There is no difference between IPv4 and IPv6 for sarra tools,
which are agnostic of IP addresses.  

On the other hand, one is expected to use hostnames, since use of IP addresses will break certificate
use for securing the transport layer (TLS, aka SSL) No testing of ip addresses in URLs (in either IP 
version) has been done. 


Mapping AMQP Concepts to Sarracenia
-----------------------------------

One thing that is safe to say is that one needs to understand a bit about AMQP to work 
with Sarracenia.  AMQP is a vast and interesting topic in it's own right.  No attempt is 
made to explain all of it here. This section just provides a little context, and introduces 
only background concepts needed to understand and/or use Sarracenia.  For more information 
on AMQP itself, a set of links is maintained at 
the `Metpx web site <http://metpx.sourceforge.net/#amqp>`_ but a search engine
will also reveal a wealth of material.

.. image:: AMQP4Sarra.svg
    :scale: 50%
    :align: center

An AMQP Server is called a Broker. *Broker* is sometimes used to refer to the software,
other times server running the broker software (same confusion as *web server*.) In the 
above diagram, AMQP vocabulary is in Orange, and Sarracenia terms are in blue.  There are 
many different broker software implementations. We use rabbitmq.  We are not trying to 
be rabbitmq specific, but management functions differ between implementations.  

*Queues* are usually taken care of transparently, but you need to know
   - A Consumer/subscriber creates a queue to receive messages.
   - Consumer queues are *bound* to exchanges (AMQP-speak) 

An *exchange* is a matchmaker between *publisher* and *consumer* queues.
   - A message arrives from a publisher. 
   - message goes to the exchange, is anyone interested in this message?
   - in a *topic based exchange*, the message topic provides the *exchange key*.
   - interested: compare message key to the bindings of *consumer queues*.
   - message is routed to interested *consumer queues*, or dropped if there aren't any.
   
- Multiple processes can share a *queue*, they just take turns removing messages from it.
   - This is used heavily for sr_sarra and sr_subcribe multiple instances.

- *Queues* can be *durable*, so even if your subscription process dies, 
  if you come back in a reasonable time and you use the same queue, 
  you will not have missed any messages.

- How to Decide if Someone is Interested.
   - For Sarracenia, we use (AMQP standard) *topic based exchanges*.
   - Subscribers indicate what topics they are interested in, and the filtering occurs server/broker side.
   - Topics are just keywords separated by a dot. wildcards: # matches anything, * matches one word.
   - We create the topic hierarchy from the path name (mapping to AMQP syntax)
   - Resolution & syntax of server filtering is set by AMQP. (. separator, # and * wildcards)
   - Server side filtering is coarse, messages can be further filtered after download using regexp on the actual paths (the reject/accept directives.)

- topic prefix?  We start the topic tree with fixed fields
     - v02 the version/format of sarracenia messages.
     - post ... the message type, this is an announcement 
       of a file (or part of a file) being available.  


Sarracenia is an AMQP Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MetPX-Sarracenia is only a light wrapper/coating around AMQP.  

- A MetPX-Sarracenia data pump is a python AMQP application that uses a (rabbitmq) 
  broker to co-ordinate SFTP and HTTP client data transfers, and accompanies a 
  web server (apache) and sftp server (openssh), often on the same user-facing address.  

- Wherever reasonable, we use their terminology and syntax. 
  If someone knows AMQP, they understand. If not, they can research.

  - Users configure a *broker*, instead of a pump.
  - by convention, the default vhost '/' is always used. (did not feel the need to use other vhosts yet)
  - users explicitly can pick their *queue* names.
  - users set *subtopic*, 
  - topics with dot separator are minimally transformed, rather than encoded.
  - queue *durable*. 
  - we use *message headers* (AMQP-speak for key-value pairs) rather than encoding in JSON or some other payload format.

- reduce complexity through conventions.
   - use only one type of exchanges (Topic), take care of bindings.
   - naming conventions for exchanges and queues.
      - exchanges start with x. 
        - xs_Weather - the exchange for the source (amqp user) named Weather to post messages
        - xpublic -- exchange used for most subscribers.
      - queues start with q\_

A lot of the processes in this guide cover rabbitmq administration because those are
the tasks required to operate a sarracenia pump.


Flow Through Exchanges
----------------------

.. image:: e-ddsr-components.jpg
    :scale: 100%
    :align: center



A description of the conventional flow of messages through exchanges on a pump:

- subscribers usually bind to the xpublic exchange to get the main data feed.
  this is the default in sr_subscribe.

- A user named Alice will have two exchanges:

  - xs_Alice the exhange where Alice posts her files and log messages.(via many tools)
  - xl_Alice the exchange where Alice reads her log messages from (via sr_log)

- usually sr_sarra will read from xs_alice, retrieve the data corresponding to Alice´s *post* 
  message, and make it available on the pump, by re-announcing it on the xpublic exchange.

- sr_winnow may pull from xs_alice instead, but follows the same pattern as sr_sarra.

- usually, sr_2xlog will read xs_alice and copy the log messages onto the private xlog exchange.

- Admins can point sr_log at the xlog exchange to get system-wide monitoring.
  Alice will not have permission to do that, she can only look at xl_Alice, which should have
  the log messages pertinent to her.

- sr_log2source looks at messages for the local Alice user in xlog, and sends them to xl_Alice.

- sr_log2cluster looks at messages in xlog, and send messages for remote users to the appropriate
  remote cluster.

The purpose of these conventions is to encourage a reasonably secure means of operating.
If a message is taken from xs_Alice, then the process doing the reading is responsible for 
ensuring that it is tagged as coming from Alice on this cluster.  This prevents certain 
types of ´spoofing´ as messages can only be posted by proper owners.


Users and Roles
---------------

Usernames for pump authentication are significant in that they are visible to all.
They are used in the directory path on public trees, as well as to authenticate to the broker.
They need to be understandable.  they are often wider scope than a person...
perhaps call them 'Accounts'.   It can be elegant to configure the same usernames
for use in transport engines.

All Account names should be unique, but nothing will avoid clashes when sources originate from
different pump networks, and clients at different destinations.  In practice, name clashes are
addressed by routing to avoid two different sources' with the same name having their 
data offerings combined on a single tree.  On the other hand, name clashes are not always an error.  
Use of a common source account name on different clusters may be used to implement folders that
are shared between the two accounts with the same name.  

Pump users are defined with the *role* option. Each option starts with the *role*
keyword, followed by the specified role, and lastly the user name which has that role.
role can be one of:

subscriber

  A subscriber is user that can only subscribe to data and return log messages. Not permitted to inject data.
  Each subscriber gets an xs_<user> named exchange on the pump, where if a user is named *Acme*, 
  the corresponding exchange will be *xs_Acme*.  This exchange is where an sr_subscribe
  process will send it's log messages.

  By convention/default, the *anonymous* user is created on all pumps to permit subscription without
  a specific account. 

source

  A user permitted to subscribe or originate data.  A source does not necessarily represent 
  one person or type of data, but rather an organization responsible for the data produced.  
  So if an organization gathers and makes available ten kinds of data with a single contact 
  email or phone number for questions about the data and it's availability, then all of 
  those collection activities might use a single 'source' account.
  
  Each source gets a xs_<user> exchange for injection of data posts, and, similar to a subscriber
  to send log messages about processing and receipt of data.

  Each source is able to view all of the messages for data it has injected, but the location where
  all of these messages are available varies according to administrator configuration of log routing.
  So a source may inject data on pumpA, but may subscribe to logs on a different pump. The logs
  corresponding to the data the source injected are written in exchange xl_<user>. 

  When a route injects data, the path is modified by sarracenia to prepend a fixed upper part
  of the directory tree.  The first level directory is the day of ingest into the network in 
  YYYYMMDD format.  The second level directory is the source name.  So for a user Alice, injecting
  data on May 4th, 2016, the root of the directory tree is:  20160504/Alice.  Note that all
  pumps are expected to run in the UTC timezone (widely, but inaccurately, referred to as GMT.)

  There are daily directories because there is a system-wide life-time for data, it is deleted
  after a standard number of days, data is just deleted from the root.

  Since all clients will see the directories, and therefore client configurations will include them.
  it would be wise to consider the account name public, and relatively static.

  Sources determine who can access their data, by specifying which cluster to send the data to.


.. note::
   restrictions by user name not yet implemented, but planned.

   FIXME: monitor role is missing.  someone who can read all logs, but not change anything.
   Ideal for service desks, and security monitoring.

feeder

  a user permitted to subscribe or originate data, but understood to represent a pump.
  this local pump user would be used to, run processes like sarra, log2source, 2xlog,
  log2cluster... etc


admin
  a user permitted to manage the local pump.  
  It is the real rabbitmq-server administrator.
  The administrator runs sr_audit to create/delete
  exchanges, users, or clean unused queues... etc.

Example of a complete valid default.conf, for a host named *blacklab* ::
 
  cluster blacklab
  admin amqps://hbic@blacklab/
  feeder  amqps://feeder@blacklab/
  role source goldenlab 
  role subscriber anonymous

A corresponding credentials.conf would look like::

  amqps://hbic:hbicpw@blacklab/
  amqps://feeder:feederpw@blacklab/
  amqps://goldenlab:puppypw@blacklab/
  amqps://anonymous:anonymous@blacklab/
  


Transport Engines
-----------------

Transport engines are the data servers queried by subscribers, by the end users, or other pumps.
The subscribers read the notices and fetch the corresponding data, using the indicated protocol.
The software to serve the data can be either SFTP or HTTP (or HTTPS.) For specifics of 
configuring the servers for use, please consult the documentation of the servers themselves.


Operations
----------

To operate a pump, there needs to be a user designated as the pump administrator.
The administrator is different from the others mostly in the permission granted
to create exchanges, and the ability to run processes that address the common
exchanges (xpublic, xlog, etc...) All other users are limited to being able to 
access only their own resources (exchange and queues).

The administrative user name is an installation choice, and exactly as for any other 
user, the configuration files are placed under ~/.config/sarra/, with the 
defaults under default.conf, and the configurations for components under
directories named after each component.  In the component directories,
Configuration files have the .conf suffix.  

The administrative processes perform validation of postings from sources. Once
they are validated, forward the postings to the public exchanges for subscribers to access.
The processes that are typically run on a broker:

- sr_audit   - purge useless queues, create exchanges and users, set user permissions according to their roles.
- sr_poll    - for sources without advertisements, revert to explicit polling for initial injection.
- sr_sarra   - various configurations to pull data from other pumps to make it available from the local pump.
- sr_sender  - send data to clients or other pumps that cannot pull data (usually because of firewalls.)
- sr_winnow  - when there are multiple redundant sources of data, select the first one to arrive, and feed sr_sarra.
- sr_shovel  - copy advertisements from pump to another, usually to feed sr_winnow.
- sr_log2cluster - copy log messages from the xlog exchange for data that came from another cluster, to where they should go.
- sr_2xlog   - copy log message is posted users on this cluster to the xlog exchange. 
- sr_log2source - copy log messages from the xlog exchange to the source that should get it.

As for any other user, there may be any number of configurations
to set up, and all of them may need to run at once.  To do so easily, one can invoke:

  sr start

to start all the files with named configurations of each component (sarra, subscribe, winnow, log, etc...)
There are two users/roles that need to be set to use a pump. They are the admin and feeder options.
They are set in ~/.config/sarra/default.conf like so:

  feeder amqp://pumpUser@localhost/
  admin  amqps://adminUser@boule.example.com/

Then the log and audit components are started as well.  It is standard practice to use a different
AMQP user for administrative tasks, such as exchange or user creation, which are performed by the admin
user,  from data flow tasks, such as pulling and posting data, performed by the feeder user.
Normally one would place credentials in ~/.config/sarra/credentials.conf
for each account, and the various configuration files would use the appropriate account.




Housekeeping - sr_audit
~~~~~~~~~~~~~~~~~~~~~~~~

When a client connects to a broker, it creates a queue which is then bound to an exchange.  The user 
can choose to have the client self-destruct when disconnected (*auto-delete*), or it can make 
it *durable* which means it should remain, waiting for the client to connect again, even across
reboots.  Clients often want to pick up where they left off, so the queues need to stay around.

sr_audit

The rabbitmq broker will never destroy a queue that is not in auto-delete (or durable.)  This means
they will build up over time.  We have a script that looks for unused queues, and cleans them out.
Currently, the default is set that any unused queue having more than 25000 messages will be deleted.
One can change this limit by having  option *max_queue_size 50000* in default.conf.

Routing
-------

Data
~~~~

The inter-connection of multiple pumps is done, on the data side, simply by daisy-chaining
sr_sarra configurations from one pump to the next.  Each sr_sarra link is configured by:

.. note::
  FIXME: sample sender to push to another pump.
  describe the to_cluster, gateway_for , and cluster options.

Logs
~~~~

Log messages are defined in the sr_log(7) man page.  They are emitted by *consumers* at the end,
as well as *feeders* as the messages traverse pumps.  log messages are posted to
the xl_<user> exchange, and after log validation sent to the xlog exchange by the 2xlog component.

Messages in xlog destined for other clusters are routed to destinations by
log2cluster component using log2cluster.conf configuration file.  log2cluster.conf
uses space separated fields: First field is the cluster name (set as per **cluster** in
post messages, the second is the destination to send the log messages for posting
originating from that cluster to) Sample, log2cluster.conf::

      clustername amqp://user@broker/vhost exchange=xlog

Where message destination is the local cluster, log2source will copy
the messages where source=<user> to xl_<user>, ready for consumption by sr_log.


What is Going On?
-----------------

The sr_log command can be invoked to bind to 'xlog' instead of the default user exchange
to get log information for an entire broker.


Canned sr_log configuration with an *on_message* action can be configured to 
gather statisical information. 

.. NOTE::
   FIXME:
   first canned sr_log configuration would be speedo...
   speedo: total rate of posts/second, total rate of logs/second.
   question: should posts go to the log as well?
   before operations, we need to figure out how Nagios will monitor it.

   sr_log is weird... works on one server, but not another... dunno bug?
   more testing needed.

   Is any of this needed, or is the rabbit GUI enough on it's own?



Rabbitmq Setup 
--------------

Sample information on setting up a rabbitmq broker for sarracenia to use.  The broker does not have to 
be on the same host as anything else, but there has to be one reachable from at least one of the 
transport engines.


Installation
~~~~~~~~~~~~

Generally speaking, we want to stay above 3.x version.  

https://www.rabbitmq.com/install-debian.html

.. Briefly::

 apt-get update
 apt-get install erlang-nox
 apt-get install rabbitmq-server

in upto-date distros, you likely can just take the distro version.


WebUI 
~~~~~

Sr_audit makes use of a variety of calls to the web management interface.
sr_audit is the component which, as the name implies, audits configurations
for left over queues, or attempts at malicious usage.  Without this sort 
of auditing, the switch is likely to accumulate messages rapidly, which 
slows it down to a greater degree as the amount of messages pending increases
potentially overflowing to disk.

Basically, from a root shell one must::

 rabbitmq-plugins enable rabbitmq_management

which will enable the webUI for the broker.  To prevent access to the management
interface for undesirables, use of firewalls, or listening only to localhost
interface for the management ui is suggested.

TLS
~~~

One should encrypt broker traffic.  Obtaining certificates is outside the scope
of these instructions, so it is not discussed in detail.  For the purposes of
the example, one method is to obtain certificates from `letsencrypt <http://www.letsencrypt.org>`_ ::

    root@boule:~# git clone https://github.com/letsencrypt/letsencrypt
    Cloning into 'letsencrypt'...
    remote: Counting objects: 33423, done.
    remote: Total 33423 (delta 0), reused 0 (delta 0), pack-reused 33423
    Receiving objects: 100% (33423/33423), 8.80 MiB | 5.74 MiB/s, done.
    Resolving deltas: 100% (23745/23745), done.
    Checking connectivity... done.
    root@boule:~# cd letsencrypt
    root@boule:~/letsencrypt# 
    root@boule:~/letsencrypt# ./letsencrypt-auto certonly --standalone -d boule.example.com
    Checking for new version...
    Requesting root privileges to run letsencrypt...
       /root/.local/share/letsencrypt/bin/letsencrypt certonly --standalone -d boule.example.com
    IMPORTANT NOTES:
     - Congratulations! Your certificate and chain have been saved at
       /etc/letsencrypt/live/boule.example.com/fullchain.pem. Your
       cert will expire on 2016-06-26. To obtain a new version of the
       certificate in the future, simply run Let's Encrypt again.
     - If you like Let's Encrypt, please consider supporting our work by:
    
       Donating to ISRG / Let's Encrypt:   https://letsencrypt.org/donate
       Donating to EFF:                    https://eff.org/donate-le
    
    root@boule:~# ls /etc/letsencrypt/live/boule.example.com/
    cert.pem  chain.pem  fullchain.pem  privkey.pem
    root@boule:~#  

This process produces key files readable only by root.  To make the files
readable by the broker (which runs under the rabbitmq users name) one will have 
to adjust the permissions to allow the broker to read the files.
probably the simplest way to do this is to copy them elsewhere::

    root@boule:~# cd /etc/letsencrypt/live/boule*
    root@boule:/etc/letsencrypt/archive# mkdir /etc/rabbitmq/boule.example.com
    root@boule:/etc/letsencrypt/archive# cp -r * /etc/rabbitmq/boule.example.com
    root@boule:~# cd /etc/rabbitmq
    root@boule:~# chown -R rabbitmq.rabbitmq boule*

Now that we have proper certificate chain, configure rabbitmq to disable
tcp, and use only the `RabbitMQ TLS Support <https://www.rabbitmq.com/ssl.html>`_ (see 
also `RabbitMQ Management <https://www.rabbitmq.com/management.html>`_ )::

    root@boule:~#  cat >/etc/rabbitmq/rabbitmq.config <<EOT

    [
      {rabbit, [
         {tcp_listeners, [{"127.0.0.1", 5672}]},
         {ssl_listeners, [5671]},
         {ssl_options, [{cacertfile,"/etc/rabbitmq/boule.example.com/fullchain.pem"},
                        {certfile,"/etc/rabbitmq/boule.example.com/cert.pem"},
                        {keyfile,"/etc/rabbitmq/boule.example.com/privkey.pem"},
                        {verify,verify_peer},
                        {fail_if_no_peer_cert,false}]}
       ]}
      {rabbitmq_management, [{listener, 
         [{port,     15671},
               {ssl,      true},
               {ssl_opts, [{cacertfile,"/etc/rabbitmq/boule.example.com/fullchain.pem"},
                              {certfile,"/etc/rabbitmq/boule.example.com/cert.pem"},
                              {keyfile,"/etc/rabbitmq/boule.example.com/privkey.pem"} ]}
         ]} 
      ]}
    ].

    EOT

Now the broker and management interface are both configured to encrypt all traffic
passed between client and broker.  An unencrypted listener was configured for localhost, 
where encryption on the local machine is useless, and adds cpu load. But management only
has a single encrypted listener configured.

.. NOTE::

  currently, sr_audit expects the Management interface to be on port 15671 if encrypted,
  15672 otherwise.  Sarra has no configuration setting to tell it otherwise.  Choosing another 
  port will break sr_audit.  FIXME.


Change Defaults 
~~~~~~~~~~~~~~~

In order to perform any configuration changes the broker needs to be running.
One needs to start up the rabbitmq broker.  on older ubuntu systems, that would be done by::

  service rabbitmq-server start

on newer systems with systemd, the best method is::

  systemctl start rabbitmq-server 

By default, an installation of a rabbitmq-server makes user guest the administrator... with password guest.
With a running rabbitmq server, one can now change that for an operational implementation... 
To void the guest user we suggest::

  rabbitmqctl delete_user guest

Some other administrator must be defined... let's call it *bunnymaster*, setting the password to *MaestroDelConejito* ...::

  root@boule:~# rabbitmqctl add_user bunnymaster MaestroDelConejito
  Creating user "bunnymaster" ...
  ...done.
  root@boule:~# 

  root@boule:~# rabbitmqctl set_user_tags bunnymaster administrator
  Setting tags for user "bunnymaster" to [administrator] ...
  ...done.
  root@boule:~# rabbitmqctl set_permissions bunnymaster ".*" ".*" ".*"
  Setting permissions for user "bunnymaster" in vhost "/" ...
  ...done.
  root@boule:~# 

Create a local linux account under which sarra administrative tasks will run (say Sarra).
This is where credentials and configuration for pump level activities will be stored.
As the configuration is maintained with this user, it is expected to be actively used
by humans, and so should have a proper interactive shell environment.  Some administrative 
access is needed, so the user is added to the sudo group::

  root@boule:~# useradd -m sarra
  root@boule:~# usermod -a -G sudo sarra
  root@boule:~# mkdir ~sarra/.config
  root@boule:~# mkdir ~sarra/.config/sarra

first need entries in the credentials.conf and default.conf files::

  root@boule:~# echo "amqps://bunnymaster:MaestroDelConejito@boule.example.com/" >~sarra/.config/sarra/credentials.conf
  root@boule:~# echo "admin amqps://bunnymaster@boule.example.com/" >~sarra/.config/sarra/default.conf
  root@boule:~# chown -R sarra.sarra ~sarra/.config
  root@boule:~# passwd sarra
  Enter new UNIX password: 
  Retype new UNIX password: 
  passwd: password updated successfully
  root@boule:~# 
  root@boule:~# chsh -s /bin/bash sarra  # for comfort

When Using TLS (aka amqps), verification prevents the use of *localhost*. 
Even for access on the local machine, the fully qualified hostname must be used.
Next::

  root@boule:~#  cd /usr/local/bin
  root@boule:/usr/local/bin# wget https://boule.example.com:15671/cli/rabbitmqadmin
  --2016-03-27 23:13:07--  https://boule.example.com:15671/cli/rabbitmqadmin
  Resolving boule.example.com (boule.example.com)... 192.184.92.216
  Connecting to boule.example.com (boule.example.com)|192.184.92.216|:15671... connected.
  HTTP request sent, awaiting response... 200 OK
  Length: 32406 (32K) [text/plain]
  Saving to: ‘rabbitmqadmin’
  
  rabbitmqadmin              100%[=======================================>]  31.65K  --.-KB/s   in 0.04s  
  
  2016-03-27 23:13:07 (863 KB/s) - ‘rabbitmqadmin’ saved [32406/32406]
  
  root@boule:/usr/local/bin#  
  root@boule:/usr/local/bin# chmod 755 rabbitmqadmin

It is necessary to download *rabbitmqadmin*, a helper command that is included in RabbitMQ, but not installed automatically.
One must download it from the management interface, and place it in a reasonable location in the path, so
that it will be found when it is called by sr_admin::

  root@boule:/usr/local/bin#  su - sarra

From this point root will not usually be needed, as all configuration can be done from the
un-privileged *sarra* account.

.. NOTE::
   out of scope of this discussion, but aside from file system permissions, 
   it is convenient to provide the sarra user sudo access to rabbitmqctl. 
   With that, the entire system can be administered without system administrative access.


Managing Users on a Pump Using Sr_audit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To set up a pump, one needs a broker administrative user (in the examples: sarra.) 
and a feeder user (in the examples: feeder.) Management of other users is done with 
the sr_audit program.

First, write the correct credentials for the admin and feeder users in 
the credentials file  .config/sarra/credentials.conf ::

 amqps://bunnymaster:MaestroDelConejito@boule.example.com/
 amqp://feeder:NoHayPanDuro@localhost/
 amqps://feeder:NoHayPanDuro@boule.example.com/
 amqps://anonymous:anonyomous@boule.example.com/
 amqps://peter:piper@boule.example.com/

Note that the feeder credentials are presented twice, once to allow un-encrypted access via
localhost, and a second time to permit access over TLS, potentially from other hosts (necessary
when a broker is operating in a cluster, with feeder processes running on multiple transport
engine nodes.)  Next step is to put roles in .config/sarra/default.conf ::

 admin  amqps://root@boule.example.com/
 feeder amqp://feeder@localhost/

Specify all knows users that you want to implement with their roles 
in the file  .config/sarra/default.conf (user role)::

 role subscriber anonymous 
 role source peter

Now to configure the pump execute the following::

 *sr_audit --users foreground*

Sample run:: 

  sarra@boule:~/.config/sarra$ sr_audit --debug --users foreground
  2016-03-28 00:41:25,380 [INFO] sr_audit start
  2016-03-28 00:41:25,380 [INFO] sr_audit run
  2016-03-28 00:41:25,380 [INFO] sr_audit waking up
  2016-03-28 00:41:25,673 [INFO] adding user feeder
  2016-03-28 00:41:25,787 [INFO] permission user 'feeder' role feeder  configure='.*' write='.*' read='.*' 
  2016-03-28 00:41:25,897 [INFO] adding user peter
  2016-03-28 00:41:26,018 [INFO] permission user 'peter' role source  configure='^q_peter.*' write='^q_peter.*|^xs_peter$' read='^q_peter.*|^xl_peter$|^xpublic$' 
  2016-03-28 00:41:26,136 [INFO] adding user anonymous
  2016-03-28 00:41:26,247 [INFO] permission user 'anonymous' role source  configure='^q_anonymous.*' write='^q_anonymous.*|^xs_anonymous$' read='^q_anonymous.*|^xpublic$' 
  2016-03-28 00:41:26,497 [INFO] adding exchange 'xlog'
  2016-03-28 00:41:26,610 [INFO] adding exchange 'xpublic'
  2016-03-28 00:41:26,730 [INFO] adding exchange 'xs_peter'
  2016-03-28 00:41:26,854 [INFO] adding exchange 'xl_peter'
  2016-03-28 00:41:26,963 [INFO] adding exchange 'xs_anonymous'
  sarra@boule:~/.config/sarra$ 


The *sr_audit* program:

- uses the *admin* account from .config/sarra/default.conf to authenticate to broker.
- creates exchanges *xpublic* and *xlog* if they don't exist.
- reads roles from .config/sarra/default.conf
- obtains a list of users and exchanges on the pump
- for each user in a *role* option:: 

      declare the user on the broker if missing.
      set    user permissions corresponding to its role (on creation)
      create user exchanges   corresponding to its role
  
- users which have no declared role are deleted.
- user exchanges which do not correspond to users' roles are deleted ('xl_*,xs_*') 
- exchanges which do not start with 'x' (aside from builtin ones) are deleted.

.. Note:: 
   PS changed this so that with --users it exits after one pass... um.. not great ...
   but otherwise:
   The program runs as a daemon.  After the initial pass to create the users,
   It will go into to sleep, and then audit the configuration again.
   To stop it from running in the foreground, stop it with: <ctrl-c>  
   (most common linux default intterupt character)
   or find some other way to kill the running process.
   
   FIXME: when invoked with --users, sr_audit, should set a 'once' flag,
   and exist immediately, rather than looping.  

One can inspect whether the sr_audit command did all it should using either the Management GUI
or the command line tool::

  sarra@boule:~$ sudo rabbitmqctl  list_exchanges
  Listing exchanges ...
  	direct
  amq.direct	direct
  amq.fanout	fanout
  amq.headers	headers
  amq.match	headers
  amq.rabbitmq.log	topic
  amq.rabbitmq.trace	topic
  amq.topic	topic
  xl_peter	topic
  xlog	topic
  xpublic	topic
  xs_anonymous	topic
  xs_peter	topic
  ...done.
  sarra@boule:~$
  sarra@boule:~$ sudo rabbitmqctl  list_users
  Listing users ...
  anonymous	[]
  bunnymaster	[administrator]
  feeder	[]
  peter	[]
  ...done.
  sarra@boule:~$ sudo rabbitmqctl  list_permissions
  Listing permissions in vhost "/" ...
  anonymous	^q_anonymous.*	^q_anonymous.*|^xs_anonymous$	^q_anonymous.*|^xpublic$
  bunnymaster	.*	.*	.*
  feeder	.*	.*	.*
  peter	^q_peter.*	^q_peter.*|^xs_peter$	^q_peter.*|^xl_peter$|^xpublic$
  ...done.
  sarra@boule:~$ 

The above looks like *sr_audit* did it's job, but the *sr_audit* program does not set user passwords. 
To do it manually, one must use the root account on the pump (via sudo)::

  sudo rabbitmqctl change_password <user> <password>

example::

  sarra@boule:~% sudo rabbitmqctl change_password anonymous anonymous
  Changing password for user "anonymous" ...
  ...done.
  sarra@boule:~% sudo rabbitmqctl change_password feeder 'NoHayPanDuro'
  Changing password for user "feeder" ...
  ...done.
  sarra@boule:~% sudo rabbitmqctl change_password peter 'piper'
  Changing password for user "peter" ...
  ...done.
  sarra@boule:~% 

In short, here are the permissions and exchanges *sr_audit* manages::

  admin user        : the only one creating users...
  admin/feeder users: have all permission over queues and exchanges

  subscribe user    : can write log messages to exchange   xs_<brokerUser> created for him
                      can read post messages from exchange xpublic
                      have all permissions on queue named  q_<brokerUser>*

  source user       : can write post messages   to exchange xs_<brokerUser> created for him
                      can read post messages from exchange  xpublic
                      can read  log messages from exchange  xl_<brokerUser> created for him
                      have all permissions on queue named   q_<brokerUser>*


To add Alice using sr_audit, one would add the following to ~/.config/sarra/default.conf::

  role source Alice

then run:: 

  sr_audit --users foreground

which would create the user, then:
 
  rabbitmqctl change_password Alice <password>


To set Alice's password.   

To remove users, just remove *role source Alice* from the default.conf file, and run::

  sr_audit --users foreground 

again.  


First Subscribe
~~~~~~~~~~~~~~~

When setting up a pump, normally the purpose is to connect it to some other pump.  To set
the parameters setting up a subscription helps us set parameters for sarra later.  So first
try a subscription to an upstream pump::

  sarra@boule:~$ ls
  sarra@boule:~$ cd ~/.config/sarra/
  sarra@boule:~/.config/sarra$ mkdir subscribe
  sarra@boule:~/.config/sarra$ cd subscribe
  sarra@boule:~/.config/sarra/subscribe$  cat >dd.conf <<EOT
  broker amqp://anonymous@dd.weather.gc.ca/

  mirror True
  directory /var/www/html

  # numerical weather model files will overwhelm a small server.
  reject .*/\.tar
  reject .*/model_giops/.*
  reject .*/grib2/.*

  accept .*
  EOT

add the password for the upstream pump to credentials.conf ::

  sarra@boule:~/.config/sarra$ echo "amqp://anonymous:anonymous@dd.weather.gc.ca/" >>../credentials.conf

then do a short foreground run, to see if it is working. hit Ctrl-C to stop it after a few messages::

  2016-03-28 09:21:27,708 [INFO] sr_subscribe start
  2016-03-28 09:21:27,708 [INFO] sr_subscribe run
  2016-03-28 09:21:27,708 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2016-03-28 09:21:28,375 [INFO] Binding queue q_anonymous.sr_subscribe.dd.78321126.82151209 with key v02.post.# from exchange xpublic on broker amqp://anonymous@dd.weather.gc.ca/
  2016-03-28 09:21:28,933 [INFO] Received notice  20160328130240.645 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWRM/2016-03-28-1300-CWRM-AUTO-swob.xml
  2016-03-28 09:21:29,297 [INFO] 201 Downloaded : v02.log.observations.swob-ml.20160328.CWRM 20160328130240.645 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWRM/2016-03-28-1300-CWRM-AUTO-swob.xml 201 boule.example.com anonymous 1128.560235 parts=1,6451,1,0,0 sum=d,f17299b2afd78ae8d894fe85d3236488 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=/var/www/html/observations/swob-ml/20160328/CWRM/2016-03-28-1300-CWRM-AUTO-swob.xml message=Downloaded 
  2016-03-28 09:21:29,389 [INFO] Received notice  20160328130240.646 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWSK/2016-03-28-1300-CWSK-AUTO-swob.xml
  2016-03-28 09:21:29,662 [INFO] 201 Downloaded : v02.log.observations.swob-ml.20160328.CWSK 20160328130240.646 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWSK/2016-03-28-1300-CWSK-AUTO-swob.xml 201 boule.example.com anonymous 1128.924688 parts=1,7041,1,0,0 sum=d,8cdc3420109c25910577af888ae6b617 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=/var/www/html/observations/swob-ml/20160328/CWSK/2016-03-28-1300-CWSK-AUTO-swob.xml message=Downloaded 
  2016-03-28 09:21:29,765 [INFO] Received notice  20160328130240.647 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWWA/2016-03-28-1300-CWWA-AUTO-swob.xml
  2016-03-28 09:21:30,045 [INFO] 201 Downloaded : v02.log.observations.swob-ml.20160328.CWWA 20160328130240.647 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWWA/2016-03-28-1300-CWWA-AUTO-swob.xml 201 boule.example.com anonymous 1129.306662 parts=1,7027,1,0,0 sum=d,aabb00e0403ebc9caa57022285ff0e18 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=/var/www/html/observations/swob-ml/20160328/CWWA/2016-03-28-1300-CWWA-AUTO-swob.xml message=Downloaded 
  2016-03-28 09:21:30,138 [INFO] Received notice  20160328130240.649 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CXVG/2016-03-28-1300-CXVG-AUTO-swob.xml
  2016-03-28 09:21:30,431 [INFO] 201 Downloaded : v02.log.observations.swob-ml.20160328.CXVG 20160328130240.649 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CXVG/2016-03-28-1300-CXVG-AUTO-swob.xml 201 boule.example.com anonymous 1129.690082 parts=1,7046,1,0,0 sum=d,186fa9627e844a089c79764feda781a7 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=/var/www/html/observations/swob-ml/20160328/CXVG/2016-03-28-1300-CXVG-AUTO-swob.xml message=Downloaded 
  2016-03-28 09:21:30,524 [INFO] Received notice  20160328130240.964 http://dd2.weather.gc.ca/ bulletins/alphanumeric/20160328/CA/CWAO/13/CACN00_CWAO_281300__TBO_05037
  ^C2016-03-28 09:21:30,692 [INFO] signal stop
  2016-03-28 09:21:30,693 [INFO] sr_subscribe stop
  sarra@boule:~/.config/sarra/subscribe$ 
  
So the connection to upstream is functional, now lets make sure the subscription does not start automatically::

  sarra@boule:~/.config/sarra/subscribe$ mv dd.conf dd.off

and turn to a sarra set up.
  


Sarra from Another Pump
~~~~~~~~~~~~~~~~~~~~~~~

Sarra is used to have a downstream pump re-advertise products from an upstream one. Sarra needs all the configuration of a subscription,
but also needs the configuration to post to the downstream broker.  The feeder account on the broker is used for this sort 
of work, and is a semi-administrative user, able to publish data to any exchange.  Assume Apache is set up (not covered here) with a 
document root of /var/www/html.  The linux account we have created to run all the sr processes is '*sarra*', so we make sure 
the document root is writable to those processes::

  sarra@boule:~$ cd ~/.config/sarra/sarra
  sarra@boule:~/.config/sarra/sarra$ sudo chown sarra.sarra /var/www/html

Then we create a configuration::

  sarra@boule:~$ cat >>dd.off <<EOT

  broker amqp://anonymous@dd.weather.gc.ca/
  exchange xpublic

  gateway_for DD

  mirror False  # usually True, except for this server!

  # Numerical Weather Model files will overwhelm a small server.
  reject .*/\.tar
  reject .*/model_giops/.*
  reject .*/grib2/.*

  directory /var/www/html
  accept .*

  url http://boule.example.com/
  document_root /var/www/html
  post_broker amqps://feeder@boule.example.com/
  
  EOT

Compared to the subscription example provided in the previous example, We have added:

exchange xpublic

  sarra is often used for specialized transfers, so the xpublic exchange is not assumed, as it is with subscribe.

gateway_for DD

   sarra implements routing by cluster, so if data is not destined for this cluster, it will skip (not download) a product.
   Inspection of the sr_subscribe output above reveals that products are destined for the DD cluster, so lets pretend to route
   for that, so that downloading happens.   

url and document_root

   these are needed to build the local posts that will be posted to the ...

post_broker
  
   where we will re-announce the files we have downloaded.

mirror False

  This is usually unnecessary, when copying between pumps, it is normal to just make direct copies.  
  However, the dd.weather.gc.ca pump predates the day/source prefix standard, so it is necessary for
  ease of cleanup.


so then try it out::

  sarra@boule:~/.config/sarra/sarra$ sr_sarra dd.off foreground
  2016-03-28 10:38:16,999 [INFO] sr_sarra start
  2016-03-28 10:38:16,999 [INFO] sr_sarra run
  2016-03-28 10:38:17,000 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2016-03-28 10:38:17,604 [INFO] Binding queue q_anonymous.sr_sarra.dd.off with key v02.post.# from exchange xpublic on broker amqp://anonymous@dd.weather.gc.ca/
  2016-03-28 10:38:19,172 [INFO] Received v02.post.bulletins.alphanumeric.20160328.UA.CWAO.14 '20160328143820.166 http://dd2.weather.gc.ca/ bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422' parts=1,124,1,0,0 sum=d,cfbcb85aac0460038babc0c5a8ec0513 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM 
  2016-03-28 10:38:19,172 [INFO] downloading/copying into /var/www/html/bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422 
  2016-03-28 10:38:19,515 [INFO] 201 Downloaded : v02.log.bulletins.alphanumeric.20160328.UA.CWAO.14 20160328143820.166 http://dd2.weather.gc.ca/ bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422 201 boule.bsqt.example.com anonymous -0.736602 parts=1,124,1,0,0 sum=d,cfbcb85aac0460038babc0c5a8ec0513 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM message=Downloaded 
  2016-03-28 10:38:19,517 [INFO] Published: '20160328143820.166 http://boule.bsqt.example.com/ bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422' parts=1,124,1,0,0 sum=d,cfbcb85aac0460038babc0c5a8ec0513 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM 
  2016-03-28 10:38:19,602 [INFO] 201 Published : v02.log.bulletins.alphanumeric.20160328.UA.CWAO.14.UANT01_CWAO_281438___22422 20160328143820.166 http://boule.bsqt.example.com/ bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422 201 boule.bsqt.example.com anonymous -0.648599 parts=1,124,1,0,0 sum=d,cfbcb85aac0460038babc0c5a8ec0513 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM message=Published 
  ^C2016-03-28 10:38:20,328 [INFO] signal stop
  2016-03-28 10:38:20,328 [INFO] sr_sarra stop
  sarra@boule:~/.config/sarra/sarra$ 

The file has the suffix 'off' so that it will not be invoked by default when the entire sarra configuration is started.
One can still start the file when it is in the off setting, by specifying the path (in this case, it is in the current directory)
so initially have 'off' files while debugging the settings.
As the configuration is working properly, rename it to so that it will be used on startup::

  sarra@boule:~/.config/sarra/sarra$ mv dd.off dd.conf
  sarra@boule:~/.config/sarra/sarra$ 


Logs
~~~~

Now that data is flowing, we need to take a look at the flow of log messages, which essentially are used by each pump to tell
upstream that data has been downloaded. add the following line to ~sarra/.config/sarrra/default.conf::

  log_daemons

This will cause the log routing daemons to be started. that will mean that messages that are logged by feeder or other
subscriber processes will all end up in the xlog exchange.  To monitor overall system activity, start up an sr_log that
is bound to the xlog exchange::

  blacklab% more boulelog.conf

  broker amqps://feeder@boule.example.com/
  exchange xlog
  accept .*

  blacklab%

  blacklab% sr_log boulelog.conf foreground
  2016-03-28 16:29:53,721 [INFO] sr_log start
  2016-03-28 16:29:53,721 [INFO] sr_log run
  2016-03-28 16:29:53,722 [INFO] AMQP  broker(boule.example.com) user(feeder) vhost(/)
  2016-03-28 16:29:54,484 [INFO] Binding queue q_feeder.sr_log.boulelog.06413933.71328785 with key v02.log.# from exchange xlog on broker amqps://feeder@boule.example.com/
  2016-03-28 16:29:55,732 [INFO] Received notice  20160328202955.139 http://boule.example.com/ radar/CAPPI/GIF/XLA/201603282030_XLA_CAPPI_1.5_RAIN.gif 201 blacklab anonymous -0.040751
  2016-03-28 16:29:56,393 [INFO] Received notice  20160328202956.212 http://boule.example.com/ radar/CAPPI/GIF/XMB/201603282030_XMB_CAPPI_1.5_RAIN.gif 201 blacklab anonymous -0.159043
  2016-03-28 16:29:56,479 [INFO] Received notice  20160328202956.179 http://boule.example.com/ radar/CAPPI/GIF/XLA/201603282030_XLA_CAPPI_1.0_SNOW.gif 201 blacklab anonymous 0.143819
  2016-03-28 16:29:56,561 [INFO] Received notice  20160328202956.528 http://boule.example.com/ radar/CAPPI/GIF/XMB/201603282030_XMB_CAPPI_1.0_SNOW.gif 201 blacklab anonymous -0.119164
  2016-03-28 16:29:57,557 [INFO] Received notice  20160328202957.405 http://boule.example.com/ bulletins/alphanumeric/20160328/SN/CWVR/20/SNVD17_CWVR_282000___01910 201 blacklab anonymous -0.161522
  2016-03-28 16:29:57,642 [INFO] Received notice  20160328202957.406 http://boule.example.com/ bulletins/alphanumeric/20160328/SN/CWVR/20/SNVD17_CWVR_282000___01911 201 blacklab anonymous -0.089808
  2016-03-28 16:29:57,729 [INFO] Received notice  20160328202957.408 http://boule.example.com/ bulletins/alphanumeric/20160328/SN/CWVR/20/SNVD17_CWVR_282000___01912 201 blacklab anonymous -0.043441
  2016-03-28 16:29:58,723 [INFO] Received notice  20160328202958.471 http://boule.example.com/ radar/CAPPI/GIF/WKR/201603282030_WKR_CAPPI_1.5_RAIN.gif 201 blacklab anonymous -0.131236
  2016-03-28 16:29:59,400 [INFO] signal stop
  2016-03-28 16:29:59,400 [INFO] sr_log stop
  blacklab% 

From this listing, we can see that a subscriber on blacklab is actively downloading from the new pump on boule.


Sarra From a Source
~~~~~~~~~~~~~~~~~~~

When reading posts directly from a source, one needs to turn on validation.
FIXME: example of how user posts are handled.

  - set source_from_exchange
  - set mirror False to get date/source tree prepended
  - validate that the checksum works...

anything else?


Cleanup 
~~~~~~~

These are examples, the implementation of cleanup is not covered by sarracenia.  Given a reasonably small tree as 
given above, it can be practical to scan the tree and prune the old files from it.
a cron job like so::

  root@boule:/etc/cron.d# more sarra_clean
  # remove files one hour after they show up.
  # for weather production, 37 minutes passed the hour is a good time.
  # remove directories the day after the last time they were touched.
  37 4 * * *  root find /var/www/html -mindepth 1 -maxdepth 1 -type d -mtime +0  | xargs rm -rf

This might see a bit aggressive, but this file was on a very small virtual server that was only intended for real-time
data transfer so keeping data around for extended periods would have filled the disk and stopped all transfers.
In large scale transfers, there is always a trade off between the practicality of keeping the data around forever, and
the need for performance, which requires us to prune directory trees regularly.  File system performance is optimal with
reasonably sized trees, and when the trees get to large, the 'find' process to traverse it, can become too onerous.

One can more easily maintain smaller directory trees by having them roll over regularly.  If you have enough disk
space to last one or more days, then a single logical cron job that would operate on the daily trees without
incurring the penalty of a find, is a good approach.

Replace the contents above with::

  34 4 * * * root find /var/www/html -mindepth 1 -maxdepth 1  -type d -regex '/var/www/html/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]' -mtime +1 | xargs rm -rf 

where the +1 can be replaced by the number of days to retain. ( would have preferred to use [0-9]{8}, but it would appear that find's regex syntax does not include repetitions. )

Note that the logs will clean up themselves, by default after 5 days they will be discarded.  Can shorten to a single day by
adding *logrotate 1* to default.conf.

Startup
~~~~~~~

FIXME: /etc/init.d/ integration missing.


Sr_Poll
~~~~~~~

FIXME: feed the sarra from source configured with an sr_poll. set up.


Sr_winnow
~~~~~~~~~

FIXME: sample sr_winnow configuration explained, with some shovels also.


Sr_sender
~~~~~~~~~

Where firewalls prevent use of sarra to pull from a pump like a subscriber would, one can reverse the feed by having the
upstream pump explicitly feed the downstream one.

FIXME:  elaborate sample sr_sender configuration.



Manually Adding Users
~~~~~~~~~~~~~~~~~~~~~

To avoid the use of sr_admin, or work around issues, one can adjust user settings manually::

  cd /usr/local/bin
  wget -q https://boule.example.com:15671/cli/rabbitmqadmin
  chmod 755 rabbitmqadmin

  rabbitmqctl add_user Alice <password>
  rabbitmqctl set_permissions -p / Alice   "^q_Alice.*$" "^q_Alice.*$|^xs_Alice$" "^q_Alice.*$|^xl_Alice$|^xpublic$"

  rabbitmqadmin -u root -p ***** declare exchange name=xs_Alice type=topic auto_delete=false durable=true
  rabbitmqadmin -u root -p ***** declare exchange name=xl_Alice type=topic auto_delete=false durable=true

or, parametrized::

  u=Alice
  rabbitmqctl add_user ${u} <password>
  rabbitmqctl set_permissions -p / ${u} "^q_${u}.$" "^q_${u}.*$|^xs_${u}$" "^q_${u}.*$|^xl_${u}$|^xpublic$"

  rabbitmqadmin -u root -p ***** declare exchange name=xs_${u} type=topic auto_delete=false durable=true
  rabbitmqadmin -u root -p ***** declare exchange name=xl_${u} type=topic auto_delete=false durable=true


Then you need to do the same work for sftp and or apache servers as required, as 
authentication needed by the payload transport protocol (SFTP, FTP, or HTTP(S)) 
is managed separately.


Configurations
--------------

There are many different arrangements in which sarracenia can be used. The guide
will work through a few examples:

Dataless 
  where one runs just sarracenia on top of a broker with no local transfer engines.
  This is used, for example to run sr_winnow on a site to provide redundant data sources.

Standalone 
  the most obvious one, run the entire stack on a single server, openssh and a web server
  as well the broker and sarra itself.  Makes a complete data pump, but without any redundancy.

Switching/Routing
  Where, in order to achieve high performance, a cluster of standalone nodes are placed behind
  a load balancer.  The load balancer algorithm is just round-robin, with no attempt to associate
  a given source with a given node.  This has the effect of pumping different parts of large files 
  through different nodes.  So one will see parts of files announced by such pump, to be
  re-assembled by subscribers.

Data Dissemination
  Where in order to serve a large number of clients, multiple identical servers, each with a complete
  mirror of data 

FIXME: 
  ok, opened big mouth, now need to work through the examples.


Dataless or S=0
~~~~~~~~~~~~~~~

A configuration which includes only the AMQP broker.  This configuration can be used when users
have access to disk space on both ends and only need a mediator.  This is the configuration
of sftp.science.gc.ca, where the HPC disk space provides the storage so that the pump does
not need any, or pumps deployed to provide redundant HA to remote data centres.

.. note:: 

  FIXME: sample configuration of shovels, and sr_winnow (with output to xpublic) to allow 
  subscribers in the SPC to obtain data from either edm or dor.

Note that while a configuration can be dataless, it can still make use of rabbitmq
clustering for high availability requirements (see rabbitmq clustering below.)


Dataless With Sr_winnow
~~~~~~~~~~~~~~~~~~~~~~~

Another example of a dataless pump would be to provide product selection from two upstream
sources using sr_winnow.  The sr_winnow is fed by shovels from upstream sources, and 
the local clients just connect to this local pump.  sr_winnow takes 
care of only presenting the products from the first server to make 
them available.   one would configure sr_winnow to output to the xpublic exchange
on the pump.

subscriber just point at the output of sr_winnow on the local pump.


Dataless With Sr_poll
~~~~~~~~~~~~~~~~~~~~~

The sr_poll program can verify if products on a remote server are ready or modified.
For each of the product, it emits an announcement on the local pump. One could use
sr_subscribe anywhere, listen to announcements and get the products (privided the
having the credentials to access it)


Standalone
~~~~~~~~~~

In a standalone configuration, there is only one node in the configuration.  It runs all components
and shares none with any other nodes.  That means the Broker and data services such as sftp and
apache are on the one node.

One appropriate usage would be a small non-24x7 data acquisition setup, to take responsibility of data
queueing and transmission away from the instrument.  It is restarted when the opportunity arises.
It is just a matter of installing and configuring all a data flow engine, a broker, and the package
itself on a single server.



Switching/Routing
~~~~~~~~~~~~~~~~~

In switching/routing configuration, there is a pair of machines running a single broker for a pool
of transfer engines.  So each transfer engine´s view of the file space is local, but the queues are 
global to the pump.


Note: On such clusters, all nodes that run a component with the
same config file create by default an identical **queue_name**. Targetting the
same broker, it forces the queue to be shared. If it should be avoided,
the user can just overwrite the default **queue_name** inserting **${HOSTNAME}**.
Each node will have its own queue, only shared by the node instances.
ex.:  queue_name q_${BROKER_USER}.${PROGRAM}.${CONFIG}.${HOSTNAME} )


Advanced Installations
----------------------

On some configurations (we usually call them *bunny*), we use a clusterd rabbitmq, like so::

        /var/lib/rabbitmq/.erlang.cookie  same on all nodes

        on each node restart  /etc/init.d/rabbitmq-server stop/start

        on one of the node

        rabbitmqctl stop_app
        rabbitmqctl join_cluster rabbit@"other node"
        rabbitmqctl start_app
        rabbitmqctl cluster_status


        # having high availability queue...
        # here all queues that starts with "cmc." will be highly available on all the cluster nodes

        rabbitmqctl set_policy ha-all "^cmc\." '{"ha-mode":"all"}'


Clustered Broker Keepalived Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this example, bunny-op is a vip that migrates between bunny1-op and bunny2-op.
Keepalived moves the vip between the two::

  #=============================================
  # vip bunny-op 192.101.12.59 port 5672
  #=============================================
  
  vrrp_script chk_rabbitmq {
          script "killall -0 rabbitmq-server"
          interval 2
  }
  
  vrrp_instance bunny-op {
          state BACKUP
          interface eth0
          virtual_router_id 247
          priority 150
          track_interface {
                  eth0
          }
          advert_int 1
          preempt_delay 5
          authentication {
                  auth_type PASS
                  auth_pass bunop
          }
          virtual_ipaddress {
  # bunny-op
                  192.101.12.59 dev eth0
          }
          track_script {
                  chk_rabbitmq
          }
  }
  
  




LDAP Integration 
~~~~~~~~~~~~~~~~

To enable LDAP authentication for rabbitmq::

         rabbitmq-plugins enable rabbitmq_auth_backend_ldap

         # replace username by ldap username
         # clear password (will be verified through the ldap one)
         rabbitmqctl add_user username aaa
         rabbitmqctl clear_password username
         rabbitmqctl set_permissions -p / username "^xpublic|^amq.gen.*$|^cmc.*$" "^amq.gen.*$|^cmc.*$" "^xpublic|^amq.gen.*$|^cmc.*$"

And you need to set up LDAP parameters in the broker configuration file:
(this sample ldap-dev test config worked when we tested it...)::


  cat /etc/rabbitmq/rabbitmq.config
  [ {rabbit, [{auth_backends, [ {rabbit_auth_backend_ldap,rabbit_auth_backend_internal}, rabbit_auth_backend_internal]}]},
    {rabbitmq_auth_backend_ldap,
     [ {servers,               ["ldap-dev.cmc.ec.gc.ca"]},
       {user_dn_pattern,       "uid=${username},ou=People,ou=depot,dc=ec,dc=gc,dc=ca"},
       {use_ssl,               false},
       {port,                  389},
       {log,                   true},
       {network,               true},
      {vhost_access_query,    {in_group,
                               "ou=${vhost}-users,ou=vhosts,dc=ec,dc=gc,dc=ca"}},
      {resource_access_query,
       {for, [{permission, configure, {in_group, "cn=admin,dc=ec,dc=gc,dc=ca"}},
              {permission, write,
               {for, [{resource, queue,    {in_group, "cn=admin,dc=ec,dc=gc,dc=ca"}},
                      {resource, exchange, {constant, true}}]}},
              {permission, read,
               {for, [{resource, exchange, {in_group, "cn=admin,dc=ec,dc=gc,dc=ca"}},
                      {resource, queue,    {constant, true}}]}}
             ]
       }},
    {tag_queries,           [{administrator, {constant, false}},
                             {management,    {constant, true}}]}
   ]
  }
  ].



Requires RABBITMQ > 3.3.x
~~~~~~~~~~~~~~~~~~~~~~~~~

Was searching on how to use LDAP strictly for password authentication
The answer I got from the Rabbitmq gurus ::
  
  On 07/08/14 20:51, michel.grenier@ec.gc.ca wrote:
  > I am trying to find a way to use our ldap server  only for 
  > authentification...
  > The user's  permissions, vhost ... etc  would already be set directly 
  > on the server
  > with rabbitmqctl...   The only thing ldap would be used for would be
  > logging.
  > Is that possible... ?   I am asking because our ldap schema is quite
  > different from
  > what rabbitmq-server requieres.
  
  Yes (as long as you're using at least 3.3.x).
  
  You need something like:
  
  {rabbit,[{auth_backends,
             [{rabbit_auth_backend_ldap, rabbit_auth_backend_internal}]}]}
  
  See http://www.rabbitmq.com/ldap.html and in particular:
  
  "The list can contain names of modules (in which case the same module is used for both authentication and authorisation), *or 2-tuples like {ModN, ModZ} in which case ModN is used for authentication and ModZ is used for authorisation*."
  
  Here ModN is rabbit_auth_backend_ldap and ModZ is rabbit_auth_backend_internal.
  
  Cheers, Simon
  


Security Considerations
-----------------------

This section is meant to provide insight to those who need to perform a security review
of the application prior to implementation.  

Authentication used by transport engines is independent of that used for the brokers.  A security 
assessment of rabbitmq brokers and the various transfer engines in use is needed to evaluate 
the overall security of a given deployment.  All credentials used by the application are stored 
in the ~/.config/sarra/credentials.conf file, and that file is forced to 600 permissions.  

The most secure method of transport is the use of SFTP with keys rather than passwords.  Secure
storage of sftp keys is covered in documentation of various SSH or SFTP clients. The credentials
file just points to those key files.

For sarracenia itself, password authentication is used to communicate with the AMQP broker,
so implementation of encrypted socket transport (SSL/TLS) on all broker traffic is strongly 
recommended.  

Sarracenia users are actually users defined on rabbitmq brokers. 
Each user Alice, on a broker to which she has access:

 - has an exchange xs_Alice, where she writes her postings, and reads her logs from.
 - has an exchange xl_Alice, where she reads her log messages.
 - can configure (read from and acknowledge) queues named qs_Alice\_.* to bind to exchanges
 - Alice can create and destroy her own queues, but no-one else's.
 - Alice can only write to her exchange (xs_Alice),
 - Exchanges are managed by the administrator, and not any user.
 - Alice can only post data that she is publishing (it will refer back to her)

Alice cannot create any exchanges or other queues not shown above.

Rabbitmq provides the granularity of security to restrict the names of
objects, but not their types.  Thus, given the ability to create a queue named q_Alice,
a malicious Alice could create an exchange named q_Alice_xspecial, and then configure
queues to bind to it, and establish a separate usage of the broker unrelated to sarracenia.

To prevent such mis-use, sr_audit is a component that is invoked regularly looking
for mis-use, and cleaning it up.


Input Validation
~~~~~~~~~~~~~~~~

Users such as Alice post their messages to their own exchange (xs_Alice).  Processes which read from 
user exchanges have a responsibility for validation.   The process that reads xs_Alice (likely an sr_sarra) 
will overwrite any *source* or *cluster* heading written into the message with the correct values for
the current cluster, and the user which posted the message.  

The checksum algorithm used must also be validated.  The algorithm must be known.  Similarly, if
there is a malformed header of some kind, it should be rejected immediately.  Only well-formed messages
should be forwarded for further processing.

In the case of sr_sarra, the checksum is re-calculated when downloading the data, it
ensures it matches the message.  If they do not match, an error log message is published.
If the *recompute_checksum* option is True, the newly calculated checksum is put into the message.
Depending on the level of confidence between a pair of pumps, the level of validation may be
relaxed to improve performance.  

Another difference with inter-pump connections, is that a pump necessarily acts as an agent for all the
users on the remote pumps and any other pumps the pump is forwarding for.  In that case, the validation
constraints are a little different:

- source doesn´t matter. (feeders can represent other users, so do not overwrite.) 
- ensure cluster is not local cluster (as that indicates either a loop or misuse.)

If the message fails the non-local cluster test, it should be rejected, and logged (published ... hmm...)

.. NOTE::
 FIXME:
   - if the source is not good, and the cluster is not good... cannot log back. so just log locally?


Privileged System Access
~~~~~~~~~~~~~~~~~~~~~~~~

Ordinary (sources, and subscribers) users operate sarra within their own permissions on the system, 
like an scp command.  The pump administrator account also runs under a normal linux user account and,
given requires privileges only on the AMQP broker, but nothing on the underlying operating system.   
It is convenient to grant the pump administrator sudo privileges for the rabbitmqctl command.

The may be a single task which must operate with privileges: cleaning up the database, which is an easily
auditable script that must be run on a regular basis.  If all acquisition is done via sarra, then all of
the files will belong to the pump administrator, and privileged access is not required for this either.


Content Scanning
~~~~~~~~~~~~~~~~

In cases where security scanning of file being transferred is deemed necessary,
one configures sarra with an *on_part* plugin.  The sample *clamav_scan.py* plugin is included
with the package. It depends on some additional packages::

  sudo apt-get install python3-pyclamd

By default, all parts of a file are scanned.  One can set an option in the configuration for the component
invoking the plugin like so::

  clamav_maxblock 3
  on_part clamav_scan.py

to limit scanning to only the first three parts of a file.  When a file is scanned, the log of the component
with scanning configured will have an entry like so::

  2016-03-30 00:41:55,497 [INFO] clamav_scan took 0.000952244 seconds, no viruses in /home/peter/test/boule/20160330/metpx/bulletins/alphanumeric/20160330/CA/CWAO/04/CACN00_CWAO_300400__PBD_05042

When plugged into Sarra, as the plugin returns True, the re-advertisement proceeds.  If a virus were found, an error
message is printed and the plugin returns False so that the part's advertisement would not be posted (so subscribers and 
downstream pumps will not pick it up.)

**FIXME: set minimum/maximum part size?**

Hooks from Sundew
-----------------

This information is very likely irrelevant to almost all users.  Sundew is another module of MetPX which is essentially being
replaced by Sarracenia.  This information is only useful to those with an installed based of Sundew wishing to bridge
to sarracenia.  The early work on Sarracenia used only the subscribe client as a downloader, and the existing WMO switch module 
from MetPX as the data source.  There was no concept of multiple users, as the switch operates as a single dissemination 
and routing tool.  This section describes the kinds of *glue* used to feed Sarracenia subscribers from a Sundew source. 
It assumes a deep understanding of MetPX-Sundew. Currently, the dd_notify.py script creates messages for the 
protocol exp., v00. and v02 (latest sarracenia protocol version)


Notifications on DD 
~~~~~~~~~~~~~~~~~~~

As a higher performance replacement for Atom/RSS feeds which tell subscribers when new data is available, we put a broker 
on our data dissemination server (dd.weather.gc.ca.) Clients can subscribe to it.  To create the notifications, we have 
one Sundew Sender (named wxo-b1-oper-dd.conf) with a send script::

  type script
  send_script sftp_amqp.py
  
  # connection info
  protocol    ftp
  host        wxo-b1.cmc.ec.gc.ca
  user        wxofeed
  password    **********
  ftp_mode    active
  
  noduplicates false
  
  # no filename validation (pds format)
  validation  False
  
  # delivery method
  lock  umask
  chmod 775
  batch 100

We see all the configuration information for a single-file sender, but the send_script overrides the
normal sender with something that builds AMQP messages as well.  This Sundew sender config 
invokes *sftp_amqp.py* as a script to do the actual send, but also to place the payload of an
AMQP message in the /apps/px/txq/dd-notify-wxo-b1/, queuing it up for a Sundew AMQP sender.
That sender´s config is::

   type amqp
   
   validation False
   noduplicates False
   
   protocol amqp
   host wxo-b1.cmc.ec.gc.ca
   user feeder
   password ********
   
   exchange_name cmc
   exchange_key  v02.post.${0}
   exchange_type topic
   
   reject ^ensemble.naefs.grib2.raw.*
   
   accept ^(.*)\+\+.*
   
The key for the topic includes a substitution.  The *${0}* contains the directory tree where the 
file has been placed on dd (with the / replaced by .)  For example, here is a log file entry::

  2013-06-06 14:47:11,368 [INFO] (86 Bytes) Message radar.24_HR_ACCUM.GIF.XSS++201306061440_XSS_24_HR_ACCUM_MM.gif:URP:XSS:RADAR:GIF::20130606144709  delivered (lat=1.368449,speed=168950.887119)

- So the key is: v02.post.radar.24_HR_ACCUM.GIF.XSS
- the file is placed under: http://dd1.weather.gc.ca/radar/24_HR_ACCUM/GIF/XSS
- the complete URL for the product is: http://dd1.weather.gc.ca/radar/24_HR_ACCUM/GIF/XSS/201306061440_XSS_24_HR_ACCUM_MM.gif

