#!/bin/ksh

echo killall dd_sara.py

killall dd_sara.py > /dev/null 2>&1
rm ./dd_sara_*.log ./.dd_sara_* ./toto* ./test/t* ./sara_test1.conf > /dev/null 2>&1
rmdir ./test > /dev/null 2>&1

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

cat << EOF > sara_test1.conf

# source

source_broker amqp://localhost/
source_exchange amq.topic
source_topic v02.post.#

sftp_user $USER
sftp_password $PASSWORD

ftp_user $USER
ftp_password $PASSWORD

# destination

broker amqp://localhost/
exchange xpublic
document_root /

EOF

mkdir ./test

echo ==== INPLACE FALSE ====

function test1 {

      ../sara/dd_sara.py $* start   > /dev/null 2>&1
      #======== 1
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_02  > /dev/null 2>&1
      sleep 10
      ls -al toto ./test/*
      N=`diff toto ./test/toto_02|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_02
      else
         echo ERROR ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_02  
         exit 1
      fi
      rm   ./test/toto_02*

      #======== 1
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_03 > /dev/null 2>&1
      sleep 10
      ls -al toto ./test/*
      N=`diff toto ./test/toto_03|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_03
      else
         echo ERROR ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_03
         exit 1
      fi
      rm   ./test/toto_03*

      #======== 1
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_04 > /dev/null 2>&1
      sleep 10
      ls -al toto ./test/*
      N=`diff toto ./test/toto_04|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_04
      else
         echo ERROR ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_04
         exit 1
      fi
      rm   ./test/toto_04*

      #======== 1

      ../sara/dd_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_05 > /dev/null 2>&1
      sleep 10
      ls -al toto ./test/*
      N=`diff toto ./test/toto_05|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_05
      else
         echo ERROR ../sara/dd_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_05
         exit 1
      fi
      rm   ./test/toto_05*

      #parts I

      #======== 2
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_06 -p i,128 > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_06.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_06.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK  ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_06 -p i,128
      else
         echo ERROR ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_06 -p i,128
         exit 1
      fi
      rm   ./test/toto_06*

      #======== 2
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_07 -p i,128 > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_07.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_07.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_07 -p i,128
      else
         echo ERROR ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_07 -p i,128
         exit 1
      fi
      rm   ./test/toto_07*

      #======== 2
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_08 -p i,128 > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_08.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_08.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_08 -p i,128
      else
         echo ERROR ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_08 -p i,128
         exit 1
      fi
      rm   ./test/toto_08*

      #======== 2
      ../sara/dd_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_09 -p i,128 > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_09.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_09.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/dd_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_09 -p i,128
      else
         echo ERROR ../sara/dd_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_09 -p i,128
         exit 1
      fi
      rm   ./test/toto_09*


      #parts P

      #======== 2
      ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_10 -p p > /dev/null 2>&1
      ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_10 -p p > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_10.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_10.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK  ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_10 -p p 
      else
         echo ERROR ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_10 -p p
         exit 1
      fi
      rm   ./test/toto_10*

      #======== 2
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_11 -p p > /dev/null 2>&1
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_11 -p p > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_11.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_11.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_11 -p p
      else
         echo ERROR ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_11 -p p
         exit 1
      fi
      rm   ./test/toto_11*

      #======== 2
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_12 -p p > /dev/null 2>&1
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_12 -p p > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_12.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_12.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_12 -p p
      else
         echo ERROR ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_12 -p p
         exit 1
      fi
      rm   ./test/toto_12*

      #======== 2
      ../sara/dd_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_13 -p p > /dev/null 2>&1
      ../sara/dd_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_13 -p p > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_13.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_13.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/dd_post.py -u ftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_13 -p p
      else
         echo ERROR ../sara/dd_post.py -u ftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_13 -p p
         exit 1
      fi
      rm   ./test/toto_13*

      
      ../sara/dd_sara.py $* stop > /dev/null 2>&1


}

python3 ./exchange.py xpublic add > /dev/null 2>&1

test1 --strip 2 --url file:                ./sara_test1.conf

mv dd_sara_sara_test1_0001.log dd_sara_sara_test1_0001.log_INPLACE_FALSE

echo ==== INPLACE TRUE ====

function test2 {

      ../sara/dd_sara.py $* start > /dev/null 2>&1

      #======== 1
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_14 > /dev/null 2>&1
      sleep 2
      ls -al toto ./test/*
      N=`diff toto ./test/toto_14|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_14
      else
         echo ERROR ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_14  
         exit 1
      fi
      rm   ./test/toto_14*

      #======== 1
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_15 > /dev/null 2>&1
      sleep 3
      ls -al toto ./test/*
      N=`diff toto ./test/toto_15|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_15
      else
         echo ERROR ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_15
         exit 1
      fi
      rm   ./test/toto_15*

      #======== 1
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_16 > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto ./test/toto_16|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_16
      else
         echo ERROR ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_16
         exit 1
      fi
      rm   ./test/toto_16*
      sleep 2

      #======== 1
      ../sara/dd_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_17 > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto ./test/toto_17|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_17
      else
         echo ERROR ../sara/dd_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_17
         exit 1
      fi
      rm   ./test/toto_17*
      sleep 2

      #parts I

      #======== 2
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_18 -p i,128  > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto ./test/toto_18|wc -l`
      if ((N==0)) ; then
         echo OK  ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_18 -p i,128
      else
         echo ERROR ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_18 -p i,128
         exit 1
      fi
      rm   ./test/toto_18*

      #======== 2
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_19 -p i,128 > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto ./test/toto_19|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_19 -p i,128
      else
         echo ERROR ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_19 -p i,128
         exit 1
      fi
      rm   ./test/toto_19*

      #======== 2
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_20 -p i,128 > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto ./test/toto_20|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_20 -p i,128
      else
         echo ERROR ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_20 -p i,128
         exit 1
      fi
      rm   ./test/toto_20*


      #======== 2
      ../sara/dd_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_21 -p i,128 > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto ./test/toto_21|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_21 -p i,128
      else
         echo ERROR ../sara/dd_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_21 -p i,128
         exit 1
      fi
      rm   ./test/toto_21*


      #parts P

      #======== 2
      ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_22 -p p > /dev/null 2>&1
      ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_22 -p p > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto ./test/toto_22|wc -l`
      if ((N==0)) ; then
         echo OK  ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_22 -p p 
      else
         echo ERROR ../sara/dd_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_22 -p p
         exit 1
      fi
      rm   ./test/toto_22*

      #======== 2
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_23 -p p > /dev/null 2>&1
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_23 -p p > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto ./test/toto_23|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_23 -p p
      else
         echo ERROR ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_23 -p p
         exit 1
      fi
      rm   ./test/toto_23*

      #======== 2
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_24 -p p > /dev/null 2>&1
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_24 -p p > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto ./test/toto_24|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_24 -p p
      else
         echo ERROR ../sara/dd_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_24 -p p
         exit 1
      fi
      rm   ./test/toto_24*

      #======== 2
      ../sara/dd_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_25 -p p > /dev/null 2>&1
      ../sara/dd_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_25 -p p > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto ./test/toto_25|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/dd_post.py -u ftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_25 -p p
      else
         echo ERROR ../sara/dd_post.py -u ftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_25 -p p
         exit 1
      fi
      rm   ./test/toto_25*

      ../sara/dd_sara.py $* stop > /dev/null 2>&1

}

test2 --strip 2 --url file: --inplace True ./sara_test1.conf
mv dd_sara_sara_test1_0001.log dd_sara_sara_test1_0001.log_INPLACE_TRUE

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

      #======== 1
      ../sara/dd_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 > /dev/null 2>&1

      #parts I

      #======== 2
      ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1

      #======== 2
      ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1

      #======== 2
      ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1

      #======== 2
      ../sara/dd_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1


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
      #======== 2
      ../sara/dd_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      ../sara/dd_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1

      
      sleep 10
      ls -al toto ./test/*

      ../sara/dd_sara.py $* stop > /dev/null 2>&1

      N=`grep modified dd_sara_sara_test1_0001.log  | wc -l`
      if ((N==20)) ; then
         echo OK  not modified in all cases
      else
         echo ERROR should have 20 cases of unmodified files
         exit 1
      fi
      rm   ./test/toto2*
 
      ../sara/dd_sara.py $* stop > /dev/null 2>&1

}

test3 --strip 2 --url file:                ./sara_test1.conf
mv dd_sara_sara_test1_0001.log dd_sara_sara_test1_0001.log_INPLACE_FALSE_NOT_MODIFIED

echo ==== INSTANCES AND INSERTS ====

function test4 {

         ../sara/dd_sara.py $* ./sara_test1.conf start > /dev/null 2>&1

         ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_26 -p i,1 -r  > /dev/null 2>&1

               sleep 20
               ls -al toto ./test/*
               N=`diff toto ./test/toto_26|wc -l`
               if ((N==0)) ; then
                  echo OK file:   INSTANCES/INSERTS
               else
                  echo ERROR file:   INSTANCES/INSERTS
                  exit 1
               fi
               rm   ./test/toto_26*

         ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_27 -p i,1 -r > /dev/null 2>&1

               sleep 30
               ls -al toto ./test/*
               N=`diff toto ./test/toto_27|wc -l`
               if ((N==0)) ; then
                  echo OK http:   INSTANCES/INSERTS
               else
                  echo ERROR http:   INSTANCES/INSERTS
                  exit 1
               fi
               rm   ./test/toto_27*

         ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_28 -p i,1 -r > /dev/null 2>&1
         
               sleep 40
               ls -al toto ./test/*
               N=`diff toto ./test/toto_28|wc -l`
               if ((N==0)) ; then
                  echo OK sftp:   INSTANCES/INSERTS
               else
                  echo ERROR sftp:   INSTANCES/INSERTS
                  exit 1
               fi
               rm   ./test/toto_28*

         ../sara/dd_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_29 -p i,1 -r > /dev/null 2>&1
         
               sleep 40
               ls -al toto ./test/*
               N=`diff toto ./test/toto_29|wc -l`
               if ((N==0)) ; then
                  echo OK ftp:   INSTANCES/INSERTS
               else
                  echo ERROR ftp:   INSTANCES/INSERTS
                  exit 1
               fi
               rm   ./test/toto_29*

         ../sara/dd_sara.py $* ./sara_test1.conf stop
         sleep 10

}

test4 --strip 2 --url file: --inplace true --instances 100

cat dd_sara_sara_test1_*.log >> dd_sara_sara_test1_0001.log_INSTANCES_INSERT
rm dd_sara_sara_test1_*.log


echo ==== INSTANCES AND INSERTS AND TRUNCATE ====

function test5 {

         ../sara/dd_sara.py $* ./sara_test1.conf start > /dev/null 2>&1

         cat toto | sed 's/12345/abcde/' > ./test/toto_30
         echo abc >> ./test/toto_30

         ../sara/dd_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_30 -p i,11 -r  > /dev/null 2>&1

               sleep 20
               ls -al toto ./test/*
               N=`diff toto ./test/toto_30|wc -l`
               if ((N==0)) ; then
                  echo OK file:   INSERTS and TRUNCATED
               else
                  echo ERROR file:   INSERTS and TRUNCATED
                  exit 1
               fi
               rm   ./test/toto_30*


         cat toto | sed 's/12345/abcde/' > ./test/toto_31
         echo abc >> ./test/toto_31

         ../sara/dd_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_31 -p i,11 -r > /dev/null 2>&1

               sleep 30
               ls -al toto ./test/*
               N=`diff toto ./test/toto_31|wc -l`
               if ((N==0)) ; then
                  echo OK http:   INSERTS and TRUNCATED
               else
                  echo ERROR http:   INSERTS and TRUNCATED
                  exit 1
               fi
               rm   ./test/toto_31*


         cat toto | sed 's/12345/abcde/' > ./test/toto_32
         echo abc >> ./test/toto_32

         ../sara/dd_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_32 -p i,11 -r > /dev/null 2>&1
         
               sleep 60
               ls -al toto ./test/*
               N=`diff toto ./test/toto_32|wc -l`
               if ((N==0)) ; then
                  echo OK sftp:   INSERTS and TRUNCATED
               else
                  echo ERROR sftp:   INSERTS and TRUNCATED
                  exit 1
               fi
               rm   ./test/toto_32*

         cat toto | sed 's/12345/abcde/' > ./test/toto_33
         echo abc >> ./test/toto_33

         ../sara/dd_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_33 -p i,11 -r > /dev/null 2>&1
         
               sleep 60
               ls -al toto ./test/*
               N=`diff toto ./test/toto_33|wc -l`
               if ((N==0)) ; then
                  echo OK sftp:   INSERTS and TRUNCATED
               else
                  echo ERROR sftp:   INSERTS and TRUNCATED
                  exit 1
               fi
               rm   ./test/toto_33*

         sleep 10
         ../sara/dd_sara.py $* ./sara_test1.conf stop

}

test5 --strip 2 --url file: --inplace true --instances 10

python3 ./exchange.py xpublic del > /dev/null 2>&1

cat dd_sara_sara_test1_*.log >> dd_sara_sara_test1_0001.log_INSTANCES_INSERT_TRUNCATE
rm dd_sara_sara_test1_*.log

#rm ./dd_sara_*.log ./.dd_sara_* ./toto* ./test/t* ./sara_test1.conf > /dev/null 2>&1
#rmdir ./test > /dev/null 2>&1

