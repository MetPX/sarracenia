====================================
 MetPX-Sarracenia Developer's Guide
====================================

:version: @Version@
:date: @Date@

.. contents::


Tools you Need
--------------


To hack on the Sarracenia source, you need:

- A linux development environment, either a workstation, or a VM of some kind.
  setup using ubuntu is automated, but adjustment for other distros is possible.
  command-line comfort a must.

- python3. The application is developed in and depends on python versions >= 3.5.

- style: PEP8 except max line length is 119, enforced via `pycodestyle <https://pycodestyle.pycqa.org/en/latest/intro.html#disclaimer>`_ for VSCode, yapf3 or other similar tool.

- an account on github.com will help in submitting patches for consideration.

Things that will be installed by automated setup:

- a bunch of other python modules indicated in the dependencies (setup.py or debian/control)

- python3 pyftpdlib module, used to run an ftpserver on a high port during the flow test.

- git. in order to download the source from the github repository, and to prepare and submit
  changes.

- a dedicated rabbitmq broker, with administrative access, to run the sr_insects tests.
  this is installed by automated tools for setting up the linux environment.
  The flow test creates and destroys exchanges and will disrupt any active flows on the broker.

after you have cloned the source code::

    git clone -b v03_wip https://github.com/MetPX/sarracenia metpx-sr3
    git clone -b v03 https://github.com/MetPX/sarrac sr3c
    git clone -b v03_wip https://github.com/MetPX/sr_insects insects
    cd sr3

The rest of the Guide takes the above for granted.

Documentation
-------------
`Documentation Standards <Documentation.rst>`_ exist in /docs/Contribution/Documentation.rst

Where to Put Options 
~~~~~~~~~~~~~~~~~~~~

Options are documented in sr3(1), which is kind of a *parent* to 
all other consuming components. Any options used by multiple components should
be documented there. Options which are unique to a single component should be
documented in the man page for that component.


Development
-----------

