#!/bin/bash

# This test suppose rabbitmq server installed on localhost

# some setting required  

# amqp://guest:guest@localhost/
# all permissions for guest on localhost broker
# exchange   xs_guest  created

# amqp://tester:testerpw@localhost/
# all permissions for tester on localhost broker
# exchange   xs_tester  created

# run from metpx-git/sarracenia/test
# invoking  ../sarra/sr_post.py for testing purpose

# the end of the script finishes with a
# desired error section

export PYTHONPATH=../sarra

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

echo sr_post --help

../sarra/sr_post.py --debug --help
echo

echo default broker + default exchange
echo sr_post -u file:${PWD}/toto -to alta

../sarra/sr_post.py --debug -u file: -to alta -path ${PWD}/toto
echo

# checking caching
echo  -blocksize -caching -reset
../sarra/sr_post.py --debug        -blocksize 1000Mb --caching -u file: -to alta -path ${PWD}/toto
../sarra/sr_post.py --debug        -blocksize 1000Mb --caching -u file: -to alta -path ${PWD}/toto
../sarra/sr_post.py --debug -reset -blocksize 1000Mb --caching -u file: -to alta -path ${PWD}/toto

echo

echo default broker + exchange amq.topic
echo sr_post -u file: -ex amq.topic -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -ex amq.topic -to alta -path ${PWD}/toto
echo


echo default guest user and vhost /
echo sr_post -u file: -b amqp://localhost -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -b amqp://localhost -to alta -path ${PWD}/toto

echo


echo new broker user
echo sr_post -u file: -b amqp://tester:testerpw@localhost -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -b amqp://tester:testerpw@localhost -to alta -path ${PWD}/toto

echo


cat << EOF > sr_post.conf
url file:
EOF

echo cat sr_post.conf
cat sr_post.conf
echo
echo sr_post -c ${PWD}/sr_post.conf -b amqp://tester:testerpw@localhost -path ${PWD}/toto

../sarra/sr_post.py --debug -c ${PWD}/sr_post.conf -b amqp://tester:testerpw@localhost -to alta -path ${PWD}/toto

rm sr_post.conf
echo


mkdir -p ~/.config/sarra 2> /dev/null

echo sr_post using ~/.config/sarra/credentials.conf 
echo sr_post -u file: -b amqp://localhost -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -b amqp://localhost -to alta -path ${PWD}/toto

echo


echo sr_post -u file: -l ./toto.log -b amqp://localhost -to alta -path ${PWD}/toto
echo cat ./toto.log

../sarra/sr_post.py --debug -u file: -l ./toto.log -b amqp://localhost -to alta -path ${PWD}/toto
cat ./toto.log
rm  ./toto.log
echo

echo sr_post -u file: -b amqp://localhost/ -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -b amqp://localhost/ -to alta -path ${PWD}/toto

echo

echo sr_post -dr ${PWD} -u file: -b amqp://localhost/ -to alta -path /toto

../sarra/sr_post.py --debug -dr ${PWD} -u file: -b amqp://localhost/ -to alta -path ${PWD}/toto

echo

echo sr_post -u file: -f my_flow -b amqp://localhost/ -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -f my_flow -b amqp://localhost/ -to alta -path ${PWD}/toto


echo

echo sr_post -u file: -tp v05.test -b amqp://localhost/ -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -tp v05.test -b amqp://localhost/ -to alta -path ${PWD}/toto


echo

echo sr_post -u file: -sub imposed.sub.topic -b amqp://localhost/ -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -sub imposed.sub.topic -b amqp://localhost/ -to alta -path ${PWD}/toto

echo


# strip rename
echo  -strip -rename

echo sr_post -u file: -rn /this/new/name -b amqp://localhost/ -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -rn /this/new/name -b amqp://localhost/ -to alta -path ${PWD}/toto

echo sr_post -u file: -strip 3 -b amqp://localhost/ -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -strip 3 -b amqp://localhost/ -to alta -path ${PWD}/toto


echo

echo sr_post -u file: -rn /this/new/dir/ -b amqp://localhost/ -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -rn "/this/new/dir/" -b amqp://localhost/ -to alta -path ${PWD}/toto

echo

echo sr_post -u file: -sum 0 -b amqp://localhost/ -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -sum 0 -b amqp://localhost/ -to alta -path ${PWD}/toto

echo

echo sr_post -u file: -sum n -b amqp://localhost/ -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -sum n -b amqp://localhost/ -to alta -path ${PWD}/toto


echo

echo sr_post -u file: -sum z,d -b amqp://localhost/ -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -sum z,d -b amqp://localhost/ -to alta -path ${PWD}/toto


echo

cat << EOF > checksum_AHAH.py
class checksum_AHAH:
      def __init__(self):
          pass
      def get_value(self):
          return 'AHAH'
      def update(self,chunk):
          pass
      def set_path(self, path ):
          pass

self.sumalgo = checksum_AHAH()
EOF

echo sr_post -u file: -sum ${PWD}/checksum_AHAH.py -b amqp://localhost/ -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -sum ${PWD}/checksum_AHAH.py -b amqp://localhost/ -to alta -path ${PWD}/toto


#rm ${PWD}/checksum_AHAH.py
echo

./rabbitmqadmin -u guest -p guest declare exchange \
     name=user_exchange type=topic auto_delete=false durable=true

echo user_exchange 
echo sr_post -u file: -ex user_exchange -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -ex user_exchange -to alta -path ${PWD}/toto

echo

cp ./toto ./toto.256.12.0.1.d.Part
echo sr_post -u file: -parts p -to alta -path ${PWD}/toto.256.12.0.1.d.Part

../sarra/sr_post.py --debug -u file: -parts p -to alta -path ${PWD}/toto.256.12.0.1.d.Part


