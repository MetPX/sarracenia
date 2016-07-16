
================
 SR_Log2clusters
================

--------------------------------------
Return Log of the Products to Clusters
--------------------------------------

:Manual section: 1 
:Date: @Date@
:Version: @Version@
:Manual group: MetPx Sarracenia Suite


SYNOPSIS
========

**sr_report2clusters** -b <broker> start|stop|restart|reload|status

DESCRIPTION
===========

.. note:: 
   FIXME: think the config file scheme has changed is this right? PS.
   FIXME: log_routing.conf entry? what's that? no documentation.
   accepts broker as argument... hmm..
   P.S. not sure I understand any of this...

**sr_report2clusters** is a program that reads the file `report2clusters(7) <report2clusters.7.html>`_.
An instance of **sr_report2clusters** is started for each line of the config file
that defines a cluster name log target : 'cluster_Name broker_Url exchange_Log'.

Each **sr_report2clusters** instance connects to the <broker> from the command line
and the **broker_Url** from the **log_routing.conf** entry.
From the <broker> it subscribes to all log messages. 
When the notification **headers['from_cluster']** matches the **cluster_Name**,
**sr_report2clusters** publish it back to the **broker_Url** under exchange **exchange_Log**.
all other notifications are ignored.


The **sr_report2clusters** command can takes 2 arguments: a broker,
followed by an action start|stop|restart|reload|status... (self explanatory).


SEE ALSO
========

`sr_config(7) <sr_config.7.html>`_ - the format of configurations for MetPX-Sarracenia.


:: FIXME add full SEE ALSO links.

