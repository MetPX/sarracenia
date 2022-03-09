
====================
Historical Revisions
====================

.. contents::


Introduction
~~~~~~~~~~~~

AMQP stands for Advanced Message Queuing Protocol.
It is the definition of a protocol that comes from the need to standardize an asynchronous message change system.
In AMQP jargon we will talk about message producers, message consumers and broker.

RABBITMQ-SERVER installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On our machines that need to process AMQP messages,
we install the broker, by installing the package rabbitmq-server_3.3.5-1_all.deb.
The basic installation is done as follows on all our machines::

    # installing package taken on the rabbitmq homepage
    # rabbitmq-server version > 3.3.x  required to use ldap for passwords verification only
    
    apt-get install erlang-nox
    dpkg -i /tmp/rabbitmq-server_3.3.5-1_all.deb
    
    # create anonymous user
    # password ********* provided in potato
    #                                          conf write read
    rabbitmqctl add_user anonymous *********
    rabbitmqctl set_permissions -p / anonymous   "^xpublic|^amq.gen.*$|^cmc.*$"     "^amq.gen.*$|^cmc.*$"    "^xpublic|^amq.gen.*$|^cmc.*$"
    rabbitmqctl list_user_permissions anonymous
    
    # create feeder user
    # password ********* provided in potato
    #                                       conf write read
    rabbitmqctl add_user feeder ********
    rabbitmqctl set_permissions -p / feeder  ".*"  ".*"  ".*"
    rabbitmqctl list_user_permissions feeder
    
    # create administrator user 
    # password ********* provided in potato
    
    rabbitmqctl add_user root   *********
    rabbitmqctl set_user_tags root administrator
    
    # takeaway administrator privileges from guest
    rabbitmqctl set_user_tags guest
    rabbitmqctl list_user_permissions guest
    rabbitmqctl change_password guest *************
    
    # list users 
    rabbitmqctl list_users
     
    
    # enabling management web application 
    # this is important since sr_rabbit uses this management facility/port access
    # to retrieve some important info
    
    rabbitmq-plugins enable rabbitmq_management
    /etc/init.d/rabbitmq-server restart



RABBITMQ-SERVER cluster installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On the bunny we have opted for a cluster installation. To do this we follow the following instructions::

    Stop rabbitmq-server on all nodes....
    
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



RABBITMQ-SERVER ldap installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On the servers where we want to have an authentication using the following instructions::

         rabbitmq-plugins enable rabbitmq_auth_backend_ldap

         # replace username by ldap username
         # clear password (will be verified through the ldap one)
         rabbitmqctl add_user username aaa
         rabbitmqctl clear_password username
         rabbitmqctl set_permissions -p / username "^xpublic|^amq.gen.*$|^cmc.*$" "^amq.gen.*$|^cmc.*$" "^xpublic|^amq.gen.*$|^cmc.*$"