echo sr_post -u file:  -rn /this/new/name -parts p -to alta -path ${PWD}/toto.256.12.0.1.d.Part

../sarra/sr_post.py --debug -u file: -rn /this/new/name -parts p -to alta -path ${PWD}/toto.256.12.0.1.d.Part


echo sr_post -u file:  -rn /this/new/dir/ -parts p -to alta -path ${PWD}/toto.256.12.0.1.d.Part

../sarra/sr_post.py --debug -u file: -rn /this/new/dir/ -parts p -to alta -path ${PWD}/toto.256.12.0.1.d.Part


rm ./toto.256.12.0.1.d.Part

echo

echo sr_post -u file: -parts i,128 -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -parts i,128 -to alta -path ${PWD}/toto

echo

echo sr_post -u file: -parts i,64 -r -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -parts i,64 -r -to alta -path ${PWD}/toto

echo

echo sr_post -u file: -parts i,64 -rr -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -parts i,64 -rr -to alta -path ${PWD}/toto

echo

echo sr_post -u file: -to cluster1,cluster2,cluster3 -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -to cluster1,cluster2,cluster3 -path ${PWD}/toto

echo

echo sr_post -u file: -debug -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -debug -to alta -path ${PWD}/toto

echo

echo ======== ERROR PART =========================
echo

echo ERROR no -to arguments
echo sr_post -u file:  -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -path ${PWD}/toto


echo ERROR file not found
echo sr_post -u file: -to alta -path ${PWD}/none_existing_file

../sarra/sr_post.py --debug -u file: -to alta -path ${PWD}/none_existing_file

echo

echo ERROR file not found
echo sr_post -dr /fake/directory -u file: -to alta -path ${PWD}/none_existing_file

../sarra/sr_post.py --debug -dr /fake/directory -u file: -to alta -path ${PWD}/none_existing_file

echo


echo ERROR config file not found
echo sr_post -c ${PWD}/none_existing_file.conf -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -c ${PWD}/none_existing_file.conf -to alta -path ${PWD}/toto

echo


echo ERROR broker not found
echo sr_post -u file: -b amqp://mylocalhost/ -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -b amqp://mylocalhost/ -to alta -path ${PWD}/toto

echo

echo ERROR broker credential
echo sr_post -u file: -b amqp://toto:titi@localhost/ -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -b amqp://toto:titi@localhost/ -to alta -path ${PWD}/toto

echo

echo ERROR broker vhost
echo sr_post -u file: -b amqp://localhost/wrong_vhost -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -b amqp://localhost/wrong_vhost -to alta -path ${PWD}/toto

echo

echo ERROR wrong sumflg
echo sr_post -u file: -sum x -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -sum x -to alta -path ${PWD}/toto

echo

echo ERROR wrong exchange
echo rabbitmqadmin delete exchange name=user_exchange
echo sr_post -u file:${PWD}/toto -ex user_exchange -to alta -path ${PWD}/toto

./rabbitmqadmin -u guest -p guest delete exchange name=user_exchange -path ${PWD}/toto
../sarra/sr_post.py --debug -u file: -ex user_exchange -to alta -path ${PWD}/toto

echo

echo ERROR wrong partfile 1
echo cp ./toto ./toto.12.256.1.d.Part
echo sr_post -u file: -parts p -to alta -path ${PWD}/toto.12.256.1.d.Part 

cp ./toto ./toto.12.256.1.d.Part
../sarra/sr_post.py --debug -u file: -parts p -to alta -path ${PWD}/toto.12.256.1.d.Part
rm ./toto.12.256.1.d.Part

echo

echo ERROR wrong partfile 2
echo cp ./toto ./toto.1024.255.1.d.Part
echo sr_post -u file: -parts p -to alta -path ${PWD}/toto.1024.255.1.d.Part

cp ./toto ./toto.1024.255.1.d.Part
../sarra/sr_post.py --debug -u file:${PWD} -parts p -to alta -path ${PWD}/toto.1024.255.1.d.Part
rm ./toto.1024.255.1.d.Part

echo

echo ERROR wrong partfile 3
echo cp ./toto ./toto.1024.256.5.d.Part
echo sr_post -u file: -parts p -to alta -path ${PWD}/toto.1024.256.5.d.Part

cp ./toto ./toto.1024.256.5.d.Part
../sarra/sr_post.py --debug -u file: -parts p -to alta -path ${PWD}/toto.1024.256.5.d.Part
rm ./toto.1024.256.5.d.Part

echo

echo ERROR wrong partfile 4
echo cp ./toto ./toto.1024.256.1.x.Part
echo sr_post -u file: -parts p -to alta -path ${PWD}/toto.1024.256.1.x.Part

cp ./toto ./toto.1024.256.1.x.Part
../sarra/sr_post.py --debug -u file: -parts p -to alta -path ${PWD}/toto.1024.256.1.x.Part
rm ./toto.1024.256.1.x.Part

echo

echo ERROR wrong partfile 5
echo cp ./toto ./toto.1024.256.1.d.bad
echo sr_post -u file: -parts p -to alta -path ${PWD}/toto.1024.256.1.d.bad

cp ./toto ./toto.1024.256.1.d.bad
../sarra/sr_post.py --debug -u file: -parts p -to alta -path ${PWD}/toto.1024.256.1.d.bad
rm ./toto.1024.256.1.d.bad

echo

echo ERROR wrong partflg
echo sr_post -u file: -parts x,128 -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -parts x,128 -to alta -path ${PWD}/toto

echo

echo ERROR wrong part chunksize
echo sr_post -u file: -parts d,a -to alta -path ${PWD}/toto

../sarra/sr_post.py --debug -u file: -parts d,a -to alta -path ${PWD}/toto

echo

rm ./toto
