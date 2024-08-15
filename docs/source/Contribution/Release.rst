============================
 Releasing MetPX-Sarracenia 
============================

:version: |release|
:date: |today|


Pre-Release Overview
--------------------

MetPX-Sarracenia is distributed in a few different ways, and each has it's own build process.
Packaged releases are always preferable to one off builds, because they are reproducible.

To publish a pre-release one needs to:

- starting with the development branch (for sr3) or v2_dev (for v2.)
  * git checkout development 
  * git pull
  * git checkout development_py36
  * git pull
  * git merge development

- validate that the correct version of C stack will be running when running flow tests.
  on each server::

      * sr3_cpost -h | head -3

  Is that the version wanted?
  Consult C installation/release info to make sure you have the version you want
  for the flow tests that follow.

  * https://github.com/MetPX/sarrac/tree/_branch_/Build.rst

  * https://github.com/MetPX/sarrac/tree/_branch_/Release.rst

- run QA process on all operating systems looking for regressions on older 3.6-based ones.

  - github runs flow tests for ubuntu 20.04 and 22.04, review those results.
  - github runs unit tests (only work on newer python versions.), review those results.
  - find ubuntu 18.04 server. build local package, run flow tests.
         * git checkout development_py36
         * python3 setup.py bdist_rpm*
         * run flow tests:

           * cd ~/sr_insects;
           * for flow_test in static_flow flakey_broker restart_server dyncamic_flow; do

             - cd $flow_test
             - ./flow_setup.sh && ./flow_limit.sh && ./flow_check.sh
             - # study results.
             - ./flow_cleanup.sh
             - cd ..

  - find redhat 8 server.  build package::
   
         * git checkout development_py36
         * git pull
         * python3 setup.py bdist_rpm*
         * run flow tests

  - find redhat 9 server,  build package::

         * git checkout development_py36
         * git pull
         * python3 setup.py bdist_rpm*
         * run flow tests


- review debian/changelog and update it based on all merges to the branch since previous release.

     * git checkout development
     * git log | less
     * vi debian/changelog
     * git commit -a -m "last changes for release"
     * git push

- Set the pre-release tags.

     * git pull
     * git checkout development_py36
     * git pull
     * git tag -a o3.xx.yyrcz -m "pre-release o3.xx.yy.rcz"
     * git pull 
     * git checkout pre_release_py36
     * git pull
     * git merge development_py36
     * git push
     * git push origin o3.xx.yyrcz

     * git checkout development
     * git tag -a v3.xx.yy.rcZ -m "pre-release v3.xx.yy.rcz"
     * git checkout pre_release
     * git pull
     * git merge development
     * git push
     * git push origin v3.xx.yyrcz



- pypi.org

  - to ensure compatiblity with python3.6, update a python3.6 branch (for redhat 8 and/or ubuntu 18.)
  - use the python3.6 branch to release to pypi (because upward compatibility works, but not downward.)

    * git checkout pre_release_py36
    * git pull
    * python3 setup.py bdist_wheel

  - upload the pre-release so that installation with pip succeeds.

    * twine upload dist/the_wheel_produced_above.whl 


- launchpad.org:  

  * ensure the two branches are ready on github.

      * pre-release branch ready.
      * pre-release_py36 branch ready.
  * update git repository (Import now): https://code.launchpad.net/~ssc-hpc-chp-spc/metpx-sarracenia/+git/trunk

      * do: **Import Now**

  * run the recipe for old OS (18.04, 20.04) https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sr3-pre-release-old

      * do: **Request Build** (on Focal and Bionic )

  * run the recipe for new OS (22.04, 24.04) https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sr3-pre-release 

      * do: **Request Build** (on Jammy and Noble at least)

- build redhat packages.

  - find redhat 8 server. build package:: 

        git checkout pre-release_py36
        git pull
        python3 setup.py bdist_rpm 

    
  - find redhat 9 server, build package::

        git checkout pre-release_py36
        git pull
        python3 setup.py bdist_rpm 

