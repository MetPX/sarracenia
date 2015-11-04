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

./rabbitmqadmin -u guest -p guest declare exchange \
     name=xpublic type=topic auto_delete=false durable=true

echo $#

if [[ $# != 2 ]]; then
   echo $0 user password
   exit 1
fi

echo killall sr_sara.py

killall sr_sara.py > /dev/null 2>&1
rm ./sr_sara_*.log ./.sr_sara_* ./toto* ./test/t* ./sara_test1.conf > /dev/null 2>&1
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

source_broker amqp://guest@localhost/
source_exchange xs_guest
source_topic v02.post.#

sftp_user $USER
sftp_password $PASSWORD

ftp_user $USER
ftp_password $PASSWORD

queue_name q_guest.sr_sara.test

source_from_exchange True
from_cluster localhost

# destination

broker amqp://guest@localhost/
exchange xpublic
document_root /

EOF

mkdir ./test

echo ==== INPLACE FALSE ====

function test1 {

      ../sara/sr_sara.py $* start   > /dev/null 2>&1
      #======== 1
      ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_02 -tc cluster1,cluster2,cluster3  > /dev/null 2>&1
      sleep 10
      ls -al toto ./test/*
      N=`diff toto ./test/toto_02|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_02
      else
         echo ERROR ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_02  
         exit 1
      fi
      rm   ./test/toto_02*

      #======== 1
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_03 > /dev/null 2>&1
      sleep 10
      ls -al toto ./test/*
      N=`diff toto ./test/toto_03|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_03
      else
         echo ERROR ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_03
         exit 1
      fi
      rm   ./test/toto_03*

      #======== 1
      ../sara/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_04 > /dev/null 2>&1
      sleep 10
      ls -al toto ./test/*
      N=`diff toto ./test/toto_04|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_04
      else
         echo ERROR ../sara/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_04
         exit 1
      fi
      rm   ./test/toto_04*

      #======== 1

      ../sara/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_05 > /dev/null 2>&1
      sleep 10
      ls -al toto ./test/*
      N=`diff toto ./test/toto_05|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_05
      else
         echo ERROR ../sara/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_05
         exit 1
      fi
      rm   ./test/toto_05*

      #parts I

      #======== 2
      ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_06 -p i,128 > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_06.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_06.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK  ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_06 -p i,128
      else
         echo ERROR ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_06 -p i,128
         exit 1
      fi
      rm   ./test/toto_06*

      #======== 2
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_07 -p i,128 > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_07.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_07.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_07 -p i,128
      else
         echo ERROR ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_07 -p i,128
         exit 1
      fi
      rm   ./test/toto_07*

      #======== 2
      ../sara/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_08 -p i,128 > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_08.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_08.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_08 -p i,128
      else
         echo ERROR ../sara/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_08 -p i,128
         exit 1
      fi
      rm   ./test/toto_08*

      #======== 2
      ../sara/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_09 -p i,128 > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_09.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_09.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_09 -p i,128
      else
         echo ERROR ../sara/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_09 -p i,128
         exit 1
      fi
      rm   ./test/toto_09*


      #parts P

      #======== 2
      ../sara/sr_post.py -u file:${PWD}/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_10 -p p > /dev/null 2>&1
      ../sara/sr_post.py -u file:${PWD}/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_10 -p p > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_10.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_10.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK  ../sara/sr_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_10 -p p 
      else
         echo ERROR ../sara/sr_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_10 -p p
         exit 1
      fi
      rm   ./test/toto_10*

      #======== 2
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_11 -p p > /dev/null 2>&1
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_11 -p p > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_11.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_11.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_11 -p p
      else
         echo ERROR ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_11 -p p
         exit 1
      fi
      rm   ./test/toto_11*

      #======== 2
      ../sara/sr_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_12 -p p > /dev/null 2>&1
      ../sara/sr_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_12 -p p > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_12.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_12.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/sr_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_12 -p p
      else
         echo ERROR ../sara/sr_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_12 -p p
         exit 1
      fi
      rm   ./test/toto_12*

      #======== 2
      ../sara/sr_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_13 -p p > /dev/null 2>&1
      ../sara/sr_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_13 -p p > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto.128.2.0.1.d.Part ./test/toto_13.128.2.0.1.d.Part|wc -l`
      N2=`diff toto.128.2.0.0.d.Part ./test/toto_13.128.2.0.0.d.Part|wc -l`
      if ((N==0 && N2==0)) ; then
         echo OK ../sara/sr_post.py -u ftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_13 -p p
      else
         echo ERROR ../sara/sr_post.py -u ftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_13 -p p
         exit 1
      fi
      rm   ./test/toto_13*

      
      ../sara/sr_sara.py $* stop > /dev/null 2>&1


}

test1 --url file:                ./sara_test1.conf

mv sr_sara_sara_test1_0001.log sr_sara_sara_test1_0001.log_INPLACE_FALSE

echo ==== INPLACE TRUE ====

function test2 {

      ../sara/sr_sara.py $* start > /dev/null 2>&1

      #======== 1
      ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_14 > /dev/null 2>&1
      sleep 2
      ls -al toto ./test/*
      N=`diff toto ./test/toto_14|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_14
      else
         echo ERROR ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_14  
         exit 1
      fi
      rm   ./test/toto_14*

      #======== 1
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_15 > /dev/null 2>&1
      sleep 3
      ls -al toto ./test/*
      N=`diff toto ./test/toto_15|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_15
      else
         echo ERROR ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_15
         exit 1
      fi
      rm   ./test/toto_15*

      #======== 1
      ../sara/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_16 > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto ./test/toto_16|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_16
      else
         echo ERROR ../sara/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_16
         exit 1
      fi
      rm   ./test/toto_16*
      sleep 2

      #======== 1
      ../sara/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_17 > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto ./test/toto_17|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_17
      else
         echo ERROR ../sara/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_17
         exit 1
      fi
      rm   ./test/toto_17*
      sleep 2

      #parts I

      #======== 2
      ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_18 -p i,128  > /dev/null 2>&1
      sleep 4
      ls -al toto ./test/*
      N=`diff toto ./test/toto_18|wc -l`
      if ((N==0)) ; then
         echo OK  ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_18 -p i,128
      else
         echo ERROR ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_18 -p i,128
         exit 1
      fi
      rm   ./test/toto_18*

      #======== 2
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_19 -p i,128 > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto ./test/toto_19|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_19 -p i,128
      else
         echo ERROR ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_19 -p i,128
         exit 1
      fi
      rm   ./test/toto_19*

      #======== 2
      ../sara/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_20 -p i,128 > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto ./test/toto_20|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_20 -p i,128
      else
         echo ERROR ../sara/sr_post.py -u sftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_20 -p i,128
         exit 1
      fi
      rm   ./test/toto_20*


      #======== 2
      ../sara/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_21 -p i,128 > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto ./test/toto_21|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_21 -p i,128
      else
         echo ERROR ../sara/sr_post.py -u ftp://px@localhost//apps/px/test/toto -rn ${PWD}/test/toto_21 -p i,128
         exit 1
      fi
      rm   ./test/toto_21*


      #parts P

      #======== 2
      ../sara/sr_post.py -u file:${PWD}/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_22 -p p > /dev/null 2>&1
      ../sara/sr_post.py -u file:${PWD}/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_22 -p p > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto ./test/toto_22|wc -l`
      if ((N==0)) ; then
         echo OK  ../sara/sr_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_22 -p p 
      else
         echo ERROR ../sara/sr_post.py -u file:${PWD}/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_22 -p p
         exit 1
      fi
      rm   ./test/toto_22*

      #======== 2
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_23 -p p > /dev/null 2>&1
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_23 -p p > /dev/null 2>&1
      sleep 6
      ls -al toto ./test/*
      N=`diff toto ./test/toto_23|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_23 -p p
      else
         echo ERROR ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_23 -p p
         exit 1
      fi
      rm   ./test/toto_23*

      #======== 2
      ../sara/sr_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_24 -p p > /dev/null 2>&1
      ../sara/sr_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_24 -p p > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto ./test/toto_24|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_24 -p p
      else
         echo ERROR ../sara/sr_post.py -u sftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_24 -p p
         exit 1
      fi
      rm   ./test/toto_24*

      #======== 2
      ../sara/sr_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto_25 -p p > /dev/null 2>&1
      ../sara/sr_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto_25 -p p > /dev/null 2>&1
      sleep 8
      ls -al toto ./test/*
      N=`diff toto ./test/toto_25|wc -l`
      if ((N==0)) ; then
         echo OK ../sara/sr_post.py -u ftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_25 -p p
      else
         echo ERROR ../sara/sr_post.py -u ftp://px@localhost//apps/px/test/toto.128.2.0.*.d.Part -rn ${PWD}/test/toto_25 -p p
         exit 1
      fi
      rm   ./test/toto_25*

      ../sara/sr_sara.py $* stop > /dev/null 2>&1

}

test2 --mirror --url file: --inplace True ./sara_test1.conf
mv sr_sara_sara_test1_0001.log sr_sara_sara_test1_0001.log_INPLACE_TRUE

echo ==== INPLACE FALSE NOT MODIFIED ====

function test3 {

      cp ./toto ./test/toto2
      cp ./toto.128.2.0.0.d.Part ./test/toto2.128.2.0.0.d.Part
      cp ./toto.128.2.0.1.d.Part ./test/toto2.128.2.0.1.d.Part

      ../sara/sr_sara.py $* start > /dev/null 2>&1
      #======== 1
      ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2  > /dev/null 2>&1

      #======== 1
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 > /dev/null 2>&1

      #======== 1
      ../sara/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 > /dev/null 2>&1

      #======== 1
      ../sara/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 > /dev/null 2>&1

      #parts I

      #======== 2
      ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1

      #======== 2
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1

      #======== 2
      ../sara/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1

      #======== 2
      ../sara/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto2 -p i,128 > /dev/null 2>&1


      #parts P

      #======== 2
      ../sara/sr_post.py -u file:${PWD}/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      ../sara/sr_post.py -u file:${PWD}/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1

      #======== 2
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      #======== 2
      ../sara/sr_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      ../sara/sr_post.py -u sftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      #======== 2
      ../sara/sr_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.1.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1
      ../sara/sr_post.py -u ftp://localhost//apps/px/test/toto.128.2.0.0.d.Part -rn ${PWD}/test/toto2 -p p > /dev/null 2>&1

      
      sleep 10
      ls -al toto ./test/*

      ../sara/sr_sara.py $* stop > /dev/null 2>&1

      N=`grep modified sr_sara_sara_test1_0001.log  | wc -l`
      if ((N==20)) ; then
         echo OK  not modified in all cases
      else
         echo ERROR should have 20 cases of unmodified files
         exit 1
      fi
      rm   ./test/toto2*
 
      ../sara/sr_sara.py $* stop > /dev/null 2>&1

}

test3 --mirror --url file:                ./sara_test1.conf
mv sr_sara_sara_test1_0001.log sr_sara_sara_test1_0001.log_INPLACE_FALSE_NOT_MODIFIED

echo ==== INSTANCES AND INSERTS ====

function test4 {

         ../sara/sr_sara.py $* ./sara_test1.conf start > /dev/null 2>&1

         ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_26 -p i,1 -r  > /dev/null 2>&1

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

         ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_27 -p i,1 -r > /dev/null 2>&1

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

         ../sara/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_28 -p i,1 -r > /dev/null 2>&1
         
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

         ../sara/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_29 -p i,1 -r > /dev/null 2>&1
         
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

         ../sara/sr_sara.py $* ./sara_test1.conf stop  > /dev/null 2>&1
         sleep 10

}

test4 --mirror --url file: --inplace true --instances 100 

cat sr_sara_sara_test1_*.log >> sr_sara_sara_test1_0001.log_INSTANCES_INSERT
rm sr_sara_sara_test1_*.log


echo ==== INSTANCES AND INSERTS AND TRUNCATE ====

function test5 {

         ../sara/sr_sara.py $* ./sara_test1.conf start > /dev/null 2>&1

         cat toto | sed 's/12345/abcde/' > ./test/toto_30
         echo abc >> ./test/toto_30

         ../sara/sr_post.py -u file:${PWD}/toto -rn ${PWD}/test/toto_30 -p i,11 -r  > /dev/null 2>&1

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

         ../sara/sr_post.py -dr /var/www -u http://localhost/test/toto -rn ${PWD}/test/toto_31 -p i,11 -r > /dev/null 2>&1

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

         ../sara/sr_post.py -u sftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_32 -p i,11 -r > /dev/null 2>&1
         
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

         ../sara/sr_post.py -u ftp://localhost//apps/px/test/toto -rn ${PWD}/test/toto_33 -p i,11 -r > /dev/null 2>&1
         
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
         ../sara/sr_sara.py $* ./sara_test1.conf stop > /dev/null 2>&1

}

test5 --mirror --url file: --inplace true --instances 10
cat sr_sara_sara_test1_*.log >> sr_sara_sara_test1_0001.log_INSTANCES_INSERT_TRUNCATE
rm sr_sara_sara_test1_*.log

rm ./sr_sara_*.log ./.sr_sara_* ./toto* ./test/t* ./sara_test1.conf > /dev/null 2>&1
rmdir ./test > /dev/null 2>&1

