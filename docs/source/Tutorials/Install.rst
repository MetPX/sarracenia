
==============================
 MetPX-Sarracenia Installation
==============================


Revision Record
---------------

:version: |release|
:date: |today|

Do you already have it?
-----------------------

If sarracenia is already installed you may invoke it like with::

    fractal% sr3 status
    status: 
    Component/Config                         State        Run  Miss   Exp Retry
    ----------------                         -----        ---  ----   --- -----
          total running configs:   0 ( processes: 0 missing: 0 stray: 0 )
    fractal%

Sarracenia can be installed system-wide or only for one user.  For use by a single 
user installation, the python `<#PIP>`_ method should work,
giving access to sr3 any all libraries needed for programmatic access.

For operational use, administrative access may be needed for package installation,
and integration with systemd. Regardless of how it is installed, some periodic
processing (on linux usually known as *cron jobs*) may also need to be configured.



Client Installation
-------------------

The package is built for python version 3.6 or higher. On systems where
they are available, debian packages are recommended. These can be obtained from the 
launchpad repository. If you cannot use debian packages, then consider pip packages 
avialable from PyPI. In both cases, the other python packages (or dependencies) needed
will be installed by the package manager automatically.



Ubuntu/Debian (apt/dpkg) **Recommended**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On Ubuntu 22.04 and derivatives::

  sudo add-apt-repository ppa:ssc-hpc-chp-spc/metpx
  sudo apt update
  sudo apt install metpx-sr3  # main python package.
  sudo apt install metpx-sr3c # optional C client.
  sudo apt install python3-amqp  # optionally support rabbitmq brokers
  sudo apt install python3-paho-mqtt  # optionally support MQTT brokers
  sudo apt install python3-netifaces # optionally support the vip directive (HA failover.)
  sudo apt install python3-dateparser python3-pytz # optionally support ftp polling.

If packages are not available, then one can substitute by using python install package (pip).
Currently, only the debian packages include man pages. The guides are only 
available in the source repository. For earlier ubuntu versions, install 
via pip is required because of missing dependencies in the python environment 
shipped with earlier operating systems.

One can create a bulletin ingest configuration::

    mkdir -p ~/.config/sr3/subscribe
    cat <<EOT >~/.config/sr3/subscribe/data-ingest.conf
    broker amqps://hpfx.collab.science.gc.ca

    topicPrefix v02.post
    subtopic *.WXO-DD.bulletins.alphanumeric.#

    directory /tmp/data-ingest
    EOT

If an option is not installed, but is needed for a given configuration, then sr3 will
detect it and complain, and one needs to install the missing support::

    fractal% sr3 foreground subscribe/data-ingest
    .2022-04-01 13:44:48,551 [INFO] 2428565 sarracenia.flow loadCallbacks plugins to load: ['sarracenia.flowcb.post.message.Message', 'sarracenia.flowcb.gather.message.Message', 'sarracenia.flowcb.retry.Retry', 'sarracenia.flowcb.housekeeping.resources.Resources', 'sarracenia.flowcb.log.Log']
    2022-04-01 13:44:48,551 [CRITICAL] 2428565 sarracenia.moth ProtocolPresent support for amqp missing, please install python packages: ['amqp']
    2022-04-01 13:44:48,564 2428564 [CRITICAL] root run_command subprocess.run failed err=Command '['/usr/bin/python3', '/home/peter/Sarracenia/sr3/sarracenia/instance.py', '--no', '0', 'foreground', 'subscribe/data-ingest']' returned non-zero exit status 1.
    
    fractal% 
    fractal% 
    fractal% sudo apt install python3-amqp
    [sudo] password for peter: 
    Reading package lists... Done
    Building dependency tree... Done
    Reading state information... Done
    The following packages were automatically installed and are no longer required:
      fonts-lyx g++-9 libblosc1 libgdk-pixbuf-xlib-2.0-0 libgdk-pixbuf2.0-0 libjs-jquery-ui liblbfgsb0 libnetplan0 libqhull-r8.0 libstdc++-9-dev python-babel-localedata
      python-matplotlib-data python-tables-data python3-alabaster python3-brotli python3-cycler python3-decorator python3-et-xmlfile python3-imagesize python3-jdcal python3-kiwisolver
      python3-lz4 python3-mpmath python3-numexpr python3-openpyxl python3-pandas-lib python3-protobuf python3-pymacaroons python3-pymeeus python3-regex python3-scipy python3-sip
      python3-smartypants python3-snowballstemmer python3-sympy python3-tables python3-tables-lib python3-tornado python3-unicodedata2 python3-xlrd python3-xlwt sphinx-common
      unicode-data
    Use 'sudo apt autoremove' to remove them.
    Suggested packages:
      python-amqp-doc
    The following NEW packages will be installed:
      python3-amqp
    0 upgraded, 1 newly installed, 0 to remove and 1 not upgraded.
    Need to get 0 B/43.2 kB of archives.
    After this operation, 221 kB of additional disk space will be used.
    Selecting previously unselected package python3-amqp.
    (Reading database ... 460430 files and directories currently installed.)
    Preparing to unpack .../python3-amqp_5.0.9-1_all.deb ...
    Unpacking python3-amqp (5.0.9-1) ...
    Setting up python3-amqp (5.0.9-1) ...
    fractal% 
    
One can satisfy missing requirements using either Debian or pip packages. To use mqtt brokers with
ubuntu 18.04, one must obtain the library via pip because the debian packages are for a version that is too old.::

    fractal% pip3 install paho-mqtt
    Defaulting to user installation because normal site-packages is not writeable
    Collecting paho-mqtt
      Using cached paho_mqtt-1.6.1-py3-none-any.whl
    Installing collected packages: paho-mqtt
    Successfully installed paho-mqtt-1.6.1
    fractal% 


