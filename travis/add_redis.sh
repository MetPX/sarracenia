sudo apt -y install redis

check_wsl=$(ps --no-headers -o comm 1)

if [[ $(($check_wsl == "init" )) ]]; then
	sudo service redis-server restart
else
	sudo systemctl restart redis-server
fi

pip3 install redis python-redis-lock

cat >> ~/.config/sr3/default.conf << EOF
retry_driver redis
redisqueue_serverurl redis://localhost:6379/0
EOF