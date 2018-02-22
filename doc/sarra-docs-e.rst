========================
Sarracenia Documentation
========================

Documentation comes in two varieties: Guides and Manual Pages. The guides provide the
overall idea of how to use the tools, with description of several components, use cases, and
some sample configurations and runs. The guides provide "Getting started" type information,
describing the purpose, in general, of the various components needed for various jobs.

The Manual Pages, on the other hand, are reference material. For each component or format,
the manual page provides a complete reference that shows all the options that exist for that
component, and also provides examples of usage. To learn the application, it is best to
start with Guides. The Guides are also best read in order, as knowledge of each guide assumes
one is familiar with the previous ones.

Once an initial configuration is established and the overall picture is understood, then the
reference materials provides quick answers to specific questions.

.. contents::

Guides
------

* `Installation <Install.html>`_ - initial installation.
* `Subscriber Guide <subscriber.html>`_ - effective downloading from a pump.
* `Source Guide <source.html>`_ - effective uploading to a pump
* `Admin Guide <Admin.html>`_ - Configuration of Pumps
* `Upgrade Guide <Admin.html>`_ - MUST READ when upgrading pumps.
* `Programming Guide <Prog.html>`_ - Programming custom plugins for workflow integration.
* `Developer Guide <Dev.html>`_ - contributing to sarracenia development.


User-Facing Components
----------------------

* `sr_post(1) <sr_post.1.html>`_ - to post individual files.
* `sr_poll(1) <sr_poll.1.html>`_ - to list files to pull from remote servers.
* `sr_subscribe(1) <sr_subscribe.1.html>`_ - the http/https subscription client.
* `sr_report(1) <sr_report.1.html>`_ - to read report messages.
* `sr_watch(1) <sr_watch.1.html>`_ - to post all changes to a given directory.
* `sr_sender(1) <sr_sender.1.html>`_ - to send files from a pump.


Administrative Components
-------------------------

* `sr_audit(8) <sr_audit.8.html>`_ - Audit the running configuration, looking for issues.
* `sr_log2save(8) <sr_log2save.8.html>`_ - Extract log messages to create a save format file.
* `sr_sarra(8) <sr_sarra.8.html>`_ - Subscribe, Acquire And Re-Advertise... the main pump.
* `sr_shovel(8) <sr_shovel.8.html>`_ - copies messages between pumps.
* `sr_winnow(8) <sr_winnow.8.html>`_ - to remove duplicate posts.


Formats/Protocols
------------------

* `sr_post(7) <sr_post.7.html>`_ - the format of postings. Posted by watch and post, consumed by subscribe.
* `sr_report(7) <sr_report.7.html>`_ - the format of report messages. Sent by consumers, for sources to measure reach.
* `sr_pulse(7) <sr_pulse.7.html>`_ - the format of postings. posted by pumps to maintain subscriber connections.


Glossary
--------

Sarracenia documentation uses a number of words in a particular way.
This glossary should make it easier to understand the rest of the documentation.

Source
  Someone who wants to ship data to someone else. They do that by advertise a trees of files that are copied from
  the starting point to one or more pumps in the network. The advertisement sources produce tell others exactly
  where and how to download the files, and Sources have to say where they want the data to go to.

  Sources use programs like `sr_post.1 <sr_post.1.html>`_, `sr_watch.1 <sr_watch.1.html>`_, and `sr_poll(1) <sr_poll.1.html>`_
  to create their advertisements.

Subscribers
  are those who examine advertisements about files that are available, and download the files
  they are interested in.

  Subscribers use `sr_subscribe(1) <sr_subscribe.1.html>`_

Post, Notice, Notification, Advertisement, Announcement
  These are AMQP messages build by sr_post, sr_poll, or sr_watch to let users know that a particular
  file is ready. The format of these AMQP messages is described by the `sr_post(7) <sr_post.7.html>`_
  manual page. All of these words are used interchangeably. Advertisements at each step preserve the
  original source of the posting, so that report messages can be routed back to the source.

Report messages
  These are AMQP messages (in `sr_report(7) <sr_report.7.html>`_ format) built by consumers of messages, to indicate
  what a given pump or subscriber decided to do with a message. They conceptually flow in the opposite
  direction of notifications in a network, to get back to the source.

Pump or broker
  A pump is a host running Sarracenia, a rabbitmq AMQP server (called a *broker* in AMQP parlance)
  The pump has administrative users and manage the AMQP broker as a dedicated resource.
  Some sort of transport engine, like an apache server, or an openssh server, is used to support file transfers.
  SFTP, and HTTP/HTTPS are the protocols which are fully supported by sarracenia. Pumps copy files from
  somewhere, and write them locally. They then re-advertised the local copy to it's neighbouring pumps, and end user
  subscribers, they can obtain the data from this pump.

.. Note::
  For end users, a pump and a broker is the same thing for all practical purposes. When pump administrators
  configure multi-host clusters, however, a broker might be running on two hosts, and the same broker could
  be used by many transport engines. The entire cluster would be considered a pump. So the two words are not
  always the same.

Dataless Pumps
  There are some pumps that have no transport engine, they just mediate transfers for other servers, by
  making messages available to clients and servers in their network area.

Dataless Transfers
  Sometimes transfers through pumps are done without using local space on the pump.

Pumping Network
  A number of interconnects servers running the sarracenia stack. Each stack determines how it routes stuff
  to the next hop, so the entire size or extent of the network may not be known to those who put data into it.

Network Maps
  Each pump should provide a network map to advise users of the known destination that they should
  advertise to send to.
