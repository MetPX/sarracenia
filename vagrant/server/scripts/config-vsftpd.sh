#!/bin/sh
sudo mkdir /apps
sudo useradd -b /apps -m px -s /bin/bash
echo "px:test" | sudo chpasswd
sudo mkdir /apps/px/test
sudo chown px.px /apps/px/test

sudo cp ~vagrant/vsftpd/vsftpd.conf /etc/vsftpd.conf
sudo chown root.root /etc/vsftpd.conf
sudo restart vsftpd
