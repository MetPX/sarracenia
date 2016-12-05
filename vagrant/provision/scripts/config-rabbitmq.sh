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

sudo rabbitmqctl add_user tsource TestSOUrCs
sudo rabbitmqctl set_permissions -p / tsource "^q_tsource.*$" "^q_tsource.*$|^xs_tsource$" "^q_tsource.*$|^xs_tsource$|^xr_tsource$|^xpublic$"
sudo rabbitmqadmin -u bunnymaster -p MaestroDelConejito declare exchange name=xs_tsource type=topic auto_delete=false durable=true
sudo rabbitmqadmin -u bunnymaster -p MaestroDelConejito declare exchange name=xr_tsource type=topic auto_delete=false durable=true

sudo rabbitmqctl add_user tfeed TestFeeding
sudo rabbitmqctl set_permissions -p / tfeed ".*" ".*" ".*"
sudo rabbitmqadmin -u bunnymaster -p MaestroDelConejito declare exchange name=xs_tfeed type=topic auto_delete=false durable=true
sudo rabbitmqadmin -u bunnymaster -p MaestroDelConejito declare exchange name=xr_tfeed type=topic auto_delete=false durable=true

sudo rabbitmqctl add_user tsub TestSUBSCribe
sudo rabbitmqctl set_permissions -p / tsub "^q_tsub.*$" "^q_tsub.*$|^xs_tsub$" "^q_tsub.*$|^xr_tsub$|^xs_tsub$|^xpublic$"
sudo rabbitmqadmin -u bunnymaster -p MaestroDelConejito declare exchange name=xs_tsub type=topic auto_delete=false durable=true
sudo rabbitmqadmin -u bunnymaster -p MaestroDelConejito declare exchange name=xr_tsub type=topic auto_delete=false durable=true

sudo rabbitmqctl add_user tsender_src TestSENDer
sudo rabbitmqctl set_permissions -p / tsender_src "^q_tsender_src.*$" "^q_tsender_src.*$|^xs_tsender_src$" "^q_tsender_src.*$|^xs_tsender_src$|^xr_tsender_src$|^xpublic$"
sudo rabbitmqadmin -u bunnymaster -p MaestroDelConejito declare exchange name=xs_tsender_src type=topic auto_delete=false durable=true
sudo rabbitmqadmin -u bunnymaster -p MaestroDelConejito declare exchange name=xr_tsender_src type=topic auto_delete=false durable=true

sudo rabbitmqctl add_user tsender_dest TestSENDer
sudo rabbitmqctl set_permissions -p / tsender_dest "^q_tsender_dest.*$" "^q_tsender_dest.*$|^xs_tsender_dest$" "^q_tsender_dest.*$|^xs_tsender_dest$|^xr_tsender_dest$|^xpublic$"
sudo rabbitmqadmin -u bunnymaster -p MaestroDelConejito declare exchange name=xs_tsender_dest type=topic auto_delete=false durable=true
sudo rabbitmqadmin -u bunnymaster -p MaestroDelConejito declare exchange name=xr_tsender_dest type=topic auto_delete=false durable=true

sudo rabbitmqadmin -u bunnymaster -p MaestroDelConejito declare exchange name=xreport type=topic auto_delete=false durable=true
sudo rabbitmqadmin -u bunnymaster -p MaestroDelConejito declare exchange name=xpublic type=topic auto_delete=false durable=true

#sudo cp ~vagrant/rabbitmq/* /etc/rabbitmq
#sudo chmod 644 /etc/rabbitmq/*
#sudo /etc/init.d/rabbitmq-server restart
