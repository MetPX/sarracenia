#!/bin/bash

# This test suppose rabbitmq server installed
# with default configuration  tsource,tsource administrator


SARRA_PATH=`pwd`/../sarra
SARRA_BIN=${SARRA_PATH}/sr_sarra.py
POST_BIN=${SARRA_PATH}/sr_post.py

DR="`cat .httpdocroot`"

if [ ! "${DR}" ]; then
  echo "must run setup.sh first"
  exit 1
else
  echo "Document root is: ${DR}"
fi

export PYTHONPATH=../sarra

cd ${DR}



#if [[ $# != 2 ]]; then
#   echo $0 user password
#   exit 1
#fi
#export USER=$1
#export PASSWORD=$2

echo Creating test files ...

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

# dirs to write published files

if [ ! -d test ]; then
   mkdir test
fi

export TL=${DR}/testlogs
if [ ! -d ${TL} ]; then
   mkdir ${TL}
fi

if [ ! -d testf ]; then
   mkdir testf
fi

cp toto    test/toto
cp toto    testf/toto

cp toto.p0 toto.128.2.0.0.d.Part
cp toto.p0 test/toto.128.2.0.0.d.Part
cp toto.p0 testf/toto.128.2.0.0.d.Part

cp toto.p1 toto.128.2.0.1.d.Part
cp toto.p1 test/toto.128.2.0.1.d.Part
cp toto.p1 testf/toto.128.2.0.1.d.Part


echo Creating sarra config files ...

cat << EOF > sarra_test1.conf

# source

broker amqp://tfeed@localhost/
exchange xs_tsource
subtopic #

directory ${DR}
accept .*

source_from_exchange True
cluster alta

# destination

post_broker amqp://tfeed@localhost/
post_exchange xpublic
document_root ${DR}

EOF

echo ""
echo "* Running INPLACE FALSE test suite:"

tstart=100
tnum=$tstart
tnumstr="100"
tgood=0
tbad=0

# runtest 
#   $1 test description.
#   $2 arguments to sr_post
#   $3 expected exit status
#...   $4 string to indicate correct execution.
#   $4 file name suffix ...


function posttest1() {


printf "\nSR_SARRA POST TEST ${tnum}: start ($1)\n"

if [ "$4" ]; then
   suff="$4"
else
   suff=""
fi

tfile="test/toto_${tnumstr}"
tlog="${TL}/test_${tnumstr}.log"
cmd="$POST_BIN $2  >${tlog} 2>&1"
echo "cwd=`pwd`"
echo $cmd
eval $cmd
sleep  3
# ... _07
# DIFF1=`diff toto.128.2.0.1.d.Part ./test/toto_07.128.2.0.1.d.Part`
DIFF="`diff toto${suff} ${tfile}${suff}`"
if [[ $? != 0 ]] ; then
   N=-1
else
   N=`diff toto${suff} ${tfile}${suff}|wc -l`
fi

if ((N==$3)) ; then
   printf "SR_SARRA POST TEST ${tnum}: OK ($1)\n"
   let tgood++
   rm -f $tlog
   rm ${tfile}
else
   printf "\nSR_SARRA POST TEST ${tnum}: FAIL ($1)\n\n"
   let tbad++
   cat $tlog
fi

let tnum++
tnumstr="`printf "%03d" $tnum `"


}


