#!/bin/bash

# This test suppose rabbitmq server installed on localhost

# some setting required  

# amqp://guest:guest@localhost/
# all permissions for guest on localhost broker
# exchange   xs_guest  created

# amqp://tsource@localhost/
# all permissions for tsource on localhost broker
# exchange   xs_tsource  created

# run from metpx-git/sarracenia/test
# invoking  ../sarra/sr_post.py for testing purpose

# the end of the script finishes with a
# desired error section

DR="`cat .httpdocroot`"

if [ ! "${DR}" ]; then
  echo "must run setup.sh first"
  exit 1
else
  echo "Document root is: ${DR}"
fi

export PYTHONPATH=../sarra

cat << EOF > ${DR}/toto
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

# this test does not work, but all it is supposed to do is show the usage...
# FIXME.
#echo sr_post --help
#
#../sarra/sr_post.py --help >srp.output 2>&1
#echo


tnum=1
printf "test ${tnum}: start "
echo default broker + default exchange
echo sr_post -u file:${DR}/toto -to alta

../sarra/sr_post.py -u file: -to alta -path ${DR}/toto
st=$?
if [ $st -eq 0 ]; then
  echo "test ${tnum}: OK"
else   
  echo "test ${tnum}: FAIL"
fi

echo

# checking caching

let tnum++
printf "test ${tnum}: start"
echo "start ( -blocksize ) -caching -reset "
../sarra/sr_post.py -blocksize 1000Mb --caching -u file: -to alta -path ${DR}/toto

st=$?
if [ $st -eq 0 ]; then
  echo "test ${tnum}: OK"
else   
  echo "test ${tnum}: FAIL"
fi

let tnum++
printf "test ${tnum}: start "
echo "start -blocksize ( -caching ) -reset "

../sarra/sr_post.py -blocksize 1000Mb --caching -u file: -to alta -path ${DR}/toto

st=$?
if [ $st -eq 0 ]; then
  echo "test ${tnum}: OK"
else   
  echo "test ${tnum}: FAIL"
fi

let tnum++
printf "test ${tnum}: start "
echo "start -blocksize -caching ( -reset ) "



../sarra/sr_post.py -reset -blocksize 1000Mb --caching -u file: -to alta -path ${DR}/toto


st=$?
if [ $st -eq 0 ]; then
  echo "test ${tnum}: OK"
else   
  echo "test ${tnum}: FAIL"
fi

let tnum++
echo "test ${tnum}: \c"


echo

echo default broker + exchange amq.topic
echo sr_post -u file: -ex amq.topic -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -ex amq.topic -to alta -path ${DR}/toto
echo


echo default guest user and vhost /
echo sr_post -u file: -b amqp://localhost -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -b amqp://localhost -to alta -path ${DR}/toto

echo


echo new broker user
echo sr_post -u file: -b amqp://tsource@localhost -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -b amqp://tsource@localhost -to alta -path ${DR}/toto

echo


cat << EOF >sr_post.conf
url file:
EOF

echo cat sr_post.conf
cat sr_post.conf
echo
echo sr_post -c ${DR}/sr_post.conf -b amqp://tsource@localhost -path ${DR}/toto

../sarra/sr_post.py -c ${DR}/sr_post.conf -b amqp://tsource@localhost -to alta -path ${DR}/toto

rm sr_post.conf
echo


mkdir -p ~/.config/sarra 2> /dev/null

echo sr_post using ~/.config/sarra/credentials.conf 
echo sr_post -u file: -b amqp://localhost -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -b amqp://localhost -to alta -path ${DR}/toto

echo


echo sr_post -u file: -l ${DR}/toto.log -b amqp://localhost -to alta -path ${DR}/toto
echo cat ${DR}/toto.log

../sarra/sr_post.py -u file: -l ${DR}/toto.log -b amqp://localhost -to alta -path ${DR}/toto
cat ${DR}/toto.log
rm  ${DR}/toto.log
echo

echo sr_post -u file: -b amqp://localhost/ -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -b amqp://localhost/ -to alta -path ${DR}/toto

echo

echo sr_post -dr ${DR} -u file: -b amqp://localhost/ -to alta -path ${DR}/toto

../sarra/sr_post.py -dr ${DR} -u file: -b amqp://localhost/ -to alta -path ${DR}/toto

echo

