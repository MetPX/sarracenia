
=====================================
 MetPX-Sarracenia for Administrators
=====================================

.. note::
  Pardon the dust, This package is alpha, not ready for general use yet. Please Stay Tuned!
  FIXME: Missing sections are highlighted by FIXME.  What is here should be accurate!

.. Contents::


Revision Record
---------------

Pre-Draft.  This document is still being built and should not be reviewed or relied upon.
the term FIXME is present to indicate locations where content addition is expected.

:version: @Version@ 
:date: @Date@



Introduction
------------

Sarracenia pumps form a network.  Each network uses a rabbitmq broker as a transfer manager
which sends advertisements in one direction and log messages in the opposite direction.
Administrators manually configure the paths that data flow at each pump, as each broker acts 
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
when delivering, it is ideal if the receivers use sr_subscribe, and a file_received hook
to trigger their further processing, so that the file is handed to them without polling.
This is the most efficient way of working, but it is understood that not all software
can be made co-operative.

Generally speaking, Linux is the main deployment target, and the only platform on which
server configurations are deployed.  Other platforms are used as client end points.
This isn´t a limitation, it is just what is used and tested.  Implementations of
the pump on Windows should work, they just are not well tested.


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
  - by convention, the default vhost '/' is always used.  Use of other vhosts is untested.
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
      - queues start with q


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
types of ´spoofing´ as all messages can only be posted by proper owners.


Users and Roles
---------------

Usernames for pump authentication are significant in that they are visible to all.
They are used in the directory path on public trees, as well as to authenticate to the broker.
They need to be understandable.  they are often wider scope than a person...
perhaps call them 'Accounts'.   It can be elegant to configure the same usernames
for use in transport engines.

All Account names should be unique, but nothing will avoid clashes when sources originate from
different pump networks, and clients at different destinations.  In practice, name clases are
addressed by routing to avoid two different sources' with the same name having their 
data offerings combined on a single tree.  On the other hand, name clashes are not always an error.  
Use of a common source account name on different clusters may be used to implement folders that
are shared between the two accounts with the same name.  


Pump users are defined in the users.conf file. Each line of the file consists of the user name
as the first field, and the user's role as the second field.  role can be one of:

subscriber

  A subscriber is user that can only subscribe to data and return log messages. Not permitted to inject data.
  Each subscriber gets an sx_<user> named exchange on the pump, where if a user is named *Acme*, 
  the corresponding exchange will be *sx_Acme*.  This exchange is where an sr_subscribe
  process will send it's log messages.

  By convention/default, a the *anonymous* user is created on all pumps to permit subscription without
  a specific account.

source

  A user permitted to subscribe or originate data.  A source does not necessarily represent 
  one person or type of data, but rather an organization responsible for the data produced.  
  So if an organization gathers and makes available ten kinds of data with a single contact 
  email or phone number for questions about the data and it's availability, then all of 
  those collection activities might use a single 'source' account.
  
  Each source gets a sx_<user> exchange for injection of data posts, and, similar to a subscriber
  to send log messages about processing and receipt of data.

  Each source is able to view all of the messages for data it has injected, but the location where
  all of these messages are available varies according to administrator configuration of log routing.
  So a source may inject data on pumpA, but may subscribe to logs on a different pump.

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


pump

  a user permitted to subscribe or originate data, but understood to represent a pump.
  a local pump user would be used to, say, run the sarra processes.


administrator
  a user permitted to modify permissions on the local pump.  
  The administrator also runs the log routing components such 
  as log2source, 2xlog, log2cluster, etc...
  

.. note::
  FIXME: makes more sense to me for a pump user to run the log routing stuff,
  and just keep manager for administrative change.  throughts?

  FIXME: manager run log* things. I doubt it works this way now... ie. those
  components should use the 'manager' setting instead of the 'broker' one?
  the 'broker' one will be the 'feeder' aka. pump ?





Transport Engines
-----------------

