#!/bin/ksh

# This test suppose rabbitmq server installed
# with default configuration  guest,guest administrator

# getting rabbitmqadmin

wget http://localhost:15672/cli/rabbitmqadmin
chmod 755 rabbitmqadmin

# configuring tester user as sara requieres

./rabbitmqadmin -u guest -p guest declare user \
     name=tester password=testerpw tags=

./rabbitmqadmin -u guest -p guest declare permission \
     vhost=/  user=tester \
     configure='^q_tester.*$' write='xs_tester' read='^q_tester.*$|^xl_tester$'

./rabbitmqadmin -u guest -p guest declare exchange \
     name=xs_tester type=topic auto_delete=false durable=true

./rabbitmqadmin -u guest -p guest declare exchange \
     name=xs_guest type=topic auto_delete=false durable=true


export PYTHONPATH=../sara

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

rm ~/.config/sara/credentials.conf 2>/dev/null

echo sr_post --help

../sara/sr_post.py --help
echo

echo default broker + default exchange
echo sr_post -u file:${PWD}/toto -to alta

../sara/sr_post.py -u file:${PWD}/toto -to alta
echo

echo

echo default broker + exchange amq.topic
echo sr_post -u file:${PWD}/toto -ex amq.topic -to alta

../sara/sr_post.py -u file:${PWD}/toto -ex amq.topic -to alta
echo


echo default guest user and vhost /
echo sr_post -u file:${PWD}/toto -b amqp://localhost -to alta

../sara/sr_post.py -u file:${PWD}/toto -b amqp://localhost -to alta

echo


echo new broker user
echo sr_post -u file:${PWD}/toto -b amqp://tester:testerpw@localhost -to alta

../sara/sr_post.py -u file:${PWD}/toto -b amqp://tester:testerpw@localhost -to alta

echo


cat << EOF > sr_post.conf
url file:${PWD}/toto
EOF

echo cat sr_post.conf
cat sr_post.conf
echo
echo sr_post -c ${PWD}/sr_post.conf -b amqp://tester:testerpw@localhost

../sara/sr_post.py -c ${PWD}/sr_post.conf -b amqp://tester:testerpw@localhost -to alta

rm sr_post.conf
echo


mkdir -p ~/.config/sara 2> /dev/null
cat << EOF > ~/.config/sara/credentials.conf
amqp://tester:testerpw@localhost
EOF

echo sr_post using ~/.config/sara/credentials.conf
echo sr_post -u file:${PWD}/toto -b amqp://localhost -to alta

../sara/sr_post.py -u file:${PWD}/toto -b amqp://localhost -to alta

echo


echo sr_post -u file:${PWD}/toto -l ./toto.log -b amqp://localhost -to alta
echo cat ./toto.log

../sara/sr_post.py -u file:${PWD}/toto -l ./toto.log -b amqp://localhost -to alta
cat ./toto.log
rm  ./toto.log
echo

echo sr_post -u file:${PWD}/toto -b amqp://localhost/ -to alta

../sara/sr_post.py -u file:${PWD}/toto -b amqp://localhost/ -to alta

echo

echo sr_post -dr ${PWD} -u file://toto -b amqp://localhost/ -to alta

../sara/sr_post.py -dr ${PWD} -u file:/toto -b amqp://localhost/ -to alta

echo

echo sr_post -u file:${PWD}/toto -f my_flow -b amqp://localhost/ -to alta

../sara/sr_post.py -u file:${PWD}/toto -f my_flow -b amqp://localhost/ -to alta


echo

echo sr_post -u file:${PWD}/toto -tp v05.test -b amqp://localhost/ -to alta

../sara/sr_post.py -u file:${PWD}/toto -tp v05.test -b amqp://localhost/ -to alta


echo

echo sr_post -u file:${PWD}/toto -sub imposed.sub.topic -b amqp://localhost/ -to alta

../sara/sr_post.py -u file:${PWD}/toto -sub imposed.sub.topic -b amqp://localhost/ -to alta

echo