Redhat/Suse Distros (rpm based)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python distutils on redhat package manager based distributions does not handle dependencies
with the current packaging, so one needs to manually install them.
For example, on fedora 28 mandatories::
 
  $ sudo dnf install python3-appdirs
  $ sudo dnf install python3-humanize
  $ sudo dnf install python3-psutil
  $ sudo dnf install python3-watchdog
  $ sudo dnf install python3-paramiko  

Optional ones::

  $ sudo dnf install python3-amqp      # optionally support rabbitmq brokers
  $ sudo dnf install python3-netifaces # optionally support vip directive for HA.
  $ sudo dnf install python3-paho-mqtt # optionally support mqtt brokers

  $ sudo dnf install python3-setuptools # needed to build rpm package.

If packages are not available, the one can substitute by using python install package (pip)

Once the dependencies are in place, one can build an RPM file using ``setuptools``::

  $ git clone https://github.com/MetPX/sarracenia
  $ cd sarracenia

  $ python3 setup.py bdist_rpm
  $ sudo rpm -i dist/*.noarch.rpm

This procedure installs only the python application (not the C one.)
No man pages nor other documentation is installed either.


PIP
~~~

On Windows or Linux distributions where system packages are not 
available or other special cases, such as if using python in virtual env, where
it is more practical to install the package using pip (python install package) 
from `<http://pypi.python.org/>`_.

It is straightforward to do that just the essentials::

  $ pip install metpx-sr3

one could also add the extras::

  $ pip install metpx-sr3[amqp,mqtt,vip]  

and to upgrade after the initial installation::

  $ pip install metpx-sr3

* To install server-wide on a linux server, prefix with *sudo*

NOTE:: 

  On many systems where both pythons 2 and 3 are installed, you may need to specify pip3 rather than pip.


System Startup and Shutdown
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the intent is to implement a Data Pump, that is a server with a role in doing
large amounts of data transfers, then the convention is to create an *sarra* application
user, and arrange for it to be started on boot, and stopped on shutdown.

When Sarracenia is installed using a debian package:

* the `SystemD <https://systemd.io>`_ unit file is installed in the right place. 
* the sarra user is created,

If installing using python3 (pip) methods, then this file should be installed:

    https://github.com/MetPX/sarracenia/blob/v03_wip/debian/metpx-sr3.service

in the correct location. It can be installed in::

    /lib/systemd/system/metpx-sr3.service

once installed, it can be activated in the normal way. It expected a sarra user
to exist, which might be created like so::

   groupadd sarra
   useradd --system --create-home sarra

Directories should be made read/write for sara.  The preferences will go in 
~sarra/.config, and the state files will be in ~sarra/.cache, and the 
periodic processing (see next session) also be implemented.


Periodic Processing/Cron Jobs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Regardless of how it is installed, Additional periodic processing may be necessary:

  * to run *sr3 sanity* to ensure that appropriate processes are running.
  * to clean up old directories and avoid filling file systems.

examples::

  # kill off stray process, or restart ones that might have died. 
  # avoiding the top of the hour or the bottom.
  7,14,21,28,35,42,49,56 * * * sr3 sanity
  # example directory cleaning jobs, script is included in examples/ subdirectory.
  17 5,11,17,23 * * *    IPALIAS='192.168.1.27';RESULT=`/sbin/ip addr show | grep $IPALIAS|wc|awk '{print $1}'`; if [ $RESULT -eq 1 ]; then tools/old_hour_dirs.py 6 /Projects/web_root ; fi  






Windows
~~~~~~~

On Windows, there are 2 (other) possible options:

**Without Python**
 Download Sarracenia installer file from `here <https://hpfx.collab.science.gc.ca/~pas037/Sarracenia_Releases>`_,
 execute it and follow the instructions.
 Don't forget to add *Sarracenia's Python directory* to your *PATH*.

**With Anaconda**
 Create your environment with the `file <../windows/sarracenia_env.yml>`_ suggested by this repository.
 Executing that command from the Anaconda Prompt should install everything::

  $ conda env create -f sarracenia_env.yml

See `Windows user manual <Windows.rst>`_ for more information on how to run Sarracenia on Windows.

Packages
~~~~~~~~

Debian packages and python wheels can be downloaded directly 
from: `launchpad <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx/+packages>`_


Source
------

Source code for each module is available `<https://github.com/MetPX>`_::

  $ git clone https://github.com/MetPX/sarracenia sarracenia
  $ cd sarracenia

Development happens on the master branch.  One probably wants real release,
so run git tag, and checkout the last one (the latest stable release)::

  $ git tag
    .
    .
    .
    v2.18.05b3
    v2.18.05b4
  $ git checkout v2.18.05b4
  $ python3 setup.py bdist_wheel
  $ pip3 install dist/metpx_sarracenia-2.18.5b4-py3-none-any.whl



Sarrac
------

The C client is available in prebuilt binaries in the launchpad repositories alongside the python packages::

  $ sudo add-apt-repository ppa:ssc-hpc-chp-spc/metpx
  $ sudo apt-get update
  $ sudo apt-get install metpx-sr3c 

For any recent ubuntu version. The librabbitmq-0.8.0 has been backported in the PPA.
sarrac's dependency. For other architectures or distributions, one can build from source::

  $ git clone https://github.com/MetPX/sarrac 

on any linux system, as long as librabbitmq dependency is satisfied. Note that the package does
not build or run on non-linux systems.
