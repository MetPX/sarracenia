
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
  easy-install3 pip
  pip3 install metpx_sarracenia
  pip3 install paramiko

On Ubuntu 14.04/16.04::

  sudo add-apt-repository ppa:ssc-hpc-chp-spc/metpx
  sudo apt-get update
  sudo apt-get install python3-metpx-sarracenia  # only supports HTTP/HTTPS
  sudo apt-get install python3-paramiko   # adds SFTP support.

.. note::
   FIXME: confirm that python3-paramiko is in our repo for 14.04?



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