Transport engines are the data servers queried by subscribers, be they end users, or other pumps.
The subscribers read the notices and fetch the corresponding data, using the indicated protocol.
The software to serve the data can be either SFTP or HTTP (or HTTPS.) For specifics of 
configuring the servers for use, please consult the documentation of the servers themselves.
The recipes here are simply examples, and are not definitive.

.. note:: 
   FIXME:  Not clear what to do here.  The application does not work without transport engines,
   but configuration of those engines are vast topics in their own right, so not a good idea
   to include configuration information here, other than to indicate the kind of settings
   that are necessary to permit operation.

httpd Configuration
~~~~~~~~~~~~~~~~~~~

Suitable when all the data being served is public, simply make a directory available.
the server needs to support byte-ranges, but that is not onerous as the popular ones do.

.. note::
   FIXME: I believe if the server is not dedicated to being a pump, and someone wants an
   offset from / to be the root of the pump... I think that's will not work.
   Sarra wants to be in the document root right now. Is this a bug?



OpenSSH Configuration
~~~~~~~~~~~~~~~~~~~~~

So any server to which ssh, or sftp, restricted or even chrooted will be accessible to the pump.
The configuration of such services is out of scope of this
FIXME... special tunable notices here.


SFTP Configuration
~~~~~~~~~~~~~~~~~~

Open SSH with restricted shell.


Operations
----------

To operate a pump, there needs to be a user designated as the pump administrator.
The administrator is different from the others mostly in the permission granted
to create exchanges, and the ability to run processes that address the common
exchanges (xpublic, xlog, etc...) All other users are limited to being able to 
access only their own queues.

The administrative user name is an installation choice, and exactly as for any other 
user, the configuration files are placed under ~/.config/sarra/, with the 
defaults under default.conf, and the configurations for components under
directories named after each component.  In the component directories,
Configuration files have the .conf suffix.  User roles are configured by
the users.conf file.

..note:: 
  FIXME: missing users.conf(7) man page.
  joe [subscriber|source|pump|admin]


The administrative processes perform validation of postings from sources, and once
they are validated, forward them to the public exchanges for subscribers to access.
The processes that are typically run on a broker:
 
- sr_sarra   - various configurations to pull data from other pumps to make it available from the local pump.
- sr_sarra   - to pull data in from local sources to make it available from the pump.
- sr_winnow  - when there are multiple redundant sources of data, select the first one to arrive, and feed sr_sarra.
- sr_poll    - for sources without advertisements, revert to explicit polling for initial injection.
- sr_log2cluster - when a log message is destined for another cluster, send it where it should go.
- sr_2xlog   - when a log message is posted by a user, copy it to xlog exchange for routing and monitoring.
- sr_log2source - when a log message is on the xlog exchange, copy to the source that should get it.
- sr_police  - aka. queue_manager.py, kill off useless or empty queues.
- sr_police2 - look for dead instances, and restart them? (cron job in sundew.)

As for any other user, there may be any number of configurations
to set up, and all of them may need to run at once.  To do so easily, one can invoke:

  sr start

to start all the files with named configurations of each component (sarra, subscribe, winnow, log, etc...)
To run as a broker administrator, the Manager option is set in ~/.config/sarra/default.conf like so:

  manager amqp://adminuser:adminpw@localhost/

Then the log and police components are started as well.  It is standard practice to use a different
AMQP user for administrative tasks, such as exchange or user creation, from data flow tasks, such as
pulling and posting data.  Normally one would place credentials in ~/.config/sarra/credentials.conf
for each account, and the various configuration files would use the appropriate account.


Housekeeping - sr_police
~~~~~~~~~~~~~~~~~~~~~~~~

When a client connects to a broker, it creates a queue which is then bound to an exchange.  The user 
can choose to have the client self-destruct when disconnected (*auto-delete*), or it can make 
it *durable* which means it should remain, waiting for the client to connect again, even across
reboots.  Clients often want to pick up where they left off, so the queues need to stay around.