function test1 {
      
      $SARRA_BIN $* start   > /dev/null 2>&1
      #sleep 5
      echo "sarra initialized. calling post tests... pwd=`pwd`"

      posttest1 "INPLACE FALSE File URL default broker" " -rn test/toto_${tnumstr} -u file: -to cluster1,cluster2,alta ${DR}/toto " 0 

      posttest1 "INPLACE FALSE HTTP URL default broker" " -rn test/toto_${tnumstr} -dr ${DR} -u http://localhost:8000/ -to alta $DR/toto " 0

      # echo -n -e "\tRunning toto_03 test ... "
      posttest1 " SFTP  " " -rn test/toto_${tnumstr} -u sftp://localhost/${DR} -to alta ${DR}/testf/toto " 0

      # echo -n -e "\tRunning toto_07 test ... "
      posttest1 " running http with explicit part " \
            " -dr ${DR} -u http://localhost:8000 -p i,128 -to alta ${DR}/test/toto " \
            0 ".128.2.0.1.d.Part"

      printf "Summary: %d tests $tgood passed, $tbad failed\n" $((tnum-tstart))

      $SARRA_BIN $* stop >/dev/null 2>&1
      exit

      #======== 1
      # echo -n -e "\tRunning toto_03 test ... "
      #DIFF=`diff ${DR}toto ${DR}/test/toto_03`
      #if [[ $? != 0 ]] ; then
      #   N=-1
      #else
      #   N=`diff ${DR}toto ${DR}/test/toto_03|wc -l`
      #fi
     # 
      #if ((N==0)) ; then
      #   echo OK #sr_post -dr ${DR} -u http://localhost:8000/test/toto -rn ${DR}/test/toto_03 -to alta
      #else
      #   echo ERROR          
      #   exit 1
      #fi
      #rm   ${DR}/test/toto_03*



      #======== 1
      # echo -n -e "\tRunning toto_04 test ... "
      echo -n "sr_post -u sftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_04 -to alta ... "
      $SARRA_PATH/sr_post -u sftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto_04 -to alta > /dev/null 2>&1
      sleep 3 
      # ls -al toto ./test/*
      DIFF=`diff toto ./test/toto_04`
      if [[ $? != 0 ]] ; then
         N=-1
      else         
         N=`diff toto ./test/toto_04|wc -l`
      fi
      
      if ((N==0)) ; then
         echo OK #sr_post -u sftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_04 -to alta
      else
         echo ERROR
         exit 1
      fi
      rm   ./test/toto_04*

      #======== 1
      # echo -n -e "\tRunning toto_05 test ... "
      echo -n "sr_post -u ftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_05 -to alta ... "
      $SARRA_PATH/sr_post -u ftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto_05 -to alta > /dev/null 2>&1
      sleep 10
      # ls -al toto ./test/*
      DIFF=`diff toto ./test/toto_05`
      if [[ $? != 0 ]] ; then
         N=-1
      else         
         N=`diff toto ./test/toto_05|wc -l`
      fi
      
      if ((N==0)) ; then
         echo OK #sr_post -u ftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_05 -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_05*

      #parts I

      #======== 2
      # echo -n -e "\tRunning toto_06 test ... "
      echo -n "sr_post -u file:${DR}/toto -rn ${DR}/test/toto_06 -p i,128 -to alta ... "
      $SARRA_PATH/sr_post -u file:${DR}/toto -rn ${DR}/test/toto_06 -p i,128 -to alta > /dev/null 2>&1
      sleep 10
      # ls -al toto ./test/*
      DIFF1=`diff toto.128.2.0.1.d.Part ./test/toto_06.128.2.0.1.d.Part`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto.128.2.0.1.d.Part ./test/toto_06.128.2.0.1.d.Part|wc -l`
      fi

      DIFF2=`diff toto.128.2.0.0.d.Part ./test/toto_06.128.2.0.0.d.Part`
      if [[ $? != 0 ]] ; then
         N2=-1
      else
         N2=`diff toto.128.2.0.0.d.Part ./test/toto_06.128.2.0.0.d.Part|wc -l`
      fi

      if ((N==0 && N2==0)) ; then
         echo OK  #sr_post -u file:${DR}/toto -rn ${DR}/test/toto_06 -p i,128 -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_06*

      #======== 2
      # echo -n -e "\tRunning toto_07 test ... "
      echo -n "sr_post -dr ${DR} -u http://localhost:8000/test/toto -rn ${DR}/test/toto_07 -p i,128 -to alta ... "
      $SARRA_PATH/sr_post -dr ${DR} -u http://localhost:8000/test/toto -rn ${DR}/test/toto_07 -p i,128 -to alta > /dev/null 2>&1
      sleep 10
      # ls -al toto ./test/*
      DIFF1=`diff toto.128.2.0.1.d.Part ./test/toto_07.128.2.0.1.d.Part`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto.128.2.0.1.d.Part ./test/toto_07.128.2.0.1.d.Part|wc -l`
      fi   

      DIFF2=`diff toto.128.2.0.0.d.Part ./test/toto_07.128.2.0.0.d.Part`
      if [[ $? != 0 ]] ; then
         N2=-1
      else     
         N2=`diff toto.128.2.0.0.d.Part ./test/toto_07.128.2.0.0.d.Part|wc -l`
      fi

      if ((N==0 && N2==0)) ; then
         echo OK # sr_post -dr ${DR} -u http://localhost:8000/test/toto -rn ${DR}/test/toto_07 -p i,128 -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_07*

      #======== 2
      # echo -n -e "\tRunning toto_08 test ... "
      echo -n "sr_post -u sftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_08 -p i,128 -to alta ... "
      $SARRA_PATH/sr_post -u sftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto_08 -p i,128 -to alta > /dev/null 2>&1
      sleep 8
      # ls -al toto ./test/*
      DIFF1=`diff toto.128.2.0.1.d.Part ./test/toto_08.128.2.0.1.d.Part`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto.128.2.0.1.d.Part ./test/toto_08.128.2.0.1.d.Part|wc -l`
      fi

      DIFF2=`diff toto.128.2.0.0.d.Part ./test/toto_08.128.2.0.0.d.Part`
      if [[ $? != 0 ]] ; then
         N2=-1
      else
         N2=`diff toto.128.2.0.0.d.Part ./test/toto_08.128.2.0.0.d.Part|wc -l`
      fi

      if ((N==0 && N2==0)) ; then
         echo OK #sr_post -u sftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_08 -p i,128 -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_08*

      #======== 2
      # echo -n -e "\tRunning toto_09 test ... "
      echo -n "sr_post -u ftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_09 -p i,128 -to alta ... "
      $SARRA_PATH/sr_post -u ftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto_09 -p i,128 -to alta > /dev/null 2>&1
      sleep 8
      # ls -al toto ./test/*
      DIFF1=`diff toto.128.2.0.1.d.Part ./test/toto_09.128.2.0.1.d.Part`
      if [[ $? != 0 ]] ; then 
         N=-1
      else
         N=`diff toto.128.2.0.1.d.Part ./test/toto_09.128.2.0.1.d.Part|wc -l`
      fi

      DIFF2=`diff toto.128.2.0.0.d.Part ./test/toto_09.128.2.0.0.d.Part`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N2=`diff toto.128.2.0.0.d.Part ./test/toto_09.128.2.0.0.d.Part|wc -l`
      fi

      if ((N==0 && N2==0)) ; then
         echo OK #sr_post -u ftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_09 -p i,128 -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_09*


      #parts P

      #======== 2
      # echo -n -e "\tRunning toto_10 test ... "
      echo -n "sr_post -u file:${DR}/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_10 -p p -to alta ... "
      $SARRA_PATH/sr_post -u file:${DR}/toto.128.2.0.1.d.Part -rn ${DR}/test/toto_10 -p p -to alta > /dev/null 2>&1
      $SARRA_PATH/sr_post -u file:${DR}/toto.128.2.0.0.d.Part -rn ${DR}/test/toto_10 -p p -to alta > /dev/null 2>&1
      sleep 4
      # ls -al toto ./test/*

      DIFF1=`diff toto.128.2.0.1.d.Part ./test/toto_10.128.2.0.1.d.Part`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto.128.2.0.1.d.Part ./test/toto_10.128.2.0.1.d.Part|wc -l`
      fi

      DIFF2=`diff toto.128.2.0.0.d.Part ./test/toto_10.128.2.0.0.d.Part`
      if [[ $? != 0 ]] ; then
         N2=-1
      else
         N2=`diff toto.128.2.0.0.d.Part ./test/toto_10.128.2.0.0.d.Part`
      fi

      if ((N==0 && N2==0)) ; then
         echo OK  #sr_post -u file:${DR}/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_10 -p p -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_10*

      #======== 2
      # echo -n -e "\tRunning toto_11 test ... "
      echo -n "sr_post -dr ${DR} -u http://localhost:8000/test/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_11 -p p -to alta ... "
      $SARRA_PATH/sr_post -dr ${DR} -u http://localhost:8000/test/toto.128.2.0.1.d.Part -rn ${DR}/test/toto_11 -p p -to alta > /dev/null 2>&1
      $SARRA_PATH/sr_post -dr ${DR} -u http://localhost:8000/test/toto.128.2.0.0.d.Part -rn ${DR}/test/toto_11 -p p -to alta > /dev/null 2>&1
      sleep 6
      # ls -al toto ./test/*
      DIFF1=`diff toto.128.2.0.1.d.Part ./test/toto_11.128.2.0.1.d.Part`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto.128.2.0.1.d.Part ./test/toto_11.128.2.0.1.d.Part|wc -l`
      fi

      DIFF2=`diff toto.128.2.0.0.d.Part ./test/toto_11.128.2.0.0.d.Part`
      if [[ $? != 0 ]] ; then
         N2=-1
      else
         N2=`diff toto.128.2.0.0.d.Part ./test/toto_11.128.2.0.0.d.Part|wc -l`
      fi

      if ((N==0 && N2==0)) ; then
         echo OK #sr_post -dr ${DR} -u http://localhost:8000/test/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_11 -p p -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_11*

      #======== 2
      # echo -n -e "\tRunning toto_12 test ... "
      echo -n "sr_post -u sftp://px@localhost/${DR}/testf/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_12 -p p -to alta ... "
      $SARRA_PATH/sr_post -u sftp://localhost/${DR}/testf/toto.128.2.0.1.d.Part -rn ${DR}/test/toto_12 -p p -to alta > /dev/null 2>&1
      $SARRA_PATH/sr_post -u sftp://localhost/${DR}/testf/toto.128.2.0.0.d.Part -rn ${DR}/test/toto_12 -p p -to alta > /dev/null 2>&1
      sleep 8
      # ls -al toto ./test/*
      DIFF1=`diff toto.128.2.0.1.d.Part ./test/toto_12.128.2.0.1.d.Part`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto.128.2.0.1.d.Part ./test/toto_12.128.2.0.1.d.Part|wc -l`
      fi

      DIFF2=`diff toto.128.2.0.0.d.Part ./test/toto_12.128.2.0.0.d.Part`

      if [[ $? != 0 ]] ; then
         N2=-1
      else
         N2=`diff toto.128.2.0.0.d.Part ./test/toto_12.128.2.0.0.d.Part|wc -l`
      fi

      if ((N==0 && N2==0)) ; then
         echo OK #sr_post -u sftp://px@localhost/${DR}/testf/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_12 -p p -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_12*

      #======== 2
      # echo -n -e "\tRunning toto_13 test ... "
      echo -n "sr_post -u ftp://px@localhost/${DR}/testf/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_13 -p p -to alta ... "
      $SARRA_PATH/sr_post -u ftp://localhost/${DR}/testf/toto.128.2.0.1.d.Part -rn ${DR}/test/toto_13 -p p -to alta > /dev/null 2>&1
      $SARRA_PATH/sr_post -u ftp://localhost/${DR}/testf/toto.128.2.0.0.d.Part -rn ${DR}/test/toto_13 -p p -to alta > /dev/null 2>&1
      sleep 8
      # ls -al toto ./test/*
      DIFF1=`diff toto.128.2.0.1.d.Part ./test/toto_13.128.2.0.1.d.Part`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto.128.2.0.1.d.Part ./test/toto_13.128.2.0.1.d.Part|wc -l`
      fi

      DIFF2=`diff toto.128.2.0.0.d.Part ./test/toto_13.128.2.0.0.d.Part`
      if [[ $? != 0 ]] ; then
         N2=-1
      else
         N2=`diff toto.128.2.0.0.d.Part ./test/toto_13.128.2.0.0.d.Part|wc -l`
      fi

      if ((N==0 && N2==0)) ; then
         echo OK #sr_post -u ftp://px@localhost/${DR}/testf/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_13 -p p -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_13*
      
      $SARRA_BIN $* stop > /dev/null 2>&1
}

test1 --debug --url file: ./sarra_test1.conf
mv sr_sarra_sarra_test1_0001.log sr_sarra_sarra_test1_0001.log_INPLACE_FALSE

echo ""
echo "* Running INPLACE TRUE test suite:"

function test2 {
      # echo -n -e "\tRunning toto_14 test ... "
      echo -n "sr_post -u file:${DR}/toto -rn ${DR}/test/toto_14 -to alta ... "
      $SARRA_BIN $* start > /dev/null 2>&1

      #======== 1
      $SARRA_PATH/sr_post -u file:${DR}/toto -rn ${DR}/test/toto_14 -to alta > /dev/null 2>&1
      sleep 2
      # ls -al toto ./test/*
      DIFF=`diff toto ./test/toto_14`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto ./test/toto_14|wc -l`
      fi

      if ((N==0)) ; then
         echo OK #sr_post -u file:${DR}/toto -rn ${DR}/test/toto_14 -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_14*

      #======== 1
      # echo -n -e "\tRunning toto_15 test ... "
      echo -n "sr_post -dr ${DR} -u http://localhost:8000/test/toto -rn ${DR}/test/toto_15 -to alta ... "
      $SARRA_PATH/sr_post -dr ${DR} -u http://localhost:8000/test/toto -rn ${DR}/test/toto_15 -to alta > /dev/null 2>&1
      sleep 3
      # ls -al toto ./test/*
      DIFF=`diff toto ./test/toto_15`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto ./test/toto_15|wc -l`
      fi

      if ((N==0)) ; then
         echo OK #sr_post -dr ${DR} -u http://localhost:8000/test/toto -rn ${DR}/test/toto_15 -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_15*

      #======== 1
      # echo -n -e "\tRunning toto_16 test ... "
      echo -n "sr_post -u sftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_16 -to alta ... "
      $SARRA_PATH/sr_post -u sftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto_16 -to alta > /dev/null 2>&1
      sleep 4
      # ls -al toto ./test/*
      DIFF=`diff toto ./test/toto_16`
      if [[ $? != 0 ]] ; then
         N=-1
      else         
         N=`diff toto ./test/toto_16|wc -l`
      fi

      if ((N==0)) ; then
         echo OK #sr_post -u sftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_16 -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_16*
      sleep 2

      #======== 1
      # echo -n -e "\tRunning toto_17 test ... "
      echo -n "sr_post -u ftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_17 -to alta ... "
      $SARRA_PATH/sr_post -u ftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto_17 -to alta > /dev/null 2>&1
      sleep 4
      # ls -al toto ./test/*
      DIFF=`diff toto ./test/toto_17`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto ./test/toto_17|wc -l`
      fi

      if ((N==0)) ; then
         echo OK #sr_post -u ftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_17 -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_17*
      sleep 2

      #parts I

      #======== 2
      # echo -n -e "\tRunning toto_18 test ... "
      echo -n "sr_post -u file:${DR}/toto -rn ${DR}/test/toto_18 -p i,128 -to alta ... "
      $SARRA_PATH/sr_post -u file:${DR}/toto -rn ${DR}/test/toto_18 -p i,128 -to alta > /dev/null 2>&1
      sleep 4
      # ls -al toto ./test/*
      DIFF=`diff toto ./test/toto_18`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto ./test/toto_18|wc -l`
      fi

      if ((N==0)) ; then
         echo OK  #sr_post -u file:${DR}/toto -rn ${DR}/test/toto_18 -p i,128 -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_18*

      #======== 2
      # echo -n -e "\tRunning toto_19 test ... "
      echo -n "sr_post -dr ${DR} -u http://localhost:8000/test/toto -rn ${DR}/test/toto_19 -p i,128 -to alta ... "
      $SARRA_PATH/sr_post -dr ${DR} -u http://localhost:8000/test/toto -rn ${DR}/test/toto_19 -p i,128 -to alta > /dev/null 2>&1
      sleep 6
      # ls -al toto ./test/*
      DIFF=`diff toto ./test/toto_19`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto ./test/toto_19|wc -l`
      fi

      if ((N==0)) ; then
         echo OK #sr_post -dr ${DR} -u http://localhost:8000/test/toto -rn ${DR}/test/toto_19 -p i,128 -to alta
      else
         echo ERROR          
         exit 1
      fi
      rm   ./test/toto_19*

      #======== 2
      # echo -n -e "\tRunning toto_20 test ... "
      echo -n "sr_post -u sftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_20 -p i,128 -to alta ... "
      $SARRA_PATH/sr_post -u sftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto_20 -p i,128 -to alta > /dev/null 2>&1
      sleep 8
      # ls -al toto ./test/*
      DIFF=`diff toto ./test/toto_20`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto ./test/toto_20|wc -l`
      fi

      if ((N==0)) ; then
         echo OK #sr_post -u sftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_20 -p i,128 -to alta
      else
         echo ERROR         
         exit 1
      fi
      rm   ./test/toto_20*


      #======== 2
      echo -n "sr_post -u ftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_21 -p i,128 -to alta ... "
      $SARRA_PATH/sr_post -u ftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto_21 -p i,128 -to alta > /dev/null 2>&1
      sleep 8
      # ls -al toto ./test/*
      DIFF=`diff toto ./test/toto_21`
      if [[ $? != 0 ]] ; then
         N=-1
      else         
         N=`diff toto ./test/toto_21|wc -l`
      fi

      if ((N==0)) ; then
         echo OK #sr_post -u ftp://px@localhost/${DR}/testf/toto -rn ${DR}/test/toto_21 -p i,128 -to alta
      else
         echo ERROR 
         exit 1
      fi
      rm   ./test/toto_21*


      #parts P

      #======== 2
      echo -n "sr_post -u file:${DR}/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_22 -p p  -to alta ... "
      $SARRA_PATH/sr_post -u file:${DR}/toto.128.2.0.1.d.Part -rn ${DR}/test/toto_22 -p p -to alta > /dev/null 2>&1
      $SARRA_PATH/sr_post -u file:${DR}/toto.128.2.0.0.d.Part -rn ${DR}/test/toto_22 -p p -to alta > /dev/null 2>&1
      sleep 6
      # ls -al toto ./test/*
      DIFF=`diff toto ./test/toto_22`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto ./test/toto_22|wc -l`
      fi

      if ((N==0)) ; then
         echo OK  #sr_post -u file:${DR}/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_22 -p p  -to alta
      else
         echo ERROR 
         exit 1
      fi
      rm   ./test/toto_22*

      #======== 2
      echo -n "sr_post -dr ${DR} -u http://localhost:8000/test/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_23 -p p -to alta ... "
      $SARRA_PATH/sr_post -dr ${DR} -u http://localhost:8000/test/toto.128.2.0.1.d.Part -rn ${DR}/test/toto_23 -p p  -to alta > /dev/null 2>&1
      $SARRA_PATH/sr_post -dr ${DR} -u http://localhost:8000/test/toto.128.2.0.0.d.Part -rn ${DR}/test/toto_23 -p p  -to alta > /dev/null 2>&1
      sleep 6
      # ls -al toto ./test/*
      DIFF=`diff toto ./test/toto_23`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto ./test/toto_23|wc -l`
      fi

      if ((N==0)) ; then
         echo OK #sr_post -dr ${DR} -u http://localhost:8000/test/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_23 -p p -to alta 
      else
         echo ERROR
         exit 1
      fi
      rm   ./test/toto_23*

      #======== 2
      echo -n "sr_post -u sftp://px@localhost/${DR}/testf/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_24 -p p -to alta ... "
      $SARRA_PATH/sr_post -u sftp://localhost/${DR}/testf/toto.128.2.0.1.d.Part -rn ${DR}/test/toto_24 -p p  -to alta > /dev/null 2>&1
      $SARRA_PATH/sr_post -u sftp://localhost/${DR}/testf/toto.128.2.0.0.d.Part -rn ${DR}/test/toto_24 -p p  -to alta > /dev/null 2>&1
      sleep 8
      # ls -al toto ./test/*
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto ./test/toto_24|wc -l`
      fi

      if ((N==0)) ; then
         echo OK #sr_post -u sftp://px@localhost/${DR}/testf/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_24 -p p -to alta 
      else
         echo ERROR
         exit 1
      fi
      rm   ./test/toto_24*

      #======== 2
      echo -n "sr_post -u ftp://px@localhost/${DR}/testf/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_25 -p p -to alta ... "
      $SARRA_PATH/sr_post -u ftp://localhost/${DR}/testf/toto.128.2.0.1.d.Part -rn ${DR}/test/toto_25 -p p  -to alta > /dev/null 2>&1
      $SARRA_PATH/sr_post -u ftp://localhost/${DR}/testf/toto.128.2.0.0.d.Part -rn ${DR}/test/toto_25 -p p  -to alta > /dev/null 2>&1
      sleep 8
      # ls -al toto ./test/*
      DIFF=`diff toto ./test/toto_25`
      if [[ $? != 0 ]] ; then
         N=-1
      else
         N=`diff toto ./test/toto_25|wc -l`
      fi

      if ((N==0)) ; then
         echo OK #sr_post -u ftp://px@localhost/${DR}/testf/toto.128.2.0.*.d.Part -rn ${DR}/test/toto_25 -p p -to alta 
      else
         echo ERROR
         exit 1
      fi
      rm   ./test/toto_25*

      $SARRA_BIN $* stop > /dev/null 2>&1

}

