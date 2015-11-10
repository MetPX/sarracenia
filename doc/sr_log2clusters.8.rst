
================
 SR_Log2clusters
================

--------------------------------------
Return Log of the Products to Clusters
--------------------------------------

:Manual section: 1 
:Date: Oct 2015
:Version: 0.0.1
:Manual group: MetPx Sarracenia Suite


SYNOPSIS
========

**sr_log2clusters** -b <broker> start|stop|restart|reload|status

DESCRIPTION
===========

**sr_log2clusters** is a program that reads the file `log_routing(7) <log_routing.7.html>`_.
An instance of **sr_log2clusters** is started for each line of the config file
that defines a cluster name log targer : 'cluster_Name broker_Url exchange_Log'.

Each **sr_log2clusters** instance connects to the <broker> from the command line
and the **broker_Url** from the **log_routing.conf** entry.
From the <broker> it subscribes to all log notifications. 
When the notification **headers['from_cluster']** matches the **cluster_Name**,
**sr_log2clusters** publish it back to the **broker_Url** under exchange **exchange_Log**.
all other notifications are ignored.


The **sr_log2clusters** command can takes 2 arguments: a broker,
followed by an action start|stop|restart|reload|status... (self described).

CONFIGURATION
=============

Options are placed in the command line in the form: 

**-option <value>** 

BROKER
------

First, the program needs to set the rabbitmq configurations of a source broker.
The broker option sets all the credential information to connect to the **AMQP** server 

**--broker|-b amqp{s}://<user>:<pw>@<brokerhost>[:port]/<vhost>**

::

      (default: amqp://guest:guest@localhost/ ) 


Once connected to an AMQP broker, **sr_log2clusters** use exchange xlog, and topic v02.log.#
to get all logs messages. 



SEE ALSO
========

:: FIXME

