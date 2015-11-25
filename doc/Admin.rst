
=====================================
 MetPX-Sarracenia for Administrators
=====================================

.. Contents::


Revision Record
---------------

Pre-Draft.  This document is still being built and should not be reviewed or relied upon.


Introduction
------------

This Manual is a stub for now.  There is no useful Guide yet.  The man pages for the 
individual commands are by and large accurate, but guides are missing for now.  
This is a collection of tidbits that try to hint at how some tasks are accomplished.

Mapping AMQP Concepts to Sarracenia
-----------------------------------

One thing that is safe to say is that one needs to understand a bit about AMQP to work 
with Sarracenia.  AMQP is a vast and interesting topic in it's own right.  No attempt is 
made to explain all of it here. This brief just provides a little context, and introduces only 
background concepts needed to understand and/or use Sarracenia.  For more information 
on AMQP itself, a set of links is maintained at 
the `Metpx web site <http://metpx.sourceforge.net/#amqp>`_ but a search engine
will also reveal a wealth of material.

.. image:: AMQP4Sarra.svg
    :scale: 50%
    :align: center

An AMQP Server is called a Broker. *Broker* is sometimes used to refer to the software,
other times server running the broker software (same confusion as *web server*.) In the above diagram, AMQP vocabulary is in Orange, and Sarracenia terms are in blue.
 
There are many different broker software implementations. We use rabbitmq. 
We are not trying to be rabbitmq specific, but management functions differ 
between implementations.  So admin tasks require 'porting' while the main application 
elements do not.

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

- A MetPX-Sarracenia pump is a python AMQP application that uses an (rabbitmq) 
  broker to co-ordinate SFTP and HTTP client data transfers, and accompanies a 
  web server (apache) and sftp server (openssh) on the same user-facing address.  

- Wherever reasonable, we use their terminology and syntax. 
  If someone knows AMQP, they understand. If not, they can research.

  - Users configure a *broker*, instead of a pump.
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



Installation 
------------

There is no installation procedure yet.  It is really a developer type process for now.
Currently the only way to install is to git clone from the sf.net.
The package is build in python3, and has a few dependencies.  On a debian derived Linux,
one can build a debian package with ´debuild´ (in the sarracenia sub-directory), or 

Debian-Derived
~~~~~~~~~~~~~~

Notes::
        debuild -uc 
	dpkg -i ../metpx-sarracenia-0.1.1.all.dpkg

Native Python 
~~~~~~~~~~~~~

notes::

	 python3 setup.py build
	 python3 setup.py install


Operations
----------

Stuff that should be running on a broker ::

  sr_log2source
  sr_source2log
  sr_log2cluster
  and some number of sr_winnows and sr_sarra's.
  queue_manager.py


Add User
~~~~~~~~

Adding a user at the broker level  

  rabbitmqctl add_user Alice <password>

When subscriber (sr_subscribe,dd_subscribe) only, permissions are (conf,write,read):

  rabbitmqctl set_permissions -p / Alice   "^q_Alice.*$" "^q_Alice.*$|^xs_Alice$" "^q_Alice.*$|^xpublic$"

When provider (sr_post,sr_watch...) permissions are :

  rabbitmqctl set_permissions -p / Alice   "^q_Alice.*$" "^q_Alice.*$|^xs_Alice$" "^q_Alice.*$|^xl_Alice$|^xpublic$"

A functional user with all permissions should be used on sarracenia broker...

  rabbitmqctl add_user feeder <password>
  rabbitmqctl set_permissions -p / Alice   ".*" ".*" ".*"

By default an installation of a rabbitmq-server makes user guest the administrator... with password guest
This should be changed for operational implementations... To void the guest user we suggest

  rabbitmqctl set_user_tags guest
  rabbitmqctl list_user_permissions guest
  rabbitmqctl change_password guest ************

And another administrator should be defined... we usually call it root...

  rabbitmqctl add_user root   *********
  rabbitmqctl set_user_tags root administrator

Then you need to do the same work for sftp and or apache servers as required.


Housekeeping
~~~~~~~~~~~~

When a client connects to a broker, it creates a queue which is then bound to an exchange.  The user 
can choose to have the client self-destruct when disconnected (*auto-delete*), or it can make 
it *durable* which means it should remain, waiting for the client to connect again, even across
reboots.  Clients often want to pick up where they left off, so the queues need to stay around.

queue_manager.py

The rabbitmq broker will never destroy a queue that is not in auto-delete (or durable.)  This means they will build up over time.  We have a script that looks for unused queues, and cleans them out. Currently, the limits are hard-coded as any queue having more than 25000 messages or 50mbytes of space will be deleted.



Rabbitmq Setup 
--------------

Sample information on setting up a rabbitmq broker for sarracenia to use.

Installation
~~~~~~~~~~~~

On machines that need to process AMQP messages, we need to install the server (or ´broker´) by installing the rabbitmq-server package.  On a debian derived system, the broker is installed as follows:

apt-get install rabbitmq-server


then run a bunch of configuration commands::

  # create anonymous user
  # password ********* provided in patates
  #                                          conf write read
  rabbitmqctl add_user anonymous *********
  rabbitmqctl set_permissions -p / anonymous   "^xpublic|^amq.gen.*$|^cmc.*$"     "^amq.gen.*$|^cmc.*$"    "^xpublic|^amq.gen.*$|^cmc.*$"
  rabbitmqctl list_user_permissions anonymous
  
  # create feeder user
  # password ********* provided in patates
  #                                       conf write read
  rabbitmqctl add_user feeder ********
  rabbitmqctl set_permissions -p / feeder  ".*"  ".*"  ".*"
  rabbitmqctl list_user_permissions feeder
  
  # create administrator user
  # password ********* provided in patates
  
  rabbitmqctl add_user root   *********
  rabbitmqctl set_user_tags root administrator
  
  # takeaway administrator privileges from guest
  rabbitmqctl set_user_tags guest
  rabbitmqctl list_user_permissions guest
  rabbitmqctl change_password guest ************

  # list users
  rabbitmqctl list_users

  # enabling management web application
  # this is important since sr_rabbit uses this management facility/port access
  # to retrieve some important info

  rabbitmq-plugins enable rabbitmq_management
  /etc/init.d/rabbitmq-server restart


Clustered Broker 
~~~~~~~~~~~~~~~~

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



   
