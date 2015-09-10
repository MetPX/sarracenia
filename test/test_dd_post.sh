#!/bin/ksh

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

echo dd_post -h

../sara/dd_post.py -h

echo

echo dd_post -u file:${PWD}/toto

../sara/dd_post.py -u file:${PWD}/toto

echo


cat << EOF > dd_post.conf
url file:${PWD}/toto
EOF

echo cat dd_post.conf
cat dd_post.conf
echo
echo dd_post -c ${PWD}/dd_post.conf

../sara/dd_post.py -c ${PWD}/dd_post.conf

rm dd_post.conf
echo

echo dd_post -u file:${PWD}/toto -l ./toto.log
echo cat ./toto.log

../sara/dd_post.py -u file:${PWD}/toto -l ./toto.log
cat ./toto.log
rm  ./toto.log
echo

echo dd_post -u file:${PWD}/toto -b amqp://localhost/

../sara/dd_post.py -u file:${PWD}/toto -b amqp://localhost/

echo

echo dd_post -dr ${PWD} -u file://toto

../sara/dd_post.py -dr ${PWD} -u file:/toto

echo

echo dd_post -u file:${PWD}/toto -f my_flow

../sara/dd_post.py -u file:${PWD}/toto -f my_flow

echo

echo dd_post -u file:${PWD}/toto -tp v05.test

../sara/dd_post.py -u file:${PWD}/toto -tp v05.test

echo

echo dd_post -u file:${PWD}/toto -sub imposed.sub.topic

../sara/dd_post.py -u file:${PWD}/toto -sub imposed.sub.topic

echo

echo dd_post -u file:${PWD}/toto -rn /this/new/name

../sara/dd_post.py -u file:${PWD}/toto -rn /this/new/name

echo

echo dd_post -u file:${PWD}/toto -rn /this/new/dir/

../sara/dd_post.py -u file:${PWD}/toto -rn /this/new/dir/

echo

echo dd_post -u file:${PWD}/toto -sum 0

../sara/dd_post.py -u file:${PWD}/toto -sum 0

echo

echo dd_post -u file:${PWD}/toto -sum n

../sara/dd_post.py -u file:${PWD}/toto -sum n

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

echo dd_post -u file:${PWD}/toto -sum ${PWD}/checksum_AHAH.py

../sara/dd_post.py -u file:${PWD}/toto -sum ${PWD}/checksum_AHAH.py

rm ${PWD}/checksum_AHAH.py
echo

echo ./exchange.py user_exchange add
echo dd_post -u file:${PWD}/toto -ex user_exchange

python3 ./exchange.py user_exchange add
../sara/dd_post.py -u file:${PWD}/toto -ex user_exchange

echo

cp ./toto ./toto.1024.256.1.d.Part
echo dd_post -u file:${PWD}/toto.1024.256.1.d.Part -p p

../sara/dd_post.py -u file:${PWD}/toto.1024.256.1.d.Part -p p
rm ./toto.1024.256.1.d.Part

echo

echo dd_post -u file:${PWD}/toto -p i,128

../sara/dd_post.py -u file:${PWD}/toto -p i,128

echo

echo dd_post -u file:${PWD}/toto -p i,64 -r

../sara/dd_post.py -u file:${PWD}/toto -p i,64 -r

echo

echo dd_post -u file:${PWD}/toto -p i,64 -rr

../sara/dd_post.py -u file:${PWD}/toto -p i,64 -rr

echo

echo dd_post -u file:${PWD}/toto -debug

../sara/dd_post.py -u file:${PWD}/toto -debug

echo

echo ======== ERROR PART =========================
echo

echo ERROR file not found
echo dd_post -u file:${PWD}/none_existing_file

../sara/dd_post.py -u file:${PWD}/none_existing_file

echo

echo ERROR file not found
echo dd_post -dr /fake/directory -u file:/none_existing_file

../sara/dd_post.py -dr /fake/directory -u file:/none_existing_file

echo


echo ERROR config file not found
echo dd_post -c ${PWD}/none_existing_file.conf

../sara/dd_post.py -c ${PWD}/none_existing_file.conf

echo


echo ERROR broker not found
echo dd_post -u file:${PWD}/toto -b amqp://mylocalhost/

../sara/dd_post.py -u file:${PWD}/toto -b amqp://mylocalhost/

echo

echo ERROR broker credential
echo dd_post -u file:${PWD}/toto -b amqp://toto:titi@localhost/

../sara/dd_post.py -u file:${PWD}/toto -b amqp://toto:titi@localhost/

echo

echo ERROR broker vhost
echo dd_post -u file:${PWD}/toto -b amqp://localhost/wrong_vhost

../sara/dd_post.py -u file:${PWD}/toto -b amqp://localhost/wrong_vhost

echo

echo ERROR wrong sumflg
echo dd_post -u file:${PWD}/toto -sum x

../sara/dd_post.py -u file:${PWD}/toto -sum x

echo

echo ERROR wrong exchange
echo ./exchange.py user_exchange del
echo dd_post -u file:${PWD}/toto -ex user_exchange

./exchange.py user_exchange del
../sara/dd_post.py -u file:${PWD}/toto -ex user_exchange

echo

echo ERROR wrong partfile 1
echo cp ./toto ./toto.12.256.1.d.Part
echo dd_post -u file:${PWD}/toto.12.256.1.d.Part -p p

cp ./toto ./toto.12.256.1.d.Part
../sara/dd_post.py -u file:${PWD}/toto.12.256.1.d.Part -p p
rm ./toto.12.256.1.d.Part

echo

echo ERROR wrong partfile 2
echo cp ./toto ./toto.1024.255.1.d.Part
echo dd_post -u file:${PWD}/toto.1024.255.1.d.Part -p p

cp ./toto ./toto.1024.255.1.d.Part
../sara/dd_post.py -u file:${PWD}/toto.1024.255.1.d.Part -p p
rm ./toto.1024.255.1.d.Part

echo

echo ERROR wrong partfile 3
echo cp ./toto ./toto.1024.256.5.d.Part
echo dd_post -u file:${PWD}/toto.1024.256.5.d.Part -p p

cp ./toto ./toto.1024.256.5.d.Part
../sara/dd_post.py -u file:${PWD}/toto.1024.256.5.d.Part -p p
rm ./toto.1024.256.5.d.Part

echo

echo ERROR wrong partfile 4
echo cp ./toto ./toto.1024.256.1.x.Part
echo dd_post -u file:${PWD}/toto.1024.256.1.x.Part -p p

cp ./toto ./toto.1024.256.1.x.Part
../sara/dd_post.py -u file:${PWD}/toto.1024.256.1.x.Part -p p
rm ./toto.1024.256.1.x.Part

echo

echo ERROR wrong partfile 5
echo cp ./toto ./toto.1024.256.1.d.bad
echo dd_post -u file:${PWD}/toto.1024.256.1.d.bad -p p

cp ./toto ./toto.1024.256.1.d.bad
../sara/dd_post.py -u file:${PWD}/toto.1024.256.1.d.bad -p p
rm ./toto.1024.256.1.d.bad

echo

echo ERROR wrong partflg
echo dd_post -u file:${PWD}/toto -p x,128

../sara/dd_post.py -u file:${PWD}/toto -p x,128

echo

echo ERROR wrong part chunksize
echo dd_post -u file:${PWD}/toto -p d,a

../sara/dd_post.py -u file:${PWD}/toto -p d,a

echo

rm ./toto
