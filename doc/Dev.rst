
====================================
 MetPX-Sarracenia Developer's Guide
====================================

.. contents::


Tools you Need
--------------

To hack on the sarracenia source, you need:
 - python3.  The application is developed in and depends on python versions > 3.
 - some python-amqp bindings (like python-amqplib for current implementations)
 - a bunch of other modules indicated in the dependencies (setup.py or debian/control)
 - paramiko. For SSH/SFTP support you need to install the python-paramiko package (which
   works with python3 even though the documentation says it is for python2.)
 - (soon?) watchdog ( https://pypi.python.org/pypi/watchdog ) not available as a .deb yet. 
   used to encapsulate directory watching for sr_watch.
 - git. in order to download the source from the sf.net repository.
 - a running rabbitmq broker (if you want to actually run any code.)

after you have cloned the source code::

    cd sarracenia. 

The rest of the Guide assumes you are there.


Release Process
---------------


Versioning Scheme
~~~~~~~~~~~~~~~~~

Each release will be versioned as ``<protocol version>.<YY>.<MM> <segment>``


Where:

- **protocol version** is the message version. In Sarra messages, they are all prefixed with v02 (at the moment).
- **YY** is the last two digits of the year of the initial release in the series.
- **MM** is a TWO digit month number i.e. for April: 04.
- **segment** is what would be used within a series. 
  from pep0440:
  X.YaN   # Alpha release
  X.YbN   # Beta release
  X.YrcN  # Release Candidate
  X.Y     # Final release

Example: 

A release in January 2016 would be versioned as ``metpx-sarracenia-2.16.01a01``

Cutting a New Release
~~~~~~~~~~~~~~~~~~~~~

* Edit ``sarra/__init__.py`` manually and increment the version number.
* Run ```release.sh```
* Edit ``sarra/__init__.py`` manually and add ``+`` to the end of the version number. This indicates ongoing development.

Each new release triggers a *tag* in the git repository.

Example::

    git tag -a sarra-v2.16.01a01 -m "release 2.16.01a01"
    
A convenience script has been created to automate the release process. Simply run ``release.sh`` and it will guide you in cutting a new release.




Building a Release
------------------

MetPX-Sarracenia is distributed in a few different ways, and each has it's own build process.


Python Wheel
~~~~~~~~~~~~

For testing and development::

    python3 setup.py bdist_wheel 

should build a wheel in the dist sub-directory.


PyPi
~~~~

Assuming pypi upload credentials are in place, uploading a new release is a one liner::

    python3 setup.py bdist_wheel upload  

Note that the same version can never be uploaded twice. 

A convenience script has been created to build and publish the *wheel* file. Simply run ``publish-to-pypi.sh`` and it will guide you in that.


Debian/Ubuntu
~~~~~~~~~~~~~

- check the **build-depends** line in *debian/control* for requirements to build from source.
- The following steps will build sarracenia but not sign the changes or the source package::

    cd metpx/sarracenia
    debuild -uc -us


Launchpad
~~~~~~~~~

The process for publishing packages to Launchpad ( https://launchpad.net/~ssc-hpc-chp-spc ) involves a more complex set of steps, and so the convenience script ``publish-to-launchpad.sh`` will be the easiest way to do so::

    publish-to-launchpad.sh sarra-v2.15.12a1 precise trusty

However, the steps below are a summary of what the script does:

- for each distribution (precise, trusty, etc) update ``debian/changelog`` to reflect the distribution
- build the source package using::

    debuild -S -uc -us
    
- sign the ``.changes`` and ``.dsc`` files::

    debsign -k<key id> <.changes file>

- upload to launchpad::

    dput ppa:ssc-hpc-chp-spc/metpx-<dist> <.changes file>
    
**Note:** The GPG keys associated with the launchpad account must be configured in order to do the last two steps.

RPM
~~~

TODO

Windows
~~~~~~~

Just do the whole python install thing with all steps for now.  Easiest is: winpython.github.io 


SourceForge
~~~~~~~~~~~

TODO

Development Environment
-----------------------


Local Python 
~~~~~~~~~~~~

Working with a non-packaged version:

notes::

    python3 setup.py build
    python3 setup.py install


