========================
Sarracenia Documentation
========================

.. danger::
  This package is not ready for use yet.  It is undergoing internal testing, and the 
  documentation is incomplete.  This note will be removed once the package documentation 
  is complete and usable.

Documentation comes in two varieties: Guides and Manual Pages.  The Guides provide give the 
overall idea of how to use the tools, with description of several components, use cases, and 
some sample configurations and runs.  The guides provide "Getting started" type information, 
describing the purpose, in general, of the various components needed for various jobs.

The Manual Pages, on the other hand, are reference material.  For each component or format, 
the manual page provides a complete reference that shows all the options that exist for that 
component, and also provides examples of usage. To learn the application, it is best to 
start with Guides. The Guides are also best read in order, as knowledge of each guide assumes 
one is familiar with the previous ones.

Once an initial configuration is established and the overall picture is understood, then the 
reference materials provides quick answers to specific questions.

.. contents::

Guides
------

* `Installation <Install.html>`_ - initial installation, and a Glossary.
* `Subscriber Guide <subscriber.html>`_ - effective downloading from a pump.
* `Source Guide <source.html>`_ - effective uploading to a pump
* `Admin Guide <Admin.html>`_ - Configuration of Pumps
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


Administrative Daemons
-----------------------

* `sr_audit(8) <sr_audit.8.html>`_ - Audit the running configuration, looking for issues.
* `sr_sarra(8) <sr_sarra.8.html>`_ - Subscribe, Acquire And Re-Advertise...  the main pump.
* `sr_report2clusters(8) <sr_report2clusters.8.html>`_ - daemon to copy report messages to other clusters.
* `sr_report2source(8) <sr_report2source.8.html>`_ - daemon to copy report messages to the originating source.
* `sr_winnow(8) <sr_winnow.8.html>`_ - to remove duplicate posts.
* `sr_shovel(8) <sr_shovel.8.html>`_ - copies messages between pumps.


Formats/Protocols
------------------

* `sr_post(7) <sr_post.7.html>`_ - the format of postings. Posted by watch and post, consumed by subscribe.
* `sr_report(7) <sr_report.7.html>`_ - the format of report messages. Sent by consumers, for sources to measure reach.
* `report2clusters(7) <report2clusters.7.html>`_ - configuration of report routing between clusters.
* `sr_config(7) <sr_config.7.html>`_ - reference for options used by many components.