echo sr_post -u file:${PWD}/toto -rn /this/new/name -b amqp://localhost/ -to alta

../sara/sr_post.py -u file:${PWD}/toto -rn /this/new/name -b amqp://localhost/ -to alta


echo

echo sr_post -u file:${PWD}/toto -rn /this/new/dir/ -b amqp://localhost/ -to alta

../sara/sr_post.py -u file:${PWD}/toto -rn "/this/new/dir/" -b amqp://localhost/ -to alta

echo

echo sr_post -u file:${PWD}/toto -sum 0 -b amqp://localhost/ -to alta

../sara/sr_post.py -u file:${PWD}/toto -sum 0 -b amqp://localhost/ -to alta

echo

echo sr_post -u file:${PWD}/toto -sum n -b amqp://localhost/ -to alta

../sara/sr_post.py -u file:${PWD}/toto -sum n -b amqp://localhost/ -to alta


echo

cat << EOF > checksum_AHAH.py
class checksum_AHAH:
      def __init__(self):
              pass
      def checksum(self, filepath, offset=0, length=0 ):
          return 'AHAH'

new_check = checksum_AHAH()

self.checksum = new_check.checksum
EOF

echo sr_post -u file:${PWD}/toto -sum ${PWD}/checksum_AHAH.py -b amqp://localhost/ -to alta

../sara/sr_post.py -u file:${PWD}/toto -sum ${PWD}/checksum_AHAH.py -b amqp://localhost/ -to alta


rm ${PWD}/checksum_AHAH.py
echo

./rabbitmqadmin -u guest -p guest declare exchange \
     name=user_exchange type=topic auto_delete=false durable=true

echo user_exchange 
echo sr_post -u file:${PWD}/toto -ex user_exchange -to alta

../sara/sr_post.py -u file:${PWD}/toto -ex user_exchange -to alta

echo

cp ./toto ./toto.256.12.0.1.d.Part
echo sr_post -u file:${PWD}/toto.256.12.0.1.d.Part -p p -to alta

../sara/sr_post.py -u file:${PWD}/toto.256.12.0.1.d.Part -p p -to alta


echo sr_post -u file:${PWD}/toto.256.12.0.1.d.Part  -rn /this/new/name -p p -to alta

../sara/sr_post.py -u file:${PWD}/toto.256.12.0.1.d.Part -rn /this/new/name -p p -to alta


echo sr_post -u file:${PWD}/toto.256.12.0.1.d.Part  -rn /this/new/dir/ -p p -to alta

../sara/sr_post.py -u file:${PWD}/toto.256.12.0.1.d.Part -rn /this/new/dir/ -p p -to alta


rm ./toto.256.12.0.1.d.Part

echo

echo sr_post -u file:${PWD}/toto -p i,128 -to alta

../sara/sr_post.py -u file:${PWD}/toto -p i,128 -to alta

echo

echo sr_post -u file:${PWD}/toto -p i,64 -r -to alta

../sara/sr_post.py -u file:${PWD}/toto -p i,64 -r -to alta

echo

echo sr_post -u file:${PWD}/toto -p i,64 -rr -to alta

../sara/sr_post.py -u file:${PWD}/toto -p i,64 -rr -to alta

echo

echo sr_post -u file:${PWD}/toto -to cluster1,cluster2,cluster3

../sara/sr_post.py -u file:${PWD}/toto -to cluster1,cluster2,cluster3

echo

echo sr_post -u file:${PWD}/toto -debug -to alta

../sara/sr_post.py -u file:${PWD}/toto -debug -to alta

echo

echo ======== ERROR PART =========================
echo

echo ERROR no -to arguments
echo sr_post -u file:${PWD}/toto 

../sara/sr_post.py -u file:${PWD}/toto


echo ERROR file not found
echo sr_post -u file:${PWD}/none_existing_file -to alta

../sara/sr_post.py -u file:${PWD}/none_existing_file -to alta

echo

echo ERROR file not found
echo sr_post -dr /fake/directory -u file:/none_existing_file -to alta

