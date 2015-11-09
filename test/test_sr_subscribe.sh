#!/bin/ksh

DD_SUBSCRIBE=../sara/sr_subscribe.py
#DD_SUBSCRIBE=../sara/dd_subscribe

echo killall ${DD_SUBSCRIBE##.*/}


killall ${DD_SUBSCRIBE##.*/} > /dev/null 2>&1
rm ./sr_susbscribe*.log ./toto* ./test/t* ./subscribe_test1.conf > /dev/null 2>&1
rmdir ./test > /dev/null 2>&1

cat << EOF > toto
0 123456789abcde
1 123456789abcde
2 123456789abcde
3 123456789abcde
4 123456789abcde
5 123456789abcde
6 123456789abcde
7 123456
89abcde
8 123456789abcde
9 123456789abcde
a 123456789abcde
b 123456789abcde
c 123456789abcde
d 123456789abcde
e 123456789abcde

EOF
cat << EOF > toto.p0
0 123456789abcde
1 123456789abcde
2 123456789abcde
3 123456789abcde
4 123456789abcde
5 123456789abcde
6 123456789abcde
7 123456
EOF
cat << EOF > toto.p1
89abcde
8 123456789abcde
9 123456789abcde
a 123456789abcde
b 123456789abcde
c 123456789abcde
d 123456789abcde
e 123456789abcde

EOF

# published files

cp toto    /var/www/test/toto
cp toto    /apps/px/test/toto

cp toto.p0 toto.128.2.0.0.d.Part
cp toto.p0 /var/www/test/toto.128.2.0.0.d.Part
cp toto.p0 /apps/px/test/toto.128.2.0.0.d.Part

cp toto.p1 toto.128.2.0.1.d.Part
cp toto.p1 /var/www/test/toto.128.2.0.1.d.Part
cp toto.p1 /apps/px/test/toto.128.2.0.1.d.Part

chmod 777 toto* /var/www/test/toto* /apps/px/test/toto*

cat << EOF > subscribe_test.conf

broker amqp://localhost/
amqp-user guest
amqp-password guest

exchange xs_guest
topic_prefix v02.post
subtopic #

directory ${PWD}/test
accept .*

expire 300

EOF

mkdir ./test
rm ./.*.queue

echo ==== INPLACE ====

function test2 {

      $DD_SUBSCRIBE $* > ./sr_subscribe_test2.log 2>&1 &

      sleep 5

      #======== 1
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -to alta > /dev/null 2>&1
      sleep 5
      touch ./test/test_no_4
      ls -al toto ./test/*
      N=`diff toto ./test/toto|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -to alta
      else
         echo ERROR ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -to alta
         exit 1
      fi
      rm   ./test/*

      #parts I

      #======== 2
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -p i,128 -to alta > /dev/null 2>&1
      sleep 5
      touch ./test/test_no_5
      ls -al toto ./test/*
      N=`diff toto ./test/toto|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto  -p i,128 -to alta
      else
         echo ERROR ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto  -p i,128 -to alta
         exit 1
      fi
      rm   ./test/*



      #parts P

      #======== 2
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.1.d.Part -p p -to alta > /dev/null 2>&1
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.0.d.Part -p p -to alta > /dev/null 2>&1
      sleep 5
      touch ./test/test_no_6
      ls -al toto ./test/*
      N=`diff toto ./test/toto|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -to alta
      else
         echo ERROR ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -to alta
         exit 1
      fi
      rm   ./test/*

      killall ${DD_SUBSCRIBE##.*/}

}


test2 ./subscribe_test.conf

echo ==== INSTANCES AND INSERTS ====

function test4 {

          $DD_SUBSCRIBE $* > ./sr_subscribe_test4.log 2>&1 &
          sleep 10

         ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -p i,1 -r -to alta > /dev/null 2>&1

               sleep 30
               touch ./test/test_no_8
               ls -al toto ./test/*
               N=`diff toto ./test/toto|wc -l`
               if ((N==0)) ; then
                  echo OK http:   INSTANCES/INSERTS
               else
                  echo ERROR http:   INSTANCES/INSERTS
                  exit 1
               fi
               rm   ./test/*

         sleep 10
         killall ${DD_SUBSCRIBE##.*/}

}


test4 ./subscribe_test.conf


echo ==== INSTANCES AND INSERTS AND TRUNCATE ====

function test5 {


          $DD_SUBSCRIBE $* > ./sr_subscribe_test5.log 2>&1 &
          sleep 10


         cat toto | sed 's/12345/abcde/' > ./test/toto
         echo abc >> ./test/toto

         ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -p i,11 -r -to alta > /dev/null 2>&1

               sleep 30
               touch ./test/test_no_9
               ls -al toto ./test/*
               N=`diff toto ./test/toto|wc -l`
               if ((N==0)) ; then
                  echo OK http:   INSERTS and TRUNCATED
               else
                  echo ERROR http:   INSERTS and TRUNCATED
                  exit 1
               fi
               rm   ./test/toto*


         sleep 10
         killall ${DD_SUBSCRIBE##.*/}


}

test5 ./subscribe_test.conf

rm ./sr_subscribe_*.log ./.*ubscribe_* ./toto* ./test/t* ./subscribe_tes*.conf > /dev/null 2>&1
rmdir ./test > /dev/null 2>&1

