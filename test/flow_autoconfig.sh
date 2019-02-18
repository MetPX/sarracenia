# Flow Test Autoconfig
#
# Script not meant to be run on personal machines (may break some configs)
# Intended use case is a fresh sys (tested on ubuntu18.04desktop)
# which can easily be run in a virtualbox VM.

# Install and configure dependencies
sudo apt -y install rabbitmq-server python3-pyftpdlib python3-paramiko net-tools python
echo

# Setup autossh login
ssh-keygen -t rsa
cat ~/.ssh/id_rsa.pub > ~/.ssh/authorized_keys
yes | ssh localhost "echo"
echo

# Setup basic configs
mkdir -p ~/.config/sarra

cat > ~/.config/sarra/default.conf << EOF
declare env FLOWBROKER=localhost
declare env SFTPUSER=${USER}
declare env TESTDOCROOT=${HOME}/sarra_devdocroot
declare env SR_CONFIG_EXAMPLES=${HOME}/sarracenia/sarra/examples
EOF

PASSWORD=$(openssl rand -hex 6)
cat > ~/.config/sarra/credentials.conf << EOF
amqp://bunnymaster:${PASSWORD}@localhost/
amqp://tsource:${PASSWORD}@localhost/
amqp://tsub:${PASSWORD}@localhost/
amqp://tfeed:${PASSWORD}@localhost/
amqp://anonymous:${PASSWORD}@localhost/
amqps://anonymous:anonymous@dd.weather.gc.ca
amqps://anonymous:anonymous@dd1.weather.gc.ca
amqps://anonymous:anonymous@dd2.weather.gc.ca
ftp://anonymous:anonymous@localhost:2121/
EOF

cat > ~/.config/sarra/admin.conf << EOF
cluster localhost
admin amqp://bunnymaster@localhost/
feeder amqp://tfeed@localhost/
declare source tsource
declare subscriber tsub
declare subscriber anonymous
EOF

echo

# Manage RabbitMQ
sudo rabbitmq-plugins enable rabbitmq_management

sudo rabbitmqctl delete_user guest

for USER_NAME in "bunnymaster" "tsource" "tsub" "tfeed" "anonymous"; do
sudo rabbitmqctl delete_user ${USER_NAME}
sudo rabbitmqctl add_user ${USER_NAME} ${PASSWORD}
sudo rabbitmqctl set_permissions ${USER_NAME} ".*" ".*" ".*"
done

sudo rabbitmqctl set_user_tags bunnymaster administrator

echo

sudo systemctl restart rabbitmq-server
cd /usr/local/bin
sudo mv rabbitmqadmin rabbitmqadmin.1
sudo wget http://localhost:15672/cli/rabbitmqadmin
sudo chmod 755 rabbitmqadmin

echo

# Perform sr_audit check
sr_audit --users foreground
