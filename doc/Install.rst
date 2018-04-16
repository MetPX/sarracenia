
==============================
 MetPX-Sarracenia Installation
==============================


Revision Record
---------------

:version: @Version@
:date: @Date@



Client Installation
-------------------

The package is built for python version 3.4 or higher. On systems where
they are available, debian packages are recommended. These can be obtained from the 
launchpad repository. If you cannot use debian packages, then consider pip packages 
avialable from PyPI. In both cases, the other python packages (or dependencies) needed
will be installed by the package manager automatically.


Ubuntu/Debian (apt/dpkg)
~~~~~~~~~~~~~~~~~~~~~~~~

On Ubuntu 14.04/16.04/17.10/18.04 and derivatives of same::

  sudo add-apt-repository ppa:ssc-hpc-chp-spc/metpx
  sudo apt-get update
  sudo apt-get install python3-metpx-sarracenia  # only supports HTTP/HTTPS
  sudo apt-get install python3-paramiko   # adds SFTP support.
  sudo apt-get install sarrac # C-version.


On Ubuntu 12.04::

  apt-get install python3-dev
  apt-get install python3-setuptools
  easy_install3 pip==1.5.6
  pip3 install paramiko==1.16.0
  pip3 install metpx_sarracenia==<latest version>

.. note::
   **Why the specific versions on older distributions?**

   pip > 1.5.6 does not support python < 3.2 which is the python in Ubuntu 12.04.

   Later versions of paramiko require the cryptography module, which
   doesn't build on python-3.2, so need to use an older version of paramiko
   which uses pyCrypto, and that does build on 3.2.



PIP
~~~

On windows, or other linux distributions where system packages are not available, the
above procedures are not applicable.  There are also special cases, such as if using
python in virtual env, where it is more practical to install the package using
pip (python install package) from `<http://pypi.python.org/>`_.  It is straightforward
to do that::

  sudo pip install metpx-sarracenia

and to upgrade after the initial installation::

  sudo pip uninstall metpx-sarracenia
  sudo pip install metpx-sarracenia


NOTE:: 

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
all dependencies for Sarracenia. You can obtain winpython from `<http://winpython.github.io/>`_ 
(note: select python version >3 ) Then one can install with pip (as above.)

Packages
~~~~~~~~

Debian packages and python wheels can be downloaded directly 
from: `launchpad <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx/+packages>`_
or (perhaps): `Sourceforge <https://sourceforge.net/projects/metpx/files/sarracenia/>`_

Sarrac
------

The C client is available in prebuilt binaries in the launchpad repositories alongside the python packages.
The librabbitmq-0.8.0 has been backported to ubuntu 16.04 and 14.04 to satisfy sarrac's dependency.
For other architectures or distributions, git clone https://github.com/MetPX/sarrac and compile 
on any linux system, as long as librabbitmq dependency is satisfied.


