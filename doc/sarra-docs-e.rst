==========================
 Sarracenia Documentation
==========================

Documentation comes in two varieties: Guides and Manual Pages. 


To learn the application, it is best to
start with Guides. The Guides are also best read in order, as knowledge of each guide assumes
one is familiar with the previous ones.

Once an initial configuration is established and the overall picture is understood, then the
reference materials provides quick answers to specific questions.

.. contents::

About
-----

* `Introduction <sarra-e.rst>`_ - Motivation, use cases, status.


Guides
------

The guides provide the
overall idea of how to use the tools, with description of several components, use cases, and
some sample configurations and runs. The guides provide "Getting started" type information,
describing the purpose, in general, of the various components needed for various jobs.

* `Installation <Install.rst>`_ - initial installation.
* `Subscriber Guide <subscriber.rst>`_ - effective downloading from a pump.
* `Source Guide <source.rst>`_ - effective uploading to a pump
* `Concepts <Concepts.rst>`_ - Abstract Concepts, Conventions, Design.
* `Admin Guide <Admin.rst>`_ - Configuration of Pumps
* `Upgrade Guide <UPGRADING.rst>`_ - MUST READ when upgrading pumps.
* `Programming Guide <Prog.rst>`_ - Programming custom plugins for workflow integration.
* `Developer Guide <Dev.rst>`_ - contributing to sarracenia development.


User-Facing Components
----------------------

The Manual Pages, on the other hand, are reference material. For each component or format,
the manual page provides a complete reference that shows all the options that exist for that
component, and also provides examples of usage. 

* `sr_post(1) <sr_post.1.rst>`_ - to post individual files.
* `sr_poll(1) <sr_poll.1.rst>`_ - to list files to pull from remote servers.
* `sr_subscribe(1) <sr_subscribe.1.rst>`_ - the http/https subscription client.
* `sr_report(1) <sr_report.1.rst>`_ - to read report messages.
* `sr_watch(1) <sr_watch.1.rst>`_ - to post all changes to a given directory.
* `sr_sender(1) <sr_sender.1.rst>`_ - to send files from a pump.


Administrative Components
-------------------------

* `sr_audit(8) <sr_audit.8.rst>`_ - Audit the running configuration, looking for issues.
* `sr_log2save(8) <sr_log2save.8.rst>`_ - Extract log messages to create a save format file.
* `sr_sarra(8) <sr_sarra.8.rst>`_ - Subscribe, Acquire And Re-Advertise... the main pump.
* `sr_shovel(8) <sr_shovel.8.rst>`_ - copies messages between pumps.
* `sr_winnow(8) <sr_winnow.8.rst>`_ - to remove duplicate posts.


Formats/Protocols
------------------

* `sr_post(7) <sr_post.7.rst>`_ - the format of postings. Posted by watch and post, consumed by subscribe.
* `sr_report(7) <sr_report.7.rst>`_ - the format of report messages. Sent by consumers, for sources to measure reach.
* `sr_pulse(7) <sr_pulse.7.rst>`_ - the format of postings. posted by pumps to maintain subscriber connections.

