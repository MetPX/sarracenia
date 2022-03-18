Glossary
========

Sarracenia documentation uses a number of words in a particular way.
This glossary should make it easier to understand the rest of the documentation.

AMQP
----

AMQP is the Advanced Message Queuing Protocol, which emerged from the financial trading industry and has gradually
matured. Implementations first appeared in 2007, and there are now several open source ones. AMQP implementations
are not JMS plumbing. JMS standardizes the API programmers use, but not the on-the-wire protocol. So
typically, one cannot exchange messages between people using different JMS providers. AMQP standardizes
for interoperability, and functions effectively as an interoperability shim for JMS, without being
limited to Java. AMQP is language neutral, and message neutral. There are many deployments using
Python, C++, and Ruby. One could adapt WMO-GTS protocols very easily to function over AMQP. JMS
providers are very Java oriented.


* `www.amqp.org <http://www.amqp.org>`_ - Defining AMQP.
* `www.openamq.org <http://www.openamq.org>`_ - Original GPL implementation from JPMorganChase
* `www.rabbitmq.com <http://www.rabbitmq.com>`_ - Another free implementation. The one we use and are happy with.
* `Apache Qpid <http://cwiki.apache.org/qpid>`_ - Yet another free implementation.
* `Apache ActiveMQ <http://activemq.apache.org/>`_ - This is really a JMS provider with a bridge for AMQP. They prefer their own openwire protocol.

Sarracenia relies heavily on the use of brokers and topic based exchanges, which were prominent in AMQP standards efforts prior
to version 1.0, at which point they were removed. It is hoped that these concepts will be re-introduced at some point. Until
that time, the application will rely on pre-1.0 standard message brokers, such as rabbitmq.

MQTT
----

The Message Queue Telemetry Transport (MQTT) version 5 is a second Message Queueing protocol with all the features
necessary to support sarracenia's data exchange patterns.

* `mqtt.org <https://mqtt.org>`_
* `mosquitto.org <https://mosquitto.org>`_
* `EMQX.io <emqx.io>`_

Source
------

Someone who wants to ship data to someone else. They do that by advertising a 
trees of files that are copied from the starting point to one or more pumps
in the network. The advertisement sources produced tell others exactly where 
and how to download the files, and Sources have to say where they want the 
  data to go to.

Sources use the `post <../Reference/sr3.1.html#post>`_,
`sr_watch.1 <../Reference/sr3.1.html#watch>`_, and 
`sr_poll(1) <../Reference/sr3.1.html#poll>`_ components to create 
their advertisements.


Subscribers
-----------
are those who examine advertisements about files that are available, and 
download the files they are interested in.

Subscribers use `subscribe(1) <../Reference/sr3.1.html#subscribe>`_


Post, Notice, Notification, Advertisement, Announcement
-------------------------------------------------------

These are AMQP messages build by sr_post, sr_poll, or sr_watch to let users
know that a particular file is ready. The format of these AMQP messages is 
described by the `sr_post(7) <../Reference/sr_post.7.html>`_ manual page. All of these 
words are used interchangeably. Advertisements at each step preserve the
original source of the posting, so that report messages can be routed back 
to the source.


Report messages
---------------

These are AMQP messages (in `sr_post(7) <../Reference/sr_post.7.html>`_ format, with _report_ 
field included) built by consumers of messages, to indicate what a given pump 
or subscriber decided to do with a message. They conceptually flow in the 
opposite direction of notifications in a network, to get back to the source.


Pump or broker
--------------

A pump is a host running Sarracenia, either a rabbitmq AMQP server or an MQTTT
one such as mosquitto. The message queueing middleware is called a *broker.*
The pump has administrative users and manage the MQP broker
as a dedicated resource. Some sort of transport engine, like an apache 
server, or an openssh server, is used to support file transfers. SFTP, and 
HTTP/HTTPS are the protocols which are fully supported by sarracenia. Pumps
copy files from somewhere, and write them locally. They then re-advertise the
local copy to its neighbouring pumps, and end user subscribers, they can 
obtain the data from this pump.

.. Note::
  For end users, a pump and a broker is the same thing for all practical 
  purposes. When pump administrators configure multi-host clusters, however, a 
  broker might be running on two hosts, and the same broker could be used by 
  many transport engines. The entire cluster would be considered a pump. So the
  two words are not always the same.


Dataless Pumps
--------------

There are some pumps that have no transport engine, they just mediate 
transfers for other servers, by making messages available to clients and
servers in their network area.


Dataless Transfers
------------------

Sometimes transfers through pumps are done without using local space on the pump.


Pumping Network
---------------

A number of interconnects servers running the sarracenia stack. Each stack 
determines how it routes items to the next hop, so the entire size or extent
of the network may not be known to those who put data into it.


Network Maps
------------

Each pump should provide a network map to advise users of the known destination
that they should advertise to send to. *FIXME* undefined so far.


WMO
---

The World Meteorological Organization, is a part of the United Nations that has the weather and environmental
monitoring, prediction, and alerting services of each country as members. For many decades, there has
been a real-time exchange of weather data between countries, often even in times of war.  The standards
that cover these exchanges are:

- Manual on the Global Telecommunications´ System: WMO Manual 386. The standard reference for this 
  domain. (a likely stale copy is  `here <WMO-386.pdf>`_.) Try https://www.wmo.int for the latest version.

Usually these links are referred to collectively as *the GTS*.  The standards are very old, and a modernization
process has been ongoing for the last decade or two. Some current work on replacing the GTS is here:

- `WMO Task Team on message queueing protocols <https://github.com/wmo-im/GTStoWIS2>`_

The discussions around this topic are important drivers for Sarracenia.

