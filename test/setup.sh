#../sarra/bi../sarra/sh

export PYTHONPATH="`pwd`/../"
testdocroot="$HOME/sarra_devdocroot"
testhost=localhost

# test users for each role: tsource, tsub, tfeed, bunnymaster (admin)

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

sed 's+HOST+'"${testhost}"'+g; s+TESTDOCROOT+'"${testdocroot}"'+g' <templates/t_prime_dd.conf >$HOME/.config/sarra/sarra/t_prime_dd.conf

sed 's+HOST+'"${testhost}"'+g; s+TESTDOCROOT+'"${testdocroot}"'+g' <templates/t_sub.conf >$HOME/.config/sarra/subscribe/t_sub.conf

# ensure users have exchanges:
sr_audit --users foreground

sr restart
