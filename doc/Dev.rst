
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

after you have cloned the source code.

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

A release in January 2016 would be version as ``metpx-sarracenia-2.16.01a01``

Cutting a New Release
~~~~~~~~~~~~~~~~~~~~~

Prior to tagging the release, the file ``sarra/__init__.py`` should be modified and the version number increased.

Each new release triggers a *tag* in the git repository.

Example::

    git tag -a rel2.16.01a01 -m "release 2.16.01a01"


Building a Release
------------------


Python Wheel
~~~~~~~~~~~~

For testing and development:

python3 setup.py bdist_wheel 

should build a wheel in the dist sub-directory.



PyPi
~~~~

Assuming pypi upload credentials are in place, uploading a new release is a one liner:

python3 setup.py bdist_wheel upload  

Note that the same version can never be uploaded twice. Need to clarify versioning.



Debian/Ubuntu
~~~~~~~~~~~~~

- check the **build-depends** line in *debian/control* for requirements to build from source.
- The following steps will build sarracenia but not sign the changes or the source package::

    cd metpx/sarracenia
    debuild -uc -us


Launchpad
~~~~~~~~~
TODO

RPM
~~~
TODO

Windows
~~~~~~~

Just do the whole python install thing with all steps for now.

