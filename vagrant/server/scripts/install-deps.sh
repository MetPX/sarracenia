#!/bin/sh   
sudo apt-get update

# get all the dependencies for rabbitmq-server and metpx-sarracenia
sudo apt-get install -y erlang-nox
sudo apt-get install -y python3-pkg-resources
sudo apt-get install -y python3-amqplib
sudo apt-get install -y python3-pyinotify
sudo apt-get install -y python3-psutil
sudo apt-get install -y python3-pip
sudo apt-get install -y apache2
sudo apt-get install -y vsftpd
sudo apt-get install -y ksh

# python3-paramiko not available for trusty, so we pip install it
sudo pip3 install paramiko

cd /tmp
wget -q https://www.rabbitmq.com/releases/rabbitmq-server/v3.5.6/rabbitmq-server_3.5.6-1_all.deb
sudo dpkg -i rabbitmq-server_3.5.6-1_all.deb 

wget -q http://iweb.dl.sourceforge.net/project/metpx/sarracenia/0.1.1/metpx-sarracenia_0.1.1_all.deb
sudo dpkg -i metpx-sarracenia_0.1.1_all.deb 

