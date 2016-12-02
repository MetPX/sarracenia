#!/bin/sh

#mkdir ~/.config
#mkdir ~/.config/sarra
#mkdir ~/.config/sarra/plugins

cd ../../

sudo rabbitmq-plugins enable rabbitmq_management

sudo service rabbitmq-server start
sudo rabbitmqctl delete_user guest

sudo rabbitmqctl add_user bunnymaster MaestroDelConejito
sudo rabbitmqctl set_user_tags bunnymaster administrator
sudo rabbitmqctl set_permissions bunnymaster ".*" ".*" ".*"

sudo cat << EOF > /home/vagrant/.config/sarra/credentials.conf
amqp://bunnymaster:MaestroDelConejito@localhost/
amqp://tfeed:TestFeeding@localhost/
amqp://tsource:TestSOUrCs@localhost/
amqp://tsub:TestSUBSCribe@localhost/
amqp://tsender_src:TestSENDer@localhost/
amqp://tsender_dest:TestSENDer@localhost/

sftp://vagrant@localhost/ ssh_keyfile=/home/vagrant/.ssh/id_rsa
EOF

sudo cat << EOF > /home/vagrant/.config/sarra/default.conf
admin amqp://bunnymaster@localhost/
feeder amqp://tfeed@localhost/
role source tsource
role source tsender_src
role source tsender_dest
role subscribe tsub
EOF

cd /usr/local/bin
sudo wget http://localhost:15672/cli/rabbitmqadmin
sudo chmod 755 rabbitmqadmin

cd ~/.config/sarra/
sr_audit --users foreground

sudo rabbitmqctl change_password tfeed TestFeeding
sudo rabbitmqctl change_password tsource TestSOUrCs
sudo rabbitmqctl change_password tsub TestSUBSCribe
sudo rabbitmqctl change_password tsender_src TestSENDer
sudo rabbitmqctl change_password tsender_dest TestSENDer

#sudo cp ~vagrant/rabbitmq/* /etc/rabbitmq
#sudo chmod 644 /etc/rabbitmq/*
#sudo /etc/init.d/rabbitmq-server restart