And we configure the LDAP services in the rabbitmq-server configuration file
(old test configuration of ldap-dev which worked only...)::

    cat /etc/rabbitmq/rabbitmq.config 
    [
    {rabbit, [{auth_backends, [ {rabbit_auth_backend_ldap,rabbit_auth_backend_internal}, rabbit_auth_backend_internal]}]},
    {rabbitmq_auth_backend_ldap,
        [ 
        {servers,               ["ldap-dev.cmc.ec.gc.ca"]},
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



Use of AMQP on DD (DDI, DD.BETA)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We (Peter) wanted to do an implementation of AMQP in METPX.
To do this, we use the python-amqplib library which implements the necessary functionality of AMQP in python.
We have thus developped a pxSender of type amqp which is the producer of messages as well as a pxReceiver of type amqp which serves as a consumer of messages.
As a broker, we use rabbitmq-server which is a standard debian package of an AMQP broker.

A pxSender of type amqp, reads the content of a file in its queue, makes a message to which it attaches a "topic" and sends it to the broker.
A pxReceiver of type amqp will announce to the broker the "topic" for which it is interested to receive messages, and the broker will send it each message corresponding to its choice.

As a message can be anything, at the level of the pxSender, we have also attached the name of the file from which the message comes.
Thus in our pxReceiver, we can insure the content of the message in the corresponding file name.
This trick is useless only for amqp changes between a sender and an amqp receiver...

Notifications for DD 
--------------------

We found in AMQP an opportunity to announce products when they arrive on DD.
So a user instead of constantly verifying if a product is present on DD.
To change it, he could subscribe (AMQP topic) to receive a message (the url of the product) that would be omitted only at the delivery of the product on DD.
We wouldn't do this exercise for newsletters... but for other products (grib,images... etc)

To implement this, we used a possibility of pxSender, the sender_script.
We have written a script sftp_amqp.py that makes the deliveries to DD and for each product, it creates a file containing the URL under which the product will be present.
Here is the beginning of the configuration of wxo-b1-oper-dd.conf::

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

We see in this config that all the information for a single-file sender is there.
But because the type is script... and the send_script sftp_amqp.py is provided, we are able to instruct our sender to do more...

The file containing the URL is placed under the txq of an AMQP sender /apps/px/txq/dd-notify-wxo-b1 for the AMQP notification to be done.
To send the files in this queue, a sender has to have written dd-notify-wxo-b1.conf which is configured as follows::

    type amqp
    
    validation False
    noduplicates False
    
    protocol amqp
    host wxo-b1.cmc.ec.gc.ca
    user feeder
    password ********
    
    exchange_name cmc  
    exchange_key  exp.dd.notify.${0}
    exchange_type topic
    
    reject ^ensemble.naefs.grib2.raw.*
    
    accept ^(.*)\+\+.*


Again, the cl for the topic contains a programmed part.
The ${0} part contains the tree structure where the product is placed on dd... For example, here is a log line from dd-notify-wxo-b1.log::

    2013-06-06 14:47:11,368 [INFO] (86 Bytes) Message radar.24_HR_ACCUM.GIF.XSS++201306061440_XSS_24_HR_ACCUM_MM.gif:URP:XSS:RADAR:GIF::20130606144709  delivered (lat=1.368449,speed=168950.887119)

===================================  ========================================================================================
And so the cl would be.              ``exp.dd.notify.radar.24_HR_ACCUM.GIF.XSS``
And the location of the file         ``http://dd1.weather.gc.ca/radar/24_HR_ACCUM/GIF/XSS``
And the complete URL in the message  ``http://dd1.weather.gc.ca/radar/24_HR_ACCUM/GIF/XSS/201306061440_XSS_24_HR_ACCUM_MM.gif``
===================================  ========================================================================================


Utilities installed on DD servers
---------------------------------

When a client connects to the broker (rabbitmq-server) it must create a queue and attach it to an exchange.
We can give this queue the option that it self-destructs when it is no longer in use or that it is preserved and continues to stack products if the client is offline.
In general, we would like the queue to be preserved and thus the connection resumption restarts the product collection without loss.

queue_manager.py
    The rabbitmq-server will never destroy a queue that has been created by a client if it is not in auto-delete mode (let alone if it is created with durability).
    This can cause a problem for example, a client that develops a process, can change IDEs several times and crams on the server a multitude of queues that will never be used.
    So we created a queue_manager.py script that verifies if the unused queues have more than X products waiting or take more than Y Mbytes...
    If so, they are destroyed by the script.
    
    At the time of writing this document, the limits are : ``25000 messages and 50Mb.``


dd-xml-inotify.py
    On our public datamart, there are products that do not come directly from pds/px/pxatx.
    As our notifications are made from the product delivery, we don't have messages for them.
    This is the case for the XML products under the directories: ``citypage_weather`` and ``marine_weather``.
    To overcome this situation, the daemon dd-xml-inotify.py has been created and installed.
    This python script uses inotify to monitor the modification of products under their directories.
    If a product is modified or added, an amqp notification is sent to the server.
    Thus all products in the datamart are covered by the message sending.  


Using AMQP with URP, BUNNY, PDS-OP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. note:: also applies to dev...


From URP-1/2 announce to BUNNY-OP that a product is ready
----------------------------------------------------------

On urp-1/2 a metpx rolls the sender amqp_expose_db.conf which announces that a product has just arrived in the db of metpx with a message of the form::

    Md5sum of product name           file-size  url                        dbname
    a985c32cbdee8af2ab5d7b8f6022e781 498081     http://urp-1.cmc.ec.gc.ca/ db/20150120/RADAR/URP/IWA/201501201810~~PA,60,10,PA_PRECIPET,MM_HR,MM:URP:IWA:RADAR:META::20150120180902

These AMQP messages are sent to the rabbitmq server on bunny-op with an exchange key that starts with ``v00.urp.input`` followed by convention by the path from db with the '/' replaced with '.'.

.. note:: that urp-1/2 runs apache and that the product annonce is in the db of metpx and is visible from the URL of the message.

BUNNY-OP and dd_dispatcher.py
-----------------------------

bunny-op is a vip that lives on bunny1-op or bunny2-op.
It is with keepalived that we make sure that this vip resides on one of the bunny-op.
We also test that rabbitmq-server is running on the same server.
The configuration part of keepalived that deals with the vip is::

    vip bunny-op 142.135.12.59 port 5672

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
                    142.135.12.59 dev eth0
            }
            track_script {
                    chk_rabbitmq
            }
    }

The rabbitmq-servers on these machines are installed in a cluster.
We put high availability on the queues beginnig with ``cmc.*``.
On each of the machines run the utility ``dd_dispatcher.py``.
This program verifies whether the vip bunny-op and proc�dera has its work only on the server where the vip lives.
(If there is a switch, auto detection in 5 seconds and the queues remain unchanged)

The utility dd_dispatcher.py subscribes to the messages ``v00.urp.input.#`` and thus redirects the messages from the 2 URP operative servers.
Upon reception of a first product, the product's md5dum is placed in a cache and the message is r�exp�di� but this time with ``v00.urp.notify`` as the exchange key.
If another message arrives from ``v00.urp.input`` with the same md5sum as the first one, it is ignored, so the products announced from the exchange key ``v00.urp.notify`` are unique and represent the first arrival of the 2 operative URPs.
    
PDS-OP receptions of dispatch messages, wget of radar products
--------------------------------------------------------------

On pds-op, a pull_urp receiver, execute the fx_script pull_amqp_wget.py.
In this script, the following command::

    # shared queue : each pull receive 1 message (prefetch_count=1)
    self.channel.basic_qos(prefetch_size=0,prefetch_count=1,a_global=False)

makes that the distribution of messages ``v00.urp.notify`` will be distributed equally across the 5 servers under pds-op.
We therefore guarantee a distributed pull.
For each message of the form::

    a985c32cbdee8af2ab5d7b8f6022e781 498081 http://urp-1.cmc.ec.gc.ca/ db/20150120/RADAR/URP/IWA/201501201810~~PA,60,10,PA_PRECIPET,MM_HR,MM:URP:IWA:RADAR:META::20150120180902

the url is reb�ted from the last 2 fields of the message and a wget of the product is made and placed in the receiver queue which is then ignored/routed in an ordinary way.

Verification / Troubleshooting 
------------------------------

In order of production 

1. On ``urp-1/2``:
    - Verify that the radar products are generated on urp-1/2.
    - Verify that notifications are generated on urp-1/2 /apps/px/log/tx_amqp_expose_db.log
2. On ``bunny1/2-op``
    - Check where bunny-op resides
    - Verify the logs of dd_dispatcher.py ``/var/log/dd_dispatcher_xxxx.log`` where xxxx is the process pid
3. On ``pds-op``
    - Check the pull_urp   

Repairing the processes that are not working properly should fix the problems in general.
More details will be added here as problems are encountered and corrected. 
