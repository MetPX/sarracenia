#!/bin/ksh

rm toto* 2> /dev/null
rm dd_sara_sara_test*.log 2> /dev/null
rm .dd_sara_sara_test*.log 2> /dev/null
rm sara_test*.conf

export USER=$1
export PASSWORD=$2

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

cp toto    toto2
cp toto    /var/www/test/toto
cp toto    /apps/px/test/toto

cp toto.p0 toto.128.2.0.0.d.Part
cp toto.p0 /var/www/test/toto.128.2.0.0.d.Part
cp toto.p0 /apps/px/test/toto.128.2.0.0.d.Part

cp toto.p0 toto2.128.2.0.0.d.Part
cp toto.p0 /var/www/test/toto2.128.2.0.0.d.Part
cp toto.p0 /apps/px/test/toto2.128.2.0.0.d.Part

cp toto.p1 toto.128.2.0.1.d.Part
cp toto.p1 /var/www/test/toto.128.2.0.1.d.Part
cp toto.p1 /apps/px/test/toto.128.2.0.1.d.Part

cp toto.p1 toto2.128.2.0.1.d.Part
cp toto.p1 /var/www/test/toto2.128.2.0.1.d.Part
cp toto.p1 /apps/px/test/toto2.128.2.0.1.d.Part

chmod 777 toto* /var/www/test/toto* /apps/px/test/toto*

cat << EOF > sara_test1.conf

# source

source_broker amqp://localhost/
source_exchange amq.topic
source_topic v02.post.#

sftp_user $USER
sftp_password $PASSWORD

# destination

broker amqp://localhost/
exchange xpublic
document_root /

EOF

cat sara_test1.conf

rm -r -f ./test >/dev/null 2>&1
mkdir ./test

echo ==== INPLACE FALSE ====

function test1 {

      ../sara/dd_sara.py $* start   > /dev/null 2>&1
      #======== 1
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2  > /dev/null 2>&1
      sleep 10
      N=`diff toto ./test/toto2|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2
      else
         echo ERROR ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2  
         exit 1
      fi
      rm   ./test/toto2*

      #======== 1
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 > /dev/null 2>&1
      sleep 10
      N=`diff toto ./test/toto2|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2
      else
         echo ERROR ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2
         exit 1
      fi
      rm   ./test/toto2*

      #======== 1
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 > /dev/null 2>&1
      sleep 10
      N=`diff toto ./test/toto2|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto2
      else
         echo ERROR ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto2
         exit 1
      fi
      rm   ./test/toto2*

      #parts I

      #======== 2
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1
      sleep 4
      N=`diff toto.128.2.0.1.d.Part ./test/toto2.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto2.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK  ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2 -p i,128
      else
         echo ERROR ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2 -p i,128
         exit 1
      fi
      rm   ./test/toto2*

      #======== 2
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1
      sleep 6
      N=`diff toto.128.2.0.1.d.Part ./test/toto2.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto2.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 -p i,128
      else
         echo ERROR ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 -p i,128
         exit 1
      fi
      rm   ./test/toto2*

      #======== 2
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1
      sleep 8
      N=`diff toto.128.2.0.1.d.Part ./test/toto2.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto2.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,128
      else
         echo ERROR ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,128
         exit 1
      fi
      rm   ./test/toto2*


      #parts P

      #======== 2
      ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      sleep 4
      N=`diff toto.128.2.0.1.d.Part ./test/toto2.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto2.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK  ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto2 -p p 
      else
         echo ERROR ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto2 -p p
         exit 1
      fi
      rm   ./test/toto2*

      #======== 2
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      sleep 6
      N=`diff toto.128.2.0.1.d.Part ./test/toto2.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto2.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto2 -p p
      else
         echo ERROR ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto2 -p p
         exit 1
      fi
      rm   ./test/toto2*

      #======== 2
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      sleep 8
      N=`diff toto.128.2.0.1.d.Part ./test/toto2.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto2.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto2 -p p
      else
         echo ERROR ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto2 -p p
         exit 1
      fi
      rm   ./test/toto2*

      
      ../sara/dd_sara.py $* stop > /dev/null 2>&1

}

test1 --strip 2 --url file:                ./sara_test1.conf


echo ==== INPLACE TRUE ====

function test2 {

      ../sara/dd_sara.py $* start > /dev/null 2>&1

      #======== 1
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2 > /dev/null 2>&1
      sleep 2
      N=`diff toto ./test/toto2|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2
      else
         echo ERROR ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2  
         exit 1
      fi
      rm   ./test/toto2*

      #======== 1
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 > /dev/null 2>&1
      sleep 3
      N=`diff toto ./test/toto2|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2
      else
         echo ERROR ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2
         exit 1
      fi
      rm   ./test/toto2*

      #======== 1
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 > /dev/null 2>&1
      sleep 4
      N=`diff toto ./test/toto2|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto2
      else
         echo ERROR ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto2
         exit 1
      fi
      rm   ./test/toto2*
      sleep 2

      #parts I

      #======== 2
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2 -p i,128  > /dev/null 2>&1
      sleep 4
      N=`diff toto ./test/toto2|wc -l`
      if ((N==0)) ; then
         echo OK  ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2 -p i,128
      else
         echo ERROR ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2 -p i,128
         exit 1
      fi
      rm   ./test/toto2*

      #======== 2
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1
      sleep 6
      N=`diff toto ./test/toto2|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 -p i,128
      else
         echo ERROR ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 -p i,128
         exit 1
      fi
      rm   ./test/toto2*

      #======== 2
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1
      sleep 8
      N=`diff toto ./test/toto2|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,128
      else
         echo ERROR ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,128
         exit 1
      fi
      rm   ./test/toto2*


      #parts P

      #======== 2
      ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      sleep 6
      N=`diff toto ./test/toto2|wc -l`
      if ((N==0)) ; then
         echo OK  ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto2 -p p 
      else
         echo ERROR ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto2 -p p
         exit 1
      fi
      rm   ./test/toto2*

      #======== 2
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      sleep 6
      N=`diff toto ./test/toto2|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto2 -p p
      else
         echo ERROR ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto2 -p p
         exit 1
      fi
      rm   ./test/toto2*

      #======== 2
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      sleep 8
      N=`diff toto ./test/toto2|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto2 -p p
      else
         echo ERROR ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto2 -p p
         exit 1
      fi
      rm   ./test/toto2*

      ../sara/dd_sara.py $* stop > /dev/null 2>&1

}