queue_manager.py

The rabbitmq broker will never destroy a queue that is not in auto-delete (or durable.)  This means they will build up over time.  We have a script that looks for unused queues, and cleans them out. Currently, the limits are hard-coded as any queue having more than 25000 messages or 50mbytes of space will be deleted.

This script is in samples/program, rather than as part of the package (as an sr_x command.)


Routing
-------

Data
~~~~

The inter-connection of multiple pumps is done, on the data side, simply by daisy-chaining
sr_sarra configurations from one pump to the next.  Each sr_sarra link is configured by:

.. note::
  FIXME: sample sarra used to pull from another pump.

.. note::
  FIXME:: sample sender to push to another pump.

.. note::
  DB cleanup is not described... (cleaning up old days)
  cron? root? pump admin? 
  need to talk about permissions with people delivering via sftp?

Logs
~~~~

Log messages are defined in the sr_log(7) man page.  They are emitted by *consumers* at the end,
as well as *feeders* as the messages traverse pumps.  log messages are posted to
the xl_<user> exchange, and after log validation send through the xlog exchange.

Messages in xlog destined for other clusters are routed to destinations by
log2cluster component using log2cluster.conf configuration file.  log2cluster.conf
uses space separated fields: First field is the cluster name (set as per **cluster** in
post messages, the second is the destination to send the log messages for posting
originating from that cluster to) Sample, log2cluster.conf::

      clustername amqp://user@broker/vhost exchange=xlog

Where message destination is the local cluster, log2user (log2source?) will copy
the messages where source=<user> to sx_<user>, ready for consumption by sr_log.


What is Going On?
-----------------

the sr_log command can be invoked, overriding the default exchange to bind to 'xlog' instead
in order to get log information for an entire broker.


.. NOTE:: 
   config sample of looking at xlog.

Canned sr_log configuration with an onmessage action can be configured to gather statisical 
information is a speedo on various aspects of operations.

.. NOTE::
   FIXME:
   first canned sr_log configuration would be speedo...
   speedo: total rate of posts/second, total rate of logs/second.
   question: should posts go to the log as well?
   before operations, we need to figure out how Nagios will monitor it.

   Is any of this needed, or is the rabbit GUI enough on it's own?


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

.. note:: 
  need samples of sr_poll configuration.


Standalone
~~~~~~~~~~

In a standalone configuration, there is only one node in the configuration.  It runs all components
and shares none with any other nodes.  That means the Broker and data services such as sftp and
apache are on the one node.

One appropriate usage would be a small non-24x7 data acquisition setup, to take responsibility of data
queueing and transmission away from the instrument.  It is restarted when the opportunity arises.
It is just a matter of installing and configuring all a data flow engine, a broker, and the package
itself on a single server.



Rabbitmq Setup 
--------------

Sample information on setting up a rabbitmq broker for sarracenia to use.  The broker does not have to 
be on the same host as anything else, but there has to be one reachable from at least one of the 
transport engines.


Installation
~~~~~~~~~~~~

Generally speaking, we want to stay above 3.x version.  

https://www.rabbitmq.com/install-debian.html
  - enable their repo. get the latest rabbitmq
  - the one in the wheezy depot is < 3.  too old?

apt-get update
apt-get install rabbitmq-server

in upto-date distros, you likely can just take the distro version.

The initial configuration of a broker set up as a Sarracenia data pump involves creating a number
of exchanges and using a number of conventions around permissions. this setup needs to be done
as root. We assume that admin work is done on the same server that is running the broker.

