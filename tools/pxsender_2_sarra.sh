#!/bin/bash

cd `dirname $1`
cd ..

p=`basename $1`

# This script needs one argument a sundew pxSender config name
# ex.:  satnet-toronto
#
# It will try to convert it to sarra sender
# It will try the routing of a whole day 
# it will not convert scripts (plugins)
#

SR_SENDER=sender/${p}.conf
TX_CONF=sender/${p}.conf.orig

# ok prepare sarra sender file

mv sender/${p}.conf sender/${p}.conf.orig

# keep header documentation of sender file in sr_sender config 

vi -c '1,/^type/-1w!./doc' -c q  sender/${p}.conf.orig
cat ./doc > $SR_SENDER
rm  ./doc

# insert standard DDSR sender starting lines

cat >> $SR_SENDER << EOF

instances 1

# broker is localhost where the product resides

broker   amqp://feeder@localhost/
exchange xpublic

EOF

cat >> $SR_SENDER << EOF
# queue

prefetch   10
queue_name q_feeder.\${PROGRAM}.\${CONFIG}.\${HOSTNAME}

# where on this broker

base_dir /apps/sarra/public_data

# what to do with product

mirror   False
EOF

# add some standard options from the tx sender

lock=`cat $TX_CONF| grep '^lock'       | awk '{print $2}' 2>/dev/null`
chmd=`cat $TX_CONF| grep '^chmod'      | awk '{print $2}' 2>/dev/null`
batc=`cat $TX_CONF| grep '^batch'      | awk '{print $2}' 2>/dev/null`
timo=`cat $TX_CONF| grep '^timeout'    | awk '{print $2}' 2>/dev/null`

if [[ -z "$lock" ]]; then lock="None"; fi
if [[ -z "$batc" ]]; then batc="100";  fi

echo "batch    $batc" >> $SR_SENDER
echo "inflight $lock" >> $SR_SENDER

if [[ ! -z "$chmd" ]]; then echo "chmod    $chmd" >> $SR_SENDER; fi
if [[ ! -z "$timo" ]]; then echo "timeout  $timo" >> $SR_SENDER; fi
echo >> $SR_SENDER

# credentials and destination

protocol=`cat $TX_CONF| grep '^protocol'    | awk '{print $2}' 2>/dev/null`
pro_host=`cat $TX_CONF| grep '^host'        | awk '{print $2}' 2>/dev/null`
pro_port=`cat $TX_CONF| grep '^port'        | awk '{print $2}' 2>/dev/null`
pro_user=`cat $TX_CONF| grep '^user'        | awk '{print $2}' 2>/dev/null`
pro_pass=`cat $TX_CONF| grep '^password'    | awk '{print $2}' 2>/dev/null`
pro_mode=`cat $TX_CONF| grep '^ftp_mode'    | awk '{print $2}' 2>/dev/null`
pro_keyf=`cat $TX_CONF| grep '^ssh_keyfile' | awk '{print $2}' 2>/dev/null`
pro_bina=`cat $TX_CONF| grep '^binary'      | awk '{print $2}' 2>/dev/null`

credline="${protocol}://${pro_user}"
destination=$credline

if [[ ! -z "$pro_pass" ]]; then
   credline="$credline:$pro_pass"
fi

credline="$credline@$pro_host"
destination="$destination@$pro_host"

if [[ ! -z "$pro_port" ]]; then
   credline="$credline:$pro_port"
   destination="$destination:$pro_port"
fi

if [[ "$protocol" == "sftp" ]]; then
   if [[ ! -z "$pro_keyf" ]]; then
      credline="$credline ssh_keyfile=$pro_keyf"
   fi
fi

if [[ "$protocol" == "ftp" ]]; then
   if [[ ! -z "$pro_mode" ]]; then
      if   [[ "$pro_mode" == "active" ]]; then
              credline="$credline active,"
      elif [[ "$pro_mode" == "passive" ]]; then
              credline="$credline passive,"
      fi
   fi
   if [[ ! -z "$pro_bina" ]]; then
      if   [[ "$pro_bina" == "True" ]]; then
              credline="$credline binary"
      elif [[ "$pro_mode" == "False" ]]; then
              credline="$credline ascii"
      fi
   fi
fi

credline=`echo $credline | sed 's/,$//'`

echo $credline > ./credentials

echo                 >> $SR_SENDER
echo "# destination" >> $SR_SENDER
echo                 >> $SR_SENDER
echo "destination $destination" >> $SR_SENDER
echo                                      >> $SR_SENDER
echo "# where to send the products"       >> $SR_SENDER
echo                                      >> $SR_SENDER
 
echo "# verify/pick from orignal config"  >> $SR_SENDER
echo                                      >> $SR_SENDER

vi -c '/^type/,$w!./ORIG' -c q sender/${p}.conf.orig
cat ./ORIG >> $SR_SENDER
rm  ./ORIG