test2 --strip 2 --url file: --inplace True ./sara_test1.conf

echo ==== INPLACE FALSE NOT MODIFIED ====

function test3 {

      cp ./toto ./test/toto2
      cp ./toto.128.2.0.0.d.Part ./test/toto2.128.2.0.0.d.Part
      cp ./toto.128.2.0.1.d.Part ./test/toto2.128.2.0.1.d.Part

      ../sara/dd_sara.py $* start > /dev/null 2>&1
      #======== 1
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2  > /dev/null 2>&1

      #======== 1
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 > /dev/null 2>&1

      #======== 1
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 > /dev/null 2>&1

      #parts I

      #======== 2
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1

      #======== 2
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1

      #======== 2
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1


      #parts P

      #======== 2
      ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1

      #======== 2
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      #======== 2
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1

      
      sleep 10

      ../sara/dd_sara.py $* stop > /dev/null 2>&1

      N=`grep modified dd_sara_sara_test1_0001.log  | wc -l`
      if ((N==15)) ; then
         echo OK  not modified in all cases
      else
         echo ERROR should have 15 cases of unmodified files
         exit 1
      fi
      rm   ./test/toto2*
 

}

../sara/dd_sara.py $* stop > /dev/null 2>&1
test3 --strip 2 --url file:                ./sara_test1.conf

echo ==== INSTANCES AND INSERTS ====

function test4 {

         ../sara/dd_sara.py $* ./sara_test1.conf start > /dev/null 2>&1

         ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2 -p i,1  > /dev/null 2>&1
         ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2 -p i,1  > /dev/null 2>&1

               sleep 20
               ls -al toto ./test/toto2
               N=`diff toto ./test/toto2|wc -l`
               if ((N==0)) ; then
                  echo OK file:   INSTANCES/INSERTS
               else
                  echo ERROR file:   INSTANCES/INSERTS
                  exit 1
               fi
               rm   ./test/toto2*

         ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 -p i,1 > /dev/null 2>&1
         ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 -p i,1 > /dev/null 2>&1

               sleep 30
               ls -al toto ./test/toto2
               N=`diff toto ./test/toto2|wc -l`
               if ((N==0)) ; then
                  echo OK http:   INSTANCES/INSERTS
               else
                  echo ERROR http:   INSTANCES/INSERTS
                  exit 1
               fi
               rm   ./test/toto2*

         ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,1 > /dev/null 2>&1
         ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,1 > /dev/null 2>&1
         
               sleep 40
               ls -al toto ./test/toto2
               N=`diff toto ./test/toto2|wc -l`
               if ((N==0)) ; then
                  echo OK sftp:   INSTANCES/INSERTS
               else
                  echo ERROR sftp:   INSTANCES/INSERTS
                  exit 1
               fi
               rm   ./test/toto2*

         ../sara/dd_sara.py $* ./sara_test1.conf stop
         sleep 10

}

test4 --strip 2 --url file: --inplace true --instances 100


echo ==== INSTANCES AND INSERTS AND TRUNCATE ====

function test5 {

         ../sara/dd_sara.py $* ./sara_test1.conf start > /dev/null 2>&1

         cat toto | sed 's/12345/abcde/' > ./test/toto2
         echo abc >> ./test/toto2

         ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2 -p i,11 -r  > /dev/null 2>&1

               sleep 20
               ls -al toto ./test/toto2
               N=`diff toto ./test/toto2|wc -l`
               if ((N==0)) ; then
                  echo OK file:   INSERTS and TRUNCATED
               else
                  echo ERROR file:   INSERTS and TRUNCATED
                  exit 1
               fi
               rm   ./test/toto2*


         cat toto | sed 's/12345/abcde/' > ./test/toto2
         echo abc >> ./test/toto2

         ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 -p i,11 -r > /dev/null 2>&1

               sleep 30
               ls -al toto ./test/toto2
               N=`diff toto ./test/toto2|wc -l`
               if ((N==0)) ; then
                  echo OK http:   INSERTS and TRUNCATED
               else
                  echo ERROR http:   INSERTS and TRUNCATED
                  exit 1
               fi
               rm   ./test/toto2*


         cat toto | sed 's/12345/abcde/' > ./test/toto2
         echo abc >> ./test/toto2

         ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,11 -r > /dev/null 2>&1
         
               sleep 60
               ls -al toto ./test/toto2
               N=`diff toto ./test/toto2|wc -l`
               if ((N==0)) ; then
                  echo OK sftp:   INSERTS and TRUNCATED
               else
                  echo ERROR sftp:   INSERTS and TRUNCATED
                  exit 1
               fi
               rm   ./test/toto2*

         ../sara/dd_sara.py $* ./sara_test1.conf stop
         sleep 10

}

test5 --strip 2 --url file: --inplace true --instances 10

rm ./dd_sara_*.log ./.dd_sara_* ./toto* ./test/t* ./sara_test1.conf > /dev/null 2>&1
rmdir ./test > /dev/null 2>&1

