#!/bin/ksh

rm ./toto* /tmp/verif 2> /dev/null

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

cat << EOF > sara_test1.conf

# source

source_broker amqp://localhost/
source_exchange amq.topic
source_topic v02.post.#

# destination

broker amqp://localhost/
exchange xpublic
document_root /

EOF

echo ==== DIRECT FILE : INPLACE T/F ====

function test1 {
      echo dd_sara $* start
      ../sara/dd_sara.py $* start 
      
      echo dd_post -u file:${PWD}/toto -rn ${PWD}/toto2
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/toto2 > /dev/null 2>&1
      
      sleep 1
      echo 
      echo check !?
      echo diff ./toto ./toto2
      diff ./toto ./toto2
      echo rm ./toto2
      rm ./toto2*
      
      ../sara/dd_sara.py $* stop
      echo dd_sara $* stop
}

test1 --strip 2 --url file:                ./sara_test1.conf
test1 --strip 2 --url file: --inplace True ./sara_test1.conf

echo ==== PARTS  FILE : INPLACE F   ====

function test2 {
      echo dd_sara $* start
      ../sara/dd_sara.py $* start 
      
      echo dd_post -u file:${PWD}/toto -rn ${PWD}/toto2 -p i,128
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/toto2 -p i,128 > /dev/null 2>&1

      sleep 2
      echo dd_post -u file:${PWD}/toto2.256.128.1.d.Part -rn ${PWD}/toto3 -p p
      echo dd_post -u file:${PWD}/toto2.256.128.0.d.Part -rn ${PWD}/toto3 -p p
      ../sara/dd_post.py -u file:${PWD}/toto2.256.128.1.d.Part -rn ${PWD}/toto3 -p p > /dev/null 2>&1
      ../sara/dd_post.py -u file:${PWD}/toto2.256.128.0.d.Part -rn ${PWD}/toto3 -p p > /dev/null 2>&1
      
      sleep 2
      echo 
      echo check !?
      echo diff ./toto2.256.128.0.d.Part ./toto3.256.128.0.d.Part
      echo diff ./toto2.256.128.1.d.Part ./toto3.256.128.1.d.Part
      diff ./toto2.256.128.0.d.Part ./toto3.256.128.0.d.Part
      diff ./toto2.256.128.1.d.Part ./toto3.256.128.1.d.Part
      
      ../sara/dd_sara.py $* stop
      echo dd_sara $* stop
}

test2 --strip 2 --url file:           ./sara_test1.conf

rm ./toto2*

echo ==== PARTS  FILE : INPLACE T   ====

function test3 {
      echo dd_sara $* start
      ../sara/dd_sara.py $* start 
      
      echo creation toto2
      echo dd_post -u file:${PWD}/toto -rn ${PWD}/toto2 -p i,128
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/toto2 -p i,128 > /dev/null 2>&1

      sleep 3
      echo diff ./toto ./toto2
      diff ./toto ./toto2
      
      echo repost i flag for toto2  NO DIFF
      echo dd_post -u file:${PWD}/toto -rn ${PWD}/toto2 -p i,128
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/toto2 -p i,128 > /dev/null 2>&1

      sleep 3
      echo diff ./toto ./toto2
      diff ./toto ./toto2

      echo repost d flag for toto2  NO DIFF
      echo dd_post -u file:${PWD}/toto2.256.128.1.d.Part -p p
      echo dd_post -u file:${PWD}/toto2.256.128.0.d.Part -p p
      cp ./toto3.256.128.1.d.Part ./toto2.256.128.1.d.Part
      ../sara/dd_post.py -u file:${PWD}/toto2.256.128.1.d.Part -p p > /dev/null 2>&1
      cp ./toto3.256.128.0.d.Part ./toto2.256.128.0.d.Part
      ../sara/dd_post.py -u file:${PWD}/toto2.256.128.0.d.Part -p p > /dev/null 2>&1
      
      echo 
      echo check !?
      echo diff ./toto ./toto2
      diff ./toto ./toto2
      
      echo repost i flag for toto2  WITH DIFF
      cat ./toto2 | sed 's/12345/abcde/' > ./toto2_mod
      mv ./toto2_mod ./toto2
      echo dd_post -u file:${PWD}/toto -rn ${PWD}/toto2 -p i,128
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/toto2 -p i,128 > /dev/null 2>&1

      sleep 3
      echo diff ./toto ./toto2
      diff ./toto ./toto2

      echo repost d flag for toto2  WITH DIFF
      cat ./toto2 | sed 's/12345/abcde/' > ./toto2_mod
      mv ./toto2_mod ./toto2
      echo dd_post -u file:${PWD}/toto2.256.128.1.d.Part -p p
      echo dd_post -u file:${PWD}/toto2.256.128.0.d.Part -p p
      cp ./toto3.256.128.1.d.Part ./toto2.256.128.1.d.Part
      ../sara/dd_post.py -u file:${PWD}/toto2.256.128.1.d.Part -p p > /dev/null 2>&1
      cp ./toto3.256.128.0.d.Part ./toto2.256.128.0.d.Part
      ../sara/dd_post.py -u file:${PWD}/toto2.256.128.0.d.Part -p p > /dev/null 2>&1

      echo repost d flag for toto2  WITH DIFF + truncated
      echo copie first, insert second, truncate
      cat ./toto2 | sed 's/12345/abcde/' > ./toto2_mod
      mv ./toto2_mod ./toto2
      echo aaaaaaaaa >> ./toto2
      echo dd_post -u file:${PWD}/toto2.256.128.0.d.Part -p p
      cp ./toto3.256.128.0.d.Part ./toto2.256.128.0.d.Part
      cp ./toto3.256.128.1.d.Part ./toto2.256.128.1.d.Part
      ../sara/dd_post.py -u file:${PWD}/toto2.256.128.0.d.Part -p p > /dev/null 2>&1
      
      echo 
      echo check !?
      echo diff ./toto ./toto2

      diff ./toto ./toto2
      
      ../sara/dd_sara.py $* stop
      echo dd_sara $* stop
}

test3 --strip 2 --url file: --inplace True ./sara_test1.conf

echo ==== Instances Part files : INPLACE T   ====


../sara/dd_sara.py --instances 100 --strip 2 --url file: --inplace True ./sara_test1.conf start

rm ./toto2*

echo dd_post -u file:${PWD}/toto -rn ${PWD}/toto2 -p i,1 -r
../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/toto2 -p i,1 -r > /dev/null 2>&1

sleep 10
echo diff ./toto ./toto2
diff ./toto ./toto2

../sara/dd_sara.py --instances 100 --strip 2 --url file: --inplace True ./sara_test1.conf stop

rm ./dd_sara_sara_test1_0*log
rm ./.dd_sara_sara_test1.state 
rm ./toto*
rm ./sara_test1.conf 