- on github: Draft a release.

  - create release notes as prompted.
  - copy the installation instructions from a previous release (for mostly ubuntu.)
  - attach:
    - wheel built on python3.6 on ubuntu 18 (the uploaded to pypi.org)
    - windows binary.
    - redhat 8 and 9 rpms labelled as such.
    
- encourage testing of pre-release, wait some time for blockers, if any.


Stable Release Process
----------------------

A Stable version is just a pre-release version that has been
re-tagged as stable after some period of waiting for issues
to arise. Since all the testing was done for the pre-release,
the stable release does not require any explicit testing.

* merge from pre-release to stable::

    
     git checkout pre-release
     git pull
     git checkout stable
     git pull
     git merge pre-release
     git push

     # there will be conflicts here for debian/changelog and sarracenia/_version.py
     # for changelog:
     #   - merge all the rcX changelogs into a single stable one.
     #   - ensure the version at the top is correct and tagged 'unstable'
     #   - edit the signature at the bottom for reflect who you are, and current date.
     # sr3 for sarracenia/_version.py (v2 sarra/__init__.py )
     #   - fix it so it shows the correct stable version.
     git tag -a v3.xx.yy -m "v3.xx.yy"
     git push origin v3.xx.yy

* merge from pre-release_py36 to stable_py36::

     git checkout pre_release_py36
     git pull
     git checkout stable_py36
     git pull
     git merge pre_release_py36
     git push
     # same editing required as above.
     git tag -a o3.xx.yy -m "o3.xx.yy"
     git push origin o3.xx.yy

* pypi.org

  - to ensure compatiblity with python3.6, update a python3.6 branch (for redhat 8 and/or ubuntu 18.)
  - use the python3.6 branch to release to pypi (because upward compatibility works, but not downward.)

    * git checkout stable_py36
    * git pull
    * python3 setup.py bdist_wheel

  - upload the pre-release so that installation with pip succeeds.

    * twine upload dist/the_wheel_produced_above.whl 

  
* go on Launchpad, 

   * stable branch ready.
   * stable_py36 branch ready.
   * https://code.launchpad.net/~ssc-hpc-chp-spc/metpx-sarracenia/+git/trunk
   * do: **Import Now**
   * https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sr3-old
   * do: **Request Build** (on Focal and Bionic )
   * https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sr3
   * do: **Request Build** (on Jammy and Noble at least)

* go on ubuntu 18.04, build bdist_wheel::

      git checkout stable_py36
      git pull
      python3 setup.py bdist_wheel 

note that *pip3 install wheel* is needed, because the one from
ubuntu 18 is not compatible with the current pypi.org.

* go on redhat 8, build rpm::

      git checkout stable_py36
      git pull
      python3 setup.py bdist_rpm 
      ls dist/
      mv rpm file to have rh8 in the name somewhere.

* go on redhat 9, build rpm **NOTE: Broken!, for now use redhat 8 process** ::

      git checkout stable_py36
      git pull
      rpmbuild --build-in-place -bb metpx-sr3.spec
      ls dist/
      mv rpm file to have rh8 in the name somewhere.


* On github.com, create release.

  * copy/paste install procedure from a previous release, adjust
  * attach wheel build on ubuntu 18.
  * attach redhat 8 rpm
  * attach redhat 9 rpm 
  * attach windows exe ... see: `Building a Windows Installer`_

Details
-------


Quality Assurance 
~~~~~~~~~~~~~~~~~

The Quality Assurance (QA) process, occurs mainly on the development branch.
prior to accepting a release, and barring known exceptions, 

* QA tests automatically triggerred by pushes to the development branch should all pass.
  (All related github actions.)
  tests: static, no_mirror, flakey_broker, restart_server, dynamic_flow are included in "flow.yml"

      
* build an ubuntu 18.04 vm and run the flow tests there to ensure that it works.
  (installation method: cloning from development on github.)
  tests: static, no_mirror, flakey_broker, restart_server, dynamic_flow

* build a redhat 8 vm and run the flow test there to ensure that it works.
  (installation method: cloning from development on github.)
  tests: static, no_mirror, flakey_broker, restart_server, dynamic_flow::

       git checkout pre_release_py36
       git pull
       python3 setup.py bdist_rpm
 
