# SSC Dorval: Data Interchange Group
# Written by Michael Saraga - 13/02/2019
# 	     mic.saraga@gmail.com
#
# N.B.
# Script not meant to be run on local machines (may break some configs)
# Intended use case is a fresh sys (dev on ubuntu16.04server)
# Which can easily be run in a virtualbox VM

# Install and configure dependencies
sudo apt -y install rabbitmq-server python3-pyftpdlib python3-paramiko

# Create flow test users
PASSWORD=$(openssl rand -hex 6)
echo ${PASSWORD} > ~/.config/sarra/flow_test_passwd.txt

for USER_NAME in "bunnymaster" "tsource" "tsub" "tfeed"; do
	sudo useradd -m ${USER_NAME}
	echo ${USER_NAME}:${PASSWORD} | sudo chpasswd
done

# Add ssh keys to their accounts (all get the same)
# FIXME: Not sure who should get what, everyone gets everything 
for USER_NAME in ${USER} "bunnymaster" "tsource" "tsub" "tfeed"; do

USER_HOME=$(eval echo "~${USER_NAME}")

sudo su ${USER_NAME} << EOSU
mkdir -p ${USER_HOME}/.ssh

cat > ${USER_HOME}/.ssh/id_rsa << EOF
-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEArI6wsAQiGm9oH+1vps8rGeAvpWSGVrFFRi3JCkNG54yQafak
FvhqJbQpkhKOkTe9NnBxoAs43Uxh2g09lc0jdHb8VgGSo0hOhOvsOOod4Zf2IQo4
NXezR7tm7kp55exwCYlRfGL0uwf4yNhZm1yA/TjRFS3EVa5AdJkPmTv9u6S4YUTO
5/1kNnJwrVoldkjBT1ShhpupzjNAxDWaR3wqbC2KUXZEGuWamo2MzD/FTrmJ4PM6
Qh4jG1QnpjNJOtgIXu4MEzwSvz5NfF4u+4igcV8B7mWbLxPwNvzv/cHLfsOmUBvI
FcaJOg8ak/hqeCqx9igCarLtLOU7PLXl1dx7TwIDAQABAoIBAQCfyZYlt/4Yepdy
ET01u1tPH8EfJ6IafxcF8HnczgXHfutvpBu4xZoNhfKEuDhaksHcum0NZbbnfcaS
03X21LoDK/docRZnqxpCjfD1lx3KfBxH5h28rTZPs2KSQFb2qWXp/sV9KGk1FCG1
Ylo/un4bflRmhzXqnWxETEQcgmfoLA9IAwcbtG0VrXLH610kQY94OfWERcL7dN1Q
9pvG8N1u5QpzIu1HgakCM5d2XZyLM9toUfGJ+p9Cq/femX+TNq9avWLuc4/5xVoP
yTxR7i0mx5OlZ4IAAtf/QR3c1ZQBF6tzMEkN8wjGx8Tm8PxLnC80cCmHgxbbnazo
kcylxKsZAoGBAN6VNGyn3bkaI7qidIlVHm5GQXLEgOsnDfnAjVqB9tqjNsbvxSmt
1zAP+gzvD1Se2HBdXuzMGRvcivjNDuGoeA06COBt945bTXetevMsF4ev2t49hzr2
vRQCb8GkTA7uPGBRztimv2t8kTRAO37QSTOYYtkbPPm+8oBOPBZTXnSVAoGBAMZ2
y/7AxNs2UM9Wq7q7LvC+g3SfMBjXNdgItPkJIl00ZBw5T+BmigiBztC532ww5592
lufpoKSQU3ALfbcQWvebepHNbKYdZUiti15r21GsrbfSuGvoL9CgHXlYAcY9GVPt
Xn7NZYDWvq64yQJmEW19faBe9ewCuCFzEITtNzNTAoGAbObxlGv5drRMYOdVP1Av
KGMlaIKuVN9x3g2Q24SVA9oxVdpATCkrDO/0NtnMVWm2mhuE8zTU4CXitOKXcl8c
BdSsPSpwoe0YFQMDEfEzvgaTfoL6JCZO0nhyt3qsX+2+Cp5cJvJG289BuB/pPB2q
gxz+2ByUk9kSCya8DWxS3ZUCgYEArVXeb16/0FHNHHmvPUT1B3DtcTMDl/6G2Wsp
XIR8zfjPItNvjycfkbSGBEkC+QRxmBXEUUL8eh5PsYFnyDZxrObPk35eUWtFJcfk
/I+pGtl9VBqn1h8Re94MQAn8ar68W0/rA0azS2bDXeioLv8kY4OB8Epf8USiuxw7
Jk3ks18CgYEAn5TPGG5Zg5BU4Jtq5+FbZBFv0Zk3czl7qug84syfHiZkSKX9r4kh
1CYSqwoP8D9D6Lp3/JtQV58dcC4b/Ku5QEeZufsrLX4QMMx5ygFag5ddfGrsKu6o
76j25OknGNEuolz+aE2L09em8Zn/ekR2fOvgriuLaepCVJW2GfVbD6E=
-----END RSA PRIVATE KEY-----
EOF

