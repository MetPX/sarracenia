
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


------------------
Building a Release
------------------



What commands are needed to perform a release:

- git branch

Name the version in a way compatible with PEP440.
Then create the various packages:  upload to 


Python Wheel
------------

For testing and development:

python3 setup.py bdist_wheel 

should build a wheel in the dist sub-directory.



PyPi
----

Assuming pypi upload credentials are in place, uploading a new release is a one liner:

python3 setup.py bdist_wheel upload  

Note that the same version can never be uploaded twice. Need to clarify versioning.



Debian/Ubuntu
-------------

- check the **build-depends** line in *debian/control* for requirements to build from source.
- The following steps will build sarracenia but not sign the changes or the source package::

    cd metpx/sarracenia
    debuild -uc -us


RPM
---


Windows
-------

Just do the whole python install thing with all steps for now.

