
====================================
 MetPX-Sarracenia Developer's Guide
====================================

:version: @Version@ 
:date: @Date@

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

    git clone git://git.code.sf.net/p/metpx/git metpx-git
    cd metpx-git/sarracenia. 

The rest of the Guide assumes you are there.

Documentation
-------------

The development process is to write up what one intends to to or have done into
a restructured text file in the doc/design sub-directory.  The files there provide
a basis for discussion.  Ideally, the information there acts as a pieces which can 
be edited into documentation for the features as they are implemented.

Each new component sr\_whatever, should have relevant man pages implemented.  
The Guides should also be revised.  The form of the documentation is still under
discussion.  Current thinking:

- Install.rst (Installation)
- Dev.rst (this guide for developers)
- Subscribers.rst (a guide for how to read data from a pump.)
- Source.rst (a guide for those publishing data to a pump.)
- Admin.rst (an Admininistrator´s Guide.)

When there are new sections, they should likely start out in design/ and after
review, graduate into the main documentation.


Development
-----------

Development occurs on the master branch, which may be in any state at any given
time, and should note be relied upon.  From time to time releases are tagged, and
maintenance results in a branch.  Releases are classified as follows:

Release Process
---------------

Alpha
  snapshot releases taken directly from master, with no other qualitative guarantees.
  no gurantee of functionality, some components may be partially implemented, some
  breakage may occur.
  no bug-fixes, issues addressed by subsequent version.
  Often used for early end-to-end testing (rather than installing custom from tree on 
  each test machine.)

Beta
  Feature Complete for a given release.  Components in their final form for this release.
  Documentation exists in at least one language.
  All previously known release block bugs addressed. 
  no bug-fixes, issues addressed by subsequent version.

RC - Release Candidate.
  implies it has gone through beta to identify and address major issues.
  Translated documentation available.
  no bug-fixes, issues addressed by subsequent version.

Final versions have no suffix and are considered stable and supported.
Stable should receive bug-fixes if necessary from time to time.


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

The first alpha release in January 2016 would be versioned as ``metpx-sarracenia-2.16.01a01``

Cutting a New Release
~~~~~~~~~~~~~~~~~~~~~

* Edit ``sarra/__init__.py`` manually and set the version number.
* Run ```release.sh```
* Edit ``sarra/__init__.py`` manually and add ``+`` to the end of the version number to differentiate continuing development on the master branch from the last release.

Each new release triggers a *tag* in the git repository.

Example::

    git tag -a sarra-v2.16.01a01 -m "release 2.16.01a01"
    
A convenience script has been created to automate the release process. Simply run ``release.sh`` and it will guide you in cutting a new release.


.. note::
   FIXME:  the adding of the + to master makes the current tree not the release,
   so need to expclicitly checkout the tag... no?  how does one 
   Can someone correct this:

   git checkout -t sarra-v2.16.01a01  ?


Building a Release
------------------

MetPX-Sarracenia is distributed in a few different ways, and each has it's own build process.
Packaged releases are always preferable to one off builds, because they are reproducible.

When development requires testing across a wide range of servers, it is preferred to make an alpha
release, rather than installing one off packages.  So the preferred mechanisms is to build
the ubuntu and pip packages at least, and install on the test machines using the relevant public
repositories.
 



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

.. note:: 
   when uploading pre-release packages (alpha,beta, or RC) PYpi does not serve those to users by default.
   For seamless upgrade, early testers need to do supply the --pre switch to pip:

   pip3 install --upgrade --pre metpx-sarracenia


Debian/Ubuntu
~~~~~~~~~~~~~

This process builds a local .deb in the parent directory using standard debian mechanisms.
- check the **build-depends** line in *debian/control* for dependencies that might be needed to build from source.
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

Web Site
~~~~~~~~

TODO - how to update the web site (required for documentation updates)


RPM
~~~

TODO

Windows
~~~~~~~

Install winpython from github.io version 3.4 or higher.  Then use pip to install from PyPI.


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


