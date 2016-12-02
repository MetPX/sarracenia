#!/bin/sh

# Generate keys for vagrant user
sudo mkdir -p ~vagrant/.ssh
ssh-keygen -trsa -f ~vagrant/.ssh/id_rsa

# Setup passwordless access vagrant->vagrant
sudo cat ~vagrant/.ssh/id_rsa.pub >> ~vagrant/.ssh/authorized_keys

#Fix perms
sudo chmod 700 ~vagrant/.ssh
sudo chmod 600 ~vagrant/.ssh/id_rsa
