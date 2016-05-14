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
amqp://anonymous:anonymous@dd.weather.gc.ca
amqp://anonymous:anonymous@dd1.weather.gc.ca
amqp://anonymous:anonymous@dd2.weather.gc.ca

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

for d in .config .config/sarra ; do
   if [ ! -d $HOME/$d ]; then
      mkdir $HOME/$d
   fi
done


for d in sarra subscribe winnow log shovel ; do
   if [ ! -d $HOME/.config/sarra/$d ]; then
      mkdir $HOME/.config/sarra/$d
   fi
done

templates="`cd templates; ls */*.conf */*.inc`"

for cf in ${templates}; do
    echo "installing $cf"
    sed 's+HOST+'"${testhost}"'+g; s+TESTDOCROOT+'"${testdocroot}"'+g' <templates/${cf} >$HOME/.config/sarra/${cf}
done

# ensure users have exchanges:
sr_audit --users foreground

adminpw="`awk ' /bunnymaster:.*\@localhost/ { sub(/^.*:/,""); sub(/\@.*$/,""); print $1; }; ' ~/.config/sarra/credentials.conf`"

for exchange in xsarra xwinnow ; do 
   echo "declaring $exchange"
   rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv declare exchange name=${exchange} type=topic auto_delete=false durable=true
done





sr restart
