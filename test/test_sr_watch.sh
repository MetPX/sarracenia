#!/bin/bash

# This test suppose rabbitmq server installed
# with default configuration  guest,guest administrator

# getting rabbitmqadmin

#wget http://localhost:15672/cli/rabbitmqadmin
#chmod 755 rabbitmqadmin

# configuring tester user as sarra requieres

#./rabbitmqadmin -u guest -p guest declare user \
#     name=tester password=testerpw tags=

#./rabbitmqadmin -u guest -p guest declare permission \
#     vhost=/  user=tester \
#     configure='^q_tester.*$' write='xs_tester' read='^q_tester.*$|^xl_tester$'

#./rabbitmqadmin -u guest -p guest declare exchange \
#     name=xs_tester type=topic auto_delete=false durable=true

#./rabbitmqadmin -u guest -p guest declare exchange \
#    name=xs_guest type=topic auto_delete=false durable=true

#rm ~/.config/sarra/credentials.conf 2>/dev/null

cat << EOF > toto
0 123456789abcde
1 123456789abcde
2 123456789abcde
3 123456789abcde
4 123456789abcde
5 123456789abcde
6 123456789abcde
7 123456789abcde
8 123456789abcde
9 123456789abcde
a 123456789abcde
b 123456789abcde
c 123456789abcde
d 123456789abcde
e 123456789abcde

EOF

echo sr_watch -u file:${PWD}/ -to alta
echo touch ./toto

../sarra/sr_watch.py -u file:${PWD}/ -to alta &
PID=$!
sleep 2
touch ./toto
sleep 2
kill -9 $PID

echo ========================================

echo sr_watch -u file:${PWD}/ -e IN_CLOSE_WRITE -to alta
echo touch ./toto

../sarra/sr_watch.py -u file:${PWD}/ -e modified -to alta &
PID=$!
sleep 2
touch ./toto
sleep 2
kill -9 $PID

echo ========================================

echo sr_watch -u file:${PWD}/ -to alta
echo rm ./toto

cp toto toto2
../sarra/sr_watch.py -u file:${PWD}/ -to alta &
PID=$!
sleep 2
rm ./toto
sleep 2
kill -9 $PID

echo


#mkdir -p ~/.config/sarra 2> /dev/null
#cat << EOF > ~/.config/sarra/credentials.conf
#amqp://tester:testerpw@localhost
#EOF

echo ========================================
echo credential file
echo sr_watch -u file:${PWD}/ -e deleted -b amqp://localhost -to alta
echo rm ./toto

mv toto2 toto
../sarra/sr_watch.py -u file:${PWD}/ -e deleted -b amqp://localhost -to alta &
PID=$!
sleep 2
rm ./toto
sleep 2
kill -9 $PID

echo