test2 --mirror True --url file: --inplace True ./sarra_test1.conf
mv sr_sarra_sarra_test1_0001.log sr_sarra_sarra_test1_0001.log_INPLACE_TRUE

# echo ==== INPLACE FALSE NOT MODIFIED ====
echo ""
echo "* Running INPLACE FALSE NOT MODIFIED test suite:"

function test3 {

      echo -n "Performing test ... "
      cp ./toto ./test/toto2
      cp ./toto.128.2.0.0.d.Part ./test/toto2.128.2.0.0.d.Part
      cp ./toto.128.2.0.1.d.Part ./test/toto2.128.2.0.1.d.Part

      $SARRA_BIN $* start > /dev/null 2>&1
      #======== 1
      $SARRA_PATH/sr_post -u file:${DR}/toto -rn ${DR}/test/toto2   -to alta > /dev/null 2>&1

      #======== 1
      $SARRA_PATH/sr_post -dr ${DR} -u http://localhost:8000/test/toto -rn ${DR}/test/toto2  -to alta > /dev/null 2>&1

      #======== 1
      $SARRA_PATH/sr_post -u sftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto2  -to alta > /dev/null 2>&1

      #======== 1
      $SARRA_PATH/sr_post -u ftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto2  -to alta > /dev/null 2>&1

      #parts I

      #======== 2
      $SARRA_PATH/sr_post -u file:${DR}/toto -rn ${DR}/test/toto2 -p i,128  -to alta > /dev/null 2>&1

      #======== 2
      $SARRA_PATH/sr_post -dr ${DR} -u http://localhost:8000/test/toto -rn ${DR}/test/toto2 -p i,128  -to alta > /dev/null 2>&1

      #======== 2
      $SARRA_PATH/sr_post -u sftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto2 -p i,128  -to alta > /dev/null 2>&1

      #======== 2
      $SARRA_PATH/sr_post -u ftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto2 -p i,128  -to alta > /dev/null 2>&1


      #parts P

      #======== 2
      $SARRA_PATH/sr_post -u file:${DR}/toto.128.2.0.1.d.Part -rn ${DR}/test/toto2 -p p  -to alta > /dev/null 2>&1
      $SARRA_PATH/sr_post -u file:${DR}/toto.128.2.0.0.d.Part -rn ${DR}/test/toto2 -p p  -to alta > /dev/null 2>&1

      #======== 2
      $SARRA_PATH/sr_post -dr ${DR} -u http://localhost:8000/test/toto.128.2.0.1.d.Part -rn ${DR}/test/toto2 -p p  -to alta > /dev/null 2>&1
      $SARRA_PATH/sr_post -dr ${DR} -u http://localhost:8000/test/toto.128.2.0.0.d.Part -rn ${DR}/test/toto2 -p p  -to alta > /dev/null 2>&1
      #======== 2
      $SARRA_PATH/sr_post -u sftp://localhost/${DR}/testf/toto.128.2.0.1.d.Part -rn ${DR}/test/toto2 -p p  -to alta > /dev/null 2>&1
      $SARRA_PATH/sr_post -u sftp://localhost/${DR}/testf/toto.128.2.0.0.d.Part -rn ${DR}/test/toto2 -p p  -to alta > /dev/null 2>&1
      #======== 2
      $SARRA_PATH/sr_post -u ftp://localhost/${DR}/testf/toto.128.2.0.1.d.Part -rn ${DR}/test/toto2 -p p  -to alta > /dev/null 2>&1
      $SARRA_PATH/sr_post -u ftp://localhost/${DR}/testf/toto.128.2.0.0.d.Part -rn ${DR}/test/toto2 -p p  -to alta > /dev/null 2>&1

      
      sleep 10
      # ls -al toto ./test/*

      $SARRA_BIN $* stop > /dev/null 2>&1

      N=`grep modified sr_sarra_sarra_test1_0001.log  | wc -l`
      if ((N==20)) ; then
         echo OK  not modified in all cases
      else
         echo ERROR should have 20 cases of unmodified files
         exit 1
      fi
      rm   ./test/toto2*
 
      $SARRA_BIN $* stop > /dev/null 2>&1

}

