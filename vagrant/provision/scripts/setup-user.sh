#!/bin/sh

# Generate keys for vagrant user
sudo mkdir -p ~vagrant/.ssh
ssh-keygen -trsa -f ~vagrant/.ssh/id_rsa
sudo chown vagrant.vagrant ~vagrant/.ssh/id_rsa
sudo chown vagrant.vagrant ~vagramt/.ssh/id_rsa.pub

# Setup passwordless access vagrant->vagrant
echo -e "\n" >> ~vagrant/.ssh/authorized_keys
sudo cat ~vagrant/.ssh/id_rsa.pub >> ~vagrant/.ssh/authorized_keys

#Fix perms
sudo chmod 700 ~vagrant/.ssh
sudo chmod 600 ~vagrant/.ssh/id_rsa
