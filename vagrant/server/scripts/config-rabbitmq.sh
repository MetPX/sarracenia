#!/bin/sh

sudo cp ~vagrant/rabbitmq/* /etc/rabbitmq
sudo chmod 644 /etc/rabbitmq/*
sudo /etc/init.d/rabbitmq-server restart