* Redhat 9 rpms currently do not work... vm and run the flow test there to ensure that it works::

       git checkout pre_release_py36
       git pull
       python3 setup.py bdist_rpm
         

* build a windows executable... test?

For extensive discussion see:  https://github.com/MetPX/sarracenia/issues/139

Once the above are done, the pre-release process can proceed.


Versioning Scheme
~~~~~~~~~~~~~~~~~

Each release will be versioned as ``<version>.<YY>.<MM> <segment>``

It is difficult to reconcile debian and python versioning conventions. 
We use rcX for pre-releases which work in both contexts.

Where:

- **Version** is the application version. Currently, 2 and 3 exist.
- **YY** is the last two digits of the year of the initial release in the series.
- **MM** is a TWO digit month number i.e. for April: 04.
- **segment** is what would be used within a series.
  from pep0440:
  X.YrcN  # Release Candidate
  X.Y     # Final release
  X.ypN   #ack! patched release.

Currently, 3.00 is still stabilizing, so the year/month convention is not being applied.
Releases are currently  3.00.iircj
where:

  * ii -- incremental number of pre-releases of 3.00

  * j -- beta increment.

The first alpha release of v2 from January 2016 would be versioned 
as ``metpx-sarracenia-2.16.01a01``. A sample v3 is v3.00.52rc2. At some point 3.00 
will be complete & solid enough that the we will resume the year/month convention.

Final versions have no suffix and are considered stable and supported.
Stable should receive bug-fixes if necessary from time to time.

.. Note:: If you change default settings for exchanges / queues  as
      part of a new version, keep in mind that all components have to use
      the same settings or the bind will fail, and they will not be able
      to connect. If a new version declares different queue or exchange
      settings, then the simplest means of upgrading (preserving data) is to
      drain the queues prior to upgrading, for example by
      setting, the access to the resource will not be granted by the server.
      (??? perhaps there is a way to get access to a resource as is... no declare)
      (??? should be investigated)

      Changing the default requires the removal and recreation of the resource.
      This has a major impact on processes...


Set the Version
~~~~~~~~~~~~~~~

This is done to *start* development on a version. It should be done on development
after every release.

* git checkout development
* Edit ``sarracenia/_version.py`` (``sarra/__init__.py`` for v2) manually and set the version number.
* Edit CHANGES.rst to add a section for the version.
* run dch to start the changelog for the current version. 
  * change *unstable* to *UNRELEASED* (maybe done automatically by dch.)
* git commit -a 
* git push


Git Branches for Pre-release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prior to releasing, ensure that all QA tests in the section above are passed.
When development for a version is complete. The following should occur:

A tag should be created to identify the end of the cycle::

   git checkout development
   git tag -a v3.16.01rc1 -m "release 3.16.01rc1"
   git push
   git push origin v3.16.01rc1

Once the tag is in the development branch, promote it to stable::

   git checkout pre-release
   git merge development
   git push

Once stable is updated on github, the docker images will be automatically upgraded, but
we then need to update the various distribution methods: `PyPI`_, and `Launchpad`_

Once package generation is complete, one should `Set the Version`_
in development to the next logical increment to ensure no further development
occurs that is identified as the released version.    


Build Python3.6 Compatbile Branch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Canonical, the company behind Ubuntu, provides Launchpad as a means of enabling third parties to build
packages for their operating system releases. It turns out that the newer OS versions have dependencies 
that are not available on the old ones. So the development branch is configured to build on newer 
releases, but an a separate branch must be created when creating releases for ubuntu bionic (18.04) and 
focal (20.04.) The same branch can be used to build on redhat 8 (another distro that uses python 3.6)

Post python 3.7.?, the installatiion method changes from the obsolete setup.py to use pyproject.toml,
and the *hatch* python tools. Prior to that version, hatchling is not supported, so setup.py must be used.
However the presence of pyproject.toml fools the setup.py into thinking it can install it.  To
get a correct installation one must:

* remove pyproject.toml (because setup.py gets confused.)

* remove "pybuild-plugin-prproject" dep from debuan

