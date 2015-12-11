#!/bin/sh

# configure apache with some defaults
sudo mkdir -p /var/www/test
sudo chown www-data:www-data /var/www/test
sudo cp ~vagrant/apache2/sites-available/default.conf /etc/apache2/sites-available/default.conf
sudo chmod 644 /etc/apache2/sites-available/default.conf
sudo a2enmod autoindex
sudo a2dissite 000-default
sudo a2ensite default
sudo /etc/init.d/apache2 restart
