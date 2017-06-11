#!/bin/bash

export PYTHONPATH="`pwd`/../"
testdocroot="$HOME/sarra_devdocroot"
testhost=localhost
sftpuser=`whoami`

if [ ! -f $HOME/.config/sarra/default.conf -o ! -f $HOME/.config/sarra/credentials.conf ]; then
 cat <<EOT
 ERROR:
 test users for each role: tsource, tsub, tfeed, bunnymaster (admin)
 need to be created before this script can be run.
 rabbitmq-server needs to be installed on localhost with admin account set and
 manually setup ~/.config/sarra/default.conf, something like this:

cluster localhost
gateway_for alta,cluster1,cluster2

broker amqp://tsource@localhost/
admin amqp://bunnymaster@localhost
feeder  amqp://tfeed@localhost
declare source tsource
declare subscriber tsub
declare subscriber anonymous
declare exchange xhoho
declare exchange xs_tsource_output
declare exchange xs_tsource_src
declare exchange xs_tsource_dest
declare exchange xs_tsource_poll
declare exchange xs_tsource_post
 
and ~/.config/sarra/credentials.conf will need to contain something like:

amqp://bunnymaster:PickAPassword@localhost
amqp://tsource:PickAPassword2@localhost
amqp://tfeed:PickAPassword3@localhost
amqp://tsub:PickAPassword4@localhost
amqp://anonymous:PickAPassword5@localhost
amqp://anonymous:anonymous@dd.weather.gc.ca
amqp://anonymous:anonymous@dd1.weather.gc.ca
amqp://anonymous:anonymous@dd2.weather.gc.ca
sftp://`id`@localhost ssh_keyfile=/home/`id`/.ssh/nopassphrasekey 

EOT
 exit 1
fi
 

if [ ! -d "$testdocroot" ]; then
  mkdir $testdocroot
  cp -r testree/* $testdocroot
  mkdir $testdocroot/downloaded_by_sub_t
  mkdir $testdocroot/sent_by_tsource2send
  mkdir $testdocroot/recd_by_srpoll_test1
  mkdir $testdocroot/posted_by_srpost_test2
fi

lo="`netstat -an | grep '127.0.0.1:8000'|wc -l`"
while [ ${lo} -gt 0 ]; do
   echo "waiting for $lo leftover sockets to clean themselves up from last run."
   sleep 10 
   lo="`netstat -an | grep '127.0.0.1:8000'|wc -l`"
   sleep 5 
done

echo "Starting trivial server on: $testdocroot, saving pid in .httpserverpid"
testrundir="`pwd`"
cd $testdocroot
$testrundir/trivialserver.py >trivialserver.log 2>&1 &
httpserverpid=$!
cd $testrundir

echo $httpserverpid >.httpserverpid
echo $testdocroot >.httpdocroot

for d in .config .config/sarra ; do
   if [ ! -d $HOME/$d ]; then
      mkdir $HOME/$d
   fi
done


for d in poll post report sarra sender shovel subscribe watch winnow ; do
   if [ ! -d $HOME/.config/sarra/$d ]; then
      mkdir $HOME/.config/sarra/$d
   fi
done

templates="`cd flow_templates; ls */*.py */*.conf */*.inc`"

for cf in ${templates}; do
    echo "installing $cf"
    sed 's+SFTPUSER+'"${sftpuser}"'+g; s+HOST+'"${testhost}"'+g; s+TESTDOCROOT+'"${testdocroot}"'+g; s+HOME+'"${HOME}"'+g' <flow_templates/${cf} >$HOME/.config/sarra/${cf}
done

# ensure users have exchanges:
sr_audit --users foreground

adminpw="`awk ' /bunnymaster:.*\@localhost/ { sub(/^.*:/,""); sub(/\@.*$/,""); print $1; exit }; ' ~/.config/sarra/credentials.conf`"

for exchange in xsarra xwinnow xwinnow00 xwinnow01 xs_tfeed xcopy xs_tsource_output xs_tsource_src xs_tsource_dest xs_tsource_poll xs_tsource_post ; do 
   echo "declaring $exchange"
   rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv declare exchange name=${exchange} type=topic auto_delete=false durable=true
done

sr restart