in detail::

  # on ubuntu 18.04 or redhat 8 (or some other release with python 3.6 )

  git checkout pre-release
  git branch -D pre_release_py36
  git branch stable_py36
  git checkout stable_py36
  vi debian/control
  # remove pybuild-plugin-pyproject from the "Build-Depends"
  git rm pyproject.toml
  # remove the new-style installer to force use of setup.py
  git commit -a -m "adjust for older os"

There might be a "--force" required at some point. Perhaps something along the lines of::

  git push origin stable_py36 --force

Then proceed with Launchpad instructions.


PyPi
~~~~

Because python packages are upward compatible, but not downward, build them on ubuntu 18.04
(oldest supported python & OS version.) in order for pip installs to work on the widest number
of systems.

for local installation on a computer with a python 3.6 for testing and development::

    python3 setup.py bdist_wheel

or... on newer systems, using build instead::

    python3 -m build --no-isolation

Pypi does not distinguish between older and newer python releases. There is only one package
version for all supported versions. When uploading from a new OS, the versions in use on the 
OS are inferred to be the minimum, and so installation on older operating systems may be blocked
by generated dependencies on overly modern versions.

So when uploading to pypi, always do so from the oldest operating system where it needs to work.
upward compatibility is more likely than downward.

Pypi Credentials go in ~/.pypirc.  Sample Content::

  [pypi]
  username: SupercomputingGCCA
  password: <get this from someone>

Assuming pypi upload credentials are in place, uploading a new release used to be a one liner::

    python3 setup.py bdist_wheel upload

on older systems, or on (python >= 3.7) newer ones::

   twine upload dist/metpx_sarracenia-2.22.6-py3-none-any.whl dist/metpx_sarracenia-2.22.6.tar.gz

Should always include source (the .tar.gz file)
Note that the CHANGES.rst file is in restructured text and is parsed by pypi.python.org
on upload.  

.. Note::

   When uploading pre-release packages (alpha,beta, or RC) PYpi does not serve those to users by default.
   For seamless upgrade, early testers need to do supply the ``--pre`` switch to pip::

     pip3 install --upgrade --pre metpx-sarracenia

   On occasion you may wish to install a specific version::

     pip3 install --upgrade metpx-sarracenia==2.16.03a9

   command line use of setup.py is deprecated.  Replaced by build and twine.


Launchpad
---------

Generalities about using Launchpad for MetPX-Sarracenia.

Repositories & Recipes
~~~~~~~~~~~~~~~~~~~~~~

For Ubuntu operating systems, the launchpad.net site is the best way to provide packages that are fully integrated
( built against current patch levels of all dependencies (software components that Sarracenia relies
on to provide full functionality.)) Ideally, when running a server, a one should use one of the repositories,
and allow automated patching to upgrade them as needed.

Before every build of any package, it is important to update the git repo mirror on launchpad.

* https://code.launchpad.net/~ssc-hpc-chp-spc/metpx-sarracenia/+git/trunk
* do: **Import Now**

Wait until this completes.

Repositories:

* Daily https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-daily (living on dev... )
  should, in principle, be always ok, but regressions happen, and not all testing is done prior to every
  commit to dev branches.
  Recipes:

  * metpx-sr3-daily -- automated daily build of sr3 packages happens from *development* branch.
  * metpx-sarracenia-daily -- automated daily build of v2 packages happens from *v2_dev* branch

* Pre-Release https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-pre-release (for newest features.)
  from *development* branch. Developers manually trigger builds here when it seems appropriate (testing out
  code that is ready for release.)

  * metpx-sr3-pre-release -- on demand build sr3 packages from pre-release branch.
  * metpx-sr3-pre-release-old -- on demand build sr3 packages from *pre_release_py36* branch.
  * metpx-sarracenia-pre-release -- on demand build sr3 packages from *v2_dev* branch.

* Release https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx (for maximum stability)
  from *v2_stable* branch.  After testing in systems subscribed to pre-releases, Developers
  merge from v2_dev branch into v2_stable one, and manually trigger a build.

  * metpx-sr3 -- on demand build sr3 packages from *stable* branch.
  * metpx-sr3-old -- on demand build sr3 packages from *stable_py36* branch.
  * metpx-sarracenia-release -- on deman build v2 packages from *v2_stable* branch.