In general, the development workflow is to get a laptop or a VM where one can run
the flow_tests (available from http://github.com/MetPX/sr_insects ) The first step
in configuring a development environment is ensuring that the sr_insects flow tests
work, as they function as a gate for commits to important branches. 

Development is most commonly done on Ubuntu >=18.04 platform. 


v2 Workflow
~~~~~~~~~~~

Finished development work for version 2 is committed to on the main branch, which is used
to produce daily snapshots. One should not normally commit changes to the main branch,
but rather merge them from a working branch.

Development branches are named after the issue they are meant to address "issue365", for
example. If there are multiple attempts to address a given issue, then use the issue
as a name prefix. For example, there could be issue365, but if we decide that isn't
a good way to address the issue, there could be an issue365_methodB branch.

**Before submitting a pull-request (PR), please ensure that the flow tests from
sr_insects have been run successfully:  at least static_flow, flakey_broker, and dynamic_flow**

When a PR is generated, the second developer can look it over for concerns.
Once satisfied with the nature of the patch, the second developer should pull the branch
and run the flow tests again (the same three) to confirm.  Only after the flow tests
have been run on multiple machines should a change be merged to main.

issues unique to v2 may be tagged *v2only*.

v3 Workflow
~~~~~~~~~~~

The upcoming version of Sarracenia is maintained in the v03_wip (work in progress) branch.
As the major refactor is substantially complete, the remaining work is now entirely constructive
and all development is co-ordinated through issues exactly as v2 is.  Issues unique to v3,
be they regressions or enhancements that don't make sense to add to v2, have the tag *v3only*.
Issues that are common between the releases are tagged *v3*.

The workflow with v3 is similar to v2 but with different branches.  New development work should
have a v03\_ prefix, such as v03\_issue401. Having all the flow tests complete fairly successfully
is one criterion for acceptance into v03_wip.

To run the sr_insects tests, the repository must be cloned with the v03_wip branch.
A gate for merging to v03_wip is for a second developer to run the flow_tests.
**For v03, these tests must run:  static_flow, flakey_broker, dynamic_flow, transform_flow**


sr_insects
~~~~~~~~~~

the sr_insects repository has it's own issues DB, and work on sr_insects is encouraged.
Both v2 and v3 are supported on the v03_wip branch of sr_insects.  That branch should be
used to support all development in both versions.... hmm... perhaps should make v03_wip
the main branch?


Local Installation
------------------

There are many different ways to install python packages on a computer. Different developers
will prefer different methods, and all the methods need to be tested prior to each release.

* **Wheel** when people are running different operating systems (non-ubuntu, non-debian) people will be installing wheels, typically that have been uploaded to pypi.python.org.  On the other hand, it is a bit of a pain/noise to upload every development version, so we only upload releases, so testing of wheels is done by building local wheels. Need to build a new wheel every time a change is made.

* **pip install (not -e)** would pull a wheel down from pypi.python.org. Generally not used during development of Sarracenia itself.

* **pip install -e** ... lets you edit the source code of the installed package, ideal for debugging problems, because it allows live changes to the application without having to go through building and installing a new package.

* **apt install** install debian package from repositories, similarly to pip install (not -e), normally dev snapshots are not uploaded to repositories, so while this would be the normal way for users of ubuntu servers, it is not available during development of the package itself.

* **dpkg -i** builds a debian package for local installation. This is how packages are tested prior to upload to repositories.  It can also be used to support development (have to run dpkg -i for each package change.)

The sr_insects tests invokes the version of metpx-sarracenia that is installed on the system,
and not what is in the development tree.  It is necessary to install the package on 
the system in order to have it run the sr_insects tests.

Prepare a Vanilla VM
~~~~~~~~~~~~~~~~~~~~

This section describes creating a test environment for use in a virtual machine. One way to build
a virtual machine is to use multipass (https://multipass.run) Assuming it is installed, one can
create a vm with::

 multipass launch -m 8G -d 30G --name flow

need to have ssh localhost work in the multipass container.  Can do that by copying multipass
private key into the container::

 fractal% multipass list                                                         
 Name                    State             IPv4             Image
 primary                 Stopped           --               Ubuntu 20.04 LTS
 flow                    Running           10.23.119.56     Ubuntu 20.04 LTS
 keen-crow               Running           10.23.119.5      Ubuntu 20.04 LTS
 fractal% 

Weird issues with ssh keys not being interpreted properly by paramiko, work around
( https://stackoverflow.com/questions/54612609/paramiko-not-a-valid-rsa-private-key-file )
::

 fractal% sudo cat /var/snap/multipass/common/data/multipassd/ssh-keys/id_rsa | sed 's/BEGIN .*PRIVATE/BEGIN RSA PRIVATE/;s/END .*PRIVATE/END RSA PRIVATE/' >id_rsa_container
 chmod 600 id_rsa_container
 scp -i id_rsa_container id_rsa_container ubuntu@10.23.119.175:/home/ubuntu/.ssh/id_rsa
                                                                   100% 1704     2.7MB/s   00:00    

 fractal% scp -i id_rsa_container id_rsa_container ubuntu@10.23.119.106:/home/ubuntu/.ssh/id_rsa
 The authenticity of host '10.23.119.106 (10.23.119.106)' can't be established.
 ECDSA key fingerprint is SHA256:jlRnxV7udiCBdAzCvOVgTu0MYJR5+kYzNwy/DIhkeD8.
 Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
 Warning: Permanently added '10.23.119.106' (ECDSA) to the list of known hosts.
 id_rsa_container                                                                                                                         100% 1712     9.4MB/s   00:00    
 fractal% multipass shell flow
 Welcome to Ubuntu 20.04.3 LTS (GNU/Linux 5.4.0-81-generic x86_64)
 
  * Documentation:  https://help.ubuntu.com
  * Management:     https://landscape.canonical.com
  * Support:        https://ubuntu.com/advantage
 
   System information as of Fri Aug 27 21:12:16 EDT 2021
 
   System load:  0.42              Processes:             112
   Usage of /:   4.4% of 28.90GB   Users logged in:       0
   Memory usage: 5%                IPv4 address for ens4: 10.23.119.106
   Swap usage:   0%
 
 
 1 update can be applied immediately.
 To see these additional updates run: apt list --upgradable
 
 
 To run a command as administrator (user "root"), use "sudo <command>".
 See "man sudo_root" for details.
 
 ubuntu@flow:~$ 

then prompt ssh to accept the localhost key::

 ubuntu@flow:~$ ssh localhost ls -a
 The authenticity of host 'localhost (127.0.0.1)' can't be established.
 ECDSA key fingerprint is SHA256:jlRnxV7udiCBdAzCvOVgTu0MYJR5+kYzNwy/DIhkeD8.
 Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
 Warning: Permanently added 'localhost' (ECDSA) to the list of known hosts.
 .
 ..
 .bash_logout
 .bashrc
 .cache
 .profile
 .ssh
 ubuntu@flow:~$ 


This will provide a shell in an initialized VM.  To configure it::

 
  git clone -b v03_wip https://github.com/MetPX/sarracenia sr3
  cd sr3

There are scripts that automate the installation of necessary environment to be able to run tests::

  travis/flow_autoconfig.sh
  travis/add_sr3.sh

You should be able to see an empty configuration::

  sr3 status

sr3c and sr3 are now installed, and should be ready to run a flow test from the sr_insects module, which
has also been cloned:

  cd ../sr_insects

The v03 branch of sr_insects supports testing of both v2 and v3, and both versions are now installed.
The flow tests are intended to be run to confirm compatibility between v2 and v3, and so one
must be able to test v2 as well::

  ubuntu@flow:~/sr_insects$ dpkg -l | grep metpx
  ii  metpx-libsr3c                    3.21.08a1-0~202108270410~ubuntu20.04.1 amd64        C-Implementation of a Sarracenia Client
  ii  metpx-sarracenia                 2.21.08-0~202108241854~ubuntu20.04.1   all          Directory mirroring in real-time for users, file servers and web sites.
  ii  metpx-sr3                        3.00.008exp                            all          v3 Directory mirroring in real-time for users, file servers and web sites.
  ii  metpx-sr3c                       3.21.08a1-0~202108270410~ubuntu20.04.1 amd64        C-Implementation of a Sarracenia Client
  ubuntu@flow:~/sr_insects$ 

The v2 package is metpx-sarracenia, whereas the v3 one is metpx-sr3. the flow tests will detect
which version is installed and test v3 if both are present.  To override that::

  ubuntu@flow:~/sr_insects$ export sarra_py_version=2.21.08
  ubuntu@flow:~/sr_insects$ 

Then one can run flow_tests from this shell normally.

Python Wheel
~~~~~~~~~~~~

If you have not used add_sr3.sh (which builds a debian package), then one can use this procedure
for local installation on a computer with a python wheel for testing and development::

    python3 setup.py bdist_wheel

Should build a wheel in the dist sub-directory.
then as root install that new package::

       pip3 install --upgrade ...<path>/dist/metpx*.whl

Local Pip install
~~~~~~~~~~~~~~~~~

For local installation on a computer, using a pip
For testing and development::

   pip3 install -e .
   export PATH=${HOME}/.local/bin

Using the local python package installer (PIP) to create a locally editable version.
The above will install the package in ~/.local/bin... so need to ensure the path includes
that directory.





Debian/Ubuntu
~~~~~~~~~~~~~

For local installation on a computer, using a debian package.
This process builds a local .deb in the parent directory using standard debian mechanisms.
- Check the **build-depends** line in *debian/control* for dependencies that might be needed to build from source.
- The following steps will build sarracenia but not sign the changes or the source package::

    cd metpx/sarracenia
    sudo apt-get install devscripts
    debuild -uc -us
    sudo dpkg -i ../<the package just built>

which accomplishes the same thing using debian packaging.
The options are detailed below:


Committing Code
~~~~~~~~~~~~~~~

What should be done prior to committing to the master branch?
Checklist:

- do development on some other branch.  Usually the branch will be named after the issue being
  addressed.  Example:  issue240, if we give up on an initial approach and start another one, 
  there may be issue240_2 for a second attempt.  There may also be feature branches, such as v03.
- **sr_insects tests works** (See Testing) The master branch should always be functional, do not commit code if the sr_insects tests are not working.
- Natural consequence: if the code changes means tests need to change, include the test change in the commit.
- **update doc/** manual pages should get their updates ideally at the same time as the code.

Usually there will be many such cycles on a development branch before one is ready
to issue a pull request. Eventually, we get to `Commits to the Master Branch`_


sr_insects Tests Description
----------------------------

Before committing code to the master branch, as a Quality Assurance measure, one should run 
all available self-tests. It is assumed that the specific changes in the code have already been unit
tested. Please add self-tests as appropriate to this process to reflect the new ones.
Generally speaking one should solve problems at the first test that fails as each test
is more complicated than the previous one.

There is a separate git repository containing the more complex tests https://github.com/MetPX/sr_insects

A typical development workflow will be (Do not try this, this is just an overview of the steps that will be 
explained in detail in following sections)::

   git branch issueXXX
   git checkout issueXXX
   cd sarra ; *make coding changes*
   cd ..
   debuild -uc -us
   cd ../sarrac
   debuild -uc -us
   sudo dpkg -i ../*.deb
   cd ..

   git clone -b v03_wip https://github.com/MetPX/sr_insects
   cd sr_insects
   sr3 status  # make sure there are no components configured before you start.
               # test results will likely be skewed otherwise.
   for test in unit static_flow flakey_browser transform_flow dynamic_flow; do
      cd $test
      ./flow_setup.sh  # *starts the flows*
      ./flow_limit.sh  # *stops the flows after some period (default: 1000) *
      ./flow_check.sh  # *checks the flows*
      ./flow_cleanup.sh  # *cleans up the flows*
      cd ..
   done

   #assuming all the tests pass.
   git commit -a  # on the branch...


Unit
~~~~

The *unit* test in sr_insects is the shortest one taking a minute or so, and not requiring
much configuration at all. They are sanity tests of code behaviour. Generally takes a minute
or two on a laptop.

Static Flow
~~~~~~~~~~~

The *static_flow* tests are a bit more complicated, testing more components, using single
threaded components in a linear way (all data moves uniformly forward.) It should be
more straight-forward to identify issues as there is no deletion and so it lends itself well
to repeating subset tests to identify individual issues. It takes about two minutes on a laptop.

Flakey Broker
~~~~~~~~~~~~~

The *flakey_broker* tests are the same as the *static_flow*, but slowed down so that they last
a few minutes, and the broker is shutdown and restarted while the posting is happenning.  
Note that post_log prints before a message is posted (because post_log is an on_post plugin, and
that action, allows one to modify the post, so it needs to be before the post actually happens.)


Dynamic Flow
~~~~~~~~~~~~

The *dynamic_flow* test add advanced features:  multi-instances, the winnow component, retry logic testing, 
and includes file removals as well. Most of the documentation here refers to runnig the
dynamic_flow test, as it is the most complicated one, and the ancestor of the others.  The unit
test was separated out from the beginnig of the dynamic_flow test, and the static_flow is
a simplified version of the original flow test as well.

Generally speaking, one should run the tests in sequence and ensure the results of earlier 
tests are good before proceeding to the next test.

Note that the development system must be configured for the sr_insects tests to run successfully. See the next
section for configuration instructions. For development with a fresh OS installation,
the configuration steps have been automated and can be applied with the flow_autoconfig.sh
script in sr_insects (https://github.com/MetPX/sr_insects/blob/master/flow_autoconfig.sh). Blind 
execution of this script on a working system may lead to undesirable side effects; you have been warned!


The configuration one is trying to replicate:

.. image:: Development/Flow_test.svg


Following table describes what each element of the dynamic flow test does, and the test coverage
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
can start a browser. If working with the C implementation as well, there are also the following
flows defined:

.. image:: Development/cFlow_test.svg

   
Running Flow Tests
------------------

This section documents these steps in much more detail.  
Before one can run the sr_insects tests, some pre-requisites must be taken care of.
note that there is travis-ci.com integration for at least the master branch
to verify functionality on a variety of python version.  Consulte::

   https://travis-ci.com/MetPX/sarracenia

for the latest test results.




Install Servers on Workstation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To prepare a computer to run the flow test, one must install some server 
software and configurations. This same work is done by travis/flow_autoconfig.sh
which is run in `Prepare a Vanilla VM`_ but if you need to configure it 
manually, below is the process.

Install a minimal localhost broker and configure rabbitmq test users::

    sudo apt-get install rabbitmq-server
    sudo rabbitmq-plugins enable rabbitmq_management

    mkdir ~/.config/sarra
    cat > ~/.config/sarra/default.conf << EOF
    declare env FLOWBROKER=localhost
    declare env MQP=amqp
    declare env SFTPUSER=${USER}
    declare env TESTDOCROOT=${HOME}/sarra_devdocroot
    declare env SR_CONFIG_EXAMPLES=${HOME}/git/sarracenia/sarra/examples
    EOF

    RABBITMQ_PASS=S0M3R4nD0MP4sS
    cat > ~/.config/sarra/credentials.conf << EOF
    amqp://bunnymaster:${RABBITMQ_PASS}@localhost/
    amqp://tsource:${RABBITMQ_PASS}@localhost/
    amqp://tsub:${RABBITMQ_PASS}@localhost/
    amqp://tfeed:${RABBITMQ_PASS}@localhost/
    amqp://anonymous:${RABBITMQ_PASS}@localhost/
    amqps://anonymous:anonymous@hpfx.collab.science.gc.ca
    amqps://anonymous:anonymous@hpfx1.collab.science.gc.ca
    amqps://anonymous:anonymous@hpfx2.collab.science.gc.ca
    amqps://anonymous:anonymous@dd.weather.gc.ca
    amqps://anonymous:anonymous@dd1.weather.gc.ca
    amqps://anonymous:anonymous@dd2.weather.gc.ca
    ftp://anonymous:anonymous@localhost:2121/
    EOF

    cat > ~/.config/sarra/admin.conf << EOF
    cluster localhost
    admin amqp://bunnymaster@localhost/
    feeder amqp://tfeed@localhost/
    declare source tsource
    declare subscriber tsub
    declare subscriber anonymous
    EOF

    sudo rabbitmqctl delete_user guest

    sudo rabbitmqctl add_user bunnymaster ${RABBITMQ_PASS}
    sudo rabbitmqctl set_permissions bunnymaster ".*" ".*" ".*"
    sudo rabbitmqctl set_user_tags bunnymaster administrator

    sudo systemctl restart rabbitmq-server
    cd /usr/local/bin
    sudo mv rabbitmqadmin rabbitmqadmin.1
    sudo wget http://localhost:15672/cli/rabbitmqadmin
    sudo chmod 755 rabbitmqadmin

    sr --users declare

.. Note::

    Please use other passwords in credentials for your configuration, just in case.
    Passwords are not to be hard coded in self test suite.
    The users bunnymaster, tsource, tsub, and tfeed are to be used for running tests.

    The idea here is to use tsource, tsub, and tfeed as broker accounts for all
    self-test operations, and store the credentials in the normal credentials.conf file.
    No passwords or key files should be stored in the source tree, as part of a self-test
    suite.

Setup Flow Test Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once the server environment is established, the flow tests use sftp transfers to localhost. 

It is also required that passwordless ssh access is configured on the test host
for the system user that will run the flow test. This can be done by creating
a private/public ssh key pair for the user (if there isn't one already) and copying
the public key to the authorized_keys file in the same directory as the keys (~/.ssh).
For associated commands, see http://www.linuxproblem.org/art_9.html

Note that on systems where older versions of Paramiko (< 2.7.2) are installed, and the ssh key pair was generated with OpenSSH >= 6.5, manually testing the below command will work, but Paramiko will not be able to connect. This is likely the case if the ``~/.ssh/id_rsa`` file contains ``BEGIN OPENSSH PRIVATE KEY``. To work around this, convert the private key's format using ``ssh-keygen -p -m PEM -f ~/.ssh/id_rsa``.

To confirm that that passwordless ssh to localhost works::

   ssh localhost ls

This should run and complete.  If it prompts for a password, the flow tests will not work.

Check that the broker is working::

   systemctl status rabbitmq-server

One part of the flow test runs an sftp server, and uses sftp client functions.
Need the following package for that::

    sudo apt-get install python3-pyftpdlib python3-paramiko



The setup script starts a trivial web server, and ftp server, and a daemon that invokes sr_post.
It also tests the C components, which need to have been already installed as well 
and defines some fixed test clients that will be used during self-tests::

    cd 
    git clone -b v03_wip https://github.com/MetPX/sr_insects
    cd sr_insects
    cd static_flow
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


Run A Flow Test
~~~~~~~~~~~~~~~

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

When done testing, run the ./flow_cleanup.sh script, which will kill the
running servers and daemons, and delete all configuration files installed for
the flow test, all queues, exchanges, and logs. This also needs to be done
between each run of the flow test::
  
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

After the flow_cleanup.sh, to check that a test has completed, use::

   sr3 status 

which should show that there are no active configurations.

If the static_flow test works, then re-run the other tests: flakey_broker, 
transform_flow, and dynamic_flow.

Dynamic Flow Test Length
~~~~~~~~~~~~~~~~~~~~~~~~

While most tests have a fixed duration, the dynamic flow test queries a remote
server and can run for any length desired. The dynamic flow_test length defaults
to 1000 files being flowed through the test cases. When in rapid development, 
one can supply an argument to shorten that::

  ./flow_limit.sh 200

Towards the end of a development cycle, longer flow_tests are adviseable::

  ./flow_limit.sh 20000 

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

High volume sample
~~~~~~~~~~~~~~~~~~

Trying the flow test with higher volume of messages (ie. 100 000) is one step closer to the goal of having a flow test running continously. This is motivated by our testing purposes. 

Limitation
++++++++++
Ubuntu have a limitation that tops inotify watches and that we encountered in `#204 <https://github.com/MetPX/sarracenia/issues/204>`_ . We can overcome this by setting the related sysctl variable. First, check what is the limit of your system::

  $ sysctl fs.inotify.max_user_watches
  fs.inotify.max_user_watches = 8196

If the limit is too low (ie. 8196), change it to a more appropriate level for the flow test::

  $ sudo sysctl fs.inotify.max_user_watches=524288

To make this change permanent add this line to ``/etc/sysctl.conf``::

  fs.inotify.max_user_watches=524288

Then excute ``sysctl -p`` and the system should now support high volume of inotify events.

Flow Test Stuck
+++++++++++++++
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

Flow tests with MQTT
~~~~~~~~~~~~~~~~~~~~

Flow tests can be run where certain components use the MQTT protocol, instead of AMQP.

FIXME: steps missing, more clarity required.

* MQTT broker is installed
* the bunnymaster tsource, tfeed, tsub users defined and given passwords (broker dependent.)
* for each user: an mqtt://user:pw@brokerhost  url's line is added to ~/.config/sr3/credentials.conf
* edit the variable MQP in ~/.config/sr3/default.conf, MQP is used by the flow tests.

Most components will use MQTT instead of amqp and can be run normally.

Commits to the Main Branch
--------------------------

Aside from typos, language fixups in the documentation, and incrementing
the version, developers are not expected to commit to master. All work 
happens on development branches, and all testing is expected to pass before 
one considers affecting master. Once the branch development is complete, 
or a unit of work-in-progress is felt to be worth merging to master, one 
must summarize the changes from the branch for the debian change log, 
request on github.

::
   
   git checkout issueXXX  # v03_issueXXX for v3 work.
   vi CHANGES.rst # summarize the changes in Restructured Text
   dch # copy/paste from CHANGES.rst, inserting one leading space.
   vi doc/UPGRADING.rst # rarely, if code has user impact.
   vi doc/fr/UPGRADING.rst # bon... ceci est visible aux usagers, donc...
   git commit -a
   git push 
   # issue a pull request on github.com.

A Second developer will review the pull request and the reviewer will decide on whether
merging is appropriate. The developer is expected to examine each commit, and 
understand it to some degree.

The Travis CI test looks at pull requests and will run them as if it were merged.
If the tests pass, then that is good qualitative indicator, however the tests are a bit
fragile at the moment, so if they fail, it would be ideal for the reviewer to run
the tests in their own development environment. If it passes in the local developer
environment one can approve a merge in spite of Travis' complaints.  


Main Branches
-------------

There is a long running discussion about `Which Version is stable <https://github.com/MetPX/sarracenia/issues/139>`_
The current set up is that there are three main branches:

* main  ... the main branch is used to build `Daily <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-daily>`_
  and `Pre-Release <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-pre-release>`_ repositories on launchpad.net.

* issue branches to be merged to main should be called issueXXX.

* v2_stable ... generally this branch gets code via merges from master, after the pre-release has been tested on a
  as many systems as possible. used to build the stable: `MetPX <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx>`_

* v03_wip ... The `version 3 <v03.rst>`_ work in progress branch is a next generation version of sarracenia in development.
  It is quite different and currently not usable at all. Do not try it, unless specifically invited. IT DOES NOT WORK.

* issue branches to be merged to v03_wip, it should be called v3_issueXXX
  

Repositories
------------

For Ubuntu operating systems, the launchpad.net site is the best way to provide packages that are fully integrated
( built against current patch levels of all dependencies (software components that Sarracenia relies
on to provide full functionality.)) Ideally, when running a server, a one should use one of the repositories,
and allow automated patching to upgrade them as needed.

Repositories:

* Daily https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-daily (living on the edge... )
  automated daily build from *master* branch.

* Pre-Release https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx-pre-release (for newest features.)
  from *master* branch. Developers manually trigger builds here when it seems appropriate (testing out
  code that is ready for release.)

* Release https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx (for maximum stability)
  from *v2_stable* branch.  After testing in systems subscribed to pre-releases, Developers
  merge from master branch into v2_stable one, and manually trigger a build.

for more discussion see `Which Version is stable <https://github.com/MetPX/sarracenia/issues/139>`_



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
- upload the release notes and binaries to github.com.
- increment the version for future commits to master.

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
  X.ypostN #ack! patched release.

Releases are classified as follows:

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

Example:

The first alpha release in January 2016 would be versioned as ``metpx-sarracenia-2.16.01a01``


Set the Version
~~~~~~~~~~~~~~~

This is done to *start* development on a version.

* git checkout master
* Edit ``sarra/__init__.py`` manually and set the version number.
* Edit CHANGES.rst to add a section for the version.
* run dch to start the changelog for the current version. 
* git commit -a 
* git push

If development continues and the time passes without the release occurring, then
the version needs to be set to again (or overwritten).  For example, a development
cycle begins in August, the version in master will be 2.19.08b1... but if development
continues into September, one should use this procedure the change the version to 2.19.09b1.



Releasing
~~~~~~~~~


When development for a version is complete. The following should occur:

A tag should be created to identify the end of the cycle::

   git checkout master
   git tag -a sarra-v2.16.01a01 -m "release 2.16.01a01"
   git push
   git push origin sarra-v2.16.01a01

then need to update the various distribution methods: `PyPI`_, and `Launchpad`_

Once package generation is complete, one should `Set the Version`_
in master to the next logical increment to ensure no further development
occurs that is identified as the released version.    


PyPi
~~~~

Pypi Credentials go in ~/.pypirc.  Sample Content::

  [pypi]
  username: SupercomputingGCCA
  password: <get this from someone>

Assuming pypi upload credentials are in place, uploading a new release used to be a one liner::

    python3 setup.py bdist_wheel upload

Note that the CHANGES.rst file is in restructured text and is parsed by pypi.python.org
on upload.  
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
* NOTE: **for some repositories, the builds are based on the master branch, for the MetPX repository, it is based on v2_stable.**
* Go to the `sarracenia release <https://code.launchpad.net/~ssc-hpc-chp-spc/+recipe/sarracenia-release>`_ recipe
* Click on the **Request build(s)** button to create a new release
* for Sarrac, follow the procedure `here <https://github.com/MetPX/sarrac#release-process>`_
* The built packages will be available in the `metpx ppa <https://launchpad.net/~ssc-hpc-chp-spc/+archive/ubuntu/metpx>`_

Ubuntu 18.04
++++++++++++

For ubuntu 18.04 (bionic), there are a few wrinkles. The recipe is called: metpx-sr3-daily-bionic, and it
takes source from a different branch: *v03_launchpda*  For every release, this branch needs to be rebased from
*v03_wip*

* git checkout v03_launchpad
* git rebase v03_wip
* git push
* import souce
* Request build from *metpx-sr3-daily-bionic* Recipe.

What is different about this *v03_launchpad* branch? It:

* removes the dependency on python3-paho-mqtt as the version in the repositories is too old.
* removed the dependency on python3-dateparser, as that package is not available in the repository.
* override the testing target un debian/rules, because testing without the dependencies fails.::

  override_dh_auto_test:
  	echo "disable on 18.04... some deps must come from pip"

The missing dependencies should be installed with pip3.



Building a Windows Installer
++++++++++++++++++++++++++++

One can also build a Windows installer with that 
`script <https://github.com/MetPX/sarracenia/blob/master/generate-win-installer.sh>`_.
It needs to be run from a Linux OS (preferably Ubuntu 18) in the root directory of Sarracenia's git. 
Then, from the shell, run::

 sudo apt install nsis
 pip3 install pynsist wheel
 ./generate-win-installer.sh 2>&1 > log.txt

The final package should be placed in build/nsis directory.


Daily Builds
++++++++++++

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
  git clone -b v03_wip https://github.com/MetPX/sarracenia sr3

One can build a very limited sort of rpm package on an rpm based distro by
using the python distutils::

   python3 setup.py bdist_rpm

This will fail trying to open a non-existent CHANGES.txt... a strange incompatibility. So 

  **comment out the two lines in setup.py used to set the long_description**, 

these lines::
   #long_description=(read('README.rst') + '\n\n' + read('CHANGES.rst') +
   #                   '\n\n' + read('AUTHORS.rst')),
 
and then the rpm build will complete. Unfortunately, it doesn't add proper dependencies, so 
one can install those manually.  

A way of addressing the dependency problem  is to decode the options from the debian/control::

   [ubuntu@fed34 sr3]$ grep Recommends debian/control | sed 's/Recommends: //;s/ //g'
   ncftp,wget
   [ubuntu@fed34 sr3]$ 

and repeat with the setup.py file...  (note: setup.py does not want spaces around versions for 
python packages, but bdist_rpm option requires them, so fix that... )::

   [ubuntu@fed34 sr3]$ tail -4 setup.py |  egrep -v '\[' | egrep -v ']' | tr '\n' ' ' | sed 's/ *//g;s/>=/ >= /g;s/^"/"python3-/;s/,"/,"python3-/g'
   "python3-amqp","python3-appdirs","python3-watchdog","python3-netifaces","python3-humanize","python3-jsonpickle","python3-paho-mqtt >= 1.5.1","python3-paramiko","python3-psutil >= 5.3.0"
   [ubuntu@fed34 sr3]$ 

then copy/paste the dependencies into the rpm building line::

   python3 setup.py bdist_rpm --requires=ncftp,wget,"python3-amqp","python3-appdirs","python3-watchdog","python3-netifaces","python3-humanize","python3-jsonpickle","python3-paho-mqtt >= 1.5.1","python3-paramiko","python3-psutil >= 5.3.0"

One can check if the dependencies are there like so::
  
  [ubuntu@fed34 sr3]$ rpm -qp dist/metpx-sr3-3.0.6-1.noarch.rpm --requires
  /usr/bin/python3
  ncftp
  python3-amqp
  python3-appdirs
  python3-humanize
  python3-jsonpickle
  python3-netifaces
  python3-paho-mqtt >= 1.5.1 
  python3-paramiko
  python3-psutil >= 5.3.0
  python3-watchdog
  rpmlib(CompressedFileNames) <= 3.0.4-1
  rpmlib(FileDigests) <= 4.6.0-1
  rpmlib(PartialHardlinkSets) <= 4.0.4-1
  rpmlib(PayloadFilesHavePrefix) <= 4.0-1
  rpmlib(PayloadIsZstd) <= 5.4.18-1
  wget
  [ubuntu@fed34 sr3]$

You can see all of the prefixed python3 dependencies required, as well as the recommended binary accellerator packages
are listed. Then if you install with dnf install, it will pull them all in.  Unfortunately, this method does not allow
the specification of version of the python dependencies which are stripped out. on Fedora 34, this is not a problem,
as all versions are new enough.  Such a package should install well.

a bit inelegant, and not sure if it will work with older versions:
`Help Wanted  <https://github.com/MetPX/sarracenia/issues57>`_


github
------

Click on Releases, Edit the release:

* should we have release names?
* copy/paste of changes from CHANGES.rst
* copy/paste of Installation bit at the end from a previous release.
* build packages locally or download from other sources.
  drag and drop into the release.

This will give us the ability to have old versions available.
launchpad.net doesn't seem to keep old versions around.



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
*website* is portable any gitlab instance, etc... And the entry point is from
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