test3 --mirror True --url file:                ./sarra_test1.conf
mv sr_sarra_sarra_test1_0001.log sr_sarra_sarra_test1_0001.log_INPLACE_FALSE_NOT_MODIFIED

# echo ==== INSTANCES AND INSERTS ====
echo ""
echo "* Running INSTANCES AND INSERTS test suite:"

function test4 {

         $SARRA_BIN $* ./sarra_test1.conf start > /dev/null 2>&1

         echo -n "Testing file ... "
         $SARRA_PATH/sr_post -u file:${DR}/toto -rn ${DR}/test/toto_26 -p i,1 -r   -to alta > /dev/null 2>&1

               sleep 20
               # ls -al toto ./test/*
               N=`diff toto ./test/toto_26|wc -l`
               if ((N==0)) ; then
                  echo OK
               else
                  echo ERROR
                  exit 1
               fi
               rm   ./test/toto_26*

         echo -n "Testing http ... "
         $SARRA_PATH/sr_post -dr ${DR} -u http://localhost:8000/test/toto -rn ${DR}/test/toto_27 -p i,1 -r  -to alta > /dev/null 2>&1

               sleep 30
               # ls -al toto ./test/*
               N=`diff toto ./test/toto_27|wc -l`
               if ((N==0)) ; then
                  echo OK
               else
                  echo ERROR
                  exit 1
               fi
               rm   ./test/toto_27*

         echo -n "Testing sftp ... "
         $SARRA_PATH/sr_post -u sftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto_28 -p i,1 -r  -to alta > /dev/null 2>&1
         
               sleep 40
               # ls -al toto ./test/*
               N=`diff toto ./test/toto_28|wc -l`
               if ((N==0)) ; then
                  echo OK
               else
                  echo ERROR
                  exit 1
               fi
               rm   ./test/toto_28*

         echo -n "Testing ftp ... "
         $SARRA_PATH/sr_post -u ftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto_29 -p i,1 -r  -to alta > /dev/null 2>&1
         
               sleep 40
               # ls -al toto ./test/*
               N=`diff toto ./test/toto_29|wc -l`
               if ((N==0)) ; then
                  echo OK
               else
                  echo ERROR
                  exit 1
               fi
               rm   ./test/toto_29*

         $SARRA_BIN $* ./sarra_test1.conf stop  > /dev/null 2>&1
         sleep 10

}

