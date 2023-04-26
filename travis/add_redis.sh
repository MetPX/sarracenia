sudo apt -y install redis

# enable auth for Redis
REDIS_SR3_PASSWORD=$(openssl rand -hex 6)
cat >> /etc/redis/redis.conf << EOF
user sr3 on >${REDIS_SR3_PASSWORD} ~* +@all
user default off
EOF
check_wsl=$(ps --no-headers -o comm 1)

# Start Redis Service
if [[ $(($check_wsl == "init" )) ]]; then
	sudo service redis-server restart
else
	sudo systemctl restart redis-server
fi

# Install Python modules
pip3 install redis python-redis-lock

# Set redis defaults for sr3
cat >> ~/.config/sr3/default.conf << EOF
retry_driver redis
redisqueue_serverurl redis://sr3:${REDIS_SR3_PASSWORD}@localhost:6379/0
EOF