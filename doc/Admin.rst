
=====================================
 MetPX-Sarracenia for Administrators
=====================================

.. NOTE::

   NOT TO BE TRUSTED.  THERE IS NO MANUAL YET.
   IF YOU DOWNLOADED THIS PACKAGE... IT IS STILL BEING DEVELOPED. 
   USAGE MAY CHANGE.  NOT RELEASED YET.

.. Contents::


Revision Record
---------------

Pre-Draft.  This document is still being built and should not be reviewed or relied upon.


Introduction
------------

Sarracenia pumps form a network.  Each network uses a rabbitmq broker as a transfer manager,
which sends advertisements in one direction, and log messages in the opposite direction.
Administrators manually configure the paths that data flow at each switch, as each broker acts 
independently, managing transfers from transfer engines it can reach, with no knowledge of 
the overall network.  The locations of switches and the directions of traffic flow are 
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
~~~~~~~~~~~~~~~~~~~~~~

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

- usually, sr_source2log will read xs_alice and copy the log messages onto the private xlog exchange.

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



Transport Engines
-----------------

Transport engines are the data servers queried by subscribers, be they end users, or other pumps.
The subscribers read the notices and fetch the corresponding data, using the indicated protocol.
The software to serve the data can be either SFTP or HTTP (or HTTPS.) For specifics of 
configuring the servers for use, please consult the documentation of the servers themselves.
The recipes here are simply examples, and are not definitive.

Sample lighttpd Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Suitable when all the data being served is public, simply make the /var/www directory available::

 cat >/etc/lighttpd/lighttpd.conf <<EOT

  server.modules = ()

  dir-listing.activate = "enable"
  
  server.document-root        = "/var/www"
  server.upload-dirs          = ( "/var/cache/lighttpd/uploads" )
  server.errorlog             = "/var/log/lighttpd/error.log"
  server.pid-file             = "/var/run/lighttpd.pid"
  server.username             = "www-data"
  server.groupname            = "www-data"
  server.port                 = 80
  
  
  index-file.names            = ( "index.php", "index.html", "index.lighttpd.html" )
  url.access-deny             = ( "~", ".inc" )
  
  # default listening port for IPv6 falls back to the IPv4 port
  ## Use ipv6 if available
  include_shell "/usr/share/lighttpd/use-ipv6.pl " + server.port
  include_shell "/usr/share/lighttpd/create-mime.assign.pl"
  include_shell "/usr/share/lighttpd/include-conf-enabled.pl"
  
  EOT

  service lighttpd start

This configuration will show all files under /var/www as folders, running under
the www-data users.  Data posted in such directories must be readable to the www-data
user, to allow the web server to read it.  so user of dd_post/dd_watch need to 
place files under there and announce as http://<server>/...


Apache Web Server
~~~~~~~~~~~~~~~~~

FIXME:
some configuration snippets for the apache web server.



OpenSSH Configuration
~~~~~~~~~~~~~~~~~~~~~

So any server to which ssh, or sftp, restricted or even chrooted will be accessible to the pump.
The configuration of such services is out of scope of this
FIXME... special tunable notices here.



Installation 
------------

The package is built in python3, and has a few dependencies.  


From Source
~~~~~~~~~~~

See Development Guide for instructions on how to build the various type of
package files.


Debian-Derived
~~~~~~~~~~~~~~

The package can be downloaded from metpx.sf.net and installed.

   dpkg -i metpx-sarracenia-0.1.1.all.dpkg



PIP
~~~

For many special cases, such as if using python in virtual env, it might be more pragmatic 
to install the package using pip (python install package) from http://pypi.python.org/_.
The application is registered in PyPi, 

pip install metpx-sarracenia

and to upgrade:

pip install --upgrade metpx-sarracenia


Local Python 
~~~~~~~~~~~~

notes::

    python3 setup.py build
    python3 setup.py install


Windows
~~~~~~~

Any native python installation will do, but the dependencies in the standard python.org
installation require the installation of a C-Compiler as well, so it gets a bit complicated.
If you have an existing python installation that works with c-modules within it, then the
complete package should install with all features.

If you do not have a python environment handy, then the easiest one to get going with
is winpython, which includes many scientifically relevant modules, and will easily install
all dependencies for Sarracenia. You can obtain winpython from http://winpython.github.io/_
(note: select python version >3 ) Then one can install a wheel from sourceforge, or using 
pip. 


Operations
----------

To operate a pump, there needs to be a user designated as the adminsitrator.
The administrator is different from the others mostly in the permission granted
to create exchanges, and the ability to run processes that address the common
exchanges (xpublic, xlog, etc...) All other users are limited to being able to 
access only their own queues.

The administrative user name is an installation choice, and exactly as for any other 
user, the configuration files are placed under ~/.config/sarra/, with the 
defaults under sarra.conf, and the configurations for components under
directories named after each component.  In the component directories,
Configuration files have the .conf suffix.  User roles are configured by
the users.conf file.

..note:: 
  FIXME: missing users.conf(7) man page.
  FIXME: missing credentials.conf(7) man page. do we need this?

The administrative processes perform validation of postings from sources, and once
they are validated, forward them to the public exchanges for subscribers to access.
The processes that are typically run on a broker:
 
- sr_sarra - various configurations to pull from other switches data to make it available from the pump.
- sr_sarra - in full validation to pull data from local sources for to make it available from the pump.
- sr_winnow - when there are multiple redundant sources of data, select the first one to arrive, and feed sr_sarra.
- sr_log2cluster - when a log message is destined for another cluster, send it where it should go.
- sr_source2log - when a log message is posted by a user, copy it to xlog exchange for routing and monitoring.
- sr_log2source - when a log message is on the xlog exchange, copy to the source that should get it.
- sr_police  - aka. queue_manager.py, kill off useless or empty queues.
- sr_police2 - look for dead instances, and restart them? (cron job in sundew.)

As for any other user, there may be any number of configurations
to set up, and all of them may need to run at once.  To do so easily, one can invoke:

  sr start

to start all the files with named configurations of each component (sarra, subscribe, winnow, log, etc...)
Additionally, if the admin mode is set in ~/.config/sarra/sarra.conf like so:

 admin True

Then the log and police components are started as well.  It is standard practice to use a different
AMQP user for administrative tasks, such as exchange or user creation, from data flow tasks, such as
pulling and posting data.  Normally one would place credentials in ~/.config/sarra/credentials.conf
for each account, and the various configuration files would use the appropriate account.


.. note::
 
  FIXME: does root or feeder run the log processes.
  FIXME: we should probably rename sarra.conf to default.conf.  It is confusing for it to be named
  after a configurable component... and not really configure that component.


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
sr_sarra configurations from one switch to the next.  Each sr_sarra link is configured by:


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
  through different nodes.  So one will see parts of files announced by such switches, to be
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



Standalone
~~~~~~~~~~

In a standalone configuration, there is only one node in the configuration.  It runs all components
and shares none with any other nodes.  That means the Broker and data services such as sftp and
apache are on the one node.

One appropriate usage would be a small non-24x7 data acquisition setup, to take responsibility of data
queueing and transmission away from the instrument.  It is restarted when the opportunity arises.
It is just a matter of installing and configuring all a data flow engine, a broker, and the package
itself on a single server.


.. note::

   FIXME: go through the topologies in design/design.rst, and document what we think is relevant.


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
  

Security Scanning
~~~~~~~~~~~~~~~~~

In cases where security scanning of file being transferred is deemed necessary, one configures sarra with an on_part hook.
FIXME: need an example of an on_file hook to call Amavis.  Have it check which part of a file is in question, and only scan
the initial part.


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



   
