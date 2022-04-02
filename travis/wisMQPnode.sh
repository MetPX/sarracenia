# Flow Test Autoconfig
#
# Script not meant to be run on personal machines (may break some configs)
# Intended use case is a fresh sys (tested on ubuntu18.04desktop)
# which can easily be run in a virtualbox VM.

# Install and configure dependencies
sudo add-apt-repository -y ppa:ssc-hpc-chp-spc/metpx-daily
sudo apt-get update
sudo apt -y install rabbitmq-server erlang-nox metpx-sr3 metpx-sr3c librabbitmq4 metpx-libsr3c metpx-libsr3c-dev git python3-pip net-tools

# install webfs (very basic web server.)
sudo apt install webfs

# Setup basic configs
mkdir -p ~/.config/sr3

cat > ~/.config/sr3/default.conf << EOF
declare env SFTPUSER=${USER}
declare env MQP=amqp
EOF

ADMIN_PASSWORD=$(openssl rand -hex 6)
FEED_PASSWORD=$(openssl rand -hex 6)
SUB_PASSWORD=$(openssl rand -hex 6)
SOURCE_PASSWORD=$(openssl rand -hex 6)
cat > ~/.config/sr3/credentials.conf << EOF
amqp://bunnymaster:${ADMIN_PASSWORD}@localhost/
amqp://tsource:${SOURCE_PASSWORD}@localhost/
amqp://tsub:${SUB_PASSWORD}@localhost/
amqp://tfeed:${FEED_PASSWORD}@localhost/
amqp://anonymous:anonymous@localhost/
amqps://anonymous:anonymous@dd.weather.gc.ca
amqps://anonymous:anonymous@dd1.weather.gc.ca
amqps://anonymous:anonymous@dd2.weather.gc.ca
amqps://anonymous:anonymous@hpfx.collab.science.gc.ca
ftp://anonymous:anonymous@localhost:2121/
EOF

cat > ~/.config/sr3/admin.conf << EOF
admin amqp://bunnymaster@localhost/
feeder amqp://tfeed@localhost/
declare source tsource
declare subscriber tsub
declare subscriber anonymous
EOF

echo

# Manage RabbitMQ
sudo systemctl restart rabbitmq-server
sudo rabbitmq-plugins enable rabbitmq_management

sudo rabbitmqctl delete_user guest

for USER_NAME in "bunnymaster" "tsource" "tsub" "tfeed" "anonymous"; do
sudo rabbitmqctl delete_user ${USER_NAME}
done

sudo rabbitmqctl add_user bunnymaster ${ADMIN_PASSWORD}
sudo rabbitmqctl set_permissions bunnymaster ".*" ".*" ".*"
sudo rabbitmqctl set_user_tags bunnymaster administrator

echo

sudo systemctl restart rabbitmq-server
cd /usr/local/bin
sudo mv rabbitmqadmin rabbitmqadmin.1
sudo wget http://localhost:15672/cli/rabbitmqadmin
sudo chmod 755 rabbitmqadmin
cd 

echo

mkdir /var/www
mkdir /var/www/html
chown ${USER} /var/www/html

# Configure users
sr3 add subscribe/wisAMQPnode_mirror.conf
sr3 --users declare
