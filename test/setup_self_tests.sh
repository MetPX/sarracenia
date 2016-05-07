#../sarra/bi../sarra/sh

export PYTHONPATH="`pwd`/../"
testdocroot="$HOME/sarra_devdocroot"
testhost=localhost

# test users for each role: tsource, tsub, tfeed, bunnymaster (admin)

if [ ! -d "$testdocroot" ]; then
  mkdir $testdocroot
  cp -r testree/* $testdocroot
fi

echo "Starting trivial server on: $testdocroot, saving pid in .httpserverpid"
testrundir="`pwd`"
cd $testdocroot
$testrundir/trivialserver.py &
httpserverpid=$!
cd $testrundir

echo $httpserverpid >.httpserverpid
echo $testdocroot >.httpdocroot

sed 's+HOST+'"${testhost}"'+g; s+TESTDOCROOT+'"${testdocroot}"'+g' <templates/prime_with_dd.conf >$HOME/.config/sarra/sarra/prime_with_dd.conf