test4 --mirror True --url file: --inplace true --instances 100 

cat sr_sarra_sarra_test1_*.log >> sr_sarra_sarra_test1_0001.log_INSTANCES_INSERT
rm sr_sarra_sarra_test1_*.log


# echo ==== INSTANCES AND INSERTS AND TRUNCATE ====
echo ""
echo "* Running INSTANCES AND INSERTS AND TRUNCATE testing suite:"

function test5 {

         $SARRA_BIN $* ./sarra_test1.conf start > /dev/null 2>&1

         cat toto | sed 's/12345/abcde/' > ./test/toto_30
         echo abc >> ./test/toto_30

         echo -n "Testing file ... "
         $SARRA_PATH/sr_post -u file:${DR}/toto -rn ${DR}/test/toto_30 -p i,11 -r  -to alta  > /dev/null 2>&1

               sleep 20
               # ls -al toto ./test/*
               N=`diff toto ./test/toto_30|wc -l`
               if ((N==0)) ; then
                  echo OK
               else
                  echo ERROR
                  exit 1
               fi
               rm   ./test/toto_30*


         cat toto | sed 's/12345/abcde/' > ./test/toto_31
         echo abc >> ./test/toto_31

         echo -n "Testing http ... "
         $SARRA_PATH/sr_post -dr ${DR} -u http://localhost:8000/test/toto -rn ${DR}/test/toto_31 -p i,11 -r  -to alta > /dev/null 2>&1

               sleep 30
               # ls -al toto ./test/*
               N=`diff toto ./test/toto_31|wc -l`
               if ((N==0)) ; then
                  echo OK
               else
                  echo ERROR
                  exit 1
               fi
               rm   ./test/toto_31*


         cat toto | sed 's/12345/abcde/' > ./test/toto_32
         echo abc >> ./test/toto_32

         echo -n "Testing sftp ... "
         $SARRA_PATH/sr_post -u sftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto_32 -p i,11 -r  -to alta > /dev/null 2>&1
         
               sleep 60
               # ls -al toto ./test/*
               N=`diff toto ./test/toto_32|wc -l`
               if ((N==0)) ; then
                  echo OK
               else
                  echo ERROR
                  exit 1
               fi
               rm   ./test/toto_32*

         cat toto | sed 's/12345/abcde/' > ./test/toto_33
         echo abc >> ./test/toto_33

         echo -n "Testing ftp ... "
         $SARRA_PATH/sr_post -u ftp://localhost/${DR}/testf/toto -rn ${DR}/test/toto_33 -p i,11 -r  -to alta > /dev/null 2>&1
         
               sleep 60
               # ls -al toto ./test/*
               N=`diff toto ./test/toto_33|wc -l`
               if ((N==0)) ; then
                  echo OK
               else
                  echo ERROR
                  exit 1
               fi
               rm   ./test/toto_33*

         sleep 10
         $SARRA_BIN $* ./sarra_test1.conf stop > /dev/null 2>&1

}

test5 --mirror True --url file: --inplace true --instances 10
cat sr_sarra_sarra_test1_*.log >> sr_sarra_sarra_test1_0001.log_INSTANCES_INSERT_TRUNCATE
rm sr_sarra_sarra_test1_*.log

rm ./sr_sarra_*.log ./.sr_sarra_* ./toto* ./test/t* ./sarra_test1.conf > /dev/null 2>&1
rmdir ./test > /dev/null 2>&1