cat > ${USER_HOME}/.ssh/id_rsa.pub << EOF
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsjrCwBCIab2gf7W+mzysZ4C+lZIZWsUVGLckKQ0bnjJBp9qQW+GoltCmSEo6RN702cHGgCzjdTGHaDT2VzSN0dvxWAZKjSE6E6+w46h3hl/YhCjg1d7NHu2buSnnl7HAJiVF8YvS7B/jI2FmbXID9ONEVLcRVrkB0mQ+ZO/27pLhhRM7n/WQ2cnCtWiV2SMFPVKGGm6nOM0DENZpHfCpsLYpRdkQa5ZqajYzMP8VOuYng8zpCHiMbVCemM0k62Ahe7gwTPBK/Pk18Xi77iKBxXwHuZZsvE/A2/O/9wct+w6ZQG8gVxok6DxqT+Gp4KrH2KAJqsu0s5Ts8teXV3HtP ${USER_NAME}@${HOSTNAME}
EOF

cat > ${USER_HOME}/.ssh/authorized_keys << EOF
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsjrCwBCIab2gf7W+mzysZ4C+lZIZWsUVGLckKQ0bnjJBp9qQW+GoltCmSEo6RN702cHGgCzjdTGHaDT2VzSN0dvxWAZKjSE6E6+w46h3hl/YhCjg1d7NHu2buSnnl7HAJiVF8YvS7B/jI2FmbXID9ONEVLcRVrkB0mQ+ZO/27pLhhRM7n/WQ2cnCtWiV2SMFPVKGGm6nOM0DENZpHfCpsLYpRdkQa5ZqajYzMP8VOuYng8zpCHiMbVCemM0k62Ahe7gwTPBK/Pk18Xi77iKBxXwHuZZsvE/A2/O/9wct+w6ZQG8gVxok6DxqT+Gp4KrH2KAJqsu0s5Ts8teXV3HtP ${USER}@${HOSTNAME}
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsjrCwBCIab2gf7W+mzysZ4C+lZIZWsUVGLckKQ0bnjJBp9qQW+GoltCmSEo6RN702cHGgCzjdTGHaDT2VzSN0dvxWAZKjSE6E6+w46h3hl/YhCjg1d7NHu2buSnnl7HAJiVF8YvS7B/jI2FmbXID9ONEVLcRVrkB0mQ+ZO/27pLhhRM7n/WQ2cnCtWiV2SMFPVKGGm6nOM0DENZpHfCpsLYpRdkQa5ZqajYzMP8VOuYng8zpCHiMbVCemM0k62Ahe7gwTPBK/Pk18Xi77iKBxXwHuZZsvE/A2/O/9wct+w6ZQG8gVxok6DxqT+Gp4KrH2KAJqsu0s5Ts8teXV3HtP bunnymaster@${HOSTNAME}
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsjrCwBCIab2gf7W+mzysZ4C+lZIZWsUVGLckKQ0bnjJBp9qQW+GoltCmSEo6RN702cHGgCzjdTGHaDT2VzSN0dvxWAZKjSE6E6+w46h3hl/YhCjg1d7NHu2buSnnl7HAJiVF8YvS7B/jI2FmbXID9ONEVLcRVrkB0mQ+ZO/27pLhhRM7n/WQ2cnCtWiV2SMFPVKGGm6nOM0DENZpHfCpsLYpRdkQa5ZqajYzMP8VOuYng8zpCHiMbVCemM0k62Ahe7gwTPBK/Pk18Xi77iKBxXwHuZZsvE/A2/O/9wct+w6ZQG8gVxok6DxqT+Gp4KrH2KAJqsu0s5Ts8teXV3HtP tsource@${HOSTNAME}
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsjrCwBCIab2gf7W+mzysZ4C+lZIZWsUVGLckKQ0bnjJBp9qQW+GoltCmSEo6RN702cHGgCzjdTGHaDT2VzSN0dvxWAZKjSE6E6+w46h3hl/YhCjg1d7NHu2buSnnl7HAJiVF8YvS7B/jI2FmbXID9ONEVLcRVrkB0mQ+ZO/27pLhhRM7n/WQ2cnCtWiV2SMFPVKGGm6nOM0DENZpHfCpsLYpRdkQa5ZqajYzMP8VOuYng8zpCHiMbVCemM0k62Ahe7gwTPBK/Pk18Xi77iKBxXwHuZZsvE/A2/O/9wct+w6ZQG8gVxok6DxqT+Gp4KrH2KAJqsu0s5Ts8teXV3HtP tsub@${HOSTNAME}
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCsjrCwBCIab2gf7W+mzysZ4C+lZIZWsUVGLckKQ0bnjJBp9qQW+GoltCmSEo6RN702cHGgCzjdTGHaDT2VzSN0dvxWAZKjSE6E6+w46h3hl/YhCjg1d7NHu2buSnnl7HAJiVF8YvS7B/jI2FmbXID9ONEVLcRVrkB0mQ+ZO/27pLhhRM7n/WQ2cnCtWiV2SMFPVKGGm6nOM0DENZpHfCpsLYpRdkQa5ZqajYzMP8VOuYng8zpCHiMbVCemM0k62Ahe7gwTPBK/Pk18Xi77iKBxXwHuZZsvE/A2/O/9wct+w6ZQG8gVxok6DxqT+Gp4KrH2KAJqsu0s5Ts8teXV3HtP tfeed@${HOSTNAME}
EOF

