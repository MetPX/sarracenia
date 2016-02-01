=================
Downloading MetPX
=================

.. contents::

Getting The Source Code
-----------------------

Development is done on the *master* branch, and releases are done on a frequent basis. The source code contains both *sundew* and *sarracenia* components, although currently only *sarracenia* is under active development.


With those explanations, feel free to grab a snapshot can be obtained using subversion via::

    git clone git://git.code.sf.net/p/metpx/git metpx


Available for anonymous read-only access. One can also obtain a stable release by checking out a release branch.

Building From Source
--------------------

Sundew
~~~~~~

Please refer to `Sundew developer guide <DevGuide.html>`_ for instructions on how to build *Metpx-Sundew*. 
Currently internal installations are done, one at a time, from source.  
Development is done on the trunk release.  When we install operationally, the process consists
of creating a branch, and running the branch on a staging system, and then implementing
on operational systems.  There are README and INSTALL files that can be used for 
installation of sundew.  One can follow those instructions to get an initial installed 
system.  

To run sundew, it is critical to install the cron cleanup jobs (mr-clean) since otherwise the 
server will slow down continuously over time until it slows to a crawl.  
It is recommended to subscribe to the mailing list and let us know what is stopping you from 
trying it out, it could inspire us to work on that bit faster to get some collaboration 
going.

Sarracenia
~~~~~~~~~~

Please refer to `Sarracenia developer guide <Dev.html>`_ for instructions on building *Metpx-Sarracenia* from source.

Sundew Binaries
---------------

MetPx-Sundew is only available for download from the `sundew section  <https://sourceforge.net/projects/metpx/files/sundew/>`_ of the project's SourceForge file storage, . 

Sarracenia Binaries
-------------------

MetPX-Sarracenia is available for download from various channels. Each has its own benefits.

PyPi
~~~~

Releases are uploaded to `PyPi <https://pypi.python.org/pypi/MetPX-sarracenia>`_ regularly. This is the recommended method if you
run a Linux distribution **older than** Ubuntu 14.04 (trusty), or you are not on Linux. In order to install from PyPi run::

  pip3 install metpx-sarracenia

Launchpad
~~~~~~~~~

Releases are built into *debian* packages for **Ubuntu 14.04 (trusty)** and **Ubuntu 16.04**. To use this method, add the project's `Launchpad repository <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx>`_ to your *sources.list* file. The fastest and easiest way is::

  sudo add-apt-repository ppa:ssc-hpc-chp-spc/metpx
  sudo apt-get update
  sudo apt-get install python3-metpx-sarracenia

SourceForge
~~~~~~~~~~~

The *.deb* binaries (build for Ubuntu 14.04) and source *tarballs* are also made available in the `sarracenia section <https://sourceforge.net/projects/metpx/files/sarracenia/>`_ of the project's SourceForge file storage. 