The following configure rabbit for initial use::

  # enabling management web application
  # this is important since sr_rabbit uses this management facility/port access
  # to retrieve some important info

  rabbitmq-plugins enable rabbitmq_management
  /etc/init.d/rabbitmq-server restart

  # Obtain the rabbitmqadmin script from the broker just installed.  
  cd /usr/local/sbin
  wget http://localhost:15672/cli/rabbitmqadmin
  chmod 755 rabbitmqadmin

  # within sarracenia,  the creation of exchanges is done by the broker administrator
  # mandatory exchanges should be created (xpublic, xlog)

  rabbitmqadmin -H broker.domain.com -u root -p ********* declare exchange name=xpublic type=topic auto_delete=false durable=true
  rabbitmqadmin -H broker.domain.com -u root -p ********* declare exchange name=xlog    type=topic auto_delete=false durable=true


SSL Setup
~~~~~~~~~

This should be mandatory, and included here as part of setup.
Wait until December 3rd, 2015... see if letsencrypt provides a simpler setup method.

.. NOTE::
   FIXME: Document this.


Change Defaults 
~~~~~~~~~~~~~~~

By default, an installation of a rabbitmq-server makes user guest the administrator... with password guest
This should be changed for operational implementations... To void the guest user we suggest

  rabbitmqctl set_user_tags guest
  rabbitmqctl list_user_permissions guest
  rabbitmqctl change_password guest ************

And another administrator should be defined... we usually call it root...

  rabbitmqctl add_user root   *********
  rabbitmqctl set_user_tags root administrator
  rabbitmqctl set_permissions root   ".*" ".*" ".*"



Add a Feeder
~~~~~~~~~~~~

Each pump has a user that does the pump's activities, such as for use by sr_sarra running locally.
It is usually feeder users that subscribe to other pumps to pull data in.
That is a user with all permissions should be used on sarracenia broker...

  rabbitmqctl add_user feeder <password>
  rabbitmqctl set_permissions feeder   ".*" ".*" ".*"

Feeders read from user queues, validate that there is no spoofing, and then further process.

At the operating system level...
sr_sarra is usually invoked by the feeder user, so it needs to have permission
users?


Add User
~~~~~~~~

This just shows how to add a user to Rabbitmq broker with appropriate permissions.
You will need to cover authentication as needed by the payload transport protocol
(SFTP, FTP, or HTTP(S)) separately.

These users have the permissions to allow use the client programs sr_post, sr_subscribe, etc... 
They can declare queues for their own use (with names that identify them clearly) and they can 
read from xpublic, and their own log exchange but they are only able to write their xs_<user> 
exchange.

Adding a user at the broker level and its permission (conf,write,read)::

  rabbitmqctl add_user Alice <password>
  rabbitmqctl set_permissions -p / Alice   "^q_Alice.*$" "^q_Alice.*$|^xs_Alice$" "^q_Alice.*$|^xl_Alice$|^xpublic$"

or, parametrized::

  u=Alice
  rabbitmqctl add_user ${u} <password>
  rabbitmqctl set_permissions -p / ${u} "^q_${u}.$" "^q_${u}.*$|^xs_${u}$" "^q_${u}.*$|^xl_${u}$|^xpublic$"


Then you need to do the same work for sftp and or apache servers as required.



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

To enable LDAP authentication for rabbitmq:

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



requires RABBITMQ > 3.3.x
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
in the ~/.config/sarra/credentials.conf file, and that that file is forced to 600 permissions.  

The most secure method of transport is the use of SFTP with keys rather than passwords.  Secure
storage of sftp keys is covered in documentation of various SSH or SFTP clients. The credentials
file just points to those key files.

For sarracenia itself, password authentication is used to communicate with the AMQP broker,
so implementation of encrypted socket transport (SSL/TLS) on all broker traffic is strongly 
recommended.  

Sarracenia users are actually users defined on rabbitmq brokers. 
Each user Alice, on a broker to which she has access:

 - has an exchange xs_Alice, where she writes her postings, and reads her logs from.
 - has an exchange xl_Alice, where she writes her log messages.
 - can create queues qs_Alice\_.* to bind to exchanges.
 - Alice can create and destroy her own queues, but no-one else's.
 - Alice can only write to her exchange (xs_Alice),
 - Exchanges are managed by the administrator, and not any user.
 - Alice can only post data that she is publishing (it will refer back to her)