ssh-keyscan -H localhost > ${USER_HOME}/.ssh/known_hosts

EOSU
done

# Setup basic configs
mkdir ~/.config/sarra

cat > ~/.config/sarra/default.conf << EOF
declare env FLOWBROKER=localhost
declare env SFTPUSER=${USER}
declare env TESTDOCROOT=${HOME}/sarra_devdocroot
declare env SR_CONFIG_EXAMPLES=${HOME}/sarracenia/sarra/examples
EOF

cat > ~/.config/sarra/credentials.conf << EOF
amqp://bunnymaster:${PASSWORD}@localhost/
amqp://tsource:${PASSWORD}@localhost/
amqp://tsub:${PASSWORD}@localhost/
amqp://tfeed:${PASSWORD}@localhost/
amqps://anonymous:anonymous@dd.weather.gc.ca
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

# Manage RabbitMQ
sudo rabbitmq-plugins enable rabbitmq_management

sudo rabbitmqctl delete_user guest
sudo rabbitmqctl add_user bunnymaster ${PASSWORD}
sudo rabbitmqctl set_permissions bunnymaster ".*" ".*" ".*"
sudo rabbitmqctl set_user_tags bunnymaster administrator

sudo systemctl restart rabbitmq-server
cd /usr/local/bin
sudo mv rabbitmqadmin rabbitmqadmin.1
sudo wget http://localhost:15672/cli/rabbitmqadmin
sudo chmod 755 rabbitmqadmin

# Perform sr_audit user check?
# XXX WTF XXX
# sr_audit --users foreground
