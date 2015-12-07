#!/bin/sh   
sudo apt-get update

# get all the dependencies for rabbitmq-server and metpx-sarracenia
sudo apt-get install -y erlang-nox
sudo apt-get install -y python3-pkg-resources
sudo apt-get install -y apache2
sudo apt-get install -y vsftpd
sudo apt-get install -y ksh

if [ $1 = "trusty" ]; then
	sudo apt-get install -y python3-amqplib
	sudo apt-get install -y python3-pyinotify
	sudo apt-get install -y python3-psutil
	sudo apt-get install -y python3-pip

	# python3-paramiko not available for trusty, so we pip install it
	sudo pip3 install paramiko
fi

if [ $1 = "precise" ]; then
	sudo apt-get install python3-dev
	sudo apt-get install python3-setuptools

	# install packages that aren't available natively
	sudo easy_install3 pip
	sudo pip3 install pyinotify
	sudo pip3 install psutil
	sudo pip3 install paramiko
fi

cd /tmp
wget -q https://www.rabbitmq.com/releases/rabbitmq-server/v3.5.6/rabbitmq-server_3.5.6-1_all.deb
sudo dpkg -i rabbitmq-server_3.5.6-1_all.deb 

if [ $1 = "trusty" ]; then
	wget -q http://iweb.dl.sourceforge.net/project/metpx/sarracenia/0.1.1/metpx-sarracenia_0.1.1_all.deb
	sudo dpkg -i metpx-sarracenia_0.1.1_all.deb 
fi

