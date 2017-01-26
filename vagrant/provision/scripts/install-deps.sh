#!/bin/sh
sudo apt-get update

# get all the dependencies for rabbitmq-server and metpx-sarracenia
sudo add-apt-repository ppa:ssc-hpc-chp-spc/metpx
sudo apt-get update
sudo apt-get install -y unzip
sudo apt-get install -y devscripts
sudo apt-get install -y dpkg-dev
sudo apt-get install -y debhelper
sudo apt-get install -y python3-setuptools
sudo apt-get install -y python-docutils
sudo apt-get install -y rabbitmq-server
sudo apt-get install -y git
sudo apt-get install -y erlang-nox
sudo apt-get install -y python3-pkg-resources
#sudo apt-get install -y apache2
#sudo apt-get install -y vsftpd
sudo apt-get install -y ksh

if [ $1 = "trusty" ]; then
	sudo apt-get install -y python3-metpx-sarracenia
	sudo apt-get install -y python3-paramiko
	sudo apt-get install -y python3-amqplib
	sudo apt-get install -y python3-pyinotify
	sudo apt-get install -y python3-psutil
	sudo apt-get install -y python3-pip

	# python3-paramiko not available for trusty, so we pip install it
	#sudo pip3 install paramiko
fi

if [ $1 = "precise" ]; then
	sudo apt-get install python3-dev
	sudo apt-get install python3-setuptools

	# install packages that aren't available natively
	sudo easy_install3 pip
	sudo pip3 install pyinotify
	sudo pip3 install psutil
	sudo pip3 install paramiko
	sudo pip3 install metpx-sarracenia
	sudo pip3 install --upgrade metpx-sarracenia
fi

cd /tmp
wget -q https://www.rabbitmq.com/releases/rabbitmq-server/v3.5.6/rabbitmq-server_3.5.6-1_all.deb
sudo dpkg -i rabbitmq-server_3.5.6-1_all.deb

#if [ $1 = "trusty" ]; then
#	wget -q http://iweb.dl.sourceforge.net/project/metpx/sarracenia/0.1.1/metpx-sarracenia_0.1.1_all.deb
#	sudo dpkg -i metpx-sarracenia_0.1.1_all.deb
#fi
