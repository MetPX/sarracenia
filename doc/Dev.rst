
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
- python3 pyftpdlib module, used to run an ftpserver on a high port during the flow test.
- git. in order to download the source from the sf.net repository.
- a dedicated rabbitmq broker, with administrative access, to run the flow_test.
  The flow test creates and destroys exchanges and will disrupt any active flows on the broker.

after you have cloned the source code::

    git clone git://git.code.sf.net/p/metpx/sarracenia metpx-sarracenia
    cd metpx-sarracenia

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

- `Install.rst <Install.html>`_ (Installation)
- `Dev.rst <Dev.html>`_ (this guide for developers)
- `Subscribers.rst <Subscribers.html>`_ (a guide for how to read data from a pump.)
- `Source.rst <Source.html>`_ (a guide for those publishing data to a pump.)
- `Admin.rst <Admin.html>`_ (an Admininistrator´s Guide.)

When there are new sections, they should likely start out in design/ and after
review, graduate into the main documentation.


Development
-----------

Development occurs on the master branch, which may be in any state at any given
time, and should not be relied upon.  From time to time releases are tagged, and
maintenance results in a branch.  Releases are classified as follows:

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
One can build python wheels, or debian packages for local testing purposes
during development.

.. Note:: If you change default settings for exchanges / queues  as
      part of a new version, keep in mind that all components have to use
      the same settings or the bind will fail, and they will not be able
      to connect.  If a new version declares different queue or exchange
      settings, then the simplest means of upgrading (preserving data) is to
      drain the queues prior to upgrading, for example by
      setting, the access to the resource will not be granted by the server.
      (??? perhaps there is a way to get access to a resource as is... no declare)
      (??? should be investigated)

      Changing the default require the removal and recreation of the resource.
      This has a major impact on processes...


Python Wheel
~~~~~~~~~~~~

For testing and development::

    python3 setup.py bdist_wheel

should build a wheel in the dist sub-directory.


Debian/Ubuntu
~~~~~~~~~~~~~

This process builds a local .deb in the parent directory using standard debian mechanisms.
- check the **build-depends** line in *debian/control* for dependencies that might be needed to build from source.
- The following steps will build sarracenia but not sign the changes or the source package::

    cd metpx/sarracenia
    sudo apt-get install devscripts
    debuild -uc -us
    sudo dpkg -i ../<the package just built>


Committing Code
~~~~~~~~~~~~~~~

What should be done prior to committing to the master branch?
Checklist:

- **flow_test works** (See Testing) The master branch should always be functional, do not commit code if the flow_test is not working.
- Natural consequence: if the code changes means tests need to change, include the test change in the commit.
- **update doc/** manual pages should get their updates ideally at the same time as the code.
- Update CHANGES.txt to assist in the release process.  Describe changes in code.
- If the code has an impact (different configuration, change in behaviour) Update doc/UPGRADING.rst



Testing
-------

Before commiting code to the master branch, as a Quality Assurance measure one should run all available self-tests.
It is assumed that the specific changes in the code have already been unit
tested.  Please add self-tests as appropriate to this process to reflect the new ones.

The configuration one is trying to replicate:

.. image:: Flow_test.svg

Assumption: test environment is a linux PC, either a laptop/desktop, or a server on which one
can start a browser. If working with the c implementation as well, there are also the following
flows defined:

.. image:: cFlow_test.svg

A typical development workflow will be::

   cd sarra ; *make coding changes*
   cd ../c
   debuild -uc -us
   cd ..
   debuild -uc -us
   sudo dpkg -i ../pkg.deb sarrac*.deb libsarra*.deb
   cd test
   ./flow_cleanup.sh
   rm directories with state (indicated by flow_cleanup.sh)
   ./flow_setup.sh  ; *starts the flows*
   ./flow_check.sh  ; *checks the flows*
   ./cpost_test.sh  ; *checks the c posting flow*
   ./libsrshim_test.sh  ; *checks libc shim library*
   
One can then study the results, and determing the next cycle of modifications to make.
The rest of this section documents these steps in much more detail.  
Before one can run the flow_test, some pre-requisites must be taken care of.

   

local installation on Workstation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The flow_test invokes the version of metpx-sarracenia that is installed on the system,
and not what is in the development tree.  It is necessary to install the package on 
the system in order to have it run the flow_test.

In your development tree ...    
One can either create a wheel by running either::

       python3 setup.py bdist_wheel

whitch creates a wheel package under  dist/metpx*.whl
then as root  install that new package::

       pip3 install --upgrade ...<path>/dist/metpx*.whl

or one can use debian packaging::

       debuild -us -uc
       sudo dpkg -i ../python3-metpx-...

which accomplishes the same thing using debian packaging.


Install servers on Workstation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install a minimal localhost broker, configure test users.
with credentials stored for localhost::

     sudo apt-get install rabbitmq-server
     sudo rabbitmq-plugins enable rabbitmq_management
     echo "amqp://bunnymaster:MaestroDelConejito@localhost/" >>~/.config/sarra/credentials.conf
     echo "amqp://tsource:TestSOUrCs@localhost/" >>~/.config/sarra/credentials.conf
     echo "amqp://tsub:TestSUBSCibe@localhost/" >>~/.config/sarra/credentials.conf
     echo "amqp://tfeed:TestFeeding@localhost/" >>~/.config/sarra/credentials.conf

     cat >~/.config/sarra/default.conf <<EOT

     broker amqp://tfeed@localhost/
     cluster localhost
     admin amqp://bunnymaster@localhost/
     feeder amqp://tfeed@localhost/
     declare source tsource
     declare subscribe tsub
     EOT

     sudo rabbitmqctl delete_user guest
     sudo rabbitmqctl add_user bunnymaster MaestroDelConejito
     sudo rabbitmqctl set_permissions bunnymaster ".*" ".*" ".*"
     sudo rabbitmqctl set_user_tags bunnymaster administrator
     cd /usr/local/bin
     sudo wget http://localhost:15672/cli/rabbitmqadmin
     chmod 755 rabbbitmqadmin
     sr_audit --users foreground

.. Note::

    Please use other passwords in credentials for your configuration, just in case.
    Passwords are not to be hard coded in self test suite.
    The users bunnymaster, tsource, tsub, and tfeed are to be used for running tests

    The idea here is to use tsource, tsub, and tfeed as broker accounts for all
    self-test operations, and store the credentials in the normal credentials.conf file.
    No passwords or key files should be stored in the source tree, as part of a self-test
    suite.


Setup the flow_test Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One part of the flow test runs an ftp server.  Need the following package for that::

    sudo apt-get install python3-pyftpdlib 

The setup script starts a trivial web server, and ftp server, 
and defines some fixed test clients that will be used during self-tests::

     cd sarracenia/test
     . ./flow_setup.sh

The working test flow setup script (``flow_setup.sh``) will install configuration files for
the network of configurations running.  


Run Flow Test
~~~~~~~~~~~~~

The flow_check.sh script reads the log files of all the components started, and compares the number
of messages, looking for a correspondence within +- 10%   It takes a few minutes for the
configuration to run before there is enough data to do the proper measurements::

     ./flow_check.sh

sample output::

     blacklab% ./flow_check.sh
     initial sample building sample size 3421 need at least 1000
     test 1: SUCCESS, shovel1 (3421) reading the same as shovel2 (3421) does
     test 2: SUCCESS, winnow (6841) reading double what sarra (3421) does
     test 3: SUCCESS, subscribe (3421) has the same number of items as sarra (3421)
     test 4: SUCCESS, subscribe (3421) has the same number of items as shovel1 (3421)
     blacklab%

if the flow_check.sh passes, then
one has a reasonable confidence in the overall functionality of the application,
but the test coverage is not exhaustive.  It is more qualitative sampling of the most
common use cases rather than a thorough examination of all functionality.  While not
thorough, it is good to know the flows are working.

Rerun basic self test
~~~~~~~~~~~~~~~~~~~~~

The following script runs some unit self tests of individual .py files in the source code::

   ./some_self_tests.sh

.. Note::

  **FIXME**: so far got first sr_credentials, sr_config, sr_consumer, sr_subscribe, sr_instances PASS.

  **FIXME**: working on sr_poster.

  **FIXME**: many tests refer to sites only accessible within EC zone.


Run Unit Tests 
~~~~~~~~~~~~~~

The following tests are self descriptive, but there is no obvious check of success.
One must examine the output of the command and determine if the result is as intended::

     test_sr_post.sh
     test_sr_watch.sh
     test_sr_subscribe.sh
     test_sr_sarra.sh

.. Note::

  Some tests error ...

  in ``test_sr_sarra.sh`` ... there are lots of ftp/sftp connections
  so some config settings like ``sshd_config`` (``MaxStartups 500``) might
  might be required to have successful tests.

Flow Cleanup
~~~~~~~~~~~~

When done testing, run::

  . ./flow_cleanup.sh

Which will kill the running web server, and delete all local queues.
This also needs to be done between each run of the flow test.


Flow Test Length
~~~~~~~~~~~~~~~~

The flow_test length defaults to 1000 files being flowed through the test cases.  when in rapid
development, one can supply an argument to shorten that::

  ./flow_test 200

Towards the end of a development cycle, longer flow_tests are adviseable::

  ./flow_test 20000 

to identify more issues.


Building a Release
------------------

MetPX-Sarracenia is distributed in a few different ways, and each has it's own build process.
Packaged releases are always preferable to one off builds, because they are reproducible.

When development requires testing across a wide range of servers, it is preferred to make
an alpha release, rather than installing one off packages.  So the preferred mechanisms is
to build the ubuntu and pip packages at least, and install on the test machines using
the relevant public repositories.

To publish a release one needs to:

- Set the version.
- upload the release to pypi.org so that installation with pip succeeds.
- upload the release to launchpad.org, so that the installation of debian packages
  using the repository succeeds.
- upload the packages to sourceforge for other users to download the package directly
- upload updated documentation to sourceforge.


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


Setting the Version
~~~~~~~~~~~~~~~~~~~

Each new release triggers a *tag* in the git repository ( executes *git tag -a sarra-v2.16.01a01 -m "release 2.16.01a01"* )

A convenience script has been created to automate the release process. Simply run ``release.sh`` and it will guide you in cutting a new release.


* Edit ``sarra/__init__.py`` manually and set the version number.
* git commit -a
* Run ```release.sh``` example::

    ./release.sh "release 2.16.01a01"

* you will be prompted to enter information about the release.

* git push


PyPi
~~~~

Pypi Credentials go in ~/.pypirc.  Sample Content::

  [pypi]
  username: SupercomputingGCCA
  password: <get this from someone>

Assuming pypi upload credentials are in place, uploading a new release used to be a one liner::

    python3 setup.py bdist_wheel upload

This still works with setuptools > 24, but ubuntu 16 only has version 20, so it can no longer be used there.
Instead, one is supposed to use the twine package.  We have tried it once installing it vi pip3,
next time, we should try the one provided with ubuntu 16.04 (via apt-get.)::

   python3 setup.py bdist_wheel 
   twine upload dist/metpx_sarracenia-2.17.7a2-py3-none-any.whl

Note that the same version can never be uploaded twice.

A convenience script has been created to build and publish the *wheel* file. Simply run ``publish-to-pypi.sh`` and it will guide you in that.

.. Note::
   When uploading pre-release packages (alpha,beta, or RC) PYpi does not serve those to users by default.
   For seamless upgrade, early testers need to do supply the ``--pre`` switch to pip::

     pip3 install --upgrade --pre metpx-sarracenia

   On occasion you may wish to install a specific version::

     pip3 install --upgrade metpx-sarracenia==2.16.03a9



Launchpad
~~~~~~~~~

Automated Build
+++++++++++++++

* Ensure the code mirror is updated by checking the **Import details** by checking `this page <https://code.launchpad.net/~ssc-hpc-chp-spc/metpx-sarracenia/master>`_
* if the code is out of date, do **Import Now** , and wait a few minutes while it is updated.
* once the repository is uptodate, proceed with the build request.
* Go to the `sarracenia release <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sarracenia-release>`_ recipe
* Click on the **Request build(s)** button to create a new release
* The built packages will be available in the `metpx ppa <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx>`_

Daily Builds
++++++++++++

Daily builds are configured using `this recipe <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sarracenia-daily>`_ and 
are run once per day when changes to the repository occur. These packages are stored in the `metpx-daily ppa <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-daily>`_.
One can also **Request build(s)** on demand if desired.


Manual Process
++++++++++++++

The process for manually publishing packages to Launchpad ( https://launchpad.net/~ssc-hpc-chp-spc ) involves a more complex set of steps, and so the convenience script ``publish-to-launchpad.sh`` will be the easiest way to do that. Currently the only supported releases are **trusty** and **xenial**. So the command used is::

    publish-to-launchpad.sh sarra-v2.15.12a1 trusty xenial


However, the steps below are a summary of what the script does:

- for each distribution (precise, trusty, etc) update ``debian/changelog`` to reflect the distribution
- build the source package using::

    debuild -S -uc -us

- sign the ``.changes`` and ``.dsc`` files::

    debsign -k<key id> <.changes file>

- upload to launchpad::

    dput ppa:ssc-hpc-chp-spc/metpx-<dist> <.changes file>

**Note:** The GPG keys associated with the launchpad account must be configured in order to do the last two steps.






Updating The Project Website
----------------------------

The MetPX website is built from the documentation in the various modules in the project. It builds using all **.rst** files found in **sarracenia/doc** as well as *some* of the **.rst** files found in **sundew/doc**.

Building Locally
~~~~~~~~~~~~~~~~

In order to build the HTML pages, the following software must be available on your workstation:

* `dia <http://dia-installer.de/>`_
* `docutils <http://docutils.sourceforge.net/>`_
* `groff <http://www.gnu.org/software/groff/>`_

From a command shell::

  cd site
  make


Updating The Website
~~~~~~~~~~~~~~~~~~~~

To publish the site to sourceforge (updating metpx.sourceforge.net), you must have a sourceforge.net account
and have the required permissions to modify the site.

From a shell, run::

  make SFUSER=myuser deploy



Development Environment
-----------------------


Local Python
~~~~~~~~~~~~

Working with a non-packaged version:

notes::

    python3 setup.py build
    python3 setup.py install


Windows
~~~~~~~

Install winpython from github.io version 3.4 or higher.  Then use pip to install from PyPI.



Conventions
-----------

Below are some coding practices that are meant to guide developers when contributing to sarracenia.
They are not hard and fast rules, just guidance.


When to Report
~~~~~~~~~~~~~~

sr_report(7) messages should be emitted to indicate final disposition of the data itself, not
any notifications or report messages (don't report report messages, it becomes an infinite loop!)
For debugging and other information, the local log file is used.  For example, sr_shovel does
not emit any sr_report(7) messages, because no data is transferred, only messages.



Where to Put Option Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most options are documented in sr_config(7), because they are common to many components.  Any options used
by multiple components should be documented there.  Options which are unique to a single component, should
be documented in the man page for that component.

Where the default value for an option varies among components, sr_config(7) should indicate only that
the default varies.  Each component's man page should indicate the option's default for that component.


Adding Checksum Algorithms
~~~~~~~~~~~~~~~~~~~~~~~~~~

To add a checksum algorithm, need to add a new class to sr_util.py, and then modify sr_config.py
to associate it with a label.  Reading of sr_util.py makes this pretty clear.
Each algorithm needs:
- an initializer (sets it to 0)
- an algorithm selector.
- an updater to add info of a given block to an existing sum,
- get_value to obtain the hash (usually after all blocks have updated it)

These are called by the code as files are downloaded, so that processing and transfer are overlapped.

For example, to add SHA-2 encoding::

  from hashlib import sha256

  class checksum_s(object):
      """
      checksum the entire contents of the file, using SHA256.
      """
      def __init__(self):
          self.value = '0'

      def get_value(self):
          self.value = self.filehash.hexdigest()
          return self.value

      def update(self,chunk):
          self.filehash.update(chunk)

      def set_path(self,path):
          self.filehash = sha256()

Then in sr_config.py, in the set_sumalgo routine::

      if flgs == 's':
          self.sumalgo = checksum_s()

Might want to add 's' to the list of valid sums in validate_sum( as well.

It is planned for a future version to make a plugin interface for this so that adding checksums
becomes an application programmer activity.
