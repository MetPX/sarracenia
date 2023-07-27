# Flow Test Autoconfig
#
# Script not meant to be run on personal machines (may break some configs)
# Intended use case is a fresh sys (tested on ubuntu18.04desktop)
# which can easily be run in a virtualbox VM.

# Install and configure dependencies
sudo apt-key adv --keyserver "hkps.pool.sks-keyservers.net" --recv-keys "0x6B73A36E6026DFCA"
sudo add-apt-repository -y ppa:ssc-hpc-chp-spc/metpx
sudo apt update
sudo apt upgrade
sudo apt -y install python3-setuptools python3-magic
sudo apt -y install metpx-libsr3c metpx-libsr3c-dev metpx-sr3c
sudo apt -y install metpx-libsr3c metpx-libsr3c-dev metpx-sr3c
sudo apt -y install erlang-nox erlang-diameter erlang-eldap findutils git librabbitmq4 net-tools openssh-client openssh-server python3-pip rabbitmq-server xattr wget 

pip3 install -U pip
pip3 install pyftpdlib paramiko net-tools

# The dependencies that are installed using apt are only available to system default Python versions (e.g. Python 3.8 on Ubuntu 20.04)
# If we are testing on a non-default Python version, we need to ensure these dependencies are still installed, so we use pip.
# See issue #407, #445.
for PKG in amqp appdirs dateparser watchdog netifaces humanize jsonpickle paho-mqtt psutil xattr ; do
    PKG_INSTALLED="`pip3 list | grep ${PKG}`"
    if [ "$?" == "0" ] ; then
        echo "$PKG is already installed"
    else
        pip3 install ${PKG}
    fi
done

# in case it was installed as a dependency.
sudo apt -y remove metpx-sr3

pip3 install -e .

# Setup basic configs
mkdir -p ~/.config/sarra ~/.config/sr3

cat > ~/.config/sarra/default.conf << EOF
expire 7h
declare env FLOWBROKER=localhost
declare env SFTPUSER=${USER}
declare env TESTDOCROOT=${HOME}/sarra_devdocroot
declare env MQP=amqp
declare env several=3
logEvents after_accept,after_work,on_housekeeping,post,after_post
EOF
cp ~/.config/sarra/default.conf ~/.config/sr3


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
cp ~/.config/sarra/credentials.conf ~/.config/sr3

cat > ~/.config/sarra/admin.conf << EOF
cluster localhost
admin amqp://bunnymaster@localhost/
feeder amqp://tfeed@localhost/
declare source tsource
declare subscriber tsub
declare subscriber anonymous
EOF
cp ~/.config/sarra/admin.conf ~/.config/sr3

echo

check_wsl=$(ps --no-headers -o comm 1)

# Manage RabbitMQ
if [[ $(($check_wsl == "init" )) ]]; then
	sudo service rabbitmq-server restart
else
	sudo systemctl restart rabbitmq-server
fi
sudo rabbitmq-plugins enable rabbitmq_management

sudo rabbitmqctl delete_user guest

for USER_NAME in "bunnymaster" "tsource" "tsub" "tfeed" "anonymous"; do
sudo rabbitmqctl delete_user ${USER_NAME}
done

sudo rabbitmqctl add_user bunnymaster ${ADMIN_PASSWORD}
sudo rabbitmqctl set_permissions bunnymaster ".*" ".*" ".*"
sudo rabbitmqctl set_user_tags bunnymaster administrator

echo

if [[ $(($check_wsl == "init" )) ]]; then
	sudo service rabbitmq-server restart
else 
	sudo systemctl restart rabbitmq-server
fi

cd /usr/local/bin
sudo mv rabbitmqadmin rabbitmqadmin.1
sudo wget http://localhost:15672/cli/rabbitmqadmin
sudo chmod 755 rabbitmqadmin
cd 

echo

# Configure users
sr3 --users declare
echo "dir: +${PWD}+"
git clone https://github.com/MetPX/sr_insects

