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

POSTBIN="`pwd`/../sarra/sr_post.py -pb amqp://tsource@localhost/ "

export PYTHONPATH=../sarra

cd ${DR}

cat << EOF >toto
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

totodsum="d,`md5sum toto | awk '{ print $1; };'`"

todel=""

# this test does not work, but all it is supposed to do is show the usage...
# FIXME.

tnum=0
tgood=0
tbad=0

# runtest 
#   $1 test description.
#   $2 arguments to sr_post
#   $3 expected exit status
#   $4 string to indicate correct execution.

posttest() {

let tnum++
printf "\nSR_POST TEST ${tnum}: start ($1)\n"

cmd="$POSTBIN -pbd ${DR} $2 >&post.out"
echo $cmd

eval $cmd
st=$?
if [ $st -eq $3 ]; then
  if [ "$4" ]; then
     echo "checking for string +$4+" 
     found="`grep \"$4\" post.out`"
     echo "found: $found" 
     if [ "$found" ]; then
        echo "SR_POST TEST ${tnum}: OK ($1)"
        let tgood++
        #cat post.out
     else
        let tbad++
        cat post.out
        echo "SR_POST TEST ${tnum}: FAIL ($1) missing expected string \"$4\" output:"
     fi    
  else
     echo "SR_POST TEST ${tnum}: OK ($1)"
     let tgood++
     #cat post.out
  fi
else   
  echo "SR_POST TEST failure debug output:"
  let tbad++
  cat post.out
  echo "SR_POST TEST ${tnum}: FAIL ($1)"
fi

}

echo


posttest "echo default broker + default exchange" " -pbu file: -to alta -path toto " 0 $totodsum
posttest "start ( -blocksize ) -caching -reset " " -blocksize 1000Mb --caching -pbu file: -to alta -path toto" 0 
posttest "caching" " -blocksize 1000Mb --caching -pbu file: -to alta -path toto" 0 
posttest "start -blocksize ( -caching ) -reset " "-blocksize 1000Mb --caching -pbu file: -to alta -path toto" 0  
posttest "start -blocksize -caching ( -reset ) " "-reset -blocksize 1000Mb --caching -pbu file: -to alta -path toto" 0 
posttest "default broker + exchange amq.topic should fail with permission" "-pbu file: -ex amq.topic -to alta -path toto" 1
posttest "default guest user and vhost /" " -pbu file: -b amqp://tsource@localhost -to alta -path toto" 0
posttest "new broker user" " -pbu file: -b amqp://tsource@localhost -to alta -path toto " 0

cat << EOF >sr_post.conf
url file:
EOF

echo cat sr_post.conf
cat sr_post.conf
echo
posttest " " "-c ${DR}/sr_post.conf -b amqp://tsource@localhost -to alta -path toto" 0

todel="$todel sr_post.conf"
echo

mkdir -p ~/.config/sarra 2> /dev/null

posttest "sr_post using ~/.config/sarra/credentials.conf " " -pbu file: -b amqp://tsource@localhost -to alta -path toto " 0
posttest " using log file " " -pbu file: -l toto.log -b amqp://tsource@localhost -to alta -path toto" 0

let tnum++
if [ -f toto.log ]; then
   printf "\nSR_POST TEST ${tnum}: OK log file created"
   #echo cat toto.log
   #cat toto.log
   todel="${todel} toto.log"
   let tgood++
else
   printf "\nSR_POST TEST ${tnum}: FAIL log file not created"
   let tbad++
fi
echo

posttest " file url " "-pbu file: -b amqp://tsource@localhost/ -to alta -path toto" 0
posttest " file url with -pbd " " -pbd ${DR} -pbu file: -b amqp://tsource@localhost/ -to alta -path toto " 0


posttest " " "-pbu file: -tp v05.test -b amqp://tsource@localhost/ -to alta -path toto" 0
posttest " " "-pbu file: -sub imposed.sub.topic -b amqp://tsource@localhost/ -to alta -path toto" 0
posttest "-strip -rename " " -pbu file: -rn /this/new/name -b amqp://tsource@localhost/ -to alta -path toto " 0
posttest " -strip 3 " "-pbu file: -strip 3 -b amqp://tsource@localhost/ -to alta -path toto " 0

echo

posttest " rname " "-pbu file: -rn /this/new/dir/ -b amqp://tsource@localhost/ -to alta -path toto " 0
posttest " " "-pbu file: -sum 0 -b amqp://tsource@localhost/ -to alta -path toto" 0

posttest " " "-pbu file: -sum n -b amqp://tsource@localhost/ -to alta -path toto" 0

posttest " " "-pbu file: -sum z,d -b amqp://tsource@localhost/ -to alta -path toto" 0

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

