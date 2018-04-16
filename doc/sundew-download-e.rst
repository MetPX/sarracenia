=================
Downloading MetPX
=================

.. contents::

Getting The Source Code
-----------------------

Development is done on the *master* branch, and releases are done on a frequent basis.
Feel free to grab a snapshot using git via::

    git clone git://git.code.sf.net/p/metpx/sundew metpx-sundew


Available for anonymous read-only access. One can also obtain a stable release by checking out a release branch.

Building From Source
--------------------


Please refer to `Sundew developer guide <DevGuide.rst>`_ for instructions on how to build *Metpx-Sundew*.
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


Sundew Binaries
---------------

MetPx-Sundew is available for download from our `Launchpad PPA <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx>`_.
Please follow the instructions on in our PPA site on how to add the PPA to your
Ubuntu system and install the latest vesrion of MetPx-Sundew::

   sudo add-apt-repository ppa:ssc-hpc-chp-spc/metpx
   sudo apt-get update
   sudo apt-get install python3-metpx-sundew 


MetPx-Sundew is also available for download from the `sundew section  <https://sourceforge.net/projects/metpx/files/sundew/>`_ of the project's SourceForge file storage, .
