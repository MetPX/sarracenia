#!/bin/bash

set -x

cdir=`dirname $1`
config=`basename $1`

cat > /tmp/Instrumentation << EOF

msg_file /local/home/sarra/convert/data/ddsr.20190804
plugin msg_from_file
plugin pxSender_log

EOF

cd $cdir

cat /tmp/Instrumentation >> $config



sr_sender stop  $config

rm ~/.cache/sarra/log/sr_sender_${config%%.conf}*.log*

sr_sender start $config

