
====================================
 MetPX-Sarracenia Developer's Guide
====================================

:version: @Version@
:date: @Date@

.. contents::


Tools you Need
--------------

To hack on the sarracenia source, you need:

- python3. The application is developed in and depends on python versions > 3.
- some python-amqp bindings (like python-amqplib for current implementations)
- a bunch of other modules indicated in the dependencies (setup.py or debian/control)
- paramiko. For SSH/SFTP support you need to install the python-paramiko package (which
  works with python3 even though the documentation says it is for python2.)
- python3 pyftpdlib module, used to run an ftpserver on a high port during the flow test.
- git. in order to download the source from the github repository.
- a dedicated rabbitmq broker, with administrative access, to run the flow_test.
  The flow test creates and destroys exchanges and will disrupt any active flows on the broker.

after you have cloned the source code::

    git clone https://github.com/MetPX/sarracenia sarracenia
    git clone https://github.com/MetPX/sarrac sarrac
    cd sarracenia

The rest of the Guide assumes you are there.

Documentation
-------------

The development process is to write up what one intends to do or have done into
a restructured text file in the doc/design sub-directory.  The files there provide
a basis for discussion. Ideally, the information there acts as a pieces which can
be edited into documentation for the features as they are implemented.

Each new component sr\_whatever, should have relevant man pages implemented.
The Guides should also be revised to reflect additions or changes:

- `Install.rst <Install.rst>`_ (Installation)
- `Dev.rst <Dev.rst>`_ (this guide for developers)
- `Subscribers.rst <Subscribers.rst>`_ (a guide for how to read data from a pump.)
- `Source.rst <Source.rst>`_ (a guide for those publishing data to a pump.)
- `Admin.rst <Admin.rst>`_ (an Admininistrator´s Guide.)

When there are new sections, they should likely start out in design/ and after
review, graduate into the main documentation.  

The French documentation has the same file names as the English, but it placed
under the fr/ sub-directory.  It's easiest if the documentation is produced in 
both languages at once. At least use an auto translation tool (such as 
www.deepl.com) to provide a starting point. (and same procedure in reverse 
for Francophones.)


Where to Put Options 
~~~~~~~~~~~~~~~~~~~~

Most options are documented in sr_subscribe(1), which is kind of a *parent* to all other consuming components.
Any options used by multiple components should be documented there. Options which are unique to a
single component should be documented in the man page for that component.

Where the default value for an option varies among components, each component's man page should indicate 
the option's default for that component. Sr_sarra, sr_winnow, sr_shovel, and sr_report components which
only exist because they use the base sr_subscribe with different defaults. There is no code difference
between them.


Development
-----------

Development occurs on the master branch, which may be in any state at any given
time, and should not be relied upon.  From time to time releases are tagged, and
maintenance results in a branch.  Releases are classified as follows:

Alpha
  Snapshot releases taken directly from master, with no other qualitative guarantees.
  No guarantee of functionality, some components may be partially implemented, some
  breakage may occur.
  No bug-fixes, issues addressed by subsequent version.
  Often used for early end-to-end testing (rather than installing custom from tree on
  each test machine.)

Beta
  Feature Complete for a given release.  Components in their final form for this release.
  Documentation exists in at least one language.
  All previously known release block bugs addressed.
  No bug-fixes, issues addressed by subsequent version.

RC - Release Candidate.
  Implies it has gone through beta to identify and address major issues.
  Translated documentation available.
  No bug-fixes, issues addressed by subsequent version.

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

      Changing the default requires the removal and recreation of the resource.
      This has a major impact on processes...


Python Wheel
~~~~~~~~~~~~

For testing and development::

    python3 setup.py bdist_wheel

Should build a wheel in the dist sub-directory.


Debian/Ubuntu
~~~~~~~~~~~~~

This process builds a local .deb in the parent directory using standard debian mechanisms.
- Check the **build-depends** line in *debian/control* for dependencies that might be needed to build from source.
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



Flow Test Description
---------------------

Before committing code to the master branch, as a Quality Assurance measure, one should run 
all available self-tests. It is assumed that the specific changes in the code have already been unit
tested. Please add self-tests as appropriate to this process to reflect the new ones.

