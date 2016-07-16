
===================
 report2clusters.conf
===================

-------------------------------------
Return Log of the Products to Brokers
-------------------------------------

:Manual section: 7 
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite


PLACEMENT
=========

**~/.config/sarra/report2clusters.conf**

DESCRIPTION
===========

The file ~/.config/sarra/report2clusters.conf defines where the logs, 
for a given cluster, must be sent to. The file has the following syntax :

cluster_Name broker_Url exchange_Log


CLUSTER_NAME
------------

First, the cluster_Name is a string interpreted as a cluster name.
When an **AMQP** message is processed by  `sr_sarra(1) <sr_sarra.1.html>`_
its headers is extended with the pair  headers['from_cluster'] = cluster_Name.
The value of 'from_cluster' can be set with option  **from_cluster cluster_Name**
in **sr_sarra**'s config file, or for the whole server if set in
~/.config/sarra/default.conf.


BROKER_URL
----------

The broker_url sets the rabbitmq configurations of the broker that should receives
the log messages for each message that contains the **headers['from_cluster'] = cluster_Name**.
The broker_url field sets all the credential information to connect to the **AMQP** server 

**--broker|-b amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**


EXCHANGE_LOG
------------

The **exchange_Log** field sets under which exchange on the specified **broker_Url**
all logs messages related to **cluster_Name** will be delivered.


.. NOTE:: 
  FIXME: give an example 




SEE ALSO
========

`sr_report2clusters(8) <sr_report2clusters.8.html>`_ - routing logs back to some clusters.