posttest "my checksum" "-pbu file: -sum ${DR}/checksum_AHAH.py -b amqp://tsource@localhost/ -to alta -path toto" 0


posttest " pick exchange xs_tsource " "-pbu file: -ex xs_tsource -to alta -path toto" 0

cp toto toto.256.12.0.1.d.Part

posttest " parts p" " -pbu file: -parts p -to alta -path toto.256.12.0.1.d.Part " 0
posttest " parts p and rename file " " -pbu file:  -rn /this/new/name -parts p -to alta -path toto.256.12.0.1.d.Part " 0
posttest " parts p and rename dir " " -pbu file:  -rn /this/new/dir/ -parts p -to alta -path toto.256.12.0.1.d.Part " 0

todel="${todel} toto.256.12.0.1.d.Part"

posttest " parts i" "-pbu file: -parts i,128 -to alta -path toto" 0

posttest " parts i2"  " -pbu file: -parts i,64 -r -to alta -path toto " 0

posttest " parts i2 -rr " " -pbu file: -parts i,64 -rr -to alta -path toto " 0

posttest " multiple clusters" " -pbu file: -to cluster1,cluster2,cluster3 -path toto " 0

posttest " huh?" " -pbu file: -to alta -path toto" 0


echo

echo ======== ERROR PART =========================
echo

posttest " result should be: ERROR no -to arguments " " -pbu file:  -path toto " 1

posttest "result should be: ERROR file not found" " -pbu file: -to alta -path ${DR}/non_existing_file " 0 "scandir_and_post not a directory"

posttest "result should be: ERROR file not found" " -pbd /fake/directory -pbu file: -to alta -path ${DR}/non_existing_file" 0 "scandir_and_post not a directory /fake/directory"

posttest "result should be: ERROR config file not found" " -c ${DR}/none_existing_file.conf -to alta -path toto " 1

posttest "result should be: ERROR broker not found " " -pbu file: -b amqp://mylocalhost/ -to alta -path toto " 1

echo

posttest "result should be: ERROR broker credential" " -pbu file: -b amqp:toto:titi@localhost/ -to alta -path toto " 1

echo

posttest "result should be: ERROR broker vhost" " -pbu file: -b amqp://localhost/wrong_vhost -to alta -path toto " 1

posttest "echo result should be: ERROR wrong sumflg" " -pbu file: -sum x -to alta -path toto " 1


echo

posttest "result should be: ERROR wrong exchange" " -pbu file:toto -ex hoho -to alta -path toto" 1

echo cp toto toto.12.256.1.d.Part

posttest "result should be: ERROR wrong partfile 1" "-pbu file: -parts p -to alta -path toto.12.256.1.d.Part " 1

cp toto toto.12.256.1.d.Part

posttest "result should be: ERROR wrong partfile 2" " -pbu file: -parts p -to alta -path toto.12.256.1.d.Part " 1


echo

cp toto toto.1024.255.1.d.Part

posttest "result should be: ERROR wrong partfile 3" " -pbu file: -parts p -to alta -path toto.1024.255.1.d.Part " 1


cp toto toto.1024.256.5.d.Part

posttest "echo result should be: ERROR wrong partfile 4" " -pbu file: -parts p -to alta -path toto.1024.256.5.d.Part " 1

echo

cp toto toto.1024.256.1.x.Part
posttest "result should be: ERROR wrong partfile 4" "-pbu file: -parts p -to alta -path toto.1024.256.1.x.Part" 1

rm toto.1024.256.1.x.Part

echo

cp toto toto.1024.256.1.d.bad
posttest "result should be: ERROR wrong partfile 5" " -pbu file: -parts p -to alta -path toto.1024.256.1.d.bad " 1

rm toto.1024.256.1.d.bad

echo

posttest "result should be: ERROR wrong partflg" "-pbu file: -parts x,128 -to alta -path toto " 1

posttest "result should be: ERROR wrong part chunksize" "sr_post -pbu file: -parts d,a -to alta -path toto" 1

lp=ThisStringIs29CharactersLongThisStringIs29CharactersLongThisStringIs29CharactersLongThisStringIs29CharactersLongThisStringIs29CharactersLongThisStringIs29CharactersLongThisStringIs29CharactersLongThisStringIs29CharactersLongThisStringIs29CharactersLongThisStringIs29CharactersLongThisStringIs29CharactersLongThisStringIs29CharactersLongThisStringIs29CharactersLongThisStringIs29CharactersLongThisStringIs29CharactersLong

cp toto $lp

posttest "result should be: ERROR path too long" "sr_post -pbu file: -to alta -path $lp " 1

echo
echo "Summary: $tnum tests $tgood passed, $tbad failed "

rm toto
exit

