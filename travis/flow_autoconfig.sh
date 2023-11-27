# Flow Test Autoconfig
#
# Script not meant to be run on personal machines (may break some configs)
# Intended use case is a fresh sys (tested on ubuntu18.04desktop)
# which can easily be run in a virtualbox VM.

# Install and configure dependencies
sudo apt-key adv --keyserver "hkps.pool.sks-keyservers.net" --recv-keys "0x6B73A36E6026DFCA"
sudo add-apt-repository -y ppa:ssc-hpc-chp-spc/metpx-daily
sudo apt-get update
sudo apt -y install openssh-server erlang-nox erlang-diameter erlang-eldap rabbitmq-server sarrac librabbitmq4 libsarrac libsarrac-dev git python3-pip python3-setuptools net-tools findutils xattr

pip3 install -U pip
pip3 install -e .
pip3 install pyftpdlib paramiko net-tools

# The dependencies that are installed using apt are only available to system default Python versions (e.g. Python 3.8 on Ubuntu 20.04)
# If we are testing on a non-default Python version, we need to ensure these dependencies are still installed, so we use pip.
# See issue #407, #445.
for PKG in amqp appdirs dateparser watchdog netifaces humanize jsonpickle psutil xattr rangehttpserver; do
    PKG_INSTALLED="`pip3 list | grep ${PKG}`"
    if [ "$?" == "0" ] ; then
        echo "$PKG is already installed"
    else
        pip3 install ${PKG}
    fi
done

# Setup basic configs
mkdir -p ~/.config/sarra

cat > ~/.config/sarra/default.conf << EOF
expire 7h
declare env FLOWBROKER=localhost
declare env SFTPUSER=${USER}
declare env TESTDOCROOT=${HOME}/sarra_devdocroot
declare env MQP=amqp
logEvents after_accept,after_work,on_housekeeping,post
EOF


ADMIN_PASSWORD=$(openssl rand -hex 6)
OTHER_PASSWORD=$(openssl rand -hex 6)
cat > ~/.config/sarra/credentials.conf << EOF
amqp://bunnymaster:${ADMIN_PASSWORD}@localhost/
amqp://tsource:${OTHER_PASSWORD}@localhost/
amqp://tsub:${OTHER_PASSWORD}@localhost/
amqp://tfeed:${OTHER_PASSWORD}@localhost/
amqp://anonymous:${OTHER_PASSWORD}@localhost/
amqps://anonymous:anonymous@dd.weather.gc.ca
amqps://anonymous:anonymous@dd1.weather.gc.ca
amqps://anonymous:anonymous@dd2.weather.gc.ca
amqps://anonymous:anonymous@hpfx.collab.science.gc.ca
ftp://anonymous:anonymous@localhost:2121/
EOF
cp ~/.config/sarra/credentials.conf 

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

# Configure users
sr_audit -users declare
echo "dir: +${PWD}+"
git clone https://github.com/MetPX/sr_insects

