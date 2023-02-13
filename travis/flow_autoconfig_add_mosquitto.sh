# Flow Test Autoconfig
#
# Script not meant to be run on personal machines (may break some configs)
# Intended use case is a fresh sys (tested on ubuntu18.04desktop)
# which can easily be run in a virtualbox VM.

# running C components which do not support mqtt. So need to run rabbitmq setup first,
# then add the mosquitto setup.

# Install and configure dependencies
sudo apt -y install mosquitto mosquitto-clients

# Setup basic configs
mkdir -p ~/.config/sr3

sed -i 's/MQP=amqp/MQP=mqtt/' ~/.config/sr3/default.conf


ADMIN_PASSWORD=$(openssl rand -hex 6)
OTHER_PASSWORD=$(openssl rand -hex 6)
cat >> ~/.config/sr3/credentials.conf << EOF
mqtt://bunnymaster:${ADMIN_PASSWORD}@localhost/
mqtt://tsource:${OTHER_PASSWORD}@localhost/
mqtt://tsub:${OTHER_PASSWORD}@localhost/
mqtt://tfeed:${OTHER_PASSWORD}@localhost/
mqtt://anonymous:${OTHER_PASSWORD}@localhost/
EOF

echo

check_wsl=$(ps --no-headers -o comm 1)

# Manage mosquitto

cat >/tmp/pwfile <<EOT
bunnymaster:${ADMIN_PASSWORD}
tsource:${OTHER_PASSWORD}
tsub:${OTHER_PASSWORD}
tfeed:${OTHER_PASSWORD}
EOT

sudo mv /tmp/pwfile /etc/mosquitto

sudo mosquitto_passwd -U /etc/mosquitto/pwfile

cat >/tmp/aclfile <<EOT
user bunnymaster
pattern readwrite #
user tfeed
pattern readwrite #
user tsource
pattern readwrite #
user tsub
pattern readwrite #
EOT
sudo mv /tmp/aclfile /etc/mosquitto

cat >/tmp/sarra.conf <<EOT
password_file /etc/mosquitto/pwfile
max_inflight_messages 1000
max_queued_messages 1000000
message_size_limit 500000
EOT
sudo mv /tmp/sarra.conf /etc/mosquitto/conf.d



if [[ $(($check_wsl == "init" )) ]]; then
	sudo service mosquitto restart
else
	sudo systemctl restart mosquitto
fi

echo "dir: +${PWD}+"
git clone https://github.com/MetPX/sr_insects
