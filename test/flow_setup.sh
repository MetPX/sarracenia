#!/bin/bash

# make sure libsrshim is off

export SR_POST_CONFIG=""
export LD_PRELOAD=""


export PYTHONPATH="`pwd`/../"
testdocroot="$HOME/sarra_devdocroot"
testhost=localhost
sftpuser=`whoami`

function application_dirs {
python3 << EOF
import appdirs

cachedir  = appdirs.user_cache_dir('sarra','science.gc.ca')
cachedir  = cachedir.replace(' ','\ ')
print('export CACHEDIR=%s'% cachedir)

confdir = appdirs.user_config_dir('sarra','science.gc.ca')
confdir = confdir.replace(' ','\ ')
print('export CONFDIR=%s'% confdir)

logdir  = appdirs.user_log_dir('sarra','science.gc.ca')
logdir  = logdir.replace(' ','\ ')
print('export LOGDIR=%s'% logdir)

EOF
}

eval `application_dirs`

if [ ! -f "$CONFDIR"/admin.conf -o ! -f "$CONFDIR"/credentials.conf ]; then
 cat <<EOT
 ERROR:
 test users for each role: tsource, tsub, tfeed, bunnymaster (admin)
 need to be created before this script can be run.
 rabbitmq-server needs to be installed on a machine (FLOWBROKER) with admin account set and
 manually setup in "$CONFDIR"/admin.conf, something like this:

declare env FLOWBROKER=localhost
declare env SFTPUSER="`whoami`"
declare env TESTDOCROOT=${HOME}/sarra_devdocroot

broker amqp://tsource@localhost/
admin amqp://bunnymaster@localhost
feeder  amqp://tfeed@localhost
declare source tsource
declare subscriber tsub
declare subscriber anonymous

and "$CONFDIR"/credentials.conf will need to contain something like:

amqp://bunnymaster:PickAPassword@localhost
ftp://anonymous:anonymous@localhost:2121/
amqp://tsource:PickAPassword2@localhost
amqp://tfeed:PickAPassword3@localhost
amqp://tsub:PickAPassword4@localhost
amqp://anonymous:PickAPassword5@localhost
amqp://anonymous:anonymous@dd.weather.gc.ca
amqp://anonymous:anonymous@dd1.weather.gc.ca
amqp://anonymous:anonymous@dd2.weather.gc.ca

EOT
 exit 1
fi
 
if [ ! -d "$testdocroot" ]; then
  mkdir $testdocroot
  cp -r testree/* $testdocroot
  mkdir $testdocroot/downloaded_by_sub_t
  mkdir $testdocroot/downloaded_by_sub_u
  mkdir $testdocroot/sent_by_tsource2send
  mkdir $testdocroot/recd_by_srpoll_test1
  mkdir $testdocroot/posted_by_srpost_test2
  mkdir $testdocroot/cfr
  mkdir $testdocroot/cfile
fi

lo="`netstat -an | grep '127.0.0.1:8000'|wc -l`"
while [ ${lo} -gt 0 ]; do
   echo "waiting for $lo leftover sockets to clean themselves up from last run."
   sleep 10 
   lo="`netstat -an | grep '127.0.0.1:8000'|wc -l`"
   sleep 5 
done

mkdir -p "$CONFDIR" 2> /dev/null

flow_confs="`cd ../sarra/examples; ls */*f[0-9][0-9].conf`"
flow_incs="`cd ../sarra/examples; ls */*f[0-9][0-9].inc`"

echo $flow_incs $flow_confs | sed 's/ / ; sr_/g' | sed 's/^/ sr_/' | sed 's+/+ add +g' | sh -x

# sr_post "add" doesn't. so a little help:
cp ../sarra/examples/post/*f[0-9][0-9].conf ~/.config/sarra/post


passed_checks=0
count_of_checks=0

queued_msgcnt="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv $query |awk '(NR == 2) { print $3; };'`"

function qchk {
#
# qchk verify correct number of queues present.
#
# 1 - number of queues to expect.
# 2 - Description string.
# 3 - query
#
queue_cnt="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv $3 |awk '(NR == 2) { print $4 };'`"

if [ "$queue_cnt" = $1 ]; then
    echo "OK, as expected $1 $2" 
    passed_checks=$((${passed_checks}+1))
else
    echo "FAILED, expected $1, but there are $queue_cnt $2"
fi

count_of_checks=$((${count_of_checks}+1))

}

function xchk {
#
# qchk verify correct number of exchanges present.
#
# 1 - number of exchanges to expect.
# 2 - Description string.
#
exnow=${LOGDIR}/flow_setup.exchanges.txt
exex=flow_lists/exchanges_expected.txt
rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list exchanges >$exnow

x_cnt="`wc -l <$exnow`"
expected_cnt="`wc -l <$exex`"
# remove column header...
x_cnt=$((${x_cnt}-1))

if [ "$x_cnt" = $expected_cnt ]; then
    echo "OK, as expected $expected_cnt $1" 
    passed_checks=$((${passed_checks}+1))
else
    echo "FAILED, expected $expected_cnt, but there are $x_cnt $1"
    printf "Missing exchanges: %s\n" "`comm -23 $exex $exnow`"
    printf "Extra exchanges: %s\n" "`comm -13 $exex $exnow`"
fi

count_of_checks=$((${count_of_checks}+1))

}


#xchk 8 "only rabbitmq default systems exchanges should be present."

# ensure users have exchanges:
sr_audit --users foreground
adminpw="`awk ' /bunnymaster:.*\@localhost/ { sub(/^.*:/,""); sub(/\@.*$/,""); print $1; exit }; ' "$CONFDIR"/credentials.conf`"

qchk 17 "queues existing after 1st audit" "show overview" 
xchk "exchanges for flow test created."

if [ "$1" = "declare" ]; then
   exit 0
fi

testrundir="`pwd`"

echo "Starting trivial http server on: $testdocroot, saving pid in .httpserverpid"
cd $testdocroot
$testrundir/trivialserver.py >trivialhttpserver.log 2>&1 &
httpserverpid=$!

# note, defaults to port 2121 so devs can start it.
python3 -m pyftpdlib >trivialftpserver.log 2>&1 &
ftpserverpid=$!

cd $testrundir

./flow_post.sh >${LOGDIR}/srposter.log 2>&1 &
flowpostpid=$!


echo $ftpserverpid >.ftpserverpid
echo $httpserverpid >.httpserverpid
echo $testdocroot >.httpdocroot
echo $flowpostpid >.flowpostpid

sr start

#sr_subscribe stop fclean
#sr_subscribe cleanup fclean
#sr_subscribe remove fclean

ret=$?

count_of_checks=$((${count_of_checks}+1))
if [ $ret -ne 0 ]; then
   echo "FAILED: sr start returned error status"
else
   echo "OK: sr start was successful"
   passed_checks=$((${passed_checks}+1))
fi

if [ $passed_checks = $count_of_checks ]; then
   echo "Overall PASSED $passed_checks/$count_of_checks checks passed!"
else
   echo "Overall: FAILED $passed_checks/$count_of_checks passed."
fi
