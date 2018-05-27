=================
Downloading MetPX
=================

.. contents::

Getting The Source Code
-----------------------

Development is done on the *master* branch, and releases are done on a frequent
basis. The source code contains both *sundew* and *sarracenia* components,
although currently only *sarracenia* is under active development.

With those explanations, feel free to grab a snapshot can be obtained using
git via::

    git clone https://github.com/MetPX/sarracenia sarracenia


Available for anonymous read-only access. One can also obtain a stable release
by checking out a release branch::

  blacklab% git tag
    
  .
  .
  .
  v2.18.04b2
  v2.18.04b3
  v2.18.04b4
  v2.18.04b5
  v2.18.05b1
  v2.18.05b2
  v2.18.05b3
  v2.18.05b4

  blacklab% git checkout v2.18.05b4
  


Building From Source
--------------------

Sundew
~~~~~~

Please refer to `Sundew developer guide <DevGuide.rst>`_ for instructions on
how to build *Metpx-Sundew*. Currently internal installations are done, one at
a time, from source. Development is done on the trunk release. When we install
operationally, the process consists of creating a branch, and running the branch
on a staging system, and then implementing on operational systems. There are
README and INSTALL files that can be used for installation of sundew. One can
follow those instructions to get an initial installed system.

To run sundew, it is critical to install the cron cleanup jobs (mr-clean) since
otherwise the server will slow down continuously over time until it slows to a
crawl. It is recommended to subscribe to the mailing list and let us know what
is stopping you from trying it out, it could inspire us to work on that bit
faster to get some collaboration going.

Sarracenia
~~~~~~~~~~

Please refer to `Sarracenia developer guide <Dev.rst>`_ for instructions on building *Metpx-Sarracenia* from source.

Sundew Binaries
---------------

MetPx-Sundew is available for download from the `Sundew <https://github.com/MetPX/Sundew/>`_ of the project's SourceForge file storage, .

Sarracenia Binaries
-------------------

Please refer to `Sarracenia Installation Guide <Install.rst>`_ for instructions on how to download and install *Metpx-Sarracenia* binaries. 
