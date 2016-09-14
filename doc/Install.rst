
==============================
 MetPX-Sarracenia Installation
==============================


Revision Record
---------------

.. warning::
    **Pre-Draft.**  This document is still being built and should not be reviewed or relied upon.

:version: @Version@
:date: @Date@



Client Installation
-------------------

The package is built for python version 3.4 or higher.  On systems where
they are available, debian packages are recommended.
These can be obtained from the launchpad repository, or using pip
(and PyPI.) In both cases, the other python packages (or dependencies) needed
will be installed by the package manager automatically.


Ubuntu/Debian (apt/dpkg)
~~~~~~~~~~~~~~~~~~~~~~~~

On Ubuntu 12.04::

  apt-get install python3-dev
  apt-get install python3-setuptools
  easy_install3 pip==1.5.6
  pip3 install paramiko==1.16.0
  pip3 install metpx_sarracenia==<latest version>

.. note::
   **Why the specific versions?**

   pip > 1.5.6 does not support python < 3.2 which is the python in Ubuntu 12.04.

   Later versions of paramiko require the cryptography module, which
   doesn't build on python-3.2, so need to use an older version of paramiko
   which uses pyCrypto, and that does build on 3.2.


On Ubuntu 14.04/16.04::

  sudo add-apt-repository ppa:ssc-hpc-chp-spc/metpx
  sudo apt-get update
  sudo apt-get install python3-metpx-sarracenia  # only supports HTTP/HTTPS
  sudo apt-get install python3-paramiko   # adds SFTP support.



PIP
~~~

On windows, or other linux distributions where system packages are not available, the
above procedures are not applicable.  There are also special cases, such as if using
python in virtual env, where it is more practical to install the package using
pip (python install package) from http://pypi.python.org/_.  It is straightforward
to do that::

  sudo pip install metpx-sarracenia

and to upgrade after the initial installation::

  sudo pip install --upgrade metpx-sarracenia

On many systems where both pythons 2 and 3 are installed, you may need to specify
pip3 rather than pip.


Windows
~~~~~~~

Any native python installation will do, but the dependencies in the standard python.org
installation require the installation of a C-Compiler as well, so it gets a bit complicated.
If you have an existing python installation that works with c-modules within it, then the
complete package should install with all features.

If you do not have a python environment handy, then the easiest one to get going with
is winpython, which includes many scientifically relevant modules, and will easily install
all dependencies for Sarracenia. You can obtain winpython from http://winpython.github.io/_
(note: select python version >3 ) Then one can install with pip (as above.)


Glossary
--------

Sarracenia documentation uses a number of words in a particular way.
This glossary should make it easier to understand the rest of the documentation.

Source
  Someone who wants to ship data to someone else.  They do that by advertise a trees of files that are copied from
  the starting point to one or more pumps in the network.  The advertisement sources produce tell others exactly
  where and how to download the files, and Sources have to say where they want the data to go to.

  Sources use programs like `sr_post.1 <sr_post.1.html>`_, `sr_watch.1 <sr_watch.1.html>`_, and `sr_poll(1) <sr_poll.1.html>`_
  to create their advertisements.

Subscribers
  are those who examine advertisements about files that are available, and download the files
  they are interested in.

  Subscribers use `sr_subscribe(1) <sr_subscribe.1.html>`_

Post, Notice, Notification, Advertisement, Announcement
  These are AMQP messages build by sr_post, sr_poll, or sr_watch to let users know that a particular
  file is ready.   The format of these AMQP messages is described by the `sr_post(7) <sr_post.7.html>`_
  manual page.  All of these words are used interchangeably.  Advertisements at each step preserve the
  original source of the posting, so that report messages can be routed back to the source.

Report messages
  These are AMQP messages (in `sr_report(7) <sr_report.7.html>`_ format) built by consumers of messages, to indicate
  what a given pump or subscriber decided to do with a message.   They conceptually flow in the opposite
  direction of notifications in a network, to get back to the source.

Pump or broker
  A pump is a host running Sarracenia, a rabbitmq AMQP server (called a *broker* in AMQP parlance)
  The pump has administrative users and manage the AMQP broker as a dedicated resource.
  Some sort of transport engine, like an apache server, or an openssh server, is used to support file transfers.
  SFTP, and HTTP/HTTPS are the protocols which are fully supported by sarracenia.  Pumps copy files from
  somewhere, and write them locally.  They then re-advertised the local copy to it's neighbouring pumps, and end user
  subscribers, they can obtain the data from this pump.

.. Note::
  For end users, a pump and a broker is the same thing for all practical purposes.  When pump administrators
  configure multi-host clusters, however, a broker might be running on two hosts, and the same broker could
  be used by many transport engines. The entire cluster would be considered a pump. So the two words are not
  always the same.

Dataless Pumps
  There are some pumps that have no transport engine, they just mediate transfers for other servers, by
  making messages available to clients and servers in their network area.

Dataless Transfers
  Sometimes transfers through pumps are done without using local space on the pump.

Pumping Network
  A number of interconnects servers running the sarracenia stack.  Each stack determines how it routes stuff
  to the next hop, so the entire size or extent of the network may not be known to those who put data into it.

Network Maps
  Each pump should provide a network map to advise users of the known destination that they should
  advertise to send to.
