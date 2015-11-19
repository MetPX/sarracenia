#!/bin/sh

# configure apache with some defaults
sudo mkdir /var/www/test
sudo chown apache:apache /var/www/test
sudo a2enmod autoindex
