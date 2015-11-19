#!/bin/sh   
sudo apt-get update

# get all the dependencies for rabbitmq-server and metpx-sarracenia
sudo apt-get install -y erlang-nox
sudo apt-get install -y python3-pkg-resources
sudo apt-get install -y python3-amqplib
sudo apt-get install -y python3-pyinotify
sudo apt-get install -y python3-psutil
sudo apt-get install -y python3-pip

# python3-paramiko not available for trusty, so we pip install it
sudo pip3 install paramiko

cd /tmp
wget https://www.rabbitmq.com/releases/rabbitmq-server/v3.5.6/rabbitmq-server_3.5.6-1_all.deb
sudo dpkg -i rabbitmq-server_3.5.6-1_all.deb 

wget http://iweb.dl.sourceforge.net/project/metpx/sarracenia/metpx-sarracenia_0.1.1_all.deb
sudo dpkg -i metpx-sarracenia_0.1.1_all.deb 

# install apache
sudo apt-get install -y apache2
