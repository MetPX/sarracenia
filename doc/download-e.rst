=================
Downloading MetPX
=================

.. contents::

Sundew
------

Currently MetPx-Sundew is only available for download from the `sundew section  <https://sourceforge.net/projects/metpx/files/sundew/>`_ of the project's SourceForge file storage, . 

Sarracenia
----------

MetPX-Sarracenia is available for download from various channels. Each has its own benefits.

PyPi
~~~~

Releases are uploaded to `PyPi <https://pypi.python.org/pypi/MetPX-sarracenia>`_ regularly. This is the recommended method if you
run a Linux distribution **older than** Ubuntu 14.04 (trusty), or you are not on Linux. In order to install from PyPi run::

  pip3 install metpx-sarracenia

Launchpad
~~~~~~~~~

Releases are built into *debian* packages for **Ubuntu 14.04 (trusty)** and will probably also work on Ubuntu 16.04 (not tested). To use this method, add the project's `Launchpad repository <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx>`_ to your *sources.list* file. The fastest and easiest way is::

  sudo add-apt-repository ppa:ssc-hpc-chp-spc/metpx
  sudo apt-get update
  sudo apt-get install python3-metpx-saracenia

SourceForge
~~~~~~~~~~~

The *.deb* binaries (build for Ubuntu 14.04) and source *tarballs* are also made available in the `sarracenia section <https://sourceforge.net/projects/metpx/files/sarracenia/>`_ of the project's SourceForge file storage. 