echo sr_post -u file: -f my_flow -b amqp://localhost/ -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -f my_flow -b amqp://localhost/ -to alta -path ${DR}/toto


echo

echo sr_post -u file: -tp v05.test -b amqp://localhost/ -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -tp v05.test -b amqp://localhost/ -to alta -path ${DR}/toto


echo

echo sr_post -u file: -sub imposed.sub.topic -b amqp://localhost/ -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -sub imposed.sub.topic -b amqp://localhost/ -to alta -path ${DR}/toto

echo


# strip rename
echo  -strip -rename

echo sr_post -u file: -rn /this/new/name -b amqp://localhost/ -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -rn /this/new/name -b amqp://localhost/ -to alta -path ${DR}/toto

echo sr_post -u file: -strip 3 -b amqp://localhost/ -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -strip 3 -b amqp://localhost/ -to alta -path ${DR}/toto


echo

echo sr_post -u file: -rn /this/new/dir/ -b amqp://localhost/ -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -rn "/this/new/dir/" -b amqp://localhost/ -to alta -path ${DR}/toto

echo

echo sr_post -u file: -sum 0 -b amqp://localhost/ -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -sum 0 -b amqp://localhost/ -to alta -path ${DR}/toto

echo

echo sr_post -u file: -sum n -b amqp://localhost/ -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -sum n -b amqp://localhost/ -to alta -path ${DR}/toto


echo

echo sr_post -u file: -sum z,d -b amqp://localhost/ -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -sum z,d -b amqp://localhost/ -to alta -path ${DR}/toto


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

echo sr_post -u file: -sum ${DR}/checksum_AHAH.py -b amqp://localhost/ -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -sum ${DR}/checksum_AHAH.py -b amqp://localhost/ -to alta -path ${DR}/toto


#rm ${DR}/checksum_AHAH.py
echo

./rabbitmqadmin -u guest -p guest declare exchange \
     name=user_exchange type=topic auto_delete=false durable=true

echo user_exchange 
echo sr_post -u file: -ex user_exchange -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -ex user_exchange -to alta -path ${DR}/toto

echo

cp ${DR}/toto ${DR}/toto.256.12.0.1.d.Part
echo sr_post -u file: -parts p -to alta -path ${DR}/toto.256.12.0.1.d.Part

../sarra/sr_post.py -u file: -parts p -to alta -path ${DR}/toto.256.12.0.1.d.Part


echo sr_post -u file:  -rn /this/new/name -parts p -to alta -path ${DR}/toto.256.12.0.1.d.Part

../sarra/sr_post.py -u file: -rn /this/new/name -parts p -to alta -path ${DR}/toto.256.12.0.1.d.Part


echo sr_post -u file:  -rn /this/new/dir/ -parts p -to alta -path ${DR}/toto.256.12.0.1.d.Part

../sarra/sr_post.py -u file: -rn /this/new/dir/ -parts p -to alta -path ${DR}/toto.256.12.0.1.d.Part


rm ${DR}/toto.256.12.0.1.d.Part

echo

echo sr_post -u file: -parts i,128 -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -parts i,128 -to alta -path ${DR}/toto

echo

echo sr_post -u file: -parts i,64 -r -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -parts i,64 -r -to alta -path ${DR}/toto

echo

echo sr_post -u file: -parts i,64 -rr -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -parts i,64 -rr -to alta -path ${DR}/toto

echo

echo sr_post -u file: -to cluster1,cluster2,cluster3 -path ${DR}/toto

../sarra/sr_post.py -u file: -to cluster1,cluster2,cluster3 -path ${DR}/toto

echo

echo sr_post -u file: -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -to alta -path ${DR}/toto

echo

echo ======== ERROR PART =========================
echo

echo result should be: ERROR no -to arguments
echo sr_post -u file:  -path ${DR}/toto

../sarra/sr_post.py -u file: -path ${DR}/toto


echo result should be: ERROR file not found
echo sr_post -u file: -to alta -path ${DR}/none_existing_file

../sarra/sr_post.py -u file: -to alta -path ${DR}/none_existing_file

echo

echo result should be: ERROR file not found
echo sr_post -dr /fake/directory -u file: -to alta -path ${DR}/none_existing_file

../sarra/sr_post.py -dr /fake/directory -u file: -to alta -path ${DR}/none_existing_file

