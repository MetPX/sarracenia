#../sarra/bi../sarra/sh

export PYTHONPATH="`pwd`/../"
testdocroot="$HOME/sarra_devdocroot"
testhost=localhost

if [ ! -f $HOME/.config/sarra/default.conf -o ! -f $HOME/.config/sarra/credentials.conf ]; then
 cat <<EOT
 ERROR:
 test users for each role: tsource, tsub, tfeed, bunnymaster (admin)
 need to be created before this script can be run.
 rabbitmq-server needs to be installed on localhost with admin account set and
 manually setup ~/.config/sarra/default.conf, something like this:

admin amqp://bunnymaster@localhost
feeder  amqp://tfeed@localhost
role source tsource
role subscriber tsub
role subscriber anonymous

 
and ~/.config/sarra/credentials.conf will need to contain something like:

amqp://bunnymaster:PickAPassword@localhost
amqp://tsource:PickAPassword2@localhost
amqp://tfeed:PickAPassword3@localhost
amqp://tsub:PickAPassword4@localhost
amqp://anonymous:PickAPassword5@localhost

EOT
 exit 1
fi
 

if [ ! -d "$testdocroot" ]; then
  mkdir $testdocroot
  cp -r testree/* $testdocroot
  mkdir $testdocroot/sub
fi

echo "Starting trivial server on: $testdocroot, saving pid in .httpserverpid"
testrundir="`pwd`"
cd $testdocroot
$testrundir/trivialserver.py >trivialserver.log 2>&1 &
httpserverpid=$!
cd $testrundir

echo $httpserverpid >.httpserverpid
echo $testdocroot >.httpdocroot

for d in .config .config/sarra .config/sarra/sarra .config/sarra/subscribe .config/sarra/winnow .config/sarra/log ; do
   if [ ! -d $HOME/$d ]; then
      mkdir $HOME/$d
   fi
done


sed 's+HOST+'"${testhost}"'+g; s+TESTDOCROOT+'"${testdocroot}"'+g' <templates/t_prime_dd.conf >$HOME/.config/sarra/sarra/t_prime_dd.conf

sed 's+HOST+'"${testhost}"'+g; s+TESTDOCROOT+'"${testdocroot}"'+g' <templates/t_sub.conf >$HOME/.config/sarra/subscribe/t_sub.conf

# ensure users have exchanges:
sr_audit --users foreground

sr restart
