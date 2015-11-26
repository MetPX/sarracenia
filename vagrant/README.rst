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

The various different setups are listed below.  

Server
------------

Installs a basic sarra server in order to test ```sr_sarra``` using the script ```test/test_sr_sarra.sh```. The ```Vagrantfile``` is setup to provision a server running:

- vsftpd
- rabbitmq-server
- apache2
- metpx-sarra (installed from deb)

Example::

    cd metpx/sarra/vagrant/server
    vagrant up
    vagrant ssh
    ./test_sr_sarrah.sh px test

 You could also simply provision this instance and test out Sarracenia.
