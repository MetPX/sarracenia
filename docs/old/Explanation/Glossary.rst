Glossary
========

Sarracenia documentation uses a number of words in a particular way.
This glossary should make it easier to understand the rest of the documentation.


Source
  Someone who wants to ship data to someone else. They do that by advertising a 
  trees of files that are copied from the starting point to one or more pumps
  in the network. The advertisement sources produced tell others exactly where 
  and how to download the files, and Sources have to say where they want the 
  data to go to.

  Sources use programs like `sr_post.1 <../Reference/sr3.1.rst#post>`_, 
  `sr_watch.1 <../Reference/sr3.1.rst#watch>`_, and `sr_poll(1) <../Reference/sr3.1.rst#poll>`_ to create 
  their advertisements.


Subscribers
  are those who examine advertisements about files that are available, and 
  download the files they are interested in.

  Subscribers use `sr_subscribe(1) <../Reference/sr3.1.rst#subscribe>`_


Post, Notice, Notification, Advertisement, Announcement
  These are AMQP messages build by sr_post, sr_poll, or sr_watch to let users
  know that a particular file is ready. The format of these AMQP messages is 
  described by the `sr_post(7) <../Reference/sr_post.7.rst>`_ manual page. All of these 
  words are used interchangeably. Advertisements at each step preserve the
  original source of the posting, so that report messages can be routed back 
  to the source.


Report messages
  These are AMQP messages (in `sr_post(7) <../Reference/sr_post.7.rst>`_ format, with _report_ 
  field included) built by consumers of messages, to indicate what a given pump 
  or subscriber decided to do with a message. They conceptually flow in the 
  opposite direction of notifications in a network, to get back to the source.


Pump or broker
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
  There are some pumps that have no transport engine, they just mediate 
  transfers for other servers, by making messages available to clients and
  servers in their network area.


Dataless Transfers
  Sometimes transfers through pumps are done without using local space on the pump.


Pumping Network
  A number of interconnects servers running the sarracenia stack. Each stack 
  determines how it routes items to the next hop, so the entire size or extent
  of the network may not be known to those who put data into it.


Network Maps
  Each pump should provide a network map to advise users of the known destination
  that they should advertise to send to. *FIXME* undefined so far.