for more discussion see `Which Version is stable <https://github.com/MetPX/sarracenia/issues/139>`_



Automated Build
~~~~~~~~~~~~~~~

* Ensure the code mirror is updated by checking the **Import details** by checking `this page for sarracenia <https://code.launchpad.net/~ssc-hpc-chp-spc/metpx-sarracenia/+git/trunk>`_
* if the code is out of date, do **Import Now** , and wait a few minutes while it is updated.
* once the repository is upto date, proceed with the build request.
* Go to the `sarracenia release <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/sarracenia-release>`_ recipe
* Go to the `sr3 release <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sr3-release>`_ recipe
* Click on the **Request build(s)** button to create a new release
* for Sarrac, follow the procedure `here <https://github.com/MetPX/sarrac#release-process>`_
* The built packages will be available in the `metpx ppa <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx>`_


Daily Builds
~~~~~~~~~~~~

Daily builds are configured 
using `this recipe for python <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/sarracenia-daily>`_ 
and `this recipe for C <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sarrac-daily>`_ and 
are run once per day when changes to the repository occur. These packages are stored in the `metpx-daily ppa <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-daily>`_.
One can also **Request build(s)** on demand if desired.


Manual Process
++++++++++++++

The process for manually publishing packages to Launchpad ( https://launchpad.net/~ssc-hpc-chp-spc ) 
involves a more complex set of steps, and so the convenient script ``publish-to-launchpad.sh`` will 
be the easiest way to do that. Currently the only supported releases are **trusty** and **xenial**. 
So the command used is::

    publish-to-launchpad.sh sarra-v2.15.12a1 trusty xenial


However, the steps below are a summary of what the script does:

- for each distribution (precise, trusty, etc) update ``debian/changelog`` to reflect the distribution
- build the source package using::

    debuild -S -uc -us

- sign the ``.changes`` and ``.dsc`` files::

    debsign -k<key id> <.changes file>

- upload to launchpad::

    dput ppa:ssc-hpc-chp-spc/metpx-<dist> <.changes file>

**Note:** The GPG keys associated with the launchpad account must be configured
in order to do the last two steps.



Backporting a Dependency
++++++++++++++++++++++++

Example::

  backportpackage -k<key id> -s bionic -d xenial -u ppa:ssc-hpc-chp-spc/ubuntu/metpx-daily librabbitmq


Building an RPM
+++++++++++++++

This process is currently a bit clumsy, but it can provide usable RPM packages.
Example of creating a multipass image for fedora to build with::

  fractal% multipass launch -m 8g --name fed34 https://mirror.csclub.uwaterloo.ca/fedora/linux/releases/34/Cloud/x86_64/images/Fedora-Cloud-Base-34-1.2.x86_64.raw.xz
  Launched: fed34                                                                 
  fractal%

Based on https://www.redhat.com/sysadmin/create-rpm-package ...  install build-dependencies::

  sudo dnf install -y rpmdevtools rpmlint git
  git clone -b development https://github.com/MetPX/sarracenia sr3
  cd sr3

One can build a very limited sort of rpm package on an rpm based distro by
The names of the package for file magic data (to determin file types) has different names on 
ubuntu vs. redhat.  The last three lines of **dependencies** in pyproject.toml are about 
"python-magic", but on redhat/fedora >= 9, it needs to be "file-magic" instead::

   # remove last three lines of dependencies in setup.py

   * on redhat <=8: vi setup.py ;  python3 setup.py bdist_rpm

   # might work, but might need some removals also.
   * on redhat >=9: vi pyproject.toml;  python3 -m build

"python-magic", but on redhat, it needs to be "file-magic" instead::

   vi pyproject.toml

using the normal (for Redhat) rpmbuild tool::

   rpmbuild --build-in-place -bb metpx-sr3.spec

When doing this on the redhat 8, edit the metpx-sr3.spec and potentially pyproject.toml
to remove the other dependencies because there are no OS packages for: paramiko, 
watchdog, xattr, & magic. Eventually, one will have removed enough that the rpm file
will be built.

One can check if the dependencies are there like so::
  
  [ubuntu@fed39 sr3]$ rpm -qR /home/ubuntu/rpmbuild/RPMS/noarch/metpx-sr3-3.00.47-0.fc39.noarch.rpm

  /usr/bin/python3
  python(abi) = 3.12
  python3-appdirs
  python3-humanfriendly
  python3-humanize
  python3-jsonpickle
  python3-paramiko
  python3-psutil
  python3-xattr
  python3.12dist(appdirs)
  python3.12dist(humanfriendly)
  python3.12dist(humanize)
  python3.12dist(jsonpickle)
  python3.12dist(paramiko)
  python3.12dist(psutil) >= 5.3
  python3.12dist(watchdog)
  python3.12dist(xattr)
  rpmlib(CompressedFileNames) <= 3.0.4-1
  rpmlib(FileDigests) <= 4.6.0-1
  rpmlib(PartialHardlinkSets) <= 4.0.4-1
  rpmlib(PayloadFilesHavePrefix) <= 4.0-1
  rpmlib(PayloadIsZstd) <= 5.4.18-1

  [ubuntu@fed39 sr3]$

You can see all of the prefixed python3 dependencies required, as well as the recommended binary accellerator packages
are listed. Then if you install with dnf install, it will pull them all in.  Unfortunately, this method does not allow
the specification of version of the python dependencies which are stripped out. on Fedora 34, this is not a problem,
as all versions are new enough.  Such a package should install well.

After installation, one can supplement, installing missing dependencies using pip (or pip3.)
Can check how much sr3 is working using *sr3 features* and use pip to add more features
after the RPM is installed.


Building a Windows Installer
----------------------------

One can also build a Windows installer with that 
`script <https://github.com/MetPX/sarracenia/blob/stable/generate-win-installer.sh>`_.
It needs to be run from a Linux OS (preferably Ubuntu 18) in the root directory of Sarracenia's git. 
find the python version in use::

    fractal% python -V
    Python 3.10.12
    fractal%

So this is python 3.10.  Only a single minor version will have the embedded package needed
by pynsist to build the executable, so look at::

    https://www.python.org/downloads/windows/

Then go look on python.org, for the "right" version (for 3.10, it is 3.10.11 )
It will contain *embed* in the file names. Once you find the correct version
From the shell, run::

   sudo apt install nsis
   pip3 install pynsist wheel
   ./generate-win-installer.sh 3.10.11 2>&1 > log.txt

The final package will be generated into *build/nsis* directory. Sometimes editing of 
the *generate-win-installer.sh* script is needed to add *--no-isolation* to the *python -m build* line.
It's not clear when that is needed.


github
------

* Click on Releases
* Click on tags, pick the tag for the new release vXX.yy.zzrcw
* Click on Pre-Release tag at the bottom if appropriate.
* Click on Generate Release notes... Review.
* copy/paste of Installation bit at the end from a previous release.
* Save as Draft.
* build packages locally or download from other sources.
  drag and drop into the release.
* Publish.

This will give us the ability to have old versions available.
launchpad.net doesn't seem to keep old versions around.


Troubleshooting
---------------



ubuntu 18
---------

trying to upload from ubuntu 18 vm::

  buntu@canny-tick:~/sr3$ twine upload dist/metpx_sr3-3.0.53rc2-py3-none-any.whl
  /usr/lib/python3/dist-packages/requests/__init__.py:80: RequestsDependencyWarning: urllib3 (1.26.18) or chardet (3.0.4) doesn't match a supported version!
    RequestsDependencyWarning)
  Uploading distributions to https://upload.pypi.org/legacy/
  Uploading metpx_sr3-3.0.53rc2-py3-none-any.whl
  100%|██████████████████████████████████████████████████████████████████████████████████████████████████| 408k/408k [00:00<00:00, 120kB/s]
  HTTPError: 400 Client Error: '2.0' is not a valid metadata version. See https://packaging.python.org/specifications/core-metadata for more information. for url: https://upload.pypi.org/legacy/
  ubuntu@canny-tick:~/sr3$ 

I uploaded from redhat8 instead. used pip3 to install twine on redhat, and that was ok.  This could be a result
of running the system provided python3-twine on ubuntu.