A typical development workflow will be::

   cd sarra ; *make coding changes*
   cd ..
   debuild -uc -us
   cd ../sarrac
   debuild -uc -us
   sudo dpkg -i ../*.deb
   cd ../sarracenia/test
   ./flow_cleanup.sh
   rm directories with state (indicated by flow_cleanup.sh)
   ./flow_setup.sh  ; *starts the flows*
   ./flow_limit.sh  ; *stops the flows after some period (default: 1000) *
   ./flow_check.sh  ; *checks the flows*
   ./flow_cleanup.sh  ; *cleans up the flows*
   
As part of the flow_setup.sh, various unit_test are run (located in the test/unit_tests
sub-directory.) The flow tests can then indicate if there is an issue
with the modification.

The configuration one is trying to replicate:

.. image:: Flow_test.svg


Python Flow Coverage
~~~~~~~~~~~~~~~~~~~~

Following table describes what each element of the flow test does, and the test coverage
shows functionality covered.

+-------------------+--------------------------------------+-------------------------------------+
|                   |                                      |                                     | 
| Configuration     | Does                                 | Test Coverage                       | 
|                   |                                      |                                     | 
+-------------------+--------------------------------------+-------------------------------------+
| subscribe t_ddx   | copy from data mart to local broker  | read amqps public data mart (v02)   | 
|                   | posting messages to local xwinnow00  | as ordinary user.                   | 
|                   | and xwinnow01 exchanges.             |                                     | 
|                   |                                      | shared queue and multiple processes | 
|                   |                                      | 3 instances download from each q    | 
|                   |                                      |                                     | 
|                   |                                      | post amqp to a local exchange (v02) | 
|                   |                                      | as feeder(admin) user               | 
|                   |                                      |                                     | 
|                   |                                      | post_exchange_split to xwinnow0x    | 
+-------------------+--------------------------------------+-------------------------------------+
| winnow t0x_f10    | winnow processing publish for xsarra | read local amqp v02                 | 
|                   | exchange for downloading.            | as feeder user.                     | 
|                   |                                      |                                     | 
|                   |                                      | complete caching (winnow) function  | 
|                   | as two sources identical, only half  |                                     | 
|                   | messages received are posted to next | post amqp v02 to local excchange.   | 
+-------------------+--------------------------------------+-------------------------------------+
| sarra download    | download the winnowed data from the  | read local amqp v02 (xsarra)        | 
| f20               | data mart to a local directory       |                                     | 
|                   | (TESTDOCROOT= ~/sarra_devdocroot)    | download using built-in python      |
|                   |                                      |                                     | 
|                   | add a header at application layer    | shared queue and multiple processes | 
|                   | longer than 255 characters.          | 5 instances download from each q    | 
|                   |                                      |                                     | 
|                   |                                      | download using accel_wget plugin    | 
|                   |                                      |                                     | 
|                   |                                      | AMQP header truncation on publish.  | 
|                   |                                      |                                     | 
|                   |                                      | post amqp v02 to xpublic            | 
|                   |                                      | as feeder user                      | 
|                   |                                      | as http downloads from localhost    | 
+-------------------+--------------------------------------+-------------------------------------+
| subscribe t       | download as client from localhost    | read amqp from local broker         | 
|                   | to downloaded_by_sub_t directory.    | as ordinary user/client.            | 
|                   |                                      |                                     | 
|                   |                                      | shared queue and multiple processes | 
|                   |                                      | 5 instances download from each q    | 
|                   |                                      |                                     | 
+-------------------+--------------------------------------+-------------------------------------+
| watch f40         | watch downloaded_by_sub_t            | client v03 post of local file.      | 
|                   | (post each file that appears there.) | (file: url)                         | 
|                   |                                      |                                     | 
|                   | memory ceiling set low               | auto restarting on memory ceiling.  | 
|                   |                                      |                                     | 
+-------------------+--------------------------------------+-------------------------------------+
| sender            | read local file, send via sftp       | client consume v03 post.            | 
| tsource2send      | to sent_by_tsource2send directory    |                                     | 
|                   |                                      | consumer read local file.           | 
|                   | post to xs_tsource_output            |                                     | 
|                   |                                      | send via sftp.                      | 
|                   |                                      |                                     | 
|                   |                                      | plugin replace_dir                  | 
|                   |                                      |                                     | 
|                   |                                      | posting sftp url.                   | 
|                   |                                      | post v02 (converting v03 back.)     | 
|                   |                                      |                                     | 
|                   |                                      | test post_exchange_suffix option.   | 
+-------------------+--------------------------------------+-------------------------------------+
| subscribe         | download via sftp from localhost     | client sftp download.               | 
| u_sftp_f60        | putting files in downloaded_by_sub_u |                                     | 
|                   | directory.                           | accel_sftp plugin.                  | 
|                   |                                      |                                     | 
+-------------------+--------------------------------------+-------------------------------------+
| post test2_f61    | post files in sent_by_tsource2send   | explicit file posting               | 
|                   | with ftp URL's in the                |                                     | 
|                   | xs_tsource_poll exchange             | ftp URL posting.                    | 
|                   |                                      |                                     | 
|                   | (wrapper script calls post)          | post_exchange_suffix option         | 
+-------------------+--------------------------------------+-------------------------------------+
| poll f62          | poll sent_by_tsource2send directory  | polling                             | 
|                   | posting sftp download URL's          |                                     | 
|                   |                                      | post_exchange_suffix option         | 
|                   |                                      |                                     | 
+-------------------+--------------------------------------+-------------------------------------+
| subscribe ftp_f70 | subscribe to test2_f61 ftp' posts.   | ftp url downloading.                | 
|                   | download files from localhost        |                                     | 
|                   | to downloaded_by_sub_u directory.    |                                     | 
|                   |                                      |                                     | 
+-------------------+--------------------------------------+-------------------------------------+
| subscribe q_f71   | subscribe to poll, downloading       | confirming poll post quality.       | 
|                   | to recd_by_srpoll_test1              |                                     | 
+-------------------+--------------------------------------+-------------------------------------+
| shovel pclean f90 | clean up files so they don't         | shovel function.                    | 
|                   | accumulate                           |                                     | 
|                   | fakes failures to exercise retries   |                                     | 
|                   |                                      | retry logic.                        | 
|                   |                                      |                                     | 
+-------------------+--------------------------------------+-------------------------------------+
| shovel pclean f91 | clean up files so they don't         | shovel with posting v03             | 
|                   | accumulate                           |                                     | 
|                   |                                      | retry logic.                        | 
+-------------------+--------------------------------------+-------------------------------------+
| shovel pclean f92 | clean up files so they don't         | shovel with consuming v03           | 
|                   | accumulate                           |                                     | 
|                   |                                      | posting v02.                        | 
|                   |                                      |                                     | 
|                   |                                      | retry logic.                        | 
+-------------------+--------------------------------------+-------------------------------------+

Assumption: test environment is a Linux PC, either a laptop/desktop, or a server on which one
can start a browser. If working with the c implementation as well, there are also the following
flows defined:

.. image:: cFlow_test.svg

   
Running Flow Test
-----------------

This section documents these steps in much more detail.  
Before one can run the flow_test, some pre-requisites must be taken care of.

Local Installation on Workstation
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


Install Servers on Workstation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install a minimal localhost broker, configure test users.
With credentials stored for localhost::

     sudo apt-get install rabbitmq-server
     sudo rabbitmq-plugins enable rabbitmq_management
     echo "amqp://bunnymaster:MaestroDelConejito@localhost/" >>~/.config/sarra/credentials.conf
     echo "amqp://tsource:TestSOUrCs@localhost/" >>~/.config/sarra/credentials.conf
     echo "amqp://tsub:TestSUBSCibe@localhost/" >>~/.config/sarra/credentials.conf
     echo "amqp://tfeed:TestFeeding@localhost/" >>~/.config/sarra/credentials.conf
     echo "amqp://anoymous:anonymous@dd.weather.gc.ca" >>~/.config/sarra/credentials.conf
     echo "ftp://anonymous:anonymous@localhost:2121/" >>~/.config/sarra/credentials.conf

     cat >~/.config/sarra/admin.conf <<EOT

     broker amqp://tfeed@localhost/
     cluster localhost
     admin amqp://bunnymaster@localhost/
     feeder amqp://tfeed@localhost/
     declare source tsource
     declare subscriber tsub
     declare subscriber anonymous
     EOT

     sudo rabbitmqctl delete_user guest
     sudo rabbitmqctl add_user bunnymaster MaestroDelConejito
     sudo rabbitmqctl set_permissions bunnymaster ".*" ".*" ".*"
     sudo rabbitmqctl set_user_tags bunnymaster administrator
     
     systemctl restart rabbitmq-server
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


Setup Flow Test Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~

One part of the flow test runs an sftp server, and uses sftp client functions.
Need the following package for that::

    sudo apt-get install python3-pyftpdlib python3-paramiko

The setup script starts a trivial web server, and ftp server, and a daemon that invokes sr_post.
It also tests the C components, which need to have been already installed as well 
and defines some fixed test clients that will be used during self-tests::

    cd sarracenia/test
    . ./flow_setup.sh
    
    blacklab% ./flow_setup.sh
    cleaning logs, just in case
    rm: cannot remove '/home/peter/.cache/sarra/log/*': No such file or directory
    Adding flow test configurations...
    2018-02-10 14:22:58,944 [INFO] copying /usr/lib/python3/dist-packages/sarra/examples/cpump/cno_trouble_f00.inc to /home/peter/.config/sarra/cpump/cno_trouble_f00.inc.
    2018-02-10 09:22:59,204 [INFO] copying /home/peter/src/sarracenia/sarra/examples/shovel/no_trouble_f00.inc to /home/peter/.config/sarra/shovel/no_trouble_f00.inc
    2018-02-10 14:22:59,206 [INFO] copying /usr/lib/python3/dist-packages/sarra/examples/cpost/veille_f34.conf to /home/peter/.config/sarra/cpost/veille_f34.conf.
    2018-02-10 14:22:59,207 [INFO] copying /usr/lib/python3/dist-packages/sarra/examples/cpump/pelle_dd1_f04.conf to /home/peter/.config/sarra/cpump/pelle_dd1_f04.conf.
    2018-02-10 14:22:59,208 [INFO] copying /usr/lib/python3/dist-packages/sarra/examples/cpump/pelle_dd2_f05.conf to /home/peter/.config/sarra/cpump/pelle_dd2_f05.conf.
    2018-02-10 14:22:59,208 [INFO] copying /usr/lib/python3/dist-packages/sarra/examples/cpump/xvan_f14.conf to /home/peter/.config/sarra/cpump/xvan_f14.conf.
    2018-02-10 14:22:59,209 [INFO] copying /usr/lib/python3/dist-packages/sarra/examples/cpump/xvan_f15.conf to /home/peter/.config/sarra/cpump/xvan_f15.conf.
    2018-02-10 09:22:59,483 [INFO] copying /home/peter/src/sarracenia/sarra/examples/poll/f62.conf to /home/peter/.config/sarra/poll/f62.conf
    2018-02-10 09:22:59,756 [INFO] copying /home/peter/src/sarracenia/sarra/examples/post/shim_f63.conf to /home/peter/.config/sarra/post/shim_f63.conf
    2018-02-10 09:23:00,030 [INFO] copying /home/peter/src/sarracenia/sarra/examples/post/test2_f61.conf to /home/peter/.config/sarra/post/test2_f61.conf
    2018-02-10 09:23:00,299 [INFO] copying /home/peter/src/sarracenia/sarra/examples/report/tsarra_f20.conf to /home/peter/.config/sarra/report/tsarra_f20.conf
    2018-02-10 09:23:00,561 [INFO] copying /home/peter/src/sarracenia/sarra/examples/report/twinnow00_f10.conf to /home/peter/.config/sarra/report/twinnow00_f10.conf
    2018-02-10 09:23:00,824 [INFO] copying /home/peter/src/sarracenia/sarra/examples/report/twinnow01_f10.conf to /home/peter/.config/sarra/report/twinnow01_f10.conf
    2018-02-10 09:23:01,086 [INFO] copying /home/peter/src/sarracenia/sarra/examples/sarra/download_f20.conf to /home/peter/.config/sarra/sarra/download_f20.conf
    2018-02-10 09:23:01,350 [INFO] copying /home/peter/src/sarracenia/sarra/examples/sender/tsource2send_f50.conf to /home/peter/.config/sarra/sender/tsource2send_f50.conf
    2018-02-10 09:23:01,615 [INFO] copying /home/peter/src/sarracenia/sarra/examples/shovel/t_dd1_f00.conf to /home/peter/.config/sarra/shovel/t_dd1_f00.conf
    2018-02-10 09:23:01,877 [INFO] copying /home/peter/src/sarracenia/sarra/examples/shovel/t_dd2_f00.conf to /home/peter/.config/sarra/shovel/t_dd2_f00.conf
    2018-02-10 09:23:02,137 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/cclean_f91.conf to /home/peter/.config/sarra/subscribe/cclean_f91.conf
    2018-02-10 09:23:02,400 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/cdnld_f21.conf to /home/peter/.config/sarra/subscribe/cdnld_f21.conf
    2018-02-10 09:23:02,658 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/cfile_f44.conf to /home/peter/.config/sarra/subscribe/cfile_f44.conf
    2018-02-10 09:23:02,921 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/clean_f90.conf to /home/peter/.config/sarra/subscribe/clean_f90.conf
    2018-02-10 09:23:03,185 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/cp_f61.conf to /home/peter/.config/sarra/subscribe/cp_f61.conf
    2018-02-10 09:23:03,455 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/ftp_f70.conf to /home/peter/.config/sarra/subscribe/ftp_f70.conf
    2018-02-10 09:23:03,715 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/q_f71.conf to /home/peter/.config/sarra/subscribe/q_f71.conf
    2018-02-10 09:23:03,978 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/t_f30.conf to /home/peter/.config/sarra/subscribe/t_f30.conf
    2018-02-10 09:23:04,237 [INFO] copying /home/peter/src/sarracenia/sarra/examples/subscribe/u_sftp_f60.conf to /home/peter/.config/sarra/subscribe/u_sftp_f60.conf
    2018-02-10 09:23:04,504 [INFO] copying /home/peter/src/sarracenia/sarra/examples/watch/f40.conf to /home/peter/.config/sarra/watch/f40.conf
    2018-02-10 09:23:04,764 [INFO] copying /home/peter/src/sarracenia/sarra/examples/winnow/t00_f10.conf to /home/peter/.config/sarra/winnow/t00_f10.conf
    2018-02-10 09:23:05,027 [INFO] copying /home/peter/src/sarracenia/sarra/examples/winnow/t01_f10.conf to /home/peter/.config/sarra/winnow/t01_f10.conf
    Initializing with sr_audit... takes a minute or two
    OK, as expected 18 queues existing after 1st audit
    OK, as expected 31 exchanges for flow test created.
    Starting trivial http server on: /home/peter/sarra_devdocroot, saving pid in .httpserverpid
    Starting trivial ftp server on: /home/peter/sarra_devdocroot, saving pid in .ftpserverpid
    running self test ... takes a minute or two
    sr_util.py TEST PASSED
    sr_credentials.py TEST PASSED
    sr_config.py TEST PASSED
    sr_cache.py TEST PASSED
    sr_retry.py TEST PASSED
    sr_consumer.py TEST PASSED
    sr_http.py TEST PASSED
    sftp testing start...
    sftp testing config read...
    sftp testing fake message built ...
    sftp sr_ftp instantiated ...
    sftp sr_ftp connected ...
    sftp sr_ftp mkdir ...
    test 01: directory creation succeeded
    test 02: file upload succeeded
    test 03: file rename succeeded
    test 04: getting a part succeeded
    test 05: download succeeded
    test 06: onfly_checksum succeeded
    Sent: bbb  into tztz/ddd 0-5
    test 07: download succeeded
    test 08: delete succeeded
    Sent: bbb  into tztz/ddd 0-5
    Sent: bbb  into tztz/ddd 0-5
    Sent: bbb  into tztz/ddd 0-5
    Sent: bbb  into tztz/ddd 0-5
    Sent: bbb  into tztz/ddd 0-5
    /home/peter
    /home/peter
    test 09: bad part succeeded
    sr_sftp.py TEST PASSED
    sr_instances.py TEST PASSED
    OK, as expected 9 tests passed
    Starting flow_post on: /home/peter/sarra_devdocroot, saving pid in .flowpostpid
    Starting up all components (sr start)...
    done.
    OK: sr start was successful
    Overall PASSED 4/4 checks passed!
    blacklab% 


As it runs the setup, it also executes all existing unit_tests.
Only proceed to the flow_check tests if all the tests in flow_setup.sh pass.



Run Flow Test
~~~~~~~~~~~~~

The flow_check.sh script reads the log files of all the components started, and compares the number
of messages, looking for a correspondence within +- 10%   It takes a few minutes for the
configuration to run before there is enough data to do the proper measurements::

     ./flow_limit.sh

sample output::

    initial sample building sample size 8 need at least 1000 
    sample now   1021 
    Sufficient!
    stopping shovels and waiting...
    2017-10-28 00:37:02,422 [INFO] sr_shovel t_dd1_f00 0001 stopping
    2017-10-28 04:37:02,435 [INFO] 2017-10-28 04:37:02,435 [INFO] info: instances option not implemented, ignored.
    info: instances option not implemented, ignored.
    2017-10-28 04:37:02,435 [INFO] 2017-10-28 04:37:02,435 [INFO] info: report_back option not implemented, ignored.
    info: report_back option not implemented, ignored.
    2017-10-28 00:37:02,436 [INFO] sr_shovel t_dd2_f00 0001 stopping
    running instance for config pelle_dd1_f04 (pid 15872) stopped.
    running instance for config pelle_dd2_f05 (pid 15847) stopped.
        maximum of the shovels is: 1022


Then check show it went with flow_check.sh::

    TYPE OF ERRORS IN LOG :

      1 /home/peter/.cache/sarra/log/sr_cpump_xvan_f14_001.log [ERROR] binding failed: server channel error 404h, message: NOT_FOUND - no exchange 'xcvan00' in vhost '/'
      1 /home/peter/.cache/sarra/log/sr_cpump_xvan_f15_001.log [ERROR] binding failed: server channel error 404h, message: NOT_FOUND - no exchange 'xcvan01' in vhost '/'

    
    test  1 success: shovels t_dd1_f00 ( 1022 ) and t_dd2_f00 ( 1022 ) should have about the same number of items read
    test  2 success: sarra tsarra (1022) should be reading about half as many items as (both) winnows (2240)
    test  3 success: tsarra (1022) and sub t_f30 (1022) should have about the same number of items
    test  4 success: max shovel (1022) and subscriber t_f30 (1022) should have about the same number of items
    test  5 success: count of truncated headers (1022) and subscribed messages (1022) should have about the same number of items
    test  6 success: count of downloads by subscribe t_f30 (1022) and messages received (1022) should be about the same
    test  7 success: downloads by subscribe t_f30 (1022) and files posted by sr_watch (1022) should be about the same
    test  8 success: posted by watch(1022) and sent by sr_sender (1022) should be about the same
    test  9 success: 1022 of 1022: files sent with identical content to those downloaded by subscribe
    test 10 success: 1022 of 1022: poll test1_f62 and subscribe q_f71 run together. Should have equal results.
    test 11 success: post test2_f61 1022 and subscribe r_ftp_f70 1021 run together. Should be about the same.
    test 12 success: cpump both pelles (c shovel) should receive about the same number of messages (3665) (3662)
    test 13 success: cdnld_f21 subscribe downloaded (1022) the same number of files that was published by both van_14 and van_15 (1022)
    test 14 success: veille_f34 should post the same number of files (1022) that subscribe cdnld_f21 downloaded (1022)
    test 15 success: veille_f34 should post the same number of files (1022) that subscribe cfile_f44 downloaded (1022)
    test 16 success: Overall 15 of 15 passed!

    blacklab% 

If the flow_check.sh passes, then one has a reasonable confidence in the overall functionality of the 
python application, but the test coverage is not exhaustive. This is the lowest gate for committing
changes to thy python code into the master branch. It is more qualitative sampling of the most
common use cases rather than a thorough examination of all functionality. While not
thorough, it is good to know the flows are working.

(As of Nov. 2017) NOTE:  the packages (deb+pip) are created with a dependency for python3-amqplib for the AMQP support.
We want to migrate to python3-pika. Therefore, the programs now supports both AMQP api. Should you have python3-pika
installed, it will be used as default. If you have both amqplib and pika installed, you can use the option::

*use_pika [true/false]*

To use pika or not. Should you set use_pika to True and python3-pika not installed, the programs will fall back to
amqplib.  The developers should test both API until we are totally migrated to PIKA.

Note that the *fclean* subscriber looks at files in and keeps files around long enough for them to go through all the other
tests.  It does this by waiting a reasonable amount of time (45 seconds, the last time checked.) then it compares the file
that have been posted by sr_watch to the files created by downloading from it.  As the *sample now* count proceeds,
it prints "OK" if the files downloaded are identical to the ones posted by sr_watch.   The addition of fclean and
the corresponding cfclean for the cflow_test, are broken.  The default setup which uses *fclean* and *cfclean* ensures
that only a few minutes worth of disk space is used at a given time, and allows for much longer tests.

By default, the flow_test is only 1000 files, but one can ask it to run longer, like so::

 ./flow_limit.sh 50000

To accumulate fifty thousand files before ending the test.  This allows testing of long term performance, especially
memory usage over time, and the housekeeping functions of on_heartbeat processing.


Flow Cleanup
~~~~~~~~~~~~

When done testing, run the ./flow_cleanup.sh script, which will kill the running servers and daemons, and 
delete all configuration files installed for the flow test, all queues, exchanges, and logs.  This also 
needs to be done between each run of the flow test::
  
  blacklab% ./flow_cleanup.sh
  Stopping sr...
  Cleanup sr...
  Cleanup trivial http server... 
  web server stopped.
  if other web servers with lost pid kill them
  Cleanup trivial ftp server... 
  ftp server stopped.
  if other ftp servers with lost pid kill them
  Cleanup flow poster... 
  flow poster stopped.
  if other flow_post.sh with lost pid kill them
  Deleting queues: 
  Deleting exchanges...
  Removing flow configs...
  2018-02-10 14:17:34,150 [INFO] info: instances option not implemented, ignored.
  2018-02-10 14:17:34,150 [INFO] info: report_back option not implemented, ignored.
  2018-02-10 14:17:34,353 [INFO] info: instances option not implemented, ignored.
  2018-02-10 14:17:34,353 [INFO] info: report_back option not implemented, ignored.
  2018-02-10 09:17:34,837 [INFO] sr_poll f62 cleanup
  2018-02-10 09:17:34,845 [INFO] deleting exchange xs_tsource_poll (tsource@localhost)
  2018-02-10 09:17:35,115 [INFO] sr_post shim_f63 cleanup
  2018-02-10 09:17:35,122 [INFO] deleting exchange xs_tsource_shim (tsource@localhost)
  2018-02-10 09:17:35,394 [INFO] sr_post test2_f61 cleanup
  2018-02-10 09:17:35,402 [INFO] deleting exchange xs_tsource_post (tsource@localhost)
  2018-02-10 09:17:35,659 [INFO] sr_report tsarra_f20 cleanup
  2018-02-10 09:17:35,659 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:35,661 [INFO] deleting queue q_tfeed.sr_report.tsarra_f20.89336558.04455188 (tfeed@localhost)
  2018-02-10 09:17:35,920 [INFO] sr_report twinnow00_f10 cleanup
  2018-02-10 09:17:35,920 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:35,922 [INFO] deleting queue q_tfeed.sr_report.twinnow00_f10.35552245.50856337 (tfeed@localhost)
  2018-02-10 09:17:36,179 [INFO] sr_report twinnow01_f10 cleanup
  2018-02-10 09:17:36,180 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:36,182 [INFO] deleting queue q_tfeed.sr_report.twinnow01_f10.48262886.11567358 (tfeed@localhost)
  2018-02-10 09:17:36,445 [WARNING] option url deprecated please use post_base_url
  2018-02-10 09:17:36,446 [WARNING] use post_base_dir instead of document_root
  2018-02-10 09:17:36,446 [INFO] sr_sarra download_f20 cleanup
  2018-02-10 09:17:36,446 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:36,448 [INFO] deleting queue q_tfeed.sr_sarra.download_f20 (tfeed@localhost)
  2018-02-10 09:17:36,449 [INFO] exchange xpublic remains
  2018-02-10 09:17:36,703 [INFO] sr_sender tsource2send_f50 cleanup
  2018-02-10 09:17:36,703 [INFO] AMQP  broker(localhost) user(tsource) vhost(/)
  2018-02-10 09:17:36,705 [INFO] deleting queue q_tsource.sr_sender.tsource2send_f50 (tsource@localhost)
  2018-02-10 09:17:36,711 [INFO] deleting exchange xs_tsource_output (tsource@localhost)
  2018-02-10 09:17:36,969 [INFO] sr_shovel t_dd1_f00 cleanup
  2018-02-10 09:17:36,969 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2018-02-10 09:17:37,072 [INFO] deleting queue q_anonymous.sr_shovel.t_dd1_f00 (anonymous@dd.weather.gc.ca)
  2018-02-10 09:17:37,095 [INFO] exchange xwinnow00 remains
  2018-02-10 09:17:37,095 [INFO] exchange xwinnow01 remains
  2018-02-10 09:17:37,389 [INFO] sr_shovel t_dd2_f00 cleanup
  2018-02-10 09:17:37,389 [INFO] AMQP  broker(dd.weather.gc.ca) user(anonymous) vhost(/)
  2018-02-10 09:17:37,498 [INFO] deleting queue q_anonymous.sr_shovel.t_dd2_f00 (anonymous@dd.weather.gc.ca)
  2018-02-10 09:17:37,522 [INFO] exchange xwinnow00 remains
  2018-02-10 09:17:37,523 [INFO] exchange xwinnow01 remains
  2018-02-10 09:17:37,804 [INFO] sr_subscribe cclean_f91 cleanup
  2018-02-10 09:17:37,804 [INFO] AMQP  broker(localhost) user(tsub) vhost(/)
  2018-02-10 09:17:37,806 [INFO] deleting queue q_tsub.sr_subscribe.cclean_f91.39328538.44917465 (tsub@localhost)
  2018-02-10 09:17:38,062 [INFO] sr_subscribe cdnld_f21 cleanup
  2018-02-10 09:17:38,062 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:38,064 [INFO] deleting queue q_tfeed.sr_subscribe.cdnld_f21.11963392.61638098 (tfeed@localhost)
  2018-02-10 09:17:38,324 [WARNING] use post_base_dir instead of document_root
  2018-02-10 09:17:38,324 [INFO] sr_subscribe cfile_f44 cleanup
  2018-02-10 09:17:38,324 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:38,326 [INFO] deleting queue q_tfeed.sr_subscribe.cfile_f44.56469334.87337271 (tfeed@localhost)
  2018-02-10 09:17:38,583 [INFO] sr_subscribe clean_f90 cleanup
  2018-02-10 09:17:38,583 [INFO] AMQP  broker(localhost) user(tsub) vhost(/)
  2018-02-10 09:17:38,585 [INFO] deleting queue q_tsub.sr_subscribe.clean_f90.45979835.20516428 (tsub@localhost)
  2018-02-10 09:17:38,854 [WARNING] extended option download_cp_command = ['cp --preserve=timestamps'] (unknown or not declared)
  2018-02-10 09:17:38,855 [INFO] sr_subscribe cp_f61 cleanup
  2018-02-10 09:17:38,855 [INFO] AMQP  broker(localhost) user(tsource) vhost(/)
  2018-02-10 09:17:38,857 [INFO] deleting queue q_tsource.sr_subscribe.cp_f61.61218922.69758215 (tsource@localhost)
  2018-02-10 09:17:39,121 [INFO] sr_subscribe ftp_f70 cleanup
  2018-02-10 09:17:39,121 [INFO] AMQP  broker(localhost) user(tsource) vhost(/)
  2018-02-10 09:17:39,123 [INFO] deleting queue q_tsource.sr_subscribe.ftp_f70.47997098.27633529 (tsource@localhost)
  2018-02-10 09:17:39,386 [INFO] sr_subscribe q_f71 cleanup
  2018-02-10 09:17:39,386 [INFO] AMQP  broker(localhost) user(tsource) vhost(/)
  2018-02-10 09:17:39,389 [INFO] deleting queue q_tsource.sr_subscribe.q_f71.84316550.21567557 (tsource@localhost)
  2018-02-10 09:17:39,658 [INFO] sr_subscribe t_f30 cleanup
  2018-02-10 09:17:39,658 [INFO] AMQP  broker(localhost) user(tsub) vhost(/)
  2018-02-10 09:17:39,660 [INFO] deleting queue q_tsub.sr_subscribe.t_f30.26453890.50752396 (tsub@localhost)
  2018-02-10 09:17:39,924 [INFO] sr_subscribe u_sftp_f60 cleanup
  2018-02-10 09:17:39,924 [INFO] AMQP  broker(localhost) user(tsource) vhost(/)
  2018-02-10 09:17:39,927 [INFO] deleting queue q_tsource.sr_subscribe.u_sftp_f60.81353341.03950190 (tsource@localhost)
  2018-02-10 09:17:40,196 [WARNING] option url deprecated please use post_base_url
  2018-02-10 09:17:40,196 [WARNING] use post_broker to set broker
  2018-02-10 09:17:40,197 [INFO] sr_watch f40 cleanup
  2018-02-10 09:17:40,207 [INFO] deleting exchange xs_tsource (tsource@localhost)
  2018-02-10 09:17:40,471 [INFO] sr_winnow t00_f10 cleanup
  2018-02-10 09:17:40,471 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:40,474 [INFO] deleting queue q_tfeed.sr_winnow.t00_f10 (tfeed@localhost)
  2018-02-10 09:17:40,480 [INFO] deleting exchange xsarra (tfeed@localhost)
  2018-02-10 09:17:40,741 [INFO] sr_winnow t01_f10 cleanup
  2018-02-10 09:17:40,741 [INFO] AMQP  broker(localhost) user(tfeed) vhost(/)
  2018-02-10 09:17:40,743 [INFO] deleting queue q_tfeed.sr_winnow.t01_f10 (tfeed@localhost)
  2018-02-10 09:17:40,750 [INFO] deleting exchange xsarra (tfeed@localhost)
  2018-02-10 14:17:40,753 [ERROR] config cno_trouble_f00 not found.
  Removing flow config logs...
  rm: cannot remove '/home/peter/.cache/sarra/log/sr_audit_f00.log': No such file or directory
  Removing document root ( /home/peter/sarra_devdocroot )...
  Done!


Flow Test Length
~~~~~~~~~~~~~~~~

The flow_test length defaults to 1000 files being flowed through the test cases.  when in rapid
development, one can supply an argument to shorten that::

  ./flow_test 200

Towards the end of a development cycle, longer flow_tests are adviseable::

  ./flow_test 20000 

to identify more issues. sample run to 100,000 entries::

  blacklab% ./flow_limit.sh 100000
  initial sample building sample size 155 need at least 100000 
  sample now 100003 content_checks:GOOD missed_dispositions:0s:0
  Sufficient!
  stopping shovels and waiting...
  2018-02-10 13:15:08,964 [INFO] 2018-02-10 13:15:08,964 [INFO] info: instances option not implemented, ignored.
  info: instances option not implemented, ignored.
  2018-02-10 13:15:08,964 [INFO] info: report_back option not implemented, ignored.
  2018-02-10 13:15:08,964 [INFO] info: report_back option not implemented, ignored.
  running instance for config pelle_dd2_f05 (pid 20031) stopped.
  running instance for config pelle_dd1_f04 (pid 20043) stopped.
  Traceback (most recent call last):ng...
    File "/usr/bin/rabbitmqadmin", line 1012, in <module>
      main()
    File "/usr/bin/rabbitmqadmin", line 413, in main
      method()
    File "/usr/bin/rabbitmqadmin", line 593, in invoke_list
      format_list(self.get(uri), cols, obj_info, self.options)
    File "/usr/bin/rabbitmqadmin", line 710, in format_list
      formatter_instance.display(json_list)
    File "/usr/bin/rabbitmqadmin", line 721, in display
      (columns, table) = self.list_to_table(json.loads(json_list), depth)
    File "/usr/bin/rabbitmqadmin", line 775, in list_to_table
      add('', 1, item, add_to_row)
    File "/usr/bin/rabbitmqadmin", line 742, in add
      add(column, depth + 1, subitem, fun)
    File "/usr/bin/rabbitmqadmin", line 742, in add
      add(column, depth + 1, subitem, fun)
    File "/usr/bin/rabbitmqadmin", line 754, in add
      fun(column, subitem)
    File "/usr/bin/rabbitmqadmin", line 761, in add_to_row
      row[column_ix[col]] = maybe_utf8(val)
    File "/usr/bin/rabbitmqadmin", line 431, in maybe_utf8
      return s.encode('utf-8')
  AttributeError: 'float' object has no attribute 'encode'
  maximum of the shovels is: 100008
  

While it is runnig one can run flow_check.sh at any time::

  NB retries for sr_subscribe t_f30 0
  NB retries for sr_sender 18
  
        1 /home/peter/.cache/sarra/log/sr_cpost_veille_f34_0001.log [ERROR] sr_cpost rename: /home/peter/sarra_devdocroot/cfr/observations/xml/AB/today/today_ab_20180210_e.xml cannot stat.
        1 /home/peter/.cache/sarra/log/sr_cpump_xvan_f14_0001.log [ERROR] binding failed: server channel error 404h, message: NOT_FOUND - no exchange 'xcvan00' in vhost '/'
        1 /home/peter/.cache/sarra/log/sr_cpump_xvan_f15_0001.log [ERROR] binding failed: server channel error 404h, message: NOT_FOUND - no exchange 'xcvan01' in vhost '/'
        1 /home/peter/.cache/sarra/log/sr_sarra_download_f20_0002.log [ERROR] Download failed http://dd2.weather.gc.ca//bulletins/alphanumeric/20180210/CA/CWAO/09/CACN00_CWAO_100857__WDK_10905 
        1 /home/peter/.cache/sarra/log/sr_sarra_download_f20_0002.log [ERROR] Failed to reach server. Reason: [Errno 110] Connection timed out
        1 /home/peter/.cache/sarra/log/sr_sarra_download_f20_0002.log [ERROR] Download failed http://dd2.weather.gc.ca//bulletins/alphanumeric/20180210/CA/CWAO/09/CACN00_CWAO_100857__WDK_10905. Type: <class 'urllib.error.URLError'>, Value: <urlopen error [Errno 110] Connection timed out>
        1 /home/peter/.cache/sarra/log/sr_sarra_download_f20_0004.log [ERROR] Download failed http://dd2.weather.gc.ca//bulletins/alphanumeric/20180210/SA/CYMM/09/SACN61_CYMM_100900___53321 
        1 /home/peter/.cache/sarra/log/sr_sarra_download_f20_0004.log [ERROR] Failed to reach server. Reason: [Errno 110] Connection timed out
        1 /home/peter/.cache/sarra/log/sr_sarra_download_f20_0004.log [ERROR] Download failed http://dd2.weather.gc.ca//bulletins/alphanumeric/20180210/SA/CYMM/09/SACN61_CYMM_100900___53321. Type: <class 'urllib.error.URLError'>, Value: <urlopen error [Errno 110] Connection timed out>
        1 /home/peter/.cache/sarra/log/sr_sarra_download_f20_0004.log [ERROR] Download failed http://dd2.weather.gc.ca//bulletins/alphanumeric/20180210/CS/CWEG/12/CSCN03_CWEG_101200___12074 
  more than 10 TYPES OF ERRORS found... for the rest, have a look at /home/peter/src/sarracenia/test/flow_check_errors_logged.txt for details

  test  1 success: shovels t_dd1_f00 (100008) and t_dd2_f00 (100008) should have about the same number of items read
  test  2 success: sarra tsarra (100008) should be reading about half as many items as (both) winnows (200016)
  test  3 success: tsarra (100008) and sub t_f30 (99953) should have about the same number of items
  test  4 success: max shovel (100008) and subscriber t_f30 (99953) should have about the same number of items
  test  5 success: count of truncated headers (100008) and subscribed messages (100008) should have about the same number of items
  test  6 success: count of downloads by subscribe t_f30 (99953) and messages received (100008) should be about the same
  test  7 success: same downloads by subscribe t_f30 (199906) and files posted (add+remove) by sr_watch (199620) should be about the same
  test  8 success: posted by watch(199620) and subscribed cp_f60 (99966) should be about half as many
  test  9 success: posted by watch(199620) and sent by sr_sender (199549) should be about the same
  test 10 success: 0 messages received that we don't know what happenned.
  test 11 success: sarra tsarra (100008) and good audit 99754 should be the same.
  test 12 success: poll test1_f62 94865 and subscribe q_f71 99935 run together. Should have equal results.
  test 13 success: post test2_f61 99731 and subscribe r_ftp_f70 99939 run together. Should be about the same.
  test 14 success: posts test2_f61 99731 and shim_f63 110795 Should be the same.
  test 15 success: cpump both pelles (c shovel) should receive about the same number of messages (160737) (160735)
  test 16 success: cdnld_f21 subscribe downloaded (50113) the same number of files that was published by both van_14 and van_15 (50221)
  test 17 success: veille_f34 should post twice as many files (100205) as subscribe cdnld_f21 downloaded (50113)
  test 18 success: veille_f34 should post twice as many files (100205) as subscribe cfile_f44 downloaded (49985)
  test 19 success: Overall 18 of 18 passed (sample size: 100008) !
  
  blacklab% 

This test was fired up at the end of the day, as it takes several hours, and results examined the next morning.

Flow Test Stuck
~~~~~~~~~~~~~~~

Sometimes flow tests (especially for large numbers) get stuck because of problems with the data stream (where multiple files get the same name) and so earlier versions remove later versions and then retries will always fail. Eventually, we will succeed in cleaning up the dd.weather.gc.ca stream, but for now sometimes a flow_check gets stuck 'Retrying.' The test has run all the messages required, and is at a phase of emptying out retries, but just keeps retrying forever with a variable number of items that never drops to zero.

To recover from this state without discarding the results of a long test, do::

  ^C to interrupt the flow_check.sh 100000
  blacklab% sr stop
  blacklab% cd ~/.cache/sarra
  blacklab% ls */*/*retry*
  shovel/pclean_f90/sr_shovel_pclean_f90_0001.retry        shovel/pclean_f92/sr_shovel_pclean_f92_0001.retry        subscribe/t_f30/sr_subscribe_t_f30_0002.retry.new
  shovel/pclean_f91/sr_shovel_pclean_f91_0001.retry        shovel/pclean_f92/sr_shovel_pclean_f92_0001.retry.state
  shovel/pclean_f91/sr_shovel_pclean_f91_0001.retry.state  subscribe/q_f71/sr_subscribe_q_f71_0004.retry.new
  blacklab% rm */*/*retry*
  blacklab% sr start
  blacklab% 
  blacklab%  ./flow_check.sh 100000
  Sufficient!
  stopping shovels and waiting...
  2018-04-07 10:50:16,167 [INFO] sr_shovel t_dd2_f00 0001 stopped
  2018-04-07 10:50:16,177 [INFO] sr_shovel t_dd1_f00 0001 stopped
  2018-04-07 14:50:16,235 [INFO] info: instances option not implemented, ignored.
  2018-04-07 14:50:16,235 [INFO] info: report_back option not
  implemented, ignored.
  2018-04-07 14:50:16,235 [INFO] info: instances option not implemented, ignored.
  2018-04-07 14:50:16,235 [INFO] info: report_back option not
  implemented, ignored.
  running instance for config pelle_dd1_f04 (pid 12435) stopped.
  running instance for config pelle_dd2_f05 (pid 12428) stopped.
  maximum of the shovels is: 100075
  

  blacklab% ./flow_check.sh

                   | dd.weather routing |
  test  1 success: sr_shovel (100075) t_dd1 should have the same number
  of items as t_dd2 (100068)
  test  2 success: sr_winnow (200143) should have the sum of the number
  of items of shovels (200143)
  test  3 success: sr_sarra (98075) should have the same number of items
  as winnows'post (100077)
  test  4 success: sr_subscribe (98068) should have the same number of
  items as sarra (98075)
                   | watch      routing |
  test  5 success: sr_watch (397354) should be 4 times subscribe t_f30 (98068)
  test  6 success: sr_sender (392737) should have about the same number
  of items as sr_watch (397354)
  test  7 success: sr_subscribe u_sftp_f60 (361172) should have the same
  number of items as sr_sender (392737)
  test  8 success: sr_subscribe cp_f61 (361172) should have the same
  number of items as sr_sender (392737)
                   | poll       routing |
  test  9 success: sr_poll test1_f62 (195408) should have half the same
  number of items of sr_sender(196368)
  test 10 success: sr_subscribe q_f71 (195406) should have about the
  same number of items as sr_poll test1_f62(195408)
                   | flow_post  routing |
  test 11 success: sr_post test2_f61 (193541) should have half the same
  number of items of sr_sender(196368)
  test 12 success: sr_subscribe ftp_f70 (193541) should have about the
  same number of items as sr_post test2_f61(193541)
  test 13 success: sr_post test2_f61 (193541) should have about the same
  number of items as shim_f63 195055
                   | py infos   routing |
  test 14 success: sr_shovel pclean_f90 (97019) should have the same
  number of watched items winnows'post (100077)
  test 15 success: sr_shovel pclean_f92 (94537}) should have the same
  number of removed items winnows'post (100077)
  test 16 success: 0 messages received that we don't know what happenned.
  test 17 success: count of truncated headers (98075) and subscribed
  messages (98075) should have about the same number of items
                   | C          routing |
  test 18 success: cpump both pelles (c shovel) should receive about the
  same number of messages (161365) (161365)
  test 19 success: cdnld_f21 subscribe downloaded (47950) the same
  number of files that was published by both van_14 and van_15 (47950)
  test 20 success: veille_f34 should post twice as many files (95846) as
  subscribe cdnld_f21 downloaded (47950)
  test 21 success: veille_f34 should post twice as many files (95846) as
  subscribe cfile_f44 downloaded (47896)
  test 22 success: Overall 21 of 21 passed (sample size: 100077) !
  
  NB retries for sr_subscribe t_f30 0
  NB retries for sr_sender 36
  

So, in this case, the results are still good in spite of not quite being 
able to terminate. If there was a significant problem, the cumulation
would indicate it.



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
- upload the release to launchpad.net, so that the installation of debian packages
  using the repository succeeds.


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

A convenient script has been created to automate the release process. Simply run ``release.sh`` and it will guide you in cutting a new release.


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

A convenient script has been created to build and publish the *wheel* file. Simply run ``publish-to-pypi.sh`` and it will guide you in that.

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

* Ensure the code mirror is updated by checking the **Import details** by checking `this page for sarracenia <https://code.launchpad.net/~ssc-hpc-chp-spc/metpx-sarracenia/+git/trunk>`_
* if the code is out of date, do **Import Now** , and wait a few minutes while it is updated.
* once the repository is upto date, proceed with the build request.
* Go to the `sarracenia release <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/sarracenia-release>`_ recipe
* Click on the **Request build(s)** button to create a new release
* for Sarrac, follow the procedure `here <https://github.com/MetPX/sarrac#release-process>`_
* The built packages will be available in the `metpx ppa <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx>`_

Daily Builds
++++++++++++

Daily builds are configured 
using `this recipe for python <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/sarracenia-daily>`_ 
and `this recipe for C <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/metpx-sarrac-daily>`_ and 
are run once per day when changes to the repository occur. These packages are stored in the `metpx-daily ppa <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-daily>`_.
One can also **Request build(s)** on demand if desired.


Manual Process
++++++++++++++

The process for manually publishing packages to Launchpad ( https://launchpad.net/~ssc-hpc-chp-spc ) involves a more complex set of steps, and so the convenient script ``publish-to-launchpad.sh`` will be the easiest way to do that. Currently the only supported releases are **trusty** and **xenial**. So the command used is::

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

One can build a very limited sort of rpm package on an rpm based distro by
using the python distutils::

   python3 setup.py bdist_rpm

Unfortunately, it doesn't add proper dependencies, so one must install those 
manually. So it will help if you must use .rpm's for compliance reasons, but
it isn't really properly done.  `Help Wanted  <https://github.com/MetPX/sarracenia/issues57>`_



Updating The Project Website
----------------------------

Prior to March 2018, the primary web-site for the project was metpx.sf.net.
That MetPX website was built from the documentation in the various modules
in the project. It builds using all **.rst** files found in 
**sarracenia/doc** as well as *some* of the **.rst** files found in 
**sundew/doc**. In the Spring of 2018, development moved to github.com.
That site renders .rst when showing pages, so separate processing to render
web pages is no longer needed.

On the current web site, updating is done by committing changes to .rst files
directly on github. There is no post-processing required. As the links are all
relative and other services such as gitlab also support such rendering, the
*website* is portable any gitlab instance, etc...  And the entry point is from
the README.rst file at the root directory of each repository.


Building Locally
~~~~~~~~~~~~~~~~

**OBSOLETE, See above**

In order to build the HTML pages, the following software must be available on your workstation:

* `dia <http://dia-installer.de/>`_
* `docutils <http://docutils.sourceforge.net/>`_
* `groff <http://www.gnu.org/software/groff/>`_

From a command shell::

  cd site
  make

note::  the makefile contains a commented line *sed that replaces .rst with .html in the files.
To build the pages locally, this sed is needed, so un-comment it, but don't commit the change
because it will break the *updating The website* procedure.


Updating The Website
~~~~~~~~~~~~~~~~~~~~

Today, just edit the pages in the git repository, and they will be active as soon as they are pushed
to the master branch.


**OBSOLETE, See above**

To publish the site to sourceforge (updating metpx.sourceforge.net), you must have a sourceforge.net account
and have the required permissions to modify the site.

From a shell, run::

  make SFUSER=myuser deploy

Only the index-e.html and index-f.html pages are used on the sf.net website 
today. Unless you want to change those pages, this operation is useless.
For all other pages, the links go directly into the various .rst files on
github.com.



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



Adding Checksum Algorithms
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::
   That addition of a checksum requires code modification is considered a weakness.
   There will be an API to be able to plugin checksums at some point.  Not done yet.

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

      if flgs == 'c':
          self.sumalgo = checksum_s()

Might want to add 's' to the list of valid sums in validate_sum as well.

It is planned for a future version to make a plugin interface for this so that adding checksums
becomes an application programmer activity.