echo


echo result should be: ERROR config file not found
echo sr_post -c ${DR}/none_existing_file.conf -to alta -path ${DR}/toto

../sarra/sr_post.py -c ${DR}/none_existing_file.conf -to alta -path ${DR}/toto

echo


echo result should be: ERROR broker not found
echo sr_post -u file: -b amqp://mylocalhost/ -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -b amqp://mylocalhost/ -to alta -path ${DR}/toto

echo

echo result should be: ERROR broker credential
echo sr_post -u file: -b amqp:${DR}/toto:titi@localhost/ -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -b amqp:${DR}/toto:titi@localhost/ -to alta -path ${DR}/toto

echo

echo result should be: ERROR broker vhost
echo sr_post -u file: -b amqp://localhost/wrong_vhost -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -b amqp://localhost/wrong_vhost -to alta -path ${DR}/toto

echo

echo result should be: ERROR wrong sumflg
echo sr_post -u file: -sum x -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -sum x -to alta -path ${DR}/toto

echo

echo result should be: ERROR wrong exchange
echo rabbitmqadmin delete exchange name=user_exchange
echo sr_post -u file:${DR}/toto -ex user_exchange -to alta -path ${DR}/toto

./rabbitmqadmin -u guest -p guest delete exchange name=user_exchange -path ${DR}/toto
../sarra/sr_post.py -u file: -ex user_exchange -to alta -path ${DR}/toto

echo

echo result should be: ERROR wrong partfile 1
echo cp ${DR}/toto ${DR}/toto.12.256.1.d.Part
echo sr_post -u file: -parts p -to alta -path ${DR}/toto.12.256.1.d.Part 

cp ${DR}/toto ${DR}/toto.12.256.1.d.Part
../sarra/sr_post.py -u file: -parts p -to alta -path ${DR}/toto.12.256.1.d.Part
rm ${DR}/toto.12.256.1.d.Part

echo

echo result should be: ERROR wrong partfile 2
echo cp ${DR}/toto ${DR}/toto.1024.255.1.d.Part
echo sr_post -u file: -parts p -to alta -path ${DR}/toto.1024.255.1.d.Part

cp ${DR}/toto ${DR}/toto.1024.255.1.d.Part
../sarra/sr_post.py -u file:${DR} -parts p -to alta -path ${DR}/toto.1024.255.1.d.Part
rm ${DR}/toto.1024.255.1.d.Part

echo

echo result should be: ERROR wrong partfile 3
echo cp ${DR}/toto ${DR}/toto.1024.256.5.d.Part
echo sr_post -u file: -parts p -to alta -path ${DR}/toto.1024.256.5.d.Part

cp ${DR}/toto ${DR}/toto.1024.256.5.d.Part
../sarra/sr_post.py -u file: -parts p -to alta -path ${DR}/toto.1024.256.5.d.Part
rm ${DR}/toto.1024.256.5.d.Part

echo

echo result should be: ERROR wrong partfile 4
echo cp ${DR}/toto ${DR}/toto.1024.256.1.x.Part
echo sr_post -u file: -parts p -to alta -path ${DR}/toto.1024.256.1.x.Part

cp ${DR}/toto ${DR}/toto.1024.256.1.x.Part
../sarra/sr_post.py -u file: -parts p -to alta -path ${DR}/toto.1024.256.1.x.Part
rm ${DR}/toto.1024.256.1.x.Part

echo

echo result should be: ERROR wrong partfile 5
echo cp ${DR}/toto ${DR}/toto.1024.256.1.d.bad
echo sr_post -u file: -parts p -to alta -path ${DR}/toto.1024.256.1.d.bad

cp ${DR}/toto ${DR}/toto.1024.256.1.d.bad
../sarra/sr_post.py -u file: -parts p -to alta -path ${DR}/toto.1024.256.1.d.bad
rm ${DR}/toto.1024.256.1.d.bad

echo

echo result should be: ERROR wrong partflg
echo sr_post -u file: -parts x,128 -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -parts x,128 -to alta -path ${DR}/toto

echo

echo result should be: ERROR wrong part chunksize
echo sr_post -u file: -parts d,a -to alta -path ${DR}/toto

../sarra/sr_post.py -u file: -parts d,a -to alta -path ${DR}/toto

echo

rm ${DR}/toto