Cannot create any exchanges or other queues not shown above.

Rabbitmq provides the granularity of security to restrict the names of
objects, but not their types.  Thus, given the ability to create a queue named q_Alice,
a malicious Alice could create an exchange named q_Alice_xspecial, and then configure
queues to bind to it, and establish a separate usage of the broker unrelated to sarracenia.

To prevent such mis-use, sr_police is a component that is invoked regularly looking
for mis-use, and cleaning it up.

.. NOTE::
   FIXME:  sr_police is a renaming of queue_manager.py queue_manager currently only looks for
   obsolete queues with high number of items queued, or which have not been accessed in a long
   time.  Need to add the feature of looking for exchanges that do not start with x and delete
   them.

   

Input Validation
~~~~~~~~~~~~~~~~

Users such as Alice post their messages to their own exchange (xs_Alice).  Processes which read from 
user exchanges have a responsibility for validation.   The process that reads xs_Alice (likely an sr_sarra) 
will overwrite any *source* or *cluster* heading written into the message with the correct values for
the current cluster, and the user which posted the message.  

The checksum algorithm used must also be validated.  The algorithm must be known.  Similarly, the
there is a malformed header of some kind, it should be rejected immediately.  Only well-formed messages
should be forwarded for further processing.

In the case of sr_sarra, using the onpart trigger, the checksum must be re-calculated from the data,
to ensure they match.  If they do not match, the file will not be forwarded.  Depending on the level of 
confidence between a pair of pumps, the level of validation may be relaxed to improve performance.  That 
is the reason for the *recompute_checksum* option.  If set to false, there should be a performance improvement.

Another difference with inter-pump connections, is that a pump necessarily acts as an agent for all the
users on the remote pumps and any other pumps the pump is forwarding for.  In that case the validation
constraints are a little different:

- source doesn´t matter. (feeders can represent other users, so do not overwrite.) 
- ensure cluster is not local cluster (as that indicates either a loop or misuse.)

If the message fails the non-local cluster test, it should be rejected (and the rejection logged back to...
hmm...)

FIXME:
   - if the source is not good, and the cluster is not good... cannot log back. so just log locally?


Privileged System Access
~~~~~~~~~~~~~~~~~~~~~~~~

No sarracenia accounts of require privileged system of any kind.  The pump administrator account requires
privileges only on the AMQP broker, but nothing on the underlying operating system.   

The may be a single task which must operate with privileges: cleaning up the database, which is an easily
auditable script that must be run on a regular basis.  If all acquisition is done via sarra, then all of
the files will belong to the pump administrator, and privileged access is not required for this either.


Content Scanning
~~~~~~~~~~~~~~~~

In cases where security scanning of file being transferred is deemed necessary, one configures sarra with an on_part hook.


.. NOTE::
  FIXME: need an example of an on_part hook to call Amavis.  Have it check which part of a file is in question, 
  and only scan the initial part.  
  use on_part hook, check which part it is, if > 2 don't bother.


Hooks from Sundew
-----------------

The early work on Sarracenia used only the subscribe client as a downloader, and the existing WMO switch module from MetPX as the data source.  There was no concept of multiple users, as the switch operates as a single dissemination and routing tool.  This section describes the kinds of *glue* used to feed Sarracenia subscribers from a Sundew source. It assumes a deep understanding of MetPX-Sundew. Currently the dd_notify.py script creates messages for the protocol exp., v00. and v02 (latest sarracenia protocol version)


Notifications on DD 
~~~~~~~~~~~~~~~~~~~

As a higher performance replacement for Atom/RSS feeds which tell subscribers when new data is available, we put a broker on our data dissemination server (dd.weather.gc.ca.) Clients can subscribe to it.  To create the notifications, we have one Sundew Sender (named wxo-b1-oper-dd.conf) with a send script::

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



   