../sara/sr_post.py -dr /fake/directory -u file:/none_existing_file -to alta

echo


echo ERROR config file not found
echo sr_post -c ${PWD}/none_existing_file.conf -to alta

../sara/sr_post.py -c ${PWD}/none_existing_file.conf -to alta

echo


echo ERROR broker not found
echo sr_post -u file:${PWD}/toto -b amqp://mylocalhost/ -to alta

../sara/sr_post.py -u file:${PWD}/toto -b amqp://mylocalhost/ -to alta

echo

echo ERROR broker credential
echo sr_post -u file:${PWD}/toto -b amqp://toto:titi@localhost/ -to alta

../sara/sr_post.py -u file:${PWD}/toto -b amqp://toto:titi@localhost/ -to alta

echo

echo ERROR broker vhost
echo sr_post -u file:${PWD}/toto -b amqp://localhost/wrong_vhost -to alta

../sara/sr_post.py -u file:${PWD}/toto -b amqp://localhost/wrong_vhost -to alta

echo

echo ERROR wrong sumflg
echo sr_post -u file:${PWD}/toto -sum x -to alta

../sara/sr_post.py -u file:${PWD}/toto -sum x -to alta

echo

echo ERROR wrong exchange
echo rabbitmqadmin delete exchange name=user_exchange
echo sr_post -u file:${PWD}/toto -ex user_exchange -to alta

./rabbitmqadmin -u guest -p guest delete exchange name=user_exchange
../sara/sr_post.py -u file:${PWD}/toto -ex user_exchange -to alta

echo

echo ERROR wrong partfile 1
echo cp ./toto ./toto.12.256.1.d.Part
echo sr_post -u file:${PWD}/toto.12.256.1.d.Part -p p -to alta

cp ./toto ./toto.12.256.1.d.Part
../sara/sr_post.py -u file:${PWD}/toto.12.256.1.d.Part -p p -to alta
rm ./toto.12.256.1.d.Part

echo

echo ERROR wrong partfile 2
echo cp ./toto ./toto.1024.255.1.d.Part
echo sr_post -u file:${PWD}/toto.1024.255.1.d.Part -p p -to alta

cp ./toto ./toto.1024.255.1.d.Part
../sara/sr_post.py -u file:${PWD}/toto.1024.255.1.d.Part -p p -to alta
rm ./toto.1024.255.1.d.Part

echo

echo ERROR wrong partfile 3
echo cp ./toto ./toto.1024.256.5.d.Part
echo sr_post -u file:${PWD}/toto.1024.256.5.d.Part -p p -to alta

cp ./toto ./toto.1024.256.5.d.Part
../sara/sr_post.py -u file:${PWD}/toto.1024.256.5.d.Part -p p -to alta
rm ./toto.1024.256.5.d.Part

echo

echo ERROR wrong partfile 4
echo cp ./toto ./toto.1024.256.1.x.Part
echo sr_post -u file:${PWD}/toto.1024.256.1.x.Part -p p -to alta

cp ./toto ./toto.1024.256.1.x.Part
../sara/sr_post.py -u file:${PWD}/toto.1024.256.1.x.Part -p p -to alta
rm ./toto.1024.256.1.x.Part

echo

echo ERROR wrong partfile 5
echo cp ./toto ./toto.1024.256.1.d.bad
echo sr_post -u file:${PWD}/toto.1024.256.1.d.bad -p p -to alta

cp ./toto ./toto.1024.256.1.d.bad
../sara/sr_post.py -u file:${PWD}/toto.1024.256.1.d.bad -p p -to alta
rm ./toto.1024.256.1.d.bad

echo

echo ERROR wrong partflg
echo sr_post -u file:${PWD}/toto -p x,128 -to alta

../sara/sr_post.py -u file:${PWD}/toto -p x,128 -to alta

echo

echo ERROR wrong part chunksize
echo sr_post -u file:${PWD}/toto -p d,a -to alta

../sara/sr_post.py -u file:${PWD}/toto -p d,a -to alta

echo

rm ./toto
rm ~/.config/sara/credentials.conf
