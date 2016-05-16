#!/bin/ksh

SARRA_PATH=/usr/bin
SR_SUBSCRIBE=${SARRA_PATH}/sr_subscribe

mkdir /tmp/sr_sarra
cd /tmp/sr_sarra

echo killall ${SR_SUBSCRIBE##.*/}


killall ${SR_SUBSCRIBE##.*/} > /dev/null 2>&1
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

chmod 666 toto* /var/www/test/toto* /apps/px/test/toto*

cat << EOF > subscribe_test.conf

broker amqp://tsource@localhost/

exchange xs_tsource
topic_prefix v02.post
subtopic #

directory ${PWD}/test
accept .*

expire 300

EOF

mkdir ./test
rm ./.*.queue


# Define test functions
function test2 {

      echo -n "sr_post -dr /var/www -u http://localhost/test/toto -to alta ... "
      $SR_SUBSCRIBE $* start > ./sr_subscribe_test2.log 2>&1 &

      sleep 5

      #======== 1
      ${SARRA_PATH}/sr_post -dr /var/www -u http://localhost/test/toto -to alta > /dev/null 2>&1
      sleep 5
      touch ./test/test_no_4

      DIFF=`diff toto ./test/toto`
      if [[ $? != 0 ]]; then
         N=-1
      else
         N=`diff toto ./test/toto|wc -l`
      fi

      if ((N==0)) ; then
         echo OK
      else
         echo FAILED 
         exit 1
      fi
      rm   ./test/*

      #parts I

      #======== 2
      echo -n "sr_post -dr /var/www -u http://localhost/test/toto  -p i,128 -to alta ... "
      ${SARRA_PATH}/sr_post -dr /var/www -u http://localhost/test/toto -p i,128 -to alta > /dev/null 2>&1
      sleep 5
      touch ./test/test_no_5

      DIFF=`diff toto ./test/toto`
      if [[ $? != 0 ]]; then
         N=-1
      else
         N=`diff toto ./test/toto|wc -l`
      fi
      if ((N==0)) ; then
         echo OK 
      else
         echo FAILED
         exit 1
      fi
      rm   ./test/*

      #parts P

      #======== 2
      echo -n "sr_post -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -to alta ... "
      ${SARRA_PATH}/sr_post -dr /var/www -u http://localhost/test/toto.128.2.0.1.d.Part -p p -to alta > /dev/null 2>&1
      ${SARRA_PATH}/sr_post -dr /var/www -u http://localhost/test/toto.128.2.0.0.d.Part -p p -to alta > /dev/null 2>&1
      sleep 5
      touch ./test/test_no_6

      DIFF=`diff toto ./test/toto`
      if [[ $? != 0 ]]; then
         N=-1
      else
         N=`diff toto ./test/toto|wc -l`
      fi
      
      if ((N==0)) ; then
         echo OK
      else
         echo FAILED
         exit 1
      fi
      rm   ./test/*

      # killall ${SR_SUBSCRIBE##.*/}
      $SR_SUBSCRIBE $* stop >> ./sr_subscribe_test2.log 2>&1 &
}

function test4 {

         echo -n "http instances/inserts ... "
         $SR_SUBSCRIBE $* start > ./sr_subscribe_test4.log 2>&1 &
         sleep 10

         ${SARRA_PATH}/sr_post -dr /var/www -u http://localhost/test/toto -p i,1 -r -to alta > /dev/null 2>&1

         sleep 30
         touch ./test/test_no_8

         DIFF=`diff toto ./test/toto`
         if [[ $? != 0 ]]; then
            N=-1
         else
            N=`diff toto ./test/toto|wc -l`
         fi
         if ((N==0)) ; then
            echo OK
         else
            echo FAILED
            exit 1
         fi
         rm   ./test/*

         sleep 10
         # killall ${SR_SUBSCRIBE##.*/}
         $SR_SUBSCRIBE $* stop >> ./sr_subscribe_test4.log 2>&1 &
}


function test5 {
         echo "http inserts and truncated ... "
         $SR_SUBSCRIBE $* start > ./sr_subscribe_test5.log 2>&1 &
         sleep 10

         cat toto | sed 's/12345/abcde/' > ./test/toto
         echo abc >> ./test/toto

         ${SARRA_PATH}/sr_post -dr /var/www -u http://localhost/test/toto -p i,11 -r -to alta > /dev/null 2>&1

         sleep 30
         touch ./test/test_no_9

         DIFF=`diff toto ./test/toto`
         if [[ $? != 0 ]]; then
            N=-1
         else
            N=`diff toto ./test/toto|wc -l`
         fi
         
         if ((N==0)) ; then
            echo OK
         else
            echo FAILED
            exit 1
         fi
         rm   ./test/toto*


         sleep 10
         # killall ${SR_SUBSCRIBE##.*/}
         $SR_SUBSCRIBE $* stop >> ./sr_subscribe_test5.log 2>&1 &
}


# Run tests
echo 
echo "* Running INPLACE test suite:"
test2 ./subscribe_test.conf

echo
echo "* Running INSTANCES AND INSERTS test suite:"
test4 ./subscribe_test.conf

echo
echo "* Running INSTANCES AND INSERTS AND TRUNCATE test suite:"
test5 ./subscribe_test.conf

rm ./sr_subscribe_*.log ./.*ubscribe_* ./toto* ./test/t* ./subscribe_tes*.conf > /dev/null 2>&1
rmdir ./test > /dev/null 2>&1
rm -rf /tmp/sr_sarra
exit 0

