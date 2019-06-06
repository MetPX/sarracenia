
=====================================
 MetPX-Sarracenia for Administrators
=====================================

.. note::
   **FIXME**: Missing sections are highlighted by **FIXME**. What is here is accurate.

.. Contents::


Revision Record
---------------

:version: @Version@
:date: @Date@


Pre-Requisites
--------------

Ideally, one should be familiar with user-level access to existing pumps
as either a `subscriber <subscriber.rst>`_ or a `source <source.rst>`_  before proceeding to administration.
This manual aims to be prescriptive, rather than explanatory.  For the reasons why things are
built as they are see `Concepts.rst <Concepts.rst>`_


Minimum Requirements
~~~~~~~~~~~~~~~~~~~~

The AMQP broker is extremely light on today's servers. The examples in 
this manual were implemented on a commercial virtual private server (VPS) 
with 256 MB of RAM, and 700MB of swap taken from a 20 GByte disk. Such 
a tiny configuration is able to keep up with almost a full feed 
from dd.weather.gc.ca (which includes, all public facing weather and 
environmental data from Environment and Climate Change Canada). The 
large numerical prediction files (GRIB and multiple GRIB's in tar files) 
were excluded to reduce bandwidth usage, but in terms of performance 
in message passing, it kept up with one client quite well.

Each Sarra process is around 80 mb of virtual memory, but only about 3 mb 
is resident, and you need to run enough of them to keep up (on the small VPS, 
ran 10 of them.) so about 30 mbytes of RAM actually used. The broker's RAM 
usage is what determines the number of clients which can be served. Slower 
clients require more RAM for their queues. So running brokerage tasks and
aggressive cleaning can reduce the overall memory footprint. The broker was
configured to use 128 MB of RAM in the examples in this manual. The rest 
of the RAM was used by the apache processes for the web transport engine.

While the above was adequate for proof of concept, it would be impractical to
be clearing out data from disk after only an hour, and the number of clients
supportable is likely quite limited. 1GB of RAM for all the sarra related
activities should be ample for many useful cases.



Operations
----------

To operate a pump, there needs to be a user designated as the pump administrator.
The administrator is different from the others mostly in the permission granted
to create arbitrary exchanges, and the ability to run processes that address the common
exchanges (xpublic, xreport, etc...) All other users are limited to being able to
access only their own resources (exchange and queues).

The administrative user name is an installation choice, and exactly as for any other
user, the configuration files are placed under ~/.config/sarra/, with the
defaults under admin.conf, and the configurations for components under
directories named after each component. In the component directories,
configuration files have the .conf suffix.

The administrative processes perform validation of postings from sources. Once
they are validated, forward the postings to the public exchanges for subscribers to access.
The processes that are typically run on a broker:

- sr_audit  - purge useless queues, create exchanges and users, set user permissions according to their roles.
- sr_poll   - for sources without advertisements, revert to explicit polling for initial injection.
- sr_sarra  - various configurations to pull data from other pumps to make it available from the local pump.
- sr_sender - send data to clients or other pumps that cannot pull data (usually because of firewalls.)
- sr_winnow - when there are multiple redundant sources of data, select the first one to arrive, and feed sr_sarra.
- sr_shovel - copy advertisements from pump to another, usually to feed sr_winnow.

As for any other user, there may be any number of configurations
to set up, and all of them may need to run at once. To do so easily, one can invoke::

  sr start

to start all the files with named configurations of each component (sarra, subscribe, winnow, log, etc...)
There are two users/roles that need to be set to use a pump. They are the admin and feeder options.
They are set in ~/.config/sarra/admin.conf like so::

  feeder amqp://pumpUser@localhost/
  admin  amqps://adminUser@boule.example.com/

Then the report and audit components are started as well. It is standard practice to use a different
AMQP user for administrative tasks, such as exchange or user creation, which are performed by the admin
user, from data flow tasks, such as pulling and posting data, performed by the feeder user.
Normally one would place credentials in ~/.config/sarra/credentials.conf
for each account, and the various configuration files would use the appropriate account.




Housekeeping - sr_audit
~~~~~~~~~~~~~~~~~~~~~~~~

When a client connects to a broker, it creates a queue which is then bound to an exchange. The user
can choose to have the client self-destruct when disconnected (*auto-delete*), or it can make
it *durable* which means it should remain, waiting for the client to connect again, even across
reboots. Clients often want to pick up where they left off, so the queues need to stay around.

The rabbitmq broker will never destroy a queue that is not in auto-delete (or durable).  This means
they will build up over time. We have a script that looks for unused queues, and cleans them out.
Currently, the default is set that any unused queue having more than 25000 messages will be deleted.
One can change this limit by having option *max_queue_size 50000* in default.conf.


Excess Queueing/Performance
~~~~~~~~~~~~~~~~~~~~~~~~~~~

When rabbitmq has hundreds of thousands of messages queued, broker performance can suffer. Such
accumulations can occur when the destination of a sender is down for a prolonged period, or a 
subscriber is unavailable for some reason. In many cases, one can simply shutdown the sender,
and delete the queue on the broker. While that solves the broker performance issue, the user
will not receive the notifications.

To avoid data loss, please consult the 
`sr_sender(1) manual page *DESTINATION UNAVAILABLE* <sr_sender.1.rst#destination-unavailable>`_
section for details of save and restore options. Briefly, when a sender is placed 
in *save* mode, rather than attempting to send each file, the messages written 
to a disk file. When the remote user is back, one invokes *restore* mode, and 
the disk file is read back, and the files are sent. In versions >= 2.18, there 
is logic to automatically save failed transfers for later retry, offloading the
queue from the broker to the instances' cache storage, so no intervention is 
needed.

In the case of components other than a sender, please consult the QUEUE Save/Restore section
of the sr_shovel(8) manual page. There is a similar mechanism used to write messages queued
to disk, to avoid them overloading the broker. When the consumer is back in service, the
*restore_to_queue* option can be used to recover missing messages.

If one gets to the point where traffic through a queue is excessive (several hundred messages
per second to a single queue), especially if there are many instances sharing the same queue
(if more than 40 instances to service a single queue) then one can run into a point where
adding instances gives no improvement in the overall throughput. For example, rabbitmq uses
only a single cpu to serve a queue. In such cases, creating multiple configurations,
(each with their own queue) dividing the traffic among them will allow further improvements 
in throughput.

sr_winnow is used to suppress duplicates.  
**Note that the duplicate suppresion cache is local to each instance**. When N instances share a queue, the
first time a posting is received, it could be picked by one instance, and if a duplicate one is received
it would likely be picked up by another instance. **For effective duplicate suppression with instances**,
one must **deploy two layers of subscribers**. Use a **first layer of subscribers (sr_shovels)** with duplicate
suppression turned off and output with *post_exchange_split*, which route posts by checksum to
a **second layer of subscribers (sr_winnow) whose duplicate suppression caches are active.**




Routing
-------

The inter-connection of multiple pumps is done, on the data side, by daisy-chaining
sr_sarra and/or sr_sender configurations from one pump to the next. 

The *to_clusters*, and *source*  headers are used for routing decisions
implemented in the *msg_to_clusters*, and *msg_by_source* plugins respectively
to be user by sender or sarra components to limit data transfers between pumps.

For report routing, the *from_cluster* header is interpreted by the 
*msg_from_cluster* plugin. Report messages are defined in the sr_report(7) man
page. They are emitted by *consumers* at the end, as well as *feeders* as the 
messages traverse pumps. Report messages are posted to the xs\_<user> exchange,
and after validation sent to the xreport exchange by the shovel component 
configurations created by sr_audit.

Messages in xreports destined for other clusters are routed to destinations by
manually configured shovels. See the Reports_ section for more details.


What is Going On?
-----------------

The sr_report command can be invoked to bind to 'xreport' instead of the 
default user exchange to get report information for an entire broker.


Canned sr_report configuration with an *on_message* action can be configured to
gather statisical information.

.. NOTE::
   **FIXME:** first canned sr_report configuration would be speedo...
   speedo: total rate of posts/second, total rate of logs/second.
   question: should posts go to the log as well?
   before operations, we need to figure out how Nagios will monitor it.

   Is any of this needed, or is the rabbit GUI enough on it's own?



Init Integration
~~~~~~~~~~~~~~~~

By default, when sarracenia is installed, it is done as a user tool and not a system-wide resource.
The tools/ sub-directory directory allows for integration with tools for different usage scenarios.

.. NOTE::
   tools/sr.init -- a sample init script suitable for sysv-init or upstart based systems.
   tools/sarra_system.service -- for systemd base systems for a 'daemon' style deployment.
   tools/sarra_user.service -- for systemd as a per user service.


Systemd installation process, by administrator::

   groupadd sarra
   useradd sarra
   cp tools/sarra_system.service /etc/systemd/system/sarra.service  (if a package installs it, it should go in /usr/lib/systemd/system )
   cp tools/sarra_user.service /etc/systemd/user/sarra.service (or /usr/lib/systemd/user, if installed by a package )
   systemctl daemon-reload
   
It is then assumed that one uses the 'sarra' account to store the daemon oriented (or system-wide) sarra configuration.
Users can also run their personal configuration in sessions via::

  systemctl --user enable sarra
  systemctl --user start sarra


On an upstart or sysv-init based system::

   cp tools/sr.init /etc/init.d/sr
   <insert magic here to get that activated.>
  


Rabbitmq Setup
--------------

Sample information on setting up a rabbitmq broker for sarracenia to use. The broker does not have to
be on the same host as anything else, but there has to be one reachable from at least one of the
transport engines.


Installation
~~~~~~~~~~~~

Generally speaking, we want to stay above 3.x version.

https://www.rabbitmq.com/install-debian.html

Briefly::

 apt-get update
 apt-get install erlang-nox
 apt-get install rabbitmq-server

In upto-date distros, you likely can just take the distro version.


WebUI
~~~~~

Sr_audit makes use of a variety of calls to the web management interface.
sr_audit is the component which, as the name implies, audits configurations
for left over queues, or attempts at malicious usage. Without this sort
of auditing, the switch is likely to accumulate messages rapidly, which
slows it down to a greater degree as the amount of messages pending increases
potentially overflowing to disk.

Basically, from a root shell one must::

 rabbitmq-plugins enable rabbitmq_management

which will enable the webUI for the broker. To prevent access to the management
interface for undesirables, use of firewalls, or listening only to localhost
interface for the management ui is suggested.

TLS
~~~

One should encrypt broker traffic. Obtaining certificates is outside the scope
of these instructions, so it is not discussed in detail. For the purposes of
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

This process produces key files readable only by root. To make the files
readable by the broker (which runs under the rabbitmq user's name) one will have
to adjust the permissions to allow the broker to read the files.
probably the simplest way to do this is to copy them elsewhere::

    root@boule:~# cd /etc/letsencrypt/live/boule*
    root@boule:/etc/letsencrypt/archive# mkdir /etc/rabbitmq/boule.example.com
    root@boule:/etc/letsencrypt/archive# cp -r * /etc/rabbitmq/boule.example.com
    root@boule:~# cd /etc/rabbitmq
    root@boule:~# chown -R rabbitmq.rabbitmq boule*

Now that we have proper certificate chain, configure rabbitmq to disable
tcp, and use only the `RabbitMQ TLS Support <https://www.rabbitmq.com/ssl.rst>`_ (see
also `RabbitMQ Management <https://www.rabbitmq.com/management.rst>`_ )::

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
passed between client and broker. An unencrypted listener was configured for localhost,
where encryption on the local machine is useless, and adds cpu load. But management only
has a single encrypted listener configured.

.. NOTE::

  Currently, sr_audit expects the Management interface to be on port 15671 if encrypted,
  15672 otherwise. Sarra has no configuration setting to tell it otherwise. Choosing another
  port will break sr_audit. **FIXME**.


Change Defaults
~~~~~~~~~~~~~~~

In order to perform any configuration changes the broker needs to be running.
One needs to start up the rabbitmq broker. On older ubuntu systems, that would be done by::

  service rabbitmq-server start

On newer systems with systemd, the best method is::

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
by humans, and so should have a proper interactive shell environment. Some administrative
access is needed, so the user is added to the sudo group::

  root@boule:~# useradd -m sarra
  root@boule:~# usermod -a -G sudo sarra
  root@boule:~# mkdir ~sarra/.config
  root@boule:~# mkdir ~sarra/.config/sarra

You would first need entries in the credentials.conf and admin.conf files::

  root@boule:~# echo "amqps://bunnymaster:MaestroDelConejito@boule.example.com/" >~sarra/.config/sarra/credentials.conf
  root@boule:~# echo "admin amqps://bunnymaster@boule.example.com/" >~sarra/.config/sarra/admin.conf
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
   Out of scope of this discussion, but aside from file system permissions,
   it is convenient to provide the sarra user sudo access to rabbitmqctl.
   With that, the entire system can be administered without system administrative access.


Managing Users on a Pump Using Sr_audit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To set up a pump, one needs a broker administrative user (in the examples: sarra)
and a feeder user (in the examples: feeder). Management of other users is done with
the sr_audit program.

First, write the correct credentials for the admin and feeder users in
the credentials file .config/sarra/credentials.conf ::

 amqps://bunnymaster:MaestroDelConejito@boule.example.com/
 amqp://feeder:NoHayPanDuro@localhost/
 amqps://feeder:NoHayPanDuro@boule.example.com/
 amqps://anonymous:anonyomous@boule.example.com/
 amqps://peter:piper@boule.example.com/

Note that the feeder credentials are presented twice, once to allow un-encrypted access via
localhost, and a second time to permit access over TLS, potentially from other hosts (necessary
when a broker is operating in a cluster, with feeder processes running on multiple transport
engine nodes.) Next step is to put roles in .config/sarra/admin.conf ::

 admin  amqps://root@boule.example.com/
 feeder amqp://feeder@localhost/

Specify all known users that you want to implement with their roles
in the file  .config/sarra/admin.conf ::

 declare subscriber anonymous
 declare source peter

Now to configure the pump execute the following::

 *sr_audit --users foreground*

Sample run::

  sarra@boule:~/.config/sarra$ sr_audit foreground --debug --users 
  2016-03-28 00:41:25,380 [INFO] sr_audit start
  2016-03-28 00:41:25,380 [INFO] sr_audit run
  2016-03-28 00:41:25,380 [INFO] sr_audit waking up
  2016-03-28 00:41:25,673 [INFO] adding user feeder
  2016-03-28 00:41:25,787 [INFO] permission user 'feeder' role feeder  configure='.*' write='.*' read='.*'
  2016-03-28 00:41:25,897 [INFO] adding user peter
  2016-03-28 00:41:26,018 [INFO] permission user 'peter' role source  configure='^q_peter.*' write='^q_peter.*|^xs_peter_.*|^xs_peter_.*' read='^q_peter_.*|^xl_peter$|^.*xpublic$'
  2016-03-28 00:41:26,136 [INFO] adding user anonymous
  2016-03-28 00:41:26,247 [INFO] permission user 'anonymous' role source  configure='^q_anonymous.*' write='^q_anonymous.*|^xs_anonymous$' read='^q_anonymous.*|^xpublic$'
  2016-03-28 00:41:26,497 [INFO] adding exchange 'xreport'
  2016-03-28 00:41:26,610 [INFO] adding exchange 'xpublic'
  2016-03-28 00:41:26,730 [INFO] adding exchange 'xs_peter'
  2016-03-28 00:41:26,854 [INFO] adding exchange 'xl_peter'
  2016-03-28 00:41:26,963 [INFO] adding exchange 'xs_anonymous'
  sarra@boule:~/.config/sarra$


The *sr_audit* program:

- uses the *admin* account from .config/sarra/admin.conf to authenticate to broker.
- creates exchanges *xpublic* and *xreport* if they don't exist.
- reads roles from .config/sarra/admin.conf
- obtains a list of users and exchanges on the pump
- for each user in a *declare* option::

      declare the user on the broker if missing.
      set    user permissions corresponding to its role (on creation)
      create user exchanges   corresponding to its role

- users which have no declared role are deleted.
- user exchanges which do not correspond to users' roles are deleted ('xl\_*,xs\_*')
- exchanges which do not start with 'x' (aside from builtin ones) are deleted.

.. Note::
   PS changed this so that with --users it exits after one pass... um.. not great ...
   but otherwise:
   The program runs as a daemon. After the initial pass to create the users,
   It will go into to sleep, and then audit the configuration again.
   To stop it from running in the foreground, stop it with: <ctrl-c>
   (most common linux default interrupt character)
   or find some other way to kill the running process.

   **FIXME:** when invoked with --users, sr_audit, should set a 'once' flag,
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
  xreport	topic
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

The above looks like *sr_audit* did its job.
In short, here are the permissions and exchanges *sr_audit* manages::

  admin user        : the only one creating users...
  admin/feeder users: have all permission over queues and exchanges

  subscribe user    : can write report messages to exchanged beginning with  xs_<brokerUser> 
                      can read post messages from exchange xpublic
                      have all permissions on queue named  q_<brokerUser>*

  source user       : can write post messages to exchanges beginning with xs_<brokerUser> 
                      can read post messages from exchange  xpublic
                      can read  report messages from exchange  xl_<brokerUser> created for him
                      have all permissions on queue named   q_<brokerUser>*


To add Alice using sr_audit, one would add the following to ~/.config/sarra/admin.conf ::

  declare source Alice

then add an appropriate amqp entry in ~/.config/sarra/credentials.conf to set the password,
then run::

  sr_audit --users foreground

To remove users, just remove *declare source Alice* from the admin.conf file, and run::

  sr_audit --users foreground

again.


First Subscribe
~~~~~~~~~~~~~~~

When setting up a pump, normally the purpose is to connect it to some other pump. To set
the parameters setting up a subscription helps us set parameters for sarra later. So first
try a subscription to an upstream pump::

  sarra@boule:~$ ls
  sarra@boule:~$ cd ~/.config/sarra/
  sarra@boule:~/.config/sarra$ mkdir subscribe
  sarra@boule:~/.config/sarra$ cd subscribe
  sarra@boule:~/.config/sarra/subscribe$ sr_subscribe edit dd.conf 
  broker amqps://anonymous@dd.weather.gc.ca/

  mirror True
  directory /var/www/html

  # numerical weather model files will overwhelm a small server.
  reject .*/\.tar
  reject .*/model_giops/.*
  reject .*/grib2/.*

  accept .*

add the password for the upstream pump to credentials.conf ::

  sarra@boule:~/.config/sarra$ echo "amqps://anonymous:anonymous@dd.weather.gc.ca/" >>../credentials.conf

then do a short foreground run, to see if it is working. Hit Ctrl-C to stop it after a few messages::

  sarra@boule:~/.config/sarra$ sr_subscribe foreground dd
  2016-03-28 09:21:27,708 [INFO] sr_subscribe start
  2016-03-28 09:21:27,708 [INFO] sr_subscribe run
  2016-03-28 09:21:27,708 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2016-03-28 09:21:28,375 [INFO] Binding queue q_anonymous.sr_subscribe.dd.78321126.82151209 with key v02.post.# from exchange xpublic on broker amqps://anonymous@dd.weather.gc.ca/
  2016-03-28 09:21:28,933 [INFO] Received notice  20160328130240.645 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWRM/2016-03-28-1300-CWRM-AUTO-swob.xml
  2016-03-28 09:21:29,297 [INFO] 201 Downloaded : v02.report.observations.swob-ml.20160328.CWRM 20160328130240.645 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWRM/2016-03-28-1300-CWRM-AUTO-swob.xml 201 boule.example.com anonymous 1128.560235 parts=1,6451,1,0,0 sum=d,f17299b2afd78ae8d894fe85d3236488 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=/var/www/html/observations/swob-ml/20160328/CWRM/2016-03-28-1300-CWRM-AUTO-swob.xml message=Downloaded
  2016-03-28 09:21:29,389 [INFO] Received notice  20160328130240.646 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWSK/2016-03-28-1300-CWSK-AUTO-swob.xml
  2016-03-28 09:21:29,662 [INFO] 201 Downloaded : v02.report.observations.swob-ml.20160328.CWSK 20160328130240.646 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWSK/2016-03-28-1300-CWSK-AUTO-swob.xml 201 boule.example.com anonymous 1128.924688 parts=1,7041,1,0,0 sum=d,8cdc3420109c25910577af888ae6b617 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=/var/www/html/observations/swob-ml/20160328/CWSK/2016-03-28-1300-CWSK-AUTO-swob.xml message=Downloaded
  2016-03-28 09:21:29,765 [INFO] Received notice  20160328130240.647 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWWA/2016-03-28-1300-CWWA-AUTO-swob.xml
  2016-03-28 09:21:30,045 [INFO] 201 Downloaded : v02.report.observations.swob-ml.20160328.CWWA 20160328130240.647 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CWWA/2016-03-28-1300-CWWA-AUTO-swob.xml 201 boule.example.com anonymous 1129.306662 parts=1,7027,1,0,0 sum=d,aabb00e0403ebc9caa57022285ff0e18 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=/var/www/html/observations/swob-ml/20160328/CWWA/2016-03-28-1300-CWWA-AUTO-swob.xml message=Downloaded
  2016-03-28 09:21:30,138 [INFO] Received notice  20160328130240.649 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CXVG/2016-03-28-1300-CXVG-AUTO-swob.xml
  2016-03-28 09:21:30,431 [INFO] 201 Downloaded : v02.report.observations.swob-ml.20160328.CXVG 20160328130240.649 http://dd2.weather.gc.ca/ observations/swob-ml/20160328/CXVG/2016-03-28-1300-CXVG-AUTO-swob.xml 201 boule.example.com anonymous 1129.690082 parts=1,7046,1,0,0 sum=d,186fa9627e844a089c79764feda781a7 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM rename=/var/www/html/observations/swob-ml/20160328/CXVG/2016-03-28-1300-CXVG-AUTO-swob.xml message=Downloaded
  2016-03-28 09:21:30,524 [INFO] Received notice  20160328130240.964 http://dd2.weather.gc.ca/ bulletins/alphanumeric/20160328/CA/CWAO/13/CACN00_CWAO_281300__TBO_05037
  ^C2016-03-28 09:21:30,692 [INFO] signal stop
  2016-03-28 09:21:30,693 [INFO] sr_subscribe stop
  sarra@boule:~/.config/sarra/subscribe$

So the connection to upstream is functional. Connecting to the server means a queue is allocated on the server,
and it will continue to accumulate messages, waiting for the client to connect again. This was just a test, so we
want the server to discard the queue::

  sarra@boule:~/.config/sarra/subscribe$ sr_subscribe cleanup dd

now let's make sure the subscription does not start automatically::

  sarra@boule:~/.config/sarra/subscribe$ mv dd.conf dd.off

and turn to a sarra set up.



Sarra from Another Pump
~~~~~~~~~~~~~~~~~~~~~~~

Sarra works by having a downstream pump re-advertise products from an upstream one. Sarra needs all the configuration of a subscription,
but also needs the configuration to post to the downstream broker. The feeder account on the broker is used for this sort
of work, and is a semi-administrative user, able to publish data to any exchange. Assume apache is set up (not covered here) with a
document root of /var/www/html. The linux account we have created to run all the sr processes is '*sarra*', so we make sure
the document root is writable to those processes::

  sarra@boule:~$ cd ~/.config/sarra/sarra
  sarra@boule:~/.config/sarra/sarra$ sudo chown sarra.sarra /var/www/html

Then we create a configuration::

  sarra@boule:~$ cat >>dd.off <<EOT

  broker amqps://anonymous@dd.weather.gc.ca/
  exchange xpublic

  msg_to_clusters DD
  on_message msg_to_clusters

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

msg_to_clusters DD

on_message msg_to_clusters

   sarra implements routing by cluster, so if data is not destined for this cluster, it will skip (not download) a product.
   Inspection of the sr_subscribe output above reveals that products are destined for the DD cluster, so let's pretend to route
   for that, so that downloading happens.

url and document_root
   these are needed to build the local posts that will be posted to the ...

post_broker
   where we will re-announce the files we have downloaded.

mirror False
  This is usually unnecessary, when copying between pumps, it is normal to just make direct copies.
  However, the dd.weather.gc.ca pump predates the day/source prefix standard, so it is necessary for
  ease of cleanup.


So then try it out::

  sarra@boule:~/.config/sarra/sarra$ sr_sarra foreground dd.off 
  2016-03-28 10:38:16,999 [INFO] sr_sarra start
  2016-03-28 10:38:16,999 [INFO] sr_sarra run
  2016-03-28 10:38:17,000 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2016-03-28 10:38:17,604 [INFO] Binding queue q_anonymous.sr_sarra.dd.off with key v02.post.# from exchange xpublic on broker amqps://anonymous@dd.weather.gc.ca/
  2016-03-28 10:38:19,172 [INFO] Received v02.post.bulletins.alphanumeric.20160328.UA.CWAO.14 '20160328143820.166 http://dd2.weather.gc.ca/ bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422' parts=1,124,1,0,0 sum=d,cfbcb85aac0460038babc0c5a8ec0513 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM
  2016-03-28 10:38:19,172 [INFO] downloading/copying into /var/www/html/bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422
  2016-03-28 10:38:19,515 [INFO] 201 Downloaded : v02.report.bulletins.alphanumeric.20160328.UA.CWAO.14 20160328143820.166 http://dd2.weather.gc.ca/ bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422 201 boule.bsqt.example.com anonymous -0.736602 parts=1,124,1,0,0 sum=d,cfbcb85aac0460038babc0c5a8ec0513 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM message=Downloaded
  2016-03-28 10:38:19,517 [INFO] Published: '20160328143820.166 http://boule.bsqt.example.com/ bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422' parts=1,124,1,0,0 sum=d,cfbcb85aac0460038babc0c5a8ec0513 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM
  2016-03-28 10:38:19,602 [INFO] 201 Published : v02.report.bulletins.alphanumeric.20160328.UA.CWAO.14.UANT01_CWAO_281438___22422 20160328143820.166 http://boule.bsqt.example.com/ bulletins/alphanumeric/20160328/UA/CWAO/14/UANT01_CWAO_281438___22422 201 boule.bsqt.example.com anonymous -0.648599 parts=1,124,1,0,0 sum=d,cfbcb85aac0460038babc0c5a8ec0513 from_cluster=DD source=metpx to_clusters=DD,DDI.CMC,DDI.EDM message=Published
  ^C2016-03-28 10:38:20,328 [INFO] signal stop
  2016-03-28 10:38:20,328 [INFO] sr_sarra stop
  sarra@boule:~/.config/sarra/sarra$

The file has the suffix 'off' so that it will not be invoked by default when the entire sarra configuration is started.
One can still start the file when it is in the off setting, by specifying the path (in this case, it is in the current directory).
So initially have 'off' files while debugging the settings.
As the configuration is working properly, rename it to so that it will be used on startup::

  sarra@boule:~/.config/sarra/sarra$ mv dd.off dd.conf
  sarra@boule:~/.config/sarra/sarra$


Reports
~~~~~~~

Now that data is flowing, we need to take a look at the flow of report messages, which essentially are used by each pump to tell
upstream that data has been downloaded. Sr_audit helps with routing by creating the following configurations:

 - for each subscriber, a shovel configuration named rr_<user>2xreport.conf is created
 - for each source, a shovel configuration named rr_xreport2<user>user.conf is created

The *2xreport* shovels subscribes to messages posted in each user's xs_ exchange and posts them to the common xreport exchange.
Sample configuration file::

  # Initial report routing configuration created by sr_audit, tune to taste.
  #     To get original back, just remove this file, and run sr_audit (or wait a few minutes)
  #     To suppress report routing, rename this file to rr_anonymous2xreport.conf.off  

  broker amqp://tfeed@localhost/
  exchange xs_anonymous
  topic_prefix v02.report
  subtopic #
  accept_unmatch True
  on_message None
  on_post None
  report_back False
  post_broker amqp://tfeed@localhost/
  post_exchange xreport

Explanations:
  - report routing shovels are administrative functions, and therefore the feeder user is used.
  - this configuration is to route the reports submitted by the 'anonymous' user.
  - on_message None, on_post None,  reduce unwanted logging on the local system.
  - report_back False  reduce unwanted reports (do sources want to understand shovel traffic?)
  - post to the xreport exchange.

The *2<user>* shovels look at all the messages in the xreport exchange, and copy them to the users xr\_ exchange.
Sample::

  # Initial report routing to sources configuration, by sr_audit, tune to taste. 
  #     To get original back, just remove this file, and run sr_audit (or wait a few minutes)
  #     To suppress report routing, rename this file to rr_xreport2tsource2.conf.off  
  
  broker amqp://tfeed@localhost/
  exchange xreport
  topic_prefix v02.report
  subtopic #
  accept_unmatch True
  msg_by_source tsource2
  on_message msg_by_source
  on_post None
  report_back False
  post_broker amqp://tfeed@localhost/
  post_exchange xr_tsource2

Explanations:
  - msg_by_source tsource2 selects that only the reports for data injected by the tsource2 user should be 
    selected.
  - the selected reports should be copied to the user's xr\_ exchange, where that user invoking sr_report will find them.


When a source invokes the sr_report component, the default exchange will be xr\_ (eXchange for Reporting). All reports received
from subscribers to data from this source will be routed to this exchange.

If an administrator invokes sr_report, it will default to the xreport exchange, and show reports from all subscribers on the cluster.

Example::

  blacklab% more boulelog.conf

  broker amqps://feeder@boule.example.com/
  exchange xreport
  accept .*

  blacklab%

  blacklab% sr_report foreground boulelog.conf 
  2016-03-28 16:29:53,721 [INFO] sr_report start
  2016-03-28 16:29:53,721 [INFO] sr_report run
  2016-03-28 16:29:53,722 [INFO] AMQP  broker(boule.example.com) user(feeder) vhost(/)
  2016-03-28 16:29:54,484 [INFO] Binding queue q_feeder.sr_report.boulelog.06413933.71328785 with key v02.report.# from exchange xreport on broker amqps://feeder@boule.example.com/
  2016-03-28 16:29:55,732 [INFO] Received notice  20160328202955.139 http://boule.example.com/ radar/CAPPI/GIF/XLA/201603282030_XLA_CAPPI_1.5_RAIN.gif 201 blacklab anonymous -0.040751
  2016-03-28 16:29:56,393 [INFO] Received notice  20160328202956.212 http://boule.example.com/ radar/CAPPI/GIF/XMB/201603282030_XMB_CAPPI_1.5_RAIN.gif 201 blacklab anonymous -0.159043
  2016-03-28 16:29:56,479 [INFO] Received notice  20160328202956.179 http://boule.example.com/ radar/CAPPI/GIF/XLA/201603282030_XLA_CAPPI_1.0_SNOW.gif 201 blacklab anonymous 0.143819
  2016-03-28 16:29:56,561 [INFO] Received notice  20160328202956.528 http://boule.example.com/ radar/CAPPI/GIF/XMB/201603282030_XMB_CAPPI_1.0_SNOW.gif 201 blacklab anonymous -0.119164
  2016-03-28 16:29:57,557 [INFO] Received notice  20160328202957.405 http://boule.example.com/ bulletins/alphanumeric/20160328/SN/CWVR/20/SNVD17_CWVR_282000___01910 201 blacklab anonymous -0.161522
  2016-03-28 16:29:57,642 [INFO] Received notice  20160328202957.406 http://boule.example.com/ bulletins/alphanumeric/20160328/SN/CWVR/20/SNVD17_CWVR_282000___01911 201 blacklab anonymous -0.089808
  2016-03-28 16:29:57,729 [INFO] Received notice  20160328202957.408 http://boule.example.com/ bulletins/alphanumeric/20160328/SN/CWVR/20/SNVD17_CWVR_282000___01912 201 blacklab anonymous -0.043441
  2016-03-28 16:29:58,723 [INFO] Received notice  20160328202958.471 http://boule.example.com/ radar/CAPPI/GIF/WKR/201603282030_WKR_CAPPI_1.5_RAIN.gif 201 blacklab anonymous -0.131236
  2016-03-28 16:29:59,400 [INFO] signal stop
  2016-03-28 16:29:59,400 [INFO] sr_report stop
  blacklab%

From this listing, we can see that a subscriber on blacklab is actively downloading from the new pump on boule.
Basically, the two sorts of shovels built automatically by sr_audit will do all the routing needed within a cluster. 
When there are volume issues, these configurations can be tweaked to increase the number of instances or use
post_exchange_split where appropriate.

Manual shovel configuration is also required to route messages between clusters. It is just a variation
of intra-cluster report routing.


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

These are examples, the implementation of cleanup is not covered by sarracenia. Given a reasonably small tree as
given above, it can be practical to scan the tree and prune the old files from it.
A cron job like so::

  root@boule:/etc/cron.d# more sarra_clean
  # remove files one hour after they show up.
  # for weather production, 37 minutes passed the hour is a good time.
  # remove directories the day after the last time they were touched.
  37 4 * * *  root find /var/www/html -mindepth 1 -maxdepth 1 -type d -mtime +0  | xargs rm -rf

This might see a bit aggressive, but this file was on a very small virtual server that was only
intended for real-time data transfer so keeping data around for extended periods would have
filled the disk and stopped all transfers. In large scale transfers, there is always a trade
off between the practicality of keeping the data around forever, and the need for performance,
which requires us to prune directory trees regularly. File system performance is optimal with
reasonably sized trees, and when the trees get too large, the 'find' process to traverse it, can
become too onerous.

One can more easily maintain smaller directory trees by having them roll over regularly. If you
have enough disk space to last one or more days, then a single logical cron job that would operate
on the daily trees without incurring the penalty of a find is a good approach.

Replace the contents above with::

  34 4 * * * root find /var/www/html -mindepth 1 -maxdepth 1  -type d -regex '/var/www/html/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]' -mtime +1 | xargs rm -rf

where the +1 can be replaced by the number of days to retain. ( Would have preferred to
use [0-9]{8}, but it would appear that find's regex syntax does not include repetitions. )

Note that the logs will clean up themselves. By default after 5 retention the oldest log will be
remove at midnight if you have always use the same default config since the first rotation.
It can be shorten to a single retention by adding *logrotate 1d* to default.conf.

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

FIXME: elaborate sample sr_sender configuration.



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


Advanced Installations
----------------------

On some configurations (we usually call them *bunny*), we use a clustered rabbitmq, like so::

        /var/lib/rabbitmq/.erlang.cookie  same on all nodes

        on each node restart  /etc/init.d/rabbitmq-server stop/start

        on one of the node

        rabbitmqctl stop_app
        rabbitmqctl join_cluster rabbit@"other node"
        rabbitmqctl start_app
        rabbitmqctl cluster_status


        # having high availability queue...
        # here all queues that starts with "cmc." will be highly available on all the cluster nodes

        rabbitmqctl set_policy ha-all "^(cmc|q_)\.*" '{"ha-mode":"all"}'


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
  > with rabbitmqctl...  The only thing ldap would be used for would be
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




Hooks from Sundew
-----------------

This information is very likely irrelevant to almost all users. Sundew is another module of MetPX which is essentially being
replaced by Sarracenia. This information is only useful to those with an installed based of Sundew wishing to bridge
to sarracenia. The early work on Sarracenia used only the subscribe client as a downloader, and the existing WMO switch module
from MetPX as the data source. There was no concept of multiple users, as the switch operates as a single dissemination
and routing tool. This section describes the kinds of *glue* used to feed Sarracenia subscribers from a Sundew source.
It assumes a deep understanding of MetPX-Sundew. Currently, the dd_notify.py script creates messages for the
protocol exp., v00. and v02 (latest sarracenia protocol version).


Notifications on DD
~~~~~~~~~~~~~~~~~~~

As a higher performance replacement for Atom/RSS feeds which tell subscribers when new data is available, we put a broker
on our data dissemination server (dd.weather.gc.ca). Clients can subscribe to it. To create the notifications, we have
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
normal sender with something that builds AMQP messages as well. This Sundew sender config
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

The key for the topic includes a substitution. The *${0}* contains the directory tree where the
file has been placed on dd (with the / replaced by .)  For example, here is a log file entry::

  2013-06-06 14:47:11,368 [INFO] (86 Bytes) Message radar.24_HR_ACCUM.GIF.XSS++201306061440_XSS_24_HR_ACCUM_MM.gif:URP:XSS:RADAR:GIF::20130606144709  delivered (lat=1.368449,speed=168950.887119)

- So the key is: v02.post.radar.24_HR_ACCUM.GIF.XSS
- the file is placed under: http://dd1.weather.gc.ca/radar/24_HR_ACCUM/GIF/XSS
- the complete URL for the product is: http://dd1.weather.gc.ca/radar/24_HR_ACCUM/GIF/XSS/201306061440_XSS_24_HR_ACCUM_MM.gif


