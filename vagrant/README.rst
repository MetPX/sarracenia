==================
 Vagrant Configs
==================

Overview
---------

This directory contains various configurations for setting up virtual machines to test
and demo `metpx-sarracenia`.  

Prerequisites
-------------

* `Vagrant <https://www.vagrantup.com/downloads.html>`_. 
* `VirtualBox <https://www.virtualbox.org/wiki/Downloads>`_.

Overview
------------

Installs a basic Linux machine in order to test different components of sarracenia. The ```Vagrantfile``` is setup to provision a server running:

- vsftpd
- rabbitmq-server
- apache2
- metpx-sarra (installed from deb)

Once provisioned, the test files are located under ```~vagrant/tests```.

Example::

    cd metpx/sarra/vagrant/server
    vagrant up
    vagrant ssh
    ./test_sr_sarrah.sh px test


You could also simply provision an instance and test out Sarracenia.


Supported OSes
---------------

* Precise (Ubuntu 12.04)
* Trusty (Ubuntu 14.04)
