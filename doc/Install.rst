
==============================
 MetPX-Sarracenia Installation
==============================

.. Contents::


Revision Record
---------------

Pre-Draft.  This document is still being built and should not be reviewed or relied upon.

:version: @Version@ 
:date: @Date@



Installation 
------------

On systems where they are available, debian packages are recommended.
from the launchpad repository, or using pip (and PYpi), in 
which case the other python packages needed will be installed
by the package manager.  


Ubuntu/Debian (apt/dpkg)
~~~~~~~~~~~~~~~~~~~~~~~~

Ubuntu 12.04 and 14.04::

  sudo add-apt-repository ppa:ssc-hpc-chp-spc/metpx
  sudo apt-get update
  sudo apt-get install python3-metpx-sarracenia

Ubuntu 16.04 is not yet supported:

.. note: 
   FIXME: 16.04 (xenial) is trivial to add, all deps are already in repos...


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

